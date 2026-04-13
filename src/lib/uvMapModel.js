const AUSTRALIA_BOUNDS = {
  minLongitude: 112,
  maxLongitude: 154.5,
  minLatitude: -44.8,
  maxLatitude: -10,
}

export const mapViewport = {
  width: 980,
  height: 760,
  padding: 48,
}

const STATE_NAME_TO_CODE = {
  'NEW SOUTH WALES': 'NSW',
  VICTORIA: 'VIC',
  QUEENSLAND: 'QLD',
  'SOUTH AUSTRALIA': 'SA',
  'WESTERN AUSTRALIA': 'WA',
  TASMANIA: 'TAS',
  'NORTHERN TERRITORY': 'NT',
  'AUSTRALIAN CAPITAL TERRITORY': 'ACT',
  NSW: 'NSW',
  VIC: 'VIC',
  QLD: 'QLD',
  SA: 'SA',
  WA: 'WA',
  TAS: 'TAS',
  NT: 'NT',
  ACT: 'ACT',
}

export function stateCodeFromName(name) {
  if (!name) {
    return ''
  }

  return STATE_NAME_TO_CODE[String(name).trim().toUpperCase()] || ''
}

export function projectCoordinates(longitude, latitude) {
  const xSpan = AUSTRALIA_BOUNDS.maxLongitude - AUSTRALIA_BOUNDS.minLongitude
  const ySpan = AUSTRALIA_BOUNDS.maxLatitude - AUSTRALIA_BOUNDS.minLatitude
  const drawableWidth = mapViewport.width - mapViewport.padding * 2
  const drawableHeight = mapViewport.height - mapViewport.padding * 2

  const x = ((Number(longitude) - AUSTRALIA_BOUNDS.minLongitude) / xSpan) * drawableWidth + mapViewport.padding
  const y =
    (1 - (Number(latitude) - AUSTRALIA_BOUNDS.minLatitude) / ySpan) * drawableHeight + mapViewport.padding

  return { x, y }
}

function collectRingPoints(coordinates = []) {
  const points = []

  for (const ring of coordinates) {
    for (const coordinate of ring || []) {
      if (Array.isArray(coordinate) && coordinate.length >= 2) {
        points.push(coordinate)
      }
    }
  }

  return points
}

function polygonPath(coordinates = []) {
  return coordinates
    .map((ring) =>
      (ring || [])
        .map((coordinate, index) => {
          const point = projectCoordinates(coordinate[0], coordinate[1])
          return `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
        })
        .concat('Z')
        .join(' '),
    )
    .join(' ')
}

function centroidFromPoints(points) {
  if (!points.length) {
    return null
  }

  let minX = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY

  for (const [longitude, latitude] of points) {
    minX = Math.min(minX, longitude)
    maxX = Math.max(maxX, longitude)
    minY = Math.min(minY, latitude)
    maxY = Math.max(maxY, latitude)
  }

  return projectCoordinates((minX + maxX) / 2, (minY + maxY) / 2)
}

export function buildGeoFeaturePaths(geoJson) {
  const features = Array.isArray(geoJson?.features) ? geoJson.features : []

  return features.map((feature) => {
    const geometry = feature?.geometry || {}
    const properties = feature?.properties || {}
    const polygons = geometry.type === 'MultiPolygon' ? geometry.coordinates || [] : [geometry.coordinates || []]
    const points = polygons.flatMap((polygon) => collectRingPoints(polygon))

    return {
      name: properties.STATE_NAME || properties.name || '',
      code: stateCodeFromName(properties.STATE_NAME || properties.name || properties.code || ''),
      path: polygons.map((polygon) => polygonPath(polygon)).join(' '),
      labelPoint: centroidFromPoints(points),
      geometry,
      properties,
    }
  })
}
