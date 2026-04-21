from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import os

app = FastAPI()


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "myuser"),
        password=os.environ.get("DB_PASSWORD", "yourpassword"),
        dbname=os.environ.get("DB_NAME", "mydb"),
        port=5432
    )

def row_to_disposal_item(row):
    return {
        "facility_name": row["facility_name"],
        "address": row["address"],
        "suburb": row["suburb"],
        "postcode": row["postcode"],
        "state": row["state"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
    }

@app.post("/map/disposal-locations/search")
def search_all_disposal_locations():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT
            facility_name,
            address,
            suburb,
            postcode,
            state,
            latitude,
            longitude
        FROM ewaste_facilities
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY suburb, facility_name
    """)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    items = [row_to_disposal_item(row) for row in rows]
    
    return {
        "items": items,
        "meta": {
            "pipeline": "fastapi",
            "source": "postgresql",
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}