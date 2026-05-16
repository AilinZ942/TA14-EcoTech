<template>
  <div class="home">
    <!-- HERO -->
    <section class="hero">
      <div class="hero-bg" aria-hidden="true">
        <img class="hero-photo" :src="heroImage" alt="" />
        <div class="hero-photo-overlay" />
        <div class="orb orb-1" />
        <div class="orb orb-2" />
        <div class="grid" />
      </div>

      <div class="eco-shell hero-shell">
        <div class="hero-meta">
          <span class="eco-eyebrow">A Victorian project · 2026</span>
          <span class="eco-mono">© Iteration 03</span>
        </div>

        <h1 class="hero-title">
          <span class="line">Give old</span>
          <span class="line">electronics</span>
          <span class="line accent">a second life.</span>
        </h1>

        <div class="hero-actions">
          <router-link to="/pickup-points" class="eco-btn eco-btn--mint">
            Find pickup near me
            <span class="arrow">→</span>
          </router-link>
          <router-link to="/ai-chat" class="eco-btn eco-btn--ghost">
            Check my device
          </router-link>
        </div>
      </div>

      <button class="scroll-cue" type="button" @click="scrollDown" aria-label="Scroll">
        <span class="cue-line" />
        <span class="eco-mono">Scroll</span>
      </button>
    </section>

    <!-- MARQUEE -->
    <section class="ticker" aria-hidden="true">
      <div class="ticker-track">
        <span v-for="i in 2" :key="i" class="ticker-row">
          <span>Repair</span>
          <span class="dot">●</span>
          <span>Reuse</span>
          <span class="dot">●</span>
          <span>Recycle</span>
          <span class="dot">●</span>
          <span>Rethink</span>
          <span class="dot">●</span>
          <span>Reduce</span>
          <span class="dot">●</span>
        </span>
      </div>
    </section>

    <!-- FOUR PATHS -->
    <section ref="pathsRef" class="paths">
      <div class="eco-shell">
        <div class="paths-head">
          <span class="eco-eyebrow reveal">Four ways forward</span>
          <h2 class="eco-h2 reveal reveal-delay-1">
            One device.<br />Four paths<br />before landfill.
          </h2>
        </div>

        <div class="paths-grid">
          <router-link
            v-for="(p, i) in paths"
            :key="p.title"
            :to="p.to"
            class="path reveal"
            :class="`reveal-delay-${i + 1}`"
            :style="{ '--accent': p.color }"
          >
            <div class="path-num">0{{ i + 1 }}</div>
            <div class="path-body">
              <h3>{{ p.title }}</h3>
              <p>{{ p.desc }}</p>
            </div>
            <span class="path-arrow">→</span>
          </router-link>
        </div>
      </div>
    </section>

    <!-- IMPACT — minimal numbers -->
    <section class="numbers">
      <div class="eco-shell numbers-grid">
        <div class="num-cell reveal">
          <span class="eco-mono">Australia / yr</span>
          <strong class="num">540K<span>t</span></strong>
          <span class="num-cap">e-waste generated</span>
        </div>
        <div class="num-cell reveal reveal-delay-1">
          <span class="eco-mono">Battery fires</span>
          <strong class="num">12K<span>+</span></strong>
          <span class="num-cap">in waste trucks each year</span>
        </div>
        <div class="num-cell reveal reveal-delay-2">
          <span class="eco-mono">Reuse impact</span>
          <strong class="num">80<span>kg</span></strong>
          <span class="num-cap">CO₂ saved per phone reused</span>
        </div>
      </div>
    </section>

    <!-- BIG STATEMENT -->
    <section class="statement reveal">
      <div class="eco-shell">
        <p class="statement-text">
          The bin is the easy answer.<br />
          <em>It's also the wrong one.</em>
        </p>
        <router-link to="/dashboard" class="eco-btn eco-btn--ghost">
          See why it matters <span class="arrow">→</span>
        </router-link>
      </div>
    </section>

    <!-- FINAL CTA -->
    <section class="end">
      <div class="eco-shell end-inner">
        <div class="end-text">
          <span class="eco-eyebrow reveal">Get started</span>
          <h2 class="eco-h2 reveal reveal-delay-1">
            Don't bin it.<br />Reroute it.
          </h2>
          <p class="eco-lead reveal reveal-delay-2">
            Three tools. Two minutes each. One better outcome for your device.
          </p>
        </div>
        <div class="end-actions reveal reveal-delay-3">
          <router-link to="/repair-check" class="end-link">
            <span class="eco-mono">01</span>
            <strong>Repair or replace?</strong>
            <span class="arrow">→</span>
          </router-link>
          <router-link to="/pickup-points" class="end-link">
            <span class="eco-mono">02</span>
            <strong>Find a pickup point</strong>
            <span class="arrow">→</span>
          </router-link>
          <router-link to="/disposal-locations" class="end-link">
            <span class="eco-mono">03</span>
            <strong>Find a drop-off</strong>
            <span class="arrow">→</span>
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useReveal } from '@/composables/useReveal'
import heroImage from '@/assets/icons/home-ewaste.png'

useReveal()

const pathsRef = ref(null)
function scrollDown() {
  pathsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const paths = [
  { title: 'Repair', desc: 'Most issues cost less to fix than to replace.', to: '/repair-check', color: '#7DD8B0' },
  { title: 'Reuse', desc: 'Drop a working device at an EcoReviva stall.', to: '/pickup-points', color: '#5EEAD4' },
  { title: 'Recycle', desc: 'Find a certified e-waste site near you.', to: '/disposal-locations', color: '#A78BFA' },
  { title: 'Rethink', desc: 'See what e-waste actually does to your health.', to: '/dashboard', color: '#F4A261' },
]
</script>

<style scoped>
.home { padding-top: 0; }

/* HERO */
.hero {
  position: relative;
  min-height: 100vh;
  padding: 140px 0 60px;
  display: flex;
  align-items: center;
  overflow: hidden;
}
.hero-bg { position: absolute; inset: 0; z-index: 0; pointer-events: none; }
.hero-photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.9;
  filter: saturate(1.18) contrast(1.12) brightness(1.08);
  transform: scale(1.04);
  animation: hero-zoom 24s ease-in-out infinite alternate;
}
.hero-photo-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(6, 18, 15, 0.66) 0%, rgba(6, 18, 15, 0.36) 45%, rgba(6, 18, 15, 0.18) 100%),
    radial-gradient(ellipse 70% 60% at 76% 44%, rgba(125, 216, 176, 0.10), transparent 62%),
    linear-gradient(180deg, rgba(6, 18, 15, 0.08), rgba(6, 18, 15, 0.55));
}
@keyframes hero-zoom {
  from { transform: scale(1.04) translate3d(0, 0, 0); }
  to { transform: scale(1.10) translate3d(-1.5%, -1%, 0); }
}
.orb {
  position: absolute;
  z-index: 1;
  border-radius: 50%;
  filter: blur(110px);
  opacity: 0.35;
  animation: float-y 18s ease-in-out infinite;
}
.orb-1 {
  width: 540px; height: 540px;
  top: -120px; left: -100px;
  background: var(--mint);
}
.orb-2 {
  width: 460px; height: 460px;
  bottom: -120px; right: -100px;
  background: var(--violet);
  opacity: 0.22;
  animation-delay: -9s;
}
.grid {
  position: absolute; inset: 0;
  z-index: 1;
  background-image:
    linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 90px 90px;
  mask-image: radial-gradient(ellipse 80% 60% at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse 80% 60% at center, black 30%, transparent 80%);
}

.hero-shell {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 36px;
}
.hero-meta {
  display: flex; justify-content: space-between; align-items: center;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(56px, 12vw, 180px);
  line-height: 0.92;
  letter-spacing: -0.05em;
  font-weight: 500;
  color: var(--ink-0);
  margin: 0;
  text-shadow: 0 10px 40px rgba(0, 0, 0, 0.45);
}
.hero-title .line {
  display: block;
  overflow: hidden;
}
.hero-title .line span {
  display: inline-block;
  animation: rise 1.1s var(--ease-out) both;
}
.line:nth-child(1) span { animation-delay: 0.1s; }
.line:nth-child(2) span { animation-delay: 0.22s; }
.line:nth-child(3) span { animation-delay: 0.34s; }
@keyframes rise {
  from { transform: translateY(110%); }
  to { transform: translateY(0); }
}
.hero-title .line { animation: rise-block 1.1s var(--ease-out) both; }
.hero-title .accent {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint) 0%, var(--mint-bright) 60%, var(--violet) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
@keyframes rise-block {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.hero-actions {
  display: flex; gap: 14px; flex-wrap: wrap;
  animation: rise-block 1.1s var(--ease-out) 0.6s both;
}

.scroll-cue {
  position: absolute;
  bottom: 30px; left: 50%;
  transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  background: transparent; border: 0;
  color: var(--ink-2);
  z-index: 3;
}
.cue-line {
  width: 1px; height: 28px;
  background: var(--mint);
  animation: drop 1.6s ease-in-out infinite;
}
@keyframes drop {
  0%, 100% { transform: scaleY(1); transform-origin: top; opacity: 0.5; }
  50% { transform: scaleY(0.4); opacity: 1; }
}

/* TICKER */
.ticker {
  margin: 60px 0 80px;
  padding: 24px 0;
  border-top: 1px solid var(--hairline);
  border-bottom: 1px solid var(--hairline);
  overflow: hidden;
  background: rgba(255,255,255,0.01);
}
.ticker-track {
  display: flex; width: max-content;
  animation: marquee 38s linear infinite;
}
.ticker-row {
  display: inline-flex; gap: 60px; align-items: center;
  padding-right: 60px;
  font-family: var(--font-display);
  font-size: clamp(36px, 5vw, 64px);
  letter-spacing: -0.02em;
  font-weight: 500;
  color: var(--ink-0);
}
.ticker-row .dot { color: var(--mint); font-size: 0.5em; }
.ticker-row span { white-space: nowrap; }
.ticker-row span:nth-child(odd):not(.dot):hover { color: var(--mint); cursor: default; }

/* PATHS */
.paths { padding: 100px 0; }
.paths-head { display: flex; flex-direction: column; gap: 18px; margin-bottom: 60px; }
.paths-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  border-top: 1px solid var(--hairline);
}
.path {
  display: grid;
  grid-template-columns: 80px 1fr 60px;
  gap: 32px;
  align-items: center;
  padding: 32px 0;
  border-bottom: 1px solid var(--hairline);
  color: var(--ink-0);
  position: relative;
  transition: padding 0.4s var(--ease-out);
}
.path::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, var(--accent) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.4s var(--ease-out);
  pointer-events: none;
  margin-left: -24px; margin-right: -24px;
  border-radius: var(--r-md);
}
.path:hover { padding: 32px 24px; }
.path:hover::before { opacity: 0.06; }
.path-num {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.18em;
  color: var(--accent);
}
.path h3 {
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 48px);
  font-weight: 500;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
  transition: color 0.3s var(--ease-out);
}
.path:hover h3 { color: var(--accent); }
.path p { color: var(--ink-2); font-size: 15px; }
.path-arrow {
  font-size: 28px;
  color: var(--ink-2);
  transition: transform 0.4s var(--ease-out), color 0.3s;
}
.path:hover .path-arrow { transform: translateX(8px); color: var(--accent); }

/* NUMBERS */
.numbers { padding: 100px 0; }
.numbers-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
}
.num-cell {
  display: flex; flex-direction: column; gap: 10px;
  padding: 36px 28px;
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-md);
  transition: transform 0.4s var(--ease-out), border-color 0.3s;
}
.num-cell:hover { transform: translateY(-4px); border-color: var(--mint); }
.num {
  font-family: var(--font-display);
  font-size: clamp(56px, 7vw, 96px);
  font-weight: 500;
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--mint);
}
.num span { font-size: 0.4em; color: var(--ink-2); margin-left: 4px; }
.num-cap { color: var(--ink-1); font-size: 14px; }

/* STATEMENT */
.statement { padding: 100px 0; text-align: center; }
.statement-text {
  font-family: var(--font-display);
  font-size: clamp(36px, 6vw, 80px);
  line-height: 1.05;
  letter-spacing: -0.03em;
  font-weight: 500;
  color: var(--ink-0);
  margin: 0 0 32px;
}
.statement-text em { color: var(--mint); font-style: italic; }
.statement .eco-btn { display: inline-flex; }

/* END */
.end {
  padding: 100px 0 40px;
}
.end-inner {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: end;
}
.end-text { display: flex; flex-direction: column; gap: 20px; }
.end-actions { display: flex; flex-direction: column; gap: 0; }
.end-link {
  display: grid;
  grid-template-columns: 60px 1fr 30px;
  gap: 18px;
  align-items: center;
  padding: 22px 0;
  border-top: 1px solid var(--hairline);
  color: var(--ink-0);
  transition: padding 0.4s var(--ease-out);
}
.end-link:last-child { border-bottom: 1px solid var(--hairline); }
.end-link strong {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 500;
}
.end-link .arrow { color: var(--ink-2); transition: color 0.3s, transform 0.4s var(--ease-out); }
.end-link:hover { padding-left: 12px; }
.end-link:hover .arrow { color: var(--mint); transform: translateX(6px); }

@media (max-width: 880px) {
  .paths-grid { gap: 0; }
  .path { grid-template-columns: 60px 1fr 40px; gap: 16px; padding: 24px 0; }
  .numbers-grid { grid-template-columns: 1fr; }
  .end-inner { grid-template-columns: 1fr; gap: 40px; align-items: stretch; }
  .hero-meta { flex-wrap: wrap; gap: 8px; }
}
</style>
