import csv
import struct
import subprocess
import sys
from pathlib import Path

import pyodbc


BASE_DIR = Path("/Users/pcw/Documents/MONASH/TA14/TA14-EcoTech/mssql_geojson_loader")
OUTPUT_DIR = BASE_DIR / "output"

SERVER = "fit5120-t14-project-db.database.windows.net"
DATABASE = "sql-db"
DRIVER = "ODBC Driver 18 for SQL Server"

SQL_COPT_SS_ACCESS_TOKEN = 1256
SQL_SCOPE = "https://database.windows.net/"

csv.field_size_limit(sys.maxsize)


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
    token = get_access_token()
    token_struct = build_token_struct(token)

    conn_str = (
        f"Driver={{{DRIVER}}};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={DATABASE};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )

    return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})


def truncate_stage_tables(cursor):
    cursor.execute("TRUNCATE TABLE dbo.vic_lga_boundaries_stage;")
    cursor.execute("TRUNCATE TABLE dbo.vic_locality_boundaries_stage;")


def insert_lga_stage(cursor):
    file_path = OUTPUT_DIR / "vic_lga_gda2020_wkt.csv"
    sql = """
        INSERT INTO dbo.vic_lga_boundaries_stage (
            abb_name,
            dt_create,
            lga_name,
            lga_pid,
            lg_ply_pid,
            state,
            geometry_wkt,
            source_file
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    with file_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["abb_name"] or None,
                row["dt_create"] or None,
                row["lga_name"] or None,
                row["lga_pid"] or None,
                row["lg_ply_pid"] or None,
                row["state"] or None,
                row["geometry_wkt"] or None,
                row["source_file"] or None,
            )
            for row in reader
        ]

    cursor.fast_executemany = True
    cursor.executemany(sql, rows)


def insert_locality_stage(cursor):
    file_path = OUTPUT_DIR / "vic_loc_gda2020_wkt.csv"
    sql = """
        INSERT INTO dbo.vic_locality_boundaries_stage (
            dt_create,
            lc_ply_pid,
            loc_class,
            loc_name,
            loc_pid,
            state,
            geometry_wkt,
            source_file
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    with file_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["dt_create"] or None,
                row["lc_ply_pid"] or None,
                row["loc_class"] or None,
                row["loc_name"] or None,
                row["loc_pid"] or None,
                row["state"] or None,
                row["geometry_wkt"] or None,
                row["source_file"] or None,
            )
            for row in reader
        ]

    cursor.fast_executemany = True
    cursor.executemany(sql, rows)


def move_stage_to_final(cursor):
    cursor.execute(
        """
        INSERT INTO dbo.vic_lga_boundaries (
            abb_name,
            dt_create,
            lga_name,
            lga_pid,
            lg_ply_pid,
            state,
            geom,
            source_file
        )
        SELECT
            abb_name,
            dt_create,
            lga_name,
            lga_pid,
            lg_ply_pid,
            state,
            geometry::STGeomFromText(geometry_wkt, 7844),
            source_file
        FROM dbo.vic_lga_boundaries_stage;
        """
    )

    cursor.execute(
        """
        INSERT INTO dbo.vic_locality_boundaries (
            dt_create,
            lc_ply_pid,
            loc_class,
            loc_name,
            loc_pid,
            state,
            geom,
            source_file
        )
        SELECT
            dt_create,
            lc_ply_pid,
            loc_class,
            loc_name,
            loc_pid,
            state,
            geometry::STGeomFromText(geometry_wkt, 7844),
            source_file
        FROM dbo.vic_locality_boundaries_stage;
        """
    )


def main():
    with connect() as conn:
        conn.autocommit = False
        cursor = conn.cursor()
        truncate_stage_tables(cursor)
        insert_lga_stage(cursor)
        insert_locality_stage(cursor)
        move_stage_to_final(cursor)
        conn.commit()
        print("Import completed successfully.")


if __name__ == "__main__":
    main()
