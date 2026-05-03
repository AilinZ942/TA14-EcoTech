<template>
  <nav v-if="showNavbar" class="navbar">
    <!-- FULL logo clickable -->
    <router-link to="/" class="logo">
      <img src="@/assets/icons/logo test.png" alt="EcoTech Logo" class="logo-img" />
      <span class="logo-text">EcoReviva</span>
    </router-link>

    <div class="links">
      <router-link to="/">Home</router-link>
      <router-link to="/dashboard">Dashboard</router-link>
      <!--<router-link to="/repair-check">Repair Check</router-link> -->
      <router-link to="/game">Sorting Game</router-link>
      <!--<router-link to="/extend-usage">Extend Usage</router-link> -->
      <router-link to="/ai-chat">AI Device Optimizer</router-link>
      <!--<router-link to="/safe-guidance">Safe Guidance</router-link>-->
      <router-link to="/disposal-locations">Disposal Locations</router-link>
      <button type="button" class="logout-button" @click="handleLogout">Logout</button>
    </div>
  </nav>

  <router-view />

  <footer class="footer">
    <p>© 2026 EcoReviva</p>
    <p>Promoting sustainable e-waste management</p>
  </footer>
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
  background: #2d6a4f;
  border-bottom: 1px solid #24553f;
}

.navbar a {
  font-weight: 600;
  color: #f0fdf4;
}

/* LOGO */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.logo:hover {
  opacity: 0.85;
}

.logo-img {
  height: 32px;
  width: auto;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.logo-text {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1;
}

/* LINKS */
.links {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.links a {
  text-decoration: none;
  color: #f0fdf4;
  font-size: 16px;
  padding: 8px 14px;
  border-radius: 12px;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

/* hover */
.links a:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  transform: translateY(-1px);
}

/* active  */
.links a.router-link-active {
  background: #d8f3dc;
  color: #1b4332;
  font-weight: 700;
}

/* logout */
.logout-button {
  border: none;
  background: #ffffff;
  color: #2d6a4f;
  font-size: 16px;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 14px;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

/* logout hover */
.logout-button:hover {
  background: #d8f3dc;
  color: #1b4332;
  transform: translateY(-1px);
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

.footer {
  text-align: center;
  padding: 20px 0;
  font-size: 14px;
  color: #6b7280;
  margin-top: 20px;
}
</style>
