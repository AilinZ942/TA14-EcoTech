<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { api } from '@/api'
import * as echarts from 'echarts'

const healthData = ref([])
const loading = ref(true)
const error = ref('')

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
    error.value = err.message || 'Failed to load health data.'
  } finally {
    loading.value = false
  }
}

const yearOptions = computed(() => {
  const years = [
    ...new Set(healthData.value.map((item) => Number(item.year)).filter(Boolean)),
  ].sort((a, b) => a - b)
  return ['All', ...years]
})

const sexOptions = computed(() => {
  const values = [...new Set(healthData.value.map((item) => item.sex).filter(Boolean))].sort()
  return ['All', ...values]
})

const cancerTypeOptions = computed(() => {
  return ['All', ...allowedCancerTypes]
})

const trendData = computed(() => {
  return healthData.value.filter((item) => {
    const matchYear =
      selectedYear.value === 'All' || Number(item.year) === Number(selectedYear.value)
    const matchSex = selectedSex.value === 'All' || item.sex === selectedSex.value
    const matchCancer =
      selectedCancerType.value === 'All' || item.cancer_type === selectedCancerType.value

    return matchYear && matchSex && matchCancer
  })
})

const overviewData = computed(() => {
  return healthData.value.filter((item) => {
    const matchYear =
      selectedYear.value === 'All' || Number(item.year) === Number(selectedYear.value)
    const matchSex = selectedSex.value === 'All' || item.sex === selectedSex.value
    return matchYear && matchSex
  })
})

const totalRecords = computed(() => trendData.value.length)

const totalCases = computed(() => {
  return trendData.value.reduce((sum, item) => sum + Number(item.cancer_cases || 0), 0)
})

const totalDeaths = computed(() => {
  return trendData.value.reduce((sum, item) => sum + Number(item.cancer_deaths || 0), 0)
})

const averageFatalityRatio = computed(() => {
  if (!trendData.value.length) return 0

  const total = trendData.value.reduce((sum, item) => {
    const cases = Number(item.cancer_cases || 0)
    const deaths = Number(item.cancer_deaths || 0)
    const ratio = cases > 0 ? deaths / cases : 0
    return sum + ratio
  }, 0)

  return total / trendData.value.length
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
    const name = item.cancer_type
    if (!name) return

    if (!map.has(name)) {
      map.set(name, {
        cancer_type: name,
        cases: 0,
        deaths: 0,
      })
    }

    const entry = map.get(name)
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

function initCharts() {
  if (trendChartRef.value) trendChart = echarts.init(trendChartRef.value)
  if (casesChartRef.value) casesChart = echarts.init(casesChartRef.value)
  if (deathsChartRef.value) deathsChart = echarts.init(deathsChartRef.value)
  if (fatalityChartRef.value) fatalityChart = echarts.init(fatalityChartRef.value)
}

function updateCharts() {
  const yearData = aggregateByYear(trendData.value)
  const cancerData = aggregateByCancerType(overviewData.value)

  const topCases = [...cancerData]
    .sort((a, b) => b.cases - a.cases)
    .slice(0, 10)
    .reverse()

  const topDeaths = [...cancerData]
    .sort((a, b) => b.deaths - a.deaths)
    .slice(0, 10)
    .reverse()

  const topFatality = [...cancerData]
    .sort((a, b) => b.avgRatio - a.avgRatio)
    .slice(0, 10)
    .reverse()

  trendChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      top: 8,
      textStyle: { color: '#1b4332' },
    },
    grid: {
      left: 50,
      right: 30,
      top: 60,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      data: yearData.map((item) => item.year),
      axisLine: { lineStyle: { color: '#95b99f' } },
      axisLabel: { color: '#1b4332' },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#e3efe5' } },
      axisLabel: { color: '#1b4332' },
    },
    series: [
      {
        name: 'Cancer Cases',
        type: 'line',
        smooth: true,
        data: yearData.map((item) => item.cases),
        lineStyle: { width: 3, color: '#43a047' },
        itemStyle: { color: '#43a047' },
        areaStyle: { color: 'rgba(67,160,71,0.12)' },
      },
      {
        name: 'Cancer Deaths',
        type: 'line',
        smooth: true,
        data: yearData.map((item) => item.deaths),
        lineStyle: { width: 3, color: '#1b5e20' },
        itemStyle: { color: '#1b5e20' },
        areaStyle: { color: 'rgba(27,94,32,0.08)' },
      },
    ],
  })

  casesChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: {
      left: 210,
      right: 30,
      top: 30,
      bottom: 30,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e3efe5' } },
      axisLabel: { color: '#1b4332' },
    },
    yAxis: {
      type: 'category',
      data: topCases.map((item) => item.cancer_type),
      axisLabel: { color: '#1b4332' },
      axisLine: { lineStyle: { color: '#95b99f' } },
    },
    series: [
      {
        name: 'Cases',
        type: 'bar',
        data: topCases.map((item) => item.cases),
        itemStyle: {
          color: '#66bb6a',
          borderRadius: [0, 8, 8, 0],
        },
      },
    ],
  })

  deathsChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: {
      left: 210,
      right: 30,
      top: 30,
      bottom: 30,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e3efe5' } },
      axisLabel: { color: '#1b4332' },
    },
    yAxis: {
      type: 'category',
      data: topDeaths.map((item) => item.cancer_type),
      axisLabel: { color: '#1b4332' },
      axisLine: { lineStyle: { color: '#95b99f' } },
    },
    series: [
      {
        name: 'Deaths',
        type: 'bar',
        data: topDeaths.map((item) => item.deaths),
        itemStyle: {
          color: '#2e7d32',
          borderRadius: [0, 8, 8, 0],
        },
      },
    ],
  })

  fatalityChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: {
      left: 210,
      right: 30,
      top: 30,
      bottom: 30,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#e3efe5' } },
      axisLabel: {
        color: '#1b4332',
        formatter: (value) => Number(value).toFixed(2),
      },
    },
    yAxis: {
      type: 'category',
      data: topFatality.map((item) => item.cancer_type),
      axisLabel: { color: '#1b4332' },
      axisLine: { lineStyle: { color: '#95b99f' } },
    },
    series: [
      {
        name: 'Fatality Ratio',
        type: 'bar',
        data: topFatality.map((item) => Number(item.avgRatio.toFixed(4))),
        itemStyle: {
          color: '#1b4332',
          borderRadius: [0, 8, 8, 0],
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

onMounted(async () => {
  await loadHealthData()
  await nextTick()
  initCharts()
  updateCharts()
  window.addEventListener('resize', resizeCharts)
})

watch([trendData, overviewData], async () => {
  await nextTick()
  updateCharts()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)

  trendChart?.dispose()
  casesChart?.dispose()
  deathsChart?.dispose()
  fatalityChart?.dispose()
})
</script>

<template>
  <div class="dashboard-page">
    <div class="hero-section">
      <div>
        <p class="dashboard-tag">Health Risk Context</p>
        <h1>Exposure-Related Cancer Trends Dashboard</h1>
      </div>
    </div>

    <div class="intro-card">
      <div class="intro-top">
        <div class="intro-text">
          <p class="intro-tag">Why this matters</p>
          <h2>Understanding the Health Context of E-waste</h2>
          <p>
            E-waste contains hazardous materials such as lead, cadmium, mercury, and chromium.
            According to the World Health Organization (WHO), exposure to toxic substances in
            e-waste is associated with increased risk of serious health conditions, including
            certain cancers. This dashboard uses Australian cancer and mortality data as a
            contextual public health view to highlight why safe disposal and recycling matter.
          </p>
        </div>
      </div>

      <div class="source-box">
        <strong>Data Sources:</strong>
        Australian Institute of Health and Welfare (AIHW) cancer and mortality statistics. Health
        risk context supported by the World Health Organization (WHO) and International Agency for
        Research on Cancer (IARC).
      </div>

      <div class="intro-points horizontal">
        <div class="point-box">
          <span class="point-icon">⚠️</span>
          <div>
            <strong>Toxic Exposure</strong>
            <p>E-waste can release heavy metals and hazardous chemicals into the environment.</p>
          </div>
        </div>

        <div class="point-box">
          <span class="point-icon">🧪</span>
          <div>
            <strong>Health Context</strong>
            <p>
              This page focuses on selected cancers associated with long-term toxic exposure risks.
            </p>
          </div>
        </div>

        <div class="point-box">
          <span class="point-icon">📊</span>
          <div>
            <strong>Data Insight</strong>
            <p>Health data helps explain why responsible e-waste disposal is important.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="filter-sticky-wrap">
      <div class="filter-bar">
        <div class="filter-item">
          <label for="year">Year</label>
          <select id="year" v-model="selectedYear">
            <option v-for="year in yearOptions" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label for="sex">Sex</label>
          <select id="sex" v-model="selectedSex">
            <option v-for="sex in sexOptions" :key="sex" :value="sex">
              {{ sex }}
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label for="cancerType">Exposure-related Cancer Type</label>
          <select id="cancerType" v-model="selectedCancerType">
            <option v-for="type in cancerTypeOptions" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <div class="filter-section-title">
      Explore selected exposure-related cancers by year, sex, and cancer type.
    </div>

    <p v-if="loading" class="state-text">Loading dashboard data...</p>
    <p v-else-if="error" class="error-text">{{ error }}</p>

    <template v-else>
      <div class="summary-grid">
        <div class="summary-card">
          <span class="card-label">Total Records</span>
          <span class="card-value">{{ totalRecords }}</span>
        </div>

        <div class="summary-card">
          <span class="card-label">Total Cases</span>
          <span class="card-value">{{ totalCases.toLocaleString() }}</span>
        </div>

        <div class="summary-card">
          <span class="card-label">Total Deaths</span>
          <span class="card-value">{{ totalDeaths.toLocaleString() }}</span>
        </div>

        <div class="summary-card">
          <span class="card-label">Avg Fatality Ratio</span>
          <span class="card-value">{{ averageFatalityRatio.toFixed(4) }}</span>
        </div>
      </div>

      <div class="chart-card large-chart">
        <div class="chart-header">
          <h2>Cases and Deaths Over Time</h2>
          <p>
            This trend chart follows all filters, including the selected exposure-related cancer
            type, so you can inspect a specific pattern in more detail.
          </p>
        </div>
        <div ref="trendChartRef" class="chart"></div>
      </div>

      <div class="analysis-section-title">
        Selected Exposure-Related Cancers: Cases, Deaths, and Fatality Rates
      </div>

      <div class="overview-note">
        These charts compare the selected exposure-related cancers across three indicators. They are
        based on the selected year and sex, but are not affected by the cancer type filter.
      </div>

      <div class="chart-grid">
        <div class="chart-card">
          <div class="chart-header">
            <h2>Selected Cancers by Cases</h2>
            <p>Most common selected exposure-related cancers in the chosen view</p>
          </div>
          <div ref="casesChartRef" class="chart small-chart"></div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <h2>Selected Cancers by Deaths</h2>
            <p>Selected cancers with the highest death burden in the chosen view</p>
          </div>
          <div ref="deathsChartRef" class="chart small-chart"></div>
        </div>
      </div>

      <div class="chart-grid single-chart-row">
        <div class="chart-card">
          <div class="chart-header">
            <h2>Selected Cancers by Fatality Ratio</h2>
            <p>Average fatality ratio across selected exposure-related cancers</p>
          </div>
          <div ref="fatalityChartRef" class="chart small-chart"></div>
        </div>
      </div>

      <div class="analysis-description">
        <p>
          This dashboard does not claim that the displayed cancer cases are directly caused by
          e-waste. Instead, it uses official national health data to provide public health context
          around diseases associated with long-term toxic exposure risks, reinforcing the importance
          of safe e-waste handling and disposal.
        </p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  padding: 32px;
  background: linear-gradient(180deg, #f8fbf8 0%, #eef4ef 100%);
  color: #1f3b2d;
}

.hero-section {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #f4fbf4 0%, #edf7ee 100%);
  border: 1px solid #dcebdc;
  border-radius: 28px;
  padding: 36px 40px;
  margin-bottom: 28px;
  box-shadow: 0 10px 30px rgba(27, 67, 50, 0.06);
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -40px;
  right: -60px;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(129, 199, 132, 0.28) 0%, rgba(129, 199, 132, 0) 70%);
  pointer-events: none;
}

.hero-section::after {
  content: '';
  position: absolute;
  bottom: -60px;
  right: 180px;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(165, 214, 167, 0.18) 0%, rgba(165, 214, 167, 0) 72%);
  pointer-events: none;
}

.dashboard-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  color: #2e7d32;
  background: #e8f5e9;
  border: 1px solid #cfe8d1;
  border-radius: 999px;
  letter-spacing: 0.3px;
}

.hero-section h1 {
  position: relative;
  z-index: 1;
  margin: 0;
  font-size: 48px;
  line-height: 1.12;
  font-weight: 800;
  color: #163828;
  letter-spacing: -0.8px;
  max-width: 900px;
}

.intro-card {
  display: block;
  margin-bottom: 24px;
  padding: 24px 28px;
  background: #ffffff;
  border: 1px solid #e3efe5;
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(27, 67, 50, 0.05);
}

.intro-top {
  margin-bottom: 18px;
}

.intro-tag {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 700;
  color: #5c7465;
  letter-spacing: 0.2px;
}

.intro-text h2 {
  margin: 0 0 12px;
  font-size: 32px;
  color: #173a29;
  line-height: 1.2;
}

.intro-text p {
  margin: 0;
  font-size: 16px;
  line-height: 1.75;
  color: #557260;
}

.source-box {
  margin-top: 18px;
  margin-bottom: 10px;
  padding: 14px 16px;
  background: #f7fbf7;
  border: 1px solid #dcebdc;
  border-radius: 16px;
  color: #456654;
  font-size: 14px;
  line-height: 1.6;
}

.source-box strong {
  color: #173a29;
}

.intro-points {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.point-box {
  display: flex;
  gap: 12px;
  padding: 16px 18px;
  background: #f1f7f2;
  border: 1px solid #e3efe5;
  border-radius: 18px;
  align-items: flex-start;
}

.point-icon {
  font-size: 20px;
  line-height: 1;
  margin-top: 2px;
  opacity: 0.9;
}

.point-box strong {
  display: block;
  color: #173a29;
  margin-bottom: 4px;
  font-size: 15px;
  font-weight: 700;
}

.point-box p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #4f6f59;
}

.filter-section-title,
.analysis-section-title {
  margin-bottom: 16px;
  padding-bottom: 10px;
  padding-left: 12px;
  font-size: 22px;
  font-weight: 700;
  color: #1b4332;
  letter-spacing: -0.2px;
  border-bottom: 1px solid #e2eee3;
  border-left: 4px solid #43a047;
}

.analysis-section-title {
  margin-top: 12px;
}

.filter-item {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid #deebdf;
  border-radius: 20px;
  padding: 16px 18px;
  box-shadow: 0 8px 20px rgba(27, 67, 50, 0.05);
}

.filter-item label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #3f8f46;
  margin-bottom: 10px;
}

.filter-item select {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  color: #173a29;
  font-size: 16px;
  font-weight: 500;
}

.filter-sticky-wrap {
  position: sticky;
  top: 16px;
  z-index: 30;
  margin-bottom: 20px;
}

.filter-bar {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 18px;
  padding: 12px;
  background: rgba(248, 251, 248, 0.92);
  backdrop-filter: blur(10px);
  border: 1px solid #dcebdc;
  border-radius: 22px;
  box-shadow: 0 8px 20px rgba(27, 67, 50, 0.06);
}

.overview-note {
  background: #f7fbf7;
  border: 1px solid #dcebdc;
  border-radius: 20px;
  padding: 18px 22px;
  margin-bottom: 20px;
  color: #456654;
  line-height: 1.6;
}

.analysis-description {
  margin-top: -4px;
  margin-bottom: 28px;
  padding: 18px 22px;
  background: #f7fbf7;
  border: 1px solid #dcebdc;
  border-radius: 20px;
  color: #557260;
}

.analysis-description p {
  margin: 0;
  font-size: 15px;
  line-height: 1.75;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}

.summary-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdfb 100%);
  border: 1px solid #e2eee3;
  border-radius: 22px;
  padding: 22px;
  box-shadow: 0 8px 24px rgba(27, 67, 50, 0.05);
}

.card-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #6b8a74;
  margin-bottom: 12px;
}

.card-value {
  display: block;
  font-size: 32px;
  font-weight: 800;
  color: #173a29;
  letter-spacing: -0.4px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

.single-chart-row {
  grid-template-columns: 1fr;
}

.chart-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdfb 100%);
  border: 1px solid #e2eee3;
  border-radius: 24px;
  padding: 22px;
  box-shadow: 0 8px 24px rgba(27, 67, 50, 0.05);
}

.chart-header h2 {
  margin: 0;
  font-size: 21px;
  font-weight: 700;
  color: #173a29;
  letter-spacing: -0.2px;
}

.chart-header p {
  margin: 8px 0 0;
  color: #6b8a74;
  font-size: 14px;
  line-height: 1.6;
}

.chart {
  width: 100%;
  height: 420px;
  margin-top: 18px;
}

.large-chart {
  margin-bottom: 24px;
}

.large-chart .chart {
  height: 430px;
}

.small-chart {
  height: 420px;
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
  font-weight: 500;
}

@media (max-width: 1200px) {
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1024px) {
  .filter-bar {
    grid-template-columns: 1fr;
  }

  .intro-points {
    grid-template-columns: 1fr;
  }

  .hero-section {
    padding: 28px 24px;
  }

  .hero-section h1 {
    font-size: 34px;
  }

  .intro-text h2 {
    font-size: 28px;
  }

  .filter-section-title,
  .analysis-section-title {
    font-size: 20px;
  }

  .dashboard-page {
    padding: 20px;
  }
}

@media (max-width: 640px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>