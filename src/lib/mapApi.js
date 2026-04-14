import disposalCsvUrl from '../public/clean_ewaste_facilities_geocoded.csv?url'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const mapDataMode = normalizeMapDataMode(import.meta.env.VITE_MAP_DATA_MODE)
const disposalApiPath = normalizeApiPath(
  import.meta.env.VITE_DISPOSAL_API_PATH || '/api/map/disposal-locations/search',
)
const allowLegacyGeoJsonFallback = String(import.meta.env.VITE_ENABLE_LEGACY_GEOJSON_FALLBACK || '')
  .trim()
  .toLowerCase() === 'true'

let cachedDisposalCsvRows = null
let cachedLegacyDisposalGeoJsonRows = null

function normalizeMapDataMode(value) {
  const normalized = String(value || 'auto').trim().toLowerCase()
  return ['local', 'azure', 'auto'].includes(normalized) ? normalized : 'auto'
}

function normalizeApiPath(value) {
  const path = String(value || '').trim()
  if (!path) return ''
  return path.startsWith('/') ? path : `/${path}`
}

function parseCsvLine(line) {
  const values = []
  let current = ''
  let inQuotes = false

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index]
    const nextCharacter = line[index + 1]

    if (character === '"') {
      if (inQuotes && nextCharacter === '"') {
        current += '"'
        index += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }

    if (character === ',' && !inQuotes) {
      values.push(current)
      current = ''
      continue
    }

    current += character
  }

  values.push(current)
  return values
}

function parseCsv(text) {
  const lines = String(text || '')
    .split(/\r?\n/)
    .filter((line) => line.trim())

  if (!lines.length) return []

  const headers = parseCsvLine(lines[0]).map((header) => header.trim())

  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line)
    const row = {}

    headers.forEach((header, index) => {
      row[header] = values[index] ?? ''
    })

    return row
  })
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
}

function toNumber(value, fallback = null) {
  if (value == null || value === '') return fallback
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : fallback
}

function toBoolean(value) {
  return String(value || '').trim().toLowerCase() === 'true'
}

function normalizeMapFacilityRow(row = {}, defaults = {}) {
  const latitude = toNumber(row.latitude ?? row.lat)
  const longitude = toNumber(row.longitude ?? row.lng ?? row.lon)
  const duplicateCount = toNumber(row.duplicate_count, 0) ?? 0
  const maptilerScore = toNumber(row.maptiler_match_score)
  const score = toNumber(row.score, maptilerScore)
  const source =
    row.source ||
    row.source_provenance ||
    row.source_file ||
    defaults.source ||
    ''
  const ewasteCategory =
    row.ewaste_category ||
    row.category ||
    row.ewaste_match_text ||
    defaults.ewaste_category ||
    ''
  const coordSource =
    row.coord_source ||
    row.coordinate_source ||
    defaults.coord_source ||
    ''

  return {
    ...row,
    resourceType: row.resourceType || defaults.resourceType || 'disposal',
    facility_name: row.facility_name || row.name || '',
    address: row.address || '',
    suburb: row.suburb || row.city || '',
    postcode: row.postcode == null ? '' : String(row.postcode),
    state: row.state || '',
    source_file: row.source_file || defaults.source_file || '',
    latitude,
    longitude,
    duplicate_count: duplicateCount,
    maptiler_match_score: maptilerScore,
    ewaste_match_flag: typeof row.ewaste_match_flag === 'boolean' ? row.ewaste_match_flag : toBoolean(row.ewaste_match_flag),
    source,
    source_provenance: row.source_provenance || row.source_file || source,
    ewaste_category: ewasteCategory,
    category: row.category || ewasteCategory,
    score,
    coord_source: coordSource,
  }
}

function normalizeGeoJsonRow(feature = {}) {
  const properties = feature?.properties || {}
  const coordinates = feature?.geometry?.coordinates
  const longitude = Array.isArray(coordinates) ? coordinates[0] : null
  const latitude = Array.isArray(coordinates) ? coordinates[1] : null

  return normalizeMapFacilityRow(
    {
      ...properties,
      longitude,
      latitude,
    },
    { source: 'legacy-geojson' },
  )
}

function matchesSearch(row, searchText) {
  const needle = normalizeText(searchText)
  if (!needle) return true

  const haystack = [
    row.facility_name,
    row.address,
    row.suburb,
    row.postcode,
    row.state,
    row.ewaste_category,
    row.source,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

  return haystack.includes(needle)
}

function filterDisposalRows(rows, payload = {}) {
  const state = normalizeText(payload.state || 'VIC')
  const category = normalizeText(payload.category)
  const limit = Number(payload.limit) > 0 ? Number(payload.limit) : rows.length

  return rows
    .filter((row) => {
      if (state && normalizeText(row.state) !== state) return false
      if (category && normalizeText(row.ewaste_category || row.category) !== category) return false
      return matchesSearch(row, payload.searchText)
    })
    .slice(0, limit)
}

async function loadLocalDisposalRows() {
  if (cachedDisposalCsvRows) {
    return cachedDisposalCsvRows
  }

  const csvResponse = await fetch(disposalCsvUrl)
  if (!csvResponse.ok) {
    throw new Error(`Local disposal CSV not found: ${csvResponse.status} ${csvResponse.statusText}`)
  }

  const csvText = await csvResponse.text()
  cachedDisposalCsvRows = parseCsv(csvText).map((row) =>
    normalizeMapFacilityRow(row, {
      resourceType: 'disposal',
      source: row.source || row.source_provenance || row.source_file || 'local-csv',
    }),
  )

  return cachedDisposalCsvRows
}

async function loadLegacyGeoJsonRows() {
  if (cachedLegacyDisposalGeoJsonRows) {
    return cachedLegacyDisposalGeoJsonRows
  }

  const response = await fetch('/clean_ewaste_facilities.geojson')
  if (!response.ok) {
    throw new Error(`Legacy disposal GeoJSON not found: ${response.status} ${response.statusText}`)
  }

  const payload = await response.json()
  const features = Array.isArray(payload?.features) ? payload.features : []
  cachedLegacyDisposalGeoJsonRows = features.map(normalizeGeoJsonRow)
  return cachedLegacyDisposalGeoJsonRows
}

async function searchLocalDisposalFacilities(payload = {}) {
  const rows = await loadLocalDisposalRows()
  return {
    items: filterDisposalRows(rows, payload),
    meta: {
      pipeline: 'local',
      mode: mapDataMode,
      source: 'csv',
    },
  }
}

function buildDisposalApiUrl() {
  if (!apiBaseUrl || !disposalApiPath) return ''
  return `${apiBaseUrl}${disposalApiPath}`
}

function normalizeDisposalResponse(payload) {
  const items = Array.isArray(payload?.items)
    ? payload.items
    : Array.isArray(payload)
      ? payload
      : []

  return {
    items: items.map((row) =>
      normalizeMapFacilityRow(row, {
        resourceType: 'disposal',
        source: row?.source || 'azure-api',
      }),
    ),
    meta: {
      pipeline: 'azure',
      mode: mapDataMode,
      source: payload?.meta?.source || 'api',
      ...payload?.meta,
    },
  }
}

async function searchAzureDisposalFacilities(payload = {}, options = {}) {
  const disposalApiUrl = buildDisposalApiUrl()
  if (!disposalApiUrl) {
    throw new Error('Azure disposal API is not configured')
  }

  const response = await fetch(disposalApiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...payload,
      resourceType: 'disposal',
    }),
    signal: options.signal,
  })

  if (!response.ok) {
    let message = `Request failed: ${response.status} ${response.statusText}`

    try {
      const errorPayload = await response.json()
      if (errorPayload?.error) {
        message = errorPayload.error
      }
    } catch {
      // Keep the HTTP fallback message when the error response is not JSON.
    }

    throw new Error(message)
  }

  const responsePayload = await response.json()
  return normalizeDisposalResponse(responsePayload)
}

async function searchDisposalFacilities(payload = {}, options = {}) {
  if (mapDataMode === 'local') {
    return searchLocalDisposalFacilities(payload)
  }

  if (mapDataMode === 'azure') {
    return searchAzureDisposalFacilities(payload, options)
  }

  try {
    return await searchAzureDisposalFacilities(payload, options)
  } catch (error) {
    const fallbackResponse = await searchLocalDisposalFacilities(payload)
    return {
      ...fallbackResponse,
      meta: {
        ...fallbackResponse.meta,
        fallbackReason: error instanceof Error ? error.message : 'Azure disposal request failed',
      },
    }
  }
}

async function searchLegacyGeoJsonDisposalFacilities(payload = {}) {
  const rows = await loadLegacyGeoJsonRows()

  return {
    items: filterDisposalRows(rows, payload),
    meta: {
      pipeline: 'legacy-geojson',
      mode: mapDataMode,
      source: 'geojson',
    },
  }
}

export async function searchMapFacilities(payload, options = {}) {
  if (payload?.resourceType === 'disposal') {
    try {
      return await searchDisposalFacilities(payload, options)
    } catch (error) {
      if (!allowLegacyGeoJsonFallback) {
        throw error
      }

      return searchLegacyGeoJsonDisposalFacilities(payload)
    }
  }

  const response = await fetch(`${apiBaseUrl}/api/map/facilities/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal: options.signal,
  })

  if (!response.ok) {
    let message = `Request failed: ${response.status} ${response.statusText}`

    try {
      const errorPayload = await response.json()
      if (errorPayload?.error) {
        message = errorPayload.error
      }
    } catch {
      // Keep the HTTP fallback message when the error response is not JSON.
    }

    throw new Error(message)
  }

  return response.json()
}
