<template>
  <nav v-if="showNavbar" class="navbar">
    <!-- FULL logo clickable -->
    <router-link to="/" class="logo">
      <img src="@/assets/logo test.png" alt="EcoTech Logo" class="logo-img" />
      <span class="logo-text">EcoTech</span>
    </router-link>

    <div class="links">
      <router-link to="/">Home</router-link>
      <router-link to="/dashboard">Dashboard</router-link>
      <!--<router-link to="/repair-check">Repair Check</router-link> -->
      <router-link to="/game">Sorting Game</router-link>
      <!--<router-link to="/extend-usage">Extend Usage</router-link> -->
      <router-link to="/device-optimizer">AI Device Optimizer</router-link>
      <!--<router-link to="/safe-guidance">Safe Guidance</router-link>-->
      <router-link to="/disposal-locations">Disposal Locations</router-link>
      <button type="button" class="logout-button" @click="handleLogout">Logout</button>
    </div>
  </nav>

  <router-view />
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI, initCSRF } from './api/index.js'

const router = useRouter()

onMounted(() => {
  initCSRF() // apply CSRF token to all API requests after app is mounted
})

const route = useRoute()
const showNavbar = computed(() => route.path !== '/login')

async function handleLogout() {
  try {
    await authAPI.logout()
  } catch (error) {
    console.error('Logout request failed:', error)
  } finally {
    router.replace('/login')
  }
}
</script>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 48px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

/* FIXED LOGO */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none; /* remove underline */
  color: inherit; /* keep normal text color */
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.logo:hover {
  opacity: 0.8;
}

.logo-img {
  height: 32px;
  width: auto;
  object-fit: contain;
}

.logo-text {
  font-size: 22px;
  font-weight: 700;
  color: #2f4054;
  line-height: 1;
}

.links {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.links a {
  text-decoration: none;
  color: #374151;
  font-size: 16px;
  padding: 8px 14px;
  border-radius: 12px;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.logout-button {
  border: 0;
  background: #0f766e;
  color: #ffffff;
  font-size: 16px;
  padding: 8px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

.logout-button:hover {
  background: #115e59;
  transform: translateY(-1px);
}

.links a:hover {
  background: #ecfdf5;
  color: #16a34a;
}

.links a.router-link-active {
  background: #d1fae5;
  color: #16a34a;
}

@media (max-width: 1024px) {
  .navbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
    padding: 16px 24px;
  }

  .links {
    width: 100%;
    gap: 6px;
  }

  .links a {
    font-size: 15px;
    padding: 7px 12px;
  }

  .logout-button {
    font-size: 15px;
    padding: 7px 12px;
  }
}
</style>
