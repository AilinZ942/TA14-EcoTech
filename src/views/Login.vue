<template>
  <div class="login-page">
    <form class="login-card" @submit.prevent="handleLogin">
      <h2>Login</h2>
      <input v-model="username" type="text" placeholder="username" required />
      <input v-model="password" type="password" placeholder="password" required />
      <button type="submit">Login</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI } from '@/api'

export default {
  setup() {
    const router = useRouter()
    const route = useRoute()
    const username = ref('')
    const password = ref('')
    const error = ref('')

    const handleLogin = async () => {
      try {
        const result = await authAPI.login(username.value, password.value)
        if (result.success) {
          const redirectPath = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
          router.replace(redirectPath)
        } else {
          error.value = result.message
          console.error(result.message)
        }
      } catch (err) {
        error.value = err?.data?.message || err?.message || 'Login failed, please try again'
        console.error(err)
      }
    }

    return { username, password, error, handleLogin }
  },
}
</script>

<style scoped>
.login-page {
  min-height: calc(100vh - 92px);
  display: grid;
  place-items: center;
  padding: 32px;
  background:
    radial-gradient(circle at top left, rgba(16, 185, 129, 0.14), transparent 34%),
    radial-gradient(circle at bottom right, rgba(20, 184, 166, 0.12), transparent 30%),
    linear-gradient(180deg, #f8fbf8 0%, #eef7f1 100%);
}

.login-card {
  width: min(100%, 420px);
  position: relative;
  overflow: hidden;
  padding: 34px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow:
    0 24px 60px rgba(15, 23, 42, 0.12),
    0 2px 8px rgba(15, 23, 42, 0.04);
  backdrop-filter: blur(14px);
}

.login-card::before {
  content: '';
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 5px;
  background: linear-gradient(90deg, #10b981, #0f766e, #22c55e);
}

.login-card h2 {
  margin: 6px 0 24px;
  color: #17352d;
  font-size: 2rem;
  letter-spacing: -0.03em;
}

.login-card input {
  width: 100%;
  border: 1px solid #d6e2dc;
  background: #f8fffb;
  color: #102620;
  border-radius: 16px;
  padding: 14px 16px;
  font-size: 1rem;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease,
    background-color 0.2s ease;
}

.login-card input + input {
  margin-top: 14px;
}

.login-card input::placeholder {
  color: #8b9a95;
}

.login-card input:focus {
  border-color: #10b981;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.14);
  transform: translateY(-1px);
}

.login-card button {
  width: 100%;
  margin-top: 18px;
  border: 0;
  border-radius: 16px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #10b981, #0f766e);
  color: #ffffff;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  cursor: pointer;
  box-shadow: 0 16px 30px rgba(15, 118, 110, 0.22);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    filter 0.2s ease;
}

.login-card button:hover {
  transform: translateY(-1px);
  box-shadow: 0 20px 34px rgba(15, 118, 110, 0.28);
  filter: brightness(1.03);
}

.login-card button:active {
  transform: translateY(0);
}

.error {
  margin: 14px 0 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.16);
  color: #b91c1c;
  line-height: 1.5;
}

@media (max-width: 640px) {
  .login-page {
    padding: 20px;
  }

  .login-card {
    padding: 24px;
    border-radius: 22px;
  }

  .login-card h2 {
    font-size: 1.7rem;
    margin-bottom: 20px;
  }
}
</style>
