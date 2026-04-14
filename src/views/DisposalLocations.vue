<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

import { searchMapFacilities } from '../lib/mapApi'
import {
  buildCategorySummary,
  buildFacilityMarkers,
  getCategoryLabel,
  getCategoryOptions,
  getFacilityBounds,
} from '../lib/ewasteMapModel'

const mapboxAccessToken = String(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '').trim()
const mapDataMode = String(import.meta.env.VITE_MAP_DATA_MODE || 'auto').trim().toLowerCase() || 'auto'

const mapContainerRef = ref(null)
const isLoading = ref(false)
const loadError = ref('')
const searchTerm = ref('')
const selectedCategory = ref('')
const facilityRows = ref([])
const facilityMarkers = ref([])
const selectedMarkerId = ref('')
const activePipeline = ref('local')
const activeSource = ref('csv')
const fallbackReason = ref('')

let map = null
let mapReady = false
let activePopup = null
let activeRequestController = null
let requestTimer = null
let renderedMarkers = []

const categoryOptions = getCategoryOptions()
const hasToken = computed(() => Boolean(mapboxAccessToken))
const visibleMarkers = computed(() => {
  const needle = searchTerm.value.trim().toLowerCase()

  return facilityMarkers.value.filter((marker) => {
    if (selectedCategory.value && marker.category !== selectedCategory.value) {
      return false
    }

    if (!needle) {
      return true
    }

    const haystack = [
      marker.facilityName,
      marker.address,
      marker.suburb,
      marker.postcode,
      marker.state,
      marker.categoryLabel,
      marker.source,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return haystack.includes(needle)
  })
})
const selectedMarker = computed(
  () => visibleMarkers.value.find((marker) => marker.id === selectedMarkerId.value) || null,
)
const categorySummary = computed(() => buildCategorySummary(visibleMarkers.value))
const tokenHelpText = computed(() =>
  hasToken.value
    ? ''
    : 'Set VITE_MAPBOX_ACCESS_TOKEN in .env.local, then restart the Vite dev server.',
)
const pipelineLabel = computed(() => {
  if (activePipeline.value === 'azure') return 'Azure API'
  if (activePipeline.value === 'legacy-geojson') return 'Legacy GeoJSON'
  return 'Local CSV'
})

function buildRequestPayload() {
  return {
    resourceType: 'disposal',
    state: '',
    category: '',
    searchText: '',
    limit: 1000,
  }
}

function removeRenderedMarkers() {
  renderedMarkers.forEach((entry) => entry.remove())
  renderedMarkers = []
}

function closePopup() {
  if (activePopup) {
    activePopup.remove()
    activePopup = null
  }
}

function popupHtml(marker) {
  const rows = [
    ['Address', marker.address || 'Not provided'],
    ['Suburb', marker.suburb || 'Not provided'],
    ['Postcode', marker.postcode || 'Not provided'],
    ['State', marker.state || 'Not provided'],
    ['Category', marker.categoryLabel || getCategoryLabel(marker.category)],
    ['Coord source', marker.coordSource || 'Not provided'],
    ['Source file', marker.sourceFile || 'Not provided'],
  ]

  return `
    <article class="map-popup">
      <p class="map-popup__eyebrow">Disposal Site</p>
      <h3>${escapeHtml(marker.facilityName)}</h3>
      ${rows
        .map(
          ([label, value]) => `
            <div class="map-popup__row">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </div>
          `,
        )
        .join('')}
    </article>
  `
}

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function selectMarker(marker, options = {}) {
  selectedMarkerId.value = marker.id

  if (!map) return

  closePopup()

  const popup = new mapboxgl.Popup({
    offset: 18,
    maxWidth: '320px',
    closeButton: true,
  })
    .setLngLat([marker.longitude, marker.latitude])
    .setHTML(popupHtml(marker))
    .addTo(map)

  popup.on('close', () => {
    if (activePopup === popup) {
      activePopup = null
    }
  })

  activePopup = popup

  if (!options.skipFlyTo) {
    map.flyTo({
      center: [marker.longitude, marker.latitude],
      zoom: Math.max(map.getZoom(), 8.2),
      speed: 0.9,
      essential: true,
    })
  }
}

function fitMapToMarkers(markers) {
  if (!map || !markers.length) return

  const bounds = getFacilityBounds(markers)
  if (!bounds) return

  if (
    bounds.minLongitude === bounds.maxLongitude &&
    bounds.minLatitude === bounds.maxLatitude
  ) {
    map.easeTo({
      center: [bounds.minLongitude, bounds.minLatitude],
      zoom: 8.5,
      duration: 700,
    })
    return
  }

  map.fitBounds(
    [
      [bounds.minLongitude, bounds.minLatitude],
      [bounds.maxLongitude, bounds.maxLatitude],
    ],
    {
      padding: 56,
      maxZoom: 9.5,
      duration: 700,
    },
  )
}

function renderMarkers() {
  if (!map || !mapReady) return

  removeRenderedMarkers()
  closePopup()

  renderedMarkers = visibleMarkers.value.map((marker) => {
    const element = document.createElement('button')
    element.type = 'button'
    element.className = 'facility-marker'
    element.style.backgroundColor = marker.categoryColor
    element.setAttribute('aria-label', marker.facilityName)
    element.addEventListener('click', () => {
      selectMarker(marker)
    })

    return new mapboxgl.Marker({
      element,
      anchor: 'center',
    })
      .setLngLat([marker.longitude, marker.latitude])
      .addTo(map)
  })

  if (selectedMarker.value) {
    selectMarker(selectedMarker.value, { skipFlyTo: true })
    return
  }

  fitMapToMarkers(visibleMarkers.value)
}

async function loadFacilities() {
  if (!hasToken.value) {
    loadError.value = ''
    facilityRows.value = []
    facilityMarkers.value = []
    return
  }

  if (activeRequestController) {
    activeRequestController.abort()
  }

  const controller = new AbortController()
  activeRequestController = controller
  isLoading.value = true
  loadError.value = ''

  try {
    const response = await searchMapFacilities(buildRequestPayload(), {
      signal: controller.signal,
    })
    const rows = Array.isArray(response?.items) ? response.items : []

    facilityRows.value = rows
    facilityMarkers.value = buildFacilityMarkers(rows)
    activePipeline.value = response?.meta?.pipeline || 'local'
    activeSource.value = response?.meta?.source || 'csv'
    fallbackReason.value = response?.meta?.fallbackReason || ''

    if (
      selectedMarkerId.value &&
      !facilityMarkers.value.some((marker) => marker.id === selectedMarkerId.value)
    ) {
      selectedMarkerId.value = ''
    }

    await nextTick()
    renderMarkers()
  } catch (error) {
    if (error?.name === 'AbortError') return

    console.error('[DisposalLocations] failed to load disposal facilities:', error)
    loadError.value =
      error instanceof Error ? error.message : 'Failed to load disposal facilities'
    facilityRows.value = []
    facilityMarkers.value = []
    selectedMarkerId.value = ''
    activePipeline.value = 'local'
    activeSource.value = 'csv'
    fallbackReason.value = ''
    removeRenderedMarkers()
    closePopup()
  } finally {
    if (activeRequestController === controller) {
      activeRequestController = null
      isLoading.value = false
    }
  }
}

function queueMarkerRefresh() {
  if (requestTimer) {
    window.clearTimeout(requestTimer)
  }

  requestTimer = window.setTimeout(() => {
    requestTimer = null
    renderMarkers()
  }, 80)
}

function initialiseMap() {
  if (!hasToken.value || map || !mapContainerRef.value) return

  mapboxgl.accessToken = mapboxAccessToken
  map = new mapboxgl.Map({
    container: mapContainerRef.value,
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [144.9631, -37.8136],
    zoom: 5.4,
  })

  map.addControl(new mapboxgl.NavigationControl(), 'top-right')

  map.on('load', () => {
    mapReady = true
    renderMarkers()
  })
}

function resetFilters() {
  selectedCategory.value = ''
  searchTerm.value = ''
}

watch(visibleMarkers, () => {
  queueMarkerRefresh()
})

onMounted(async () => {
  initialiseMap()
  await loadFacilities()
})

onBeforeUnmount(() => {
  if (requestTimer) {
    window.clearTimeout(requestTimer)
  }

  if (activeRequestController) {
    activeRequestController.abort()
  }

  removeRenderedMarkers()
  closePopup()

  if (map) {
    map.remove()
    map = null
  }

  mapReady = false
})
</script>

<template>
  <section class="disposal-page">
    <header class="hero-card">
      <div>
        <p class="eyebrow">Disposal Locations</p>
        <h1>Mapbox disposal site map</h1>
        <p class="hero-copy">
          This page now uses a Mapbox GL JS embedded map and consumes disposal rows through the
          unified `{ items: [...] }` pipeline. In `auto` mode it prefers Azure when available and
          falls back to the local cleaned CSV.
        </p>
      </div>

      <div class="hero-stats">
        <article>
          <span>Visible sites</span>
          <strong>{{ visibleMarkers.length }}</strong>
        </article>
        <article>
          <span>Pipeline</span>
          <strong>{{ pipelineLabel }}</strong>
        </article>
        <article>
          <span>Mode</span>
          <strong>{{ mapDataMode }}</strong>
        </article>
        <article>
          <span>Source</span>
          <strong>{{ activeSource }}</strong>
        </article>
      </div>
    </header>

    <div class="content-grid">
      <section class="map-panel">
        <div class="toolbar-card">
          <label>
            <span>Search</span>
            <input
              v-model.trim="searchTerm"
              type="search"
              placeholder="Facility, suburb, address, postcode"
            />
          </label>

          <label>
            <span>Category</span>
            <select v-model="selectedCategory">
              <option value="">All categories</option>
              <option
                v-for="category in categoryOptions"
                :key="category.value"
                :value="category.value"
              >
                {{ category.label }}
              </option>
            </select>
          </label>

          <div class="toolbar-actions">
            <button type="button" class="ghost" @click="resetFilters">Clear filters</button>
          </div>
        </div>

        <div class="map-frame">
          <div v-if="!hasToken" class="map-overlay map-overlay--warning">
            <h2>Mapbox token required</h2>
            <p>{{ tokenHelpText }}</p>
            <code>VITE_MAPBOX_ACCESS_TOKEN=your_token_here</code>
          </div>

          <div v-else-if="isLoading" class="map-overlay">
            <p>Loading disposal facilities...</p>
          </div>

          <div v-else-if="loadError" class="map-overlay map-overlay--error">
            <h2>Unable to load disposal data</h2>
            <p>{{ loadError }}</p>
            <p v-if="fallbackReason">{{ fallbackReason }}</p>
          </div>

          <div ref="mapContainerRef" class="map-container" />
        </div>

        <p v-if="fallbackReason && !loadError" class="support-copy">
          Azure disposal data was unavailable, so the page automatically fell back to the local CSV.
          Reason: {{ fallbackReason }}
        </p>
      </section>

      <aside class="side-panel">
        <section class="panel-card">
          <p class="eyebrow">Selection</p>
          <template v-if="selectedMarker">
            <h2>{{ selectedMarker.facilityName }}</h2>
            <div class="detail-list">
              <div class="detail-row"><span>Address</span><strong>{{ selectedMarker.address || 'Not provided' }}</strong></div>
              <div class="detail-row"><span>Suburb</span><strong>{{ selectedMarker.suburb || 'Not provided' }}</strong></div>
              <div class="detail-row"><span>Postcode</span><strong>{{ selectedMarker.postcode || 'Not provided' }}</strong></div>
              <div class="detail-row"><span>State</span><strong>{{ selectedMarker.state || 'Not provided' }}</strong></div>
              <div class="detail-row"><span>Category</span><strong>{{ selectedMarker.categoryLabel }}</strong></div>
              <div class="detail-row"><span>Coord source</span><strong>{{ selectedMarker.coordSource || 'Not provided' }}</strong></div>
              <div class="detail-row"><span>Source file</span><strong>{{ selectedMarker.sourceFile || 'Not provided' }}</strong></div>
            </div>
          </template>
          <template v-else>
            <h2>Map summary</h2>
            <p class="support-copy">
              Click a marker to inspect a disposal site. The summary updates from the current visible
              marker set.
            </p>
            <div class="detail-list">
              <div class="detail-row"><span>Rows loaded</span><strong>{{ facilityRows.length }}</strong></div>
              <div class="detail-row"><span>Markers shown</span><strong>{{ visibleMarkers.length }}</strong></div>
              <div class="detail-row"><span>Pipeline</span><strong>{{ pipelineLabel }}</strong></div>
              <div class="detail-row"><span>Mode</span><strong>{{ mapDataMode }}</strong></div>
            </div>
          </template>
        </section>

        <section class="panel-card">
          <p class="eyebrow">Categories</p>
          <h2>Visible breakdown</h2>
          <div class="category-list">
            <div
              v-for="entry in categorySummary"
              :key="entry.key"
              class="category-row"
            >
              <span class="category-label">
                <span class="category-dot" :style="{ backgroundColor: entry.color }" />
                {{ entry.label }}
              </span>
              <strong>{{ entry.count }}</strong>
            </div>
            <p v-if="!categorySummary.length" class="support-copy">
              No disposal sites match the current filters.
            </p>
          </div>
        </section>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.disposal-page{min-height:100vh;padding:2rem;background:linear-gradient(180deg,#f6f4ef 0%,#ece6db 100%);color:#102a43}
.hero-card,.toolbar-card,.panel-card{border:1px solid rgba(16,42,67,.12);border-radius:28px;background:rgba(255,252,247,.94);box-shadow:0 20px 60px rgba(16,42,67,.08)}
.hero-card{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(280px,.9fr);gap:1.25rem;padding:1.5rem;margin-bottom:1.5rem}
.eyebrow{margin:0 0 .35rem;font-size:.76rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#9b4b1e}
h1,h2,p{margin-top:0}
h1{margin-bottom:.75rem;font-size:clamp(2rem,3vw,3.1rem);line-height:1.05}
.hero-copy,.support-copy{margin-bottom:0;color:#486581;line-height:1.6}
.hero-stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.85rem}
.hero-stats article{padding:1rem;border-radius:22px;background:#102a43;color:#fff}
.hero-stats span{display:block;margin-bottom:.35rem;color:rgba(255,255,255,.68);font-size:.82rem}
.hero-stats strong{font-size:1.05rem}
.content-grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(320px,.85fr);gap:1.5rem;align-items:start}
.map-panel,.side-panel{display:grid;gap:1rem}
.toolbar-card,.panel-card{padding:1.2rem}
.toolbar-card{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(180px,.7fr) auto;gap:1rem;align-items:end}
label{display:grid;gap:.45rem;font-size:.92rem;font-weight:700;color:#334e68}
input,select{min-height:46px;border:1px solid rgba(16,42,67,.14);border-radius:16px;padding:.85rem 1rem;background:#fffdfa;color:#102a43;font:inherit}
button{min-height:44px;border:0;border-radius:999px;padding:.72rem 1rem;background:#102a43;color:#fff;font-weight:700;cursor:pointer}
.ghost{background:rgba(16,42,67,.1);color:#102a43}
.map-frame{position:relative;min-height:640px;border:1px solid rgba(16,42,67,.14);border-radius:30px;overflow:hidden;background:#dfe8e8}
.map-container{width:100%;height:640px}
.map-overlay{position:absolute;inset:18px auto auto 18px;z-index:2;max-width:340px;padding:1rem 1.1rem;border-radius:18px;background:rgba(16,42,67,.9);color:#fff}
.map-overlay h2,.map-overlay p{margin-bottom:.55rem}
.map-overlay code{display:block;padding:.7rem .8rem;border-radius:12px;background:rgba(255,255,255,.08);font-size:.86rem;word-break:break-all}
.map-overlay--warning{background:rgba(122,72,21,.94)}
.map-overlay--error{background:rgba(122,29,29,.94)}
.detail-list,.category-list{display:grid;gap:.7rem}
.detail-row,.category-row{display:flex;gap:1rem;justify-content:space-between;align-items:start}
.detail-row span,.category-row span{color:#486581}
.detail-row strong,.category-row strong{text-align:right}
.category-label{display:inline-flex;align-items:center;gap:.55rem}
.category-dot{width:12px;height:12px;border-radius:999px;flex:0 0 auto}
:deep(.facility-marker){width:18px;height:18px;border:3px solid #fff;border-radius:999px;box-shadow:0 8px 18px rgba(16,42,67,.28);cursor:pointer;padding:0}
:deep(.mapboxgl-popup-content){padding:0;border-radius:18px;box-shadow:0 18px 36px rgba(16,42,67,.18)}
:deep(.mapboxgl-popup-close-button){padding:.45rem .55rem;font-size:1.1rem}
:deep(.map-popup){padding:1rem 1rem .95rem;min-width:240px;color:#102a43}
:deep(.map-popup__eyebrow){margin:0 0 .3rem;font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#9b4b1e}
:deep(.map-popup h3){margin:0 0 .7rem;font-size:1rem;line-height:1.35}
:deep(.map-popup__row){display:flex;gap:.8rem;justify-content:space-between;align-items:start;padding:.18rem 0}
:deep(.map-popup__row span){color:#627d98}
:deep(.map-popup__row strong){max-width:160px;text-align:right}
@media (max-width:1100px){.hero-card,.content-grid{grid-template-columns:1fr}}
@media (max-width:760px){.disposal-page{padding:1rem}.toolbar-card{grid-template-columns:1fr}.hero-stats{grid-template-columns:1fr}.map-frame,.map-container{min-height:520px;height:520px}}
</style>
