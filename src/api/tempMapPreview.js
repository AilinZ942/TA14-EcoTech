import geocodedCsv from '../../backend/data_for_map/clean_ewaste_facilities_geocoded.csv?raw'
import curatedCsv from '../../backend/data_for_map/ewaste_recycling_locations_curated.csv?raw'
import postcodesCsv from '../../backend/data_for_map/australian_postcodes.csv?raw'

const NEARBY_DISTANCE_TIERS_KM = [10, 20, 50, 100]
const SEARCH_RANGE_VALUES = new Set([
  'exact',
  'auto',
  '10',
  '20',
  '50',
  '100',
  'state',
])

function parseCsv(text) {
  const rows = []
  let row = []
  let value = ''
  let quoted = false

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    const next = text[i + 1]
    if (char === '"') {
      if (quoted && next === '"') {
        value += '"'
        i += 1
      } else {
        quoted = !quoted
      }
    } else if (char === ',' && !quoted) {
      row.push(value)
      value = ''
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && next === '\n') i += 1
      row.push(value)
      if (row.some((cell) => cell.trim())) rows.push(row)
      row = []
      value = ''
    } else {
      value += char
    }
  }

  row.push(value)
  if (row.some((cell) => cell.trim())) rows.push(row)

  const headers = rows.shift()?.map((header) => header.trim()) || []
  return rows.map((cells) =>
    Object.fromEntries(headers.map((header, i) => [header, String(cells[i] || '').trim()])),
  )
}

function mapRow(row, source) {
  return {
    facility_name: row.facility_name || row.display_name || row.provider_name || '',
    address: row.address || row.formatted_address || '',
    suburb: row.suburb || '',
    postcode: row.postcode || '',
    state: row.state || '',
    latitude: Number(row.latitude),
    longitude: Number(row.longitude),
    ewaste_category: row.ewaste_match_text || row.corrected_source_type || row.source_type || '',
    ewaste_match_text: row.ewaste_match_text || row.corrected_accepted_items || row.accepted_items || '',
    ewaste_match_column: row.ewaste_match_column || '',
    accepted_items: row.corrected_accepted_items || row.accepted_items || '',
    note: row.note || '',
    national_phone_number: row.national_phone_number || '',
    website_uri: row.website_uri || '',
    google_maps_uri: row.google_maps_uri || '',
    source,
    source_file: row.source_file || '',
    coord_source: row.coord_source || (source === 'local_csv_curated' ? 'google_places' : ''),
    dedupe_key: row.dedupe_key || row.place_id || '',
  }
}

function key(...parts) {
  return parts
    .filter(Boolean)
    .map((part) => String(part).trim().toLowerCase())
    .join('|')
}

function norm(value) {
  return String(value || '')
    .trim()
    .toUpperCase()
    .replace('THE CITY OF ', '')
    .replace('CITY OF ', '')
    .replace(' CITY COUNCIL', '')
    .replace(' COUNCIL', '')
    .replace(' SHIRE', '')
}

function lookupContext() {
  const postcodeRows = parseCsv(postcodesCsv)
  const exactLookup = new Map()
  const postcodeLookup = new Map()
  const profiles = new Map()

  postcodeRows.forEach((row) => {
    const latitude = Number(row.Lat_precise || row.lat)
    const longitude = Number(row.Long_precise || row.long)
    const postcodeData = {
      lga_region: row.lgaregion,
      region: row.region,
      postcode_latitude: latitude,
      postcode_longitude: longitude,
    }

    exactLookup.set(key(row.state, row.postcode, row.locality), postcodeData)
    if (!postcodeLookup.has(key(row.state, row.postcode))) {
      postcodeLookup.set(key(row.state, row.postcode), postcodeData)
    }

    addProfile(profiles, {
      tier: 'suburb',
      state: row.state,
      label: row.locality,
      suburb: row.locality,
      postcode: row.postcode,
      latitude,
      longitude,
    })
    addProfile(profiles, {
      tier: 'postcode',
      state: row.state,
      label: row.postcode,
      suburb: row.locality,
      postcode: row.postcode,
      latitude,
      longitude,
    })
    addProfile(profiles, {
      tier: 'state',
      state: row.state,
      label: row.state,
      suburb: row.locality,
      postcode: row.postcode,
      latitude,
      longitude,
    })
  })

  return {
    exactLookup,
    postcodeLookup,
    profiles: Array.from(profiles.values()).map(finalizeProfile),
  }
}

function addProfile(profiles, input) {
  const profileKey = key(input.tier, input.state, norm(input.label))
  const profile = profiles.get(profileKey) || {
    tier: input.tier,
    label: input.label,
    state: input.state,
    suburbs: new Set(),
    postcodes: new Set(),
    points: [],
  }

  if (input.suburb) profile.suburbs.add(norm(input.suburb))
  if (input.postcode) profile.postcodes.add(String(input.postcode).trim())
  if (Number.isFinite(input.latitude) && Number.isFinite(input.longitude)) {
    profile.points.push({ latitude: input.latitude, longitude: input.longitude })
  }

  profiles.set(profileKey, profile)
}

function finalizeProfile(profile) {
  const center = profile.points.length
    ? {
        latitude:
          profile.points.reduce((sum, point) => sum + point.latitude, 0) / profile.points.length,
        longitude:
          profile.points.reduce((sum, point) => sum + point.longitude, 0) / profile.points.length,
      }
    : null

  return {
    ...profile,
    center,
    focus_area: {
      label: profile.label,
      center,
    },
  }
}

function enrich(items) {
  const context = lookupContext()
  return items.map((item) => ({
    ...item,
    ...(context.exactLookup.get(key(item.state, item.postcode, item.suburb)) ||
      context.postcodeLookup.get(key(item.state, item.postcode)) ||
      {}),
  }))
}

function itemText(item) {
  return [
    item.facility_name,
    item.address,
    item.suburb,
    item.postcode,
    item.state,
    item.source,
    item.ewaste_match_text,
    item.accepted_items,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function haversineKm(first, second) {
  if (!first || !second) return null
  if (
    !Number.isFinite(first.latitude) ||
    !Number.isFinite(first.longitude) ||
    !Number.isFinite(second.latitude) ||
    !Number.isFinite(second.longitude)
  ) {
    return null
  }

  const radiusKm = 6371
  const lat1 = (first.latitude * Math.PI) / 180
  const lat2 = (second.latitude * Math.PI) / 180
  const deltaLat = ((second.latitude - first.latitude) * Math.PI) / 180
  const deltaLon = ((second.longitude - first.longitude) * Math.PI) / 180
  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLon / 2) ** 2

  return radiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function resolveProfile(query, profiles) {
  const normalized = norm(query)
  if (!normalized) return null

  const stateAliases = new Map([
    ['VIC', 'VIC'],
    ['VICTORIA', 'VIC'],
    ['NSW', 'NSW'],
    ['NEW SOUTH WALES', 'NSW'],
    ['QLD', 'QLD'],
    ['QUEENSLAND', 'QLD'],
    ['SA', 'SA'],
    ['SOUTH AUSTRALIA', 'SA'],
    ['WA', 'WA'],
    ['WESTERN AUSTRALIA', 'WA'],
    ['TAS', 'TAS'],
    ['TASMANIA', 'TAS'],
    ['NT', 'NT'],
    ['NORTHERN TERRITORY', 'NT'],
    ['ACT', 'ACT'],
    ['AUSTRALIAN CAPITAL TERRITORY', 'ACT'],
  ])

  if (stateAliases.has(normalized)) {
    return profiles.find(
      (profile) => profile.tier === 'state' && profile.state === stateAliases.get(normalized),
    )
  }

  const postcodeProfile = profiles.find(
    (profile) => profile.tier === 'postcode' && profile.postcodes.has(query.trim()),
  )
  if (postcodeProfile) return postcodeProfile

  return profiles.find(
    (profile) => profile.tier === 'suburb' && norm(profile.label) === normalized,
  )
}

function itemMatchesProfile(item, profile) {
  if (!profile || item.state !== profile.state) return false
  if (profile.tier === 'state') return true
  if (profile.tier === 'postcode') return profile.postcodes.has(String(item.postcode || '').trim())
  return profile.suburbs.has(norm(item.suburb))
}

function nearbyItems(items, profile, maxDistanceKm) {
  if (!profile?.center) return []

  return items
    .map((item) => ({
      item,
      distance: haversineKm(profile.center, {
        latitude: item.latitude,
        longitude: item.longitude,
      }),
    }))
    .filter((entry) => entry.distance != null && entry.distance <= maxDistanceKm)
    .sort((left, right) => left.distance - right.distance)
    .map((entry) => entry.item)
}

function normalizeSearchRange(value) {
  const range = String(value || 'exact').trim().toLowerCase()
  return SEARCH_RANGE_VALUES.has(range) ? range : 'exact'
}

function stateFallback(items, profile, query, messagePrefix) {
  const fallback = items.filter((item) => item.state === profile.state)
  return {
    items: fallback,
    search: {
      query,
      mode: 'fallback',
      label: profile.label,
      distance_km: null,
      search_range: 'state',
      message: `${messagePrefix} Showing all locations in ${profile.state}.`,
      match_count: fallback.length,
      focus_area: profile.focus_area,
    },
  }
}

function noFallbackResult(query, message) {
  return {
    items: [],
    search: {
      query,
      mode: 'none',
      message,
      match_count: 0,
    },
  }
}

function filterForSearch(items, searchText, searchRange = 'exact') {
  const query = String(searchText || '').trim()
  if (!query) return { items, search: null }

  const selectedRange = normalizeSearchRange(searchRange)
  const profile = resolveProfile(query, lookupContext().profiles)

  if (profile) {
    const matchedLocation = items.filter((item) => itemMatchesProfile(item, profile))

    if (selectedRange === 'exact') {
      if (matchedLocation.length) {
        return {
          items: matchedLocation,
          search: {
            query,
            mode: 'exact',
            label: profile.label,
            message: '',
            search_range: selectedRange,
            match_count: matchedLocation.length,
            focus_area: profile.focus_area,
          },
        }
      }

      return noFallbackResult(
        query,
        `No exact disposal locations were found for '${query}'. Choose a wider search range to see nearby alternatives.`,
      )
    }

    if (selectedRange === 'state') {
      return stateFallback(
        items,
        profile,
        query,
        `Showing all locations in the selected state for '${query}'.`,
      )
    }

    const rangesToTry =
      selectedRange === 'auto'
        ? NEARBY_DISTANCE_TIERS_KM
        : [Number(selectedRange)]

    for (const distanceKm of rangesToTry) {
      const nearby = nearbyItems(items, profile, distanceKm)
      if (nearby.length) {
        return {
          items: nearby,
          search: {
            query,
            mode: matchedLocation.length ? 'range' : 'fallback',
            label: profile.label,
            distance_km: distanceKm,
            search_range: selectedRange,
            message: `Showing disposal locations within ${distanceKm}km of '${query}'.`,
            match_count: nearby.length,
            focus_area: profile.focus_area,
          },
        }
      }
    }

    const maxDistanceKm = rangesToTry[rangesToTry.length - 1]
    return noFallbackResult(
      query,
      `No disposal locations within ${maxDistanceKm}km were found for '${query}'. Choose State-wide to see all locations in ${profile.state}.`,
    )
  }

  const exact = items.filter((item) => itemText(item).includes(query.toLowerCase()))
  if (exact.length) {
    return {
      items: exact,
      search: {
        query,
        mode: 'exact',
        search_range: selectedRange,
        match_count: exact.length,
      },
    }
  }

  return noFallbackResult(query, `No disposal locations match '${query}'.`)
}

export function getTempMapPreview(searchText = '', searchRange = 'exact') {
  const allItems = enrich([
    ...parseCsv(geocodedCsv).map((row) => mapRow(row, 'local_csv_geocoded')),
    ...parseCsv(curatedCsv)
      .filter((row) => row.final_keep !== 'False')
      .map((row) => mapRow(row, 'local_csv_curated')),
  ]).filter((row) => Number.isFinite(row.latitude) && Number.isFinite(row.longitude))
  const result = filterForSearch(allItems, searchText, searchRange)

  return {
    items: result.items,
    meta: {
      pipeline: 'temp-frontend-preview',
      source: 'backend/data_for_map',
      row_count: result.items.length,
      temporary: true,
      search: result.search,
    },
  }
}
