<template>
  <div class="ai">
    <div class="eco-shell">
      <header class="head">
        <span class="eco-eyebrow">AI Device Optimizer</span>
        <h1 class="eco-display">
          A smart assistant<br /><em>for tired devices.</em>
        </h1>
        <p class="eco-lead">
          Tell us your device and what's wrong. Get a tailored 4-step plan — or a clear nudge to repair, reuse, or recycle.
        </p>
      </header>

      <transition name="fade-up" mode="out-in">
        <!-- Step 1 -->
        <section v-if="step === 'device'" key="device" class="card">
          <span class="eco-mono">Step 01</span>
          <h2>Pick your device</h2>
          <div class="devices">
            <button v-for="d in devices" :key="d.id" class="device" @click="chooseDevice(d.id)">
              <span class="d-icon">{{ d.icon }}</span>
              <strong>{{ d.label }}</strong>
              <span class="d-text">{{ d.text }}</span>
            </button>
          </div>
        </section>

        <!-- Step 2 -->
        <section v-else-if="step === 'issue'" key="issue" class="card">
          <button class="back" @click="step = 'device'">← Change device</button>
          <span class="eco-mono">Step 02</span>
          <h2>What's the issue with your <em>{{ deviceLabel.toLowerCase() }}</em>?</h2>

          <div class="quick">
            <button
              v-for="q in quickIssues"
              :key="q.label"
              class="chip"
              :class="{ on: issueText.includes(q.label) }"
              @click="setIssue(q.label)"
            >
              <span>{{ q.icon }}</span> {{ q.label }}
            </button>
          </div>

          <label>
            Describe it in your own words
            <textarea v-model="issueText" rows="4" placeholder="e.g. battery drains in 3 hours, gets warm during video calls"></textarea>
          </label>

          <button class="eco-btn eco-btn--mint" :disabled="!issueText.trim()" @click="getTips">
            Get optimisation tips <span class="arrow">→</span>
          </button>
          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        </section>

        <!-- Loading -->
        <section v-else-if="step === 'loading'" key="loading" class="card loading">
          <div class="loader">
            <div class="ring" />
          </div>
          <h2>Analysing your {{ deviceLabel.toLowerCase() }}…</h2>
          <p>The model is reading your description and matching it to actionable tips.</p>
        </section>

        <!-- Result -->
        <section v-else-if="step === 'result' && result" key="result" class="result">
          <header class="rhead">
            <div>
              <span class="eco-mono">Recommendation ready ✓</span>
              <h2>{{ result.issue_label }}</h2>
              <p>{{ result.device_summary }}</p>
            </div>
            <div class="score">
              <span class="eco-mono">Sustainability score</span>
              <div class="ring-bar" :style="{ '--p': sustainScore }">
                <strong>{{ sustainScore }}</strong>
              </div>
              <span class="eco-mono cap">{{ scoreCaption }}</span>
            </div>
          </header>

          <div class="rgrid">
            <article class="block">
              <span class="eco-eyebrow">What's happening</span>
              <h3>Plain-English explanation</h3>
              <p>{{ result.issue_explanation }}</p>
            </article>

            <article class="block">
              <span class="eco-eyebrow">Action plan</span>
              <h3>Optimization tips</h3>
              <ol>
                <li v-for="(t, i) in result.suggestions" :key="i">{{ t }}</li>
              </ol>
            </article>
          </div>

          <div class="paths">
            <article v-for="p in pathSuggestions" :key="p.label" class="path">
              <span class="p-icon">{{ p.icon }}</span>
              <strong>{{ p.label }}</strong>
              <p>{{ p.text }}</p>
              <router-link :to="p.to" class="p-link">{{ p.cta }} →</router-link>
            </article>
          </div>

          <div class="ractions">
            <button class="eco-btn eco-btn--ghost" @click="restart">Run another query</button>
            <span class="eco-mono">Model · {{ result.model }}</span>
          </div>
        </section>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { api } from '@/api'

const devices = [
  { id: 'phone', label: 'Phone', icon: '📱', text: 'Daily mobile use' },
  { id: 'laptop', label: 'Laptop', icon: '💻', text: 'Work and study' },
  { id: 'tablet', label: 'Tablet', icon: '📲', text: 'Reading, browsing' },
]
const quickIssues = [
  { label: 'Battery drains fast', icon: '🔋' },
  { label: 'Runs slowly', icon: '🐢' },
  { label: 'Storage almost full', icon: '💾' },
  { label: 'Overheats during use', icon: '🔥' },
]

const step = ref('device')
const selectedDevice = ref('')
const issueText = ref('')
const errorMessage = ref('')
const result = ref(null)

const deviceLabel = computed(() => devices.find(d => d.id === selectedDevice.value)?.label || 'device')

function chooseDevice(id) { selectedDevice.value = id; step.value = 'issue'; errorMessage.value = '' }
function setIssue(label) {
  if (issueText.value.includes(label)) {
    issueText.value = issueText.value.replace(label, '').replace(/\s{2,}/g, ' ').trim()
  } else {
    issueText.value = (issueText.value + ' ' + label).trim()
  }
}

async function getTips() {
  if (!issueText.value.trim()) return
  step.value = 'loading'
  errorMessage.value = ''
  const apiDeviceType = selectedDevice.value === 'tablet' ? 'phone' : selectedDevice.value
  try {
    result.value = await api.getDeviceOptimizationTips({ device_type: apiDeviceType, issue_text: issueText.value })
    step.value = 'result'
  } catch (err) {
    result.value = mockResponse(selectedDevice.value, issueText.value)
    step.value = 'result'
  }
}

function restart() { step.value = 'device'; selectedDevice.value = ''; issueText.value = ''; result.value = null; errorMessage.value = '' }

function mockResponse(deviceId, text) {
  const cat = /battery|drain|charge|hot|overheat/i.test(text) ? 'Battery drain'
    : /storage|space|full|memory/i.test(text) ? 'Storage full'
    : /slow|lag|crash|freeze/i.test(text) ? 'Slow performance' : 'General device care'
  const labelMap = { phone: 'Phone', laptop: 'Laptop', tablet: 'Tablet' }
  return {
    device_type: deviceId,
    device_label: labelMap[deviceId] || 'Device',
    device_summary: deviceId === 'phone' ? 'Best for everyday mobile use.' : 'Best for longer sessions at a desk.',
    issue_category: cat.toLowerCase().replace(/[^a-z]/g, '_'),
    issue_label: cat,
    issue_explanation: 'Most ' + cat.toLowerCase() + ' issues come from a few common causes — background apps, screen brightness, or storage pressure. Small changes usually help a lot.',
    suggestions: [
      'Restart the device to clear temporary clutter.',
      'Check which apps use the most resources and close ones you don\'t need.',
      'Update the operating system to the latest version.',
      'Free up storage by removing unused apps and large media.',
    ],
    model: 'demo-fallback',
  }
}

const sustainScore = computed(() => {
  if (!result.value) return 0
  const base = { battery_drain: 64, storage_full: 72, slow_performance: 68, general: 78 }
  return base[(result.value.issue_category || 'general').toLowerCase()] || 70
})
const scoreCaption = computed(() => {
  const s = sustainScore.value
  if (s >= 75) return 'Healthy — keep using it'
  if (s >= 55) return 'Worth optimising first'
  return 'Consider repair or reuse'
})
const pathSuggestions = computed(() => {
  const s = sustainScore.value
  if (s >= 70) return [
    { label: 'Extend usage', icon: '⏳', text: 'Apply the tips above for a few weeks. Most issues clear up.', to: '/dashboard', cta: 'See impact' },
    { label: 'When ready', icon: '♻', text: 'When the device finally retires, give it a second life.', to: '/pickup-points', cta: 'Find pickup' },
  ]
  if (s >= 55) return [
    { label: 'Try repair', icon: '🛠', text: 'A part swap (battery, fan) is often cheaper than replacement.', to: '/repair-check', cta: 'Repair tool' },
    { label: 'Or reuse', icon: '♻', text: 'If you upgrade, donate or sell — don\'t bin a working device.', to: '/pickup-points', cta: 'Find pickup' },
  ]
  return [
    { label: 'Repair or replace?', icon: '⚖', text: 'Run a 30-second cost check to decide.', to: '/repair-check', cta: 'Decide now' },
    { label: 'Recycle safely', icon: '⌧', text: 'When it\'s truly done, drop it at a certified e-waste site.', to: '/disposal-locations', cta: 'Find drop-off' },
  ]
})
</script>

<style scoped>
.ai { padding-top: 140px; padding-bottom: 80px; min-height: 100vh; }

.head {
  display: flex; flex-direction: column; gap: 18px;
  max-width: 720px;
  margin: 0 auto 60px;
  text-align: center;
  align-items: center;
}
.head h1 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

.fade-up-enter-active, .fade-up-leave-active { transition: opacity 0.4s var(--ease-out), transform 0.4s var(--ease-out); }
.fade-up-enter-from { opacity: 0; transform: translateY(16px); }
.fade-up-leave-to { opacity: 0; transform: translateY(-12px); }

.card {
  max-width: 920px;
  margin: 0 auto;
  padding: 40px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  display: flex; flex-direction: column; gap: 20px;
}
.card h2 {
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 44px);
  font-weight: 500;
  letter-spacing: -0.03em;
  line-height: 1.05;
}
.card h2 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

.back {
  align-self: flex-start;
  background: transparent;
  border: 0;
  color: var(--ink-2);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}
.back:hover { color: var(--mint); }

.devices { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.device {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 32px 20px;
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  color: var(--ink-0);
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
}
.device:hover {
  background: rgba(125,216,176,0.08);
  border-color: var(--mint);
  transform: translateY(-4px);
}
.d-icon {
  font-size: 36px;
  width: 64px; height: 64px;
  display: grid; place-items: center;
  background: rgba(125,216,176,0.1);
  border: 1px solid rgba(125,216,176,0.25);
  border-radius: var(--r-md);
}
.device strong { font-family: var(--font-display); font-size: 18px; font-weight: 500; }
.d-text { color: var(--ink-2); font-size: 12px; }

.quick { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 14px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
  color: var(--ink-1);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}
.chip:hover { background: rgba(125,216,176,0.08); border-color: var(--mint); }
.chip.on { background: var(--mint); color: var(--ink-on-light); border-color: var(--mint); }

label {
  display: flex; flex-direction: column; gap: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--ink-2);
  text-transform: uppercase;
}
textarea {
  padding: 14px 16px;
  background: rgba(0,0,0,0.25);
  border: 1px solid var(--hairline);
  border-radius: var(--r-sm);
  color: var(--ink-0);
  font-family: var(--font-body);
  font-size: 14px;
  resize: vertical;
  text-transform: none; letter-spacing: 0;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
}
textarea:focus { border-color: var(--mint); box-shadow: 0 0 0 4px rgba(125,216,176,0.12); }

.error {
  padding: 12px 14px;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.25);
  color: var(--bad);
  font-size: 13px;
  border-radius: var(--r-sm);
}

/* Loading */
.loading { align-items: center; text-align: center; padding: 80px 30px; }
.loader { width: 100px; height: 100px; position: relative; margin-bottom: 20px; }
.ring {
  position: absolute; inset: 0;
  border-radius: 50%;
  border: 2px solid var(--hairline);
  border-top-color: var(--mint);
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Result */
.result {
  max-width: 1080px;
  margin: 0 auto;
  display: flex; flex-direction: column; gap: 24px;
}
.rhead {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 32px;
  flex-wrap: wrap;
  padding: 32px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
}
.rhead h2 {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 500;
  margin: 12px 0 8px;
}
.rhead p { color: var(--ink-1); font-size: 14px; max-width: 480px; }
.score { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.score .cap { color: var(--mint); }
.ring-bar {
  width: 100px; height: 100px;
  border-radius: 50%;
  background: conic-gradient(var(--mint) calc(var(--p) * 1%), var(--hairline) 0);
  display: grid; place-items: center;
  position: relative;
}
.ring-bar::before { content: ''; position: absolute; inset: 8px; border-radius: 50%; background: var(--bg-1); }
.ring-bar strong { position: relative; font-family: var(--font-display); font-size: 26px; color: var(--mint); font-weight: 500; }

.rgrid { display: grid; grid-template-columns: 1.1fr 1fr; gap: 20px; }
.block {
  padding: 28px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 14px;
}
.block h3 { font-family: var(--font-display); font-size: 20px; font-weight: 500; }
.block p { color: var(--ink-1); font-size: 14px; line-height: 1.6; }
.block ol { margin: 0; padding-left: 20px; color: var(--ink-1); display: flex; flex-direction: column; gap: 10px; font-size: 14px; line-height: 1.6; }

.paths { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.path {
  padding: 22px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 8px;
}
.p-icon {
  width: 48px; height: 48px;
  display: grid; place-items: center;
  background: rgba(125,216,176,0.12);
  border: 1px solid rgba(125,216,176,0.25);
  border-radius: var(--r-sm);
  font-size: 22px;
}
.path strong { font-family: var(--font-display); font-size: 16px; font-weight: 500; }
.path p { color: var(--ink-2); font-size: 13px; }
.p-link { color: var(--mint); font-size: 13px; font-weight: 500; margin-top: auto; }

.ractions { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }

@media (max-width: 880px) {
  .devices { grid-template-columns: 1fr; }
  .rgrid, .paths { grid-template-columns: 1fr; }
  .rhead { flex-direction: column; align-items: flex-start; }
  .card { padding: 24px; }
}
</style>
