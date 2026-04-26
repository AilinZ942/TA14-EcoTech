import csv
import struct
import subprocess
from pathlib import Path

import pyodbc


BASE_DIR = Path("/Users/pcw/Documents/MONASH/TA14/TA14-EcoTech/database")

# Update these before running.
SERVER = "fit5120-t14-project-db.database.windows.net"
DATABASE = "sql-db"
DRIVER = "ODBC Driver 18 for SQL Server"

# Prefer the cleaned CSV generated in this folder.
CSV_FILE = BASE_DIR / "clean_ewaste_facilities_geocoded_clean.csv"

SQL_COPT_SS_ACCESS_TOKEN = 1256
SQL_SCOPE = "https://database.windows.net/"


def clean_text(value):
    if value is None:
        return None
    value = " ".join(str(value).strip().split())
    return value or None


def clean_float(value):
    value = clean_text(value)
    if value is None:
        return None
    return float(value)


def clean_int(value):
    value = clean_text(value)
    if value is None:
        return None
    return int(value)


def clean_bit(value):
    value = clean_text(value)
    if value is None:
        return None
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y"}:
        return 1
    if lowered in {"0", "false", "no", "n"}:
        return 0
    return None


def get_access_token():
    result = subprocess.run(
        [
            "az",
            "account",
            "get-access-token",
            "--resource",
            SQL_SCOPE,
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError("Failed to get Azure SQL access token from Azure CLI.")
    return token


def build_token_struct(token):
    token_bytes = token.encode("utf-16-le")
    return struct.pack("<I", len(token_bytes)) + token_bytes


def connect():
    token_struct = build_token_struct(get_access_token())
    conn_str = (
        f"Driver={{{DRIVER}}};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={DATABASE};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})


def ensure_table_exists(cursor):
    cursor.execute(
        """
        IF OBJECT_ID('dbo.clean_ewaste_facilities_geocoded', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.clean_ewaste_facilities_geocoded (
                id BIGINT IDENTITY(1,1) PRIMARY KEY,
                facility_name NVARCHAR(255) NOT NULL,
                address NVARCHAR(255) NULL,
                suburb NVARCHAR(100) NULL,
                postcode NVARCHAR(10) NULL,
                state NVARCHAR(10) NULL,
                latitude FLOAT NULL,
                longitude FLOAT NULL,
                coord_source NVARCHAR(50) NULL,
                duplicate_count INT NULL,
                source_file NVARCHAR(255) NULL,
                source_provenance NVARCHAR(255) NULL,
                ewaste_match_flag BIT NULL,
                ewaste_match_text NVARCHAR(255) NULL,
                ewaste_match_column NVARCHAR(100) NULL,
                review_flag NVARCHAR(255) NULL,
                dedupe_key NVARCHAR(255) NULL,
                original_latitude FLOAT NULL,
                original_longitude FLOAT NULL,
                original_coord_source NVARCHAR(50) NULL,
                maptiler_query NVARCHAR(255) NULL,
                maptiler_place_name NVARCHAR(255) NULL,
                maptiler_match_score FLOAT NULL,
                maptiler_feature_id NVARCHAR(100) NULL
            );
        END;
        """
    )


def read_rows():
    with CSV_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield (
                clean_text(row.get("facility_name")),
                clean_text(row.get("address")),
                clean_text(row.get("suburb")),
                clean_text(row.get("postcode")),
                clean_text(row.get("state")),
                clean_float(row.get("latitude")),
                clean_float(row.get("longitude")),
                clean_text(row.get("coord_source")),
                clean_int(row.get("duplicate_count")),
                clean_text(row.get("source_file")),
                clean_text(row.get("source_provenance")),
                clean_bit(row.get("ewaste_match_flag")),
                clean_text(row.get("ewaste_match_text")),
                clean_text(row.get("ewaste_match_column")),
                clean_text(row.get("review_flag")),
                clean_text(row.get("dedupe_key")),
                clean_float(row.get("original_latitude")),
                clean_float(row.get("original_longitude")),
                clean_text(row.get("original_coord_source")),
                clean_text(row.get("maptiler_query")),
                clean_text(row.get("maptiler_place_name")),
                clean_float(row.get("maptiler_match_score")),
                clean_text(row.get("maptiler_feature_id")),
            )


def insert_rows(cursor):
    sql = """
        INSERT INTO dbo.clean_ewaste_facilities_geocoded (
            facility_name,
            address,
            suburb,
            postcode,
            state,
            latitude,
            longitude,
            coord_source,
            duplicate_count,
            source_file,
            source_provenance,
            ewaste_match_flag,
            ewaste_match_text,
            ewaste_match_column,
            review_flag,
            dedupe_key,
            original_latitude,
            original_longitude,
            original_coord_source,
            maptiler_query,
            maptiler_place_name,
            maptiler_match_score,
            maptiler_feature_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    rows = list(read_rows())
    cursor.fast_executemany = True
    cursor.executemany(sql, rows)
    return len(rows)


def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    with connect() as conn:
        conn.autocommit = False
        cursor = conn.cursor()
        ensure_table_exists(cursor)
        inserted_count = insert_rows(cursor)
        conn.commit()
        print(f"Import completed successfully. Inserted {inserted_count} rows.")


if __name__ == "__main__":
    main()
