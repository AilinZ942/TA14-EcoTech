# TA14-EcoTech

## Local Setup

### build local database

we use docker to create a virtual database, so you don't need to create a database in your local server. It helps us collaborate and run the 

```docker compose up db```

connect to the db using psql or pg admin4, and update database (insert data, change tables)

```pg_dump --no-owner --no-acl -U [username] -d [database_name] > ./migrations/backup.sql```




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

<<<<<<< HEAD
Cloud VM Server: AWS EC2 - t3 small
=======
Cloud VM Server: AWS EC2 - m7i-flex.large
>>>>>>> parent of fa1ed8b (Reapply "added pickup location page")

DNS:  https://freedns.afraid.org/ named "Free DNS" 

## Important Notes !!!

### Do not change other code blocks!
make sure your code will not affect the other's code, if you need it, make sure **write some docs** to explain your code


### If you have other questions please ask our team




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
- psycopg2-binary
- requests
- requests for calling the Groq API
- pyshp
- gunicorn for serving python on web


Python dependencies are listed in  `backend/requirements.txt`.


When the `/api/pickup-stalls` backend endpoint is implemented, swap the mock import in `PickupPoints.vue` for the API call.ss
When the `/api/pickup-stalls` backend endpoint is implemented, swap the mock import in `PickupPoints.vue` for the API call.
