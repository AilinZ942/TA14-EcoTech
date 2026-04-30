const API_SITE = import.meta.env.VITE_API_SITE

async function request(baseUrl, path, options = {}) {
  const requestOptions = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  }

  const response = await fetch(`${baseUrl}${path}`, requestOptions)

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json()
}

// API
export const api = {

  getHealthAll() {
    return request(API_SITE, '/health/all')
  },


  // Emissions
  getHeavyMetalState() {
    return request(API_SITE, '/emissions/state')
  },

  getHeavyMetalFacility() {
    return request(API_SITE, '/emissions/facility')
  },

  // Disposal locations
  searchDisposalLocations() {
    return request(API_SITE, '/map/disposal-locations')
  }
}
