<template>
  <section class="pickup-page">
    <!-- Hero -->
    <header class="hero">
      <div class="hero-inner">
        <span class="eyebrow">Pickup Points</span>
        <h1>EcoReviva stalls near you.</h1>
        <p class="lead">
          Drop off a working device at a stall, or pick up a refurbished one. Every reused device
          keeps materials in use and out of landfill.
        </p>

        <div class="mode-tabs">
          <button
            v-for="m in modes"
            :key="m.id"
            :class="['tab', { on: mode === m.id }]"
            @click="mode = m.id"
          >
            <span class="tab-icon">{{ m.icon }}</span>
            {{ m.label }}
          </button>
        </div>
      </div>
    </header>

    <!-- Buyer modes: search & filter -->
    <section v-if="mode !== 'sell'" class="controls">
      <div class="search-bar">
        <span class="ic">🔍</span>
        <input
          v-model="searchTerm"
          type="search"
          :placeholder="searchPlaceholder"
        />
        <button v-if="searchTerm" class="clear" @click="searchTerm = ''" aria-label="Clear">×</button>
      </div>

      <div class="filter-row">
        <div class="filter-group">
          <span class="lbl">Category</span>
          <div class="chips">
            <button
              :class="['chip', { on: !selectedCategory }]"
              @click="selectedCategory = ''"
            >All</button>
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

        <div class="filter-group">
          <span class="lbl">Within</span>
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
    </section>

    <!-- Map + main panel -->
    <section class="layout">
      <!-- Map -->
      <div class="map-card">
        <div v-if="!hasToken" class="map-placeholder">
          <div class="map-grid">
            <div v-for="n in 64" :key="n" class="cell" />
          </div>
          <div class="placeholder-msg">
            <strong>Stall map</strong>
            <span>Set <code>VITE_MAPBOX_ACCESS_TOKEN</code> for live map. {{ visibleStalls.length }} stalls shown below.</span>
          </div>
          <span class="user-pin" title="You" :style="userPinStyle">●</span>
          <button
            v-for="(s, i) in visibleStalls.slice(0, 24)"
            :key="s.id"
            class="map-pin"
            :class="{ active: selectedStallId === s.id, focused: focusedStallId === s.id }"
            :style="pinStyle(s, i)"
            @click="selectStall(s.id)"
          >
            <strong>{{ i + 1 }}</strong>
          </button>
        </div>
        <div v-else ref="mapEl" class="map" />
      </div>

      <!-- Right panel -->
      <aside class="panel">
        <!-- BROWSE mode -->
        <div v-if="mode === 'browse'" class="results">
          <h3 class="panel-title">Available devices</h3>
          <div v-if="!matchingDevices.length" class="empty">
            <span>📦</span>
            <p>No devices match that. Try clearing filters or widening the range.</p>
          </div>
          <article
            v-for="d in matchingDevices"
            :key="d.id"
            class="device-card"
            :class="{ open: selectedDeviceId === d.id }"
            @click="selectDevice(d)"
          >
            <div class="device-row">
              <div class="device-icon" :data-cat="d.category">{{ categoryIcon(d.category) }}</div>
              <div class="device-info">
                <h4>{{ d.brand }} {{ d.model }}</h4>
                <span class="meta">
                  {{ d.condition }} · {{ d.year }}{{ d.storage ? ' · ' + d.storage : '' }}
                </span>
              </div>
              <div class="device-price">
                <strong>${{ d.price }}</strong>
              </div>
            </div>
            <div class="stall-line">
              <span class="dot" />
              At <strong>{{ d._stall.name }}</strong> · {{ d._distance }} km
            </div>
            <transition name="expand">
              <div v-if="selectedDeviceId === d.id" class="device-actions">
                <p class="stall-addr">{{ d._stall.address }}, {{ d._stall.suburb }} {{ d._stall.postcode }}</p>
                <button class="btn primary" @click.stop="goToStall(d._stall)">
                  Get directions →
                </button>
                <button class="btn ghost" @click.stop="reserveStub(d)">
                  Reserve at stall
                </button>
              </div>
            </transition>
          </article>
        </div>

        <!-- STALL mode -->
        <div v-else-if="mode === 'stalls'" class="results">
          <h3 class="panel-title">Stalls near you</h3>
          <div v-if="!visibleStalls.length" class="empty">
            <span>📍</span>
            <p>No stalls within range. Try increasing the distance.</p>
          </div>
          <article
            v-for="(s, i) in visibleStalls"
            :key="s.id"
            class="stall-card"
            :class="{ open: selectedStallId === s.id, focused: focusedStallId === s.id }"
            @click="selectStall(s.id)"
          >
            <header class="stall-head">
              <div>
                <h4>
                  <span class="pill">{{ i + 1 }}</span>
                  {{ s.name }}
                </h4>
                <p class="meta">{{ s.address }}, {{ s.suburb }} {{ s.postcode }}</p>
              </div>
              <span :class="['status', s.open ? 'on' : 'off']">
                <span class="ind" />
                {{ s.open ? 'Open' : 'Closed' }}
              </span>
            </header>

            <div class="stall-meta">
              <div><span class="ml">Distance</span><strong>{{ s._distance }} km</strong></div>
              <div><span class="ml">Hours</span><strong>{{ s.hours }}</strong></div>
              <div><span class="ml">Devices</span><strong>{{ s.inventory.length }}</strong></div>
            </div>

            <div class="inv-chips">
              <span
                v-for="d in s.inventory.slice(0, 5)"
                :key="d.id"
                class="inv-chip"
              >
                {{ categoryIcon(d.category) }} {{ d.brand }} {{ d.model }} · ${{ d.price }}
              </span>
              <span v-if="s.inventory.length > 5" class="inv-chip more">
                +{{ s.inventory.length - 5 }} more
              </span>
            </div>

            <transition name="expand">
              <div v-if="selectedStallId === s.id" class="stall-expand">
                <h5>Full inventory</h5>
                <div class="inv-grid">
                  <div v-for="d in s.inventory" :key="d.id" class="inv-card">
                    <span class="inv-icon">{{ categoryIcon(d.category) }}</span>
                    <strong>{{ d.brand }} {{ d.model }}</strong>
                    <span class="inv-meta">{{ d.condition }} · {{ d.year }}</span>
                    <span class="inv-price">${{ d.price }}</span>
                  </div>
                </div>
                <div class="stall-actions">
                  <button class="btn primary" @click.stop="goToStall(s)">Get directions →</button>
                  <a v-if="s.phone" :href="'tel:' + s.phone" class="btn ghost" @click.stop>Call {{ s.phone }}</a>
                </div>
              </div>
            </transition>
          </article>
        </div>

        <!-- SELL mode -->
        <div v-else class="sell-panel">
          <div class="sell-card">
            <span class="eyebrow">Sell to EcoReviva</span>
            <h3>Hand over a device, earn store credit.</h3>
            <p>Drop off any working phone, laptop, tablet, or accessory at your nearest stall. Our team checks it on the spot.</p>
            <h5>What we accept</h5>
            <ul class="accept">
              <li><span>📱</span> Phones (any brand, 2017+)</li>
              <li><span>💻</span> Laptops (working, charger included)</li>
              <li><span>📲</span> Tablets and e-readers</li>
              <li><span>🎧</span> Audio gear in working condition</li>
              <li><span>🔌</span> Chargers and cables (sealed or tested)</li>
            </ul>
            <p class="note">No swollen batteries, water damage, or accounts still signed in.</p>
          </div>

          <div v-if="nearestStall" class="nearest-card">
            <span class="eyebrow">Nearest stall</span>
            <h3>{{ nearestStall.name }}</h3>
            <p class="addr">{{ nearestStall.address }}, {{ nearestStall.suburb }} {{ nearestStall.postcode }}</p>
            <div class="nearest-meta">
              <div><span>Distance</span><strong>{{ nearestStall._distance }} km</strong></div>
              <div><span>Hours</span><strong>{{ nearestStall.hours }}</strong></div>
              <div><span>Phone</span><strong>{{ nearestStall.phone }}</strong></div>
            </div>
            <button class="btn primary big" @click="goToStall(nearestStall)">Get directions →</button>
          </div>
        </div>
      </aside>
    </section>

    <!-- Impact card -->
    <section class="impact">
      <div class="impact-inner">
        <div>
          <span class="eyebrow">Why this matters</span>
          <h2>Every reused device reduces e-waste and keeps resources in use.</h2>
          <p>Reusing a single phone avoids ~80 kg CO₂. A laptop avoids ~300 kg. Pickup stalls keep working tech in circulation across Victoria.</p>
        </div>
        <div class="impact-stats">
          <div><strong>{{ stalls.length }}</strong><span>EcoReviva stalls</span></div>
          <div><strong>{{ totalDevices }}</strong><span>Devices listed</span></div>
          <div><strong>4.6★</strong><span>Avg rating</span></div>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { CATEGORIES, NETWORK_CENTER, haversineKm, stalls } from '@/lib/pickupStallsMock'

const mapboxToken = String(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '').trim()
const hasToken = computed(() => Boolean(mapboxToken))

// State
const modes = [
  { id: 'browse', label: 'Browse devices', icon: '🛒' },
  { id: 'stalls', label: 'Find a stall', icon: '📍' },
  { id: 'sell', label: 'Sell a device', icon: '💰' },
]
const mode = ref('browse')
const searchTerm = ref('')
const selectedCategory = ref('')
const rangeKm = ref(50)
// `Infinity` = all Australia. Stalls span every state, so users outside Melbourne
// need a wider net to find their nearest one.
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

// Try real geolocation, fall back to network centre
onMounted(() => {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(
    (pos) => { userLocation.value = { lat: pos.coords.latitude, lng: pos.coords.longitude } },
    () => {}, // silently keep default
    { timeout: 3000 },
  )
})

const searchPlaceholder = computed(() =>
  mode.value === 'browse'
    ? 'Search a device — e.g. "Samsung S24", "iPhone", "MacBook"'
    : 'Search a suburb or stall name',
)

// Pre-compute distances and flatten devices
const stallsWithDistance = computed(() =>
  stalls
    .map((s) => ({
      ...s,
      _distance: haversineKm(userLocation.value, { lat: s.lat, lng: s.lng }).toFixed(1),
      _distanceNum: haversineKm(userLocation.value, { lat: s.lat, lng: s.lng }),
    }))
    .sort((a, b) => a._distanceNum - b._distanceNum),
)

// Stalls visible after range + search filter (stalls mode)
const visibleStalls = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  return stallsWithDistance.value.filter((s) => {
    if (s._distanceNum > rangeKm.value) return false
    if (mode.value === 'stalls' && term) {
      const hay = `${s.name} ${s.suburb} ${s.postcode} ${s.address}`.toLowerCase()
      const invHit = s.inventory.some(
        (d) => `${d.brand} ${d.model}`.toLowerCase().includes(term),
      )
      if (!hay.includes(term) && !invHit) return false
    }
    // category filter applies in stalls mode too — stall must have at least one matching device
    if (selectedCategory.value) {
      if (!s.inventory.some((d) => d.category === selectedCategory.value)) return false
    }
    return true
  })
})

// All devices, flattened and filtered (browse mode)
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
  return CATEGORIES.find((c) => c.value === cat)?.icon || '✦'
}

function selectStall(id) {
  selectedStallId.value = selectedStallId.value === id ? '' : id
  focusedStallId.value = id
  flyToStall(id)
  // Bring the card into view
  nextTick(() => {
    const el = document.querySelector(`.stall-card.open`)
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
    `In the live version this will trigger a server-side hold.\n` +
    `For now please call ${d._stall.phone || 'the stall'} to confirm.`,
  )
}

// === Mapbox (lazy) ===
const mapEl = ref(null)
let map = null
let markers = []

async function initMap() {
  if (!hasToken.value || !mapEl.value || map) return
  const mapboxgl = (await import('mapbox-gl')).default
  await import('mapbox-gl/dist/mapbox-gl.css')
  mapboxgl.accessToken = mapboxToken
  map = new mapboxgl.Map({
    container: mapEl.value,
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [userLocation.value.lng, userLocation.value.lat],
    zoom: 11,
  })
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
  // user marker
  const me = document.createElement('div')
  me.className = 'eco-me'
  new mapboxgl.Marker({ element: me }).setLngLat([userLocation.value.lng, userLocation.value.lat]).addTo(map)
}

function flyToStall(id) {
  if (!map) return
  const s = stalls.find((x) => x.id === id)
  if (!s) return
  map.flyTo({ center: [s.lng, s.lat], zoom: 13.5, essential: true })
}

onMounted(() => { initMap() })
onBeforeUnmount(() => { if (map) { map.remove(); map = null } })
watch([visibleStalls, focusedStallId], () => { renderMarkers() })

// === Placeholder pin geometry (no Mapbox token) ===
const pinPositions = computed(() => {
  const cols = 6
  return visibleStalls.value.slice(0, 24).map((s, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    return { left: 10 + col * 14, top: 16 + row * 17 }
  })
})

function pinStyle(_s, i) {
  const p = pinPositions.value[i] || { left: 50, top: 50 }
  return { left: p.left + '%', top: p.top + '%' }
}

const userPinStyle = computed(() => ({ left: '50%', top: '88%' }))
</script>

<style scoped>
/* Match the existing minty EcoReviva palette */
.pickup-page {
  --green-900: #1b4332;
  --green-700: #2d6a4f;
  --green-500: #40916c;
  --green-300: #95d5b2;
  --green-100: #d8f3dc;
  --mint: #52b788;
  --ink: #1f2937;
  --muted: #475569;
  --bg-soft: #f4faf5;
  background: linear-gradient(180deg, #f7fbf8 0%, #eef7f1 100%);
  min-height: calc(100vh - 92px);
  padding-bottom: 60px;
  color: var(--ink);
}

/* HERO */
.hero {
  position: relative;
  padding: 64px 24px 32px;
  background:
    radial-gradient(ellipse at top left, rgba(82, 183, 136, 0.18), transparent 50%),
    radial-gradient(ellipse at top right, rgba(64, 145, 108, 0.18), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, transparent 100%);
  overflow: hidden;
}
.hero::before, .hero::after {
  content: '';
  position: absolute;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  pointer-events: none;
}
.hero::before { top: -120px; left: -100px; background: var(--mint); }
.hero::after { top: -120px; right: -100px; background: var(--green-500); }
.hero-inner {
  position: relative;
  max-width: 1200px;
  margin: 0 auto;
  display: flex; flex-direction: column; gap: 12px; align-items: center; text-align: center;
}
.eyebrow {
  display: inline-block;
  font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase;
  padding: 6px 14px; border-radius: 999px;
  background: rgba(45, 106, 79, 0.1);
  color: var(--green-700);
  border: 1px solid rgba(45, 106, 79, 0.18);
  font-weight: 700;
}
.hero h1 {
  font-size: clamp(32px, 5vw, 48px);
  margin: 0;
  color: var(--green-900);
  letter-spacing: -0.02em;
}
.lead { color: var(--muted); max-width: 600px; line-height: 1.6; font-size: 16px; margin: 0; }

.mode-tabs {
  display: flex; gap: 6px; padding: 6px;
  background: #ffffff;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  margin-top: 16px;
  box-shadow: 0 10px 30px rgba(45, 106, 79, 0.08);
  flex-wrap: wrap;
  justify-content: center;
}
.tab {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 18px;
  border: 0; cursor: pointer;
  background: transparent;
  border-radius: 999px;
  color: var(--muted);
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s ease;
}
.tab:hover { background: var(--green-100); color: var(--green-700); }
.tab.on {
  background: linear-gradient(135deg, var(--green-500), var(--green-700));
  color: #ffffff;
  box-shadow: 0 8px 20px rgba(45, 106, 79, 0.3);
}
.tab-icon { font-size: 16px; }

/* CONTROLS */
.controls {
  max-width: 1200px; margin: 24px auto 16px;
  padding: 20px 24px;
  background: #ffffff;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 10px 40px rgba(45, 106, 79, 0.06);
  display: flex; flex-direction: column; gap: 14px;
}
.search-bar {
  position: relative;
  display: flex; align-items: center; gap: 12px;
  padding: 6px 16px;
  background: var(--bg-soft);
  border: 1.5px solid rgba(148, 163, 184, 0.25);
  border-radius: 999px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.search-bar:focus-within {
  border-color: var(--green-500);
  box-shadow: 0 0 0 4px rgba(82, 183, 136, 0.16);
}
.search-bar .ic { color: var(--muted); }
.search-bar input {
  flex: 1; border: 0; background: transparent; padding: 12px 0;
  font-size: 15px; color: var(--ink); outline: none;
}
.search-bar input::placeholder { color: #94a3b8; }
.clear {
  background: rgba(148, 163, 184, 0.2);
  color: var(--muted);
  border: 0;
  width: 26px; height: 26px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px; line-height: 1;
}
.clear:hover { background: rgba(244, 63, 94, 0.18); color: #b91c1c; }

.filter-row { display: flex; gap: 28px; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 6px; }
.lbl {
  font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--muted); font-weight: 700;
}
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--bg-soft);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 999px;
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.chip:hover { background: var(--green-100); border-color: var(--green-300); }
.chip.on {
  background: linear-gradient(135deg, var(--green-500), var(--green-700));
  color: #ffffff;
  border-color: transparent;
  box-shadow: 0 6px 18px rgba(45, 106, 79, 0.25);
}
.chip span { font-size: 14px; }

.result-line { color: var(--muted); font-size: 14px; margin: 0; }
.result-line strong { color: var(--green-700); font-weight: 700; }

/* LAYOUT */
.layout {
  max-width: 1200px; margin: 0 auto 32px; padding: 0 24px;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
  align-items: start;
}

/* MAP */
.map-card {
  position: sticky;
  top: 24px;
  height: 600px;
  background: #ffffff;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 16px 50px rgba(45, 106, 79, 0.08);
  overflow: hidden;
}
.map { width: 100%; height: 100%; }
.map-placeholder { position: relative; width: 100%; height: 100%; background: linear-gradient(135deg, #e7f5ec, #d8f3dc 60%, #c7e9d2); }
.map-grid {
  position: absolute; inset: 0;
  display: grid; grid-template-columns: repeat(8, 1fr);
}
.map-grid .cell {
  border-right: 1px solid rgba(45, 106, 79, 0.08);
  border-bottom: 1px solid rgba(45, 106, 79, 0.08);
}
.placeholder-msg {
  position: absolute;
  top: 16px; left: 16px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(45, 106, 79, 0.15);
  padding: 10px 14px;
  border-radius: 14px;
  display: flex; flex-direction: column; gap: 4px;
  max-width: 320px;
  box-shadow: 0 8px 20px rgba(45, 106, 79, 0.1);
}
.placeholder-msg strong { color: var(--green-700); font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; }
.placeholder-msg span { color: var(--muted); font-size: 12px; line-height: 1.5; }
.placeholder-msg code {
  background: rgba(45, 106, 79, 0.1);
  color: var(--green-700);
  padding: 1px 5px;
  border-radius: 5px;
  font-family: ui-monospace, monospace;
  font-size: 11px;
}

.map-pin {
  position: absolute;
  transform: translate(-50%, -100%);
  width: 36px; height: 44px;
  background: transparent;
  border: 0;
  cursor: pointer;
  color: var(--green-700);
  transition: transform 0.25s ease;
}
.map-pin::before {
  content: '';
  position: absolute;
  inset: 0 0 6px 0;
  background: linear-gradient(135deg, var(--green-500), var(--green-700));
  border-radius: 18px 18px 18px 4px;
  transform: rotate(-45deg);
  box-shadow: 0 10px 20px rgba(45, 106, 79, 0.3);
}
.map-pin strong {
  position: relative;
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  display: grid; place-items: center;
  width: 30px; height: 30px;
  background: transparent;
  margin: 4px auto;
}
.map-pin:hover { transform: translate(-50%, -100%) scale(1.1); }
.map-pin.focused::before, .map-pin.active::before {
  background: linear-gradient(135deg, #fb923c, #f97316);
  box-shadow: 0 0 0 4px rgba(251, 146, 60, 0.25), 0 12px 30px rgba(251, 146, 60, 0.45);
}

.user-pin {
  position: absolute;
  width: 16px; height: 16px;
  background: #2563eb;
  color: transparent;
  border: 3px solid #ffffff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3), 0 8px 16px rgba(37, 99, 235, 0.35);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3), 0 8px 16px rgba(37, 99, 235, 0.35); }
  50% { box-shadow: 0 0 0 10px rgba(37, 99, 235, 0.15), 0 8px 16px rgba(37, 99, 235, 0.35); }
}

/* PANEL */
.panel { display: flex; flex-direction: column; gap: 14px; }
.panel-title {
  font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--green-700); margin: 0 0 4px;
}

.empty {
  padding: 40px 20px;
  text-align: center;
  background: #ffffff;
  border-radius: 18px;
  border: 1px dashed rgba(148, 163, 184, 0.35);
  color: var(--muted);
}
.empty span { font-size: 36px; display: block; margin-bottom: 6px; }
.empty p { margin: 0; font-size: 14px; }

/* DEVICE CARDS */
.device-card {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 16px;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.3s ease;
}
.device-card:hover {
  transform: translateY(-2px);
  border-color: var(--green-300);
  box-shadow: 0 14px 30px rgba(45, 106, 79, 0.1);
}
.device-card.open { border-color: var(--green-500); box-shadow: 0 18px 40px rgba(45, 106, 79, 0.15); }

.device-row {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 12px;
  align-items: center;
}
.device-icon {
  width: 56px; height: 56px;
  display: grid; place-items: center;
  background: linear-gradient(135deg, var(--green-100), rgba(149, 213, 178, 0.25));
  border-radius: 14px;
  font-size: 26px;
}
.device-info h4 { margin: 0 0 3px; font-size: 16px; color: var(--green-900); }
.device-info .meta { color: var(--muted); font-size: 12px; }
.device-price strong { font-size: 20px; color: var(--green-700); font-weight: 700; }

.stall-line {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  color: var(--muted);
  font-size: 13px;
  display: flex; align-items: center; gap: 8px;
}
.stall-line .dot {
  width: 8px; height: 8px;
  background: var(--green-500);
  border-radius: 50%;
}
.stall-line strong { color: var(--green-700); }

.device-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  display: flex; flex-wrap: wrap; gap: 8px;
}
.stall-addr { color: var(--muted); font-size: 13px; margin: 0 0 6px; width: 100%; }

/* STALL CARDS */
.stall-card {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 18px;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.3s ease;
}
.stall-card:hover { transform: translateY(-2px); border-color: var(--green-300); }
.stall-card.open, .stall-card.focused { border-color: var(--green-500); box-shadow: 0 18px 40px rgba(45, 106, 79, 0.15); }

.stall-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.stall-head h4 { margin: 0 0 4px; font-size: 16px; color: var(--green-900); display: flex; align-items: center; gap: 8px; }
.pill {
  display: inline-grid; place-items: center;
  min-width: 24px; height: 24px;
  background: var(--green-500);
  color: #ffffff;
  border-radius: 8px;
  font-size: 12px; font-weight: 700;
}
.stall-head .meta { color: var(--muted); font-size: 13px; margin: 0; }
.status { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700; padding: 5px 10px; border-radius: 999px; }
.status.on { background: rgba(82, 183, 136, 0.18); color: var(--green-700); }
.status.off { background: rgba(244, 63, 94, 0.16); color: #be123c; }
.ind { width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }

.stall-meta {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg-soft);
  border-radius: 14px;
}
.stall-meta > div { display: flex; flex-direction: column; }
.ml { font-size: 10px; letter-spacing: 0.1em; color: var(--muted); text-transform: uppercase; }
.stall-meta strong { font-size: 13px; color: var(--green-900); margin-top: 2px; }

.inv-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.inv-chip {
  font-size: 12px;
  padding: 6px 10px;
  background: var(--green-100);
  color: var(--green-700);
  border-radius: 8px;
  border: 1px solid rgba(82, 183, 136, 0.25);
  font-weight: 600;
}
.inv-chip.more { background: rgba(148, 163, 184, 0.12); color: var(--muted); border-color: rgba(148, 163, 184, 0.2); }

.stall-expand {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  display: flex; flex-direction: column; gap: 10px;
}
.stall-expand h5 { font-size: 12px; letter-spacing: 0.12em; color: var(--green-700); text-transform: uppercase; margin: 0; }
.inv-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.inv-card {
  display: flex; flex-direction: column;
  padding: 12px;
  background: var(--bg-soft);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.18);
}
.inv-icon { font-size: 22px; }
.inv-card strong { font-size: 13px; margin: 4px 0 2px; color: var(--green-900); }
.inv-meta { font-size: 11px; color: var(--muted); }
.inv-price { font-size: 15px; color: var(--green-700); font-weight: 700; margin-top: 4px; }

.stall-actions { display: flex; flex-wrap: wrap; gap: 8px; }

/* BUTTONS */
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  border: 0; cursor: pointer;
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.2s ease;
}
.btn.primary {
  background: linear-gradient(135deg, var(--green-500), var(--green-700));
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(45, 106, 79, 0.28);
}
.btn.primary:hover { transform: translateY(-1px); box-shadow: 0 14px 30px rgba(45, 106, 79, 0.4); }
.btn.primary.big { padding: 14px 22px; font-size: 14px; }
.btn.ghost {
  background: #ffffff;
  color: var(--green-700);
  border: 1px solid rgba(82, 183, 136, 0.4);
}
.btn.ghost:hover { background: var(--green-100); }

/* SELL PANEL */
.sell-panel { display: flex; flex-direction: column; gap: 14px; }
.sell-card, .nearest-card {
  background: #ffffff;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 24px;
  box-shadow: 0 12px 36px rgba(45, 106, 79, 0.08);
  display: flex; flex-direction: column; gap: 10px;
}
.sell-card h3, .nearest-card h3 { margin: 4px 0; font-size: 22px; color: var(--green-900); }
.sell-card p, .nearest-card .addr, .note { color: var(--muted); margin: 0; line-height: 1.6; font-size: 14px; }
.note { font-style: italic; font-size: 13px; }
.sell-card h5 { font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--green-700); margin: 6px 0 0; }
.accept { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.accept li {
  display: flex; align-items: center; gap: 10px;
  font-size: 14px;
  color: var(--ink);
}
.accept li span {
  display: grid; place-items: center;
  width: 32px; height: 32px;
  background: var(--green-100);
  border-radius: 10px;
  font-size: 16px;
}

.nearest-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding: 14px;
  background: var(--bg-soft);
  border-radius: 14px;
  margin: 6px 0 4px;
}
.nearest-meta > div { display: flex; flex-direction: column; }
.nearest-meta span { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.nearest-meta strong { font-size: 14px; color: var(--green-900); margin-top: 2px; }

/* IMPACT */
.impact {
  max-width: 1200px;
  margin: 32px auto 0;
  padding: 0 24px;
}
.impact-inner {
  background: linear-gradient(135deg, var(--green-700), var(--green-900));
  border-radius: 28px;
  padding: 36px;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 32px;
  align-items: center;
  color: #ffffff;
  box-shadow: 0 24px 60px rgba(45, 106, 79, 0.25);
  position: relative;
  overflow: hidden;
}
.impact-inner::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top right, rgba(149, 213, 178, 0.3), transparent 50%),
    radial-gradient(circle at bottom left, rgba(149, 213, 178, 0.15), transparent 50%);
}
.impact-inner > div { position: relative; }
.impact-inner .eyebrow {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  color: #d8f3dc;
}
.impact-inner h2 { margin: 10px 0 6px; font-size: clamp(22px, 3vw, 30px); color: #ffffff; letter-spacing: -0.02em; }
.impact-inner p { color: rgba(216, 243, 220, 0.9); margin: 0; line-height: 1.6; }
.impact-stats { display: flex; justify-content: space-around; gap: 16px; }
.impact-stats > div { display: flex; flex-direction: column; align-items: center; }
.impact-stats strong { font-size: 32px; font-weight: 700; color: #ffffff; }
.impact-stats span { font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: rgba(216, 243, 220, 0.8); margin-top: 4px; text-align: center; }

/* TRANSITIONS */
.expand-enter-active, .expand-leave-active { transition: max-height 0.3s ease, opacity 0.3s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; }
.expand-enter-to, .expand-leave-from { max-height: 800px; opacity: 1; }

/* RESPONSIVE */
@media (max-width: 1024px) {
  .layout { grid-template-columns: 1fr; }
  .map-card { position: relative; top: 0; height: 360px; }
  .impact-inner { grid-template-columns: 1fr; text-align: left; }
}
@media (max-width: 600px) {
  .filter-row { flex-direction: column; gap: 14px; }
  .stall-meta { grid-template-columns: 1fr; }
  .inv-grid { grid-template-columns: 1fr; }
  .nearest-meta { grid-template-columns: 1fr; }
  .device-row { grid-template-columns: 48px 1fr; }
  .device-price { grid-column: 1 / -1; text-align: right; }
}

/* Mapbox markers (loaded into mapbox-gl-rendered DOM, hence :global) */
:deep(.eco-marker) {
  width: 26px; height: 32px;
  background: linear-gradient(135deg, #52b788, #2d6a4f);
  border-radius: 14px 14px 14px 3px;
  transform: rotate(-45deg);
  box-shadow: 0 8px 18px rgba(45, 106, 79, 0.35);
  cursor: pointer;
}
:deep(.eco-marker.focused) {
  background: linear-gradient(135deg, #fb923c, #f97316);
  box-shadow: 0 8px 18px rgba(251, 146, 60, 0.45), 0 0 0 4px rgba(251, 146, 60, 0.25);
}
:deep(.eco-me) {
  width: 16px; height: 16px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid #ffffff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
}
</style>
