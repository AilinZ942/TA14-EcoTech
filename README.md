# TA14-EcoTech (EcoReviva)

Vue 3 + Vite frontend, Flask + PostgreSQL backend. Iteration 3 adds the **Pickup Points** page (38 EcoReviva stalls across all Australian states).

## Repo layout

```
TA14-EcoTech/
├── frontend/              # Vue 3 + Vite app
│   ├── src/
│   │   ├── views/         # Home, Dashboard, Game, AIChat, RepairCheck,
│   │   │                  # DisposalLocations, PickupPoints (NEW), Login
│   │   ├── components/    # AppNavbar, etc.
│   │   ├── lib/           # pickupStallsMock.js (NEW — mock pickup stall data)
│   │   ├── router/
│   │   └── api/
│   ├── package.json
│   └── vite.config.js
├── backend/               # Flask app
│   ├── app.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── db/
│   │   └── migrations/backup.sql
│   └── requirements.txt
└── README.md
```

## Local setup

### Frontend
```
cd frontend
npm install
npm run dev          # http://localhost:5173
```

### Backend (optional — frontend works with mocks if backend is down)
```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --host 0.0.0.0 --port 8000
```

### Database (only for live disposal-locations data)
```
createdb -U <user> ecotech
psql -U <user> -d ecotech -f backend/db/migrations/backup.sql
```
Create `backend/.env.local` with `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`.

### Mapbox (optional — for the live pickup map)
Create `frontend/.env.local`:
```
VITE_MAPBOX_ACCESS_TOKEN=pk.your_public_token_here
```
**Never commit `sk.` (secret) tokens.** Only `pk.` (public) tokens belong in browser code.

## What's new in this iteration

- **`frontend/src/views/PickupPoints.vue`** — buyer flow (browse devices, find stalls), seller flow (nearest stall + accept rules), interactive map
- **`frontend/src/lib/pickupStallsMock.js`** — 38 stalls × 3-5 devices each, across VIC, NSW, QLD, WA, SA, TAS, ACT, NT
- **`frontend/src/router/index.js`** — added `/pickup-points` route
- **`frontend/src/App.vue`** — added Pickup Points navbar link
- **`frontend/src/api/index.js`** — added `getPickupStalls()` and `reservePickupDevice()` stubs

When the `/api/pickup-stalls` backend endpoint is implemented, swap the mock import in `PickupPoints.vue` for the API call.ss