from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Blueprint, jsonify
import psycopg2.extras
from psycopg2 import pool

from login import login_required


load_dotenv()

location_bp = Blueprint("location", __name__)

connection_pool = None


def get_connection_pool():
    global connection_pool

    if connection_pool is not None:
        return connection_pool

    try:
        connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "myuser"),
            password=os.environ.get("DB_PASSWORD", "mypassword"),
            dbname=os.environ.get("DB_NAME", "mydb"),
            port=5432,
        )
    except Exception as exc:
        raise RuntimeError("Database unavailable") from exc

    return connection_pool


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


def fetch_all_disposal_locations():
    pool_instance = get_connection_pool()
    conn = pool_instance.getconn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
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
            """
        )
        rows = cur.fetchall()
        cur.close()

        return {
            "items": [row_to_disposal_item(row) for row in rows],
            "meta": {
                "pipeline": "flask",
                "source": "postgresql",
            },
        }
    finally:
        pool_instance.putconn(conn)


@location_bp.route("/map/disposal-locations", methods=["GET"])
@login_required
def search_all_disposal_locations():
    try:
        payload = fetch_all_disposal_locations()
    except RuntimeError as exc:
        return jsonify({"detail": str(exc)}), 503

    return jsonify(payload)
