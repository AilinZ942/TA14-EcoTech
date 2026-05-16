<template>
  <div class="login">
    <div class="login-bg" aria-hidden="true">
      <div class="orb orb-1" />
      <div class="orb orb-2" />
    </div>

    <div class="login-grid">
      <aside class="brand-side">
        <div class="brand-mark">
          <img :src="logoImage" alt="EcoReviva logo" class="login-logo" />
          <span>EcoReviva</span>
        </div>
        <h1>
          Give old<br />electronics<br /><em>a second life.</em>
        </h1>
        <p>The Victorian platform for repair, reuse, and safe e-waste disposal.</p>

        <ul class="bullets">
          <li><span>01</span> Find pickup stalls across Australia</li>
          <li><span>02</span> Get a clear repair-or-replace verdict</li>
          <li><span>03</span> Learn the real health impact</li>
        </ul>
      </aside>

      <form class="card" @submit.prevent="handleLogin">
        <span class="eco-eyebrow">Sign in</span>
        <h2>Welcome back.</h2>
        <p class="hint">Use your team credentials to continue.</p>

        <label>
          Username
          <input v-model="username" type="text" placeholder="admin" autocomplete="username" required />
        </label>
        <label>
          Password
          <input v-model="password" type="password" placeholder="••••••••" autocomplete="current-password" required />
        </label>

        <button type="submit" :disabled="busy" class="submit">
          <span v-if="!busy">Continue <span class="arrow">→</span></span>
          <span v-else class="spinner" />
        </button>

        <p v-if="error" class="error">{{ error }}</p>
        <p class="muted">Demo: <code>admin</code> / <code>password</code></p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI } from '@/api'
import logoImage from '@/assets/icons/ecoreviva-logo.png'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function handleLogin() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    const result = await authAPI.login(username.value, password.value)
    if (result.success) {
      const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
      router.replace(redirect)
    } else {
      error.value = result.message || 'Login failed.'
    }
  } catch (err) {
    error.value = err?.data?.message || err?.message || 'Login failed, please try again.'
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.login {
  position: relative;
  min-height: 100vh;
  padding: 60px 24px;
  display: grid;
  place-items: center;
  overflow: hidden;
}
.login-bg { position: absolute; inset: 0; pointer-events: none; }
.orb { position: absolute; border-radius: 50%; filter: blur(110px); opacity: 0.3; }
.orb-1 { width: 540px; height: 540px; top: -120px; left: -100px; background: var(--mint); }
.orb-2 { width: 460px; height: 460px; bottom: -100px; right: -100px; background: var(--violet); opacity: 0.2; }

.login-grid {
  position: relative;
  z-index: 2;
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: 1.2fr 0.9fr;
  gap: 80px;
  align-items: center;
}

.brand-side { display: flex; flex-direction: column; gap: 28px; }
.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
}
.login-logo {
  width: 42px;
  height: 50px;
  object-fit: contain;
  padding: 4px;
  border: 1px solid var(--hairline-strong);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  filter: drop-shadow(0 10px 18px rgba(16, 185, 129, 0.22));
}
.brand-side h1 {
  font-family: var(--font-display);
  font-size: clamp(40px, 6vw, 72px);
  line-height: 1;
  font-weight: 500;
  letter-spacing: -0.04em;
  color: var(--ink-0);
}
.brand-side h1 em {
  font-style: italic;
  background: linear-gradient(120deg, var(--mint), var(--mint-bright) 60%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.brand-side > p { color: var(--ink-1); font-size: 16px; max-width: 440px; }

.bullets { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 14px; }
.bullets li {
  display: flex; align-items: center; gap: 14px;
  color: var(--ink-1);
  font-size: 14px;
}
.bullets li span {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--mint);
  letter-spacing: 0.18em;
}

.card {
  background: var(--surface);
  border: 1px solid var(--hairline);
  border-radius: var(--r-lg);
  padding: 36px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  backdrop-filter: blur(20px);
}
.card h2 {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 500;
  letter-spacing: -0.02em;
  color: var(--ink-0);
}
.hint { color: var(--ink-2); font-size: 14px; margin-bottom: 8px; }

label {
  display: flex; flex-direction: column; gap: 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-2);
}
input {
  width: 100%;
  padding: 14px 16px;
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--hairline);
  border-radius: var(--r-sm);
  color: var(--ink-0);
  font-family: var(--font-body);
  font-size: 15px;
  outline: none;
  text-transform: none; letter-spacing: 0;
  transition: border-color 0.3s, box-shadow 0.3s;
}
input::placeholder { color: var(--ink-3); }
input:focus { border-color: var(--mint); box-shadow: 0 0 0 4px rgba(125,216,176,0.12); }

.submit {
  margin-top: 8px;
  padding: 16px 20px;
  border: 0;
  border-radius: var(--r-sm);
  background: var(--mint);
  color: var(--ink-on-light);
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s var(--ease-out);
}
.submit:hover:not(:disabled) {
  background: var(--mint-bright);
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(125,216,176,0.3);
}
.submit:disabled { opacity: 0.7; cursor: progress; }
.submit .arrow { display: inline-block; margin-left: 6px; transition: transform 0.3s; }
.submit:hover .arrow { transform: translateX(4px); }

.spinner {
  width: 18px; height: 18px;
  border-radius: 50%;
  border: 2px solid rgba(0,0,0,0.2);
  border-top-color: var(--ink-on-light);
  animation: sp 0.7s linear infinite;
}
@keyframes sp { to { transform: rotate(360deg); } }

.error {
  margin: 4px 0 0;
  padding: 12px 14px;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.25);
  color: var(--bad);
  font-size: 13px;
  border-radius: var(--r-sm);
}
.muted { color: var(--ink-3); font-size: 12px; }
.muted code {
  background: rgba(125, 216, 176, 0.1);
  color: var(--mint);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
}

@media (max-width: 880px) {
  .login-grid { grid-template-columns: 1fr; gap: 40px; }
}
</style>
