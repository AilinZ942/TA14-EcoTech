<template>
  <div class="game">
    <div class="eco-shell">
      <transition name="fade" mode="out-in">
        <!-- COVER -->
        <section v-if="!started && !finished" key="cover" class="cover">
          <span class="eco-eyebrow">Sorting Game · Iteration 03</span>
          <h1 class="eco-display">
            Where does this<br /><em>e-waste</em> go?
          </h1>
          <p class="eco-lead">
            Drag or tap each item into the right bin. Score points, learn the rules,
            avoid the bin that ruins recycling for everyone.
          </p>

          <div class="bin-preview">
            <div v-for="b in bins" :key="b.name" class="bin-mini">
              <span>{{ b.icon }}</span>
              <strong>{{ b.name }}</strong>
            </div>
          </div>

          <div class="cover-actions">
            <button class="eco-btn eco-btn--mint" @click="startGame">
              Start the round <span class="arrow">→</span>
            </button>
            <span class="eco-mono">10 items · 2 minutes · first try counts</span>
          </div>
        </section>

        <!-- BOARD -->
        <section v-else-if="started && !finished" key="board" class="board">
          <header class="hud">
            <div class="hud-left">
              <span class="eco-mono">Score</span>
              <strong class="hud-score">{{ score }}</strong>
            </div>
            <div class="hud-progress">
              <div class="bar-wrap">
                <div class="bar" :style="{ width: progressPct + '%' }" />
              </div>
              <span>{{ sortedCount }} / {{ totalItems }} sorted</span>
            </div>
            <button class="eco-btn eco-btn--ghost" @click="restart">Reset</button>
          </header>

          <section class="items">
            <button
              v-for="item in unsortedItems"
              :key="item.id"
              class="item"
              :class="{ active: selectedItem?.id === item.id }"
              draggable="true"
              @click="selectItem(item)"
              @dragstart="dragStart(item, $event)"
            >
              <span class="emoji">{{ item.icon }}</span>
              <span class="name">{{ item.name }}</span>
            </button>
          </section>

          <p class="prompt">{{ promptText }}</p>

          <section class="bins">
            <div
              v-for="bin in bins"
              :key="bin.name"
              class="bin"
              :class="[{ ok: feedbackBin === bin.name && feedbackType === 'ok',
                         bad: feedbackBin === bin.name && feedbackType === 'bad' }]"
              @click="placeItem(bin.name)"
              @dragover.prevent
              @drop.prevent="dropItem(bin.name)"
            >
              <header>
                <span class="bin-ic">{{ bin.icon }}</span>
                <strong>{{ bin.name }}</strong>
                <span class="count">{{ sortedItems[bin.name].length }}</span>
              </header>
              <div class="bin-items">
                <span
                  v-for="it in sortedItems[bin.name]"
                  :key="it.id"
                  class="chip"
                  @click.stop="returnItem(it, bin.name)"
                >
                  {{ it.icon }} {{ it.name }}
                </span>
              </div>
            </div>
          </section>

          <transition name="fade">
            <div v-if="lastTip" class="toast" :class="lastWasCorrect ? 'good' : 'bad'">
              <strong>{{ lastWasCorrect ? '✓ Correct' : '✗ Not quite' }}</strong>
              <span>{{ lastTip }}</span>
            </div>
          </transition>

          <div class="actions">
            <button v-if="unsortedItems.length === 0" class="eco-btn eco-btn--mint" @click="finish">
              View result <span class="arrow">→</span>
            </button>
            <button v-else class="eco-btn eco-btn--ghost" @click="finish">View result early</button>
          </div>
        </section>

        <!-- RESULT -->
        <section v-else key="result" class="result">
          <div class="ring" :style="{ '--p': pct }">
            <div class="ring-inner">
              <span class="ring-num">{{ score }}</span>
              <span class="ring-cap">/ {{ totalItems }}</span>
            </div>
          </div>
          <h2 class="eco-h2">{{ resultHeadline }}</h2>
          <p class="eco-lead">{{ resultText }}</p>
          <div class="actions">
            <button class="eco-btn eco-btn--mint" @click="restart">
              Play again <span class="arrow">→</span>
            </button>
            <router-link to="/disposal-locations" class="eco-btn eco-btn--ghost">
              Find a real bin
            </router-link>
          </div>
        </section>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const bins = [
  { name: 'Reuse / Donate', icon: '♻' },
  { name: 'E-waste recycling', icon: '⌧' },
  { name: 'Hazardous drop-off', icon: '⚠' },
  { name: 'Household bin', icon: '✕' },
]

const itemsPool = [
  { id: 1, name: 'Old smartphone (works)', icon: '📱', correct: 'Reuse / Donate', tip: 'Working phones can be donated, sold, or traded in.' },
  { id: 2, name: 'Swollen lithium battery', icon: '🔋', correct: 'Hazardous drop-off', tip: 'Take swollen batteries to a battery-safe drop-off — never the bin.' },
  { id: 3, name: 'Working laptop', icon: '💻', correct: 'Reuse / Donate', tip: 'Wipe the data, then donate to schools, charities, or pickup points.' },
  { id: 4, name: 'Broken charger cable', icon: '🔌', correct: 'E-waste recycling', tip: 'Cables contain copper. Drop them at any e-waste collection point.' },
  { id: 5, name: 'Wired headphones', icon: '🎧', correct: 'E-waste recycling', tip: 'Small electronics → e-waste recycling, never kerbside.' },
  { id: 6, name: 'Empty pizza box', icon: '🍕', correct: 'Household bin', tip: 'Greasy paper goes to general waste in most council areas.' },
  { id: 7, name: 'Cracked screen tablet', icon: '📲', correct: 'E-waste recycling', tip: 'Even broken tablets are valuable — recyclers recover the metals.' },
  { id: 8, name: 'Toner cartridge', icon: '🖨', correct: 'E-waste recycling', tip: 'Most office stores accept toners back for recycling.' },
  { id: 9, name: 'Light bulb (LED)', icon: '💡', correct: 'Hazardous drop-off', tip: 'LEDs and CFLs contain trace metals — drop at hazardous waste.' },
  { id: 10, name: 'Banana peel', icon: '🍌', correct: 'Household bin', tip: 'Compost if you can; otherwise general waste. Not a recyclable.' },
]

const started = ref(false)
const finished = ref(false)
const items = ref([])
const sortedItems = ref({})
const selectedItem = ref(null)
const score = ref(0)
const feedbackBin = ref('')
const feedbackType = ref('')
const lastTip = ref('')
const lastWasCorrect = ref(false)
const attempted = ref(new Set())

const totalItems = computed(() => items.value.length + sortedCount.value)
const sortedCount = computed(() => Object.values(sortedItems.value).reduce((a, b) => a + b.length, 0))
const unsortedItems = computed(() => items.value)
const progressPct = computed(() => totalItems.value ? (sortedCount.value / totalItems.value) * 100 : 0)
const pct = computed(() => totalItems.value ? Math.round((score.value / totalItems.value) * 100) : 0)
const promptText = computed(() => selectedItem.value ? `Selected: ${selectedItem.value.name} → tap a bin to place it` : 'Tap an item, then tap a bin. Or drag it across.')

function startGame() {
  items.value = [...itemsPool].sort(() => Math.random() - 0.5)
  sortedItems.value = bins.reduce((acc, b) => { acc[b.name] = []; return acc }, {})
  score.value = 0
  attempted.value = new Set()
  selectedItem.value = null
  finished.value = false
  started.value = true
}

function restart() { startGame() }
function selectItem(it) { selectedItem.value = selectedItem.value?.id === it.id ? null : it }
function dragStart(it, ev) { selectedItem.value = it; ev.dataTransfer.setData('text/plain', String(it.id)) }
function dropItem(binName) { if (selectedItem.value) placeItem(binName) }

function placeItem(binName) {
  const it = selectedItem.value
  if (!it) return
  const correct = it.correct === binName
  const counts = !attempted.value.has(it.id)
  if (counts) {
    attempted.value.add(it.id)
    if (correct) score.value += 1
  }
  sortedItems.value[binName].push(it)
  items.value = items.value.filter(x => x.id !== it.id)
  feedbackBin.value = binName
  feedbackType.value = correct ? 'ok' : 'bad'
  lastWasCorrect.value = correct
  lastTip.value = correct ? `Right — ${it.tip}` : `${it.correct} would be safer. ${it.tip}`
  selectedItem.value = null
  setTimeout(() => { feedbackBin.value = ''; feedbackType.value = '' }, 700)
  setTimeout(() => { lastTip.value = '' }, 3500)
}

function returnItem(it, binName) {
  sortedItems.value[binName] = sortedItems.value[binName].filter(x => x.id !== it.id)
  items.value = [...items.value, it]
}

function finish() { finished.value = true }

const resultHeadline = computed(() => {
  if (pct.value >= 80) return 'You\'re an e-waste pro.'
  if (pct.value >= 50) return 'Solid run. A few tricky ones.'
  return 'Round one done. Try again.'
})
const resultText = computed(() => {
  if (pct.value >= 80) return 'Share what you learned. Most people get the swollen battery wrong.'
  if (pct.value >= 50) return 'Visit the dashboard to see why these categories matter.'
  return 'Open the disposal map — each location lists exactly what it accepts.'
})
</script>

<style scoped>
.game { padding-top: 140px; padding-bottom: 80px; min-height: 100vh; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.4s var(--ease-out), transform 0.4s var(--ease-out); }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(10px); }

/* COVER */
.cover {
  display: flex; flex-direction: column; align-items: center; gap: 24px;
  text-align: center;
  max-width: 800px;
  margin: 60px auto 0;
}
.cover h1 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

.bin-preview {
  display: flex; flex-wrap: wrap; gap: 10px;
  justify-content: center;
  margin: 16px 0 8px;
}
.bin-mini {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-pill);
  font-size: 13px;
  color: var(--ink-1);
}
.bin-mini span { color: var(--mint); font-size: 16px; }
.bin-mini strong { font-weight: 500; }

.cover-actions { display: flex; flex-wrap: wrap; gap: 18px; align-items: center; justify-content: center; }

/* BOARD */
.board { display: flex; flex-direction: column; gap: 28px; }
.hud {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 24px;
  align-items: center;
  padding: 18px 22px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
}
.hud-left { display: flex; flex-direction: column; }
.hud-score {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 500;
  color: var(--mint);
  letter-spacing: -0.02em;
  line-height: 1;
}
.hud-progress { display: flex; flex-direction: column; gap: 8px; }
.bar-wrap { height: 4px; background: var(--hairline); border-radius: 999px; overflow: hidden; }
.bar { height: 100%; background: linear-gradient(90deg, var(--mint), var(--mint-bright)); transition: width 0.5s var(--ease-out); }
.hud-progress span { font-family: var(--font-mono); font-size: 11px; color: var(--ink-2); letter-spacing: 0.12em; }

.items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}
.item {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 18px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  cursor: grab;
  color: var(--ink-0);
  transition: all 0.25s var(--ease-out);
}
.item:hover { background: rgba(125,216,176,0.08); border-color: var(--mint); transform: translateY(-3px); }
.item.active { background: rgba(125,216,176,0.16); border-color: var(--mint); box-shadow: 0 0 30px rgba(125,216,176,0.3); }
.emoji { font-size: 30px; }
.name { font-size: 12px; text-align: center; color: var(--ink-1); }

.prompt { color: var(--ink-2); text-align: center; font-size: 14px; }

.bins { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.bin {
  min-height: 200px;
  padding: 18px;
  background: var(--surface);
  border: 1.5px dashed var(--hairline-strong);
  border-radius: var(--r-md);
  cursor: pointer;
  display: flex; flex-direction: column; gap: 12px;
  transition: all 0.25s var(--ease-out);
}
.bin:hover { background: rgba(125,216,176,0.06); border-color: var(--mint); }
.bin.ok { background: rgba(125,216,176,0.18); border-color: var(--mint); animation: ping 0.5s var(--ease-out); }
.bin.bad { background: rgba(248, 113, 113, 0.18); border-color: var(--bad); animation: shake 0.4s var(--ease-out); }
@keyframes ping { 0% { transform: scale(1); } 50% { transform: scale(1.04); } 100% { transform: scale(1); } }
@keyframes shake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-4px); } 75% { transform: translateX(4px); } }

.bin header { display: flex; align-items: center; gap: 10px; }
.bin .bin-ic { font-size: 20px; color: var(--mint); }
.bin strong { font-family: var(--font-display); font-size: 13px; flex: 1; font-weight: 500; }
.bin .count {
  background: rgba(125,216,176,0.16);
  border: 1px solid rgba(125,216,176,0.3);
  border-radius: var(--r-pill);
  padding: 2px 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--mint);
}
.bin-items { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-size: 11px;
  padding: 5px 10px;
  border-radius: var(--r-sm);
  background: rgba(0,0,0,0.25);
  color: var(--ink-1);
  cursor: pointer;
}

.toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  padding: 14px 20px;
  display: flex; align-items: center; gap: 12px;
  font-size: 13px;
  border-radius: var(--r-md);
  max-width: min(540px, calc(100% - 32px));
  background: rgba(6, 18, 15, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid;
}
.toast.good { border-color: var(--mint); }
.toast.bad { border-color: var(--bad); }
.toast.good strong { color: var(--mint); }
.toast.bad strong { color: var(--bad); }

.actions { display: flex; gap: 12px; flex-wrap: wrap; justify-content: flex-end; }

/* RESULT */
.result {
  text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 18px;
  max-width: 600px;
  margin: 60px auto 0;
}
.ring {
  width: 200px; height: 200px;
  border-radius: 50%;
  background: conic-gradient(var(--mint) calc(var(--p) * 1%), var(--hairline) 0);
  display: grid; place-items: center;
  position: relative;
}
.ring::before { content: ''; position: absolute; inset: 14px; border-radius: 50%; background: var(--bg-1); }
.ring-inner { position: relative; display: flex; flex-direction: column; }
.ring-num { font-family: var(--font-display); font-size: 56px; font-weight: 500; color: var(--mint); letter-spacing: -0.04em; line-height: 1; }
.ring-cap { font-family: var(--font-mono); font-size: 11px; color: var(--ink-2); letter-spacing: 0.18em; }

@media (max-width: 880px) { .bins { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) {
  .bins { grid-template-columns: 1fr; }
  .hud { grid-template-columns: 1fr; gap: 14px; }
  .actions { justify-content: stretch; }
}
</style>
