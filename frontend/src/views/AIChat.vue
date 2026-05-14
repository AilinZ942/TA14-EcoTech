<template>
  <section class="device-optimizer-page">
    <div class="page-intro">
      <div class="intro-text">
        <h2>Optimize your device smarter</h2>
        <p>Get personalized tips to improve performance and extend lifespan</p>
      </div>

      <div class="info-wrapper">
        <button class="info-button">ⓘ How it works</button>

        <div class="info-popover">
          <h3>How it works</h3>
          <ol>
            <li>Select your device</li>
            <li>Describe your issue</li>
            <li>Our AI analyzes your input</li>
            <li>Get personalized optimization tips</li>
          </ol>
        </div>
      </div>
    </div>

    <div class="optimizer-card">
      <template v-if="!selectedDeviceType && !result">
        <h1>Select Your Device</h1>
        <p class="subtitle">AI-powered optimization for sustainable device performance</p>

        <div class="device-grid">
          <button class="device-card" type="button" @click="selectedDeviceType = 'phone'">
            <div class="icon-circle">
              <img src="@/assets/icons/mobile-notch.png" class="device-icon" />
            </div>
            <h2>Phone</h2>
            <p>Best for everyday use and mobility</p>
          </button>

          <button class="device-card" type="button" @click="selectedDeviceType = 'laptop'">
            <div class="icon-circle">
              <img src="@/assets/icons/laptop.png" class="device-icon" />
            </div>
            <h2>Laptop</h2>
            <p>Best for study, work, and long sessions</p>
          </button>
        </div>
      </template>

      <template v-else-if="selectedDeviceType && !result && !isSending">
        <button class="back-button" type="button" @click="selectedDeviceType = ''">
          ← Back to device selection
        </button>

        <h1>What's the Issue?</h1>
        <p class="subtitle">
          Describe the problem you're experiencing with your
          {{ getDeviceLabel(selectedDeviceType).toLowerCase() }}
        </p>

        <label class="query-label" for="issueText">Your Query</label>
        <textarea
          id="issueText"
          v-model="issueText"
          :placeholder="getPlaceholder(selectedDeviceType)"
        ></textarea>

        <button
          class="submit-button"
          :class="{ active: issueText.trim() }"
          type="button"
          @click="getTips"
        >
          Get Optimization Tips
        </button>
        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      </template>

      <template v-else-if="isSending">
        <div class="loading-card">
          <div class="loading-spinner"></div>
          <h2>Analyzing Your Issue...</h2>
          <p>Our AI is processing your query to provide the best optimization tips</p>
        </div>
      </template>

      <template v-else>
        <div class="success-icon">✓</div>

        <h1>{{ result.issue_label }}</h1>
        <p class="subtitle">
          Here are personalized recommendations for your {{ result.device_label.toLowerCase() }}
        </p>

        <div class="query-summary"><strong>Your Query:</strong> {{ issueText }}</div>

        <div class="result-summary">
          <div class="summary-block">
            <span>Device</span>
            <strong>{{ result.device_label }}</strong>
          </div>

          <div class="summary-block">
            <span>Issue Category</span>
            <strong>{{ result.issue_label }}</strong>
          </div>

          <div class="summary-block">
            <span>Why It Matters</span>
            <strong>{{ result.device_summary }}</strong>
          </div>
        </div>

        <div class="result-section">
          <h2>What may be affecting your device</h2>
          <p>{{ result.issue_explanation }}</p>
        </div>

        <div class="result-section">
          <h2>Optimisation tips</h2>

          <div class="tips-list">
            <div v-for="(tip, index) in result.suggestions" :key="tip" class="tip-card">
              <span class="tip-number">{{ index + 1 }}</span>
              <p>{{ tip }}</p>
            </div>
          </div>
        </div>

        <button class="restart-button" type="button" @click="resetForm">
          ↻ Start New Optimization
        </button>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { api } from '@/api'

const STORAGE_KEY = 'ecotech-device-optimizer-v2'

const deviceTypes = [
  {
    value: 'laptop',
    label: 'Laptop',
    hint: 'Good for study, work, and longer sessions',
  },
  {
    value: 'phone',
    label: 'Phone',
    hint: 'Good for everyday use and mobility',
  },
]

const selectedDeviceType = ref('')
const issueText = ref('')
const result = ref(null)
const errorMessage = ref('')
const isSending = ref(false)

const resultTitle = computed(() => {
  if (result.value) {
    return `${result.value.device_label} - ${result.value.issue_label}`
  }

  if (selectedDeviceType.value && issueText.value.trim()) {
    const device = getDeviceLabel(selectedDeviceType.value)
    return `${device} - Ready for analysis`
  }

  return 'No results yet'
})

const canOptimize = computed(() => Boolean(selectedDeviceType.value && issueText.value.trim()))

function getPlaceholder(device) {
  if (device === 'laptop') {
    return 'e.g., My laptop is running very slow'
  }
  if (device === 'phone') {
    return 'e.g., My phone battery drains too quickly'
  }
  return 'Describe your issue...'
}

function getDeviceLabel(value) {
  const item = deviceTypes.find((entry) => entry.value === value)
  return item ? item.label : 'Device'
}

function loadState() {
  if (typeof window === 'undefined') return

  const raw = window.sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return

  try {
    const parsed = JSON.parse(raw)
    selectedDeviceType.value = parsed.selectedDeviceType || ''
    issueText.value = parsed.issueText || ''
    result.value = parsed.result || null
  } catch {
    selectedDeviceType.value = ''
    issueText.value = ''
    result.value = null
  }
}

function persistState() {
  if (typeof window === 'undefined') return

  window.sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      selectedDeviceType: selectedDeviceType.value,
      issueText: issueText.value,
      result: result.value,
    }),
  )
}

function resetForm() {
  selectedDeviceType.value = ''
  issueText.value = ''
  result.value = null
  errorMessage.value = ''
  persistState()
}

async function getTips() {
  if (!selectedDeviceType.value || !issueText.value.trim()) {
    errorMessage.value = 'Please describe the issue before getting optimisation tips.'
    result.value = null
    persistState()
    return
  }

  if (isSending.value) return

  isSending.value = true
  errorMessage.value = ''

  try {
    const response = await api.getDeviceOptimizationTips({
      device_type: selectedDeviceType.value,
      issue_text: issueText.value.trim(),
    })

    result.value = response
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Something went wrong.'
    result.value = null
  } finally {
    isSending.value = false
    persistState()
  }
}

watch([selectedDeviceType, issueText, result], persistState, { deep: true })

onMounted(() => {
  loadState()
  persistState()
})
</script>

<style scoped>
/* Page Layout */
.device-optimizer-page {
  min-height: 100vh;
  padding: 30px 24px 60px;
  background: #eaf5ef;

  display: flex;
  flex-direction: column;
  align-items: center;

  color: #173f2e;
}

/* Intro */
.page-intro {
  width: min(100%, 1080px);
  margin: 0 auto 18px;

  display: flex;
  justify-content: space-between;
  align-items: center;
}

.intro-text h2 {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
  color: #1f4d3a;
}

.intro-text p {
  margin: 0;
  font-size: 16px;
  color: #5f7f73;
}

/* Info Button + Popover */
.info-wrapper {
  position: relative;
}

.info-button {
  border: none;
  background: #d9eee4;
  color: #2d7352;

  border-radius: 999px;
  padding: 10px 18px;

  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
}

.info-popover {
  position: absolute;
  top: 52px;
  right: 0;

  width: 300px;
  padding: 18px;
  border-radius: 16px;

  background: white;
  box-shadow: 0 14px 34px rgba(23, 63, 46, 0.16);

  opacity: 0;
  pointer-events: none;
  transform: translateY(-6px);
  transition: 0.2s ease;
}

.info-wrapper:hover .info-popover {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.info-popover h3 {
  margin: 0 0 10px;
  font-size: 18px;
  color: #173f2e;
}

.info-popover ol {
  margin: 0;
  padding-left: 20px;
  line-height: 1.7;
  color: #557d70;
}

/* Main Card */
.optimizer-card {
  width: min(100%, 1080px);

  background: white;
  border-radius: 22px;
  padding: 46px 52px;

  box-shadow: 0 18px 42px rgba(23, 63, 46, 0.14);
}

/* Titles */
.optimizer-card h1 {
  margin: 0;
  text-align: center;
  font-size: 42px;
  font-weight: 700;
}

.subtitle {
  margin: 14px 0 38px;
  text-align: center;
  font-size: 22px;
  color: #557d70;
}

/* Device Cards */
.device-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 28px;
}

.device-card {
  border: none;
  border-radius: 18px;
  background: #d9eee4;

  padding: 44px 32px;
  cursor: pointer;

  transition: 0.2s ease;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 26px rgba(23, 63, 46, 0.14);
}

.icon-circle {
  width: 116px;
  height: 116px;
  margin: 0 auto 24px;

  border-radius: 50%;
  background: #2d7352;

  display: flex;
  align-items: center;
  justify-content: center;
}

.device-card h2 {
  margin: 0 0 14px;
  font-size: 28px;
  text-align: center;
}

.device-card p {
  margin: 0;
  text-align: center;
  font-size: 18px;
  color: #42685c;
}

.device-icon {
  width: 56px;
  height: 56px;
  object-fit: contain;
}

/* Back Button */
.back-button {
  border: none;
  background: none;

  font-size: 20px;
  font-weight: 600;
  color: #557d70;

  cursor: pointer;
  margin-bottom: 28px;
}

/* Input */
.query-label {
  display: block;
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 14px;
}

textarea {
  width: 100%;
  min-height: 170px;

  border-radius: 16px;
  border: 1px solid #d8e6df;

  padding: 24px;
  font-size: 22px;

  resize: vertical;
  outline: none;
}

/* Buttons */
.submit-button,
.restart-button {
  width: 100%;
  margin-top: 34px;
  border: none;
  border-radius: 14px;
  padding: 24px;
  font-size: 22px;
  font-weight: 700;
  background: #c7ddd4;
  color: #315f50;
  cursor: pointer;
  transition: 0.2s ease;
}

.restart-button:hover {
  background: #2d7352;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(45, 115, 82, 0.2);
}

.submit-button.active {
  background: #2d7352;
  color: white;
  box-shadow: 0 12px 24px rgba(45, 115, 82, 0.2);
}

.submit-button.active:hover {
  background: #246247;
  transform: translateY(-2px);
}

/* Loading */
.loading-card {
  margin-top: 34px;
  padding: 48px 32px;

  border-radius: 18px;
  background: #ffffff;

  box-shadow: 0 14px 34px rgba(23, 63, 46, 0.14);
  text-align: center;
}

.loading-spinner {
  width: 64px;
  height: 64px;

  margin: 0 auto 22px;

  border: 6px solid #e6f0eb;
  border-top-color: #2d7352;

  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Result */
.success-icon {
  width: 82px;
  height: 82px;

  margin: 0 auto 26px;

  border-radius: 50%;
  background: #eef4f1;

  display: flex;
  align-items: center;
  justify-content: center;

  font-size: 52px;
  color: #2d7352;
}

.query-summary {
  margin-bottom: 30px;
  padding: 22px 26px;

  border-radius: 18px;
  background: #f1f8f5;

  font-size: 20px;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  margin-bottom: 34px;
}

.summary-block {
  padding: 24px;
  border-radius: 22px;

  background: linear-gradient(180deg, #ffffff 0%, #f5fbf8 100%);
  border: 1px solid #d6e8df;
}

.summary-block span {
  display: block;
  margin-bottom: 14px;

  font-size: 18px;
  font-weight: 700;
  text-transform: uppercase;

  color: #647c70;
}

.summary-block strong {
  font-size: 22px;
}

/* Tips */
.tips-list {
  display: grid;
  gap: 22px;
}

.tip-card {
  display: flex;
  align-items: center;
  gap: 22px;

  padding: 22px 24px;

  border-radius: 16px;
  background: #e9f5ef;
}

.tip-number {
  width: 46px;
  height: 46px;

  border-radius: 50%;
  background: #2d7352;
  color: white;

  display: flex;
  align-items: center;
  justify-content: center;
}

/* Error */
.error-message {
  margin-top: 18px;
  color: #ad3b3b;
  font-weight: 600;
}

/* Responsive */
@media (max-width: 760px) {
  .device-grid,
  .result-summary {
    grid-template-columns: 1fr;
  }
}
</style>
