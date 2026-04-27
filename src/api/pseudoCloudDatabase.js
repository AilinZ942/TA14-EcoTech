import cleanEwasteCsv from '../../data_for_map/clean_ewaste_facilities_geocoded.csv?raw'
import curatedRecyclingCsv from '../../data_for_map/ewaste_recycling_locations_curated.csv?raw'
import { getNearbyCouncilFallbacks, resolveLocationQuery } from '../lib/locationLookup'

const TRUE_VALUES = new Set(['true', '1', 'yes', 'y'])
const FALSE_VALUES = new Set(['false', '0', 'no', 'n'])
const NEARBY_COUNCIL_FALLBACK_KM = 100

function parseCsv(text) {
  const rows = []
  let row = []
  let value = ''
  let inQuotes = false

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index]
    const nextChar = text[index + 1]

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        value += '"'
        index += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }

    if (char === ',' && !inQuotes) {
      row.push(value)
      value = ''
      continue
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && nextChar === '\n') index += 1
      row.push(value)
      if (row.some((cell) => cell !== '')) rows.push(row)
      row = []
      value = ''
      continue
    }

    value += char
  }

  row.push(value)
  if (row.some((cell) => cell !== '')) rows.push(row)

  const headers = rows.shift()?.map((header) => header.trim()) || []
  return rows.map((cells) =>
    Object.fromEntries(headers.map((header, index) => [header, cells[index]?.trim() || ''])),
  )
}

function toBoolean(value) {
  const normalized = String(value || '').trim().toLowerCase()
  if (TRUE_VALUES.has(normalized)) return true
  if (FALSE_VALUES.has(normalized)) return false
  return null
}

function cleanText(value) {
  return String(value || '').trim()
}

function cleanNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function normalizeSearchTerm(value) {
  return cleanText(value).toUpperCase()
}

function normalizeCleanEwasteRow(row, index) {
  return {
    ...row,
    id: `clean-${row.dedupe_key || index}`,
    facility_name: cleanText(row.facility_name),
    address: cleanText(row.address),
    suburb: cleanText(row.suburb),
    postcode: cleanText(row.postcode),
    state: cleanText(row.state).toUpperCase(),
    latitude: cleanNumber(row.latitude),
    longitude: cleanNumber(row.longitude),
    source: 'clean_ewaste_facilities_geocoded',
    source_table: 'clean_ewaste_facilities_geocoded',
  }
}

function normalizeCuratedRow(row, index) {
  const acceptedItems = cleanText(row.corrected_accepted_items || row.accepted_items)
  const sourceType = cleanText(row.corrected_source_type || row.source_type)

  return {
    ...row,
    id: `curated-${row.place_id || index}`,
    facility_name: cleanText(row.display_name || row.provider_name || `Curated location ${index + 1}`),
    address: cleanText(row.formatted_address || row.suburb),
    suburb: cleanText(row.suburb),
    postcode: cleanText(row.postcode),
    state: cleanText(row.state || row.state_scope).toUpperCase(),
    latitude: cleanNumber(row.latitude),
    longitude: cleanNumber(row.longitude),
    ewaste_category: sourceType,
    ewaste_match_text: acceptedItems,
    ewaste_match_column: sourceType,
    coord_source: 'google_places_curated',
    source: 'ewaste_recycling_locations_curated',
    source_table: 'ewaste_recycling_locations_curated',
    source_file: 'ewaste_recycling_locations_curated.csv',
    website_uri: cleanText(row.website_uri),
    google_maps_uri: cleanText(row.google_maps_uri),
    accepted_items: acceptedItems,
    confidence_score: cleanNumber(row.confidence_score),
  }
}

function isUsableMapRow(row) {
  return Number.isFinite(row.latitude) && Number.isFinite(row.longitude) && Boolean(row.state)
}

function rowSearchText(row) {
  return [
    row.facility_name,
    row.display_name,
    row.provider_name,
    row.address,
    row.formatted_address,
    row.suburb,
    row.postcode,
    row.state,
    row.accepted_items,
    row.ewaste_match_text,
  ]
    .filter(Boolean)
    .join(' ')
    .toUpperCase()
}

function rowCategoryText(row) {
  return [
    row.ewaste_category,
    row.ewaste_match_text,
    row.ewaste_match_column,
    row.facility_name,
    row.source_file,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function rowMatchesCategory(row, category) {
  if (!category) return true

  const text = rowCategoryText(row)
  if (category === 'battery_recycling') return text.includes('battery')
  if (category === 'drop_off') {
    return (
      text.includes('drop off') ||
      text.includes('drop-off') ||
      text.includes('officeworks') ||
      text.includes('harvey norman') ||
      text.includes('domayne') ||
      text.includes('retail_in_store')
    )
  }
  if (category === 'e_waste_recycling') {
    return text.includes('recycling') || text.includes('resource recovery') || text.includes('recycle')
  }
  return text.includes(category.replaceAll('_', ' '))
}

function buildFocusArea({ type = 'none', label = '', query = '', fallbackLevel = 'none', bounds = null } = {}) {
  return { type, label, query, fallbackLevel, bounds }
}

function filterRowsWithFallback(rows, params = {}) {
  const rawQuery = cleanText(params.searchText || params.suburb || params.postcode)
  const location = resolveLocationQuery(rawQuery)
  const category = cleanText(params.category)
  const categoryRows = rows.filter((row) => rowMatchesCategory(row, category))

  if (location.matchType === 'none') {
    return {
      rows: categoryRows,
      focusArea: buildFocusArea(),
      fallbackMessage: '',
      location,
    }
  }

  if (location.matchType === 'unknown') {
    return filterUnknownLocation(categoryRows, rawQuery, location)
  }

  if (location.matchType === 'state') {
    const stateRows = rowsMatchingState(categoryRows, location.stateCode)
    return {
      rows: stateRows,
      focusArea: buildFocusArea({
        type: 'state',
        label: location.stateName,
        query: rawQuery,
        fallbackLevel: 'state',
        bounds: location.stateBounds,
      }),
      fallbackMessage: '',
      location,
    }
  }

  if (location.matchType === 'council') {
    const councilRows = rowsMatchingCouncil(categoryRows, location)
    if (councilRows.length) {
      return {
        rows: councilRows,
        focusArea: buildFocusArea({
          type: 'lga',
          label: location.council,
          query: rawQuery,
          fallbackLevel: 'council',
          bounds: location.councilBounds,
        }),
        fallbackMessage: '',
        location,
      }
    }

    return fallbackToNearbyCouncilOrState(categoryRows, location, rawQuery)
  }

  const exactRows = rowsMatchingExactPlace(categoryRows, location)
  if (exactRows.length) {
    return {
      rows: exactRows,
      focusArea: buildFocusArea({
        type: location.matchType,
        label: location.label,
        query: rawQuery,
        fallbackLevel: 'exact',
        bounds: location.councilBounds,
      }),
      fallbackMessage: '',
      location,
    }
  }

  const councilRows = rowsMatchingCouncil(categoryRows, location)
  if (councilRows.length) {
    return {
      rows: councilRows,
      focusArea: buildFocusArea({
        type: 'lga',
        label: location.council,
        query: rawQuery,
        fallbackLevel: 'council',
        bounds: location.councilBounds,
      }),
      fallbackMessage: `No exact recycling services were found in ${location.label}. Showing services in ${location.council}.`,
      location,
    }
  }

  return fallbackToNearbyCouncilOrState(categoryRows, location, rawQuery)
}

function filterUnknownLocation(categoryRows, rawQuery, location) {
  const query = normalizeSearchTerm(rawQuery)
  const broaderTextRows = categoryRows.filter((row) => rowSearchText(row).includes(query))
  if (broaderTextRows.length) {
    return {
      rows: broaderTextRows,
      focusArea: buildFocusArea({
        type: 'search',
        label: titleFromQuery(query),
        query: rawQuery,
        fallbackLevel: 'text',
      }),
      fallbackMessage: '',
      location,
    }
  }

  return {
    rows: [],
    focusArea: buildFocusArea({ type: 'search', label: location.label, query: rawQuery, fallbackLevel: 'none' }),
    fallbackMessage: `No matching state, council, suburb, or postcode was found for ${location.label}.`,
    location,
  }
}

function rowsMatchingExactPlace(rows, location) {
  const suburb = normalizeSearchTerm(location.suburb)
  const postcode = cleanText(location.postcode)

  return rows.filter((row) => {
    if (location.matchType === 'postcode') {
      return cleanText(row.postcode) === postcode
    }

    if (location.matchType === 'suburb') {
      return normalizeSearchTerm(row.suburb) === suburb
    }

    return false
  })
}

function rowsMatchingCouncil(rows, location) {
  const suburbs = new Set(location.councilSuburbs || [])
  const postcodes = new Set(location.councilPostcodes || [])

  return rows.filter(
    (row) =>
      row.state === location.stateCode &&
      (suburbs.has(normalizeSearchTerm(row.suburb)) || postcodes.has(cleanText(row.postcode))),
  )
}

function rowsMatchingState(rows, stateCode) {
  return rows.filter((row) => row.state === stateCode)
}

function fallbackToNearbyCouncilOrState(rows, location, rawQuery) {
  const nearbyCouncils = getNearbyCouncilFallbacks(location, NEARBY_COUNCIL_FALLBACK_KM)

  for (const nearbyCouncil of nearbyCouncils) {
    const nearbyRows = rowsMatchingCouncil(rows, nearbyCouncil)
    if (!nearbyRows.length) continue

    return {
      rows: nearbyRows,
      focusArea: buildFocusArea({
        type: 'lga',
        label: nearbyCouncil.council,
        query: rawQuery,
        fallbackLevel: 'nearby-council',
        bounds: nearbyCouncil.councilBounds,
      }),
      fallbackMessage: `No exact or council-level services were found for ${location.label}. Showing services in nearby ${nearbyCouncil.council} (${Math.round(nearbyCouncil.distanceKm)} km away).`,
      location: {
        ...location,
        fallbackCouncil: nearbyCouncil.council,
        fallbackDistanceKm: nearbyCouncil.distanceKm,
      },
    }
  }

  return fallbackToState(rows, location, rawQuery)
}

function fallbackToState(rows, location, rawQuery) {
  const stateRows = rowsMatchingState(rows, location.stateCode)

  return {
    rows: stateRows,
    focusArea: buildFocusArea({
      type: 'state',
      label: location.stateName,
      query: rawQuery,
      fallbackLevel: 'state',
      bounds: location.stateBounds,
    }),
    fallbackMessage: `No exact or council-level services were found for ${location.label}. Showing services across ${location.stateName}.`,
    location,
  }
}

function titleFromQuery(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

function loadCleanEwasteFacilities() {
  return parseCsv(cleanEwasteCsv)
    .map(normalizeCleanEwasteRow)
    .filter(isUsableMapRow)
}

function loadCuratedRecyclingLocations() {
  return parseCsv(curatedRecyclingCsv)
    .filter((row) => toBoolean(row.final_keep) !== false && toBoolean(row.keep) !== false)
    .map(normalizeCuratedRow)
    .filter(isUsableMapRow)
}

function delay(value) {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(value), 120)
  })
}

export async function getMapLocationDatasets(params = {}) {
  const [cleanFacilities, curatedLocations] = await Promise.all([
    delay(loadCleanEwasteFacilities()),
    delay(loadCuratedRecyclingLocations()),
  ])
  const cleanResult = filterRowsWithFallback(cleanFacilities, params)
  const curatedResult = filterRowsWithFallback(curatedLocations, params)

  return {
    datasets: {
      clean_ewaste_facilities_geocoded: cleanResult.rows,
      ewaste_recycling_locations_curated: curatedResult.rows,
    },
    meta: {
      pipeline: 'pseudo-cloud-db',
      source: 'local-csv-fixtures',
      loadedTables: ['clean_ewaste_facilities_geocoded', 'ewaste_recycling_locations_curated'],
      focusAreas: {
        clean_ewaste_facilities_geocoded: cleanResult.focusArea,
        ewaste_recycling_locations_curated: curatedResult.focusArea,
      },
      fallbackMessages: {
        clean_ewaste_facilities_geocoded: cleanResult.fallbackMessage,
        ewaste_recycling_locations_curated: curatedResult.fallbackMessage,
      },
      locationMatches: {
        clean_ewaste_facilities_geocoded: cleanResult.location,
        ewaste_recycling_locations_curated: curatedResult.location,
      },
    },
  }
}
