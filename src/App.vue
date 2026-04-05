<template>
  <nav class="navbar">
    <div class="logo">
      <span class="icon">♻</span>
      EcoTech
    </div>
    <div class="links">
      <router-link to="/">Home</router-link>
      <router-link to="/dashboard">Dashboard</router-link>
      <router-link to="/repair-check">Repair Check</router-link>
      <router-link to="/extend-usage">Extend Usage</router-link>
      <router-link to="/ai-chat">AI Chat</router-link>
      <router-link to="/safe-guidance">Safe Guidance</router-link>
      <router-link to="/disposal-locations">Disposal Locations</router-link>
    </div>
  </nav>

  <router-view />
</template>

<script setup></script>

<style scoped>
header {
  line-height: 1.5;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 60px;
  background: #ffffff;
  border-bottom: 1px solid #eee;
}

.logo {
  font-weight: 600;
  font-size: 22px;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  color: #16a34a;
  font-size: 24px;
}

.links a {
  margin: 0 12px;
  text-decoration: none;
  color: #374151;
  font-size: 16px;
  padding: 6px 12px;
  border-radius: 10px;
  transition: 0.2s;
}

.links a:hover {
  background: #ecfdf5;
}

.links a.router-link-active {
  background: #d1fae5;
  color: #16a34a;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>
