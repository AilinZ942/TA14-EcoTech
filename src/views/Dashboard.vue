<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { api } from '@/api'
import * as echarts from 'echarts'
import pearsonHeatmapUrl from '@/assets/health-analysis/emissions_health_pearson_heatmap.png'
import spearmanHeatmapUrl from '@/assets/health-analysis/emissions_health_spearman_heatmap.png'
import pearsonSummaryCsv from '@/data/health-analysis/emissions_health_pearson_summary.csv?raw'
import spearmanSummaryCsv from '@/data/health-analysis/emissions_health_spearman_summary.csv?raw'
import regressionCoefficientsCsv from '@/data/health-analysis/emissions_health_multiple_regression_coefficients.csv?raw'
import regressionModelsCsv from '@/data/health-analysis/emissions_health_multiple_regression_models.csv?raw'
import overallEnvironmentHeatmapUrl from '@/assets/environment-analysis/overall_state_aggregate_pearson_heatmap.png'
import overallEnvironmentSummaryCsv from '@/data/environment-analysis/overall_state_aggregate_pearson_summary.csv?raw'
import stateEnvironmentSummaryCsv from '@/data/environment-analysis/state_pearson_correlation_summary.csv?raw'
import stateEnvironmentTotalsCsv from '@/data/environment-analysis/state_total_ewaste_pollutants.csv?raw'
import wasteStateYearCsv from '@/data/environment-analysis/waste_state_year_agg.csv?raw'

const stateEnvironmentHeatmaps = import.meta.glob('@/assets/environment-analysis/state-heatmaps/*.png', {
  eager: true,
  import: 'default',
})

const loading = ref(true)
const error = ref('')
const dashboardNotice = ref('')

const healthData = ref([])
const statePollutionData = ref([])
const facilityPollutionData = ref([])

const selectedYear = ref('All')
const selectedMetal = ref('All')
const selectedState = ref('All')
const selectedSex = ref('All')
const selectedCancerType = ref('All')
const selectedEvidenceView = ref('environment')
const selectedHealthMetric = ref('age_standardised_rate_per_100000')
const selectedCorrelationMethod = ref('pearson')
const selectedEnvironmentState = ref('Overall')

const pollutionStateChartRef = ref(null)
const topFacilityChartRef = ref(null)
const metalTotalsChartRef = ref(null)
const healthTrendChartRef = ref(null)
const fatalityChartRef = ref(null)
const regressionChartRef = ref(null)
const environmentImpactChartRef = ref(null)

let pollutionStateChart = null
let topFacilityChart = null
let metalTotalsChart = null
let healthTrendChart = null
let fatalityChart = null
let regressionChart = null
let environmentImpactChart = null

function parseCsv(raw) {
  const [headerLine, ...lines] = raw.trim().split(/\r?\n/)
  const headers = headerLine.split(',')

  return lines
    .filter(Boolean)
    .map((line) => {
      const values = line.split(',')
      return headers.reduce((row, header, index) => {
        const value = values[index] ?? ''
        const numericValue = Number(value)
        row[header] = value !== '' && Number.isFinite(numericValue) ? numericValue : value
        return row
      }, {})
    })
}

function formatMetricLabel(metric) {
  return String(metric || '')
    .replace(/_per_100000/g, ' per 100k')
    .replace(/_per_1000/g, ' per 1k')
    .replace(/_kg/g, ' kg')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

const pearsonSummary = parseCsv(pearsonSummaryCsv)
const spearmanSummary = parseCsv(spearmanSummaryCsv)
const regressionCoefficients = parseCsv(regressionCoefficientsCsv)
const regressionModels = parseCsv(regressionModelsCsv)
const overallEnvironmentSummary = parseCsv(overallEnvironmentSummaryCsv)
const stateEnvironmentSummary = parseCsv(stateEnvironmentSummaryCsv)
const stateEnvironmentTotals = parseCsv(stateEnvironmentTotalsCsv)
const wasteStateYear = parseCsv(wasteStateYearCsv)

async function loadDashboardData() {
  try {
    loading.value = true
    error.value = ''
    dashboardNotice.value = ''

    const [healthRes, stateRes, facilityRes] = await Promise.allSettled([
      Promise.resolve().then(() => api.getHealthAll?.()),
      Promise.resolve().then(() => api.getHeavyMetalState()),
      Promise.resolve().then(() => api.getHeavyMetalFacility()),
    ])

    healthData.value =
      healthRes.status === 'fulfilled' && Array.isArray(healthRes.value?.items) ? healthRes.value.items : []
    statePollutionData.value =
      stateRes.status === 'fulfilled' && Array.isArray(stateRes.value?.items) ? stateRes.value.items : []
    facilityPollutionData.value =
      facilityRes.status === 'fulfilled' && Array.isArray(facilityRes.value?.items) ? facilityRes.value.items : []

    const unavailableSources = [
      healthRes.status === 'rejected' || !Array.isArray(healthRes.value?.items) ? 'health API' : '',
      stateRes.status === 'rejected' || !Array.isArray(stateRes.value?.items) ? 'state emissions API' : '',
      facilityRes.status === 'rejected' || !Array.isArray(facilityRes.value?.items) ? 'facility emissions API' : '',
    ].filter(Boolean)

    if (unavailableSources.length) {
      dashboardNotice.value = `${unavailableSources.join(', ')} unavailable. Showing packaged analysis outputs where possible.`
    }
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

const healthMetricOptions = computed(() => regressionModels.map((item) => item.health_metric))

const environmentStateOptions = computed(() => [
  'Overall',
  ...stateEnvironmentSummary.map((item) => item.state).sort(),
])

const selectedCorrelationSummary = computed(() =>
  selectedCorrelationMethod.value === 'spearman' ? spearmanSummary : pearsonSummary,
)

const selectedHeatmapUrl = computed(() =>
  selectedCorrelationMethod.value === 'spearman' ? spearmanHeatmapUrl : pearsonHeatmapUrl,
)

const selectedRegressionModel = computed(() => {
  return regressionModels.find((item) => item.health_metric === selectedHealthMetric.value) || regressionModels[0]
})

const selectedEnvironmentHeatmapUrl = computed(() => {
  if (selectedEnvironmentState.value === 'Overall') return overallEnvironmentHeatmapUrl

  const match = Object.entries(stateEnvironmentHeatmaps).find(([path]) =>
    path.endsWith(`${selectedEnvironmentState.value}_pearson_heatmap.png`),
  )

  return match?.[1] || overallEnvironmentHeatmapUrl
})

const selectedEnvironmentSignal = computed(() => {
  if (selectedEnvironmentState.value === 'Overall') {
    return overallEnvironmentSummary
      .map((item) => ({
        label: formatMetricLabel(item.waste_metric),
        pollutant: formatMetricLabel(item.top_pollutant_metric),
        corr: Number(item.top_pearson_corr || 0),
        context: `${item.n_states_used} states`,
      }))
      .sort((a, b) => Math.abs(b.corr) - Math.abs(a.corr))[0]
  }

  const item = stateEnvironmentSummary.find((row) => row.state === selectedEnvironmentState.value)
  if (!item) return null

  return {
    label: selectedEnvironmentState.value,
    pollutant: formatMetricLabel(item.top_environmental_metric_for_ewaste),
    corr: Number(item.top_pearson_corr_for_ewaste || 0),
    context: `${item.n_years_total} years`,
  }
})

const topEnvironmentStates = computed(() => {
  return [...stateEnvironmentTotals]
    .map((item) => ({
      state: item.state,
      ewaste: Number(item.ewaste_proxy_tonnes || 0),
      recycling: Number(item.hazardous_recycling_tonnes || 0),
      disposal: Number(item.hazardous_disposal_tonnes || 0),
      air: Number(item.total_air_emission_kg || 0),
      land: Number(item.total_land_emission_kg || 0),
      water: Number(item.total_water_emission_kg || 0),
    }))
    .sort((a, b) => b.ewaste - a.ewaste)
    .slice(0, 5)
})

const selectedEnvironmentTotals = computed(() => {
  if (selectedEnvironmentState.value === 'Overall') {
    return stateEnvironmentTotals.reduce(
      (totals, item) => {
        totals.ewaste += Number(item.ewaste_proxy_tonnes || 0)
        totals.recycling += Number(item.hazardous_recycling_tonnes || 0)
        totals.disposal += Number(item.hazardous_disposal_tonnes || 0)
        totals.air += Number(item.total_air_emission_kg || 0)
        totals.land += Number(item.total_land_emission_kg || 0)
        totals.water += Number(item.total_water_emission_kg || 0)
        return totals
      },
      { ewaste: 0, recycling: 0, disposal: 0, air: 0, land: 0, water: 0 },
    )
  }

  const row = stateEnvironmentTotals.find((item) => item.state === selectedEnvironmentState.value)

  return {
    ewaste: Number(row?.ewaste_proxy_tonnes || 0),
    recycling: Number(row?.hazardous_recycling_tonnes || 0),
    disposal: Number(row?.hazardous_disposal_tonnes || 0),
    air: Number(row?.total_air_emission_kg || 0),
    land: Number(row?.total_land_emission_kg || 0),
    water: Number(row?.total_water_emission_kg || 0),
  }
})

const environmentYearCount = computed(() => {
  const rows =
    selectedEnvironmentState.value === 'Overall'
      ? wasteStateYear
      : wasteStateYear.filter((item) => item.state === selectedEnvironmentState.value)

  return new Set(rows.map((item) => item.year_label)).size
})

const topCorrelationFindings = computed(() => {
  const corrKey = selectedCorrelationMethod.value === 'spearman' ? 'top_spearman_corr' : 'top_pearson_corr'

  return selectedCorrelationSummary.value
    .map((item) => ({
      healthMetric: item.health_metric,
      emissionsMetric: item.top_emissions_metric,
      corr: Number(item[corrKey] || 0),
      pairs: Number(item.n_state_year_pairs || 0),
    }))
    .sort((a, b) => Math.abs(b.corr) - Math.abs(a.corr))
    .slice(0, 4)
})

const selectedMetricTopCorrelation = computed(() => {
  const corrKey = selectedCorrelationMethod.value === 'spearman' ? 'top_spearman_corr' : 'top_pearson_corr'
  const item = selectedCorrelationSummary.value.find((row) => row.health_metric === selectedHealthMetric.value)

  if (!item) return null

  return {
    healthMetric: item.health_metric,
    emissionsMetric: item.top_emissions_metric,
    corr: Number(item[corrKey] || 0),
    pairs: Number(item.n_state_year_pairs || 0),
  }
})

const regressionHighlights = computed(() => {
  return regressionCoefficients
    .filter((item) => item.health_metric === selectedHealthMetric.value)
    .sort((a, b) => Number(b.abs_standardized_beta || 0) - Number(a.abs_standardized_beta || 0))
    .slice(0, 8)
    .reverse()
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
  if (regressionChartRef.value) regressionChart = echarts.init(regressionChartRef.value)
  if (environmentImpactChartRef.value) environmentImpactChart = echarts.init(environmentImpactChartRef.value)
}

function updateCharts() {
  const pollutionState = aggregateStateMetal(filteredPollutionState.value)
  const facilities = topFacilities(filteredPollutionFacility.value)
  const metalTotals = aggregateMetalTotals(filteredPollutionFacility.value)
  const healthTrend = aggregateHealthTrend(filteredHealth.value)
  const fatality = aggregateFatality(filteredHealth.value).slice(0, 8).reverse()
  const regression = regressionHighlights.value
  const environmentStates = topEnvironmentStates.value.slice().reverse()

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

  regressionChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        const item = params[0]
        const row = regression[item.dataIndex]
        const direction = Number(row.standardized_beta || 0) >= 0 ? 'Positive' : 'Negative'
        return `
          <strong>${formatMetricLabel(row.emissions_metric)}</strong><br/>
          ${direction} standardized beta: ${Number(row.standardized_beta || 0).toFixed(2)}<br/>
          Raw beta: ${Number(row.raw_beta || 0).toExponential(2)}
        `
      },
      ...tooltipStyle(),
    },
    grid: { left: 190, right: 26, top: 20, bottom: 24 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#557260' },
      splitLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.08)' } },
    },
    yAxis: {
      type: 'category',
      data: regression.map((item) => formatMetricLabel(item.emissions_metric)),
      axisLabel: { color: '#173a29', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        name: 'Standardized beta',
        type: 'bar',
        data: regression.map((item) => Number(item.standardized_beta || 0)),
        barWidth: 16,
        itemStyle: {
          color(params) {
            return Number(params.value) >= 0 ? '#2f9e6d' : '#c77943'
          },
          borderRadius: [0, 10, 10, 0],
        },
      },
    ],
  })

  environmentImpactChart?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    legend: {
      top: 8,
      textStyle: { color: '#557260' },
    },
    grid: { left: 54, right: 24, top: 54, bottom: 36 },
    xAxis: {
      type: 'category',
      data: environmentStates.map((item) => item.state),
      axisLabel: { color: '#557260' },
      axisLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.14)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#557260',
        formatter(value) {
          return `${Number(value / 1000000).toFixed(0)}m`
        },
      },
      splitLine: { lineStyle: { color: 'rgba(23, 58, 41, 0.08)' } },
    },
    series: [
      {
        name: 'E-waste proxy tonnes',
        type: 'bar',
        data: environmentStates.map((item) => item.ewaste),
        barMaxWidth: 24,
        itemStyle: { color: '#2f9e6d', borderRadius: [8, 8, 0, 0] },
      },
      {
        name: 'Hazardous disposal tonnes',
        type: 'bar',
        data: environmentStates.map((item) => item.disposal),
        barMaxWidth: 24,
        itemStyle: { color: '#c77943', borderRadius: [8, 8, 0, 0] },
      },
      {
        name: 'Hazardous recycling tonnes',
        type: 'bar',
        data: environmentStates.map((item) => item.recycling),
        barMaxWidth: 24,
        itemStyle: { color: '#4f8ebf', borderRadius: [8, 8, 0, 0] },
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
  regressionChart?.resize()
  environmentImpactChart?.resize()
}

function disposeCharts() {
  pollutionStateChart?.dispose()
  topFacilityChart?.dispose()
  metalTotalsChart?.dispose()
  healthTrendChart?.dispose()
  fatalityChart?.dispose()
  regressionChart?.dispose()
  environmentImpactChart?.dispose()
}

watch(
  [filteredPollutionState, filteredPollutionFacility, filteredHealth, selectedHealthMetric, selectedEnvironmentState],
  async () => {
    await nextTick()
    updateCharts()
  },
)

watch(selectedEvidenceView, async () => {
  await nextTick()
  resizeCharts()
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
      <section v-if="dashboardNotice" class="status-card notice-card">
        <h3>Static analysis mode</h3>
        <p>{{ dashboardNotice }}</p>
      </section>

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

      <section class="analysis-shell">
        <div class="section-header">
          <div>
            <span class="section-tag">Evidence Layer</span>
            <h2>
              {{
                selectedEvidenceView === 'environment'
                  ? 'E-waste environment impact signals'
                  : 'Environment-health statistical signals'
              }}
            </h2>
          </div>
          <div class="analysis-controls">
            <div class="evidence-tabs" aria-label="Evidence view">
              <button
                type="button"
                :class="{ active: selectedEvidenceView === 'environment' }"
                @click="selectedEvidenceView = 'environment'"
              >
                Environment
              </button>
              <button
                type="button"
                :class="{ active: selectedEvidenceView === 'health' }"
                @click="selectedEvidenceView = 'health'"
              >
                Health
              </button>
            </div>

            <template v-if="selectedEvidenceView === 'health'">
              <select v-model="selectedCorrelationMethod" aria-label="Correlation method">
                <option value="pearson">Pearson</option>
                <option value="spearman">Spearman</option>
              </select>
              <select v-model="selectedHealthMetric" aria-label="Health metric">
                <option v-for="metric in healthMetricOptions" :key="metric" :value="metric">
                  {{ formatMetricLabel(metric) }}
                </option>
              </select>
            </template>

            <select
              v-else
              v-model="selectedEnvironmentState"
              aria-label="Environment state heatmap"
            >
              <option v-for="state in environmentStateOptions" :key="state" :value="state">
                {{ state === 'Overall' ? 'Overall Australia' : state }}
              </option>
            </select>
          </div>
        </div>

        <div v-show="selectedEvidenceView === 'health'" class="evidence-grid">
          <article class="heatmap-panel">
            <div class="heatmap-frame">
              <img :src="selectedHeatmapUrl" alt="Environment and health correlation heatmap" />
            </div>
          </article>

          <article class="model-panel">
            <span class="model-label">Selected model</span>
            <h3>{{ formatMetricLabel(selectedHealthMetric) }}</h3>
            <div class="model-stats">
              <div>
                <strong>{{ Number(selectedRegressionModel?.r_squared || 0).toFixed(2) }}</strong>
                <span>R squared</span>
              </div>
              <div>
                <strong>{{ Number(selectedRegressionModel?.adjusted_r_squared || 0).toFixed(2) }}</strong>
                <span>Adjusted R squared</span>
              </div>
              <div>
                <strong>{{ selectedRegressionModel?.n_state_year_pairs || 0 }}</strong>
                <span>State-year pairs</span>
              </div>
            </div>
            <p v-if="selectedMetricTopCorrelation">
              Strongest {{ selectedCorrelationMethod }} signal:
              <strong>{{ formatMetricLabel(selectedMetricTopCorrelation.emissionsMetric) }}</strong>
              at {{ Number(selectedMetricTopCorrelation.corr || 0).toFixed(2) }}.
            </p>
          </article>
        </div>

        <div v-show="selectedEvidenceView === 'environment'" class="evidence-grid">
          <article class="heatmap-panel">
            <div class="heatmap-frame">
              <img :src="selectedEnvironmentHeatmapUrl" alt="E-waste and pollutant correlation heatmap" />
            </div>
          </article>

          <article class="model-panel">
            <span class="model-label">Environment impact</span>
            <h3>{{ selectedEnvironmentState === 'Overall' ? 'Overall Australia' : selectedEnvironmentState }}</h3>
            <div class="model-stats">
              <div>
                <strong>{{ formatNumber(selectedEnvironmentTotals.ewaste.toFixed(0)) }}</strong>
                <span>E-waste proxy tonnes</span>
              </div>
              <div>
                <strong>{{ formatNumber(selectedEnvironmentTotals.disposal.toFixed(0)) }}</strong>
                <span>Hazardous disposal tonnes</span>
              </div>
              <div>
                <strong>{{ environmentYearCount }}</strong>
                <span>Years analysed</span>
              </div>
            </div>
            <p v-if="selectedEnvironmentSignal">
              Strongest environment signal:
              <strong>{{ selectedEnvironmentSignal.pollutant }}</strong>
              at {{ selectedEnvironmentSignal.corr.toFixed(2) }} across
              {{ selectedEnvironmentSignal.context }}.
            </p>
          </article>
        </div>
      </section>

      <section v-show="selectedEvidenceView === 'health'" class="chart-grid">
        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">Correlation Ranking</span>
              <h2>Top linked health outcomes</h2>
            </div>
          </div>
          <div class="correlation-list">
            <div v-for="item in topCorrelationFindings" :key="item.healthMetric" class="correlation-row">
              <div>
                <strong>{{ formatMetricLabel(item.healthMetric) }}</strong>
                <span>{{ formatMetricLabel(item.emissionsMetric) }}</span>
              </div>
              <b :class="{ negative: item.corr < 0 }">{{ item.corr.toFixed(2) }}</b>
            </div>
          </div>
        </article>

        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">Regression Coefficients</span>
              <h2>Largest standardized predictors</h2>
            </div>
          </div>
          <div ref="regressionChartRef" class="chart-box"></div>
        </article>
      </section>

      <section v-show="selectedEvidenceView === 'environment'" class="chart-grid">
        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">State Ranking</span>
              <h2>Largest e-waste pressure states</h2>
            </div>
          </div>
          <div class="correlation-list">
            <div v-for="item in topEnvironmentStates" :key="item.state" class="correlation-row">
              <div>
                <strong>{{ item.state }}</strong>
                <span>
                  Air {{ formatNumber(item.air.toFixed(0)) }} kg · Land
                  {{ formatNumber(item.land.toFixed(0)) }} kg
                </span>
              </div>
              <b>{{ formatNumber(item.ewaste.toFixed(0)) }}</b>
            </div>
          </div>
        </article>

        <article class="chart-shell">
          <div class="section-header compact">
            <div>
              <span class="section-tag">Waste Flow</span>
              <h2>E-waste, disposal, and recycling comparison</h2>
            </div>
          </div>
          <div ref="environmentImpactChartRef" class="chart-box"></div>
        </article>
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
.analysis-shell,
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
.heatmap-panel,
.model-panel,
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

.notice-card {
  border-color: rgba(199, 121, 67, 0.26);
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

.analysis-shell {
  margin-bottom: 24px;
}

.analysis-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.evidence-tabs {
  display: inline-flex;
  padding: 4px;
  border-radius: 16px;
  background: rgba(241, 248, 242, 0.92);
  border: 1px solid rgba(210, 232, 214, 0.98);
}

.evidence-tabs button {
  border: 0;
  border-radius: 12px;
  padding: 9px 14px;
  background: transparent;
  color: #557260;
  font-weight: 700;
  cursor: pointer;
}

.evidence-tabs button.active {
  background: #ffffff;
  color: #2e7d32;
  box-shadow: 0 8px 18px rgba(27, 67, 50, 0.08);
}

.analysis-controls select {
  min-width: 190px;
  background: rgba(255, 255, 255, 0.94);
  color: #173a29;
  border: 1px solid rgba(210, 232, 214, 0.98);
  border-radius: 14px;
  padding: 12px 14px;
  outline: none;
}

.evidence-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.65fr;
  gap: 18px;
}

.heatmap-panel,
.model-panel {
  border-radius: 24px;
  padding: 20px;
}

.heatmap-frame {
  width: 100%;
  overflow: auto;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid rgba(210, 232, 214, 0.98);
}

.heatmap-frame img {
  display: block;
  width: 100%;
  min-width: 760px;
  height: auto;
}

.model-label {
  display: inline-flex;
  margin-bottom: 12px;
  color: #2e7d32;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.model-panel h3 {
  margin: 0 0 18px;
  color: #143324;
  font-size: 1.35rem;
  line-height: 1.25;
}

.model-panel p {
  margin: 18px 0 0;
  color: #557260;
  line-height: 1.7;
}

.model-stats {
  display: grid;
  gap: 12px;
}

.model-stats div {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(241, 248, 242, 0.86);
  border: 1px solid rgba(210, 232, 214, 0.92);
}

.model-stats strong {
  color: #143324;
  font-size: 1.15rem;
}

.model-stats span {
  color: #557260;
  text-align: right;
}

.correlation-list {
  display: grid;
  gap: 12px;
}

.correlation-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 70px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(241, 248, 242, 0.82);
  border: 1px solid rgba(210, 232, 214, 0.92);
}

.correlation-row div {
  display: grid;
  gap: 5px;
}

.correlation-row strong {
  color: #143324;
}

.correlation-row span {
  color: #557260;
  font-size: 0.92rem;
}

.correlation-row b {
  color: #2f9e6d;
  font-size: 1.35rem;
}

.correlation-row b.negative {
  color: #c77943;
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
  .evidence-grid,
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
  .heatmap-panel,
  .model-panel,
  .chart-shell,
  .status-card {
    border-radius: 20px;
  }

  .analysis-controls,
  .analysis-controls select {
    width: 100%;
  }

  .heatmap-frame img {
    min-width: 680px;
  }
}
</style>
