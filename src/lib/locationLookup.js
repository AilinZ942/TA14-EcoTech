import australianPostcodesCsv from '../../data_for_map/australian_postcodes.csv?raw'
import locationLookupCsv from '../../data_for_map/location_lookup.csv?raw'

const STATE_ALIASES = new Map([
  ['ACT', 'ACT'],
  ['AUSTRALIAN CAPITAL TERRITORY', 'ACT'],
  ['NSW', 'NSW'],
  ['NEW SOUTH WALES', 'NSW'],
  ['NT', 'NT'],
  ['NORTHERN TERRITORY', 'NT'],
  ['QLD', 'QLD'],
  ['QUEENSLAND', 'QLD'],
  ['SA', 'SA'],
  ['SOUTH AUSTRALIA', 'SA'],
  ['TAS', 'TAS'],
  ['TASMANIA', 'TAS'],
  ['VIC', 'VIC'],
  ['VICTORIA', 'VIC'],
  ['WA', 'WA'],
  ['WESTERN AUSTRALIA', 'WA'],
])

const STATE_NAMES = {
  ACT: 'Australian Capital Territory',
  NSW: 'New South Wales',
  NT: 'Northern Territory',
  QLD: 'Queensland',
  SA: 'South Australia',
  TAS: 'Tasmania',
  VIC: 'Victoria',
  WA: 'Western Australia',
}

const STATE_BOUNDS = {
  ACT: { minLongitude: 148.75, minLatitude: -35.92, maxLongitude: 149.4, maxLatitude: -35.12 },
  NSW: { minLongitude: 140.99, minLatitude: -37.51, maxLongitude: 153.64, maxLatitude: -28.16 },
  NT: { minLongitude: 129.0, minLatitude: -26.02, maxLongitude: 138.0, maxLatitude: -10.9 },
  QLD: { minLongitude: 138.0, minLatitude: -29.18, maxLongitude: 153.55, maxLatitude: -9.14 },
  SA: { minLongitude: 129.0, minLatitude: -38.06, maxLongitude: 141.0, maxLatitude: -25.99 },
  TAS: { minLongitude: 143.82, minLatitude: -43.74, maxLongitude: 148.5, maxLatitude: -39.58 },
  VIC: { minLongitude: 140.96, minLatitude: -39.2, maxLongitude: 150.05, maxLatitude: -33.98 },
  WA: { minLongitude: 112.92, minLatitude: -35.13, maxLongitude: 129.0, maxLatitude: -13.69 },
}

const COUNCIL_BOUNDS = {
  'VIC|BAYSIDE': {
    minLongitude: 144.986,
    minLatitude: -37.999,
    maxLongitude: 145.065,
    maxLatitude: -37.886,
  },
  'VIC|MONASH': {
    minLongitude: 145.045,
    minLatitude: -37.962,
    maxLongitude: 145.235,
    maxLatitude: -37.835,
  },
}

function parseCsv(text) {
  const rows = []
  let row = []
  let value = ''
  let inQuotes = false

  for (let index = 0; index < String(text || '').length; index += 1) {
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
    Object.fromEntries(headers.map((header, index) => [header, cleanText(cells[index])])),
  )
}

function cleanText(value) {
  return String(value || '').trim()
}

function normalizeKey(value) {
  return cleanText(value)
    .toUpperCase()
    .replace(/^CITY OF\s+/, '')
    .replace(/^THE CITY OF\s+/, '')
    .replace(/\s+CITY COUNCIL$/, '')
    .replace(/\s+COUNCIL$/, '')
    .replace(/\s+SHIRE$/, '')
    .replace(/[^A-Z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function titleCase(value) {
  return cleanText(value)
    .toLowerCase()
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

function canonicalCouncilName(row) {
  const stateCode = cleanText(row.state || row.state_code).toUpperCase()
  const rawCouncil = cleanText(row.lgaregion || row.council)
  const council = rawCouncil.replace(/\s*\([^)]*\)\s*/g, '').trim()

  if (!council) return ''
  if (stateCode === 'VIC' && normalizeKey(council) === 'MONASH') return 'City of Monash'
  if (stateCode === 'VIC' && normalizeKey(council) === 'BAYSIDE') return 'Bayside City Council'
  if (/city|council|shire|municipality|borough|regional/i.test(council)) return titleCase(council)
  return titleCase(council)
}

function normalizePostcodeRow(row) {
  return {
    stateCode: cleanText(row.state).toUpperCase(),
    stateName: STATE_NAMES[cleanText(row.state).toUpperCase()] || cleanText(row.state),
    council: canonicalCouncilName(row),
    suburb: titleCase(row.locality),
    postcode: cleanText(row.postcode),
    latitude: Number(row.Lat_precise || row.lat),
    longitude: Number(row.Long_precise || row.long),
    source: 'australian_postcodes',
  }
}

function normalizeManualRow(row) {
  return {
    stateCode: cleanText(row.state_code).toUpperCase(),
    stateName: cleanText(row.state_name),
    council: cleanText(row.council),
    suburb: cleanText(row.suburb),
    postcode: cleanText(row.postcode),
    source: 'location_lookup',
  }
}

const manualLookupRows = parseCsv(locationLookupCsv).map(normalizeManualRow)
const postcodeLookupRows = parseCsv(australianPostcodesCsv)
  .map(normalizePostcodeRow)
  .filter((row) => row.stateCode && row.suburb && row.postcode && row.council)

const lookupRows = dedupeLookupRows([...manualLookupRows, ...postcodeLookupRows])

function dedupeLookupRows(rows) {
  const seen = new Set()
  const deduped = []

  for (const row of rows) {
    const key = [row.stateCode, normalizeKey(row.council), normalizeKey(row.suburb), row.postcode].join('|')
    if (seen.has(key)) continue
    seen.add(key)
    deduped.push(row)
  }

  return deduped
}

const manualSuggestionRows = manualLookupRows
const councilProfiles = buildCouncilProfiles()

function buildCouncilProfiles() {
  const profiles = new Map()

  lookupRows.forEach((row) => {
    const key = councilKey(row)
    if (!key) return

    if (!profiles.has(key)) {
      profiles.set(key, {
        key,
        stateCode: row.stateCode,
        stateName: row.stateName || STATE_NAMES[row.stateCode] || row.stateCode,
        council: row.council,
        suburbs: new Set(),
        postcodes: new Set(),
        latitudeTotal: 0,
        longitudeTotal: 0,
        coordinateCount: 0,
        bounds: null,
      })
    }

    const profile = profiles.get(key)
    profile.suburbs.add(normalizeKey(row.suburb))
    profile.postcodes.add(row.postcode)

    if (Number.isFinite(row.latitude) && Number.isFinite(row.longitude)) {
      profile.latitudeTotal += row.latitude
      profile.longitudeTotal += row.longitude
      profile.coordinateCount += 1
      profile.bounds = expandBounds(profile.bounds, row)
    }
  })

  return Array.from(profiles.values()).map((profile) => ({
    ...profile,
    suburbs: Array.from(profile.suburbs).filter(Boolean),
    postcodes: Array.from(profile.postcodes).filter(Boolean),
    center:
      profile.coordinateCount > 0
        ? {
            latitude: profile.latitudeTotal / profile.coordinateCount,
            longitude: profile.longitudeTotal / profile.coordinateCount,
          }
        : null,
    bounds: COUNCIL_BOUNDS[profile.key] || profile.bounds,
  }))
}

function councilKey(row) {
  if (!row?.stateCode || !row?.council) return ''
  return `${row.stateCode}|${normalizeKey(row.council)}`
}

function expandBounds(bounds, row) {
  if (!bounds) {
    return {
      minLongitude: row.longitude,
      minLatitude: row.latitude,
      maxLongitude: row.longitude,
      maxLatitude: row.latitude,
    }
  }

  return {
    minLongitude: Math.min(bounds.minLongitude, row.longitude),
    minLatitude: Math.min(bounds.minLatitude, row.latitude),
    maxLongitude: Math.max(bounds.maxLongitude, row.longitude),
    maxLatitude: Math.max(bounds.maxLatitude, row.latitude),
  }
}

function buildCouncilScope(row) {
  const profile = councilProfiles.find((entry) => entry.key === councilKey(row))

  return {
    suburbs: profile?.suburbs || [],
    postcodes: profile?.postcodes || [],
    center: profile?.center || null,
    bounds: profile?.bounds || null,
  }
}

function buildLookupResult(row, matchType, input) {
  const councilScope = buildCouncilScope(row)

  return {
    input: cleanText(input),
    matchType,
    stateCode: row.stateCode,
    stateName: row.stateName || STATE_NAMES[row.stateCode] || row.stateCode,
    council: row.council,
    suburb: row.suburb,
    postcode: row.postcode,
    councilSuburbs: councilScope.suburbs,
    councilPostcodes: councilScope.postcodes,
    councilCenter: councilScope.center,
    councilBounds: councilScope.bounds,
    stateBounds: STATE_BOUNDS[row.stateCode] || null,
  }
}

export function resolveLocationQuery(input) {
  const raw = cleanText(input)
  const key = normalizeKey(raw)

  if (!key) {
    return {
      input: '',
      matchType: 'none',
      label: '',
    }
  }

  const stateCode = STATE_ALIASES.get(key)
  if (stateCode) {
    return {
      input: raw,
      matchType: 'state',
      stateCode,
      stateName: STATE_NAMES[stateCode] || titleCase(raw),
      label: STATE_NAMES[stateCode] || stateCode,
      stateBounds: STATE_BOUNDS[stateCode] || null,
    }
  }

  const postcodeMatch = lookupRows.find((row) => row.postcode === raw)
  if (postcodeMatch) {
    return {
      ...buildLookupResult(postcodeMatch, 'postcode', raw),
      label: `${postcodeMatch.suburb} ${postcodeMatch.postcode}`,
    }
  }

  const councilMatch = lookupRows.find((row) => normalizeKey(row.council) === key)
  if (councilMatch) {
    return {
      ...buildLookupResult(councilMatch, 'council', raw),
      suburb: '',
      postcode: '',
      label: councilMatch.council,
    }
  }

  const suburbMatch = lookupRows.find((row) => normalizeKey(row.suburb) === key)
  if (suburbMatch) {
    return {
      ...buildLookupResult(suburbMatch, 'suburb', raw),
      label: suburbMatch.suburb,
    }
  }

  return {
    input: raw,
    matchType: 'unknown',
    label: titleCase(raw),
  }
}

export function getLocationSuggestions() {
  const suggestions = new Set()

  Object.values(STATE_NAMES).forEach((stateName) => suggestions.add(stateName))

  manualSuggestionRows.forEach((row) => {
    suggestions.add(row.council)
    suggestions.add(row.suburb)
    suggestions.add(row.postcode)
    suggestions.add(`${row.suburb} ${row.postcode}`)
  })

  return Array.from(suggestions)
    .filter(Boolean)
    .sort((left, right) => left.localeCompare(right))
}

export function getNearbyCouncilFallbacks(location, maxDistanceKm = 25) {
  if (!location?.stateCode || !location?.councilCenter) return []

  return councilProfiles
    .filter(
      (profile) =>
        profile.stateCode === location.stateCode &&
        profile.key !== `${location.stateCode}|${normalizeKey(location.council)}` &&
        profile.center,
    )
    .map((profile) => ({
      stateCode: profile.stateCode,
      stateName: profile.stateName,
      council: profile.council,
      councilSuburbs: profile.suburbs,
      councilPostcodes: profile.postcodes,
      councilCenter: profile.center,
      councilBounds: profile.bounds,
      stateBounds: STATE_BOUNDS[profile.stateCode] || null,
      distanceKm: distanceKm(location.councilCenter, profile.center),
    }))
    .filter((profile) => profile.distanceKm <= maxDistanceKm)
    .sort((left, right) => left.distanceKm - right.distanceKm)
}

function distanceKm(left, right) {
  const earthRadiusKm = 6371
  const lat1 = toRadians(left.latitude)
  const lat2 = toRadians(right.latitude)
  const deltaLat = toRadians(right.latitude - left.latitude)
  const deltaLon = toRadians(right.longitude - left.longitude)
  const a =
    Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLon / 2) * Math.sin(deltaLon / 2)

  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function toRadians(value) {
  return (value * Math.PI) / 180
}
