import { createRouter, createWebHashHistory } from 'vue-router'

import Home from '@/views/Home.vue'
import Dashboard from '@/views/Dashboard.vue'
import RepairCheck from '@/views/RepairCheck.vue'
import ExtendUsage from '@/views/ExtendUsage.vue'
import AIChat from '@/views/AIChat.vue'
import SafeGuidance from '@/views/SafeGuidance.vue'
import DisposalLocations from '@/views/DisposalLocations.vue'
import PickupPoints from '@/views/PickupPoints.vue'
import Game from '@/views/Game.vue'
import Login from '@/views/Login.vue'
import { authAPI } from '@/api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },

  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },

  {
    path: '/repair-check',
    name: 'RepairCheck',
    component: RepairCheck,
    meta: { requiresAuth: true }
  },
  {
    path: '/extend-usage',
    name: 'ExtendUsage',
    component: ExtendUsage,
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-chat',
    name: 'AIChat',
    component: AIChat,
    meta: { requiresAuth: true }
  },

  {
    path: '/safe-guidance',
    name: 'SafeGuidance',
    component: SafeGuidance,
    meta: { requiresAuth: true }
  },
  {
    path: '/disposal-locations',
    name: 'DisposalLocations',
    component: DisposalLocations,
    meta: { requiresAuth: true }
  },
  {
    path: '/pickup-points',
    name: 'PickupPoints',
    component: PickupPoints,
    meta: { requiresAuth: true }
  },
  {
    path: '/game',
    name: 'Game',
    component: Game,
    meta: { requiresAuth: true }
  }
    
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, saved) {
    if (saved) return saved
    return { top: 0, behavior: 'smooth' }
  },
})

// Cache auth state briefly so navigation doesn't refetch on every link click
let authCache = { value: null, ts: 0 }

router.beforeEach(async (to) => {
  let isLoggedIn = false
  const now = Date.now()

  if (authCache.value !== null && now - authCache.ts < 5000) {
    isLoggedIn = authCache.value
  } else {
    try {
      const authState = await authAPI.checkAuth()
      isLoggedIn = Boolean(authState?.logged_in)
    } catch (error) {
      isLoggedIn = false
    }
    authCache = { value: isLoggedIn, ts: now }
  }

  if (to.path === '/login' && isLoggedIn) return { path: '/' }
  if (to.meta.requiresAuth !== false && !isLoggedIn) {
    return {
      path: '/login',
      query: to.fullPath !== '/' ? { redirect: to.fullPath } : {},
    }
  }
  return true
})

export default router
