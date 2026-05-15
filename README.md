# TA14-EcoTech

## Local Setup

### build local database and backend

we use docker to create a virtual database, so you don't need to create a database in your local server. It helps us collaborate and run the server and database.

if you want to run the backend, every time you need to:

go the /backend

```docker compose up --build -d```


you can connect to the db using psql or pg admin4, and update database (insert data, change tables), then you need to update the backup database

```pg_dump --no-owner --no-acl -U [username] -d [database_name] > ./migrations/backup.sql```

if you want to shut down the backend in local, you need to:

```docker compose down -v```



### Start the frontend

use the other terminal

go to /frontend

```npm run build```

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

Cloud VM Server: AWS EC2 - m7i-flex.large

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


