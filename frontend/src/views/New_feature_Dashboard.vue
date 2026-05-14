<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

import { api } from '@/api'

const loading = ref(true)
const error = ref('')

const healthRows = ref([])
const healthFilterOptions = ref({ years: [], sexes: [], cancer_types: [] })
const stateRows = ref([])
const facilityRows = ref([])

const selectedYear = ref('')
const selectedSex = ref('')
const selectedCancerType = ref('')
const showAllCancers = ref(false)

const trendChartRef = ref(null)
const stateChartRef = ref(null)
let trendChart = null
let stateChart = null

const pathwayChains = [
  {
    tag: 'Chain 1',
    title: 'E-waste to environment',
    steps: [
      'E-waste generation',
      'Hazardous disposal and recycling pressure',
      'Air, land, and water emissions',
    ],
    evidence:
      'The environmental analysis links e-waste pressure with pollutant release patterns, especially heavy metal and total emission indicators.',
  },
  {
    tag: 'Chain 2',
    title: 'Environment to health',
    steps: ['Pollution indicators', 'State-year health comparison', 'Mortality and burden signals'],
    evidence:
      'The health analysis compares emission indicators with outcomes such as deaths, premature deaths, avoidable deaths, and years of life lost.',
  },
]

const HEAVY_METAL_LINKED = [
  { name: 'Lung cancer', icon: '🫁', metal: 'Pb · Cd' },
  { name: 'Kidney cancer', icon: '🩺', metal: 'Pb · Cd' },
  { name: 'Bladder cancer', icon: '🩺', metal: 'Cd' },
  { name: 'Prostate cancer', icon: '👨', metal: 'Cd' },
  { name: 'Brain cancer', icon: '🧠', metal: 'Pb' },
  { name: 'Acute myeloid leukaemia', icon: '🩸', metal: 'Pb' },
  { name: 'Acute lymphoblastic leukaemia', icon: '🩸', metal: 'Pb' },
  { name: 'Stomach cancer', icon: '🫀', metal: 'Pb' },
  { name: 'Liver cancer', icon: '🫀', metal: 'Cd · Hg' },
  { name: 'Pancreatic cancer', icon: '🫀', metal: 'Cd' },
]

const METAL_NAMES = {
  Pb: 'lead',
  Cd: 'cadmium',
  Hg: 'mercury',
}

function formatMetal(metalStr) {
  return metalStr
    .split('·')
    .map((m) => {
      const key = m.trim()
      return `${METAL_NAMES[key]} (${key})`
    })
    .join(' and ')
}

function parseFY(reportYear) {
  if (reportYear === null || reportYear === undefined) return null
  const value = String(reportYear)
  if (value.includes('/')) return Number.parseInt(value.split('/')[0], 10)
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) ? parsed : null
}

function safeNumber(value) {
  const parsed = Number(value || 0)
  return Number.isFinite(parsed) ? parsed : 0
}

function formatNumber(value) {
  return Math.round(safeNumber(value)).toLocaleString()
}

function formatTonnes(kg) {
  const tonnes = safeNumber(kg) / 1000
  if (tonnes >= 1000) return `${(tonnes / 1000).toFixed(1)}k tonnes`
  if (tonnes >= 1) return `${tonnes.toFixed(1)} tonnes`
  return `${Math.round(safeNumber(kg))} kg`
}

function pct(value) {
  if (!Number.isFinite(value)) return '—'
  const sign = value >= 0 ? '+' : '−'
  return `${sign}${Math.abs(Math.round(value))}%`
}

function extractItems(response) {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.items)) return response.items
  return []
}

function extractFilters(response) {
  if (response?.items && typeof response.items === 'object' && !Array.isArray(response.items)) {
    return response.items
  }
  if (response && typeof response === 'object' && !Array.isArray(response)) {
    return response
  }
  return { years: [], sexes: [], cancer_types: [] }
}

const availableYears = computed(() => {
  const years = healthFilterOptions.value.years || []
  return [...years].sort((a, b) => Number(a) - Number(b))
})

const availableSexes = computed(() => healthFilterOptions.value.sexes || [])
const availableCancerTypes = computed(() => healthFilterOptions.value.cancer_types || [])

const filteredHealthRows = computed(() => {
  return healthRows.value.filter((row) => {
    if (selectedYear.value && String(row.year) !== String(selectedYear.value)) return false
    if (selectedSex.value && String(row.sex) !== String(selectedSex.value)) return false
    if (selectedCancerType.value && String(row.cancer_type) !== String(selectedCancerType.value)) {
      return false
    }
    return true
  })
})

const growthSourceRows = computed(() =>
  filteredHealthRows.value.length ? filteredHealthRows.value : healthRows.value,
)

const healthStats = computed(() => {
  const years = new Set(healthRows.value.map((row) => row.year).filter(Boolean))
  const cancers = new Set(healthRows.value.map((row) => row.cancer_type).filter(Boolean))

  return [
    {
      label: 'Health rows',
      value: formatNumber(healthRows.value.length),
      text: 'DB-backed health records loaded from the cloud database.',
    },
    {
      label: 'Years',
      value: formatNumber(years.size),
      text: 'Distinct reporting years available in the health table.',
    },
    {
      label: 'Cancer types',
      value: formatNumber(cancers.size),
      text: 'Cancer categories available for filtering.',
    },
    {
      label: 'Filtered rows',
      value: formatNumber(filteredHealthRows.value.length),
      text: 'Rows matching the current filter selection.',
    },
  ]
})

const emissionsByYear = computed(() => {
  const map = {}
  for (const row of stateRows.value) {
    const year = parseFY(row.report_year)
    if (!year) continue
    map[year] = (map[year] || 0) + safeNumber(row.total_air_emission_kg)
  }
  return map
})

const fixedLinkedCancerByYear = computed(() => {
  const map = {}

  for (const row of healthRows.value) {
    const year = Number(row.year)
    if (!Number.isFinite(year)) continue
    if (year < 1999 || year > 2010) continue

    map[year] = (map[year] || 0) + safeNumber(row.cancer_cases)
  }

  return map
})

const earliestYear = computed(() => {
  const years = Object.keys(emissionsByYear.value).map(Number).filter(Number.isFinite)
  return years.length ? Math.min(...years) : null
})

const latestYear = computed(() => {
  const years = Object.keys(emissionsByYear.value).map(Number).filter(Number.isFinite)
  return years.length ? Math.max(...years) : null
})

const earliestEmissionsKg = computed(() =>
  earliestYear.value ? emissionsByYear.value[earliestYear.value] || 0 : 0,
)
const latestEmissionsKg = computed(() =>
  latestYear.value ? emissionsByYear.value[latestYear.value] || 0 : 0,
)

const emissionsChange = computed(() => {
  const first = earliestEmissionsKg.value
  const last = latestEmissionsKg.value
  if (!first) return null
  return ((last - first) / first) * 100
})

const earliestHealthYear = computed(() => {
  const years = Object.keys(fixedLinkedCancerByYear.value).map(Number).filter(Number.isFinite)
  return years.length ? Math.min(...years) : null
})

const latestHealthYear = computed(() => {
  const years = Object.keys(fixedLinkedCancerByYear.value).map(Number).filter(Number.isFinite)
  return years.length ? Math.max(...years) : null
})

const earliestLinkedCases = computed(() =>
  earliestHealthYear.value ? fixedLinkedCancerByYear.value[earliestHealthYear.value] || 0 : 0,
)
const latestLinkedCases = computed(() =>
  latestHealthYear.value ? fixedLinkedCancerByYear.value[latestHealthYear.value] || 0 : 0,
)

const cancerChange = computed(() => {
  const first = earliestLinkedCases.value
  const last = latestLinkedCases.value
  if (!first) return null
  return ((last - first) / first) * 100
})

const perCancerGrowth = computed(() => {
  const result = []
  const rows = growthSourceRows.value.filter(
    (row) => String(row.sex) === String(selectedSex.value || row.sex),
  )

  for (const cancer of HEAVY_METAL_LINKED) {
    const points = rows.filter((row) => row.cancer_type === cancer.name)
    if (!points.length) {
      result.push({ ...cancer, change: null, latest: 0 })
      continue
    }

    const sorted = [...points].sort((a, b) => Number(a.year) - Number(b.year))
    const first = safeNumber(sorted[0].cancer_cases)
    const last = safeNumber(sorted[sorted.length - 1].cancer_cases)
    const change = first > 0 ? ((last - first) / first) * 100 : null
    result.push({ ...cancer, change, latest: last })
  }

  return result.sort((a, b) => (b.change || -Infinity) - (a.change || -Infinity))
})

const displayedCancers = computed(() =>
  showAllCancers.value ? perCancerGrowth.value : perCancerGrowth.value.slice(0, 5),
)

const topPollutingStates = computed(() => {
  const totals = {}
  for (const row of stateRows.value) {
    if (!row.state) continue
    totals[row.state] = (totals[row.state] || 0) + safeNumber(row.total_air_emission_kg)
  }

  return Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([state, kg]) => ({ state, kg }))
})

const allStatesEmissions = computed(() =>
  stateRows.value.reduce((sum, row) => sum + safeNumber(row.total_air_emission_kg), 0),
)

const top3Share = computed(() => {
  const top = topPollutingStates.value.reduce((sum, row) => sum + row.kg, 0)
  return allStatesEmissions.value > 0 ? (top / allStatesEmissions.value) * 100 : 0
})

const metalMix = computed(() => {
  const map = { Lead: 0, Mercury: 0, Cadmium: 0 }
  for (const row of stateRows.value) {
    const metal = String(row.metal || '').replace(' & compounds', '')
    if (metal in map) map[metal] += safeNumber(row.total_air_emission_kg)
  }
  const total = map.Lead + map.Mercury + map.Cadmium
  return Object.entries(map).map(([metal, kg]) => ({
    metal,
    kg,
    pct: total > 0 ? (kg / total) * 100 : 0,
  }))
})

const topFacilities = computed(() =>
  [...facilityRows.value]
    .sort((a, b) => safeNumber(b.total_air_emission_kg) - safeNumber(a.total_air_emission_kg))
    .slice(0, 5),
)

const trendChartOption = computed(() => {
  const START_YEAR = 1999
  const END_YEAR = 2010

  const eYears = Object.keys(emissionsByYear.value)
    .map(Number)
    .filter((y) => y >= START_YEAR && y <= END_YEAR)
    .sort((a, b) => a - b)

  const cYears = Object.keys(fixedLinkedCancerByYear.value)
    .map(Number)
    .filter((y) => y >= START_YEAR && y <= END_YEAR)
    .sort((a, b) => a - b)

  const xMin = START_YEAR
  const xMax = END_YEAR

  if (!eYears.length || !cYears.length) return {}

  const eBase = emissionsByYear.value[eYears[0]] || 1
  const cBase = fixedLinkedCancerByYear.value[cYears[0]] || 1

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const year = params?.[0]?.axisValue ?? ''
        let html = `<strong>${year}</strong><br>`
        for (const item of params) {
          const diff = item.data[1] - 100
          html += `${item.marker} ${item.seriesName}: <b>${item.data[1]}</b> (${diff >= 0 ? '+' : ''}${diff}% vs first year)<br>`
        }
        return html
      },
    },
    legend: { bottom: 0, icon: 'roundRect', itemHeight: 10 },
    grid: { left: 70, right: 30, top: 24, bottom: 60 },
    xAxis: {
      type: 'value',
      min: xMin,
      max: xMax,
      axisLabel: { color: '#4b5563', formatter: (v) => Math.round(v) },
      splitLine: { show: false },
      axisLine: { lineStyle: { color: '#d1d5db' } },
    },
    yAxis: {
      type: 'value',
      name: 'Indexed (first year = 100)',
      nameTextStyle: { color: '#6b7280', fontSize: 11 },
      axisLabel: { color: '#4b5563' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: 'Heavy-metal pollution',
        type: 'line',
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 3, color: '#dc2626' },
        itemStyle: { color: '#dc2626' },
        data: eYears.map((year) => [year, Math.round((emissionsByYear.value[year] / eBase) * 100)]),
      },
      {
        name: 'Linked cancer cases',
        type: 'line',
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 3, color: '#7c3aed' },
        itemStyle: { color: '#7c3aed' },
        data: cYears.map((year) => [
          year,
          Math.round((fixedLinkedCancerByYear.value[year] / cBase) * 100),
        ]),
      },
    ],
  }
})

const stateChartOption = computed(() => {
  const totals = {}
  for (const row of stateRows.value) {
    if (!row.state) continue
    totals[row.state] = (totals[row.state] || 0) + safeNumber(row.total_air_emission_kg)
  }

  const sorted = Object.entries(totals).sort((a, b) => a[1] - b[1])

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (value) => formatTonnes(value),
    },
    grid: { left: 60, right: 60, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#4b5563',
        formatter: (value) =>
          value >= 1_000_000
            ? `${(value / 1_000_000).toFixed(1)}M kg`
            : `${(value / 1000).toFixed(0)}k`,
      },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map(([state]) => state),
      axisLabel: { color: '#374151', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barWidth: 22,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: (params) => (params.dataIndex >= sorted.length - 3 ? '#dc2626' : '#22c55e'),
        },
        label: {
          show: true,
          position: 'right',
          formatter: (params) => formatTonnes(params.value),
          color: '#4b5563',
          fontSize: 12,
        },
        data: sorted.map(([, value]) => Math.round(value)),
      },
    ],
  }
})

function renderCharts() {
  if (trendChartRef.value) {
    if (!trendChart) trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption(trendChartOption.value, true)
  }

  if (stateChartRef.value) {
    if (!stateChart) stateChart = echarts.init(stateChartRef.value)
    stateChart.setOption(stateChartOption.value, true)
  }
}

function handleResize() {
  trendChart?.resize()
  stateChart?.resize()
}

async function loadData() {
  try {
    loading.value = true
    error.value = ''

    const [healthResponse, filterResponse, stateResponse, facilityResponse] = await Promise.all([
      api.getHealthAll_2(),
      api.getHealthFilter(),
      api.getHeavyMetalState(),
      api.getHeavyMetalFacility(),
    ])

    healthRows.value = extractItems(healthResponse)
    healthFilterOptions.value = extractFilters(filterResponse)
    stateRows.value = extractItems(stateResponse)
    facilityRows.value = extractItems(facilityResponse)

    if (!availableSexes.value.length && healthRows.value.length) {
      healthFilterOptions.value = {
        ...healthFilterOptions.value,
        sexes: [...new Set(healthRows.value.map((row) => row.sex).filter(Boolean))],
      }
    }
  } catch (e) {
    console.error('[Dashboard] failed to load data:', e)
    error.value = e?.message || 'Failed to load dashboard data.'
  } finally {
    loading.value = false
    await nextTick()
    renderCharts()
  }
}

watch(
  [filteredHealthRows, stateRows, facilityRows],
  async () => {
    await nextTick()
    renderCharts()
  },
  { deep: true },
)

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  stateChart?.dispose()
})
</script>

<template>
  <section class="db-dashboard">
    <!--
    <div class="hero-card">
  
      <div class="hero-copy">
        
        <p class="eyebrow">Database-backed dashboard</p>
        <h1>Pollution and health insights, now driven by the cloud database.</h1>
        <p class="lede">
          This view uses `getHealthAll_2`, `getHealthFilter`, `getHeavyMetalState`, and
          `getHeavyMetalFacility` so we can inspect the real tables directly from the backend.
        </p>
      </div>

      <div class="hero-meta">
        <div class="meta-chip" v-for="card in healthStats" :key="card.label">
          <span class="chip-label">{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <small>{{ card.text }}</small>
        </div>
      </div>
      
    </div>
    -->

    <section class="analysis-panel">
      <div class="section-header">
        <div>
          <p class="section-tag">Trend comparison</p>
          <h2>Indexed heavy-metal emissions and linked cancers</h2>
        </div>
      </div>

      <div ref="trendChartRef" class="chart-frame"></div>
      <p class="chart-note">
        Both lines are indexed to 100 at their first year so the growth pattern can be compared side
        by side.
      </p>
    </section>

    <section class="panel">
      <div class="section-header">
        <div>
          <p class="section-tag">Health filters</p>
          <h2>Slice the database-backed health table</h2>
        </div>
      </div>

      <div class="filter-grid">
        <label>
          <span>Year</span>
          <select v-model="selectedYear">
            <option value="">All years</option>
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}</option>
          </select>
        </label>

        <label>
          <span>Sex</span>
          <select v-model="selectedSex">
            <option value="">All sexes</option>
            <option v-for="sex in availableSexes" :key="sex" :value="sex">{{ sex }}</option>
          </select>
        </label>

        <label>
          <span>Cancer type</span>
          <select v-model="selectedCancerType">
            <option value="">All cancers</option>
            <option v-for="cancer in availableCancerTypes" :key="cancer" :value="cancer">
              {{ cancer }}
            </option>
          </select>
        </label>
      </div>
    </section>
    <!--
    <section class="pathway-grid">
      <article v-for="chain in pathwayChains" :key="chain.title" class="pathway-card">
        <span class="section-tag">{{ chain.tag }}</span>
        <h2>{{ chain.title }}</h2>
        <div class="pathway-steps">
          <template v-for="(step, index) in chain.steps" :key="step">
            <strong>{{ step }}</strong>
            <span v-if="index < chain.steps.length - 1" class="arrow">→</span>
          </template>
        </div>
        <p>{{ chain.evidence }}</p>
      </article>
    </section>
-->
    <!--
    <section class="stats-grid">
      <article v-for="card in healthStats" :key="card.label" class="card">
        <span class="card-label">{{ card.label }}</span>
        <h2>{{ card.value }}</h2>
        <p>{{ card.text }}</p>
      </article>
    </section>
  -->

    <section class="content-grid">
      <article class="panel">
        <div class="section-header compact">
          <div>
            <p class="section-tag">Cancer growth</p>
            <h2>Growth of cancers linked to heavy metals</h2>
          </div>
          <button type="button" class="secondary-button" @click="showAllCancers = !showAllCancers">
            {{ showAllCancers ? 'Show less' : 'Show all' }}
          </button>
        </div>

        <div class="cancer-grid">
          <article
            v-for="(cancer, index) in displayedCancers"
            :key="cancer.name"
            class="cancer-card"
          >
            <div class="cancer-top">
              <span class="cancer-icon">{{ cancer.icon }}</span>

              <span class="cancer-info-wrapper">
                <button class="cancer-info-button" type="button">i</button>
                <span class="cancer-info-tooltip">
                  Associated with {{ formatMetal(cancer.metal) }}
                </span>
              </span>
            </div>
            <h3>{{ cancer.name }}</h3>
            <p class="cancer-change">{{ pct(cancer.change) }}</p>
            <p class="cancer-detail">{{ formatNumber(cancer.latest) }} cases in latest year</p>
            <span v-if="index === 0" class="top-badge">Highest increase</span>
          </article>
        </div>
      </article>

      <!--
      <article class="panel">
        <div class="section-header compact">
          <div>
            <p class="section-tag">Health rows</p>
            <h2>Filtered database records</h2>
          </div>
        </div>

        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Year</th>
                <th>Sex</th>
                <th>Cancer</th>
                <th>Cases</th>
                <th>Deaths</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in filteredHealthRows.slice(0, 10)"
                :key="`${row.year}-${row.sex}-${row.cancer_type}`"
              >
                <td>{{ row.year }}</td>
                <td>{{ row.sex }}</td>
                <td>{{ row.cancer_type }}</td>
                <td>{{ formatNumber(row.cancer_cases) }}</td>
                <td>{{ formatNumber(row.cancer_deaths) }}</td>
              </tr>
              <tr v-if="!filteredHealthRows.length">
                <td colspan="5" class="empty-cell">No rows match the selected filters.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
      -->
    </section>

    <section class="analysis-panel">
      <div class="section-header">
        <div>
          <p class="section-tag">State emissions</p>
          <h2>Where pollution concentrates</h2>
          <p class="section-desc">
            Just three states account for
            <strong>{{ Math.round(top3Share) }}%</strong>
            of total reported heavy-metal air emissions.
          </p>
        </div>
      </div>

      <div class="state-cards">
        <div v-for="(item, index) in topPollutingStates" :key="item.state" class="state-card">
          <span class="state-rank">{{ index + 1 }}</span>

          <div>
            <strong class="state-name">{{ item.state }}</strong>
            <p class="state-amount">{{ formatTonnes(item.kg) }} air emissions, all-time</p>
          </div>
        </div>
      </div>

      <div ref="stateChartRef" class="chart-frame"></div>
    </section>

    <!-- 
      <article class="panel">
        <div class="section-header compact">
          <div>
            <p class="section-tag">Top facilities</p>
            <h2>Largest emissions facilities</h2>
          </div>
        </div>

        <div class="facility-list">
          <article
            v-for="facility in topFacilities"
            :key="`${facility.facility_id}-${facility.metal}`"
            class="facility-card"
          >
            <strong>{{ facility.facility_name }}</strong>
            <span>{{ facility.state }} · {{ facility.metal }}</span>
            <p>{{ formatTonnes(facility.total_air_emission_kg) }} air emissions</p>
          </article>
          
        </div>
      </article>
      -->
  </section>

  <section class="impact-panel">
    <p class="section-tag">What this means for you</p>

    <h2 class="impact-title">One phone may be small. Millions of phones aren’t.</h2>

    <div class="impact-cards">
      <div class="impact-card">
        <strong>8 g</strong>
        <span>Average heavy-metal content in a single smartphone</span>
      </div>

      <div class="impact-card">
        <strong>~25 yrs</strong>
        <span>How long lead can persist in soil after landfilling</span>
      </div>

      <div class="impact-card">
        <strong>100%</strong>
        <span>Metals that can be safely contained by recycling</span>
      </div>
    </div>

    <p class="impact-note">
      When you recycle a device properly, these materials stay out of the air, water, and food chain
      — for generations.
    </p>
  </section>

  <section v-if="loading" class="status-box">Loading…</section>
  <section v-else-if="error" class="status-box error">
    <strong>Couldn't load data.</strong>
    <p>{{ error }}</p>
  </section>
</template>

<style scoped>
.db-dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 28px 0 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: transparent;
  color: #173a29;
  box-sizing: border-box;
}

.db-dashboard > section {
  width: 100%;
  margin: 0;
  box-sizing: border-box;
}

.impact-panel {
  max-width: 1400px;
  width: 100%;
  margin: 16px auto 0;
  padding: 24px;
  border-radius: 18px;
  background: #f8faf9;
  border: 1px solid #e3efe7;
  box-sizing: border-box;
}

.hero-card,
.panel,
.card,
.pathway-card,
.analysis-panel {
  border: 1px solid rgba(210, 232, 214, 0.98);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(251, 253, 251, 0.94));
  box-shadow: 0 18px 34px rgba(27, 67, 50, 0.05);
  backdrop-filter: blur(14px);
  border-radius: 26px;
}

.hero-card {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 24px;
  padding: 30px;
}

.eyebrow {
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 11px;
  font-weight: 800;
  color: #16a34a;
}

.hero-copy h1,
.panel h2,
.analysis-panel h2 {
  margin: 0;
  color: #0f3a25;
}

.hero-copy h1 {
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.15;
  max-width: 820px;
}

.lede,
.section-note,
.chart-note,
.facility-card p,
.pathway-card p,
.table-wrap,
.meta-chip small {
  color: #587465;
}

.hero-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.meta-chip {
  border-radius: 18px;
  padding: 16px;
  background: rgba(241, 248, 242, 0.94);
  border: 1px solid rgba(210, 232, 214, 0.98);
}

.chip-label,
.section-tag {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 7px 14px;
  border-radius: 999px;
  background: rgba(232, 245, 233, 0.92);
  border: 1px solid rgba(207, 232, 209, 0.98);
  color: #2e7d32;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.meta-chip strong {
  display: block;
  margin-bottom: 4px;
  font-size: 1.05rem;
  color: #163728;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-header.compact {
  margin-bottom: 18px;
}

.filter-grid,
.stats-grid,
.content-grid,
.pathway-grid {
  display: grid;
  gap: 20px;
}

.filter-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.filter-grid label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 700;
  color: #335342;
}

.filter-grid select {
  border-radius: 14px;
  border: 1px solid #d1ead5;
  background: #ffffff;
  padding: 12px 14px;
  color: #163728;
}

.pathway-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.pathway-card {
  padding: 28px;
}

.pathway-card h2 {
  font-size: 1.6rem;
  margin-bottom: 16px;
}

.pathway-steps {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin: 18px 0;
}

.pathway-steps strong {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(241, 248, 242, 0.92);
  border: 1px solid rgba(210, 232, 214, 0.98);
  color: #163728;
}

.pathway-steps .arrow {
  color: #2e7d32;
  font-size: 1.2rem;
  font-weight: 900;
}

.analysis-panel {
  padding: 26px;
}

.chart-frame {
  width: 100%;
  min-height: 360px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.card {
  padding: 22px;
}

.card-label {
  display: block;
  margin-bottom: 8px;
  color: #2e7d32;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.card h2 {
  font-size: 2rem;
  margin-bottom: 8px;
}

.content-grid {
  grid-template-columns: 1fr;
}

.panel {
  padding: 24px;
}

.cancer-grid,
.facility-list {
  display: grid;
  gap: 14px;
}

.cancer-grid {
  grid-template-columns: repeat(5, 1fr);
}

.cancer-card {
  border-radius: 18px;
  padding: 16px;
  background: rgba(241, 248, 242, 0.92);
  border: 1px solid rgba(210, 232, 214, 0.98);
  position: relative;
}

.cancer-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.cancer-icon {
  font-size: 1.2rem;
}

.info-icon {
  font-size: 14px;
  cursor: pointer;
  opacity: 0.7;
  transition: 0.2s;
}

.info-icon:hover {
  opacity: 1;
  transform: scale(1.1);
}

.top-badge {
  padding: 4px 10px;
  border-radius: 999px;
  background: #fee2e2;
  color: #991b1b;
  font-size: 12px;
  font-weight: 700;
}

.cancer-info-wrapper {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 3;
}

.cancer-info-button {
  width: 18px;
  height: 18px;

  border-radius: 50%;
  border: 1px solid #b7d1c4;

  background: rgba(255, 255, 255, 0.8);
  color: #6b8f7d;

  display: flex;
  align-items: center;
  justify-content: center;

  font-size: 11px;
  font-weight: 700;

  cursor: pointer;
  transition: 0.15s ease;
}

.cancer-info-button:hover {
  background: #173a29;
  border-color: #173a29;
  color: white;
}

.cancer-info-tooltip {
  position: absolute;
  top: 36px;
  right: 0;

  max-width: 240px;
  min-width: 160px;
  white-space: normal;

  padding: 8px 10px;
  border-radius: 10px;

  background: #f8faf9;
  border: 1px solid #e3eee8;
  box-shadow: 0 8px 20px rgba(23, 63, 46, 0.18);

  color: #173a29;
  font-size: 12px;
  line-height: 1.4;

  opacity: 0;
  pointer-events: none;
  transform: translateY(-2px);
  transition: 0.1s ease;
  z-index: 99;
}

.cancer-info-wrapper:hover .cancer-info-tooltip {
  opacity: 1;
  transform: translateY(0);
}

.cancer-metal {
  font-size: 12px;
  color: #4b5563;
}

.cancer-change {
  margin: 10px 0 4px;
  font-size: 1.4rem;
  font-weight: 800;
  color: #0f3a25;
}

.cancer-detail {
  margin: 0;
  font-size: 13px;
}

.table-wrap {
  overflow: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(210, 232, 214, 0.72);
  text-align: left;
}

.data-table th {
  color: #335342;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.empty-cell {
  text-align: center;
  color: #6b7280;
}

.state-list {
  list-style: none;
  padding: 0;
  margin: 0 0 12px;
  display: grid;
  gap: 12px;
}

.state-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 0;
  margin: 0;
}

.state-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-radius: 16px;
  list-style: none;
}

.rank {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #d7efe2;
  color: #1f6f4a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.state-info {
  flex: 1;
  margin-left: 16px;
}

.state-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f3d2b;
}

.state-desc {
  display: block;
  font-size: 13px;
  color: #7f9a8c;
}

.state-value {
  font-size: 20px;
  font-weight: 600;
  color: #2f8f5b;
}

.state-value span {
  font-size: 12px;
  margin-left: 4px;
  color: #7f9a8c;
}

.state-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.state-card {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 20px 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
}

.state-rank {
  font-size: 34px;
  font-weight: 800;
  color: #dc2626;
  line-height: 1;
}

.state-name {
  display: block;
  font-size: 18px;
  font-weight: 800;
  color: #1f2937;
}

.state-amount {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.section-desc {
  margin: 8px 0 0;
  color: #587465;
  font-size: 15px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .state-cards {
    grid-template-columns: 1fr;
  }
}

.facility-list {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.facility-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(241, 248, 242, 0.92);
  border: 1px solid rgba(210, 232, 214, 0.98);
}

.facility-card strong {
  display: block;
  margin-bottom: 6px;
  color: #163728;
}

.secondary-button {
  border: 1px solid #cfe4da;
  background: #f8fffb;
  color: #0f766e;
  border-radius: 14px;
  padding: 10px 14px;
  font-weight: 800;
  cursor: pointer;
}

.status-box {
  padding: 18px 20px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  color: #4b5563;
  text-align: center;
}

.status-box.error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.section-note,
.chart-note {
  margin-top: 10px;
  font-size: 14px;
}

@media (max-width: 1100px) {
  .hero-card,
  .pathway-grid,
  .content-grid,
  .stats-grid,
  .filter-grid {
    grid-template-columns: 1fr;
  }
}

.impact-panel {
  margin-top: 40px;
  padding: 28px;
  border-radius: 18px;
  background: #f8faf9;
  border: 1px solid #e3efe7;
}

.impact-tag {
  font-size: 12px;
  letter-spacing: 1px;
  color: #6b8f7d;
  margin-bottom: 10px;
  text-transform: uppercase;
}

.impact-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f3d2b;
  margin-bottom: 24px;
}

.impact-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.impact-card {
  padding: 18px;
  border-radius: 14px;

  background: white;
  border: 1px solid #e5e7eb;

  text-align: center;
}

.impact-card strong {
  display: block;
  font-size: 18px;
  color: #1f3d2b;
}

.impact-card span {
  display: block;
  font-size: 13px;
  color: #6b7280;
  margin-top: 6px;
}

.impact-note {
  margin-top: 18px;
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}
</style>
