<template>
  <header v-if="showChrome" class="nav" :class="{ scrolled }">
    <div class="nav-inner">
      <router-link to="/" class="brand" @click="closeMenu">
        <span class="brand-mark">
          <img :src="logoImage" alt="EcoReviva logo" class="brand-logo" />
        </span>
        <span class="brand-text">EcoReviva</span>
        <span class="brand-tag">VIC · AU</span>
      </router-link>

      <nav class="links" :class="{ open: menuOpen }">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          @click="closeMenu"
          class="link"
        >
          <span class="link-text">{{ link.label }}</span>
        </router-link>
        <button class="link logout-link" type="button" @click="handleLogout">
          <span class="link-text">Logout</span>
        </button>
      </nav>

      <button class="hamburger" type="button" aria-label="Menu" @click="menuOpen = !menuOpen">
        <span :class="{ on: menuOpen }" />
        <span :class="{ on: menuOpen }" />
      </button>
    </div>
  </header>

  <main>
    <router-view v-slot="{ Component, route }">
      <transition name="page" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
  </main>

  <footer v-if="showChrome" class="foot">
    <div class="foot-inner eco-shell">
      <div class="foot-grid">
        <div class="foot-brand">
          <div class="foot-mark">
            <img :src="logoImage" alt="EcoReviva logo" class="foot-logo" />
          </div>
          <p class="foot-line">Give old electronics<br /><em>a second life.</em></p>
          <span class="eco-mono">© 2026 — TA-14 industry project</span>
        </div>
        <div class="foot-cols">
          <div class="foot-col">
            <span class="eco-mono">Discover</span>
            <router-link to="/dashboard">Health insights</router-link>
            <router-link to="/disposal-locations">Disposal map</router-link>
            <router-link to="/pickup-points">Pickup points</router-link>
          </div>
          <div class="foot-col">
            <span class="eco-mono">Tools</span>
            <router-link to="/ai-chat">AI Optimizer</router-link>
            <router-link to="/repair-check">Repair / Replace</router-link>
            <router-link to="/game">Sorting Game</router-link>
          </div>
        </div>
      </div>
      <div class="foot-rule" />
      <div class="foot-bottom">
        <span class="eco-mono">EcoReviva — Iteration 3</span>
        <span class="eco-mono">Made in Melbourne</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI, initCSRF } from '@/api'
import logoImage from '@/assets/icons/ecoreviva-logo.png'

const route = useRoute()
const router = useRouter()

const links = [
  { to: '/', label: 'Home' },
  { to: '/dashboard', label: 'Health' },
  { to: '/game', label: 'Game' },
  { to: '/ai-chat', label: 'AI Optimizer' },
  { to: '/repair-check', label: 'Repair' },
  { to: '/pickup-points', label: 'Pickup' },
  { to: '/disposal-locations', label: 'Disposal' },
]

const showChrome = computed(() => route.path !== '/login')
const scrolled = ref(false)
const menuOpen = ref(false)

function onScroll() { scrolled.value = window.scrollY > 12 }
onMounted(() => {
  initCSRF()
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))
watch(() => route.path, () => { menuOpen.value = false })

function closeMenu() { menuOpen.value = false }
async function handleLogout() {
  try { await authAPI.logout() } catch (e) {}
  router.replace('/login')
}
</script>

<style>
/* page transition */
.page-enter-active, .page-leave-active {
  transition: opacity 0.5s var(--ease-out), transform 0.5s var(--ease-out);
}
.page-enter-from { opacity: 0; transform: translateY(20px); }
.page-leave-to { opacity: 0; transform: translateY(-10px); }
</style>

<style scoped>
.nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  padding: 22px 0;
  transition: padding 0.4s var(--ease-out), background 0.4s var(--ease-out);
}
.nav.scrolled {
  padding: 12px 0;
  background: rgba(6, 18, 15, 0.7);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  border-bottom: 1px solid var(--hairline);
}
.nav-inner {
  width: min(1240px, calc(100% - 48px));
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--ink-0);
}
.brand-mark {
  display: inline-grid; place-items: center;
  width: 38px; height: 38px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--hairline-strong);
  align-self: center;
  overflow: hidden;
}
.brand-logo {
  width: 30px;
  height: 34px;
  object-fit: contain;
  filter: drop-shadow(0 6px 12px rgba(16, 185, 129, 0.24));
}
.brand-text {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 19px;
  letter-spacing: -0.02em;
}
.brand-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-2);
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.links {
  display: flex;
  align-items: center;
  gap: 4px;
}
.link {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 9px 14px;
  border-radius: var(--r-pill);
  background: transparent;
  border: 0;
  color: var(--ink-1);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.3s var(--ease-out), background 0.3s var(--ease-out);
}
.link:hover { color: var(--ink-0); }
.link.router-link-exact-active {
  color: var(--ink-on-light);
  background: var(--mint);
  box-shadow: 0 6px 22px rgba(125, 216, 176, 0.3);
}
.logout-link { color: var(--ink-2); }
.logout-link:hover { color: var(--bad); }

.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: transparent;
  border: 0;
  padding: 6px;
  cursor: pointer;
}
.hamburger span {
  width: 22px; height: 1.5px;
  background: var(--ink-0);
  transition: transform 0.3s var(--ease-out), opacity 0.2s;
}
.hamburger span.on:nth-child(1) { transform: translateY(3.5px) rotate(45deg); }
.hamburger span.on:nth-child(2) { transform: translateY(-3px) rotate(-45deg); }

main { min-height: 100vh; }

.foot {
  margin-top: 120px;
  padding: 80px 0 36px;
  border-top: 1px solid var(--hairline);
  background: linear-gradient(180deg, transparent, rgba(0,0,0,0.4));
}
.foot-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 60px;
  align-items: start;
}
.foot-brand { display: flex; flex-direction: column; gap: 18px; }
.foot-mark {
  width: 56px; height: 56px;
  display: grid; place-items: center;
  border: 1px solid var(--hairline-strong);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  overflow: hidden;
}
.foot-logo {
  width: 42px;
  height: 48px;
  object-fit: contain;
  filter: drop-shadow(0 10px 18px rgba(16, 185, 129, 0.22));
}
.foot-line {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 500;
  letter-spacing: -0.02em;
  color: var(--ink-0);
  margin: 0;
  line-height: 1.1;
}
.foot-line em { color: var(--mint); font-style: normal; }
.foot-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
.foot-col { display: flex; flex-direction: column; gap: 12px; }
.foot-col .eco-mono { color: var(--ink-2); margin-bottom: 4px; }
.foot-col a {
  color: var(--ink-1);
  font-size: 14px;
  transition: color 0.2s var(--ease-out);
}
.foot-col a:hover { color: var(--mint); }

.foot-rule {
  height: 1px;
  background: var(--hairline);
  margin: 50px 0 24px;
}
.foot-bottom { display: flex; justify-content: space-between; }

@media (max-width: 880px) {
  .hamburger { display: flex; }
  .links {
    position: absolute;
    top: calc(100% + 10px); left: 16px; right: 16px;
    flex-direction: column;
    align-items: stretch;
    padding: 14px;
    background: rgba(10, 27, 23, 0.96);
    border: 1px solid var(--hairline);
    border-radius: var(--r-md);
    backdrop-filter: blur(18px);
    transform: translateY(-10px);
    opacity: 0;
    pointer-events: none;
    transition: transform 0.3s var(--ease-out), opacity 0.3s;
  }
  .links.open { transform: translateY(0); opacity: 1; pointer-events: auto; }
  .link { padding: 12px 14px; justify-content: flex-start; }
  .foot-grid { grid-template-columns: 1fr; gap: 40px; }
  .foot-cols { gap: 24px; }
}
</style>
