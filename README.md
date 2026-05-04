# TA14-EcoTech


## Local Setup

### build local database

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
AI model: llama-cpp-python

Data loading:
backend/db/migrations/backup.sql -> local PostgreSQL
```

This is the high-level flow:
- the browser loads the Vue app
- the Vue app calls Flask through `/api`
- Flask reads data from PostgreSQL
- the AI route uses the local Qwen model through `llama-cpp-python`
- the local loading script rebuilds the schema and imports CSV data into PostgreSQL




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
- llama-cpp-python for AI model loading
- huggingface-hub for downloading model
- pyshp
- gunicorn for serving python on web


Python dependencies are listed in  `backend/requirements.txt`.




