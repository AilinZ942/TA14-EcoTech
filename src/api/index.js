const API_SITE = 'http://localhost:8000/api' //Server URL from environment variable




import { ref } from 'vue';
const csrfToken = ref('');
export async function initCSRF() {
  try {
    const response = await fetch(`${API_SITE}/csrf-token`, {
      credentials: 'include'
    });
    const data = await response.json();
    csrfToken.value = data.csrf_token;
    console.log('CSRF token initialized.');
  } catch (error) {
    console.error('failed to initialize CSRF token:', error);
  }
}

async function request(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken.value,
      ...(options.headers || {}),
    },
  })

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const error = new Error(data?.message || data?.detail || `API request failed: ${response.status}`)
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export const authAPI = {
  login(username, password) {
    return request(API_SITE, '/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },

  logout() {
    return request(API_SITE, '/logout', {
      method: 'POST',
    })
  },

  checkAuth() {
    return request(API_SITE, '/check-auth', {
      method: 'GET',
    })
  },
}

export const api = {
  getHeavyMetalState() {
    return request(API_SITE, '/emissions/state')
  },

  getHeavyMetalFacility() {
    return request(API_SITE, '/emissions/facility')
  },

  searchDisposalLocations() {
    return request(API_SITE, '/map/disposal-locations')
  },

  getDeviceOptimizationTips(payload) {
    return request(API_SITE, '/ai/device-optimizer', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
