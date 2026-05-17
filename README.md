# TA14-EcoTech

## Local Setup

### build local database

we use docker to create a virtual database, so you don't need to create a database in your local server. It helps us collaborate and run the the server. First you need to download docker from [Docker desktop](https://www.docker.com/)


After downloading the docker desktop, you need to open it. then you need to run the docker command:

```
cd backend
docker compose up --build -d
```

to build the database. Once you have done that, you can find that the backend service is running.

You can connect to the db using psql or pg admin4, and update database (insert data, change tables), after that, you need to update the backup file by using this command

```pg_dump --no-owner --no-acl -U user -d my_database > ./migrations/backup.sql```


Every time when you change the backend code or update the database, you need to rebuild it

```
docker compose down -v
docker compose up --build -d
```

More docker details can be found on their website.


### Install frontend dependencies

```
cd frontend
npm install
npm run build
```

### Start the frontend service

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


