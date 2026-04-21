<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { api } from '@/api'
import * as echarts from 'echarts'

const loading = ref(true)
const error = ref('')

const healthData = ref([])
const statePollutionData = ref([])
const facilityPollutionData = ref([])

const selectedYear = ref('All')
const selectedMetal = ref('All')
const selectedState = ref('All')
const selectedSex = ref('All')
const selectedCancerType = ref('All')

const pollutionStateChartRef = ref(null)
const topFacilityChartRef = ref(null)
const metalTotalsChartRef = ref(null)
const healthTrendChartRef = ref(null)
const fatalityChartRef = ref(null)

let pollutionStateChart = null
let topFacilityChart = null
let metalTotalsChart = null
let healthTrendChart = null
let fatalityChart = null

async function loadDashboardData() {
  try {
    loading.value = true
    error.value = ''

    const [healthRes, stateRes, facilityRes] = await Promise.all([
      api.getHealthAll(),
      api.getHeavyMetalState(),
      api.getHeavyMetalFacility(),
    ])

    healthData.value = Array.isArray(healthRes.items) ? healthRes.items : []
    statePollutionData.value = Array.isArray(stateRes.items) ? stateRes.items : []
    facilityPollutionData.value = Array.isArray(facilityRes.items) ? facilityRes.items : []
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to load dashboard data.'
  } finally {
    loading.value = false
  }
}

const yearOptions = computed(() => {
  const years = new Set()

  healthData.value.forEach((item) => {
    if (item.year !== null && item.year !== undefined) years.add(String(item.year))
  })

  statePollutionData.value.forEach((item) => {
    if (item.report_year !== null && item.report_year !== undefined) years.add(String(item.report_year))
  })

  return ['All', ...Array.from(years).sort()]
})

const metalOptions = computed(() => {
  const metals = [...new Set(facilityPollutionData.value.map((item) => item.metal).filter(Boolean))].sort()
  return ['All', ...metals]
})

const stateOptions = computed(() => {
  const states = [...new Set(statePollutionData.value.map((item) => item.state).filter(Boolean))].sort()
  return ['All', ...states]
})

const sexOptions = computed(() => {
  const sexes = [...new Set(healthData.value.map((item) => item.sex).filter(Boolean))].sort()
  return ['All', ...sexes]
})

const cancerTypeOptions = computed(() => {
  const types = [...new Set(healthData.value.map((item) => item.cancer_type).filter(Boolean))].sort()
  return ['All', ...types]
})

const filteredPollutionState = computed(() => {
  return statePollutionData.value.filter((item) => {
    const yearMatch = selectedYear.value === 'All' || String(item.report_year) === String(selectedYear.value)
    const metalMatch = selectedMetal.value === 'All' || item.metal === selectedMetal.value
    const stateMatch = selectedState.value === 'All' || item.state === selectedState.value
    return yearMatch && metalMatch && stateMatch
  })
})

const filteredPollutionFacility = computed(() => {
  return facilityPollutionData.value.filter((item) => {
    const yearMatch = selectedYear.value === 'All' || String(item.report_year) === String(selectedYear.value)
    const metalMatch = selectedMetal.value === 'All' || item.metal === selectedMetal.value
    const stateMatch = selectedState.value === 'All' || item.state === selectedState.value
    return yearMatch && metalMatch && stateMatch
  })
})

const filteredHealth = computed(() => {
  return healthData.value.filter((item) => {
    const yearMatch =
      selectedYear.value === 'All' ||
      String(item.year) === String(selectedYear.value) ||
      String(item.report_year) === String(selectedYear.value)

    const sexMatch = selectedSex.value === 'All' || item.sex === selectedSex.value
    const cancerMatch = selectedCancerType.value === 'All' || item.cancer_type === selectedCancerType.value

    return yearMatch && sexMatch && cancerMatch
  })
})

const totalLead = computed(() =>
  filteredPollutionFacility.value
    .filter((item) => item.metal === 'Lead')
    .reduce((sum, item) => sum + Number(item.total_air_emission_kg || 0), 0),
)

const totalMercury = computed(() =>
  filteredPollutionFacility.value
    .filter((item) => item.metal === 'Mercury')
    .reduce((sum, item) => sum + Number(item.total_air_emission_kg || 0), 0),
)

const totalCadmium = computed(() =>
  filteredPollutionFacility.value
    .filter((item) => item.metal === 'Cadmium')
    .reduce((sum, item) => sum + Number(item.total_air_emission_kg || 0), 0),
)

const totalCases = computed(() =>
  filteredHealth.value.reduce((sum, item) => sum + Number(item.cancer_cases || 0), 0),
)

const totalDeaths = computed(() =>
  filteredHealth.value.reduce((sum, item) => sum + Number(item.cancer_deaths || 0), 0),
)

const avgFatalityRatio = computed(() => {
  if (!filteredHealth.value.length) return 0

  const total = filteredHealth.value.reduce((sum, item) => {
    const cases = Number(item.cancer_cases || 0)
    const deaths = Number(item.cancer_deaths || 0)
    return sum + (cases > 0 ? deaths / cases : 0)
  }, 0)

  return total / filteredHealth.value.length
})

const highestEmissionState = computed(() => {
  const map = new Map()

  filteredPollutionState.value.forEach((item) => {
    const state = item.state
    const val = Number(item.total_air_emission_kg || 0)
    map.set(state, (map.get(state) || 0) + val)
  })

  if (!map.size) return 'No data'

  return [...map.entries()].sort((a, b) => b[1] - a[1])[0][0]
})

const topCancerCondition = computed(() => {
  const map = new Map()

  filteredHealth.value.forEach((item) => {
    const type = item.cancer_type
    const val = Number(item.cancer_cases || 0)
    map.set(type, (map.get(type) || 0) + val)
  })

  if (!map.size) return 'No data'

  return [...map.entries()].sort((a, b) => b[1] - a[1])[0][0]
})

function formatNumber(value) {
  return Number(value || 0).toLocaleString()
}

function tooltipStyle() {
  return {
    backgroundColor: 'rgba(241, 248, 242, 0.97)',
    borderColor: 'rgba(210, 232, 214, 0.98)',
    borderWidth: 1,
    textStyle: { color: '#173a29', fontSize: 13 },
    extraCssText: `
      border-radius: 16px;
      box-shadow: 0 18px 34px rgba(27, 67, 50, 0.10);
      backdrop-filter: blur(10px);
    `,
  }
}

function aggregateHealthTrend(data) {
  const map = new Map()

  data.forEach((item) => {
    const year = String(item.year)
    if (!map.has(year)) {
      map.set(year, { year, cases: 0, deaths: 0 })
    }

    const entry = map.get(year)
    entry.cases += Number(item.cancer_cases || 0)
    entry.deaths += Number(item.cancer_deaths || 0)
  })

  return [...map.values()].sort((a, b) => String(a.year).localeCompare(String(b.year)))
}

function aggregateFatality(data) {
  const map = new Map()

  data.forEach((item) => {
    const type = item.cancer_type
    if (!map.has(type)) {
      map.set(type, { cancer_type: type, cases: 0, deaths: 0 })
    }

    const entry = map.get(type)
    entry.cases += Number(item.cancer_cases || 0)
    entry.deaths += Number(item.cancer_deaths || 0)
  })

  return [...map.values()]
    .map((item) => ({
      cancer_type: item.cancer_type,
      ratio: item.cases > 0 ? item.deaths / item.cases : 0,
    }))
    .sort((a, b) => b.ratio - a.ratio)
}

function aggregateMetalTotals(data) {
  const map = new Map()

  data.forEach((item) => {
    const metal = item.metal
    const value = Number(item.total_air_emission_kg || 0)
    map.set(metal, (map.get(metal) || 0) + value)
  })

  return [...map.entries()].map(([metal, value]) => ({ metal, value }))
}

function aggregateStateMetal(data) {
  const states = [...new Set(data.map((item) => item.state).filter(Boolean))].sort()
  const metals = ['Lead', 'Mercury', 'Cadmium']

  const series = metals.map((metal) => ({
    name: metal,
    type: 'bar',
    barMaxWidth: 24,
    data: states.map((state) => {
      return data
        .filter((item) => item.state === state && item.metal === metal)
        .reduce((sum, item) => sum + Number(item.total_air_emission_kg || 0), 0)
    }),
  }))

  return { states, series }
}

function topFacilities(data) {
  return [...data]
    .sort((a, b) => Number(b.total_air_emission_kg || 0) - Number(a.total_air_emission_kg || 0))
    .slice(0, 10)
    .reverse()
}

function initCharts() {
  if (pollutionStateChartRef.value) pollutionStateChart = echarts.init(pollutionStateChartRef.value)
  if (topFacilityChartRef.value) topFacilityChart = echarts.init(topFacilityChartRef.value)
  if (metalTotalsChartRef.value) metalTotalsChart = echarts.init(metalTotalsChartRef.value)
  if (healthTrendChartRef.value) healthTrendChart = echarts.init(healthTrendChartRef.value)
  if (fatalityChartRef.value) fatalityChart = echarts.init(fatalityChartRef.value)
}

function updateCharts() {
  const pollutionState = aggregateStateMetal(filteredPollutionState.value)
  const facilities = topFacilities(filteredPollutionFacility.value)
  const metalTotals = aggregateMetalTotals(filteredPollutionFacility.value)
  const healthTrend = aggregateHealthTrend(filteredHealth.value)
  const fatality = aggregateFatality(filteredHealth.value).slice(0, 8).reverse()

  pollutionStateChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    legend: {
      top: 8,
      textStyle: { color: '#557260' },
    },
    grid: { left: 50, right: 20, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: pollutionState.states,
      axisLabel: { color: '#557260' },
      axisLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.14)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#557260' },
      splitLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.08)' } },
    },
    series: pollutionState.series.map((s, idx) => ({
      ...s,
      itemStyle: {
        borderRadius: [8, 8, 0, 0],
        color: ['#81c784', '#43a047', '#2e7d32'][idx],
      },
    })),
  })

  topFacilityChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 180, right: 20, top: 20, bottom: 20 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#557260' },
      splitLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.08)' } },
    },
    yAxis: {
      type: 'category',
      data: facilities.map((item) => item.facility_name),
      axisLabel: { color: '#173a29', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: facilities.map((item) => Number(item.total_air_emission_kg || 0)),
        barWidth: 16,
        itemStyle: {
          color: '#81c784',
          borderRadius: [0, 10, 10, 0],
        },
      },
    ],
  })

  metalTotalsChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', ...tooltipStyle() },
    series: [
      {
        type: 'pie',
        radius: ['42%', '70%'],
        center: ['50%', '52%'],
        data: metalTotals.map((item) => ({
          name: item.metal,
          value: item.value,
        })),
        label: { color: '#173a29' },
        itemStyle: {
          borderWidth: 2,
          borderColor: '#f8fbf8',
        },
        color: ['#81c784', '#43a047', '#2e7d32'],
      },
    ],
  })

  healthTrendChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...tooltipStyle() },
    legend: {
      top: 8,
      textStyle: { color: '#557260' },
    },
    grid: { left: 50, right: 20, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: healthTrend.map((item) => item.year),
      boundaryGap: false,
      axisLabel: { color: '#557260' },
      axisLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.14)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#557260' },
      splitLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.08)' } },
    },
    series: [
      {
        name: 'Cases',
        type: 'line',
        smooth: true,
        data: healthTrend.map((item) => item.cases),
        lineStyle: { width: 3, color: '#81c784' },
        itemStyle: { color: '#81c784' },
      },
      {
        name: 'Deaths',
        type: 'line',
        smooth: true,
        data: healthTrend.map((item) => item.deaths),
        lineStyle: { width: 3, color: '#43a047' },
        itemStyle: { color: '#43a047' },
      },
    ],
  })

  fatalityChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 190, right: 20, top: 20, bottom: 20 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#557260' },
      splitLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.08)' } },
    },
    yAxis: {
      type: 'category',
      data: fatality.map((item) => item.cancer_type),
      axisLabel: { color: '#173a29', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: fatality.map((item) => Number(item.ratio.toFixed(3))),
        barWidth: 16,
        itemStyle: {
          color: '#3f8f46',
          borderRadius: [0, 10, 10, 0],
        },
      },
    ],
  })
}

function resizeCharts() {
  pollutionStateChart?.resize()
  topFacilityChart?.resize()
  metalTotalsChart?.resize()
  healthTrendChart?.resize()
  fatalityChart?.resize()
}

function disposeCharts() {
  pollutionStateChart?.dispose()
  topFacilityChart?.dispose()
  metalTotalsChart?.dispose()
  healthTrendChart?.dispose()
  fatalityChart?.dispose()
}

watch([filteredPollutionState, filteredPollutionFacility, filteredHealth], async () => {
  await nextTick()
  updateCharts()
})

onMounted(async () => {
  await loadDashboardData()
  await nextTick()
  initCharts()
  updateCharts()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>

<template>
  <div class="dashboard-page">
    <section class="hero-panel">
      <div class="hero-left">
        <span class="eyebrow">EcoTech Combined Impact Dashboard</span>
        <h1>Pollution and cancer burden in one view</h1>
        <p>
          This dashboard combines heavy metal pollution data with cancer case and death data to
          present the environmental and health impact story together.
        </p>
      </div>

      <div class="hero-right">
        <div class="hero-chip">Lead, Mercury, Cadmium</div>
        <div class="hero-chip">Pollution + Health</div>
        <div class="hero-chip">Evidence-driven insights</div>
      </div>
    </section>

    <section class="filter-panel">
      <div class="filter-group">
        <label>Year</label>
        <select v-model="selectedYear">
          <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Metal</label>
        <select v-model="selectedMetal">
          <option v-for="metal in metalOptions" :key="metal" :value="metal">{{ metal }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label>State</label>
        <select v-model="selectedState">
          <option v-for="state in stateOptions" :key="state" :value="state">{{ state }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Sex</label>
        <select v-model="selectedSex">
          <option v-for="sex in sexOptions" :key="sex" :value="sex">{{ sex }}</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Cancer Type</label>
        <select v-model="selectedCancerType">
          <option v-for="type in cancerTypeOptions" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>
    </section>

    <section v-if="loading" class="status-card">
      <h3>Loading dashboard...</h3>
      <p>Please wait while the combined data is being loaded.</p>
    </section>

    <section v-else-if="error" class="status-card error-card">
      <h3>Unable to load dashboard</h3>
      <p>{{ error }}</p>
    </section>

    <template v-else>
      <section class="stats-grid">
        <article class="stat-card">
          <span class="stat-label">Lead Emissions</span>
          <h2>{{ formatNumber(totalLead) }}</h2>
          <p>Total air emission load for lead.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Mercury Emissions</span>
          <h2>{{ formatNumber(totalMercury) }}</h2>
          <p>Total air emission load for mercury.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Cadmium Emissions</span>
          <h2>{{ formatNumber(totalCadmium) }}</h2>
          <p>Total air emission load for cadmium.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Cancer Cases</span>
          <h2>{{ formatNumber(totalCases) }}</h2>
          <p>Total visible cancer cases under current filters.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Cancer Deaths</span>
          <h2>{{ formatNumber(totalDeaths) }}</h2>
          <p>Total visible cancer deaths under current filters.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Avg Fatality Ratio</span>
          <h2>{{ avgFatalityRatio.toFixed(3) }}</h2>
          <p>Deaths relative to cases in current view.</p>
        </article>
      </section>

      <section class="insight-grid">
        <article class="insight-card">
          <span>Highest emission state</span>
          <h3>{{ highestEmissionState }}</h3>
          <p>This state currently shows the largest visible air-emission burden.</p>
        </article>

        <article class="insight-card">
          <span>Top cancer burden</span>
          <h3>{{ topCancerCondition }}</h3>
          <p>This condition has the highest visible case count under selected filters.</p>
        </article>
      </section>

      <section class="chart-shell">
        <div class="section-header">
          <div>
            <span class="section-tag">Pollution by State</span>
            <h2>Heavy metal air emissions across states</h2>
          </div>
        </div>
        <div ref="pollutionStateChartRef" class="chart-box large-chart"></div>
      </section>

      <section class="chart-grid">
        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">Facilities</span>
              <h2>Top polluted facilities</h2>
            </div>
          </div>
          <div ref="topFacilityChartRef" class="chart-box"></div>
        </article>

        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">Metal Comparison</span>
              <h2>Overall pollution share</h2>
            </div>
          </div>
          <div ref="metalTotalsChartRef" class="chart-box"></div>
        </article>
      </section>

      <section class="chart-shell">
        <div class="section-header">
          <div>
            <span class="section-tag">Health Trend</span>
            <h2>Cancer cases and deaths over time</h2>
          </div>
        </div>
        <div ref="healthTrendChartRef" class="chart-box large-chart"></div>
      </section>

      <section class="chart-shell">
        <div class="section-header">
          <div>
            <span class="section-tag">Health Severity</span>
            <h2>Highest fatality ratio conditions</h2>
          </div>
        </div>
        <div ref="fatalityChartRef" class="chart-box"></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  padding: 30px 24px 80px;
  background:
    radial-gradient(circle at 88% 8%, rgba(129, 199, 132, 0.12), transparent 18%),
    radial-gradient(circle at 12% 92%, rgba(67, 160, 71, 0.08), transparent 22%),
    linear-gradient(180deg, #f8fbf8 0%, #eef4ef 100%);
  color: #173a29;
}

.hero-panel,
.filter-panel,
.stats-grid,
.insight-grid,
.chart-shell,
.status-card {
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}

.hero-panel,
.filter-panel,
.stat-card,
.insight-card,
.chart-shell,
.status-card {
  border: 1px solid rgba(226, 238, 227, 0.98);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.76) 0%, rgba(251, 253, 251, 0.84) 100%);
  box-shadow:
    0 18px 34px rgba(27, 67, 50, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(14px);
}

.hero-panel {
  border-radius: 28px;
  padding: 32px;
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 20px;
  margin-bottom: 24px;
}

.eyebrow,
.section-tag,
.stat-label,
.insight-card span {
  display: inline-flex;
  margin: 0 0 14px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(232, 245, 233, 0.9);
  border: 1px solid rgba(207, 232, 209, 0.98);
  color: #2e7d32;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-left h1 {
  margin: 0 0 12px;
  font-size: clamp(2rem, 4vw, 3.6rem);
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -1px;
  color: #143324;
}

.hero-left p {
  margin: 0;
  line-height: 1.8;
  color: #557260;
}

.hero-right {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-content: center;
}

.hero-chip {
  padding: 12px 16px;
  border-radius: 999px;
  background: linear-gradient(180deg, #eff8f0 0%, #e7f4e8 100%);
  border: 1px solid rgba(210, 232, 214, 0.98);
  color: #173a29;
  font-weight: 600;
  height: fit-content;
}

.filter-panel {
  border-radius: 24px;
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-size: 0.9rem;
  color: #173a29;
  font-weight: 600;
}

.filter-group select {
  width: 100%;
  background: rgba(255, 255, 255, 0.9);
  color: #173a29;
  border: 1px solid rgba(210, 232, 214, 0.98);
  border-radius: 14px;
  padding: 14px;
  outline: none;
}

.status-card {
  border-radius: 24px;
  padding: 28px;
  margin-bottom: 24px;
}

.status-card h3 {
  margin: 0 0 10px;
  color: #143324;
}

.status-card p {
  margin: 0;
  color: #557260;
}

.error-card {
  border-color: rgba(220, 120, 120, 0.28);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 24px;
  padding: 24px;
}

.stat-card h2 {
  margin: 0 0 8px;
  font-size: 2rem;
  color: #143324;
}

.stat-card p {
  margin: 0;
  color: #557260;
  line-height: 1.6;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.insight-card {
  border-radius: 24px;
  padding: 24px;
}

.insight-card h3 {
  margin: 0 0 8px;
  font-size: 1.4rem;
  color: #143324;
}

.insight-card p {
  margin: 0;
  line-height: 1.7;
  color: #557260;
}

.chart-shell {
  border-radius: 28px;
  padding: 24px;
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 20px;
  margin-bottom: 16px;
}

.section-header h2 {
  margin: 0;
  font-size: 1.45rem;
  color: #143324;
}

.section-header.compact {
  margin-bottom: 10px;
}

.chart-grid {
  max-width: 1400px;
  margin: 0 auto 24px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.chart-grid .chart-shell {
  margin: 0;
}

.chart-box {
  width: 100%;
  height: 420px;
}

.large-chart {
  height: 500px;
}

@media (max-width: 1100px) {
  .hero-panel,
  .filter-panel,
  .stats-grid,
  .insight-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    padding: 18px 14px 60px;
  }

  .chart-box,
  .large-chart {
    height: 340px;
  }

  .hero-panel,
  .filter-panel,
  .stat-card,
  .insight-card,
  .chart-shell,
  .status-card {
    border-radius: 20px;
  }
}
</style>