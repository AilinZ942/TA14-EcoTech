<template>
  <div class="dash">
    <!-- INTRO -->
    <transition name="fade-up" mode="out-in">
      <section v-if="phase === 'intro'" key="intro" class="phase intro">
        <div class="eco-shell intro-grid">
          <div class="intro-text">
            <span class="eco-eyebrow">Health & e-waste</span>
            <h1 class="eco-display">
              Five questions.<br />
              <em>Real impact.</em>
            </h1>
            <p class="eco-lead">
              Most health stats about e-waste land flat. So we'll ask you five quick questions —
              then show you the numbers that actually apply to <em>your</em> habits.
            </p>
            <div class="intro-actions">
              <button class="eco-btn eco-btn--mint" @click="start">
                Start the 60-second check <span class="arrow">→</span>
              </button>
              <button class="eco-btn eco-btn--ghost" @click="phase = 'insights'">
                Skip to the data
              </button>
            </div>
          </div>
          <aside class="intro-meta">
            <div class="meta-card">
              <span class="eco-mono">What you'll learn</span>
              <ul>
                <li>The pollutant most linked to your habits</li>
                <li>Your personal health-risk profile</li>
                <li>Three concrete actions you can take today</li>
              </ul>
            </div>
            <div class="meta-card">
              <span class="eco-mono">Time</span>
              <strong>~ 60 seconds</strong>
            </div>
          </aside>
        </div>
      </section>

      <!-- QUIZ -->
      <section v-else-if="phase === 'quiz'" key="quiz" class="phase quiz">
        <div class="eco-shell quiz-shell">
          <header class="quiz-head">
            <span class="eco-mono">Question {{ qIndex + 1 }} / {{ questions.length }}</span>
            <div class="progress">
              <div class="bar" :style="{ width: progressPct + '%' }" />
            </div>
            <button class="back" @click="back" :disabled="qIndex === 0">← Back</button>
          </header>

          <transition name="slide" mode="out-in">
            <div class="qcard" :key="qIndex">
              <h2 class="qprompt">{{ current.q }}</h2>
              <p v-if="current.help" class="qhelp">{{ current.help }}</p>

              <div class="opts">
                <button
                  v-for="opt in current.options"
                  :key="opt.value"
                  class="opt"
                  :class="{ on: answers[current.id] === opt.value }"
                  @click="answer(opt.value)"
                >
                  <span class="opt-mark">
                    <svg v-if="answers[current.id] === opt.value" viewBox="0 0 16 16" width="14" height="14">
                      <path d="M2 8l4 4 8-9" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </span>
                  <span class="opt-text">
                    <strong>{{ opt.label }}</strong>
                    <em v-if="opt.tag">{{ opt.tag }}</em>
                  </span>
                </button>
              </div>
            </div>
          </transition>
        </div>
      </section>

      <!-- INSIGHTS -->
      <section v-else key="insights" class="phase insights">
        <div class="eco-shell">
          <header class="ins-head">
            <span class="eco-eyebrow reveal">Your read</span>
            <h2 class="eco-h2 reveal reveal-delay-1">
              Based on your answers,<br />
              <em>{{ profile.title }}</em>
            </h2>
            <p class="eco-lead reveal reveal-delay-2">{{ profile.summary }}</p>
            <div class="ins-actions reveal reveal-delay-3">
              <button class="eco-btn eco-btn--ghost" @click="restart">Retake quiz</button>
              <router-link to="/disposal-locations" class="eco-btn eco-btn--mint">
                Find a drop-off <span class="arrow">→</span>
              </router-link>
            </div>
          </header>

          <!-- THREE BIG NUMBERS -->
          <div class="kpi-grid">
            <div class="kpi reveal" v-for="(k, i) in kpis" :key="k.label" :class="`reveal-delay-${i + 1}`">
              <span class="eco-mono">{{ k.label }}</span>
              <strong class="kpi-num">{{ k.value }}<span>{{ k.unit }}</span></strong>
              <p>{{ k.note }}</p>
            </div>
          </div>

          <!-- CHAIN -->
          <article class="chain reveal">
            <span class="eco-eyebrow">The chain</span>
            <h3>From device → environment → people</h3>
            <div class="chain-flow">
              <div v-for="(step, i) in chain" :key="step.t" class="chain-node">
                <span class="ch-dot" />
                <strong>{{ step.t }}</strong>
                <p>{{ step.d }}</p>
                <span v-if="i < chain.length - 1" class="chain-line" />
              </div>
            </div>
          </article>

          <!-- SIGNAL BARS -->
          <article class="signals reveal">
            <div class="signals-head">
              <span class="eco-eyebrow">Strongest signals</span>
              <h3>What predicts harm best?</h3>
            </div>
            <div class="signal-list">
              <div v-for="f in findings" :key="f.metric" class="signal">
                <div class="sig-meta">
                  <strong>{{ f.metric }}</strong>
                  <span>{{ f.signal }}</span>
                </div>
                <div class="sig-bars">
                  <div class="sig-bar">
                    <div class="bar mint" :style="{ width: (f.spearman * 100) + '%' }" />
                    <span class="bar-val">{{ f.spearman }}</span>
                  </div>
                </div>
              </div>
            </div>
            <p class="sig-foot">
              <span class="eco-mono">Spearman correlation · 0–1</span>
              Based on Australian state-year health and emissions data.
            </p>
          </article>

          <!-- WHAT TO DO -->
          <article class="actions-card reveal">
            <span class="eco-eyebrow">What to do</span>
            <h3>Three concrete actions</h3>
            <div class="action-list">
              <div v-for="(a, i) in profile.actions" :key="a.title" class="action">
                <span class="a-num">0{{ i + 1 }}</span>
                <div>
                  <strong>{{ a.title }}</strong>
                  <p>{{ a.text }}</p>
                </div>
                <router-link v-if="a.to" :to="a.to" class="a-link">{{ a.cta }} →</router-link>
              </div>
            </div>
          </article>
        </div>
      </section>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '@/api'
import { useReveal } from '@/composables/useReveal'

useReveal()

// Quiz state
const phase = ref('intro') // intro | quiz | insights
const qIndex = ref(0)
const answers = reactive({})

const questions = [
  {
    id: 'replace',
    q: 'How often do you replace your phone?',
    help: 'Best estimate. Skips and trade-ins count too.',
    options: [
      { value: 'every1', label: 'Every 1 year', tag: 'Heavy upgrader' },
      { value: 'every2', label: 'Every 2–3 years', tag: 'Average' },
      { value: 'every4', label: 'Every 4+ years', tag: 'Low impact' },
      { value: 'never', label: 'Until it dies', tag: 'Minimalist' },
    ],
  },
  {
    id: 'disposal',
    q: 'When a device dies, where does it usually go?',
    options: [
      { value: 'bin', label: 'General rubbish bin', tag: 'Highest risk' },
      { value: 'drawer', label: 'Sits in a drawer for years', tag: 'Latent risk' },
      { value: 'recycle', label: 'E-waste recycling drop-off', tag: 'Good' },
      { value: 'reuse', label: 'Sold, donated, or traded in', tag: 'Best' },
    ],
  },
  {
    id: 'battery',
    q: 'A swollen lithium battery — what would you do?',
    options: [
      { value: 'bin', label: 'Throw in the bin', tag: 'Fire risk' },
      { value: 'drawer', label: 'Leave in the drawer', tag: 'Risky' },
      { value: 'unknown', label: 'I genuinely don\'t know', tag: 'Most people' },
      { value: 'safe', label: 'Take to a battery drop-off', tag: 'Correct' },
    ],
  },
  {
    id: 'cables',
    q: 'Old chargers, cables, headphones — what happens to them?',
    options: [
      { value: 'bin', label: 'They go in the bin', tag: 'Common' },
      { value: 'box', label: 'In a "tech junk" box at home', tag: 'Likely' },
      { value: 'recycle', label: 'I drop them at e-waste sites', tag: 'Best' },
    ],
  },
  {
    id: 'aware',
    q: 'How concerned are you about e-waste health impact?',
    options: [
      { value: 'low', label: 'Honestly, not much', tag: 'Common' },
      { value: 'mid', label: 'A little', tag: 'Average' },
      { value: 'high', label: 'A lot', tag: 'Engaged' },
    ],
  },
]

const current = computed(() => questions[qIndex.value])
const progressPct = computed(() => ((qIndex.value + 1) / questions.length) * 100)

function start() { phase.value = 'quiz'; qIndex.value = 0 }
function answer(value) {
  answers[current.value.id] = value
  setTimeout(() => {
    if (qIndex.value < questions.length - 1) qIndex.value++
    else phase.value = 'insights'
  }, 280)
}
function back() { if (qIndex.value > 0) qIndex.value-- }
function restart() { phase.value = 'intro'; qIndex.value = 0; for (const k in answers) delete answers[k] }

// === Insights ===
const profile = computed(() => {
  const a = answers
  // Risk score: bin/drawer/unknown answers raise it
  let risk = 0
  if (a.replace === 'every1') risk += 2
  if (a.replace === 'every2') risk += 1
  if (a.disposal === 'bin') risk += 3
  if (a.disposal === 'drawer') risk += 2
  if (a.battery === 'bin') risk += 3
  if (a.battery === 'drawer' || a.battery === 'unknown') risk += 2
  if (a.cables === 'bin') risk += 2
  if (a.cables === 'box') risk += 1
  if (a.aware === 'low') risk += 1

  if (risk >= 8) return profileHigh
  if (risk >= 4) return profileMid
  return profileLow
})

const profileHigh = {
  title: 'your habits sit on the high-impact end.',
  summary:
    'You replace devices often and tend to bin them. That puts you in the group most exposed to battery-fire risk and most responsible for emissions tied to manufacturing new devices.',
  actions: [
    { title: 'Stop binning batteries today', text: 'A single swollen battery can ignite a waste truck. Drop them at any battery point — supermarkets, libraries, e-waste centres.', cta: 'Find a drop-off', to: '/disposal-locations' },
    { title: 'Run the repair check', text: 'Before replacing your next device, spend 30 seconds on the repair-or-replace tool. Most issues cost less to fix.', cta: 'Open repair tool', to: '/repair-check' },
    { title: 'Sell instead of binning', text: 'Working devices have value. Drop them at an EcoReviva pickup stall — no listing, no haggling.', cta: 'Find pickup', to: '/pickup-points' },
  ],
}
const profileMid = {
  title: 'your habits are average for Australia.',
  summary:
    'You\'re not the worst case, but old devices probably pile up in a drawer. That\'s where battery degradation and e-waste creep happen.',
  actions: [
    { title: 'Empty the tech-junk drawer', text: 'Set aside one Saturday. Any working device → pickup point. Anything dead → e-waste drop-off.', cta: 'Find drop-off', to: '/disposal-locations' },
    { title: 'Treat batteries differently', text: 'Cables in a regular bin is fine in some councils. Batteries — never. Always a battery point.', cta: 'See safety tips', to: '/disposal-locations' },
    { title: 'Try a longer phone cycle', text: 'Stretching from 2 years to 4 cuts your manufacturing emissions in half.', cta: 'AI optimizer', to: '/ai-chat' },
  ],
}
const profileLow = {
  title: 'you\'re already in the low-impact group.',
  summary:
    'Long device cycles and proper disposal mean you\'re not the problem. The risk is what your friends and family do — and that\'s where you can have the biggest knock-on impact.',
  actions: [
    { title: 'Share what you know', text: 'The sorting game is the easiest thing to send to a friend. Two minutes, no signup.', cta: 'Open the game', to: '/game' },
    { title: 'Take old devices off other hands', text: 'You already do the hard part. Offer to drop off other people\'s tech junk too — they often won\'t.', cta: 'Find a drop-off', to: '/disposal-locations' },
    { title: 'Push the repair tool', text: 'When friends ask "should I upgrade?" — send them the calculator instead of an opinion.', cta: 'Repair tool', to: '/repair-check' },
  ],
}

// KPI numbers (also varies slightly with profile)
const kpis = computed(() => {
  const high = profile.value.title.includes('high-impact')
  const low = profile.value.title.includes('low-impact')
  return [
    {
      label: 'Likely exposure',
      value: high ? 'High' : low ? 'Low' : 'Medium',
      unit: '',
      note: 'How directly your habits expose people around you to e-waste pollutants.',
    },
    {
      label: 'Strongest signal',
      value: '0.94',
      unit: '',
      note: 'Spearman correlation between water emissions and years of life lost (state-year data).',
    },
    {
      label: 'Battery fires per year',
      value: '12',
      unit: 'K+',
      note: 'In Australian waste trucks. Most are caused by binned lithium batteries.',
    },
  ]
})

const chain = [
  { t: 'E-waste generation', d: 'Old phones, laptops, batteries, cables — discarded faster than they\'re recycled.' },
  { t: 'Pollutants released', d: 'Heavy metals leach into water. PM2.5 from informal burning enters air.' },
  { t: 'Health burden', d: 'Premature deaths and years of life lost — measurable per Australian state.' },
]

// Pulled from /api/health/all with a baked-in fallback
const findings = ref([
  { metric: 'Years of Life Lost', signal: 'Total Water Emission', spearman: 0.94 },
  { metric: 'Avoidable Deaths', signal: 'Total Water Emission', spearman: 0.93 },
  { metric: 'Premature Deaths', signal: 'Total Water Emission', spearman: 0.93 },
  { metric: 'Deaths', signal: 'Total Water Emission', spearman: 0.90 },
  { metric: 'Crude Rate', signal: 'Zinc Water', spearman: 0.82 },
])

onMounted(async () => {
  try {
    const data = await api.getHealthAll()
    if (Array.isArray(data?.findings) && data.findings.length) {
      findings.value = data.findings.map((f) => ({
        metric: f.metric, signal: f.signal, spearman: f.spearman,
      }))
    }
  } catch (e) { /* keep fallback */ }
})
</script>

<style scoped>
.dash { padding-top: 120px; padding-bottom: 80px; min-height: 100vh; }
.phase { padding: 40px 0; }

/* INTRO */
.intro-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 60px;
  align-items: center;
  min-height: 70vh;
}
.intro-text { display: flex; flex-direction: column; gap: 28px; }
.intro-text h1 { color: var(--ink-0); }
.intro-text h1 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.intro-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; }
.intro-meta { display: flex; flex-direction: column; gap: 18px; }
.meta-card {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  padding: 24px;
  display: flex; flex-direction: column; gap: 12px;
}
.meta-card ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.meta-card ul li {
  position: relative;
  padding-left: 22px;
  color: var(--ink-1);
  font-size: 14px;
}
.meta-card ul li::before {
  content: ''; position: absolute; left: 0; top: 8px;
  width: 8px; height: 8px;
  background: var(--mint);
  border-radius: 50%;
}
.meta-card strong {
  font-family: var(--font-display);
  font-size: 32px;
  letter-spacing: -0.02em;
  color: var(--mint);
}

/* QUIZ */
.quiz-shell { max-width: 900px; }
.quiz-head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 20px;
  align-items: center;
  margin-bottom: 60px;
}
.progress {
  height: 2px;
  background: var(--hairline);
  border-radius: 999px;
  overflow: hidden;
}
.progress .bar {
  height: 100%;
  background: linear-gradient(90deg, var(--mint), var(--mint-bright));
  transition: width 0.5s var(--ease-out);
}
.back {
  background: transparent;
  border: 0;
  color: var(--ink-2);
  font-size: 13px;
  cursor: pointer;
}
.back:disabled { opacity: 0.3; cursor: not-allowed; }
.back:not(:disabled):hover { color: var(--mint); }

.qcard { display: flex; flex-direction: column; gap: 28px; }
.qprompt {
  font-family: var(--font-display);
  font-size: clamp(32px, 5vw, 56px);
  line-height: 1.1;
  letter-spacing: -0.03em;
  font-weight: 500;
  color: var(--ink-0);
}
.qhelp { color: var(--ink-2); font-size: 14px; max-width: 60ch; }
.opts { display: grid; gap: 10px; grid-template-columns: 1fr 1fr; }
.opt {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: 14px;
  align-items: center;
  padding: 22px 24px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  text-align: left;
  color: var(--ink-0);
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
}
.opt:hover { border-color: var(--mint); background: rgba(125, 216, 176, 0.05); transform: translateY(-2px); }
.opt.on { border-color: var(--mint); background: rgba(125, 216, 176, 0.12); }
.opt-mark {
  width: 28px; height: 28px;
  border-radius: 50%;
  border: 1.5px solid var(--hairline-strong);
  display: grid; place-items: center;
  color: var(--ink-on-light);
  background: transparent;
  transition: all 0.2s var(--ease-out);
}
.opt.on .opt-mark {
  background: var(--mint);
  border-color: var(--mint);
}
.opt-text { display: flex; flex-direction: column; gap: 4px; }
.opt-text strong { font-family: var(--font-display); font-weight: 500; font-size: 17px; }
.opt-text em { font-style: normal; color: var(--ink-2); font-size: 12px; font-family: var(--font-mono); letter-spacing: 0.06em; text-transform: uppercase; }

/* INSIGHTS */
.ins-head {
  display: flex; flex-direction: column; gap: 18px;
  max-width: 900px;
  margin-bottom: 80px;
}
.ins-head h2 { color: var(--ink-0); }
.ins-head h2 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.ins-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; }

.kpi-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;
  margin-bottom: 60px;
}
.kpi {
  display: flex; flex-direction: column; gap: 12px;
  padding: 32px 28px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  transition: border-color 0.3s, transform 0.3s var(--ease-out);
}
.kpi:hover { border-color: var(--mint); transform: translateY(-4px); }
.kpi-num {
  font-family: var(--font-display);
  font-size: clamp(48px, 6vw, 80px);
  font-weight: 500;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--mint);
}
.kpi-num span { font-size: 0.5em; color: var(--ink-2); margin-left: 4px; }
.kpi p { font-size: 14px; color: var(--ink-1); }

/* CHAIN */
.chain {
  padding: 40px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  margin-bottom: 60px;
  display: flex; flex-direction: column; gap: 24px;
}
.chain h3 {
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 36px);
  font-weight: 500;
  letter-spacing: -0.02em;
}
.chain-flow {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  position: relative;
}
.chain-node {
  position: relative;
  padding: 20px 24px 20px 0;
  display: flex; flex-direction: column; gap: 6px;
}
.ch-dot {
  width: 12px; height: 12px;
  background: var(--mint);
  border-radius: 50%;
  margin-bottom: 8px;
  box-shadow: 0 0 0 4px rgba(125, 216, 176, 0.16);
}
.chain-node strong { font-family: var(--font-display); font-size: 18px; font-weight: 500; }
.chain-node p { color: var(--ink-2); font-size: 14px; }
.chain-line {
  position: absolute;
  top: 26px; left: 14px; right: 0; height: 1px;
  background: linear-gradient(90deg, var(--mint), transparent);
}

/* SIGNALS */
.signals {
  padding: 40px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  margin-bottom: 60px;
  display: flex; flex-direction: column; gap: 24px;
}
.signals-head h3 {
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 36px);
  font-weight: 500;
  letter-spacing: -0.02em;
  margin-top: 8px;
}
.signal-list { display: flex; flex-direction: column; gap: 18px; }
.signal {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 28px;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--hairline);
}
.signal:last-child { border-bottom: 0; }
.sig-meta strong { display: block; font-family: var(--font-display); font-size: 18px; font-weight: 500; margin-bottom: 4px; }
.sig-meta span { color: var(--ink-2); font-size: 13px; }
.sig-bar {
  position: relative;
  height: 10px;
  background: var(--hairline);
  border-radius: 999px;
  overflow: visible;
}
.sig-bar .bar {
  height: 100%;
  background: linear-gradient(90deg, var(--mint), var(--mint-bright));
  border-radius: 999px;
  position: relative;
}
.bar-val {
  position: absolute;
  right: 0;
  top: -22px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--mint);
}
.sig-foot { color: var(--ink-2); font-size: 13px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }

/* ACTIONS */
.actions-card {
  padding: 40px;
  background: linear-gradient(135deg, rgba(125, 216, 176, 0.08), transparent);
  border: 1px solid rgba(125, 216, 176, 0.25);
  border-radius: var(--r-lg);
  display: flex; flex-direction: column; gap: 24px;
}
.actions-card h3 {
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 36px);
  font-weight: 500;
  letter-spacing: -0.02em;
  margin-top: 8px;
}
.action-list { display: flex; flex-direction: column; gap: 0; }
.action {
  display: grid;
  grid-template-columns: 60px 1fr auto;
  gap: 18px;
  align-items: center;
  padding: 22px 0;
  border-top: 1px solid var(--hairline);
}
.action:last-child { border-bottom: 1px solid var(--hairline); }
.action .a-num { font-family: var(--font-mono); font-size: 12px; color: var(--mint); letter-spacing: 0.18em; }
.action strong { display: block; font-family: var(--font-display); font-size: 18px; font-weight: 500; margin-bottom: 4px; }
.action p { color: var(--ink-2); font-size: 14px; max-width: 60ch; }
.a-link { color: var(--mint); font-size: 13px; font-weight: 500; white-space: nowrap; }
.a-link:hover { color: var(--mint-bright); }

/* TRANSITIONS */
.fade-up-enter-active, .fade-up-leave-active {
  transition: opacity 0.5s var(--ease-out), transform 0.5s var(--ease-out);
}
.fade-up-enter-from { opacity: 0; transform: translateY(16px); }
.fade-up-leave-to { opacity: 0; transform: translateY(-16px); }
.slide-enter-active, .slide-leave-active {
  transition: opacity 0.45s var(--ease-out), transform 0.45s var(--ease-out);
}
.slide-enter-from { opacity: 0; transform: translateX(40px); }
.slide-leave-to { opacity: 0; transform: translateX(-40px); }

@media (max-width: 880px) {
  .intro-grid { grid-template-columns: 1fr; gap: 40px; }
  .opts { grid-template-columns: 1fr; }
  .quiz-head { grid-template-columns: 1fr; gap: 12px; }
  .kpi-grid { grid-template-columns: 1fr; }
  .chain-flow { grid-template-columns: 1fr; }
  .chain-line { display: none; }
  .signal { grid-template-columns: 1fr; gap: 8px; }
  .action { grid-template-columns: 40px 1fr; gap: 12px; }
  .a-link { grid-column: 2; }
  .chain, .signals, .actions-card { padding: 24px; }
}
</style>
