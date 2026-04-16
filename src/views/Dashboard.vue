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

const heroRef = ref(null)
const infoStripRef = ref(null)
const filtersRef = ref(null)
const summaryRef = ref(null)
const trendSectionRef = ref(null)
const compareSectionRef = ref(null)
const takeawayRef = ref(null)

let trendChart = null
let casesChart = null
let deathsChart = null
let fatalityChart = null
let observer = null

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
  const years = [...new Set(healthData.value.map((item) => Number(item.year)).filter(Boolean))].sort(
    (a, b) => a - b,
  )
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

const selectedFiltersSummary = computed(() => {
  const yearText = selectedYear.value === 'All' ? 'All years' : `Year ${selectedYear.value}`
  const sexText = selectedSex.value === 'All' ? 'All sexes' : selectedSex.value
  const cancerText =
    selectedCancerType.value === 'All' ? 'All selected conditions' : selectedCancerType.value

  return `${yearText} • ${sexText} • ${cancerText}`
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

function formatCompactNumber(value) {
  return Number(value || 0).toLocaleString()
}

function tooltipStyle() {
  return {
    backgroundColor: 'rgba(7, 20, 14, 0.97)',
    borderColor: 'rgba(129, 199, 132, 0.30)',
    borderWidth: 1,
    textStyle: {
      color: '#f4fff5',
      fontSize: 13,
    },
    padding: [12, 14],
    extraCssText: `
      border-radius: 18px;
      box-shadow: 0 22px 52px rgba(0, 0, 0, 0.36);
      backdrop-filter: blur(14px);
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
    animationDuration: 1200,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      ...tooltipStyle(),
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: 'rgba(129, 199, 132, 0.74)',
          width: 2,
          shadowBlur: 14,
          shadowColor: 'rgba(129, 199, 132, 0.38)',
        },
      },
      formatter(params) {
        if (!params?.length) return ''
        const year = params[0].axisValue
        const lines = params
          .map(
            (item) => `
              <div style="margin-top:7px; display:flex; align-items:center; gap:8px;">
                <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${item.color}; box-shadow:0 0 12px ${item.color};"></span>
                <span>${item.seriesName}: <strong>${formatCompactNumber(item.data)}</strong></span>
              </div>
            `,
          )
          .join('')
        return `
          <div style="font-weight:700; font-size:14px; margin-bottom:4px;">${year}</div>
          ${lines}
        `
      },
    },
    legend: {
      top: 10,
      textStyle: { color: '#1b4332', fontWeight: 600 },
      itemWidth: 14,
      itemHeight: 14,
    },
    grid: {
      left: 50,
      right: 30,
      top: 72,
      bottom: 40,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: yearData.map((item) => item.year),
      axisLine: { lineStyle: { color: '#a8cdb0' } },
      axisTick: { show: false },
      axisLabel: { color: '#274833', fontWeight: 600 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(201, 224, 205, 0.74)' } },
      axisLabel: { color: '#274833' },
    },
    series: [
      {
        name: 'Cases',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 9,
        showSymbol: false,
        emphasis: {
          focus: 'series',
          scale: true,
          itemStyle: {
            borderWidth: 3,
            borderColor: '#ffffff',
            shadowBlur: 20,
            shadowColor: 'rgba(67,160,71,0.62)',
          },
        },
        data: yearData.map((item) => item.cases),
        lineStyle: {
          width: 4,
          color: '#43a047',
          shadowBlur: 16,
          shadowColor: 'rgba(67,160,71,0.30)',
        },
        itemStyle: { color: '#43a047' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(67,160,71,0.34)' },
            { offset: 1, color: 'rgba(67,160,71,0.03)' },
          ]),
        },
      },
      {
        name: 'Deaths',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 9,
        showSymbol: false,
        emphasis: {
          focus: 'series',
          scale: true,
          itemStyle: {
            borderWidth: 3,
            borderColor: '#ffffff',
            shadowBlur: 20,
            shadowColor: 'rgba(27,94,32,0.58)',
          },
        },
        data: yearData.map((item) => item.deaths),
        lineStyle: {
          width: 4,
          color: '#1b5e20',
          shadowBlur: 16,
          shadowColor: 'rgba(27,94,32,0.30)',
        },
        itemStyle: { color: '#1b5e20' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(27,94,32,0.22)' },
            { offset: 1, color: 'rgba(27,94,32,0.02)' },
          ]),
        },
      },
    ],
  })

  casesChart?.setOption({
    backgroundColor: 'transparent',
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...tooltipStyle(),
      formatter(params) {
        if (!params?.length) return ''
        const item = params[0]
        return `
          <div style="font-weight:700; margin-bottom:6px;">${item.name}</div>
          <div>Cases: <strong>${formatCompactNumber(item.value)}</strong></div>
        `
      },
    },
    grid: {
      left: 240,
      right: 30,
      top: 24,
      bottom: 30,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(201, 224, 205, 0.74)' } },
      axisLabel: { color: '#274833' },
    },
    yAxis: {
      type: 'category',
      data: topCases.map((item) => item.cancer_type),
      axisLabel: { color: '#1b4332', fontWeight: 600 },
      axisLine: { lineStyle: { color: '#a8cdb0' } },
      axisTick: { show: false },
    },
    series: [
      {
        name: 'Cases',
        type: 'bar',
        data: topCases.map((item) => item.cases),
        barWidth: 18,
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(67,160,71,0.08)',
          borderRadius: [0, 10, 10, 0],
        },
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#8be292' },
            { offset: 1, color: '#43a047' },
          ]),
          shadowBlur: 14,
          shadowColor: 'rgba(67,160,71,0.26)',
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowColor: 'rgba(67,160,71,0.40)',
          },
        },
      },
    ],
  })

  deathsChart?.setOption({
    backgroundColor: 'transparent',
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...tooltipStyle(),
      formatter(params) {
        if (!params?.length) return ''
        const item = params[0]
        return `
          <div style="font-weight:700; margin-bottom:6px;">${item.name}</div>
          <div>Deaths: <strong>${formatCompactNumber(item.value)}</strong></div>
        `
      },
    },
    grid: {
      left: 240,
      right: 30,
      top: 24,
      bottom: 30,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(201, 224, 205, 0.74)' } },
      axisLabel: { color: '#274833' },
    },
    yAxis: {
      type: 'category',
      data: topDeaths.map((item) => item.cancer_type),
      axisLabel: { color: '#1b4332', fontWeight: 600 },
      axisLine: { lineStyle: { color: '#a8cdb0' } },
      axisTick: { show: false },
    },
    series: [
      {
        name: 'Deaths',
        type: 'bar',
        data: topDeaths.map((item) => item.deaths),
        barWidth: 18,
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(27,94,32,0.08)',
          borderRadius: [0, 10, 10, 0],
        },
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#5ab36a' },
            { offset: 1, color: '#1b5e20' },
          ]),
          shadowBlur: 14,
          shadowColor: 'rgba(27,94,32,0.26)',
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowColor: 'rgba(27,94,32,0.40)',
          },
        },
      },
    ],
  })

  fatalityChart?.setOption({
    backgroundColor: 'transparent',
    animationDuration: 1000,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...tooltipStyle(),
      formatter(params) {
        if (!params?.length) return ''
        const item = params[0]
        return `
          <div style="font-weight:700; margin-bottom:6px;">${item.name}</div>
          <div>Severity ratio: <strong>${Number(item.value).toFixed(4)}</strong></div>
        `
      },
    },
    grid: {
      left: 240,
      right: 30,
      top: 24,
      bottom: 30,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(201, 224, 205, 0.74)' } },
      axisLabel: {
        color: '#274833',
        formatter: (value) => Number(value).toFixed(2),
      },
    },
    yAxis: {
      type: 'category',
      data: topFatality.map((item) => item.cancer_type),
      axisLabel: { color: '#1b4332', fontWeight: 600 },
      axisLine: { lineStyle: { color: '#a8cdb0' } },
      axisTick: { show: false },
    },
    series: [
      {
        name: 'Severity Ratio',
        type: 'bar',
        data: topFatality.map((item) => Number(item.avgRatio.toFixed(4))),
        barWidth: 18,
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(27,67,50,0.08)',
          borderRadius: [0, 10, 10, 0],
        },
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#5b9875' },
            { offset: 1, color: '#1b4332' },
          ]),
          shadowBlur: 14,
          shadowColor: 'rgba(27,67,50,0.26)',
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowColor: 'rgba(27,67,50,0.40)',
          },
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

function setupRevealAnimations() {
  const sections = [
    heroRef.value,
    infoStripRef.value,
    filtersRef.value,
    summaryRef.value,
    trendSectionRef.value,
    compareSectionRef.value,
    takeawayRef.value,
  ].filter(Boolean)

  sections.forEach((section, index) => {
    section.classList.add('reveal-section')
    section.style.setProperty('--reveal-delay', `${index * 0.08}s`)
  })

  if (summaryRef.value) {
    const cards = summaryRef.value.querySelectorAll('.summary-card')
    cards.forEach((card, index) => {
      card.classList.add('reveal-child')
      card.style.setProperty('--child-delay', `${0.12 + index * 0.08}s`)
    })
  }

  if (compareSectionRef.value) {
    const compareCards = compareSectionRef.value.querySelectorAll('.chart-card')
    compareCards.forEach((card, index) => {
      card.classList.add('reveal-child')
      card.style.setProperty('--child-delay', `${0.15 + index * 0.10}s`)
    })
  }

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          observer?.unobserve(entry.target)
        }
      })
    },
    {
      threshold: 0.12,
      rootMargin: '0px 0px -20px 0px',
    },
  )

  sections.forEach((section) => observer.observe(section))
}

onMounted(async () => {
  await loadHealthData()
  await nextTick()
  initCharts()
  updateCharts()
  setupRevealAnimations()
  window.addEventListener('resize', resizeCharts)
})

watch([trendData, overviewData], async () => {
  await nextTick()
  updateCharts()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  observer?.disconnect()
  trendChart?.dispose()
  casesChart?.dispose()
  deathsChart?.dispose()
  fatalityChart?.dispose()
})
</script>

<template>
  <div class="dashboard-page">
    <section ref="heroRef" class="hero-section">
      <div class="hero-orb hero-orb-one"></div>
      <div class="hero-orb hero-orb-two"></div>
      <div class="hero-grid-lines"></div>

      <div class="hero-content">
        <div class="hero-copy">
          <p class="dashboard-tag">Health Risk Context</p>
          <h1>Understand Why Safe E-waste Disposal Matters</h1>
          <p class="hero-subtext">
            This dashboard turns health data into simple insights. You do not need technical
            knowledge. Scroll, hover, and explore the trends to understand why harmful waste should
            be handled safely.
          </p>

          <div class="hero-chip-row">
            <span class="hero-chip">Interactive insights</span>
            <span class="hero-chip">Simple health view</span>
            <span class="hero-chip">Trusted public data</span>
          </div>
        </div>

        <div class="hero-side-card">
          <span class="side-card-label">Current view</span>
          <strong>{{ selectedFiltersSummary }}</strong>
          <p>
            Use the filters below to explore changes by year, sex, or a selected health condition.
          </p>
        </div>
      </div>
    </section>

    <section ref="infoStripRef" class="info-strip">
      <div class="info-strip-item glass-card">
        <span class="info-strip-icon">ℹ️</span>
        <div>
          <strong>What this page shows</strong>
          <p>A simple view of selected cancers associated with long-term toxic exposure risks.</p>
        </div>
      </div>

      <div class="info-strip-item glass-card">
        <span class="info-strip-icon">🖱️</span>
        <div>
          <strong>How to use it</strong>
          <p>Hover over any chart to see clear values in a floating pop-up card.</p>
        </div>
      </div>

      <div class="info-strip-item glass-card">
        <span class="info-strip-icon">📚</span>
        <div>
          <strong>Data source</strong>
          <p>AIHW health data, with health-risk context supported by WHO and IARC.</p>
        </div>
      </div>
    </section>

    <section ref="filtersRef" class="filter-sticky-wrap">
      <div class="filter-bar">
        <div class="filter-item glass-card">
          <label for="year">Year</label>
          <select id="year" v-model="selectedYear">
            <option v-for="year in yearOptions" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>

        <div class="filter-item glass-card">
          <label for="sex">Sex</label>
          <select id="sex" v-model="selectedSex">
            <option v-for="sex in sexOptions" :key="sex" :value="sex">
              {{ sex }}
            </option>
          </select>
        </div>

        <div class="filter-item glass-card">
          <label for="cancerType">Health condition</label>
          <select id="cancerType" v-model="selectedCancerType">
            <option v-for="type in cancerTypeOptions" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>
      </div>
    </section>

    <p v-if="loading" class="state-text">Loading dashboard data...</p>
    <p v-else-if="error" class="error-text">{{ error }}</p>

    <template v-else>
      <section ref="summaryRef">
        <div class="section-heading">
          <h2>Quick Health Insights</h2>
          <p>These cards update automatically based on your selected filters.</p>
        </div>

        <div class="summary-grid">
          <div class="summary-card glass-card">
            <div class="summary-icon">🧾</div>
            <span class="card-label">Records</span>
            <span class="card-value">{{ totalRecords }}</span>
            <span class="card-footnote">Data rows in the current view</span>
          </div>

          <div class="summary-card glass-card">
            <div class="summary-icon">🧬</div>
            <span class="card-label">Cases</span>
            <span class="card-value">{{ totalCases.toLocaleString() }}</span>
            <span class="card-footnote">Total reported cases in this view</span>
          </div>

          <div class="summary-card glass-card">
            <div class="summary-icon">⚠️</div>
            <span class="card-label">Deaths</span>
            <span class="card-value">{{ totalDeaths.toLocaleString() }}</span>
            <span class="card-footnote">Total recorded deaths in this view</span>
          </div>

          <div class="summary-card glass-card">
            <div class="summary-icon">📈</div>
            <span class="card-label">Severity Ratio</span>
            <span class="card-value">{{ averageFatalityRatio.toFixed(4) }}</span>
            <span class="card-footnote">Deaths compared with total cases</span>
          </div>
        </div>
      </section>

      <section ref="trendSectionRef">
        <div class="section-heading">
          <h2>Main Trend View</h2>
          <p>Hover over the graph to see how reported cases and deaths change over time.</p>
        </div>

        <div class="chart-card glass-card interactive-chart-card">
          <div class="chart-header">
            <div>
              <span class="mini-tag">Interactive graph</span>
              <h3>Cases and Deaths Over Time</h3>
            </div>
            <p>
              This graph follows all selected filters and helps you compare changes year by year.
            </p>
          </div>
          <div ref="trendChartRef" class="chart trend-chart"></div>
        </div>

        <div class="insight-banner glass-card">
          <div>
            <strong>What does this graph mean?</strong>
            <p>
              If the lines rise, the selected condition appears more often or causes more deaths in
              that period. Hover over any point to see the exact numbers.
            </p>
          </div>
        </div>
      </section>

      <section ref="compareSectionRef">
        <div class="section-heading">
          <h2>Compare Conditions</h2>
          <p>
            These charts compare selected conditions by how common they are, how serious they are,
            and how much death impact they have.
          </p>
        </div>

        <div class="chart-grid">
          <div class="chart-card glass-card interactive-chart-card">
            <div class="chart-header">
              <div>
                <span class="mini-tag">Comparison</span>
                <h3>Most Common Conditions</h3>
              </div>
              <p>Shows which selected conditions appear most often in the chosen view.</p>
            </div>
            <div ref="casesChartRef" class="chart small-chart"></div>
          </div>

          <div class="chart-card glass-card interactive-chart-card">
            <div class="chart-header">
              <div>
                <span class="mini-tag">Comparison</span>
                <h3>Highest Death Impact</h3>
              </div>
              <p>Shows which selected conditions contribute most to recorded deaths.</p>
            </div>
            <div ref="deathsChartRef" class="chart small-chart"></div>
          </div>
        </div>

        <div class="chart-grid single-chart-row">
          <div class="chart-card glass-card interactive-chart-card">
            <div class="chart-header">
              <div>
                <span class="mini-tag">Comparison</span>
                <h3>Condition Severity Ratio</h3>
              </div>
              <p>
                Higher values mean deaths make up a larger share of total cases for that condition.
              </p>
            </div>
            <div ref="fatalityChartRef" class="chart small-chart"></div>
          </div>
        </div>
      </section>

      <section ref="takeawayRef" class="analysis-description glass-card">
        <h3>Simple takeaway</h3>
        <p>
          This dashboard makes complex health data easier to understand. It does not claim that
          these cases are directly caused by e-waste. Instead, it gives a public health view of
          conditions associated with long-term toxic exposure risks, helping users understand why
          safe disposal matters.
        </p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  padding: 34px;
  background:
    radial-gradient(circle at 86% 5%, rgba(129, 199, 132, 0.20), transparent 18%),
    radial-gradient(circle at 12% 92%, rgba(67, 160, 71, 0.12), transparent 21%),
    linear-gradient(180deg, #f8fbf8 0%, #eef4ef 100%);
  color: #1f3b2d;
  overflow: hidden;
}

.reveal-section {
  opacity: 0;
  transform: translateY(70px) scale(0.985);
  filter: blur(10px);
  transition:
    opacity 1s cubic-bezier(0.22, 1, 0.36, 1),
    transform 1.05s cubic-bezier(0.22, 1, 0.36, 1),
    filter 1.05s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: var(--reveal-delay, 0s);
  will-change: opacity, transform, filter;
}

.reveal-section.revealed {
  opacity: 1;
  transform: translateY(0) scale(1);
  filter: blur(0);
}

.reveal-child {
  opacity: 0;
  transform: translateY(32px);
  transition:
    opacity 0.85s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.85s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: var(--child-delay, 0s);
}

.revealed .reveal-child {
  opacity: 1;
  transform: translateY(0);
}

.hero-section {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(220, 235, 220, 0.95);
  border-radius: 36px;
  padding: 40px;
  margin-bottom: 28px;
  background:
    linear-gradient(135deg, rgba(244, 251, 244, 0.82) 0%, rgba(237, 247, 238, 0.78) 100%);
  box-shadow:
    0 22px 48px rgba(27, 67, 50, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.80);
  backdrop-filter: blur(15px);
}

.hero-orb {
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
  filter: blur(8px);
}

.hero-orb-one {
  top: -90px;
  right: -20px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(129, 199, 132, 0.26) 0%, rgba(129, 199, 132, 0) 72%);
  animation: floatOrbOne 12s ease-in-out infinite;
}

.hero-orb-two {
  bottom: -120px;
  left: 8%;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(67, 160, 71, 0.18) 0%, rgba(67, 160, 71, 0) 72%);
  animation: floatOrbTwo 14s ease-in-out infinite;
}

.hero-grid-lines {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.20), transparent 90%);
  pointer-events: none;
}

@keyframes floatOrbOne {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(-14px, 18px, 0); }
}

@keyframes floatOrbTwo {
  0%, 100% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(18px, -14px, 0); }
}

.hero-content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(280px, 0.78fr);
  gap: 26px;
  align-items: stretch;
}

.dashboard-tag,
.mini-tag,
.hero-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.dashboard-tag {
  margin: 0 0 14px;
  padding: 8px 14px;
  font-size: 13px;
  color: #2e7d32;
  background: rgba(232, 245, 233, 0.90);
  border: 1px solid rgba(207, 232, 209, 0.98);
}

.hero-copy h1 {
  margin: 0 0 14px;
  font-size: 58px;
  line-height: 1.0;
  font-weight: 800;
  color: #143324;
  letter-spacing: -1.35px;
  max-width: 940px;
}

.hero-subtext {
  margin: 0;
  max-width: 780px;
  font-size: 16px;
  line-height: 1.9;
  color: #557260;
}

.hero-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}

.hero-chip {
  padding: 8px 12px;
  font-size: 12px;
  color: #2d6544;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(207, 232, 209, 0.95);
  box-shadow: 0 8px 18px rgba(27, 67, 50, 0.04);
}

.hero-side-card {
  align-self: stretch;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 26px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0%, rgba(247, 251, 247, 0.80) 100%);
  border: 1px solid rgba(220, 235, 220, 0.95);
  box-shadow:
    0 20px 36px rgba(27, 67, 50, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.76);
  backdrop-filter: blur(14px);
}

.side-card-label {
  display: inline-block;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #5c7465;
}

.hero-side-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 20px;
  line-height: 1.45;
  color: #173a29;
}

.hero-side-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #557260;
}

.info-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 26px;
}

.glass-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0%, rgba(251, 253, 251, 0.80) 100%);
  border: 1px solid rgba(226, 238, 227, 0.98);
  box-shadow:
    0 16px 32px rgba(27, 67, 50, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(15px);
}

.info-strip-item {
  display: flex;
  gap: 12px;
  padding: 20px;
  border-radius: 22px;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease,
    border-color 0.3s ease;
}

.info-strip-item:hover {
  transform: translateY(-5px);
  border-color: rgba(129, 199, 132, 0.52);
  box-shadow:
    0 18px 34px rgba(27, 67, 50, 0.07),
    0 0 0 1px rgba(129, 199, 132, 0.12);
}

.info-strip-icon {
  font-size: 20px;
  line-height: 1;
  margin-top: 2px;
}

.info-strip-item strong {
  display: block;
  margin-bottom: 4px;
  color: #173a29;
  font-size: 15px;
}

.info-strip-item p {
  margin: 0;
  color: #557260;
  font-size: 13px;
  line-height: 1.65;
}

.filter-sticky-wrap {
  position: sticky;
  top: 14px;
  z-index: 40;
  margin-bottom: 28px;
}

.filter-bar {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 18px;
  padding: 12px;
  background: rgba(248, 251, 248, 0.72);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(220, 235, 220, 0.96);
  border-radius: 28px;
  box-shadow:
    0 16px 30px rgba(27, 67, 50, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.filter-item {
  border-radius: 22px;
  padding: 16px 18px;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease,
    border-color 0.3s ease;
}

.filter-item:hover {
  transform: translateY(-3px);
  border-color: rgba(129, 199, 132, 0.58);
  box-shadow:
    0 18px 30px rgba(27, 67, 50, 0.08),
    0 0 0 1px rgba(129, 199, 132, 0.14);
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
  font-weight: 600;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
  margin-bottom: 16px;
}

.section-heading h2 {
  margin: 0;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #173a29;
}

.section-heading p {
  margin: 0;
  color: #647f6d;
  font-size: 14px;
  line-height: 1.65;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 18px;
  margin-bottom: 34px;
}

.summary-card {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  padding: 24px;
  transition:
    transform 0.34s ease,
    box-shadow 0.34s ease,
    border-color 0.34s ease;
}

.summary-card::before {
  content: '';
  position: absolute;
  top: -34px;
  right: -22px;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(129, 199, 132, 0.18) 0%, transparent 72%);
  pointer-events: none;
}

.summary-card:hover {
  transform: translateY(-9px) scale(1.01);
  border-color: rgba(129, 199, 132, 0.58);
  box-shadow:
    0 22px 40px rgba(27, 67, 50, 0.09),
    0 0 0 1px rgba(129, 199, 132, 0.15);
}

.summary-icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  margin-bottom: 14px;
  border-radius: 16px;
  background: linear-gradient(180deg, #eff8f0 0%, #e7f4e8 100%);
  font-size: 21px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.88);
}

.card-label {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #6b8a74;
  margin-bottom: 8px;
}

.card-value {
  display: block;
  font-size: 34px;
  font-weight: 800;
  color: #173a29;
  letter-spacing: -0.5px;
  margin-bottom: 8px;
}

.card-footnote {
  display: block;
  font-size: 13px;
  line-height: 1.55;
  color: #5f7967;
}

.chart-card {
  border-radius: 30px;
  padding: 26px;
  margin-bottom: 28px;
  transition:
    transform 0.36s ease,
    box-shadow 0.36s ease,
    border-color 0.36s ease;
}

.interactive-chart-card:hover {
  transform: translateY(-9px) scale(1.003);
  border-color: rgba(129, 199, 132, 0.58);
  box-shadow:
    0 26px 44px rgba(27, 67, 50, 0.10),
    0 0 0 1px rgba(129, 199, 132, 0.14);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 18px;
}

.chart-header h3 {
  margin: 6px 0 0;
  font-size: 27px;
  font-weight: 800;
  color: #173a29;
  letter-spacing: -0.42px;
}

.chart-header p {
  max-width: 420px;
  margin: 0;
  color: #647f6d;
  font-size: 14px;
  line-height: 1.8;
}

.mini-tag {
  padding: 7px 12px;
  font-size: 12px;
  color: #2e7d32;
  background: rgba(236, 247, 237, 0.90);
  border: 1px solid rgba(212, 236, 214, 0.98);
}

.chart {
  width: 100%;
  height: 420px;
  margin-top: 18px;
}

.trend-chart {
  height: 510px;
}

.small-chart {
  height: 440px;
}

.insight-banner {
  display: flex;
  gap: 12px;
  margin-top: -2px;
  margin-bottom: 30px;
  padding: 20px 24px;
  border-radius: 24px;
}

.insight-banner strong {
  display: block;
  margin-bottom: 6px;
  color: #173a29;
  font-size: 16px;
}

.insight-banner p {
  margin: 0;
  color: #557260;
  line-height: 1.8;
  font-size: 14px;
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

.analysis-description {
  margin-bottom: 28px;
  padding: 26px 28px;
  border-radius: 30px;
}

.analysis-description h3 {
  margin: 0 0 10px;
  font-size: 24px;
  color: #173a29;
  letter-spacing: -0.25px;
}

.analysis-description p {
  margin: 0;
  font-size: 15px;
  line-height: 1.9;
  color: #557260;
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

@media (max-width: 1280px) {
  .hero-content {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }

  .info-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1024px) {
  .dashboard-page {
    padding: 22px;
  }

  .filter-bar {
    grid-template-columns: 1fr;
  }

  .section-heading {
    flex-direction: column;
    align-items: start;
  }

  .chart-header {
    flex-direction: column;
  }

  .hero-copy h1 {
    font-size: 40px;
  }

  .chart-header h3 {
    font-size: 22px;
  }

  .section-heading h2 {
    font-size: 24px;
  }

  .trend-chart {
    height: 440px;
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    padding: 16px;
  }

  .hero-section {
    padding: 24px 20px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .hero-copy h1 {
    font-size: 31px;
  }

  .hero-subtext {
    font-size: 15px;
  }

  .chart,
  .trend-chart,
  .small-chart {
    height: 360px;
  }

  .chart-header p {
    max-width: 100%;
  }
}
</style>