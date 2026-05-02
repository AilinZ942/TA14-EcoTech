#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DATA_DIR="$BACKEND_DIR/db/data"
SCHEMA_FILE="$SCRIPT_DIR/schema.sql"
ENV_FILE="$BACKEND_DIR/.env.local"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ecotech-load-XXXXXX")"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT INT TERM

if [[ ! -f "$ENV_FILE" ]]; then
  echo "error"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-}"
DB_USER="${DB_USER:-}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_SSLMODE="${DB_SSLMODE:-prefer}"

if [[ -z "$DB_NAME" || -z "$DB_USER" ]]; then
  echo "error"
  exit 1
fi

export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"
export PGDATABASE="$DB_NAME"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"
export PGSSLMODE="$DB_SSLMODE"

filter_csv() {
  local source_file="$1"
  local target_file="$2"
  shift 2

  python3 - "$source_file" "$target_file" "$@" <<'PY'
import csv
import pathlib
import sys

source_file = pathlib.Path(sys.argv[1])
target_file = pathlib.Path(sys.argv[2])
columns = sys.argv[3:]

with source_file.open("r", encoding="utf-8-sig", newline="") as src, target_file.open(
    "w", encoding="utf-8", newline=""
) as dst:
    reader = csv.DictReader(src)
    writer = csv.writer(dst)
    writer.writerow(columns)
    for row in reader:
        writer.writerow([row.get(column, "") for column in columns])
PY
}

run_quiet() {
  if ! "$@" >/dev/null 2>&1; then
    echo "error"
    exit 1
  fi
}

run_psql_copy() {
  local sql="$1"
  if ! psql -v ON_ERROR_STOP=1 -q -c "$sql" >/dev/null 2>&1; then
    echo "error"
    exit 1
  fi
}

if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" >/dev/null 2>&1; then
  echo "error"
  exit 1
fi

run_quiet psql -v ON_ERROR_STOP=1 -q -f "$SCHEMA_FILE"

filter_csv \
  "$DATA_DIR/clean_ewaste_facilities_geocoded.csv" \
  "$TMP_DIR/clean_ewaste_facilities_geocoded.csv" \
  facility_name address suburb postcode state latitude longitude

run_psql_copy "\copy clean_ewaste_facilities_geocoded (facility_name, address, suburb, postcode, state, latitude, longitude) FROM '$TMP_DIR/clean_ewaste_facilities_geocoded.csv' WITH (FORMAT csv, HEADER true)"
run_psql_copy "\copy location_lookup (state_code, state_name, council, suburb, postcode) FROM '$DATA_DIR/location_lookup.csv' WITH (FORMAT csv, HEADER true)"
run_psql_copy "\copy australian_postcodes (postcode, locality, state, long, lat, dc, type, status, sa3, sa3name, sa4, sa4name, region, lat_precise, long_precise, sa1_code_2021, sa1_name_2021, sa2_code_2021, sa2_name_2021, sa3_code_2021, sa3_name_2021, sa4_code_2021, sa4_name_2021, ra_2011, ra_2016, ra_2021, ra_2021_name, mmm_2015, mmm_2019, ced, altitude, chargezone, phn_code, phn_name, lgaregion, lgacode, electorate, electoraterating, sed_code, sed_name) FROM '$DATA_DIR/australian_postcodes.csv' WITH (FORMAT csv, HEADER true)"
run_psql_copy "\copy ewaste_recycling_locations_curated (state_scope, state_full_name, provider_name, search_query, source_type, verification_level, place_id, display_name, formatted_address, suburb, state, postcode, latitude, longitude, national_phone_number, website_uri, google_maps_uri, business_status, primary_type, types, accepted_items, note, in_state_bbox, passes_name_filter, passes_state_filter, confidence_score, keep, data_quality_status, corrected_source_type, corrected_accepted_items, quality_reason, final_keep, manual_review_required) FROM '$DATA_DIR/ewaste_recycling_locations_curated.csv' WITH (FORMAT csv, HEADER true)"

echo "Loading OK"
