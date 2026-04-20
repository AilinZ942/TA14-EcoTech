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

const focusedCancerTypes = [
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

const focusedCancerSet = new Set(focusedCancerTypes)

async function loadHealthData() {
  try {
    loading.value = true
    error.value = ''

    const res = await api.getHealthAll()
    const items = Array.isArray(res.items) ? res.items : []
    healthData.value = items.filter((item) => focusedCancerSet.has(item.cancer_type))
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

const cancerTypeOptions = computed(() => ['All', ...focusedCancerTypes])

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
  const grouped = aggregateByCancerType(compareData.value)
  if (!grouped.length) return 'No data'
  return [...grouped].sort((a, b) => b.cases - a.cases)[0].cancer_type
})

const strongestRiskPattern = computed(() => {
  const grouped = aggregateByCancerType(compareData.value)
  if (!grouped.length) return 'No data'
  return [...grouped].sort((a, b) => b.avgRatio - a.avgRatio)[0].cancer_type
})

const yearsCovered = computed(() => {
  const years = filteredData.value.map((item) => Number(item.year)).filter(Boolean)
  if (!years.length) return 'No years'
  return `${Math.min(...years)} - ${Math.max(...years)}`
})

function aggregateByYear(data) {
  const map = new Map()

  data.forEach((item) => {
    const year = Number(item.year)
    if (!year) return

    if (!map.has(year)) {
      map.set(year, { year, cases: 0, deaths: 0 })
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
    backgroundColor: 'rgba(10, 14, 20, 0.96)',
    borderColor: 'rgba(0, 214, 143, 0.18)',
    borderWidth: 1,
    textStyle: {
      color: '#f7fffb',
      fontSize: 13,
    },
    extraCssText: `
      border-radius: 18px;
      box-shadow: 0 18px 40px rgba(0,0,0,0.35);
      backdrop-filter: blur(10px);
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

  const topCases = [...cancerGroups].sort((a, b) => b.cases - a.cases).slice(0, 6).reverse()
  const topDeaths = [...cancerGroups].sort((a, b) => b.deaths - a.deaths).slice(0, 6).reverse()
  const topFatality = [...cancerGroups]
    .sort((a, b) => b.avgRatio - a.avgRatio)
    .slice(0, 6)
    .reverse()

  trendChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...tooltipStyle() },
    legend: {
      top: 10,
      textStyle: { color: '#d9f7ec', fontWeight: 600 },
    },
    grid: { left: 45, right: 24, top: 60, bottom: 35 },
    xAxis: {
      type: 'category',
      data: yearly.map((item) => item.year),
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
      axisLabel: { color: '#b8d9ce' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: { color: '#b8d9ce' },
    },
    series: [
      {
        name: 'Cancer Cases',
        type: 'line',
        smooth: true,
        data: yearly.map((item) => item.cases),
        lineStyle: { width: 3, color: '#25d68a' },
        itemStyle: { color: '#25d68a' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37,214,138,0.26)' },
            { offset: 1, color: 'rgba(37,214,138,0.02)' },
          ]),
        },
      },
      {
        name: 'Cancer Deaths',
        type: 'line',
        smooth: true,
        data: yearly.map((item) => item.deaths),
        lineStyle: { width: 3, color: '#77f2b7' },
        itemStyle: { color: '#77f2b7' },
      },
    ],
  })

  casesChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 175, right: 20, top: 10, bottom: 20 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: { color: '#b8d9ce' },
    },
    yAxis: {
      type: 'category',
      data: topCases.map((item) => item.cancer_type),
      axisLabel: { color: '#e5fff3', fontWeight: 600 },
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
          color: '#25d68a',
        },
      },
    ],
  })

  deathsChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 175, right: 20, top: 10, bottom: 20 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: { color: '#b8d9ce' },
    },
    yAxis: {
      type: 'category',
      data: topDeaths.map((item) => item.cancer_type),
      axisLabel: { color: '#e5fff3', fontWeight: 600 },
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
          color: '#77f2b7',
        },
      },
    ],
  })

  fatalityChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    grid: { left: 175, right: 20, top: 10, bottom: 20 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: {
        color: '#b8d9ce',
        formatter: (value) => Number(value).toFixed(2),
      },
    },
    yAxis: {
      type: 'category',
      data: topFatality.map((item) => item.cancer_type),
      axisLabel: { color: '#e5fff3', fontWeight: 600 },
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
          color: '#b4ffd6',
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
  <div class="health-dashboard">
    <section class="hero">
      <div class="hero-left">
        <div class="badge">EcoTech · Health Impact Dashboard</div>
        <h1>Understanding toxic exposure through health patterns</h1>
        <p>
          Explore cancer cases, deaths, and fatality patterns across selected conditions that are
          relevant to toxic environmental exposure concerns.
        </p>

        <div class="hero-tags">
          <span>Environmental health</span>
          <span>Cancer impact</span>
          <span>Evidence-driven insights</span>
        </div>
      </div>

      <div class="hero-right">
        <div class="hero-stat">
          <span>Total Cases</span>
          <h2>{{ formatCompactNumber(totalCases) }}</h2>
        </div>
        <div class="hero-stat">
          <span>Total Deaths</span>
          <h2>{{ formatCompactNumber(totalDeaths) }}</h2>
        </div>
        <div class="hero-stat">
          <span>Fatality Ratio</span>
          <h2>{{ avgFatalityRatio.toFixed(3) }}</h2>
        </div>
      </div>
    </section>

    <section class="filter-strip">
      <div class="filter-card">
        <label>Year</label>
        <select v-model="selectedYear">
          <option v-for="year in yearOptions" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
      </div>

      <div class="filter-card">
        <label>Sex</label>
        <select v-model="selectedSex">
          <option v-for="sex in sexOptions" :key="sex" :value="sex">
            {{ sex }}
          </option>
        </select>
      </div>

      <div class="filter-card">
        <label>Cancer Type</label>
        <select v-model="selectedCancerType">
          <option v-for="type in cancerTypeOptions" :key="type" :value="type">
            {{ type }}
          </option>
        </select>
      </div>
    </section>

    <section v-if="loading" class="message-card">
      <h3>Loading dashboard...</h3>
      <p>Fetching health data from the database.</p>
    </section>

    <section v-else-if="error" class="message-card error">
      <h3>Could not load dashboard</h3>
      <p>{{ error }}</p>
    </section>

    <template v-else>
      <section class="summary-grid">
        <article class="summary-card">
          <span class="mini-label">Years covered</span>
          <h3>{{ yearsCovered }}</h3>
          <p>Visible time span under the current filter view.</p>
        </article>

        <article class="summary-card">
          <span class="mini-label">Most reported condition</span>
          <h3>{{ dominantCancer }}</h3>
          <p>The condition with the highest visible case volume.</p>
        </article>

        <article class="summary-card">
          <span class="mini-label">Highest severity signal</span>
          <h3>{{ strongestRiskPattern }}</h3>
          <p>The condition showing the strongest fatality ratio pattern.</p>
        </article>
      </section>

      <section class="feature-panel">
        <div class="panel-header">
          <div>
            <span class="mini-label">Trend Overview</span>
            <h2>Health impact across time</h2>
          </div>
          <p>
            This view compares case counts and deaths to show how the health burden changes across
            years.
          </p>
        </div>
        <div ref="trendChartRef" class="chart large"></div>
      </section>

      <section class="dual-grid">
        <article class="feature-panel compact">
          <div class="panel-header compact-header">
            <div>
              <span class="mini-label">Case Burden</span>
              <h2>Top cancer cases</h2>
            </div>
          </div>
          <div ref="casesChartRef" class="chart"></div>
        </article>

        <article class="feature-panel compact">
          <div class="panel-header compact-header">
            <div>
              <span class="mini-label">Death Burden</span>
              <h2>Top cancer deaths</h2>
            </div>
          </div>
          <div ref="deathsChartRef" class="chart"></div>
        </article>
      </section>

      <section class="feature-panel">
        <div class="panel-header">
          <div>
            <span class="mini-label">Severity Lens</span>
            <h2>Highest fatality ratios</h2>
          </div>
          <p>
            This helps identify which selected conditions show the highest deaths relative to cases.
          </p>
        </div>
        <div ref="fatalityChartRef" class="chart"></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.health-dashboard {
  min-height: 100vh;
  padding: 28px 24px 80px;
  background:
    radial-gradient(circle at top left, rgba(0, 214, 143, 0.12), transparent 26%),
    radial-gradient(circle at top right, rgba(120, 255, 200, 0.08), transparent 22%),
    linear-gradient(180deg, #07110d 0%, #0c1814 50%, #101c18 100%);
  color: #f4fff8;
}

.hero,
.filter-strip,
.summary-grid,
.feature-panel,
.message-card {
  max-width: 1380px;
  margin-left: auto;
  margin-right: auto;
}

.hero,
.filter-card,
.summary-card,
.feature-panel,
.message-card,
.hero-right {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 22px 50px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(12px);
}

.hero {
  border-radius: 32px;
  padding: 34px;
  display: grid;
  grid-template-columns: 1.5fr 0.9fr;
  gap: 24px;
  margin-bottom: 24px;
}

.badge,
.mini-label {
  display: inline-block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #8df0bf;
  font-weight: 700;
  margin-bottom: 12px;
}

.hero-left h1 {
  margin: 0 0 14px;
  font-size: clamp(2rem, 4vw, 3.8rem);
  line-height: 1.02;
  max-width: 760px;
}

.hero-left p {
  margin: 0;
  color: #bfd9cf;
  line-height: 1.75;
  max-width: 720px;
  font-size: 1rem;
}

.hero-tags {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 22px;
}

.hero-tags span {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(37, 214, 138, 0.1);
  border: 1px solid rgba(37, 214, 138, 0.16);
  color: #e6fff3;
  font-size: 0.92rem;
}

.hero-right {
  border-radius: 24px;
  padding: 20px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.hero-stat {
  padding: 18px;
  border-radius: 20px;
  background: rgba(7, 17, 13, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.hero-stat span {
  display: block;
  color: #9ec8b7;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.hero-stat h2 {
  margin: 0;
  font-size: 2rem;
  color: #ffffff;
}

.filter-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.filter-card {
  border-radius: 22px;
  padding: 18px;
}

.filter-card label {
  display: block;
  margin-bottom: 8px;
  color: #d7f7e6;
  font-weight: 600;
}

.filter-card select {
  width: 100%;
  padding: 14px 14px;
  border-radius: 14px;
  border: 1px solid rgba(141, 240, 191, 0.14);
  background: rgba(7, 17, 13, 0.82);
  color: #f4fff8;
  outline: none;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.summary-card {
  border-radius: 24px;
  padding: 24px;
}

.summary-card h3 {
  margin: 0 0 8px;
  font-size: 1.45rem;
  color: #ffffff;
}

.summary-card p {
  margin: 0;
  color: #bfd9cf;
  line-height: 1.7;
}

.feature-panel {
  border-radius: 28px;
  padding: 24px;
  margin-bottom: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: end;
  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.55rem;
}

.panel-header p {
  margin: 0;
  color: #bfd9cf;
  line-height: 1.7;
  max-width: 520px;
  text-align: right;
}

.dual-grid {
  max-width: 1380px;
  margin: 0 auto 24px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.compact {
  margin-bottom: 0;
}

.compact-header {
  margin-bottom: 10px;
}

.chart {
  width: 100%;
  height: 420px;
}

.chart.large {
  height: 500px;
}

.message-card {
  border-radius: 24px;
  padding: 24px;
  margin-bottom: 24px;
}

.message-card.error {
  border-color: rgba(255, 120, 120, 0.16);
}

@media (max-width: 1100px) {
  .hero,
  .summary-grid,
  .dual-grid,
  .filter-strip {
    grid-template-columns: 1fr;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .panel-header p {
    text-align: left;
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .health-dashboard {
    padding: 18px 14px 60px;
  }

  .hero,
  .feature-panel,
  .summary-card,
  .filter-card,
  .message-card {
    border-radius: 22px;
  }

  .chart,
  .chart.large {
    height: 340px;
  }

  .hero {
    padding: 24px;
  }
}
</style>