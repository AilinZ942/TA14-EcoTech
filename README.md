# TA14-EcoTech

EcoTech is a Vue 3 and Flask prototype for e-waste awareness. The current stage connects two main frontend features to named API methods:

- `api.getHealthAll()` for the health impact dashboard
- `api.searchDisposalLocation()` for disposal location search and map data

The repo also contains temporary preview routes so teammates can review the health dashboard and disposal map without completing the normal login flow.

## Tech Stack

### Frontend

- Node.js `>=20.19.0`
- Vue 3
- Vue Router
- Vite
- Mapbox GL for the disposal map

Frontend dependencies are managed by `package.json` and `package-lock.json`.

### Backend

- Python `>=3.10`
- Flask
- Flask-CORS
- Flask-WTF
- psycopg2 for PostgreSQL access
- python-dotenv for local environment variables

Python dependencies are listed in both `requirements.txt` and `backend/requirements.txt`.

## Project Structure

```text
group_repo_29_04/
  backend/
    main.py                 Flask app entry point
    health.py               /api/health/all endpoint
    location.py             /api/map/disposal-locations endpoint
    login.py                auth and CSRF endpoints
    optimizer.py            AI device optimizer endpoint
    data_for_map/           local map CSV and boundary data
  src/
    api/index.js            shared frontend API wrapper
    api/tempMapPreview.js   temporary frontend-only disposal map preview data
    router/index.js         Vue routes and preview auth bypass
    views/Dashboard.vue     health dashboard
    views/DisposalLocations.vue
    views/EwasteAustraliaMap.vue
  .env.local                local Vite preview variables
```

## Main API Contract

The frontend should call the backend through `src/api/index.js`.

| Frontend method | HTTP method | Backend path | Main consumers |
| --- | --- | --- | --- |
| `api.getHealthAll()` | `GET` | `/api/health/all` | `src/views/Dashboard.vue` |
| `api.searchDisposalLocation()` | `GET` | `/api/map/disposal-locations` | `src/views/DisposalLocations.vue`, `src/views/EwasteAustraliaMap.vue` |

`api.searchDisposalLocations()` still exists as a compatibility alias, but new frontend code should use `api.searchDisposalLocation()`.

## Local Setup

### Install frontend dependencies

```powershell
npm install
```

### Install backend dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you only work inside the backend folder, this also works:

```powershell
pip install -r backend\requirements.txt
```

### Start the backend

```powershell
python backend\main.py
```

The backend runs on:

```text
http://localhost:8000
```

### Start the frontend

```powershell
npm run dev
```

Vite usually starts at `http://localhost:5173`. If that port is busy, it will choose the next available port.

## Preview Pages

These preview pages were added for the current stage so teammates can review the work quickly:

| Preview | URL |
| --- | --- |
| Health dashboard preview | `http://localhost:5173/#/health-preview` |
| Disposal locations preview | `http://localhost:5173/#/disposal-locations` |

If Vite starts on another port, replace `5173` with the port shown in the terminal.

Example from one local run:

```text
http://127.0.0.1:5176/#/health-preview
http://127.0.0.1:5176/#/disposal-locations
```

### Preview environment variables

The local preview mode is controlled by `.env.local`:

```env
VITE_MAPBOX_ACCESS_TOKEN=your_mapbox_token
VITE_MAP_DATA_SOURCE=local
VITE_ALLOW_MAP_PREVIEW_WITHOUT_LOGIN=true
VITE_TEMP_MAP_PREVIEW=1
```

`VITE_TEMP_MAP_PREVIEW=1` makes `api.searchDisposalLocation()` use `src/api/tempMapPreview.js` instead of the live backend endpoint. This lets the disposal page show local CSV map data during development.

## How To Remove The Preview Code Later

When the team no longer needs the temporary preview pages, use this checklist.

1. Remove or disable the health preview route

   File: `src/router/index.js`

   Delete this route:

   ```js
   {
     path: '/health-preview',
     name: 'HealthPreview',
     component: Dashboard,
     meta: { requiresAuth: false }
   }
   ```

2. Remove the login-page preview link

   File: `src/views/Login.vue`

   Delete the link that points to `/health-preview`, plus the `.preview-link` styles if they are no longer used.

3. Turn off the disposal frontend preview data

   File: `.env.local`

   Remove this line or set it to `0`:

   ```env
   VITE_TEMP_MAP_PREVIEW=1
   ```

4. Remove the disposal preview auth bypass

   File: `src/router/index.js`

   Delete the `TEMP_MAP_PREVIEW` constant and this guard block:

   ```js
   if (TEMP_MAP_PREVIEW && to.path === '/disposal-locations') {
     return true
   }
   ```

5. Remove the temporary frontend data module

   File: `src/api/index.js`

   Delete the `TEMP_MAP_PREVIEW` branch inside `searchDisposalLocation()`.

   Then delete:

   ```text
   src/api/tempMapPreview.js
   ```

Do not delete `backend/data_for_map/` unless the backend no longer needs local CSV fallback data.

## Useful Commands

### Build frontend

```powershell
npm run build
```

### Lint frontend

```powershell
npm run lint
```

### Check backend syntax

```powershell
python -m py_compile backend\main.py backend\health.py backend\location.py backend\login.py backend\optimizer.py
```

## Notes For Teammates

- The intended frontend integration surface is `getHealthAll()` and `searchDisposalLocation()`.
- The health preview route is only a public route alias for `Dashboard.vue`; the real dashboard route remains `/dashboard`.
- The disposal preview mode is temporary and is controlled by `VITE_TEMP_MAP_PREVIEW`.
- `requirements.txt` is for Python only. Frontend packages such as Leaflet, Mapbox, Vue, and Vite belong in `package.json`.
