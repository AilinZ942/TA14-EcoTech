const API_SITE = '/api'
const TEMP_MAP_PREVIEW = import.meta.env.DEV && import.meta.env.VITE_TEMP_MAP_PREVIEW === '1'

import { ref } from 'vue'
const csrfToken = ref('')
export async function initCSRF() {
  try {
    const response = await fetch(`${API_SITE}/csrf-token`)
    const data = await response.json()
    csrfToken.value = data.csrf_token
    console.log('CSRF token initialized.')
  } catch (error) {
    console.error('failed to initialize CSRF token:', error)
  }
}

async function request(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
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
// Chengwei's work - authentication endpoints
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

  // Xiaoyao's work - health matrix endpoints
  getHealthAll() {
    return request(API_SITE, '/health/all')
  },

  // Jashwanth's work - health endpoints
  getHealthAll_2() {
    return request(API_SITE, '/health/all_2')
  },
  
  getHealthFilter() {
    return request(API_SITE, '/health/filters')
  },
  
  getHeavyMetalState() {
    return request(API_SITE, '/emissions/state')
  },
  
  getHeavyMetalFacility() {
    return request(API_SITE, '/emissions/facility')
  },

  

  //Xiaoyao's work - map endpoints
  searchDisposalLocation(options = {}) {
    if (TEMP_MAP_PREVIEW) {
      return import('./tempMapPreview').then(({ getTempMapPreview }) =>
        getTempMapPreview(options.searchText, options.searchRange),
      )
    }

    const { searchText, searchRange, ...fetchOptions } = options
    const params = new URLSearchParams()
    if (searchText) params.set('searchText', searchText)
    if (searchRange) params.set('searchRange', searchRange)
    const suffix = params.toString() ? `?${params}` : ''

    return request(API_SITE, `/map/disposal-locations${suffix}`, fetchOptions)
  },

  // Chengwei's work - device optimization endpoints
  getDeviceOptimizationTips(payload) {
    return request(API_SITE, '/ai/device-optimizer', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
