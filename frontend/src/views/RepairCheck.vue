<template>
  <div class="rc">
    <div class="eco-shell">
      <header class="head">
        <span class="eco-eyebrow">Repair · Replace · Reuse · Recycle</span>
        <h1 class="eco-display">
          Repair or replace?<br /><em>Decide in 30 seconds.</em>
        </h1>
        <p class="eco-lead">
          Tell us about the device. We'll do the math on cost, age, and condition — and tell you what makes the most sense.
        </p>
      </header>

      <div class="grid">
        <!-- FORM -->
        <section class="form">
          <span class="eco-mono">Your device</span>
          <h2>Inputs</h2>

          <label class="field">
            <span>Device type</span>
            <div class="seg">
              <button v-for="d in devices" :key="d.id" :class="{ on: form.device === d.id }" @click="form.device = d.id">
                {{ d.icon }} {{ d.label }}
              </button>
            </div>
          </label>

          <div class="row">
            <label class="field">
              <span>Age (years)</span>
              <input type="number" v-model.number="form.age" min="0" max="20" step="1" />
            </label>
            <label class="field">
              <span>Original price ($)</span>
              <input type="number" v-model.number="form.original" min="0" step="50" />
            </label>
          </div>

          <div class="row">
            <label class="field">
              <span>Repair quote ($)</span>
              <input type="number" v-model.number="form.repair" min="0" step="10" />
            </label>
            <label class="field">
              <span>Replacement cost ($)</span>
              <input type="number" v-model.number="form.replace" min="0" step="50" />
            </label>
          </div>

          <label class="field">
            <span>Condition</span>
            <div class="seg">
              <button v-for="c in conditions" :key="c.id" :class="{ on: form.condition === c.id }" @click="form.condition = c.id">
                {{ c.label }}
              </button>
            </div>
          </label>

          <label class="field">
            <span>What's wrong? (optional)</span>
            <textarea v-model="form.note" rows="2" placeholder="cracked screen, swollen battery, won't charge…"></textarea>
          </label>
        </section>

        <!-- RESULT -->
        <section class="result">
          <article class="verdict" :class="`tone-${verdict.tone}`">
            <span class="v-icon">{{ verdict.icon }}</span>
            <span class="eco-eyebrow">Recommendation</span>
            <h2>{{ verdict.title }}</h2>
            <p>{{ verdict.text }}</p>
            <router-link :to="verdict.cta.to" class="eco-btn eco-btn--mint">
              {{ verdict.cta.label }} <span class="arrow">→</span>
            </router-link>
          </article>

          <article class="compare">
            <h3>Cost comparison</h3>
            <div class="bar-row">
              <span class="bar-label">Repair</span>
              <div class="bar-track"><div class="bar repair" :style="{ width: barRepairPct + '%' }" /></div>
              <strong>${{ form.repair || 0 }}</strong>
            </div>
            <div class="bar-row">
              <span class="bar-label">Replace</span>
              <div class="bar-track"><div class="bar replace" :style="{ width: barReplacePct + '%' }" /></div>
              <strong>${{ form.replace || 0 }}</strong>
            </div>
            <div class="ratio">
              Repair is <strong :class="repairRatio < 50 ? 'good' : 'bad'">{{ repairRatio }}%</strong> of replacement cost.
            </div>
          </article>

          <article class="why">
            <h3>Why this recommendation?</h3>
            <ul>
              <li v-for="r in verdict.reasons" :key="r">{{ r }}</li>
            </ul>
          </article>
        </section>
      </div>

      <section class="paths">
        <article v-for="p in fourPaths" :key="p.label" class="path">
          <span class="p-icon">{{ p.icon }}</span>
          <h4>{{ p.label }}</h4>
          <p>{{ p.text }}</p>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'

const devices = [
  { id: 'phone', label: 'Phone', icon: '📱' },
  { id: 'laptop', label: 'Laptop', icon: '💻' },
  { id: 'tablet', label: 'Tablet', icon: '📲' },
]
const conditions = [
  { id: 'minor', label: 'Minor issue' },
  { id: 'moderate', label: 'Moderate' },
  { id: 'major', label: 'Major fault' },
]

const form = reactive({
  device: 'laptop', age: 3, original: 1500, repair: 250, replace: 1400, condition: 'moderate', note: '',
})

const repairRatio = computed(() => {
  if (!form.replace) return 0
  return Math.min(999, Math.round((form.repair / form.replace) * 100))
})

const fourPaths = [
  { label: 'Repair', icon: '🛠', text: 'Cheaper than replacement and avoids new manufacturing.' },
  { label: 'Reuse', icon: '♻', text: 'Working but unused devices belong in someone else\'s hands.' },
  { label: 'Recycle', icon: '⌧', text: 'When materials matter more than the device, recycle responsibly.' },
  { label: 'Donate', icon: '🎁', text: 'Schools, charities, and pickup points need working devices.' },
]

const verdict = computed(() => {
  const ratio = repairRatio.value
  const tooOld = form.age >= (form.device === 'phone' ? 5 : 7)
  const major = form.condition === 'major'

  if (form.condition === 'minor' || (ratio < 40 && !tooOld)) {
    return { tone: 'mint', icon: '🛠', title: 'Repair it.',
      text: `Repair is only ${ratio}% of replacement cost — clearly the better deal financially and environmentally.`,
      reasons: [
        `Repair quote ($${form.repair}) is well below the 50% threshold.`,
        `Device age (${form.age} years) is reasonable for a typical lifespan.`,
        'Repairing extends life and avoids new-manufacturing emissions.',
      ],
      cta: { to: '/disposal-locations', label: 'Find a repair / drop-off' },
    }
  }
  if (ratio >= 40 && ratio < 70 && !tooOld && !major) {
    return { tone: 'mint', icon: '🛠', title: 'Worth repairing.',
      text: `At ${ratio}% of replacement, repair still makes sense — especially if you can use the device for another year or two.`,
      reasons: [
        'Repair cost is below the typical 70% break-even point.',
        'Avoiding a new device avoids manufacturing impact.',
        'Set a reminder to re-evaluate if it breaks again.',
      ],
      cta: { to: '/ai-chat', label: 'Get optimisation tips' },
    }
  }
  if (form.condition === 'minor' && tooOld) {
    return { tone: 'cool', icon: '♻', title: 'Reuse or donate it.',
      text: 'It still works, but it\'s past its peak. Pass it on before recycling.',
      reasons: [
        `Age (${form.age} years) is at the upper end of practical life.`,
        'Working devices have value to schools, charities, or buyers.',
        'Wipe your data first using the device\'s factory reset.',
      ],
      cta: { to: '/pickup-points', label: 'Find pickup point' },
    }
  }
  if (major && ratio >= 70) {
    return { tone: 'warm', icon: '⌧', title: 'Recycle it safely.',
      text: `Repair would cost ${ratio}% of replacement and the fault is major. Drop it at a certified e-waste site.`,
      reasons: [
        `Repair-to-replace ratio (${ratio}%) exceeds the 70% threshold.`,
        'Major faults often signal more failures soon after.',
        'Recyclers recover gold, copper, and rare metals from the device.',
      ],
      cta: { to: '/disposal-locations', label: 'Find e-waste drop-off' },
    }
  }
  return { tone: 'warm', icon: '🔁', title: 'Replace — but reuse the old one.',
    text: `At ${ratio}% repair-to-replace, replacing wins financially. Donate or sell the old device — don\'t bin it.`,
    reasons: [
      `Repair-to-replace ratio is ${ratio}%.`,
      'Replacement may have better warranty and efficiency.',
      'Pass the old device on through pickup points before recycling.',
    ],
    cta: { to: '/pickup-points', label: 'Find pickup point' },
  }
})

const max = computed(() => Math.max(form.repair || 0, form.replace || 0) || 1)
const barRepairPct = computed(() => Math.min(100, ((form.repair || 0) / max.value) * 100))
const barReplacePct = computed(() => Math.min(100, ((form.replace || 0) / max.value) * 100))
</script>

<style scoped>
.rc { padding-top: 140px; padding-bottom: 80px; min-height: 100vh; }

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

.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }

.form {
  padding: 32px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  display: flex; flex-direction: column; gap: 18px;
}
.form h2 { font-family: var(--font-display); font-size: 24px; font-weight: 500; margin-bottom: 4px; }

.row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field > span {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--ink-2);
  text-transform: uppercase;
}
.field input, .field textarea {
  padding: 12px 14px;
  background: rgba(0,0,0,0.25);
  border: 1px solid var(--hairline);
  border-radius: var(--r-sm);
  color: var(--ink-0);
  font-family: var(--font-body);
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.field input:focus, .field textarea:focus { border-color: var(--mint); box-shadow: 0 0 0 4px rgba(125,216,176,0.12); }

.seg { display: flex; gap: 6px; flex-wrap: wrap; }
.seg button {
  flex: 1;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-sm);
  color: var(--ink-1);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
}
.seg button:hover { border-color: var(--mint); color: var(--ink-0); }
.seg button.on { background: var(--mint); color: var(--ink-on-light); border-color: var(--mint); }

/* RESULT */
.result { display: flex; flex-direction: column; gap: 16px; }
.verdict {
  padding: 32px;
  background: linear-gradient(135deg, rgba(125,216,176,0.10), transparent);
  border: 1px solid rgba(125,216,176,0.3);
  border-radius: var(--r-lg);
  display: flex; flex-direction: column; gap: 12px;
}
.verdict.tone-cool { background: linear-gradient(135deg, rgba(56,189,248,0.1), transparent); border-color: rgba(56,189,248,0.3); }
.verdict.tone-warm { background: linear-gradient(135deg, rgba(244,162,97,0.12), transparent); border-color: rgba(244,162,97,0.3); }
.v-icon { font-size: 42px; }
.verdict h2 {
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 38px);
  font-weight: 500;
  letter-spacing: -0.02em;
  color: var(--ink-0);
}
.verdict p { color: var(--ink-1); line-height: 1.6; }
.verdict .eco-btn { align-self: flex-start; }

.compare {
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 12px;
}
.compare h3 { font-family: var(--font-display); font-size: 16px; font-weight: 500; }
.bar-row { display: grid; grid-template-columns: 80px 1fr 70px; align-items: center; gap: 12px; font-size: 13px; }
.bar-label { color: var(--ink-2); font-family: var(--font-mono); font-size: 11px; }
.bar-track { background: var(--hairline); border-radius: 999px; height: 8px; overflow: hidden; }
.bar { height: 100%; border-radius: 999px; transition: width 0.5s var(--ease-out); }
.bar.repair { background: linear-gradient(90deg, var(--mint), var(--mint-bright)); }
.bar.replace { background: linear-gradient(90deg, var(--violet), var(--rose)); }
.bar-row strong { font-family: var(--font-mono); text-align: right; color: var(--ink-0); }
.ratio { text-align: center; padding-top: 10px; border-top: 1px solid var(--hairline); color: var(--ink-2); font-size: 13px; }
.ratio strong { font-family: var(--font-display); margin: 0 4px; font-weight: 500; }
.ratio strong.good { color: var(--mint); }
.ratio strong.bad { color: var(--peach); }

.why {
  padding: 22px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 10px;
}
.why h3 { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--mint); }
.why ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.why li {
  padding-left: 22px;
  color: var(--ink-1);
  font-size: 13px;
  line-height: 1.6;
  position: relative;
}
.why li::before {
  content: '·'; position: absolute; left: 0; top: 0;
  color: var(--mint); font-size: 24px; line-height: 1;
}

/* PATHS */
.paths {
  margin-top: 60px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.path {
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  display: flex; flex-direction: column; gap: 10px;
  transition: all 0.3s var(--ease-out);
}
.path:hover { border-color: var(--mint); transform: translateY(-4px); }
.p-icon {
  font-size: 24px;
  width: 48px; height: 48px;
  display: grid; place-items: center;
  background: rgba(125,216,176,0.12);
  border: 1px solid rgba(125,216,176,0.25);
  border-radius: var(--r-sm);
  color: var(--mint);
}
.path h4 { font-family: var(--font-display); font-size: 16px; font-weight: 500; }
.path p { color: var(--ink-2); font-size: 13px; line-height: 1.6; }

@media (max-width: 1024px) {
  .grid { grid-template-columns: 1fr; }
  .paths { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .row { grid-template-columns: 1fr; }
  .paths { grid-template-columns: 1fr; }
  .form { padding: 24px; }
}
</style>
