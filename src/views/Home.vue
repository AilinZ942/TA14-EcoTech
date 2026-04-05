<template>
  <div class="home">
    <!-- Navbar -->
    <header class="navbar">
      <div class="logo-section">
        <span class="logo">♻</span>
        <span class="brand">EcoTech</span>
      </div>

      <nav class="nav-links">
        <router-link to="/" class="nav-item active">Home</router-link>
        <router-link to="/dashboard" class="nav-item">Dashboard</router-link>
        <router-link to="/repair-check" class="nav-item">Repair Check</router-link>
        <router-link to="/extend-usage" class="nav-item">Extend Usage</router-link>
        <router-link to="/ai-chat" class="nav-item">AI Chat</router-link>
        <router-link to="/safe-guidance" class="nav-item">Safe Guidance</router-link>
        <router-link to="/disposal" class="nav-item">Disposal Locations</router-link>
      </nav>
    </header>

    <!-- Hero -->
    <section class="hero">
      <img :src="heroImg" class="hero-img" />
      <div class="overlay"></div>

      <div class="hero-text">
        <h1>Welcome to EcoTech</h1>
        <p>
          We are dedicated to reducing electronic waste and promoting sustainable technology
          practices.
        </p>
      </div>
    </section>

    <!-- Intro -->
    <section class="intro">
      <p>
        Our platform helps you extend the life of your devices, provides guidance on proper
        disposal, and connects you with resources for environmentally conscious tech usage.
      </p>
    </section>

    <!-- Feature Cards -->
    <section class="features">
      <router-link to="/repair-check" class="card-link">
        <div class="card">
          <div class="card-top green">
            <div class="icon-box">
              <span class="icon">📱</span>
            </div>
            <h3>Device Assessment</h3>
          </div>
          <p class="card-text">Check if your device can be repaired instead of replaced.</p>
        </div>
      </router-link>

      <router-link to="/extend-usage" class="card-link">
        <div class="card">
          <div class="card-top blue">
            <div class="icon-box">
              <span class="icon">💻</span>
            </div>
            <h3>Usage Tips</h3>
          </div>
          <p class="card-text">Learn how to extend your device lifespan.</p>
        </div>
      </router-link>

      <router-link to="/dashboard" class="card-link">
        <div class="card">
          <div class="card-top purple">
            <div class="icon-box">
              <span class="icon">⚡</span>
            </div>
            <h3>E-Waste Impact</h3>
          </div>
          <p class="card-text">Understand environmental impact of e-waste.</p>
        </div>
      </router-link>
    </section>

    <!-- Mission -->
    <section class="mission">
      <div class="mission-card">
        <h2>Our Mission</h2>

        <p class="mission-sub">
          Electronic waste is one of the fastest-growing waste streams in the world. Millions of
          tons end up in landfills each year.
        </p>

        <p class="mission-main">
          We provide tools to help users make better decisions, from repair to safe disposal.
          Together, we can build a sustainable future.
        </p>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">© 2026 EcoTech. Reducing e-waste, one device at a time.</footer>
  </div>
</template>

<script setup>
import heroImg from '@/assets/e-waste.png'
</script>

<style scoped>
.home {
  background: #f7f7f7;
  font-family: Arial, sans-serif;
}

.navbar {
  display: flex;
  justify-content: space-between;
  padding: 16px 32px;
  background: white;
  border-bottom: 1px solid #eee;
}

.logo-section {
  display: flex;
  gap: 8px;
  align-items: center;
}

.logo {
  color: green;
  font-size: 24px;
}

.brand {
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 12px;
}

.nav-item {
  text-decoration: none;
  color: #333;
  padding: 8px 14px;
  border-radius: 10px;
}

.nav-item.active {
  background: #dcfce7;
  color: green;
}

.hero {
  position: relative;
  height: 450px;
  border-radius: 16px;
  overflow: hidden;
  margin: 20px;
}

.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
}

.hero-text {
  position: absolute;
  bottom: 30px;
  left: 30px;
  color: white;
}

.hero-text h1 {
  font-size: 40px;
}

.intro {
  text-align: center;
  padding: 30px 80px;
  color: #555;
}

.features {
  display: flex;
  gap: 24px;
  padding: 20px 40px;
  align-items: stretch;
}

.card-link {
  flex: 1;
  text-decoration: none;
  color: inherit;
}

.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: 0.2s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.card-top {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  min-height: 56px;
}

.card-top h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #334155;
}

.icon-box {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon {
  font-size: 22px;
  line-height: 1;
}

.card-text {
  margin: 0;
  font-size: 16px;
  line-height: 1.5;
  color: #475569;
}

.green {
  background: #dcfce7;
}

.blue {
  background: #dbeafe;
}

.purple {
  background: #f3e8ff;
}

.mission {
  padding: 24px 40px 40px;
}

.mission-card {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 16px;
  padding: 32px 40px;
}

.mission-card h2 {
  margin: 0 0 16px;
  font-size: 28px;
  font-weight: 600;
  color: #334155;
}

.mission-main {
  margin: 0 0 12px;
  font-size: 18px;
  line-height: 1.6;
  color: #475569;
}

.mission-sub {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  color: #64748b;
}

.footer {
  text-align: center;
  padding: 20px;
  color: #666;
}
</style>
