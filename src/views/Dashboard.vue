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

async function loadHealthData() {
  try {
    loading.value = true
    error.value = ''

    const res = await api.getHealthAll()
    healthData.value = Array.isArray(res.items) ? res.items : []
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to load health data.'
  } finally {
    loading.value = false
  }
}

const yearOptions = computed(() => {
  const years = [...new Set(healthData.value.map((item) => item.year))].sort((a, b) => a - b)
  return ['All', ...years]
})

const sexOptions = computed(() => {
  const values = [...new Set(healthData.value.map((item) => item.sex))].sort()
  return ['All', ...values]
})

const cancerTypeOptions = computed(() => {
  const values = [...new Set(healthData.value.map((item) => item.cancer_type))].sort()
  return ['All', ...values]
})

const filteredData = computed(() => {
  return healthData.value.filter((item) => {
    const matchYear = selectedYear.value === 'All' || item.year === selectedYear.value
    const matchSex = selectedSex.value === 'All' || item.sex === selectedSex.value
    const matchCancer =
      selectedCancerType.value === 'All' || item.cancer_type === selectedCancerType.value

    return matchYear && matchSex && matchCancer
  })
})

const totalRecords = computed(() => filteredData.value.length)

const totalCases = computed(() => {
  return filteredData.value.reduce((sum, item) => sum + Number(item.cancer_cases || 0), 0)
})

const totalDeaths = computed(() => {
  return filteredData.value.reduce((sum, item) => sum + Number(item.cancer_deaths || 0), 0)
})

const averageFatalityRatio = computed(() => {
  if (!filteredData.value.length) return 0
  const total = filteredData.value.reduce((sum, item) => sum + Number(item.fatality_ratio || 0), 0)
  return total / filteredData.value.length
})

function aggregateByYear(data) {
  const map = new Map()

  data.forEach((item) => {
    const year = Number(item.year)
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
    if (!map.has(name)) {
      map.set(name, {
        cancer_type: name,
        cases: 0,
        deaths: 0,
        ratioTotal: 0,
        count: 0,
      })
    }

    const entry = map.get(name)
    entry.cases += Number(item.cancer_cases || 0)
    entry.deaths += Number(item.cancer_deaths || 0)
    entry.ratioTotal += Number(item.fatality_ratio || 0)
    entry.count += 1
  })

  return [...map.values()].map((item) => ({
    cancer_type: item.cancer_type,
    cases: item.cases,
    deaths: item.deaths,
    avgRatio: item.count ? item.ratioTotal / item.count : 0,
  }))
}

function initCharts() {
  if (trendChartRef.value) trendChart = echarts.init(trendChartRef.value)
  if (casesChartRef.value) casesChart = echarts.init(casesChartRef.value)
  if (deathsChartRef.value) deathsChart = echarts.init(deathsChartRef.value)
  if (fatalityChartRef.value) fatalityChart = echarts.init(fatalityChartRef.value)
}

function updateCharts() {
  const yearData = aggregateByYear(filteredData.value)
  const cancerData = aggregateByCancerType(filteredData.value)

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

  if (trendChart) {
    trendChart.setOption({
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
  }

  if (casesChart) {
    casesChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: {
        left: 180,
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
            borderRadius: [0, 6, 6, 0],
          },
        },
      ],
    })
  }

  if (deathsChart) {
    deathsChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: {
        left: 180,
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
            borderRadius: [0, 6, 6, 0],
          },
        },
      ],
    })
  }

  if (fatalityChart) {
    fatalityChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: {
        left: 180,
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
            borderRadius: [0, 6, 6, 0],
          },
        },
      ],
    })
  }
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

watch(filteredData, async () => {
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
        <p class="dashboard-tag">Health Analytics</p>
        <h1>Cancer Trends & Fatality Dashboard</h1>
        <p class="dashboard-subtitle">
          Explore cancer cases, deaths, and fatality patterns by year, sex, and cancer type.
        </p>
      </div>
    </div>

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
        <label for="cancerType">Cancer Type</label>
        <select id="cancerType" v-model="selectedCancerType">
          <option v-for="type in cancerTypeOptions" :key="type" :value="type">
            {{ type }}
          </option>
        </select>
      </div>
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
          <p>Trend of cancer cases and deaths across years</p>
        </div>
        <div ref="trendChartRef" class="chart"></div>
      </div>

      <div class="chart-grid">
        <div class="chart-card">
          <div class="chart-header">
            <h2>Top 10 Cancer Types by Cases</h2>
            <p>Most common cancer types in the filtered dataset</p>
          </div>
          <div ref="casesChartRef" class="chart small-chart"></div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <h2>Top 10 Cancer Types by Deaths</h2>
            <p>Most severe cancer burden by deaths</p>
          </div>
          <div ref="deathsChartRef" class="chart small-chart"></div>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-header">
          <h2>Top 10 Cancer Types by Fatality Ratio</h2>
          <p>Average fatality ratio by cancer type</p>
        </div>
        <div ref="fatalityChartRef" class="chart small-chart"></div>
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
  margin: 0 0 14px;
  font-size: 48px;
  line-height: 1.12;
  font-weight: 800;
  color: #163828;
  letter-spacing: -0.8px;
  max-width: 900px;
}

.dashboard-subtitle {
  position: relative;
  z-index: 1;
  margin: 0;
  font-size: 18px;
  max-width: 760px;
  line-height: 1.65;
  color: #4f6f59;
}

.filter-bar {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}

.filter-item {
  background: rgba(255, 255, 255, 0.88);
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

.chart-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdfb 100%);
  border: 1px solid #e2eee3;
  border-radius: 24px;
  padding: 22px;
  box-shadow: 0 8px 24px rgba(27, 67, 50, 0.05);
  margin-bottom: 28px;
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

@media (max-width: 1024px) {
  .summary-grid,
  .chart-grid,
  .filter-bar {
    grid-template-columns: 1fr;
  }

  .hero-section {
    padding: 28px 24px;
  }

  .hero-section h1 {
    font-size: 34px;
  }

  .dashboard-subtitle {
    font-size: 16px;
  }

  .dashboard-page {
    padding: 20px;
  }
}
</style>
