# Data Pipeline Guide

This project has a unified frontend search contract, but the disposal data does not come from a single source. In practice there are two normal operating tracks plus one optional compatibility fallback.

## 1. Pipeline At A Glance

```text
DisposalLocations.vue / EwasteAustraliaMap.vue
  -> buildRequestPayload()
  -> searchMapFacilities(payload, options)
  -> payload.resourceType === "disposal"
     -> searchDisposalFacilities()
        -> local mode: searchLocalDisposalFacilities()
        -> azure mode: searchAzureDisposalFacilities()
        -> auto mode: try Azure, then fallback to local CSV
     -> optional final fallback: searchLegacyGeoJsonDisposalFacilities()
  -> normalizeMapFacilityRow()
  -> buildFacilityMarkers()
  -> filterFacilities() / buildCategorySummary()
  -> render map
```

## 2. The Two Main Tracks

### Track A: Azure disposal API

Entry:
- `src/lib/mapApi.js`

Flow:
1. `searchMapFacilities()` detects `resourceType === 'disposal'`
2. `searchDisposalFacilities()` checks `VITE_MAP_DATA_MODE`
3. If mode is `azure` or `auto`, `searchAzureDisposalFacilities()` sends a `POST`
4. The response is normalized by `normalizeDisposalResponse()`
5. The UI receives a standard `{ items, meta }` structure

Expected contract:

```json
{
  "items": [
    {
      "facility_name": "Example site",
      "address": "123 Example Rd",
      "suburb": "Melbourne",
      "postcode": "3000",
      "state": "VIC",
      "latitude": -37.81,
      "longitude": 144.96
    }
  ],
  "meta": {
    "pipeline": "azure",
    "source": "api"
  }
}
```

Notes:
- This is the preferred remote track when backend service is available.
- It allows the frontend to stay thin while still using the same rendering model.

### Track B: Local cleaned CSV

Entry:
- `src/lib/mapApi.js`
- dataset: `src/public/clean_ewaste_facilities_geocoded.csv`

Flow:
1. `loadLocalDisposalRows()` fetches the CSV asset bundled by Vite
2. `parseCsv()` and `parseCsvLine()` convert text to row objects
3. `normalizeMapFacilityRow()` converts CSV rows to the shared map row shape
4. `filterDisposalRows()` applies state/category/search filtering in-browser
5. The UI receives `{ items, meta: { pipeline: 'local', source: 'csv' } }`

Notes:
- This is the best local/dev-safe pipeline because it needs no backend.
- In `.env.local`, the repo is currently configured as `VITE_MAP_DATA_MODE=local`.

## 3. The Legacy Fallback Track

### Track C: Legacy GeoJSON fallback

Entry:
- `public/clean_ewaste_facilities.geojson`

When it activates:
- only if the disposal pipeline throws
- and `VITE_ENABLE_LEGACY_GEOJSON_FALLBACK=true`

Flow:
1. `searchMapFacilities()` catches a disposal failure
2. it calls `searchLegacyGeoJsonDisposalFacilities()`
3. `loadLegacyGeoJsonRows()` loads GeoJSON features
4. `normalizeGeoJsonRow()` adapts them to the shared row shape

Why it matters:
- it preserves an escape hatch for older data assets
- but it is clearly legacy, because the preferred local source is now the cleaned geocoded CSV

## 4. Shared Normalization Layer

The real "unifier" is not the UI. It is the combination of:

- `normalizeMapFacilityRow()` in `src/lib/mapApi.js`
- `buildFacilityMarkers()` in `src/lib/ewasteMapModel.js`

These functions make different source formats look the same to the map views.

Shared fields downstream include:

- `facility_name`
- `address`
- `suburb`
- `postcode`
- `state`
- `latitude`
- `longitude`
- `resourceType`
- `category` / `ewaste_category`
- `coord_source`
- `source_file`
- `source`

Because of this, the rendering layer does not need to know whether a row came from Azure, CSV, or GeoJSON.

## 5. Where The Pipeline Is Consumed

### `src/views/DisposalLocations.vue`

Purpose:
- routed page
- uses Mapbox GL
- disposal only
- surfaces `pipeline`, `source`, and `fallbackReason` in the UI

This is the clearest place to inspect the dual-track behavior in action.

### `src/views/EwasteAustraliaMap.vue`

Purpose:
- custom SVG map
- supports both `disposal` and `repair`
- calls the same `searchMapFacilities()` entry

Important caveat:
- it is not currently registered in `src/router/index.js`
- so it contains important pipeline behavior, but is not part of the active route surface today

## 6. Repair Pipeline Is Not Dual-Track

The "dual-track" setup mainly applies to `resourceType === 'disposal'`.

For non-disposal searches, `searchMapFacilities()` currently posts directly to:

```text
${VITE_API_BASE_URL}/api/map/facilities/search
```

So the repair side is:

- request-driven
- backend-dependent
- not equipped with the same local CSV fallback structure

This asymmetry is worth remembering when planning future cleanup.

## 7. Current Structural Risks

- Data assets are stored in two public-like locations: `src/public/` and `public/`
- Pipeline logic, parsing logic, and transport logic all live together in `src/lib/mapApi.js`
- The repo contains raw temp extraction folders next to runtime app files
- There is no dedicated provenance document for how the cleaned CSV was generated from the raw sources

## 8. Recommended Refactor Direction

If we want to keep evolving this stack, a clean next architecture would be:

```text
src/lib/map/
  dataSources/
    azureDisposalSource.js
    localDisposalCsvSource.js
    legacyGeoJsonSource.js
    repairApiSource.js
  normalize/
    normalizeFacilityRow.js
  model/
    ewasteMapModel.js
  index.js
```

That would separate:

- transport
- parsing
- normalization
- rendering model

without changing the existing view contract.
