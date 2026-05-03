<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api'
import NewFeatureDashboard from './New_feature_Dashboard.vue'
import pearsonHeatmapUrl from '@/assets/health-analysis/emissions_health_pearson_heatmap.png'
import spearmanHeatmapUrl from '@/assets/health-analysis/emissions_health_spearman_heatmap.png'
import environmentHeatmapUrl from '@/assets/environment-analysis/overall_state_aggregate_pearson_heatmap.png'

const selectedMethod = ref('spearman')

const selectedHeatmapUrl = computed(() =>
  selectedMethod.value === 'spearman' ? spearmanHeatmapUrl : pearsonHeatmapUrl,
)

const summaryCards = ref([])
const pathwayChains = ref([])
const environmentSummary = ref([])
const stateEnvironmentSignals = ref([])
const topEwasteStates = ref([])
const findings = ref([])
const modelCards = ref([])

function applyHealthData(data = {}) {
  summaryCards.value = Array.isArray(data.summaryCards) ? data.summaryCards : []
  pathwayChains.value = Array.isArray(data.pathwayChains) ? data.pathwayChains : []
  environmentSummary.value = Array.isArray(data.environmentSummary) ? data.environmentSummary : []
  stateEnvironmentSignals.value = Array.isArray(data.stateEnvironmentSignals)
    ? data.stateEnvironmentSignals
    : []
  topEwasteStates.value = Array.isArray(data.topEwasteStates) ? data.topEwasteStates : []
  findings.value = Array.isArray(data.findings) ? data.findings : []
  modelCards.value = Array.isArray(data.modelCards) ? data.modelCards : []
}

onMounted(async () => {
  try {
    applyHealthData(await api.getHealthAll())
  } catch (error) {
    console.error('[Dashboard] failed to load health data:', error)
  }
})
</script>

<template>
  <main class="dashboard-page">
    <section class="hero-panel">
      <div>
        <span class="eyebrow">Impact Dashboard</span>
        <h1>E-waste pollution and health impact insights</h1>
        <p>
          This dashboard presents the evidence pathway from e-waste pressure to environmental
          pollution, then from pollution indicators to health burden signals.
        </p>
      </div>
      <div class="hero-chips">
        <span>E-waste pressure</span>
        <span>Environmental emissions</span>
        <span>Health burden</span>
      </div>
    </section>

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

    <section class="stats-grid">
      <article v-for="card in summaryCards" :key="card.label" class="card">
        <span class="card-label">{{ card.label }}</span>
        <h2>{{ card.value }}</h2>
        <p>{{ card.text }}</p>
      </article>
    </section>

    <section class="analysis-panel">
      <div class="section-header">
        <div>
          <span class="section-tag">E-waste → Environment</span>
          <h2>E-waste pressure and pollutant emission signals</h2>
        </div>
      </div>

      <div class="heatmap-frame">
        <img :src="environmentHeatmapUrl" alt="E-waste and pollutant correlation heatmap" />
      </div>
    </section>

    <section class="content-grid">
      <article class="panel">
        <div class="section-header compact">
          <div>
            <span class="section-tag">Overall Signals</span>
            <h2>National environment correlations</h2>
          </div>
        </div>
        <div class="finding-list">
          <div v-for="item in environmentSummary" :key="item.metric" class="finding-row">
            <div>
              <strong>{{ item.metric }}</strong>
              <span>{{ item.pollutant }} · {{ item.context }}</span>
            </div>
            <b>{{ item.corr.toFixed(2) }}</b>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="section-header compact">
          <div>
            <span class="section-tag">State Signals</span>
            <h2>Strongest state-level e-waste links</h2>
          </div>
        </div>
        <div class="finding-list">
          <div v-for="item in stateEnvironmentSignals" :key="item.state" class="finding-row">
            <div>
              <strong>{{ item.state }}</strong>
              <span>{{ item.pollutant }}</span>
            </div>
            <b :class="{ negative: item.corr < 0 }">{{ item.corr.toFixed(2) }}</b>
          </div>
        </div>
      </article>
    </section>

    <section class="analysis-panel">
      <div class="section-header">
        <div>
          <span class="section-tag">Environment → Health</span>
          <h2>Pollution indicators and health burden signals</h2>
        </div>
        <div class="method-tabs" aria-label="Correlation method">
          <button
            type="button"
            :class="{ active: selectedMethod === 'pearson' }"
            @click="selectedMethod = 'pearson'"
          >
            Pearson
          </button>
          <button
            type="button"
            :class="{ active: selectedMethod === 'spearman' }"
            @click="selectedMethod = 'spearman'"
          >
            Spearman
          </button>
        </div>
      </div>

      <div class="heatmap-frame">
        <img :src="selectedHeatmapUrl" alt="Environment and health correlation heatmap" />
      </div>
    </section>

    <section class="content-grid">
      <article class="panel">
        <div class="section-header compact">
          <div>
            <span class="section-tag">Top Signals</span>
            <h2>Fixed analysis findings</h2>
          </div>
        </div>
        <div class="finding-list">
          <div v-for="finding in findings" :key="finding.metric" class="finding-row">
            <div>
              <strong>{{ finding.metric }}</strong>
              <span>{{ finding.signal }}</span>
            </div>
            <b>
              {{ selectedMethod === 'spearman' ? finding.spearman.toFixed(2) : finding.pearson.toFixed(2) }}
            </b>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="section-header compact">
          <div>
            <span class="section-tag">Regression Summary</span>
            <h2>Selected model results</h2>
          </div>
        </div>
        <div class="model-list">
          <div v-for="model in modelCards" :key="model.title" class="model-card">
            <h3>{{ model.title }}</h3>
            <div class="model-stats">
              <span>R squared <strong>{{ model.r2 }}</strong></span>
              <span>Adjusted <strong>{{ model.adjusted }}</strong></span>
            </div>
            <p>{{ model.note }}</p>
          </div>
        </div>
      </article>
    </section>

    <section class="panel state-pressure-panel">
      <div class="section-header compact">
        <div>
          <span class="section-tag">E-waste Pressure</span>
          <h2>Largest e-waste pressure states</h2>
        </div>
      </div>
      <div class="state-pressure-grid">
        <article v-for="item in topEwasteStates" :key="item.state" class="state-card">
          <h3>{{ item.state }}</h3>
          <strong>{{ item.ewaste }}</strong>
          <span>Air {{ item.air }} · Water {{ item.water }}</span>
        </article>
      </div>
    </section>

    <section class="new-feature-shell">
      <NewFeatureDashboard />
    </section>
  </main>
</template>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  padding: 30px 24px 80px;
  background:
    radial-gradient(circle at 88% 8%, rgba(129, 199, 132, 0.12), transparent 18%),
    radial-gradient(circle at 12% 92%, rgba(67, 160, 71, 0.08), transparent 22%),
    linear-gradient(180deg, #f8fbf8 0%, #eef4ef 100%);
  color: #163728;
}

.hero-panel,
.pathway-grid,
.stats-grid,
.analysis-panel,
.content-grid,
.state-pressure-panel {
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
}

.hero-panel,
.card,
.pathway-card,
.analysis-panel,
.panel {
  border: 1px solid rgba(226, 238, 227, 0.98);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.78) 0%, rgba(251, 253, 251, 0.88) 100%);
  box-shadow:
    0 18px 34px rgba(27, 67, 50, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(14px);
}

.hero-panel {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 24px;
  margin-bottom: 24px;
  padding: 32px;
  border-radius: 28px;
}

.eyebrow,
.section-tag,
.card-label {
  display: inline-flex;
  margin: 0 0 14px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(232, 245, 233, 0.9);
  border: 1px solid rgba(207, 232, 209, 0.98);
  color: #2e7d32;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-panel h1 {
  margin: 0 0 14px;
  font-size: clamp(2rem, 4vw, 3.5rem);
  line-height: 1.08;
  color: #143324;
}

.hero-panel p,
.card p,
.model-card p {
  margin: 0;
  color: #587465;
  line-height: 1.75;
}

.hero-chips {
  display: flex;
  flex-wrap: wrap;
  align-content: center;
  gap: 12px;
}

.hero-chips span {
  padding: 12px 16px;
  border-radius: 999px;
  background: #eff8f0;
  border: 1px solid rgba(210, 232, 214, 0.98);
  font-weight: 700;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.pathway-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.card,
.pathway-card,
.analysis-panel,
.panel {
  border-radius: 24px;
  padding: 24px;
}

.analysis-panel {
  margin-bottom: 24px;
}

.pathway-card h2 {
  margin: 0 0 18px;
  color: #143324;
  font-size: 1.45rem;
}

.pathway-card p {
  margin: 18px 0 0;
  color: #587465;
  line-height: 1.75;
}

.pathway-steps {
  display: flex;
  align-items: stretch;
  gap: 10px;
  flex-wrap: wrap;
}

.pathway-steps strong,
.pathway-steps .arrow {
  display: inline-flex;
  align-items: center;
  min-height: 48px;
}

.pathway-steps strong {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(241, 248, 242, 0.9);
  border: 1px solid rgba(210, 232, 214, 0.98);
  color: #163728;
}

.pathway-steps .arrow {
  color: #2e7d32;
  font-size: 1.35rem;
  font-weight: 900;
}

.card h2 {
  margin: 0 0 8px;
  color: #143324;
  font-size: 2rem;
}

.section-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

.section-header h2 {
  margin: 0;
  color: #143324;
  font-size: 1.45rem;
}

.section-header.compact {
  margin-bottom: 12px;
}

.method-tabs {
  display: inline-flex;
  gap: 6px;
  padding: 5px;
  border-radius: 16px;
  background: rgba(241, 248, 242, 0.92);
  border: 1px solid rgba(210, 232, 214, 0.98);
}

.method-tabs button {
  border: 0;
  border-radius: 12px;
  padding: 10px 15px;
  background: transparent;
  color: #587465;
  font-weight: 800;
  cursor: pointer;
}

.method-tabs button.active {
  background: #ffffff;
  color: #2e7d32;
  box-shadow: 0 8px 18px rgba(27, 67, 50, 0.08);
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

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-top: 24px;
  margin-bottom: 24px;
}

.finding-list,
.model-list {
  display: grid;
  gap: 12px;
}

.finding-row,
.model-card {
  border-radius: 18px;
  background: rgba(241, 248, 242, 0.82);
  border: 1px solid rgba(210, 232, 214, 0.92);
}

.finding-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 70px;
  padding: 14px 16px;
}

.finding-row div {
  display: grid;
  gap: 5px;
}

.finding-row strong,
.model-card h3 {
  color: #143324;
}

.finding-row span {
  color: #587465;
}

.finding-row b {
  color: #2f9e6d;
  font-size: 1.35rem;
}

.finding-row b.negative {
  color: #c77943;
}

.state-pressure-panel {
  margin-top: 24px;
}

.state-pressure-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.state-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(241, 248, 242, 0.82);
  border: 1px solid rgba(210, 232, 214, 0.92);
}

.state-card h3 {
  margin: 0;
  color: #143324;
}

.state-card strong {
  color: #2f9e6d;
  font-size: 1.45rem;
}

.state-card span {
  color: #587465;
  line-height: 1.5;
}

.model-card {
  padding: 16px;
}

.model-card h3 {
  margin: 0 0 10px;
}

.model-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.model-stats span {
  padding: 8px 10px;
  border-radius: 12px;
  background: #ffffff;
  color: #587465;
}

.model-stats strong {
  color: #143324;
}

@media (max-width: 1100px) {
  .hero-panel,
  .pathway-grid,
  .stats-grid,
  .content-grid,
  .state-pressure-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    padding: 18px 14px 60px;
  }

  .hero-panel,
  .card,
  .pathway-card,
  .analysis-panel,
  .panel {
    border-radius: 20px;
  }

  .section-header {
    align-items: stretch;
    flex-direction: column;
  }

  .method-tabs {
    width: 100%;
  }

  .method-tabs button {
    flex: 1;
  }

  .heatmap-frame img {
    min-width: 680px;
  }
}
</style>
