# TA14-EcoTech

EcoTech is a Vue 3 + Vite frontend project for e-waste awareness, repair guidance, and disposal location discovery. The repository is no longer just a simple SPA shell: it now also contains a frontend-side map data integration layer with a dual-track disposal data pipeline.

## Quick Start

```sh
npm install
npm run dev
```

Build and lint:

```sh
npm run build
npm run lint
```

## Repository Map

```text
TA14-EcoTech/
├─ public/
│  └─ clean_ewaste_facilities.geojson        # legacy fallback disposal dataset
├─ src/
│  ├─ api/
│  │  └─ index.js                            # thin Azure API wrapper for AI chat
│  ├─ assets/                               # global styles and static images
│  ├─ lib/
│  │  ├─ mapApi.js                           # unified map data gateway
│  │  ├─ ewasteMapModel.js                   # row normalization, categories, filtering, markers
│  │  ├─ uvMapModel.js                       # SVG map projection helpers
│  │  ├─ australiaStatesGeoJson.js           # Australia basemap geometry
│  │  ├─ vic_lga_gda2020.geojson             # Victoria LGA geometry
│  │  ├─ vic_loc_gda2020.geojson             # Victoria locality geometry
│  │  └─ VIC_postcodes.geojson               # postcode geometry reference
│  ├─ public/
│  │  ├─ clean_ewaste_facilities_geocoded.csv
│  │  └─ maptiler_geocode_cache.json
│  ├─ router/
│  │  └─ index.js                            # active route registry
│  └─ views/
│     ├─ DisposalLocations.vue               # Mapbox disposal page
│     ├─ EwasteAustraliaMap.vue              # custom SVG national/Victoria map
│     └─ *.vue                               # other pages
├─ tmp_vic_*                                # shapefile extraction scratch data
├─ architecture.txt                         # text architecture graph
└─ README.md
```

## Current Product Surface

- `src/views/AIChat.vue` uses `src/api/index.js` and talks to the Azure backend.
- `src/views/DisposalLocations.vue` is the active routed disposal map page.
- `src/views/EwasteAustraliaMap.vue` contains a richer custom SVG map that supports both `disposal` and `repair` resource types, but it is not currently wired into `src/router/index.js`.

That last point matters: some of the most important pipeline logic exists in the repo, but not every view using it is currently exposed in navigation.

## Dual-Track Data Pipeline

The disposal map uses a unified frontend contract:

```text
UI view
  -> buildRequestPayload()
  -> searchMapFacilities(payload)
  -> choose pipeline by VITE_MAP_DATA_MODE
     -> Azure disposal API
     -> or local cleaned CSV
     -> optionally legacy GeoJSON fallback
  -> normalize rows
  -> build markers / filter / render
```

### Main idea

There are two primary disposal data tracks:

1. `Azure API track`
   `src/lib/mapApi.js` posts disposal search payloads to `VITE_API_BASE_URL + VITE_DISPOSAL_API_PATH`
2. `Local CSV track`
   the same module loads `src/public/clean_ewaste_facilities_geocoded.csv` and filters it in-browser

There is also one optional legacy rescue path:

3. `Legacy GeoJSON fallback`
   when enabled by `VITE_ENABLE_LEGACY_GEOJSON_FALLBACK=true`, the code can fall back to `public/clean_ewaste_facilities.geojson`

This means the repo is effectively operating with a "dual-track pipeline" for normal operation and a third legacy compatibility layer for failure recovery.

See [docs/data-pipeline.md](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/docs/data-pipeline.md) for the full data-flow breakdown.

## Key Files For The Pipeline

- [src/lib/mapApi.js](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/src/lib/mapApi.js): pipeline switchboard, CSV parser, Azure request layer, fallback behavior
- [src/lib/ewasteMapModel.js](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/src/lib/ewasteMapModel.js): shared normalization, categorization, filtering, marker shaping
- [src/views/DisposalLocations.vue](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/src/views/DisposalLocations.vue): routed Mapbox map, shows pipeline state and fallback reason
- [src/views/EwasteAustraliaMap.vue](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/src/views/EwasteAustraliaMap.vue): custom SVG map using the same unified search entry

## Environment Variables

The map stack currently depends on:

- `VITE_MAPBOX_ACCESS_TOKEN`: required by `DisposalLocations.vue`
- `VITE_MAP_DATA_MODE=local|azure|auto`: selects disposal data strategy
- `VITE_API_BASE_URL`: Azure backend base URL
- `VITE_DISPOSAL_API_PATH`: disposal search path, defaults to `/api/map/disposal-locations/search`
- `VITE_ENABLE_LEGACY_GEOJSON_FALLBACK=true|false`: optional legacy fallback

Typical local development setup:

```env
VITE_MAPBOX_ACCESS_TOKEN=your_token_here
VITE_MAP_DATA_MODE=local
# VITE_API_BASE_URL=https://your-api-base-url
# VITE_DISPOSAL_API_PATH=/api/map/disposal-locations/search
# VITE_ENABLE_LEGACY_GEOJSON_FALLBACK=true
```

## Architectural Notes

### What is clean

- The map UI reads through one entry point: `searchMapFacilities(payload)`
- Local and remote disposal data are normalized into the same row shape
- Marker/category/filter logic is centralized in `ewasteMapModel.js`

### What is still messy

- Disposal data assets are split across `src/public/` and root `public/`
- `EwasteAustraliaMap.vue` is important but currently not routed
- The repo keeps temporary shapefile extraction directories alongside app source
- `README.md` previously focused on the old SPA shape and under-described the data layer

## Suggested Next Cleanup Pass

If we continue organizing this repo, the next high-value changes would be:

1. Move raw and generated map datasets into a dedicated top-level `data/` or `docs/data/` structure with provenance notes.
2. Separate temporary shapefile extraction artifacts from committed application assets.
3. Decide whether `EwasteAustraliaMap.vue` is the future primary map page or an experiment, then either route it or archive it.
4. Split `src/lib/mapApi.js` into smaller modules once backend contracts stabilize.

## Additional Docs

- [architecture.txt](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/architecture.txt)
- [docs/data-pipeline.md](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/docs/data-pipeline.md)
