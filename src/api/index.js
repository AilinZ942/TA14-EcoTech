const apiSiteBaseUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_SITE || '')

// Normalizes the API base URL by trimming whitespace, removing trailing slashes, and stripping any trailing '/api' segment.
function normalizeApiBaseUrl(value) {
  let normalized = String(value || '').trim().replace(/\/$/, '')
  if (!normalized) return ''

  if (normalized.endsWith('/api')) {
    normalized = normalized.slice(0, -4)
  }

  return normalized
}

// Parses the error response from the API, attempting to extract a meaningful error message from the JSON body if available.
async function parseErrorResponse(response) {
  let message = `HTTP error! status: ${response.status}`

  try {
    const payload = await response.json()
    if (payload?.error) {
      message = payload.error
    }
  } catch {
    // Keep the fallback HTTP error when the body is not JSON.
  }

  return message
}

// Constructs the full API URL by combining the base URL with the provided path, ensuring proper formatting.

function buildApiUrl(path) {
  if (!apiSiteBaseUrl) {
    throw new Error('API site URL is not configured. Set VITE_API_SITE in .env.local.')
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${apiSiteBaseUrl}${normalizedPath}`
}

async function requestJson(path, options = {}) {
  const response = await fetch(buildApiUrl(path), options)
  if (!response.ok) {
    throw new Error(await parseErrorResponse(response))
  }

  return response.json()
}

// API
export const api = {

  getMapLocation: async (postcode) => {
    if (typeof postcode !== 'string') {
      throw new Error('Parameter must be a string')
    }

    return requestJson(`/api/map/disposal-locations/${postcode}`)
  },

  searchDisposalLocations: async (payload = {}, options = {}) => {
    return requestJson('/api/map/disposal-locations/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: options.signal,
    })
  },
}