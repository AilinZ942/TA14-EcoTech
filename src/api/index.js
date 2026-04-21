const API_BASE =
  import.meta.env.VITE_API_BASE ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000/api'

async function request(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json'

    },
    
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `API request failed: ${response.status}`)
  }

  return response.json()
}

// API
export const api = {
  // Health
  getHealthAll() {
    return request('/health/all')
  },

  // Emissions
  getHeavyMetalState() {
    return request('/emissions/state')
  },

  getHeavyMetalFacility() {
    return request('/emissions/facility')
  },

  // Disposal locations
  searchDisposalLocations(params = {}) {
    const query = new URLSearchParams()

    if (params.suburb) query.append('suburb', params.suburb)
    if (params.postcode) query.append('postcode', params.postcode)
    if (params.state) query.append('state', params.state)
    if (params.limit) query.append('limit', params.limit)

    const qs = query.toString()
    return request(`/map/disposal-locations/search${qs ? `?${qs}` : ''}`)
  },

  getDisposalLocationsByPostcode(postcode) {
    return request(`/map/disposal-locations/${postcode}`)
  },

  getPerson() {
    return request('/getperson')
  },
}