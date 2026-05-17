<template>
  <section class="repair-page">
    <div class="repair-shell">
      <header class="hero">
        <div class="hero-badge">
          <span>✦</span>
        </div>
        <h1>Repair or Replace?</h1>
        <p>Choose your device details and let the system compare repair cost, used value, and repair status.</p>
      </header>

      <div class="card">
        <div class="form-grid">
          <div class="field">
            <label>Brand</label>
            <select v-model="form.brand">
              <option v-for="brand in brandOptions" :key="brand.value" :value="brand.value">
                {{ brand.label }}
              </option>
            </select>
          </div>

          <div class="field">
            <label>Model</label>
            <select v-model="form.model">
              <option value="" disabled>Select model</option>
              <option v-for="model in modelOptions" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
          </div>

          <div class="field">
            <label>Storage</label>
            <select v-model="form.storage">
              <option value="" disabled>Select storage</option>
              <option v-for="storage in storageOptions" :key="storage" :value="storage">
                {{ storage }}
              </option>
            </select>
          </div>

          <div class="field">
            <label>Fault Type</label>
            <select v-model="form.faultType">
              <option value="" disabled>Select fault type</option>
              <option v-for="fault in faultTypeOptions" :key="fault" :value="fault">
                {{ fault }}
              </option>
            </select>
          </div>

          <div class="field">
            <label>Age</label>
            <select v-model="form.age">
              <option value="" disabled>Select age</option>
              <option v-for="age in ageOptions" :key="age.value" :value="age.value">
                {{ age.label }}
              </option>
            </select>
          </div>

          <div class="field field--wide">
            <label>Problem</label>
            <textarea
              v-model="form.problem"
              rows="5"
              placeholder="Describe the main issue with the device..."
            />
          </div>
        </div>

        <button class="analyze-button" :disabled="isSubmitting" @click="analyze">
          <span v-if="isSubmitting">Analyzing...</span>
          <span v-else>Analyze with AI</span>
        </button>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      </div>

      <div v-if="isSubmitting" class="result-card loading-card">
        <div class="spinner"></div>
        <h2>Running repair analysis...</h2>
        <p>We are checking the price tables, predicting repair status, and preparing the final recommendation.</p>
      </div>

      <div v-else-if="result" class="result-card">
        <div class="result-topline">
          <div>
            <p class="eyebrow">Decision</p>
            <h2>{{ result.recommendation }}</h2>
          </div>
          <div class="decision-pill" :class="decisionClass(result.recommendation)">
            {{ result.confidence || 'medium' }} confidence
          </div>
        </div>

        <p class="result-reason">{{ result.reason }}</p>

        <div class="stats-grid">
          <div class="stat">
            <span>Current Price</span>
            <strong>{{ formatMoney(result.current_price_aud) }}</strong>
          </div>
          <div class="stat">
            <span>Repair Price</span>
            <strong>{{ formatMoney(result.repair_price_aud) }}</strong>
          </div>
          <div class="stat">
            <span>Repair Status</span>
            <strong>{{ result.repair_status || 'Unavailable' }}</strong>
          </div>
          <div class="stat">
            <span>Decision Source</span>
            <strong>{{ result.decision_source }}</strong>
          </div>
        </div>

        <div class="summary-block">
          <h3>What we used</h3>
          <ul>
            <li><strong>Brand:</strong> {{ result.brand }}</li>
            <li><strong>Model:</strong> {{ result.model }}</li>
            <li><strong>Storage:</strong> {{ result.storage }}</li>
            <li><strong>Age:</strong> {{ result.age }}</li>
            <li><strong>Fault Type:</strong> {{ result.fault_type }}</li>
            <li><strong>Problem:</strong> {{ result.problem }}</li>
          </ul>
        </div>

      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { api, initCSRF } from '@/api'

const brandOptions = [
  { value: 'Apple', label: 'Apple' },
]

const modelStorageMap = {
  'iPhone SE (2nd Gen)': ['64GB', '128GB', '256GB'],
  'iPhone SE (3rd Gen)': ['64GB', '128GB', '256GB'],
  'iPhone XR': ['64GB', '128GB', '256GB'],
  'iPhone 11': ['64GB', '128GB', '256GB'],
  'iPhone 12': ['64GB', '128GB', '256GB'],
  'iPhone 12 mini': ['64GB', '128GB', '256GB'],
  'iPhone 12 Pro': ['128GB', '256GB', '512GB'],
  'iPhone 12 Pro Max': ['128GB', '256GB', '512GB'],
  'iPhone 13': ['128GB', '256GB', '512GB'],
  'iPhone 13 mini': ['128GB', '256GB', '512GB'],
  'iPhone 13 Pro': ['128GB', '256GB', '512GB'],
  'iPhone 13 Pro Max': ['128GB', '256GB', '512GB'],
  'iPhone 14': ['128GB', '256GB', '512GB'],
  'iPhone 14 Plus': ['128GB', '256GB', '512GB'],
  'iPhone 14 Pro': ['128GB', '256GB', '512GB'],
  'iPhone 14 Pro Max': ['128GB', '256GB', '512GB'],
  'iPhone 15': ['128GB', '256GB', '512GB'],
  'iPhone 15 Plus': ['128GB', '256GB', '512GB'],
  'iPhone 15 Pro': ['128GB', '256GB', '512GB'],
  'iPhone 15 Pro Max': ['128GB', '256GB', '512GB'],
  'iPhone 16': ['128GB', '256GB', '512GB'],
  'iPhone 16 Plus': ['128GB', '256GB', '512GB'],
  'iPhone 16 Pro': ['128GB', '256GB', '512GB'],
  'iPhone 16 Pro Max': ['128GB', '256GB', '512GB'],
  'iPhone 16e': ['256GB', '512GB'],
  'iPhone 17': ['256GB', '512GB'],
  'iPhone 17e': ['256GB', '512GB'],
  'iPhone 17 Pro': ['256GB', '512GB', '1TB'],
  'iPhone 17 Pro Max': ['256GB', '512GB', '1TB', '2TB'],
  'iPhone Air': ['256GB', '512GB', '1TB'],
}

const modelOptions = computed(() => Object.keys(modelStorageMap))

const faultTypeMap = computed(() => {
  const base = [
    'Battery',
    'Back glass damage',
    'Rear camera damage',
    'Screen damage',
    'Screen and back glass damage',
    'Other damage',
  ]
  return Object.fromEntries(modelOptions.value.map((model) => [model, base]))
})

const ageOptions = [
  { value: 'unknown_age', label: 'Unknown' },
  { value: '1', label: '1 year' },
  { value: '2', label: '2 years' },
  { value: '3', label: '3 years' },
  { value: '4', label: '4 years' },
  { value: '5', label: '5 years' },
  { value: '6', label: '6 years' },
  { value: '7', label: '7 years' },
  { value: '8+', label: '8+ years' },
]

const form = reactive({
  brand: 'Apple',
  model: '',
  storage: '',
  faultType: '',
  age: '',
  problem: '',
})

const result = ref(null)
const errorMessage = ref('')
const isSubmitting = ref(false)

const storageOptions = computed(() => modelStorageMap[form.model] || [])
const faultTypeOptions = computed(() => faultTypeMap.value[form.model] || [])

function resetDownstream() {
  form.storage = ''
  form.faultType = ''
  result.value = null
  errorMessage.value = ''
}

function formatMoney(value) {
  if (value === null || value === undefined || value === '') return 'Unavailable'
  const numberValue = Number(value)
  if (Number.isNaN(numberValue)) return 'Unavailable'
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: numberValue % 1 === 0 ? 0 : 2,
  }).format(numberValue)
}

function decisionClass(value) {
  const normalized = String(value || '').toLowerCase()
  if (normalized.includes('repair')) return 'decision-pill--repair'
  if (normalized.includes('replace')) return 'decision-pill--replace'
  return 'decision-pill--uncertain'
}

async function analyze() {
  errorMessage.value = ''
  result.value = null

  if (!form.model || !form.storage || !form.faultType || !form.age || !form.problem.trim()) {
    errorMessage.value = 'Please fill in model, storage, fault type, age, and problem before analyzing.'
    return
  }

  isSubmitting.value = true

  try {
    const response = await api.analyzeRepairDecision({
      brand: form.brand,
      model: form.model,
      storage: form.storage,
      fault_type: form.faultType,
      age: form.age,
      problem: form.problem.trim(),
    })

    result.value = response
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Something went wrong.'
  } finally {
    isSubmitting.value = false
  }
}

watch(
  () => form.model,
  () => {
    resetDownstream()
  },
)

watch(
  () => [form.storage, form.faultType, form.age, form.problem],
  () => {
    errorMessage.value = ''
  },
)

onMounted(async () => {
  await initCSRF()
})
</script>

<style scoped>
.repair-page {
  min-height: 100vh;
  padding: 48px 24px 72px;
  background:
    radial-gradient(circle at top, rgba(191, 223, 209, 0.55), transparent 34%),
    linear-gradient(180deg, #f6fbf8 0%, #edf5ef 100%);
  color: #1f4333;
}

.repair-shell {
  max-width: 1120px;
  margin: 0 auto;
}

.hero {
  text-align: center;
  margin-bottom: 28px;
}

.hero-badge {
  width: 104px;
  height: 104px;
  border-radius: 999px;
  margin: 0 auto 22px;
  background: #e2ece7;
  display: grid;
  place-items: center;
  color: #346a53;
  font-size: 2.4rem;
  box-shadow: 0 18px 40px rgba(46, 91, 68, 0.08);
}

.hero h1 {
  margin: 0;
  font-size: clamp(2.6rem, 5vw, 4.4rem);
  line-height: 1.05;
  letter-spacing: -0.04em;
}

.hero p {
  max-width: 760px;
  margin: 16px auto 0;
  color: #5f7f71;
  font-size: 1.1rem;
  line-height: 1.6;
}

.card,
.result-card {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(63, 105, 84, 0.12);
  border-radius: 28px;
  box-shadow: 0 18px 48px rgba(46, 91, 68, 0.08);
  backdrop-filter: blur(16px);
}

.card {
  padding: 28px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field--wide {
  grid-column: 1 / -1;
}

label {
  font-size: 1rem;
  font-weight: 700;
  color: #224235;
}

select,
textarea {
  width: 100%;
  border: 1.5px solid #d6e4db;
  border-radius: 18px;
  background: #fff;
  color: #18362c;
  font: inherit;
  padding: 18px 20px;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

select {
  height: 68px;
}

textarea {
  resize: vertical;
  min-height: 140px;
}

select:focus,
textarea:focus {
  border-color: #95baa4;
  box-shadow: 0 0 0 4px rgba(148, 187, 164, 0.16);
}

.analyze-button {
  width: 100%;
  margin-top: 24px;
  border: none;
  border-radius: 22px;
  padding: 20px 24px;
  background: #c9dcd2;
  color: #3b6550;
  font-size: 1.15rem;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.analyze-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(78, 122, 102, 0.18);
  background: #b7d0c2;
}

.analyze-button:disabled {
  cursor: wait;
  opacity: 0.8;
}

.error-message {
  margin: 16px 2px 0;
  color: #b03d3d;
  font-weight: 600;
}

.result-card {
  margin-top: 24px;
  padding: 28px;
}

.loading-card {
  display: grid;
  place-items: center;
  gap: 12px;
  text-align: center;
}

.spinner {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 4px solid rgba(59, 101, 80, 0.16);
  border-top-color: #3b6550;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.result-topline {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eyebrow {
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.74rem;
  color: #729486;
}

.result-topline h2 {
  margin: 0;
  font-size: 2rem;
  line-height: 1.1;
}

.decision-pill {
  border-radius: 999px;
  padding: 10px 14px;
  font-weight: 700;
  white-space: nowrap;
  background: #edf5ef;
  color: #426452;
}

.decision-pill--repair {
  background: #e5f5ea;
  color: #25603a;
}

.decision-pill--replace {
  background: #fbe9e5;
  color: #9e4b31;
}

.decision-pill--uncertain {
  background: #eef2f4;
  color: #50606a;
}

.result-reason {
  margin: 18px 0 0;
  color: #456557;
  line-height: 1.7;
  font-size: 1.02rem;
}

.stats-grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.stat {
  border: 1px solid rgba(63, 105, 84, 0.1);
  border-radius: 20px;
  background: #f8fbf9;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat span {
  color: #678275;
  font-size: 0.92rem;
}

.stat strong {
  font-size: 1.05rem;
  color: #19372d;
}

.summary-block {
  margin-top: 22px;
  padding: 18px 20px;
  border-radius: 22px;
  background: #f4f8f6;
}

.summary-block h3 {
  margin: 0 0 12px;
  font-size: 1.02rem;
}

.summary-block ul {
  margin: 0;
  padding-left: 18px;
  color: #46685a;
  line-height: 1.8;
}

@media (max-width: 860px) {
  .form-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .result-topline {
    flex-direction: column;
  }
}
</style>
