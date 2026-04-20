<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { api } from '@/api'
import * as echarts from 'echarts'

const loading = ref(true)
const error = ref('')
const healthData = ref([])

const selectedYear = ref('All')
const selectedSex = ref('All')
const selectedCancerType = ref('All')

const trendChartRef = ref(null)
const casesChartRef = ref(null)
const deathsChartRef = ref(null)
const fatalityChartRef = ref(null)

let trendChart = null
let casesChart = null
let deathsChart = null
let fatalityChart = null

const allowedCancerTypes = [
  'Lung cancer',
  'Liver cancer',
  'Kidney cancer',
  'Bladder cancer',
  'Acute lymphoblastic leukaemia',
  'Acute myeloid leukaemia',
  'Chronic lymphocytic leukaemia',
  'Chronic myeloid leukaemia',
  'Non-Hodgkin lymphoma',
]

const allowedCancerSet = new Set(allowedCancerTypes)

async function loadHealthData() {
  try {
    loading.value = true
    error.value = ''

    const res = await api.getHealthAll()
    const items = Array.isArray(res.items) ? res.items : []

    healthData.value = items.filter((item) => allowedCancerSet.has(item.cancer_type))
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to load dashboard data.'
  } finally {
    loading.value = false
  }
}

const yearOptions = computed(() => {
  const years = [...new Set(healthData.value.map((item) => Number(item.year)).filter(Boolean))].sort(
    (a, b) => a - b,
  )
  return ['All', ...years]
})

const sexOptions = computed(() => {
  const values = [...new Set(healthData.value.map((item) => item.sex).filter(Boolean))].sort()
  return ['All', ...values]
})

const cancerTypeOptions = computed(() => ['All', ...allowedCancerTypes])

const filteredData = computed(() => {
  return healthData.value.filter((item) => {
    const matchYear =
      selectedYear.value === 'All' || Number(item.year) === Number(selectedYear.value)
    const matchSex = selectedSex.value === 'All' || item.sex === selectedSex.value
    const matchCancer =
      selectedCancerType.value === 'All' || item.cancer_type === selectedCancerType.value

    return matchYear && matchSex && matchCancer
  })
})

const compareData = computed(() => {
  return healthData.value.filter((item) => {
    const matchYear =
      selectedYear.value === 'All' || Number(item.year) === Number(selectedYear.value)
    const matchSex = selectedSex.value === 'All' || item.sex === selectedSex.value
    return matchYear && matchSex
  })
})

const totalRecords = computed(() => filteredData.value.length)

const totalCases = computed(() =>
  filteredData.value.reduce((sum, item) => sum + Number(item.cancer_cases || 0), 0),
)

const totalDeaths = computed(() =>
  filteredData.value.reduce((sum, item) => sum + Number(item.cancer_deaths || 0), 0),
)

const avgFatalityRatio = computed(() => {
  if (!filteredData.value.length) return 0

  const total = filteredData.value.reduce((sum, item) => {
    const cases = Number(item.cancer_cases || 0)
    const deaths = Number(item.cancer_deaths || 0)
    return sum + (cases > 0 ? deaths / cases : 0)
  }, 0)

  return total / filteredData.value.length
})

const dominantCancer = computed(() => {
  const aggregated = aggregateByCancerType(compareData.value)
  if (!aggregated.length) return 'No data'

  return [...aggregated].sort((a, b) => b.cases - a.cases)[0].cancer_type
})

const insightText = computed(() => {
  if (!filteredData.value.length) {
    return 'No matching records found for the selected filters.'
  }

  return `Showing ${formatCompactNumber(totalCases.value)} total cases and ${formatCompactNumber(totalDeaths.value)} total deaths for ${selectedCancerType.value === 'All' ? 'the selected cancers' : selectedCancerType.value}.`
})

function aggregateByYear(data) {
  const map = new Map()

  data.forEach((item) => {
    const year = Number(item.year)
    if (!year) return

    if (!map.has(year)) {
      map.set(year, {
        year,
        cases: 0,
        deaths: 0,
      })
    }

    const entry = map.get(year)
    entry.cases += Number(item.cancer_cases || 0)
    entry.deaths += Number(item.cancer_deaths || 0)
  })

  return [...map.values()].sort((a, b) => a.year - b.year)
}

function aggregateByCancerType(data) {
  const map = new Map()

  data.forEach((item) => {
    const type = item.cancer_type
    if (!type) return

    if (!map.has(type)) {
      map.set(type, {
        cancer_type: type,
        cases: 0,
        deaths: 0,
      })
    }

    const entry = map.get(type)
    entry.cases += Number(item.cancer_cases || 0)
    entry.deaths += Number(item.cancer_deaths || 0)
  })

  return [...map.values()].map((item) => ({
    cancer_type: item.cancer_type,
    cases: item.cases,
    deaths: item.deaths,
    avgRatio: item.cases > 0 ? item.deaths / item.cases : 0,
  }))
}

function formatCompactNumber(value) {
  return Number(value || 0).toLocaleString()
}

function tooltipStyle() {
  return {
    backgroundColor: 'rgba(9, 16, 13, 0.96)',
    borderColor: 'rgba(120, 255, 165, 0.22)',
    borderWidth: 1,
    textStyle: {
      color: '#f5fff7',
      fontSize: 13,
    },
    extraCssText: `
      border-radius: 16px;
      box-shadow: 0 18px 40px rgba(0,0,0,0.35);
      backdrop-filter: blur(8px);
    `,
  }
}

function initCharts() {
  if (trendChartRef.value) trendChart = echarts.init(trendChartRef.value)
  if (casesChartRef.value) casesChart = echarts.init(casesChartRef.value)
  if (deathsChartRef.value) deathsChart = echarts.init(deathsChartRef.value)
  if (fatalityChartRef.value) fatalityChart = echarts.init(fatalityChartRef.value)
}

function updateCharts() {
  const yearly = aggregateByYear(filteredData.value)
  const cancerGroups = aggregateByCancerType(compareData.value)

  const topCases = [...cancerGroups].sort((a, b) => b.cases - a.cases).slice(0, 8).reverse()
  const topDeaths = [...cancerGroups].sort((a, b) => b.deaths - a.deaths).slice(0, 8).reverse()
  const topFatality = [...cancerGroups]
    .sort((a, b) => b.avgRatio - a.avgRatio)
    .slice(0, 8)
    .reverse()

  trendChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...tooltipStyle(),
    },
    legend: {
      top: 8,
      textStyle: { color: '#d9f7e2', fontWeight: 600 },
    },
    grid: {
      left: 50,
      right: 24,
      top: 60,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: yearly.map((item) => item.year),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.18)' } },
      axisLabel: { color: '#b7d9c1' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#b7d9c1' },
    },
    series: [
      {
        name: 'Cases',
        type: 'line',
        smooth: true,
        data: yearly.map((item) => item.cases),
        lineStyle: { width: 3, color: '#66e087' },
        itemStyle: { color: '#66e087' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102,224,135,0.28)' },
            { offset: 1, color: 'rgba(102,224,135,0.02)' },
          ]),
        },
      },
      {
        name: 'Deaths',
        type: 'line',
        smooth: true,
        data: yearly.map((item) => item.deaths),
        lineStyle: { width: 3, color: '#2bb673' },
        itemStyle: { color: '#2bb673' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(43,182,115,0.24)' },
            { offset: 1, color: 'rgba(43,182,115,0.02)' },
          ]),
        },
      },
    ],
  })

  casesChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 180, right: 20, top: 20, bottom: 26 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#b7d9c1' },
    },
    yAxis: {
      type: 'category',
      data: topCases.map((item) => item.cancer_type),
      axisLabel: { color: '#d9f7e2', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: topCases.map((item) => item.cases),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: '#66e087',
        },
      },
    ],
  })

  deathsChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 180, right: 20, top: 20, bottom: 26 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: '#b7d9c1' },
    },
    yAxis: {
      type: 'category',
      data: topDeaths.map((item) => item.cancer_type),
      axisLabel: { color: '#d9f7e2', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: topDeaths.map((item) => item.deaths),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: '#2bb673',
        },
      },
    ],
  })

  fatalityChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 180, right: 20, top: 20, bottom: 26 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: {
        color: '#b7d9c1',
        formatter: (value) => Number(value).toFixed(2),
      },
    },
    yAxis: {
      type: 'category',
      data: topFatality.map((item) => item.cancer_type),
      axisLabel: { color: '#d9f7e2', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: topFatality.map((item) => Number(item.avgRatio.toFixed(3))),
        barWidth: 16,
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: '#9fffc0',
        },
      },
    ],
  })
}

function resizeCharts() {
  trendChart?.resize()
  casesChart?.resize()
  deathsChart?.resize()
  fatalityChart?.resize()
}

function disposeCharts() {
  trendChart?.dispose()
  casesChart?.dispose()
  deathsChart?.dispose()
  fatalityChart?.dispose()

  trendChart = null
  casesChart = null
  deathsChart = null
  fatalityChart = null
}

watch([filteredData, compareData], async () => {
  await nextTick()
  updateCharts()
})

onMounted(async () => {
  await loadHealthData()
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
      <div class="hero-copy">
        <span class="eyebrow">EcoTech Health Dashboard</span>
        <h1>Toxic exposure and cancer impact overview</h1>
        <p>
          This dashboard presents selected cancer conditions linked to toxic exposure concerns.
          It helps users explore case volume, deaths, and fatality patterns across time.
        </p>

        <div class="hero-highlights">
          <div class="mini-pill">Health trends</div>
          <div class="mini-pill">Severity patterns</div>
          <div class="mini-pill">Filter by year, sex, and condition</div>
        </div>
      </div>

      <div class="hero-side-card">
        <div class="side-label">Current view</div>
        <div class="side-value">{{ selectedCancerType === 'All' ? 'All selected cancers' : selectedCancerType }}</div>
        <p>{{ insightText }}</p>
      </div>
    </section>

    <section class="filter-panel">
      <div class="filter-group">
        <label>Year</label>
        <select v-model="selectedYear">
          <option v-for="year in yearOptions" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label>Sex</label>
        <select v-model="selectedSex">
          <option v-for="sex in sexOptions" :key="sex" :value="sex">
            {{ sex }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label>Cancer Type</label>
        <select v-model="selectedCancerType">
          <option v-for="type in cancerTypeOptions" :key="type" :value="type">
            {{ type }}
          </option>
        </select>
      </div>
    </section>

    <section v-if="loading" class="status-card">
      <h3>Loading dashboard...</h3>
      <p>Please wait while health data is being fetched.</p>
    </section>

    <section v-else-if="error" class="status-card error-card">
      <h3>Unable to load dashboard</h3>
      <p>{{ error }}</p>
    </section>

    <template v-else>
      <section class="stats-grid">
        <article class="stat-card">
          <span class="stat-label">Records</span>
          <h2>{{ formatCompactNumber(totalRecords) }}</h2>
          <p>Filtered dataset rows currently visible.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Total Cases</span>
          <h2>{{ formatCompactNumber(totalCases) }}</h2>
          <p>Combined cancer cases under the current filters.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Total Deaths</span>
          <h2>{{ formatCompactNumber(totalDeaths) }}</h2>
          <p>Combined cancer deaths under the current filters.</p>
        </article>

        <article class="stat-card">
          <span class="stat-label">Avg. Fatality Ratio</span>
          <h2>{{ avgFatalityRatio.toFixed(3) }}</h2>
          <p>Average deaths-to-cases ratio across visible rows.</p>
        </article>
      </section>

      <section class="insight-grid">
        <article class="insight-card">
          <span>Most dominant condition</span>
          <h3>{{ dominantCancer }}</h3>
          <p>This condition currently contributes the highest visible case count.</p>
        </article>

        <article class="insight-card">
          <span>Filter summary</span>
          <h3>
            {{ selectedYear === 'All' ? 'All years' : selectedYear }},
            {{ selectedSex === 'All' ? 'All sexes' : selectedSex }}
          </h3>
          <p>Use filters to sharpen the health story and compare different patterns.</p>
        </article>
      </section>

      <section class="chart-shell trend-shell">
        <div class="section-header">
          <div>
            <span class="section-tag">Trend Analysis</span>
            <h2>Cases and deaths over time</h2>
          </div>
          <p>
            This chart helps show whether the selected cancer conditions rise, fall, or remain stable
            over the years.
          </p>
        </div>
        <div ref="trendChartRef" class="chart-box large-chart"></div>
      </section>

      <section class="chart-grid">
        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">Cases</span>
              <h2>Top conditions by case count</h2>
            </div>
          </div>
          <div ref="casesChartRef" class="chart-box"></div>
        </article>

        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">Deaths</span>
              <h2>Top conditions by death count</h2>
            </div>
          </div>
          <div ref="deathsChartRef" class="chart-box"></div>
        </article>
      </section>

      <section class="chart-shell">
        <div class="section-header">
          <div>
            <span class="section-tag">Severity</span>
            <h2>Highest fatality ratio conditions</h2>
          </div>
          <p>
            Higher ratio means deaths are large relative to cases. This helps highlight more severe
            conditions in the selected view.
          </p>
        </div>
        <div ref="fatalityChartRef" class="chart-box"></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  padding: 32px 24px 80px;
  background:
    radial-gradient(circle at top left, rgba(71, 196, 120, 0.14), transparent 30%),
    radial-gradient(circle at top right, rgba(95, 255, 174, 0.08), transparent 24%),
    linear-gradient(180deg, #08120d 0%, #0d1d15 55%, #11261b 100%);
  color: #f3fff7;
}

.hero-panel {
  max-width: 1400px;
  margin: 0 auto 28px;
  display: grid;
  grid-template-columns: 1.5fr 0.9fr;
  gap: 20px;
  align-items: stretch;
}

.hero-copy,
.hero-side-card,
.filter-panel,
.stat-card,
.chart-shell,
.insight-card,
.status-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(12px);
}

.hero-copy {
  border-radius: 28px;
  padding: 34px;
}

.eyebrow,
.section-tag,
.side-label,
.stat-label,
.insight-card span {
  display: inline-block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #8de8aa;
  margin-bottom: 12px;
  font-weight: 700;
}

.hero-copy h1 {
  margin: 0 0 14px;
  font-size: clamp(2rem, 4vw, 3.6rem);
  line-height: 1.05;
  color: #f5fff8;
}

.hero-copy p {
  margin: 0;
  max-width: 760px;
  color: #b7d9c1;
  font-size: 1rem;
  line-height: 1.7;
}

.hero-highlights {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 22px;
}

.mini-pill {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(102, 224, 135, 0.12);
  border: 1px solid rgba(102, 224, 135, 0.18);
  color: #dfffea;
  font-size: 0.92rem;
}

.hero-side-card {
  border-radius: 28px;
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.side-value {
  font-size: 1.55rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.2;
  margin-bottom: 12px;
}

.hero-side-card p {
  margin: 0;
  line-height: 1.7;
  color: #b7d9c1;
}

.filter-panel {
  max-width: 1400px;
  margin: 0 auto 28px;
  border-radius: 24px;
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-size: 0.9rem;
  color: #d7f7e0;
  font-weight: 600;
}

.filter-group select {
  width: 100%;
  background: rgba(8, 18, 13, 0.82);
  color: #f3fff7;
  border: 1px solid rgba(122, 255, 170, 0.12);
  border-radius: 14px;
  padding: 14px 14px;
  outline: none;
  font-size: 0.95rem;
}

.status-card {
  max-width: 1400px;
  margin: 0 auto 28px;
  border-radius: 24px;
  padding: 28px;
}

.status-card h3,
.error-card h3 {
  margin: 0 0 8px;
}

.error-card {
  border-color: rgba(255, 120, 120, 0.18);
}

.stats-grid {
  max-width: 1400px;
  margin: 0 auto 28px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.stat-card {
  border-radius: 24px;
  padding: 24px;
}

.stat-card h2 {
  margin: 0 0 8px;
  font-size: 2rem;
  color: #ffffff;
}

.stat-card p {
  margin: 0;
  color: #b7d9c1;
  line-height: 1.6;
  font-size: 0.95rem;
}

.insight-grid {
  max-width: 1400px;
  margin: 0 auto 28px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.insight-card {
  border-radius: 24px;
  padding: 24px;
}

.insight-card h3 {
  margin: 0 0 10px;
  font-size: 1.4rem;
  color: #ffffff;
}

.insight-card p {
  margin: 0;
  color: #b7d9c1;
  line-height: 1.7;
}

.chart-shell {
  max-width: 1400px;
  margin: 0 auto 28px;
  border-radius: 28px;
  padding: 24px;
}

.trend-shell {
  padding-top: 28px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 20px;
  margin-bottom: 18px;
}

.section-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #ffffff;
}

.section-header p {
  margin: 0;
  max-width: 520px;
  color: #b7d9c1;
  line-height: 1.7;
  text-align: right;
}

.section-header.compact {
  margin-bottom: 12px;
}

.chart-grid {
  max-width: 1400px;
  margin: 0 auto;
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
  .chart-grid,
  .insight-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .filter-panel {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .section-header p {
    text-align: left;
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    padding: 20px 14px 60px;
  }

  .hero-copy,
  .hero-side-card,
  .filter-panel,
  .stat-card,
  .chart-shell,
  .insight-card,
  .status-card {
    border-radius: 20px;
  }

  .chart-box,
  .large-chart {
    height: 340px;
  }

  .hero-copy {
    padding: 24px;
  }
}
</style>