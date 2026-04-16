<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const mapRef = ref(null)

const loading = ref(true)
const error = ref('')
const searchQuery = ref('')
const selectedCategory = ref('All')
const selectedSite = ref(null)
const allSites = ref([])

const userLocation = ref(null)
const locatingUser = ref(false)
const nearestOnly = ref(false)

let map = null
let markersLayer = null
let userMarker = null

const allowedCategories = ['All', 'E-waste recycling', 'Drop-off point', 'Other']

function normalizeCategory(value) {
  const raw = String(value || '').trim().toLowerCase()

  if (raw.includes('battery')) return 'Battery recycling'
  if (raw.includes('transfer')) return 'Transfer station'
  if (raw.includes('repair') || raw.includes('reuse')) return 'Repair and reuse'
  if (raw.includes('drop')) return 'Drop-off point'
  if (raw.includes('e-waste') || raw.includes('ewaste') || raw.includes('electronic')) {
    return 'E-waste recycling'
  }

  return 'Other'
}

function parseCoordinate(value) {
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}

function formatAddress(site) {
  const parts = [
    site.address_line_1 || site.address || '',
    site.suburb || '',
    site.state || '',
    site.postcode || '',
  ].filter(Boolean)

  return parts.join(', ')
}

function normalizeSite(raw, index) {
  const lat =
    parseCoordinate(raw.latitude) ??
    parseCoordinate(raw.lat) ??
    parseCoordinate(raw.y) ??
    parseCoordinate(raw.geom_lat)

  const lng =
    parseCoordinate(raw.longitude) ??
    parseCoordinate(raw.lng) ??
    parseCoordinate(raw.lon) ??
    parseCoordinate(raw.x) ??
    parseCoordinate(raw.geom_lng)

  return {
    id: raw.id || raw.site_id || raw.facility_id || `site-${index}`,
    name: raw.facility_name || raw.name || raw.site_name || 'Unknown facility',
    category: normalizeCategory(raw.category || raw.site_category || raw.type),
    address_line_1: raw.address_line_1 || raw.address || '',
    suburb: raw.suburb || raw.city || '',
    state: raw.state || '',
    postcode: raw.postcode || '',
    source_file: raw.source_file || '',
    coordinate_source: raw.coordinate_source || '',
    accepted_items: raw.accepted_items || '',
    phone: raw.phone || '',
    website: raw.website || '',
    latitude: lat,
    longitude: lng,
    distanceKm: null,
    raw,
  }
}

function haversineDistance(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180
  const R = 6371

  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2)

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

async function fetchSites() {
  loading.value = true
  error.value = ''

  try {
    const payload = {
      query: '',
      category: '',
      limit: 500,
    }

    const res = await fetch('/api/map/disposal-locations/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      throw new Error(`Failed to load disposal locations (${res.status})`)
    }

    const data = await res.json()

    const items = Array.isArray(data?.items)
      ? data.items
      : Array.isArray(data)
        ? data
        : []

    allSites.value = items
      .map((item, index) => normalizeSite(item, index))
      .filter((site) => site.latitude !== null && site.longitude !== null)
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to load disposal locations.'
  } finally {
    loading.value = false
  }
}

const processedSites = computed(() => {
  return allSites.value.map((site) => {
    let distanceKm = null

    if (userLocation.value) {
      distanceKm = haversineDistance(
        userLocation.value.latitude,
        userLocation.value.longitude,
        site.latitude,
        site.longitude,
      )
    }

    return {
      ...site,
      distanceKm,
    }
  })
})

const filteredSites = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  let results = processedSites.value.filter((site) => {
    const matchCategory =
      selectedCategory.value === 'All' || site.category === selectedCategory.value

    const searchableText = [
      site.name,
      site.address_line_1,
      site.suburb,
      site.state,
      site.postcode,
      site.category,
    ]
      .join(' ')
      .toLowerCase()

    const matchQuery = !query || searchableText.includes(query)

    const excluded =
      site.category === 'Battery recycling' ||
      site.category === 'Transfer station' ||
      site.category === 'Repair and reuse'

    return matchCategory && matchQuery && !excluded
  })

  if (nearestOnly.value && userLocation.value) {
    results = results
      .filter((site) => site.distanceKm !== null)
      .sort((a, b) => a.distanceKm - b.distanceKm)
      .slice(0, 5)
  }

  return results
})

const visibleCount = computed(() => filteredSites.value.length)

function createMarkerIcon(isSelected = false) {
  return L.divIcon({
    className: 'custom-marker-wrapper',
    html: `
      <div class="custom-marker ${isSelected ? 'selected' : ''}">
        <span></span>
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -20],
  })
}

function createUserMarkerIcon() {
  return L.divIcon({
    className: 'custom-user-marker-wrapper',
    html: `
      <div class="custom-user-marker">
        <span></span>
      </div>
    `,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
}

function initMap() {
  if (!mapRef.value || map) return

  map = L.map(mapRef.value, {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView([-37.8136, 144.9631], 6)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)

  markersLayer = L.layerGroup().addTo(map)
}

function updateUserMarker() {
  if (!map) return

  if (userMarker) {
    map.removeLayer(userMarker)
    userMarker = null
  }

  if (userLocation.value) {
    userMarker = L.marker([userLocation.value.latitude, userLocation.value.longitude], {
      icon: createUserMarkerIcon(),
    }).addTo(map)

    userMarker.bindPopup('<strong>Your current location</strong>')
  }
}

function renderMarkers() {
  if (!map || !markersLayer) return

  markersLayer.clearLayers()
  updateUserMarker()

  const bounds = []

  if (userLocation.value) {
    bounds.push([userLocation.value.latitude, userLocation.value.longitude])
  }

  filteredSites.value.forEach((site) => {
    const isSelected = selectedSite.value?.id === site.id

    const marker = L.marker([site.latitude, site.longitude], {
      icon: createMarkerIcon(isSelected),
    })

    marker.on('click', () => {
      selectedSite.value = site
      map.flyTo([site.latitude, site.longitude], 13, { duration: 1.2 })
      nextTick(() => renderMarkers())
    })

    marker.bindPopup(`
      <div style="min-width: 190px;">
        <strong>${site.name}</strong><br/>
        <span>${site.category}</span><br/>
        <span>${formatAddress(site)}</span>
        ${site.distanceKm !== null ? `<br/><span><strong>${site.distanceKm.toFixed(2)} km away</strong></span>` : ''}
      </div>
    `)

    markersLayer.addLayer(marker)
    bounds.push([site.latitude, site.longitude])
  })

  if (bounds.length) {
    map.fitBounds(bounds, {
      padding: [40, 40],
      maxZoom: filteredSites.value.length <= 1 ? 14 : 11,
    })
  }
}

function selectFirstSiteIfNeeded() {
  if (!filteredSites.value.length) {
    selectedSite.value = null
    return
  }

  const stillVisible = filteredSites.value.find((site) => site.id === selectedSite.value?.id)
  if (!stillVisible) {
    selectedSite.value = filteredSites.value[0]
  }
}

function useMyLocation() {
  if (!navigator.geolocation) {
    error.value = 'Geolocation is not supported in this browser.'
    return
  }

  locatingUser.value = true
  error.value = ''

  navigator.geolocation.getCurrentPosition(
    (position) => {
      userLocation.value = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      }
      nearestOnly.value = true
      locatingUser.value = false
      nextTick(() => {
        selectFirstSiteIfNeeded()
        renderMarkers()
      })
    },
    (geoError) => {
      console.error(geoError)
      locatingUser.value = false
      error.value = 'Could not access your location. Please allow location access and try again.'
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0,
    },
  )
}

function clearNearestFilter() {
  nearestOnly.value = false
  userLocation.value = null
  nextTick(() => {
    selectFirstSiteIfNeeded()
    renderMarkers()
  })
}

function openNavigation(site) {
  if (!site) return
  const url = `https://www.google.com/maps/dir/?api=1&destination=${site.latitude},${site.longitude}`
  window.open(url, '_blank')
}

watch(filteredSites, async () => {
  selectFirstSiteIfNeeded()
  await nextTick()
  renderMarkers()
})

watch(selectedSite, async () => {
  await nextTick()
  renderMarkers()
})

onMounted(async () => {
  initMap()
  await fetchSites()
  await nextTick()
  selectFirstSiteIfNeeded()
  renderMarkers()
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="disposal-page">
    <section class="hero-section">
      <div class="hero-copy">
        <p class="page-tag">Disposal Locations</p>
        <h1>Find a Safe Place to Dispose of E-waste</h1>
        <p class="hero-text">
          Search by suburb, postcode, facility name, or address to find safe places where you can
          dispose of electronic waste responsibly.
        </p>
      </div>
    </section>

    <section class="search-panel">
      <div class="search-bar-card">
        <div class="search-grid">
          <div class="field-group search-field">
            <label for="searchQuery">Search location or facility</label>
            <input
              id="searchQuery"
              v-model="searchQuery"
              type="text"
              placeholder="Try Melbourne, 3000, Carlton, or facility name"
            />
          </div>

          <div class="field-group category-field">
            <label for="categoryFilter">Category</label>
            <select id="categoryFilter" v-model="selectedCategory">
              <option v-for="category in allowedCategories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </div>
        </div>

        <div class="action-row">
          <button class="action-btn primary" @click="useMyLocation" :disabled="locatingUser">
            {{ locatingUser ? 'Getting location...' : 'Use My Location' }}
          </button>

          <button
            v-if="nearestOnly"
            class="action-btn secondary"
            @click="clearNearestFilter"
          >
            Show All Locations
          </button>
        </div>

        <div class="search-meta">
          <span class="meta-pill">
            {{ visibleCount }} {{ nearestOnly ? 'nearest' : '' }} locations found
          </span>
          <span class="meta-note">Interactive map powered by OpenStreetMap</span>
        </div>
      </div>
    </section>

    <p v-if="loading" class="state-text">Loading disposal locations...</p>
    <p v-else-if="error" class="error-text">{{ error }}</p>

    <template v-else>
      <section class="content-grid">
        <div class="map-panel">
          <div class="panel-header">
            <div>
              <p class="panel-tag">Live Map</p>
              <h2>Explore nearby disposal points</h2>
            </div>
            <p>
              Click any marker to view more details about the location.
            </p>
          </div>

          <div ref="mapRef" class="actual-map"></div>
        </div>

        <div class="details-panel">
          <div class="panel-header small">
            <div>
              <p class="panel-tag">Selected Location</p>
              <h2>Location details</h2>
            </div>
          </div>

          <div v-if="selectedSite" class="details-card">
            <div class="site-badge-row">
              <span class="category-badge">{{ selectedSite.category }}</span>
              <span v-if="selectedSite.distanceKm !== null" class="distance-badge">
                {{ selectedSite.distanceKm.toFixed(2) }} km away
              </span>
            </div>

            <h3>{{ selectedSite.name }}</h3>

            <div class="detail-item">
              <span class="detail-label">Address</span>
              <p>{{ formatAddress(selectedSite) }}</p>
            </div>

            <div class="detail-item" v-if="selectedSite.accepted_items">
              <span class="detail-label">Accepted items</span>
              <p>{{ selectedSite.accepted_items }}</p>
            </div>

            <div class="detail-item" v-if="selectedSite.phone">
              <span class="detail-label">Phone</span>
              <p>{{ selectedSite.phone }}</p>
            </div>

            <div class="detail-item" v-if="selectedSite.website">
              <span class="detail-label">Website</span>
              <a :href="selectedSite.website" target="_blank" rel="noopener noreferrer">
                {{ selectedSite.website }}
              </a>
            </div>

            <div class="nav-action-row">
              <button class="navigate-btn" @click="openNavigation(selectedSite)">
                Navigate
              </button>
            </div>
          </div>

          <div v-else class="empty-card">
            <p>No matching disposal location found.</p>
          </div>
        </div>
      </section>

      <section class="results-section">
        <div class="panel-header small">
          <div>
            <p class="panel-tag">Available Locations</p>
            <h2>{{ nearestOnly ? 'Top 5 nearest results' : 'Browse all visible results' }}</h2>
          </div>
        </div>

        <div class="results-list">
          <button
            v-for="site in filteredSites"
            :key="site.id"
            class="result-card"
            :class="{ active: selectedSite?.id === site.id }"
            @click="selectedSite = site"
          >
            <div class="result-top">
              <h3>{{ site.name }}</h3>
              <span class="mini-badge">{{ site.category }}</span>
            </div>

            <p>{{ formatAddress(site) }}</p>

            <div class="result-bottom" v-if="site.distanceKm !== null">
              <span class="distance-text">{{ site.distanceKm.toFixed(2) }} km away</span>
              <span class="navigate-text">Tap to view</span>
            </div>
          </button>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.disposal-page {
  min-height: 100vh;
  padding: 32px;
  background:
    radial-gradient(circle at 86% 6%, rgba(129, 199, 132, 0.16), transparent 18%),
    radial-gradient(circle at 12% 90%, rgba(67, 160, 71, 0.10), transparent 22%),
    linear-gradient(180deg, #f8fbf8 0%, #eef4ef 100%);
  color: #173a29;
}

.hero-section {
  margin-bottom: 24px;
  padding: 36px 40px;
  border-radius: 32px;
  background:
    linear-gradient(135deg, rgba(244, 251, 244, 0.88) 0%, rgba(237, 247, 238, 0.84) 100%);
  border: 1px solid rgba(220, 235, 220, 0.96);
  box-shadow:
    0 18px 40px rgba(27, 67, 50, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(12px);
}

.page-tag,
.panel-tag {
  display: inline-flex;
  margin: 0 0 14px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(232, 245, 233, 0.9);
  border: 1px solid rgba(207, 232, 209, 0.98);
  color: #2e7d32;
  font-size: 13px;
  font-weight: 700;
}

.hero-copy h1 {
  margin: 0 0 14px;
  font-size: 52px;
  line-height: 1.02;
  font-weight: 800;
  letter-spacing: -1.2px;
  color: #143324;
  max-width: 900px;
}

.hero-text {
  margin: 0;
  max-width: 760px;
  font-size: 17px;
  line-height: 1.85;
  color: #557260;
}

.search-panel {
  margin-bottom: 24px;
}

.search-bar-card,
.map-panel,
.details-panel,
.results-section {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.76) 0%, rgba(251, 253, 251, 0.84) 100%);
  border: 1px solid rgba(226, 238, 227, 0.98);
  box-shadow:
    0 16px 32px rgba(27, 67, 50, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(14px);
  border-radius: 28px;
}

.search-bar-card {
  padding: 20px;
}

.search-grid {
  display: grid;
  grid-template-columns: 1.8fr 0.8fr;
  gap: 18px;
}

.field-group label {
  display: block;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #3f8f46;
}

.field-group input,
.field-group select {
  width: 100%;
  min-height: 54px;
  padding: 0 16px;
  border-radius: 18px;
  border: 1px solid rgba(210, 226, 213, 0.95);
  background: rgba(255, 255, 255, 0.9);
  color: #173a29;
  font-size: 15px;
  outline: none;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.action-btn,
.navigate-btn {
  min-height: 46px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    opacity 0.25s ease;
}

.action-btn:hover,
.navigate-btn:hover {
  transform: translateY(-2px);
}

.action-btn.primary,
.navigate-btn {
  background: #2e7d32;
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(46, 125, 50, 0.22);
}

.action-btn.secondary {
  background: rgba(236, 247, 237, 0.95);
  color: #2e7d32;
  border: 1px solid rgba(212, 236, 214, 0.98);
}

.action-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.search-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  gap: 12px;
}

.meta-pill {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(236, 247, 237, 0.9);
  border: 1px solid rgba(212, 236, 214, 0.98);
  color: #2e7d32;
  font-size: 13px;
  font-weight: 700;
}

.meta-note {
  font-size: 13px;
  color: #5f7967;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(340px, 0.75fr);
  gap: 20px;
  margin-bottom: 24px;
}

.map-panel,
.details-panel,
.results-section {
  padding: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  color: #173a29;
}

.panel-header p {
  margin: 0;
  max-width: 320px;
  color: #647f6d;
  font-size: 14px;
  line-height: 1.7;
}

.actual-map {
  height: 620px;
  border-radius: 24px;
  overflow: hidden;
  border: 1px solid rgba(218, 232, 220, 0.95);
}

.details-card,
.empty-card {
  padding: 20px;
  border-radius: 22px;
  background: rgba(245, 250, 246, 0.92);
  border: 1px solid rgba(220, 235, 222, 0.96);
}

.details-card h3 {
  margin: 0 0 18px;
  font-size: 28px;
  line-height: 1.2;
  color: #173a29;
}

.site-badge-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.category-badge,
.mini-badge,
.distance-badge {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(236, 247, 237, 0.95);
  border: 1px solid rgba(212, 236, 214, 0.98);
  color: #2e7d32;
  font-size: 12px;
  font-weight: 700;
}

.detail-item + .detail-item {
  margin-top: 16px;
}

.detail-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #5c7465;
}

.detail-item p,
.detail-item a,
.empty-card p {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: #557260;
  word-break: break-word;
}

.detail-item a {
  color: #2e7d32;
  text-decoration: none;
}

.nav-action-row {
  margin-top: 20px;
}

.results-list {
  display: grid;
  gap: 14px;
}

.result-card {
  text-align: left;
  width: 100%;
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid rgba(220, 235, 222, 0.96);
  background: rgba(245, 250, 246, 0.92);
  cursor: pointer;
  transition:
    transform 0.28s ease,
    box-shadow 0.28s ease,
    border-color 0.28s ease;
}

.result-card:hover,
.result-card.active {
  transform: translateY(-3px);
  border-color: rgba(129, 199, 132, 0.62);
  box-shadow:
    0 14px 28px rgba(27, 67, 50, 0.08),
    0 0 0 1px rgba(129, 199, 132, 0.12);
}

.result-top {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
  margin-bottom: 8px;
}

.result-card h3 {
  margin: 0;
  font-size: 20px;
  line-height: 1.25;
  color: #173a29;
}

.result-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #557260;
}

.result-bottom {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  gap: 10px;
}

.distance-text,
.navigate-text {
  font-size: 13px;
  font-weight: 700;
  color: #2e7d32;
}

.state-text,
.error-text {
  margin-top: 20px;
  font-size: 16px;
}

.state-text {
  color: #557260;
}

.error-text {
  color: #c62828;
  font-weight: 600;
}

:deep(.custom-marker-wrapper),
:deep(.custom-user-marker-wrapper) {
  background: transparent;
  border: none;
}

:deep(.custom-marker) {
  width: 24px;
  height: 24px;
  border-radius: 999px 999px 999px 0;
  transform: rotate(-45deg);
  background: #43a047;
  border: 2px solid #ffffff;
  box-shadow: 0 10px 20px rgba(27, 67, 50, 0.22);
  display: grid;
  place-items: center;
}

:deep(.custom-marker span) {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #ffffff;
  transform: rotate(45deg);
}

:deep(.custom-marker.selected) {
  background: #1b5e20;
  box-shadow: 0 12px 24px rgba(27, 94, 32, 0.35);
}

:deep(.custom-user-marker) {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #1565c0;
  border: 3px solid #ffffff;
  box-shadow: 0 0 0 8px rgba(21, 101, 192, 0.16);
  display: grid;
  place-items: center;
}

:deep(.custom-user-marker span) {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #ffffff;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .actual-map {
    height: 500px;
  }
}

@media (max-width: 900px) {
  .disposal-page {
    padding: 20px;
  }

  .hero-copy h1 {
    font-size: 40px;
  }

  .search-grid {
    grid-template-columns: 1fr;
  }

  .panel-header {
    flex-direction: column;
  }

  .panel-header p {
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .disposal-page {
    padding: 16px;
  }

  .hero-section,
  .search-bar-card,
  .map-panel,
  .details-panel,
  .results-section {
    padding: 20px;
  }

  .hero-copy h1 {
    font-size: 32px;
  }

  .actual-map {
    height: 380px;
  }

  .search-meta,
  .action-row,
  .result-bottom {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-top {
    flex-direction: column;
  }
}
</style>