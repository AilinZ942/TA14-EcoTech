import { createRouter, createWebHashHistory } from 'vue-router'

import Home from '@/views/Home.vue'
import Dashboard from '@/views/Dashboard.vue'
import RepairCheck from '@/views/RepairCheck.vue'
import ExtendUsage from '@/views/ExtendUsage.vue'
import AIChat from '@/views/AIChat.vue'
import SafeGuidance from '@/views/SafeGuidance.vue'
import DisposalLocations from '@/views/DisposalLocations.vue'
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
    path: '/device-optimizer',
    name: 'DeviceOptimizer',
    component: AIChat,
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-chat',
    redirect: '/device-optimizer',
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
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to) => {
  let isLoggedIn = false

  try {
    const authState = await authAPI.checkAuth()
    isLoggedIn = Boolean(authState?.logged_in)
  } catch (error) {
    isLoggedIn = false
  }

  if (to.path === '/login' && isLoggedIn) {
    return { path: '/' }
  }

  if (to.meta.requiresAuth !== false && !isLoggedIn) {
    return {
      path: '/login',
      query: to.fullPath !== '/' ? { redirect: to.fullPath } : {},
    }
  }

  return true
})

export default router
