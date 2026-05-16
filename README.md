# TA14-EcoTech

## Local Setup

### build local database

we use docker to create a virtual database, so you don't need to create a database in your local server. It helps us collaborate and run the 

```docker compose up db```

connect to the db using psql or pg admin4, and update database (insert data, change tables)

```pg_dump --no-owner --no-acl -U [username] -d [database_name] > ./migrations/backup.sql```


Vue 3 + Vite frontend, Flask + PostgreSQL backend. Iteration 3 adds the **Pickup Points** page (38 EcoReviva stalls across all Australian states).

## Repo layout

```
docker compose down -v
docker compose up -d
```

### Update database

try to start the postgresql first, if you use macOS, use homebrew to start it：

```brew services start postgresql```

Once you start it, you need to know these things:

- DB_HOST
- DB_USER
- DB_PASSWORD
- DB_NAME
- DB_PORT

and set them in **./backend/.env.local** file

then run backup.sql

```
dropdb -U username database_name
createdb -U username database_name
psql -U username -d database_name -f .backend/db/scripts/backup.sql
```



### Install frontend dependencies
```
npm install
npm run build
```
### Install backend dependencies

```
python -m venv .venv
backend/.venv/bin/activate
pip install -r ./backend/requirements.txt
```


### Start the backend

use one terminal 

```flask --app app run --host 0.0.0.0 --port 8000```

### Start the frontend

use the other terminal

```npm run dev```

Vite usually starts at `http://localhost:5173`. If that port is busy, it will choose the next available port.


## System Architecture

```text
User Browser
    |
    v
Vue Frontend
    |
    v
Flask Backend  --->  PostgreSQL
    |
    v
AI model: Groq API

Data loading:
backend/db/migrations/backup.sql -> local PostgreSQL
```

This is the high-level flow:
- the browser loads the Vue app
- the Vue app calls Flask through `/api`
- Flask reads data from PostgreSQL
- the AI route uses the Groq chat completions API for device optimisation responses
- the local loading script rebuilds the schema and imports CSV data into PostgreSQL


## Deployment

Cloud VM Server: AWS EC2 - t3 small

DNS:  https://freedns.afraid.org/ named "Free DNS" 

## Important Notes !!!

### Do not change other code blocks!
make sure your code will not affect the other's code, if you need it, make sure **write some docs** to explain your code


### If you have other questions please ask our team


## Tech Stack

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

When the `/api/pickup-stalls` backend endpoint is implemented, swap the mock import in `PickupPoints.vue` for the API call.
