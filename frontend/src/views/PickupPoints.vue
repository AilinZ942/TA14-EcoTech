<template>
  <div class="pp">
    <!-- HERO -->
    <section class="pp-hero">
      <div class="eco-shell hero-grid">
        <div class="hero-text">
          <span class="eco-eyebrow reveal">EcoReviva stalls</span>
          <h1 class="eco-display reveal reveal-delay-1">
            Buy reused.<br />
            <em>Sell what's still alive.</em>
          </h1>
          <p class="eco-lead reveal reveal-delay-2">
            38 stalls across Australia. Bring an old device, walk out with credit.
            Or pick up a refurbished one — checked, wiped, ready.
          </p>

          <div class="hero-modes reveal reveal-delay-3">
            <button
              v-for="m in modes"
              :key="m.id"
              class="mode-pill"
              :class="{ on: mode === m.id }"
              @click="mode = m.id"
            >
              <span class="mode-icon">{{ m.icon }}</span>
              {{ m.label }}
              <span class="mode-count">{{ m.id === 'browse' ? matchingDevices.length : visibleStalls.length }}</span>
            </button>
          </div>
        </div>

        <aside class="hero-stats reveal reveal-delay-4">
          <div class="stat">
            <span class="eco-mono">Stalls live</span>
            <strong>{{ stalls.length }}</strong>
          </div>
          <div class="stat">
            <span class="eco-mono">Devices listed</span>
            <strong>{{ totalDevices }}</strong>
          </div>
          <div class="stat">
            <span class="eco-mono">Coverage</span>
            <strong>8 states</strong>
          </div>
        </aside>
      </div>
    </section>

    <!-- SEARCH BAR -->
    <section v-if="mode !== 'sell'" class="search-section">
      <div class="eco-shell">
        <div class="search-card eco-glass">
          <div class="search-input">
            <span class="search-ic">⌕</span>
            <input
              v-model="searchTerm"
              type="search"
              :placeholder="searchPlaceholder"
            />
            <button v-if="searchTerm" class="clear" @click="searchTerm = ''" aria-label="Clear">×</button>
          </div>

          <div class="search-row">
            <div class="filter-block">
              <span class="eco-mono">Category</span>
              <div class="chips">
                <button :class="['chip', { on: !selectedCategory }]" @click="selectedCategory = ''">
                  All
                </button>
                <button
                  v-for="c in CATEGORIES"
                  :key="c.value"
                  :class="['chip', { on: selectedCategory === c.value }]"
                  @click="selectedCategory = selectedCategory === c.value ? '' : c.value"
                >
                  <span>{{ c.icon }}</span> {{ c.label }}
                </button>
              </div>
            </div>

            <div class="filter-block">
              <span class="eco-mono">Within</span>
              <div class="chips">
                <button
                  v-for="r in ranges"
                  :key="r.label"
                  :class="['chip', { on: rangeKm === r.value }]"
                  @click="rangeKm = r.value"
                >{{ r.label }}</button>
              </div>
            </div>
          </div>

          <p class="result-line">
            <strong>{{ resultCount }}</strong>
            {{ mode === 'browse' ? 'matching devices' : 'stalls' }}
            {{ rangeKm === Infinity ? 'across Australia' : 'within ' + rangeKm + ' km' }}
            <span v-if="searchTerm">for "{{ searchTerm }}"</span>
          </p>
        </div>
      </div>
    </section>

    <!-- LAYOUT -->
    <section class="layout-section">
      <div class="eco-shell layout">
        <!-- MAP -->
        <div class="map-card">
          <div v-if="!hasToken" class="map-placeholder">
            <div class="map-grid">
              <div v-for="n in 64" :key="n" class="cell" />
            </div>
            <div class="placeholder-msg">
              <span class="eco-mono">Stall map</span>
              <p>Set <code>VITE_MAPBOX_ACCESS_TOKEN</code> in <code>.env.local</code> for live map.</p>
            </div>
            <button
              v-for="(s, i) in visibleStalls.slice(0, 24)"
              :key="s.id"
              class="map-pin"
              :class="{ active: selectedStallId === s.id, focused: focusedStallId === s.id }"
              :style="pinStyle(s, i)"
              @click="selectStall(s.id)"
            >
              <span class="pin-num">{{ i + 1 }}</span>
            </button>
          </div>
          <div v-else ref="mapEl" class="map" />
          <div class="map-overlay">
            <div class="overlay-pill">
              <span class="ov-dot" />
              {{ visibleStalls.length }} live
            </div>
          </div>
        </div>

        <!-- RESULTS PANEL -->
        <aside class="panel">
          <!-- BROWSE -->
          <div v-if="mode === 'browse'" class="results">
            <div v-if="!matchingDevices.length" class="empty">
              <span>—</span>
              <h4>No devices match those filters</h4>
              <p>Try clearing a chip or widening the range.</p>
            </div>
            <article
              v-for="d in matchingDevices.slice(0, 50)"
              :key="d.id"
              class="device"
              :class="{ open: selectedDeviceId === d.id }"
              @click="selectDevice(d)"
            >
              <div class="device-row">
                <div class="device-icon">{{ categoryIcon(d.category) }}</div>
                <div class="device-info">
                  <h4>{{ d.brand }} {{ d.model }}</h4>
                  <span class="meta">
                    {{ d.condition }} · {{ d.year }}{{ d.storage ? ' · ' + d.storage : '' }}
                  </span>
                </div>
                <div class="device-price">
                  <strong>${{ d.price }}</strong>
                  <span>{{ d._distance }} km</span>
                </div>
              </div>
              <div class="stall-bar">
                <span class="stall-dot" />
                <span class="stall-loc">{{ d._stall.suburb }} · {{ d._stall.name }}</span>
                <span class="stall-state">{{ d._stall.state }}</span>
              </div>
              <transition name="expand">
                <div v-if="selectedDeviceId === d.id" class="device-actions">
                  <p class="addr">{{ d._stall.address }}, {{ d._stall.suburb }} {{ d._stall.postcode }}</p>
                  <div class="action-row">
                    <button class="eco-btn eco-btn--mint" @click.stop="goToStall(d._stall)">
                      Get directions <span class="arrow">→</span>
                    </button>
                    <button class="eco-btn eco-btn--ghost" @click.stop="reserveStub(d)">
                      Reserve
                    </button>
                  </div>
                </div>
              </transition>
            </article>
          </div>

          <!-- STALLS -->
          <div v-else-if="mode === 'stalls'" class="results">
            <div v-if="!visibleStalls.length" class="empty">
              <span>—</span>
              <h4>No stalls in range</h4>
              <p>Try widening the distance or selecting "All Australia".</p>
            </div>
            <article
              v-for="(s, i) in visibleStalls"
              :key="s.id"
              class="stall"
              :class="{ open: selectedStallId === s.id, focused: focusedStallId === s.id }"
              @click="selectStall(s.id)"
            >
              <header class="stall-head">
                <div class="stall-id">
                  <span class="stall-num">{{ String(i + 1).padStart(2, '0') }}</span>
                </div>
                <div class="stall-info">
                  <h4>{{ s.name }}</h4>
                  <p>{{ s.address }}, {{ s.suburb }} {{ s.postcode }}</p>
                </div>
                <span class="status" :class="s.open ? 'on' : 'off'">
                  <span class="ind" />
                  {{ s.open ? 'Open' : 'Closed' }}
                </span>
              </header>

              <div class="stall-stats">
                <div><span class="eco-mono">Distance</span><strong>{{ s._distance }} km</strong></div>
                <div><span class="eco-mono">Hours</span><strong>{{ s.hours }}</strong></div>
                <div><span class="eco-mono">Devices</span><strong>{{ s.inventory.length }}</strong></div>
              </div>

              <div class="inv-strip">
                <span
                  v-for="d in s.inventory.slice(0, 4)"
                  :key="d.id"
                  class="inv-tag"
                >
                  {{ categoryIcon(d.category) }} {{ d.brand }} {{ d.model }}
                </span>
                <span v-if="s.inventory.length > 4" class="inv-tag more">
                  +{{ s.inventory.length - 4 }}
                </span>
              </div>

              <transition name="expand">
                <div v-if="selectedStallId === s.id" class="stall-expand">
                  <h5>Full inventory</h5>
                  <div class="inv-grid">
                    <div v-for="d in s.inventory" :key="d.id" class="inv-card">
                      <span class="inv-icon">{{ categoryIcon(d.category) }}</span>
                      <div>
                        <strong>{{ d.brand }} {{ d.model }}</strong>
                        <span class="inv-meta">{{ d.condition }} · {{ d.year }}</span>
                      </div>
                      <span class="inv-price">${{ d.price }}</span>
                    </div>
                  </div>
                  <div class="action-row">
                    <button class="eco-btn eco-btn--mint" @click.stop="goToStall(s)">
                      Get directions <span class="arrow">→</span>
                    </button>
                    <a v-if="s.phone" :href="'tel:' + s.phone" class="eco-btn eco-btn--ghost" @click.stop>
                      Call {{ s.phone }}
                    </a>
                  </div>
                </div>
              </transition>
            </article>
          </div>

          <!-- SELL -->
          <div v-else class="sell-panel">
            <div class="sell-card eco-glass">
              <span class="eco-eyebrow">Sell to EcoReviva</span>
              <h3>Hand it over.<br />Walk out with credit.</h3>
              <p>Bring any working device to a stall. Our team checks it on the spot, wipes the data, and pays out in minutes.</p>

              <div class="accept-grid">
                <div v-for="a in accepts" :key="a.label" class="accept">
                  <span class="ac-icon">{{ a.icon }}</span>
                  <strong>{{ a.label }}</strong>
                  <span>{{ a.note }}</span>
                </div>
              </div>

              <div class="warn">
                <strong>⚠ Don't bring</strong>
                <span>swollen batteries, water-damaged units, or devices still signed in.</span>
              </div>
            </div>

            <div v-if="nearestStall" class="nearest-card">
              <span class="eco-mono">Nearest to you</span>
              <h3>{{ nearestStall.name }}</h3>
              <p class="addr">{{ nearestStall.address }}, {{ nearestStall.suburb }} {{ nearestStall.postcode }}</p>
              <div class="nearest-stats">
                <div><span class="eco-mono">Distance</span><strong>{{ nearestStall._distance }} km</strong></div>
                <div><span class="eco-mono">Hours</span><strong>{{ nearestStall.hours }}</strong></div>
                <div><span class="eco-mono">Phone</span><strong>{{ nearestStall.phone }}</strong></div>
              </div>
              <button class="eco-btn eco-btn--mint" @click="goToStall(nearestStall)">
                Get directions <span class="arrow">→</span>
              </button>
            </div>
          </div>
        </aside>
      </div>
    </section>

    <!-- IMPACT FOOTER -->
    <section class="impact reveal">
      <div class="eco-shell impact-grid">
        <div>
          <span class="eco-eyebrow">The bigger picture</span>
          <h2 class="eco-h2">
            Every device kept alive<br />
            <em>is a device unmined.</em>
          </h2>
          <p class="eco-lead">
            Reusing a phone saves ~80 kg of CO₂. A laptop saves ~300 kg. The cleanest material is the one already extracted.
          </p>
        </div>
        <div class="big-stats">
          <div><strong>80kg</strong><span>CO₂ saved per phone</span></div>
          <div><strong>300kg</strong><span>CO₂ saved per laptop</span></div>
          <div><strong>3g</strong><span>gold per discarded device</span></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { CATEGORIES, NETWORK_CENTER, haversineKm, stalls } from '@/lib/pickupStallsMock'
import { useReveal } from '@/composables/useReveal'

useReveal()

const mapboxToken = String(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '').trim()
const hasToken = computed(() => Boolean(mapboxToken))

const modes = [
  { id: 'browse', label: 'Browse devices', icon: '⌕' },
  { id: 'stalls', label: 'Find a stall', icon: '◉' },
  { id: 'sell', label: 'Sell a device', icon: '$' },
]

const accepts = [
  { icon: '📱', label: 'Phones', note: 'Any brand, 2017+' },
  { icon: '💻', label: 'Laptops', note: 'Working, charger included' },
  { icon: '📲', label: 'Tablets', note: 'iOS, Android, e-readers' },
  { icon: '🎧', label: 'Audio', note: 'Headphones, earbuds, speakers' },
  { icon: '🔌', label: 'Chargers', note: 'Sealed or tested' },
  { icon: '🖱️', label: 'Accessories', note: 'Mice, keyboards, webcams' },
]

const mode = ref('browse')
const searchTerm = ref('')
const selectedCategory = ref('')
const rangeKm = ref(50)
const ranges = [
  { value: 10, label: '10 km' },
  { value: 25, label: '25 km' },
  { value: 50, label: '50 km' },
  { value: 100, label: '100 km' },
  { value: 500, label: '500 km' },
  { value: Infinity, label: 'All Australia' },
]
const selectedStallId = ref('')
const selectedDeviceId = ref('')
const focusedStallId = ref('')
const userLocation = ref({ ...NETWORK_CENTER })

onMounted(() => {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(
    (pos) => { userLocation.value = { lat: pos.coords.latitude, lng: pos.coords.longitude } },
    () => {},
    { timeout: 3000 },
  )
})

const searchPlaceholder = computed(() =>
  mode.value === 'browse'
    ? 'Search a model — "Samsung S24", "iPhone", "MacBook"…'
    : 'Search a suburb or stall name',
)

const stallsWithDistance = computed(() =>
  stalls
    .map((s) => ({
      ...s,
      _distance: haversineKm(userLocation.value, { lat: s.lat, lng: s.lng }).toFixed(1),
      _distanceNum: haversineKm(userLocation.value, { lat: s.lat, lng: s.lng }),
    }))
    .sort((a, b) => a._distanceNum - b._distanceNum),
)

const visibleStalls = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  return stallsWithDistance.value.filter((s) => {
    if (s._distanceNum > rangeKm.value) return false
    if (mode.value === 'stalls' && term) {
      const hay = `${s.name} ${s.suburb} ${s.postcode} ${s.address}`.toLowerCase()
      const hit = s.inventory.some((d) => `${d.brand} ${d.model}`.toLowerCase().includes(term))
      if (!hay.includes(term) && !hit) return false
    }
    if (selectedCategory.value) {
      if (!s.inventory.some((d) => d.category === selectedCategory.value)) return false
    }
    return true
  })
})

const matchingDevices = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  const all = []
  for (const s of stallsWithDistance.value) {
    if (s._distanceNum > rangeKm.value) continue
    for (const d of s.inventory) {
      if (selectedCategory.value && d.category !== selectedCategory.value) continue
      if (term) {
        const hay = `${d.brand} ${d.model} ${d.category} ${d.color || ''}`.toLowerCase()
        if (!hay.includes(term)) continue
      }
      all.push({ ...d, _stall: s, _distance: s._distance, _distanceNum: s._distanceNum })
    }
  }
  return all.sort((a, b) => a._distanceNum - b._distanceNum)
})

const resultCount = computed(() =>
  mode.value === 'browse' ? matchingDevices.value.length : visibleStalls.value.length,
)
const totalDevices = computed(() => stalls.reduce((acc, s) => acc + s.inventory.length, 0))
const nearestStall = computed(() => stallsWithDistance.value[0] || null)

function categoryIcon(cat) {
  return CATEGORIES.find((c) => c.value === cat)?.icon || '·'
}

function selectStall(id) {
  selectedStallId.value = selectedStallId.value === id ? '' : id
  focusedStallId.value = id
  flyToStall(id)
  nextTick(() => {
    const el = document.querySelector('.stall.open')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

function selectDevice(d) {
  selectedDeviceId.value = selectedDeviceId.value === d.id ? '' : d.id
  focusedStallId.value = d._stall.id
  flyToStall(d._stall.id)
}

function goToStall(s) {
  const q = encodeURIComponent(`${s.address}, ${s.suburb} ${s.postcode} ${s.state}`)
  window.open(`https://www.google.com/maps/search/?api=1&query=${q}`, '_blank')
}

function reserveStub(d) {
  alert(
    `Reserve ${d.brand} ${d.model} at ${d._stall.name}.\n\n` +
    `In production this triggers a server-side hold. For now please call ${d._stall.phone || 'the stall'}.`,
  )
}

// === Mapbox (lazy) ===
const mapEl = ref(null)
let map = null
let markers = []
let userMarker = null

async function initMap() {
  if (!hasToken.value || !mapEl.value || map) return
  const mapboxgl = (await import('mapbox-gl')).default
  await import('mapbox-gl/dist/mapbox-gl.css')
  mapboxgl.accessToken = mapboxToken
  map = new mapboxgl.Map({
    container: mapEl.value,
    style: 'mapbox://styles/mapbox/dark-v11',
    center: [userLocation.value.lng, userLocation.value.lat],
    zoom: 11,
    attributionControl: false,
  })
  map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right')
  map.on('load', renderMarkers)
}

async function renderMarkers() {
  if (!map) return
  const mapboxgl = (await import('mapbox-gl')).default
  markers.forEach((m) => m.remove())
  markers = []
  for (const s of visibleStalls.value) {
    const el = document.createElement('div')
    el.className = 'eco-marker'
    if (focusedStallId.value === s.id) el.classList.add('focused')
    el.addEventListener('click', () => selectStall(s.id))
    const m = new mapboxgl.Marker({ element: el }).setLngLat([s.lng, s.lat]).addTo(map)
    markers.push(m)
  }
  if (userMarker) userMarker.remove()
  const me = document.createElement('div')
  me.className = 'eco-me'
  userMarker = new mapboxgl.Marker({ element: me })
    .setLngLat([userLocation.value.lng, userLocation.value.lat])
    .addTo(map)
}

function flyToStall(id) {
  if (!map) return
  const s = stalls.find((x) => x.id === id)
  if (!s) return
  map.flyTo({ center: [s.lng, s.lat], zoom: 13.5, essential: true, duration: 1200 })
}

onMounted(() => { initMap() })
onBeforeUnmount(() => { if (map) { map.remove(); map = null } })
watch([visibleStalls, focusedStallId], () => { renderMarkers() })
watch(userLocation, () => {
  if (map) map.flyTo({ center: [userLocation.value.lng, userLocation.value.lat], zoom: 11, essential: true })
})

// Placeholder pin geometry
const pinPositions = computed(() => {
  const cols = 6
  return visibleStalls.value.slice(0, 24).map((_, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    return { left: 10 + col * 14, top: 16 + row * 17 }
  })
})

function pinStyle(_s, i) {
  const p = pinPositions.value[i] || { left: 50, top: 50 }
  return { left: p.left + '%', top: p.top + '%' }
}
</script>

<style scoped>
.pp { padding-top: 100px; padding-bottom: 0; min-height: 100vh; }

/* HERO */
.pp-hero { padding: 80px 0 60px; }
.hero-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 60px;
  align-items: end;
}
.hero-text { display: flex; flex-direction: column; gap: 24px; }
.hero-text h1 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

.hero-modes { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.mode-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
  color: var(--ink-1);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
}
.mode-pill:hover { border-color: var(--mint); color: var(--ink-0); }
.mode-pill.on {
  background: var(--mint);
  color: var(--ink-on-light);
  border-color: var(--mint);
  box-shadow: 0 8px 24px rgba(125, 216, 176, 0.3);
}
.mode-icon { font-size: 16px; }
.mode-count {
  margin-left: 4px;
  padding: 2px 8px;
  background: rgba(0,0,0,0.18);
  border-radius: var(--r-pill);
  font-family: var(--font-mono);
  font-size: 11px;
}
.mode-pill.on .mode-count { background: rgba(0,0,0,0.18); }
.mode-pill:not(.on) .mode-count { background: var(--hairline); color: var(--ink-2); }

.hero-stats {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  border-left: 1px solid var(--hairline);
  padding-left: 32px;
}
.hero-stats .stat {
  padding: 20px 0;
  border-bottom: 1px solid var(--hairline);
  display: flex; flex-direction: column; gap: 6px;
}
.hero-stats .stat:last-child { border-bottom: 0; }
.hero-stats .stat strong {
  font-family: var(--font-display);
  font-size: clamp(36px, 5vw, 56px);
  font-weight: 500;
  letter-spacing: -0.04em;
  color: var(--mint);
  line-height: 1;
}

/* SEARCH */
.search-section { padding: 0 0 40px; }
.search-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.search-input {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 16px;
  background: rgba(0,0,0,0.25);
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
  transition: border-color 0.3s, box-shadow 0.3s;
}
.search-input:focus-within {
  border-color: var(--mint);
  box-shadow: 0 0 0 4px rgba(125, 216, 176, 0.12);
}
.search-ic { color: var(--mint); font-size: 18px; }
.search-input input {
  flex: 1;
  background: transparent;
  border: 0;
  outline: 0;
  color: var(--ink-0);
  font-size: 15px;
  padding: 12px 0;
  font-family: var(--font-body);
}
.search-input input::placeholder { color: var(--ink-3); }
.clear {
  background: var(--hairline);
  color: var(--ink-1);
  border: 0;
  width: 26px; height: 26px;
  border-radius: 50%;
  font-size: 18px; line-height: 1;
  cursor: pointer;
  transition: all 0.2s;
}
.clear:hover { background: var(--bad); color: white; }

.search-row { display: flex; gap: 32px; flex-wrap: wrap; }
.filter-block { display: flex; flex-direction: column; gap: 8px; flex: 1; min-width: 220px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
.chip.on {
  background: var(--mint);
  color: var(--ink-on-light);
  border-color: var(--mint);
}

.result-line { color: var(--ink-2); font-size: 13px; margin: 0; }
.result-line strong { color: var(--mint); font-family: var(--font-mono); margin-right: 4px; }

/* LAYOUT */
.layout-section { padding-bottom: 80px; }
.layout {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
  align-items: start;
}

/* MAP */
.map-card {
  position: sticky;
  top: 100px;
  height: 700px;
  background: var(--bg-1);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  overflow: hidden;
  position: relative;
}
.map { width: 100%; height: 100%; }
.map-overlay {
  position: absolute;
  top: 18px; left: 18px;
  z-index: 5;
  pointer-events: none;
}
.overlay-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
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
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 0 3px rgba(125, 216, 176, 0.2); }
  50% { box-shadow: 0 0 0 8px rgba(125, 216, 176, 0); }
}

.map-placeholder {
  position: relative;
  width: 100%; height: 100%;
  background: linear-gradient(135deg, #0E2620, #061511);
}
.map-grid {
  position: absolute; inset: 0;
  display: grid; grid-template-columns: repeat(8, 1fr);
}
.map-grid .cell {
  border-right: 1px solid rgba(125, 216, 176, 0.05);
  border-bottom: 1px solid rgba(125, 216, 176, 0.05);
}
.placeholder-msg {
  position: absolute; bottom: 20px; left: 20px;
  background: rgba(6, 18, 15, 0.92);
  border: 1px solid var(--hairline);
  padding: 12px 16px;
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 4px;
  max-width: 320px;
}
.placeholder-msg p { color: var(--ink-2); font-size: 12px; }
.placeholder-msg code { background: rgba(125,216,176,0.12); color: var(--mint); padding: 1px 6px; border-radius: 4px; font-size: 11px; }

.map-pin {
  position: absolute;
  width: 32px; height: 38px;
  background: transparent;
  border: 0;
  cursor: pointer;
  transform: translate(-50%, -100%);
  transition: transform 0.3s var(--ease-out);
}
.map-pin::before {
  content: '';
  position: absolute;
  inset: 0 0 6px 0;
  background: var(--mint);
  border-radius: 16px 16px 16px 4px;
  transform: rotate(-45deg);
  box-shadow: 0 6px 16px rgba(125, 216, 176, 0.45);
}
.pin-num {
  position: relative;
  display: grid; place-items: center;
  width: 26px; height: 26px;
  margin: 4px auto;
  color: var(--ink-on-light);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
}
.map-pin:hover { transform: translate(-50%, -100%) scale(1.1); }
.map-pin.focused::before, .map-pin.active::before {
  background: var(--peach);
  box-shadow: 0 6px 16px rgba(244, 162, 97, 0.5), 0 0 0 4px rgba(244, 162, 97, 0.18);
}

/* PANEL */
.panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 700px;
  overflow-y: auto;
  padding-right: 4px;
  scroll-behavior: smooth;
}

.empty {
  text-align: center;
  padding: 80px 30px;
  background: var(--surface);
  border: 1px dashed var(--hairline-strong);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 8px; align-items: center;
}
.empty span { font-size: 36px; color: var(--ink-3); }
.empty h4 { font-family: var(--font-display); font-size: 18px; font-weight: 500; }
.empty p { color: var(--ink-2); font-size: 14px; }

/* DEVICE CARD */
.device {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  padding: 18px;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
}
.device:hover {
  border-color: var(--mint);
  background: rgba(125, 216, 176, 0.04);
  transform: translateY(-2px);
}
.device.open {
  border-color: var(--mint);
  background: rgba(125, 216, 176, 0.06);
  box-shadow: 0 16px 40px rgba(0,0,0,0.25);
}

.device-row {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 16px;
  align-items: center;
}
.device-icon {
  width: 56px; height: 56px;
  display: grid; place-items: center;
  background: rgba(125, 216, 176, 0.10);
  border: 1px solid rgba(125, 216, 176, 0.25);
  border-radius: var(--r-sm);
  font-size: 26px;
}
.device-info h4 {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 500;
  margin-bottom: 4px;
}
.device-info .meta { color: var(--ink-2); font-size: 12px; }
.device-price { text-align: right; display: flex; flex-direction: column; gap: 2px; }
.device-price strong {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--mint);
  font-weight: 500;
  letter-spacing: -0.02em;
}
.device-price span { font-family: var(--font-mono); font-size: 11px; color: var(--ink-2); }

.stall-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--hairline);
  font-size: 12px;
  color: var(--ink-2);
}
.stall-dot {
  width: 6px; height: 6px;
  background: var(--mint);
  border-radius: 50%;
}
.stall-loc { color: var(--ink-1); }
.stall-state {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.16em;
  color: var(--ink-2);
  padding: 2px 8px;
  background: var(--hairline);
  border-radius: var(--r-pill);
}

.device-actions, .stall-expand {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--hairline);
  display: flex; flex-direction: column; gap: 14px;
}
.addr { color: var(--ink-2); font-size: 13px; }
.action-row { display: flex; flex-wrap: wrap; gap: 8px; }

/* STALL CARD */
.stall {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  padding: 22px;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
}
.stall:hover { border-color: var(--mint); background: rgba(125, 216, 176, 0.04); transform: translateY(-2px); }
.stall.open, .stall.focused { border-color: var(--mint); background: rgba(125, 216, 176, 0.06); box-shadow: 0 16px 40px rgba(0,0,0,0.25); }

.stall-head {
  display: grid;
  grid-template-columns: 50px 1fr auto;
  gap: 14px;
  align-items: flex-start;
}
.stall-num {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  color: var(--mint);
  padding: 4px 10px;
  background: rgba(125, 216, 176, 0.12);
  border-radius: var(--r-pill);
  display: inline-block;
}
.stall-info h4 { font-family: var(--font-display); font-size: 18px; font-weight: 500; margin-bottom: 4px; }
.stall-info p { color: var(--ink-2); font-size: 13px; }

.status {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 600;
  padding: 5px 10px;
  border-radius: var(--r-pill);
  font-family: var(--font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.status.on { background: rgba(125, 216, 176, 0.18); color: var(--mint); }
.status.off { background: rgba(248, 113, 113, 0.18); color: var(--bad); }
.ind { width: 6px; height: 6px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }

.stall-stats {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 14px;
  background: rgba(0,0,0,0.18);
  border: 1px solid var(--hairline);
  border-radius: var(--r-sm);
}
.stall-stats > div { display: flex; flex-direction: column; gap: 4px; }
.stall-stats strong { font-family: var(--font-display); font-size: 14px; }

.inv-strip { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }
.inv-tag {
  font-size: 11px;
  padding: 5px 10px;
  background: rgba(125, 216, 176, 0.10);
  color: var(--mint);
  border: 1px solid rgba(125, 216, 176, 0.22);
  border-radius: var(--r-pill);
  font-weight: 500;
}
.inv-tag.more { background: var(--hairline); color: var(--ink-2); border-color: transparent; }

.stall-expand h5 { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.18em; color: var(--mint); text-transform: uppercase; }

.inv-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.inv-card {
  display: grid;
  grid-template-columns: 32px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--hairline);
  border-radius: var(--r-sm);
}
.inv-icon { font-size: 22px; }
.inv-card strong { display: block; font-family: var(--font-display); font-size: 13px; font-weight: 500; }
.inv-meta { font-size: 11px; color: var(--ink-2); }
.inv-price { font-family: var(--font-mono); font-size: 13px; color: var(--mint); }

/* SELL */
.sell-panel { display: flex; flex-direction: column; gap: 14px; }
.sell-card, .nearest-card {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  padding: 32px;
  display: flex; flex-direction: column; gap: 18px;
}
.sell-card h3 {
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.05;
  font-weight: 500;
  letter-spacing: -0.03em;
  color: var(--ink-0);
}
.sell-card p { color: var(--ink-1); }

.accept-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 8px;
}
.accept {
  display: grid;
  grid-template-columns: 36px 1fr;
  grid-template-rows: auto auto;
  column-gap: 12px;
  padding: 14px;
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--hairline);
  border-radius: var(--r-sm);
}
.ac-icon {
  grid-row: 1 / 3;
  font-size: 22px;
  display: grid; place-items: center;
}
.accept strong { font-family: var(--font-display); font-size: 14px; font-weight: 500; }
.accept span { color: var(--ink-2); font-size: 12px; }

.warn {
  margin-top: 8px;
  padding: 14px 16px;
  background: rgba(244, 162, 97, 0.10);
  border: 1px solid rgba(244, 162, 97, 0.3);
  border-radius: var(--r-sm);
  color: var(--ink-1);
  font-size: 13px;
}
.warn strong { color: var(--peach); display: block; margin-bottom: 2px; }

.nearest-card {
  background: linear-gradient(135deg, rgba(125, 216, 176, 0.08), transparent);
  border-color: rgba(125, 216, 176, 0.3);
}
.nearest-card h3 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 500;
}
.nearest-card .addr { color: var(--ink-1); font-size: 14px; }
.nearest-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding: 14px;
  background: rgba(0,0,0,0.2);
  border-radius: var(--r-sm);
}
.nearest-stats > div { display: flex; flex-direction: column; gap: 4px; }
.nearest-stats strong { font-family: var(--font-display); font-size: 13px; }

/* IMPACT */
.impact { padding: 100px 0 0; }
.impact-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 60px;
  align-items: center;
}
.impact h2 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.big-stats {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
}
.big-stats > div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 20px 0;
  border-top: 1px solid var(--hairline);
}
.big-stats > div:last-child { border-bottom: 1px solid var(--hairline); }
.big-stats strong {
  font-family: var(--font-display);
  font-size: clamp(36px, 5vw, 56px);
  font-weight: 500;
  letter-spacing: -0.04em;
  color: var(--mint);
  line-height: 1;
}
.big-stats span { color: var(--ink-2); font-size: 13px; }

/* TRANSITIONS */
.expand-enter-active, .expand-leave-active {
  transition: max-height 0.4s var(--ease-out), opacity 0.4s, padding 0.4s;
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; padding-top: 0; padding-bottom: 0; }
.expand-enter-to, .expand-leave-from { max-height: 800px; opacity: 1; }

/* RESPONSIVE */
@media (max-width: 1024px) {
  .layout { grid-template-columns: 1fr; }
  .map-card { position: relative; top: 0; height: 400px; }
  .panel { max-height: none; }
  .hero-grid { grid-template-columns: 1fr; gap: 32px; align-items: stretch; }
  .hero-stats { border-left: 0; padding-left: 0; border-top: 1px solid var(--hairline); padding-top: 16px; }
  .impact-grid { grid-template-columns: 1fr; gap: 40px; }
}
@media (max-width: 600px) {
  .stall-stats { grid-template-columns: 1fr; }
  .nearest-stats { grid-template-columns: 1fr; }
  .accept-grid { grid-template-columns: 1fr; }
  .inv-grid { grid-template-columns: 1fr; }
  .device-row { grid-template-columns: 48px 1fr; }
  .device-price { grid-column: 1 / -1; flex-direction: row; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid var(--hairline); margin-top: 6px; }
  .sell-card, .nearest-card { padding: 22px; }
}

/* Mapbox markers */
:deep(.eco-marker) {
  width: 22px; height: 28px;
  background: var(--mint);
  border-radius: 11px 11px 11px 3px;
  transform: rotate(-45deg);
  box-shadow: 0 4px 14px rgba(125, 216, 176, 0.5);
  cursor: pointer;
  transition: transform 0.2s var(--ease-out);
}
:deep(.eco-marker:hover) { transform: rotate(-45deg) scale(1.15); }
:deep(.eco-marker.focused) {
  background: var(--peach);
  box-shadow: 0 4px 14px rgba(244, 162, 97, 0.55), 0 0 0 4px rgba(244, 162, 97, 0.2);
}
:deep(.eco-me) {
  width: 14px; height: 14px;
  background: var(--violet);
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.3);
}
:deep(.mapboxgl-ctrl) {
  background: rgba(6, 18, 15, 0.85) !important;
  border: 1px solid var(--hairline) !important;
}
:deep(.mapboxgl-ctrl button) { color: var(--ink-0) !important; }
</style>
