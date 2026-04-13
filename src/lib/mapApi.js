import disposalCsvUrl from '../public/clean_ewaste_facilities_geocoded.csv?url'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

let cachedDisposalGeoJson = null
let cachedDisposalCsvRows = null

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

function normalizeGeoJsonRow(feature = {}) {
  const properties = feature?.properties || {}
  const coordinates = feature?.geometry?.coordinates
  const longitude = Array.isArray(coordinates) ? coordinates[0] : null
  const latitude = Array.isArray(coordinates) ? coordinates[1] : null

  return {
    ...properties,
    longitude,
    latitude,
  }
}

function normalizeCsvRow(row = {}) {
  return {
    ...row,
    latitude: row.latitude ? Number(row.latitude) : null,
    longitude: row.longitude ? Number(row.longitude) : null,
    duplicate_count: row.duplicate_count ? Number(row.duplicate_count) : 0,
    maptiler_match_score: row.maptiler_match_score ? Number(row.maptiler_match_score) : null,
    ewaste_match_flag: String(row.ewaste_match_flag || '').toLowerCase() === 'true',
    source: row.source || row.source_provenance || row.source_file || '',
    ewaste_category: row.ewaste_category || row.ewaste_match_text || '',
  }
}

function normalizeText(value) {
  return String(value || '').trim().toLowerCase()
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

async function loadStaticDisposalRows() {
  if (cachedDisposalCsvRows) {
    return cachedDisposalCsvRows
  }

  try {
    const csvResponse = await fetch(disposalCsvUrl)
    if (csvResponse.ok) {
      const csvText = await csvResponse.text()
      cachedDisposalCsvRows = parseCsv(csvText).map(normalizeCsvRow)
      return cachedDisposalCsvRows
    }
  } catch {
    // Fall through to the GeoJSON fallback below.
  }

  if (cachedDisposalGeoJson) {
    return cachedDisposalGeoJson
  }

  const response = await fetch('/clean_ewaste_facilities.geojson')
  if (!response.ok) {
    throw new Error(`Static facility data not found: ${response.status} ${response.statusText}`)
  }

  const payload = await response.json()
  const features = Array.isArray(payload?.features) ? payload.features : []
  cachedDisposalGeoJson = features.map(normalizeGeoJsonRow)
  return cachedDisposalGeoJson
}

async function searchStaticDisposalFacilities(payload = {}) {
  const rows = await loadStaticDisposalRows()
  const state = normalizeText(payload.state)
  const category = normalizeText(payload.category)
  const limit = Number(payload.limit) > 0 ? Number(payload.limit) : rows.length

  const items = rows
    .filter((row) => {
      if (state && normalizeText(row.state) !== state) return false
      if (category && normalizeText(row.ewaste_category) !== category) return false
      return matchesSearch(row, payload.searchText)
    })
    .slice(0, limit)

  return { items }
}

export async function searchMapFacilities(payload, options = {}) {
  const shouldUseStaticFallback = !apiBaseUrl && payload?.resourceType !== 'repair'

  if (shouldUseStaticFallback) {
    return searchStaticDisposalFacilities(payload)
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

    if (payload?.resourceType !== 'repair' && (response.status === 404 || response.status >= 500)) {
      return searchStaticDisposalFacilities(payload)
    }

    throw new Error(message)
  }

  return response.json()
}
