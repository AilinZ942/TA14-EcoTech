<template>
  <section class="repair-page">
    <div class="eco-shell repair-shell">
      <header class="head">
        <span class="eco-eyebrow">Repair Check</span>
        <h1 class="eco-display">Repair or Replace?</h1>
        <p class="eco-lead">
          Choose your device details and let the system compare repair cost, used value, and repair
          status.
        </p>
      </header>

      <div class="eco-glass form-card">
        <div class="form-grid">
          <div class="field">
            <label class="field-label">Brand</label>
            <select v-model="form.brand">
              <option v-for="brand in brandOptions" :key="brand.value" :value="brand.value">
                {{ brand.label }}
              </option>
            </select>
          </div>

          <div class="field">
            <label class="field-label">Model</label>
            <select v-model="form.model">
              <option value="" disabled>Select model</option>
              <option v-for="model in modelOptions" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
          </div>

          <div class="field">
            <label class="field-label">Storage</label>
            <select v-model="form.storage">
              <option value="" disabled>Select storage</option>
              <option v-for="storage in storageOptions" :key="storage" :value="storage">
                {{ storage }}
              </option>
            </select>
          </div>

          <div class="field">
            <label class="field-label">Fault Type</label>
            <select v-model="form.faultType">
              <option value="" disabled>Select fault type</option>
              <option v-for="fault in faultTypeOptions" :key="fault" :value="fault">
                {{ fault }}
              </option>
            </select>
          </div>

          <div class="field">
            <label class="field-label">Age</label>
            <select v-model="form.age">
              <option value="" disabled>Select age</option>
              <option v-for="age in ageOptions" :key="age.value" :value="age.value">
                {{ age.label }}
              </option>
            </select>
          </div>

          <div class="field field--wide">
            <label class="field-label">Problem</label>
            <textarea
              v-model="form.problem"
              rows="5"
              placeholder="Describe the main issue with the device..."
            />
          </div>
        </div>

        <button class="eco-btn eco-btn--mint action-btn" :disabled="isSubmitting" @click="analyze">
          <span v-if="isSubmitting">Analyzing...</span>
          <span v-else>Analyze with AI</span>
          <span class="arrow">→</span>
        </button>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      </div>

      <div v-if="isSubmitting" class="eco-glass result-card loading-card">
        <div class="spinner"></div>
        <span class="eco-mono">Working</span>
        <h2>Running repair analysis...</h2>
        <p>We are checking the price tables, predicting repair status, and preparing the final recommendation.</p>
      </div>

      <div v-else-if="result" class="eco-glass result-card">
        <div class="result-topline">
          <div>
            <p class="eco-mono">Decision</p>
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
  padding: 140px 0 80px;
}

.repair-shell {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.head {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 760px;
  margin: 0 auto;
  text-align: center;
  align-items: center;
}

.head h1 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.form-card,
.result-card {
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  padding: 32px;
}

.form-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

.field-label {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-2);
}

select,
textarea {
  width: 100%;
  border: 1px solid var(--hairline-strong);
  border-radius: var(--r-md);
  background: rgba(255, 255, 255, 0.03);
  color: var(--ink-0);
  font: inherit;
  padding: 16px 18px;
  outline: none;
  transition:
    border-color 0.2s var(--ease-out),
    box-shadow 0.2s var(--ease-out),
    transform 0.2s var(--ease-out),
    background 0.2s var(--ease-out);
}

select {
  min-height: 62px;
}

textarea {
  resize: vertical;
  min-height: 140px;
}

select:focus,
textarea:focus {
  border-color: var(--mint);
  box-shadow: 0 0 0 4px rgba(125, 216, 176, 0.12);
  background: rgba(255, 255, 255, 0.05);
}

.action-btn {
  width: 100%;
  justify-content: center;
  margin-top: 6px;
}

.error-message {
  margin-top: 4px;
  color: var(--bad);
  font-weight: 500;
}

.result-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
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
  border: 4px solid rgba(125, 216, 176, 0.18);
  border-top-color: var(--mint);
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

.result-topline h2 {
  margin: 0;
  font-size: clamp(26px, 3vw, 40px);
  line-height: 1.1;
}

.decision-pill {
  border-radius: var(--r-pill);
  padding: 10px 14px;
  font-weight: 700;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.05);
  color: var(--ink-0);
  border: 1px solid var(--hairline-strong);
}

.decision-pill--repair {
  background: rgba(94, 234, 212, 0.12);
  color: var(--mint-bright);
  border-color: rgba(94, 234, 212, 0.24);
}

.decision-pill--replace {
  background: rgba(244, 162, 97, 0.12);
  color: var(--peach);
  border-color: rgba(244, 162, 97, 0.24);
}

.decision-pill--uncertain {
  background: rgba(255, 255, 255, 0.04);
  color: var(--ink-1);
}

.result-reason {
  color: var(--ink-1);
  line-height: 1.7;
  font-size: 1.02rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.stat {
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  background: rgba(255, 255, 255, 0.03);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat span {
  color: var(--ink-2);
  font-size: 0.92rem;
}

.stat strong {
  font-size: 1.05rem;
  color: var(--ink-0);
}

.summary-block {
  padding: 18px 20px;
  border-radius: var(--r-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--hairline);
}

.summary-block h3 {
  margin: 0 0 12px;
  font-size: 1.02rem;
}

.summary-block ul {
  margin: 0;
  padding-left: 18px;
  color: var(--ink-1);
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

  .repair-page {
    padding-top: 120px;
  }
}
</style>
