<template>
  <div class="game-page">
    <!-- Cover -->
    <section v-if="!started && !finished" class="cover-card">
      <div class="cover-icon">♻️</div>
      <p class="eyebrow">EcoTech Game</p>
      <h1>E-waste Sorting Challenge</h1>

      <p class="cover-desc">
        Select an item and place it into the correct bin to test your recycling knowledge.
      </p>

      <p class="cover-hint">
        Click or drag items into the correct bins. Only your first attempt for each item counts.
      </p>

      <button class="primary-btn" @click="startGame">Start Game</button>
    </section>

    <!-- Game -->
    <section v-else-if="started && !finished" class="game-card">
      <div class="top-actions">
        <button class="back-btn" @click="goHome">← Back to Start</button>
      </div>

      <div class="top-bar">
        <span>{{ unsortedItems.length }} items remaining</span>
        <span>Score: {{ score }}</span>
      </div>

      <div class="items-grid">
        <button
          v-for="item in unsortedItems"
          :key="item.id"
          class="item-card"
          :class="{ selected: selectedItem?.id === item.id }"
          draggable="true"
          @click="selectItem(item)"
          @dragstart="dragStart(item)"
        >
          <div class="item-icon">{{ item.icon }}</div>
          <span>{{ item.name }}</span>
        </button>
      </div>

      <p class="hint">
        {{
          selectedItem
            ? 'Selected: ' + selectedItem.name + ' → click a bin to place it'
            : 'Click or drag an item into a bin. Click a sorted item to move it back.'
        }}
      </p>

      <div class="bins-grid">
        <div
          v-for="bin in bins"
          :key="bin.name"
          class="bin-box"
          :class="[
            bin.className,
            {
              correctFlash: feedbackBin === bin.name && feedbackType === 'correct',
              wrongFlash: feedbackBin === bin.name && feedbackType === 'wrong',
            },
          ]"
          @click="placeItem(bin.name)"
          @dragover.prevent
          @drop="dropItem(bin.name)"
        >
          <h3>{{ bin.icon }} {{ bin.name }}</h3>

          <div class="placed-items">
            <div
              v-for="item in sortedItems[bin.name]"
              :key="item.id"
              class="placed-card"
              @click.stop="returnItem(item, bin.name)"
            >
              <div class="placed-icon">{{ item.icon }}</div>
              <span>{{ item.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="game-actions">
        <button
          v-if="unsortedItems.length > 0"
          class="secondary-btn"
          @click="showEndConfirm = true"
        >
          View Result Early
        </button>

        <button v-if="unsortedItems.length === 0" class="primary-btn" @click="finishGame">
          View Result
        </button>
      </div>
    </section>

    <!-- Result -->
    <section v-else class="result-card">
      <div class="cover-icon">🎉</div>
      <p class="eyebrow">Sorting Result</p>

      <h1>{{ resultTitle }}</h1>

      <div class="final-score">{{ score }} / {{ items.length * 10 }}</div>

      <p class="cover-desc">
        You got {{ correctCount }} out of {{ items.length }} items correct on the first attempt.
      </p>

      <div class="result-summary">
        <p v-if="correctCount === items.length">
          Excellent! You sorted every item correctly on the first try.
        </p>
        <p v-else-if="correctCount >= 6">
          Good effort! You understand most e-waste sorting rules, but some items need extra
          attention.
        </p>
        <p v-else>
          Keep practising! Some electronic items need special disposal to reduce environmental
          impact.
        </p>
      </div>

      <div class="explanation-box">
        <h3>Sorting Guide</h3>
        <p>
          <strong>E-Waste:</strong> phones, chargers, keyboards, monitors and other electronic
          devices.
        </p>
        <p><strong>Battery Bin:</strong> loose batteries or removable device batteries.</p>
        <p>
          <strong>Repair / Reuse:</strong> working or repairable devices that can be reused before
          recycling.
        </p>
        <p>
          <strong>General Waste:</strong> non-electronic items that cannot be recycled through
          e-waste services.
        </p>
      </div>

      <div class="result-actions">
        <button class="primary-btn" @click="restartGame">Play Again</button>
        <button class="secondary-btn" @click="goHome">Back to Start</button>
      </div>
    </section>

    <!-- Early End Confirm Modal -->
    <div v-if="showEndConfirm" class="confirm-overlay">
      <div class="confirm-box">
        <h3>End the game early?</h3>
        <p>Your current score will be shown on the result page.</p>

        <div class="confirm-actions">
          <button class="secondary-btn" @click="showEndConfirm = false">Cancel</button>
          <button class="primary-btn" @click="finishGameEarly">End Game</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="showToast" class="toast" :class="toastType">
      {{ toastText }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const started = ref(false)
const finished = ref(false)
const selectedItem = ref(null)
const draggedItem = ref(null)
const showEndConfirm = ref(false)

const score = ref(0)
const feedbackBin = ref('')
const feedbackType = ref('')

const showToast = ref(false)
const toastText = ref('')
const toastType = ref('')

const bins = [
  { name: 'E-Waste', icon: '⚡', className: 'ewaste-bin' },
  { name: 'Battery Bin', icon: '🔋', className: 'battery-bin' },
  { name: 'Repair / Reuse', icon: '🛠️', className: 'reuse-bin' },
  { name: 'General Waste', icon: '🗑️', className: 'general-bin' },
]

const initialItems = [
  {
    id: 1,
    name: 'Old Phone',
    icon: '📱',
    answer: 'E-Waste',
    okMsg:
      'Correct! Old phones contain gold, copper and toxic heavy metals — e-waste recycling recovers them safely.',
    errMsg: {
      battery:
        "The phone has a battery inside, but don't dismantle it yourself. The whole device goes to E-Waste.",
      repair:
        "This phone is old and no longer functional — it's not worth refurbishing. It belongs in E-Waste.",
      general:
        'Never throw phones in general waste. They contain toxic metals that leach into soil and groundwater.',
    },
  },
  {
    id: 2,
    name: 'Loose Battery',
    icon: '🔋',
    answer: 'Battery Bin',
    okMsg:
      'Correct! Any loose battery — regardless of size — must go to a dedicated Battery Bin to prevent toxic leakage.',
    errMsg: {
      ewaste:
        'Loose batteries need their own separate bin — dropping them in with e-waste creates a fire and leakage risk.',
      repair:
        "A loose battery can't be reused on its own safely. It must go to the Battery Bin for proper disposal.",
      general:
        'Never put loose batteries in general waste — they can rupture, leak acid and contaminate the entire landfill.',
    },
  },
  {
    id: 3,
    name: 'Working Tablet',
    icon: '📲',
    answer: 'Repair / Reuse',
    okMsg:
      'Excellent! A working tablet can be donated or refurbished — keeping it in use is far better than recycling it.',
    errMsg: {
      ewaste:
        "Don't recycle a working device! This tablet still functions — donate or refurbish it instead.",
      battery:
        "The tablet's battery is inside the device. Since it still works, the whole unit goes to Repair / Reuse.",
      general:
        'A working tablet is valuable electronics — putting it in general waste is wasteful and potentially illegal.',
    },
  },
  {
    id: 4,
    name: 'Broken Charger',
    icon: '🔌',
    answer: 'E-Waste',
    okMsg:
      'Right! Chargers contain copper wiring and electronic components — they need specialist e-waste recycling.',
    errMsg: {
      battery:
        "A charger isn't a battery — it contains copper wiring and circuit components that go to E-Waste.",
      repair:
        "A broken charger is a fire hazard — it's not safe to repair at home. Send it to E-Waste.",
      general:
        "Chargers contain copper and mixed plastics that can be recovered — they're e-waste, not general waste.",
    },
  },
  {
    id: 5,
    name: 'Old Laptop',
    icon: '💻',
    answer: 'E-Waste',
    okMsg:
      'Spot on! Old laptops contain lead, mercury and lithium — certified e-waste facilities handle them safely.',
    errMsg: {
      battery:
        "The laptop has a battery inside, but don't dismantle it yourself. The whole unit goes to E-Waste.",
      repair:
        "An old, non-functional laptop isn't worth repairing. It belongs in E-Waste for safe material recovery.",
      general:
        'Laptops contain lead and mercury — putting them in general waste is illegal and environmentally harmful.',
    },
  },
  {
    id: 6,
    name: 'Headphones',
    icon: '🎧',
    answer: 'E-Waste',
    okMsg:
      'Correct! Headphones contain electronic drivers, copper wiring and sometimes batteries — always e-recycle them.',
    errMsg: {
      battery:
        'Headphones contain more than just a battery — the drivers and wiring make them e-waste, not battery bin material.',
      repair: "Old, broken headphones aren't worth refurbishing for reuse. They belong in E-Waste.",
      general:
        "Headphones contain electronic components and copper — they're e-waste, not something you can bin normally.",
    },
  },
  {
    id: 7,
    name: 'Keyboard',
    icon: '⌨️',
    answer: 'E-Waste',
    okMsg:
      'Right! Keyboards contain printed circuit boards and electronic switches — they need e-waste recycling.',
    errMsg: {
      battery:
        "A keyboard doesn't run on removable batteries — it contains circuit boards that go to E-Waste.",
      repair:
        'An old keyboard has very little refurbishment value. It belongs in E-Waste for PCB and component recovery.',
      general:
        "Keyboards contain circuit boards and plastic that can be recovered — they're e-waste, not general rubbish.",
    },
  },
  {
    id: 8,
    name: 'Laptop Battery',
    icon: '🔋',
    answer: 'Battery Bin',
    okMsg:
      'Great! Lithium laptop batteries need their own dedicated recycling stream — never mix them with e-waste.',
    errMsg: {
      ewaste:
        'Close, but batteries need their own separate bin — mixing lithium with general e-waste is a serious fire risk.',
      repair:
        "A depleted laptop battery can't be safely recharged or reused. It must go to the Battery Bin.",
      general:
        'Never put lithium batteries in general waste — they can catch fire and leak toxic chemicals in landfill.',
    },
  },
  {
    id: 9,
    name: 'Old Monitor',
    icon: '🖥️',
    answer: 'E-Waste',
    okMsg:
      'Correct! Monitors contain lead, mercury and rare metals — they must go to a certified e-waste facility.',
    errMsg: {
      battery:
        "Monitors don't run on batteries — they contain hazardous materials like lead that require E-Waste disposal.",
      repair:
        'An old monitor has little reuse value and contains toxic materials — E-Waste is the only safe option.',
      general:
        'Monitors contain lead and mercury — putting them in general waste is dangerous and illegal in most regions.',
    },
  },
  {
    id: 10,
    name: 'Phone Case',
    icon: '📦',
    answer: 'General Waste',
    okMsg:
      'Exactly! A phone case is just moulded plastic or silicone — no electronics or battery, so general waste it is.',
    errMsg: {
      ewaste:
        "A phone case has no circuit boards or wiring inside. It's just plastic — it belongs in General Waste.",
      battery:
        "There's no battery in a phone case — it's moulded rubber or plastic. It goes straight to General Waste.",
      repair:
        "A phone case has no electronic components and nothing worth repairing. It's simply General Waste.",
    },
  },
]

const items = ref(
  initialItems.map((item) => ({
    ...item,
    sorted: false,
    selectedBin: '',
    firstAttempted: false,
    firstCorrect: false,
  })),
)

const sortedItems = ref({
  'E-Waste': [],
  'Battery Bin': [],
  'Repair / Reuse': [],
  'General Waste': [],
})

const unsortedItems = computed(() => {
  return items.value.filter((item) => !item.sorted)
})

const correctCount = computed(() => {
  return items.value.filter((item) => item.firstCorrect).length
})

const resultTitle = computed(() => {
  if (correctCount.value === items.value.length) return 'Perfect Sorting!'
  if (correctCount.value >= 6) return 'Good Job!'
  return 'Keep Practising!'
})

function startGame() {
  started.value = true
  finished.value = false
}

function selectItem(item) {
  selectedItem.value = item
}

function dragStart(item) {
  draggedItem.value = item
}

function dropItem(binName) {
  if (!draggedItem.value) return

  selectedItem.value = draggedItem.value
  placeItem(binName)
  draggedItem.value = null
}

function showFeedback(text, type) {
  toastText.value = text
  toastType.value = type
  showToast.value = true

  setTimeout(
    () => {
      showToast.value = false
    },
    type === 'wrong' ? 3000 : 2000,
  )
}

function placeItem(binName) {
  if (!selectedItem.value) return

  const item = selectedItem.value
  const target = items.value.find((i) => i.id === item.id)

  if (!target) return

  const binMap = {
    'E-Waste': 'ewaste',
    'Battery Bin': 'battery',
    'Repair / Reuse': 'repair',
    'General Waste': 'general',
  }

  const binKey = binMap[binName]

  feedbackBin.value = binName

  if (!target.firstAttempted) {
    target.firstAttempted = true

    if (target.answer === binName) {
      target.firstCorrect = true
      score.value += 10
      showFeedback(target.okMsg || 'Correct! +10', 'correct')
    } else {
      showFeedback(target.errMsg?.[binKey] || 'Wrong! Try again', 'wrong')
    }
  } else if (target.answer === binName) {
    showFeedback(target.okMsg || 'Correct!', 'correct')
  } else {
    showFeedback(target.errMsg?.[binKey] || 'Wrong! Try again', 'wrong')
  }

  if (target.answer === binName) {
    feedbackType.value = 'correct'

    sortedItems.value[binName].push(target)
    target.sorted = true
    target.selectedBin = binName
  } else {
    feedbackType.value = 'wrong'
  }

  selectedItem.value = null

  setTimeout(() => {
    feedbackBin.value = ''
    feedbackType.value = ''
  }, 700)
}

function returnItem(item, binName) {
  if (selectedItem.value) {
    placeItem(binName)
    return
  }

  sortedItems.value[binName] = sortedItems.value[binName].filter((i) => i.id !== item.id)

  const target = items.value.find((i) => i.id === item.id)

  if (target) {
    target.sorted = false
    target.selectedBin = ''
  }
}

function finishGame() {
  finished.value = true
}

function finishGameEarly() {
  showEndConfirm.value = false
  finished.value = true
}

function resetGame() {
  score.value = 0
  selectedItem.value = null
  draggedItem.value = null
  feedbackBin.value = ''
  feedbackType.value = ''
  showToast.value = false
  toastText.value = ''
  toastType.value = ''
  finished.value = false
  showEndConfirm.value = false

  items.value = initialItems.map((item) => ({
    ...item,
    sorted: false,
    selectedBin: '',
    firstAttempted: false,
    firstCorrect: false,
  }))

  sortedItems.value = {
    'E-Waste': [],
    'Battery Bin': [],
    'Repair / Reuse': [],
    'General Waste': [],
  }
}

function restartGame() {
  resetGame()
  started.value = true
}

function goHome() {
  resetGame()
  started.value = false
}
</script>

<style scoped>
.game-page {
  min-height: 100vh;
  padding: 120px 6% 60px;
  background: linear-gradient(180deg, #f4fbf7 0%, #ffffff 100%);
  display: flex;
  justify-content: center;
  align-items: center;
}

.cover-card,
.game-card,
.result-card {
  width: 100%;
  max-width: 1200px;
  background: #ffffff;
  border-radius: 28px;
  padding: 48px;
  text-align: center;
  box-shadow: 0 20px 50px rgba(27, 94, 62, 0.14);
}

.cover-card,
.result-card {
  max-width: 760px;
}

.cover-icon {
  width: 86px;
  height: 86px;
  margin: 0 auto 18px;
  border-radius: 50%;
  background: #e6f6ec;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42px;
}

.eyebrow {
  color: #2f8f5b;
  font-weight: 800;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.cover-card h1,
.result-card h1 {
  font-size: 42px;
  color: #123524;
  margin-bottom: 16px;
}

.cover-desc {
  max-width: 580px;
  margin: 0 auto 22px;
  color: #5b6770;
  font-size: 18px;
  line-height: 1.6;
}

.cover-hint {
  color: #7a8792;
  font-weight: 700;
  margin-bottom: 36px;
}

.top-actions {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 18px;
}

.back-btn {
  padding: 11px 20px;
  border-radius: 999px;
  border: 2px solid #2f8f5b;
  background: #e6f6ec;
  color: #246b45;
  font-size: 16px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(47, 143, 91, 0.16);
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: #2f8f5b;
  color: white;
  transform: translateX(-3px);
}

.top-bar {
  display: flex;
  justify-content: space-between;
  color: #2f8f5b;
  font-weight: 800;
  font-size: 18px;
  margin-bottom: 26px;
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 18px;
  margin-bottom: 22px;
}

.item-card {
  min-height: 120px;
  padding: 18px 12px;
  border: 2px solid #d7e7dc;
  border-radius: 18px;
  background: #ffffff;
  cursor: grab;
  transition: all 0.2s ease;
}

.item-card:active {
  cursor: grabbing;
}

.item-card:hover,
.item-card.selected {
  border-color: #2f8f5b;
  background: #e6f6ec;
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(47, 143, 91, 0.18);
}

.item-icon {
  font-size: 42px;
  margin-bottom: 10px;
}

.item-card span {
  font-weight: 800;
  color: #1f2933;
}

.hint {
  margin: 14px 0 26px;
  color: #7a8792;
  font-weight: 800;
}

.bins-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-top: 24px;
}

.bin-box {
  min-height: 220px;
  border-radius: 22px;
  padding: 22px 18px;
  text-align: center;
  cursor: pointer;
  transition: all 0.22s ease;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.bin-box:hover {
  transform: translateY(-5px);
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.13);
}

.bin-box h3 {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 800;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.75);
  color: #123524;
  margin: 0 auto 18px;
}

.correctFlash {
  animation: correctFlash 0.7s ease;
}

.wrongFlash {
  animation: wrongFlash 0.7s ease;
}

@keyframes correctFlash {
  0% {
    transform: scale(1);
  }
  40% {
    transform: scale(1.04);
    background: #bbf7d0;
  }
  100% {
    transform: scale(1);
  }
}

@keyframes wrongFlash {
  0% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-8px);
    background: #fecaca;
  }
  50% {
    transform: translateX(8px);
    background: #fecaca;
  }
  100% {
    transform: translateX(0);
  }
}

.ewaste-bin {
  background: linear-gradient(180deg, #faf5ff 0%, #f3e8ff 100%);
  border: 2px solid #a855f7;
}

.battery-bin {
  background: linear-gradient(180deg, #fff7f7 0%, #fee2e2 100%);
  border: 2px solid #ef4444;
}

.reuse-bin {
  background: linear-gradient(180deg, #f0fdf4 0%, #dcfce7 100%);
  border: 2px solid #22c55e;
}

.general-bin {
  background: linear-gradient(180deg, #ffffff 0%, #f3f4f6 100%);
  border: 2px solid #9ca3af;
}

.placed-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.placed-card {
  padding: 12px 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(15, 23, 42, 0.08);
  text-align: center;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
}

.placed-card:hover {
  transform: translateY(-2px);
  background: white;
}

.placed-icon {
  font-size: 26px;
  margin-bottom: 4px;
}

.placed-card span {
  font-size: 13px;
  font-weight: 700;
  color: #374151;
}

.game-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 30px;
  flex-wrap: wrap;
}

.final-score {
  font-size: 36px;
  font-weight: 900;
  color: #2f8f5b;
  margin: 20px 0;
}

.result-summary {
  max-width: 560px;
  margin: 0 auto 24px;
  padding: 18px;
  border-radius: 18px;
  background: #f0f8f3;
  color: #246b45;
  font-weight: 700;
  line-height: 1.6;
}

.explanation-box {
  max-width: 640px;
  margin: 0 auto 28px;
  padding: 24px;
  border-radius: 20px;
  background: #f8faf9;
  text-align: left;
}

.explanation-box h3 {
  color: #123524;
  margin-bottom: 14px;
}

.explanation-box p {
  color: #5b6770;
  line-height: 1.6;
  margin-bottom: 10px;
}

.primary-btn,
.secondary-btn {
  padding: 15px 38px;
  border-radius: 999px;
  font-size: 17px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-btn {
  border: none;
  background: #2f8f5b;
  color: white;
}

.primary-btn:hover {
  background: #247348;
  transform: translateY(-2px);
}

.secondary-btn {
  border: 2px solid #2f8f5b;
  background: white;
  color: #2f8f5b;
}

.secondary-btn:hover {
  background: #f0f8f3;
  transform: translateY(-2px);
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 20px;
}

.confirm-box {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 24px;
  padding: 32px;
  text-align: center;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.25);
}

.confirm-box h3 {
  font-size: 24px;
  color: #123524;
  margin-bottom: 12px;
}

.confirm-box p {
  color: #5b6770;
  line-height: 1.6;
  margin-bottom: 24px;
}

.confirm-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
}

.toast {
  position: fixed;
  top: 110px;
  left: 50%;
  transform: translateX(-50%) scale(0.9);
  max-width: 720px;
  width: calc(100% - 40px);
  padding: 18px 26px;
  border-radius: 18px;
  color: white;
  font-size: 15.5px;
  line-height: 1.6;
  font-weight: 700;
  text-align: center;
  z-index: 9999;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.25);
  animation: popToast 0.3s ease forwards;
}

.toast.correct {
  background: #22c55e;
}

.toast.wrong {
  background: #ef4444;
}

@keyframes popToast {
  0% {
    opacity: 0;
    transform: translateX(-50%) scale(0.75);
  }
  100% {
    opacity: 1;
    transform: translateX(-50%) scale(1);
  }
}

@media (max-width: 1000px) {
  .items-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .bins-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .game-page {
    padding: 100px 5% 40px;
  }

  .cover-card,
  .game-card,
  .result-card {
    padding: 30px;
  }

  .cover-card h1,
  .result-card h1 {
    font-size: 32px;
  }

  .items-grid,
  .bins-grid {
    grid-template-columns: 1fr;
  }

  .result-actions,
  .confirm-actions {
    flex-direction: column;
    gap: 12px;
  }

  .toast {
    top: 90px;
    font-size: 14.5px;
    padding: 14px 20px;
  }
}
</style>
