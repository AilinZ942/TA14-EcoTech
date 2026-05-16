<template>
  <div class="dl">
    <!-- HERO -->
    <section class="hero">
      <div class="eco-shell hero-grid">
        <div class="hero-text">
          <span class="eco-eyebrow">Disposal map</span>
          <h1 class="eco-display">
            Find a <em>safe drop-off.</em>
          </h1>
          <p class="eco-lead">
            E-waste centres, battery points, council-run sites across Victoria.
            Search a suburb, filter what you need to drop, get directions.
          </p>
        </div>
      </div>
    </section>

    <!-- SEARCH -->
    <section class="search-section">
      <div class="eco-shell">
        <div class="search-card eco-glass">
          <div class="search-input">
            <span class="search-ic">⌕</span>
            <input
              v-model="searchTerm"
              type="search"
              placeholder="Suburb, postcode, or council (e.g. Carlton, 3053, Melbourne)"
              @keydown.enter="runSearch"
            />
            <button class="eco-btn eco-btn--mint" @click="runSearch" :disabled="isLoading">
              <span v-if="!isLoading">Search</span>
              <span v-else class="mini-spin" />
            </button>
          </div>

          <div class="search-row">
            <div class="filter-block">
              <span class="eco-mono">Range</span>
              <div class="chips">
                <button v-for="r in ranges" :key="r.value" :class="['chip', { on: selectedRange === r.value }]" @click="selectedRange = r.value">{{ r.label }}</button>
              </div>
            </div>
            <div class="filter-block">
              <span class="eco-mono">Accepts</span>
              <div class="chips">
                <button v-for="c in categories" :key="c.value" :class="['chip', { on: selectedCategory === c.value }]" @click="selectedCategory = c.value">
                  <span>{{ c.icon }}</span> {{ c.label }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- LAYOUT -->
    <section class="layout-section">
      <div class="eco-shell layout">
        <div class="map-card">
          <div v-if="!hasToken" class="map-placeholder">
            <div class="grid">
              <div v-for="n in 64" :key="n" class="cell" />
            </div>
            <div class="placeholder-msg">
              <span class="eco-mono">Map preview</span>
              <p>Set <code>VITE_MAPBOX_ACCESS_TOKEN</code> for live map. Results show on the right.</p>
            </div>
            <div v-if="visibleResults.length" class="dots">
              <span v-for="(r, i) in visibleResults.slice(0, 12)" :key="i"
                class="dot"
                :style="{ left: ((i % 6) * 14 + 10) + '%', top: (Math.floor(i / 6) * 26 + 22) + '%' }">
                {{ i + 1 }}
              </span>
            </div>
          </div>
          <div v-else ref="mapEl" class="map" />
          <div class="map-overlay">
            <div class="overlay-pill">
              <span class="ov-dot" />
              {{ visibleResults.length }} found
            </div>
          </div>
        </div>

        <aside class="panel">
          <header class="panel-head">
            <strong class="result-count">{{ visibleResults.length }} locations</strong>
            <span v-if="searchMeta?.message" class="meta">{{ searchMeta.message }}</span>
          </header>

          <div v-if="loadError" class="alert">{{ loadError }}</div>

          <div class="result-list">
            <article
              v-for="(loc, i) in visibleResults.slice(0, 30)"
              :key="(loc.dedupe_key || loc.facility_name) + i"
              class="loc"
            >
              <header class="loc-head">
                <div>
                  <h3>{{ loc.facility_name || 'Disposal location' }}</h3>
                  <p>{{ loc.address || `${loc.suburb || ''} ${loc.state || ''} ${loc.postcode || ''}` }}</p>
                </div>
                <span :class="['status', loc.business_status !== 'CLOSED_PERMANENTLY' ? 'on' : 'off']">
                  <span class="ind" />
                  {{ loc.business_status !== 'CLOSED_PERMANENTLY' ? 'Open' : 'Closed' }}
                </span>
              </header>
              <div v-if="locationTags(loc).length" class="tags">
                <span v-for="t in locationTags(loc)" :key="t" class="tag">{{ t }}</span>
              </div>
              <p v-if="loc.note" class="note">{{ loc.note }}</p>
              <div class="actions">
                <button class="eco-btn eco-btn--ghost" @click="openDetails(loc)">View</button>
                <button class="eco-btn eco-btn--mint" @click="openDirections(loc)">
                  Directions <span class="arrow">→</span>
                </button>
              </div>
            </article>

            <div v-if="!visibleResults.length && !isLoading && !loadError" class="empty">
              <span>⌖</span>
              <h4>No results yet</h4>
              <p>Search a suburb or postcode to see disposal locations.</p>
            </div>
          </div>
        </aside>
      </div>
    </section>

    <!-- SAFETY TIPS -->
    <section class="tips">
      <div class="eco-shell">
        <header class="tips-head">
          <span class="eco-eyebrow">Before you go</span>
          <h2 class="eco-h2">E-waste safety in <em>30 seconds.</em></h2>
        </header>
        <div class="tip-grid">
          <article class="tip">
            <span class="t-icon warn">⚠</span>
            <h4>Don't bag batteries</h4>
            <p>Tape the terminals. Loose, in a dedicated pouch.</p>
          </article>
          <article class="tip">
            <span class="t-icon">📱</span>
            <h4>Wipe before donating</h4>
            <p>Factory-reset. Remove SIM and SD cards.</p>
          </article>
          <article class="tip">
            <span class="t-icon">🔥</span>
            <h4>Swollen battery?</h4>
            <p>Hazardous drop-off, immediately. Don't store, don't bin.</p>
          </article>
          <article class="tip">
            <span class="t-icon">🔌</span>
            <h4>Bundle cables</h4>
            <p>Cables together so recyclers can sort them quickly.</p>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { api } from '@/api'

const ranges = [
  { value: 'exact', label: 'Exact' },
  { value: '10', label: '10 km' },
  { value: '20', label: '20 km' },
  { value: '50', label: '50 km' },
  { value: 'state', label: 'State-wide' },
]
const categories = [
  { value: '', label: 'All', icon: '✦' },
  { value: 'general_ewaste', label: 'General', icon: '⌧' },
  { value: 'battery', label: 'Batteries', icon: '🔋' },
  { value: 'mobile', label: 'Mobiles', icon: '📱' },
  { value: 'computer', label: 'Computers', icon: '💻' },
]

const mapboxToken = String(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '').trim()
const hasToken = computed(() => Boolean(mapboxToken))

const searchTerm = ref('')
const selectedRange = ref('exact')
const selectedCategory = ref('')
const isLoading = ref(false)
const loadError = ref('')
const results = ref([])
const searchMeta = ref(null)
const mapEl = ref(null)
let map = null
let renderedMarkers = []

const visibleResults = computed(() => {
  if (!selectedCategory.value) return results.value
  return results.value.filter(r => {
    const text = `${r.ewaste_category || ''} ${r.ewaste_match_text || ''} ${r.accepted_items || ''}`.toLowerCase()
    if (selectedCategory.value === 'battery') return /batter/.test(text)
    if (selectedCategory.value === 'mobile') return /mobile|phone/.test(text)
    if (selectedCategory.value === 'computer') return /computer|laptop|tablet|monitor/.test(text)
    return true
  })
})

function locationTags(loc) {
  const t = []
  if (loc.ewaste_category) t.push(loc.ewaste_category.replace(/_/g, ' '))
  if (loc.source === 'cloud_database') t.push('verified')
  return t.slice(0, 3)
}

async function runSearch() {
  if (isLoading.value) return
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await api.searchDisposalLocation({ searchText: searchTerm.value, searchRange: selectedRange.value })
    results.value = res.data || res.items || res || []
    searchMeta.value = res.meta?.search || null
    if (hasToken.value) renderMarkers()
  } catch (err) {
    results.value = mockResults()
    searchMeta.value = { message: 'Showing demo locations — backend unavailable.' }
  } finally {
    isLoading.value = false
  }
}

function mockResults() {
  return [
    { facility_name: 'Carlton E-Waste Drop-off', address: '5 Lygon Street, Carlton VIC 3053', latitude: -37.7989, longitude: 144.9667, ewaste_category: 'general_ewaste', accepted_items: 'phones, laptops, batteries', source: 'cloud_database' },
    { facility_name: 'Melbourne Battery Point', address: '230 Collins Street, Melbourne VIC 3000', latitude: -37.8163, longitude: 144.9684, ewaste_category: 'battery', accepted_items: 'all batteries' },
    { facility_name: 'Recycling Centre — Brunswick', address: '12 Sydney Road, Brunswick VIC 3056', latitude: -37.7676, longitude: 144.9602, ewaste_category: 'computer', accepted_items: 'computers, monitors, cables' },
    { facility_name: 'Council Hub — Footscray', address: '8 Hopkins Street, Footscray VIC 3011', latitude: -37.7997, longitude: 144.9000, ewaste_category: 'mobile', accepted_items: 'phones, tablets, accessories' },
  ]
}

function openDirections(loc) {
  if (loc.google_maps_uri) { window.open(loc.google_maps_uri, '_blank'); return }
  const q = encodeURIComponent(loc.address || `${loc.facility_name} ${loc.suburb || ''}`)
  window.open(`https://www.google.com/maps/search/?api=1&query=${q}`, '_blank')
}
function openDetails(loc) {
  if (loc.website_uri) window.open(loc.website_uri, '_blank')
}

async function initMap() {
  if (!hasToken.value || !mapEl.value || map) return
  const mapboxgl = (await import('mapbox-gl')).default
  await import('mapbox-gl/dist/mapbox-gl.css')
  mapboxgl.accessToken = mapboxToken
  map = new mapboxgl.Map({
    container: mapEl.value,
    style: 'mapbox://styles/mapbox/dark-v11',
    center: [144.9631, -37.8136], zoom: 9.5, attributionControl: false,
  })
  map.on('load', renderMarkers)
}

async function renderMarkers() {
  if (!map) return
  const mapboxgl = (await import('mapbox-gl')).default
  renderedMarkers.forEach(m => m.remove())
  renderedMarkers = []
  visibleResults.value.forEach((loc) => {
    if (loc.latitude == null || loc.longitude == null) return
    const el = document.createElement('div')
    el.className = 'eco-disposal-marker'
    const m = new mapboxgl.Marker({ element: el }).setLngLat([loc.longitude, loc.latitude]).addTo(map)
    renderedMarkers.push(m)
  })
}

onMounted(() => { initMap() })
onBeforeUnmount(() => { if (map) { map.remove(); map = null } })
watch(selectedCategory, () => { if (hasToken.value) renderMarkers() })
</script>

<style scoped>
.dl { padding-top: 100px; padding-bottom: 0; min-height: 100vh; }

/* HERO */
.hero { padding: 80px 0 40px; }
.hero-grid { display: grid; gap: 24px; }
.hero-text { display: flex; flex-direction: column; gap: 18px; max-width: 800px; }
.hero-text h1 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

/* SEARCH */
.search-section { padding: 20px 0 40px; }
.search-card { padding: 24px; display: flex; flex-direction: column; gap: 18px; }
.search-input {
  display: flex; align-items: center; gap: 12px;
  padding: 6px 16px 6px 20px;
  background: rgba(0,0,0,0.25);
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
}
.search-input:focus-within { border-color: var(--mint); box-shadow: 0 0 0 4px rgba(125,216,176,0.12); }
.search-ic { color: var(--mint); font-size: 18px; }
.search-input input {
  flex: 1; background: transparent; border: 0; outline: 0;
  color: var(--ink-0); font-size: 15px; padding: 10px 0;
}
.search-input input::placeholder { color: var(--ink-3); }
.mini-spin {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid rgba(0,0,0,0.2);
  border-top-color: var(--ink-on-light);
  animation: sp 0.7s linear infinite;
}
@keyframes sp { to { transform: rotate(360deg); } }

.search-row { display: flex; gap: 32px; flex-wrap: wrap; }
.filter-block { display: flex; flex-direction: column; gap: 8px; flex: 1; min-width: 220px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
  color: var(--ink-1);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
}
.chip:hover { border-color: var(--mint); color: var(--ink-0); }
.chip.on { background: var(--mint); color: var(--ink-on-light); border-color: var(--mint); }

/* LAYOUT */
.layout-section { padding-bottom: 80px; }
.layout {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 24px;
  align-items: start;
}

/* MAP */
.map-card {
  position: sticky;
  top: 100px;
  height: 640px;
  background: var(--bg-1);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  overflow: hidden;
  position: relative;
}
.map { width: 100%; height: 100%; }

.map-overlay { position: absolute; top: 18px; left: 18px; z-index: 5; pointer-events: none; }
.overlay-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 14px;
  background: rgba(6, 18, 15, 0.85);
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--mint);
  backdrop-filter: blur(10px);
}
.ov-dot {
  width: 8px; height: 8px;
  background: var(--mint);
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(125, 216, 176, 0.25);
}

.map-placeholder { position: relative; width: 100%; height: 100%; background: linear-gradient(135deg, #0E2620, #061511); }
.grid { position: absolute; inset: 0; display: grid; grid-template-columns: repeat(8, 1fr); }
.cell { border-right: 1px solid rgba(125,216,176,0.05); border-bottom: 1px solid rgba(125,216,176,0.05); }
.placeholder-msg {
  position: absolute; bottom: 20px; left: 20px;
  padding: 12px 16px;
  background: rgba(6, 18, 15, 0.9);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 4px;
  max-width: 320px;
}
.placeholder-msg p { color: var(--ink-2); font-size: 12px; }
.placeholder-msg code { background: rgba(125,216,176,0.12); color: var(--mint); padding: 1px 6px; border-radius: 4px; font-size: 11px; }

.dots { position: absolute; inset: 0; }
.dot {
  position: absolute;
  width: 30px; height: 30px;
  background: var(--mint);
  color: var(--ink-on-light);
  border-radius: 50%;
  display: grid; place-items: center;
  font-family: var(--font-mono);
  font-size: 11px; font-weight: 700;
  box-shadow: 0 6px 20px rgba(125,216,176,0.5);
  animation: float-y 4s ease-in-out infinite;
}
.dot:nth-child(odd) { animation-delay: -2s; }

/* PANEL */
.panel { display: flex; flex-direction: column; gap: 14px; max-height: 640px; overflow-y: auto; padding-right: 4px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.result-count { font-family: var(--font-display); font-size: 16px; color: var(--mint); font-weight: 500; }
.panel-head .meta { font-family: var(--font-mono); font-size: 11px; color: var(--ink-2); text-align: right; }

.alert {
  padding: 12px 14px;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.25);
  color: var(--bad);
  border-radius: var(--r-sm);
  font-size: 13px;
}

.result-list { display: flex; flex-direction: column; gap: 12px; }
.loc {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  padding: 20px;
  display: flex; flex-direction: column; gap: 12px;
  transition: all 0.25s var(--ease-out);
}
.loc:hover { border-color: var(--mint); transform: translateY(-2px); }

.loc-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; }
.loc h3 { font-family: var(--font-display); font-size: 17px; font-weight: 500; margin-bottom: 4px; }
.loc-head p { color: var(--ink-2); font-size: 13px; }
.status {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: var(--r-pill);
  font-weight: 600;
}
.status.on { background: rgba(125,216,176,0.18); color: var(--mint); }
.status.off { background: rgba(248,113,113,0.18); color: var(--bad); }
.ind { width: 6px; height: 6px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }

.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag {
  font-size: 11px;
  padding: 4px 10px;
  background: rgba(125,216,176,0.1);
  color: var(--mint);
  border: 1px solid rgba(125,216,176,0.22);
  border-radius: var(--r-pill);
}
.note { color: var(--ink-2); font-size: 13px; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }

.empty {
  padding: 60px 30px;
  text-align: center;
  background: var(--surface);
  border: 1px dashed var(--hairline-strong);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 8px; align-items: center;
}
.empty span { font-size: 36px; color: var(--ink-3); }
.empty h4 { font-family: var(--font-display); font-size: 18px; font-weight: 500; }
.empty p { color: var(--ink-2); font-size: 14px; }

/* TIPS */
.tips { padding: 80px 0 100px; }
.tips-head { display: flex; flex-direction: column; gap: 14px; margin-bottom: 40px; max-width: 600px; }
.tips-head h2 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.tip-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.tip {
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 12px;
  transition: all 0.3s var(--ease-out);
}
.tip:hover { border-color: var(--mint); transform: translateY(-4px); }
.t-icon {
  width: 44px; height: 44px;
  display: grid; place-items: center;
  background: rgba(125,216,176,0.12);
  border: 1px solid rgba(125,216,176,0.25);
  border-radius: var(--r-sm);
  font-size: 20px;
  color: var(--mint);
}
.t-icon.warn { background: rgba(244,162,97,0.12); border-color: rgba(244,162,97,0.3); color: var(--peach); }
.tip h4 { font-family: var(--font-display); font-size: 16px; font-weight: 500; }
.tip p { color: var(--ink-2); font-size: 13px; line-height: 1.6; }

@media (max-width: 1024px) {
  .layout { grid-template-columns: 1fr; }
  .map-card { position: relative; top: 0; height: 380px; }
  .panel { max-height: none; }
  .tip-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .tip-grid { grid-template-columns: 1fr; }
}

:deep(.eco-disposal-marker) {
  width: 18px; height: 18px;
  border-radius: 50%;
  background: var(--mint);
  border: 2px solid var(--bg-0);
  box-shadow: 0 0 16px rgba(125,216,176,0.6);
  cursor: pointer;
}
</style>
