#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ROOT_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
DATA_DIR="$BACKEND_DIR/db/data"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ecotech-db-XXXXXX")"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT INT TERM

load_env_file() {
  local env_file="$1"
  if [[ -f "$env_file" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$env_file"
    set +a
  fi
}

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

ensure_postgres_running() {
  if pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
    return 0
  fi

  echo "PostgreSQL is not running or not reachable at ${DB_HOST}:${DB_PORT}."
  echo "Please start your local PostgreSQL server manually, then rerun this script."
  exit 1
}

load_env_file "$BACKEND_DIR/.env.local"
load_env_file "$ROOT_DIR/.env.local"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-localdb}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_SSLMODE="${DB_SSLMODE:-prefer}"

export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"
export PGDATABASE="$DB_NAME"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"
export PGSSLMODE="$DB_SSLMODE"

cd "$ROOT_DIR"

ensure_postgres_running

dropdb --if-exists "$DB_NAME"
createdb "$DB_NAME"
psql -d "$DB_NAME" -f "$SCRIPT_DIR/schema.sql"

filter_csv \
  "$DATA_DIR/clean_ewaste_facilities_geocoded.csv" \
  "$TMP_DIR/clean_ewaste_facilities_geocoded.csv" \
  facility_name address suburb postcode state latitude longitude
filter_csv \
  "$DATA_DIR/location_lookup.csv" \
  "$TMP_DIR/location_lookup.csv" \
  state_code state_name council suburb postcode
filter_csv \
  "$DATA_DIR/australian_postcodes.csv" \
  "$TMP_DIR/australian_postcodes.csv" \
  postcode locality state long lat dc type status sa3 sa3name sa4 sa4name region lat_precise long_precise sa1_code_2021 sa1_name_2021 sa2_code_2021 sa2_name_2021 sa3_code_2021 sa3_name_2021 sa4_code_2021 sa4_name_2021 ra_2011 ra_2016 ra_2021 ra_2021_name mmm_2015 mmm_2019 ced altitude chargezone phn_code phn_name lgaregion lgacode electorate electoraterating sed_code sed_name
filter_csv \
  "$DATA_DIR/ewaste_recycling_locations_curated.csv" \
  "$TMP_DIR/ewaste_recycling_locations_curated.csv" \
  state_scope state_full_name provider_name search_query source_type verification_level place_id display_name formatted_address suburb state postcode latitude longitude national_phone_number website_uri google_maps_uri business_status primary_type types accepted_items note in_state_bbox passes_name_filter passes_state_filter confidence_score keep data_quality_status corrected_source_type corrected_accepted_items quality_reason final_keep manual_review_required

psql -d "$DB_NAME" -c "\copy clean_ewaste_facilities_geocoded (facility_name, address, suburb, postcode, state, latitude, longitude) FROM '$TMP_DIR/clean_ewaste_facilities_geocoded.csv' WITH (FORMAT csv, HEADER true)"
psql -d "$DB_NAME" -c "\copy location_lookup (state_code, state_name, council, suburb, postcode) FROM '$TMP_DIR/location_lookup.csv' WITH (FORMAT csv, HEADER true)"
psql -d "$DB_NAME" -c "\copy australian_postcodes (postcode, locality, state, long, lat, dc, type, status, sa3, sa3name, sa4, sa4name, region, lat_precise, long_precise, sa1_code_2021, sa1_name_2021, sa2_code_2021, sa2_name_2021, sa3_code_2021, sa3_name_2021, sa4_code_2021, sa4_name_2021, ra_2011, ra_2016, ra_2021, ra_2021_name, mmm_2015, mmm_2019, ced, altitude, chargezone, phn_code, phn_name, lgaregion, lgacode, electorate, electoraterating, sed_code, sed_name) FROM '$TMP_DIR/australian_postcodes.csv' WITH (FORMAT csv, HEADER true)"
psql -d "$DB_NAME" -c "\copy ewaste_recycling_locations_curated (state_scope, state_full_name, provider_name, search_query, source_type, verification_level, place_id, display_name, formatted_address, suburb, state, postcode, latitude, longitude, national_phone_number, website_uri, google_maps_uri, business_status, primary_type, types, accepted_items, note, in_state_bbox, passes_name_filter, passes_state_filter, confidence_score, keep, data_quality_status, corrected_source_type, corrected_accepted_items, quality_reason, final_keep, manual_review_required) FROM '$TMP_DIR/ewaste_recycling_locations_curated.csv' WITH (FORMAT csv, HEADER true)"

echo "Local database loaded successfully."
