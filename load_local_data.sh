#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
DATA_DIR="$BACKEND_DIR/db/data"
SCHEMA_FILE="$BACKEND_DIR/db/scripts/schema.sql"
ENV_FILE="$BACKEND_DIR/.env.local"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ecotech-load-XXXXXX")"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT INT TERM

fail() {
  echo "error"
  exit 1
}

run_with_error() {
  local output
  if ! output="$("$@" 2>&1)"; then
    if [[ -n "$output" ]]; then
      printf '%s\n' "$output"
    fi
    fail
  fi
}

escape_sql_literal() {
  local value="$1"
  printf "%s" "${value//\'/\'\'}"
}

filter_csv_columns() {
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

copy_csv() {
  local table_name="$1"
  local csv_file="$2"
  shift 2

  local columns_sql
  local IFS=,
  columns_sql="$*"

  local escaped_file
  escaped_file="$(escape_sql_literal "$csv_file")"

  run_with_error psql -v ON_ERROR_STOP=1 -q -c "\copy $table_name ($columns_sql) FROM '$escaped_file' WITH (FORMAT csv, HEADER true)"
}

if [[ ! -f "$ENV_FILE" ]]; then
  fail
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
  fail
fi

if [[ ! -f "$SCHEMA_FILE" ]]; then
  fail
fi

export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"
export PGDATABASE="$DB_NAME"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"
export PGSSLMODE="$DB_SSLMODE"

pg_ready_output=""
if ! pg_ready_output="$(pg_isready -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" 2>&1)"; then
  if [[ -n "$pg_ready_output" ]]; then
    printf '%s\n' "$pg_ready_output"
  fi
  fail
fi

run_with_error psql -v ON_ERROR_STOP=1 -q -c "SELECT 1"
run_with_error psql -v ON_ERROR_STOP=1 -q -f "$SCHEMA_FILE"

if [[ ! -f "$DATA_DIR/final_health_merged_dataset.csv" ]]; then
  fail
fi
copy_csv \
  health_merged \
  "$DATA_DIR/final_health_merged_dataset.csv" \
  year sex cancer_type cancer_cases cancer_deaths fatality_ratio

if [[ ! -f "$DATA_DIR/heavy_metal_state.csv" ]]; then
  fail
fi
copy_csv \
  heavy_metal_state \
  "$DATA_DIR/heavy_metal_state.csv" \
  report_year state metal total_air_emission_kg total_water_emission_kg total_land_emission_kg facility_count

if [[ ! -f "$DATA_DIR/heavy_metal_facility.csv" ]]; then
  fail
fi
copy_csv \
  heavy_metal_facility \
  "$DATA_DIR/heavy_metal_facility.csv" \
  report_year facility_id facility_name state postcode latitude longitude metal total_air_emission_kg total_water_emission_kg total_land_emission_kg

if [[ ! -f "$DATA_DIR/location_lookup.csv" ]]; then
  fail
fi
copy_csv \
  location_lookup \
  "$DATA_DIR/location_lookup.csv" \
  state_code state_name council suburb postcode

if [[ ! -f "$DATA_DIR/australian_postcodes.csv" ]]; then
  fail
fi
filter_csv_columns \
  "$DATA_DIR/australian_postcodes.csv" \
  "$TMP_DIR/australian_postcodes.csv" \
  postcode locality state long lat dc type status sa3 sa3name sa4 sa4name region lat_precise long_precise sa1_code_2021 sa1_name_2021 sa2_code_2021 sa2_name_2021 sa3_code_2021 sa3_name_2021 sa4_code_2021 sa4_name_2021 ra_2011 ra_2016 ra_2021 ra_2021_name mmm_2015 mmm_2019 ced altitude chargezone phn_code phn_name lgaregion lgacode electorate electoraterating sed_code sed_name
copy_csv \
  australian_postcodes \
  "$TMP_DIR/australian_postcodes.csv" \
  postcode locality state long lat dc type status sa3 sa3name sa4 sa4name region lat_precise long_precise sa1_code_2021 sa1_name_2021 sa2_code_2021 sa2_name_2021 sa3_code_2021 sa3_name_2021 sa4_code_2021 sa4_name_2021 ra_2011 ra_2016 ra_2021 ra_2021_name mmm_2015 mmm_2019 ced altitude chargezone phn_code phn_name lgaregion lgacode electorate electoraterating sed_code sed_name

if [[ ! -f "$DATA_DIR/clean_ewaste_facilities_geocoded.csv" ]]; then
  fail
fi
filter_csv_columns \
  "$DATA_DIR/clean_ewaste_facilities_geocoded.csv" \
  "$TMP_DIR/clean_ewaste_facilities_geocoded.csv" \
  facility_name address suburb postcode state latitude longitude
copy_csv \
  clean_ewaste_facilities_geocoded \
  "$TMP_DIR/clean_ewaste_facilities_geocoded.csv" \
  facility_name address suburb postcode state latitude longitude

if [[ ! -f "$DATA_DIR/ewaste_recycling_locations_curated.csv" ]]; then
  fail
fi
copy_csv \
  ewaste_recycling_locations_curated \
  "$DATA_DIR/ewaste_recycling_locations_curated.csv" \
  state_scope state_full_name provider_name search_query source_type verification_level place_id display_name formatted_address suburb state postcode latitude longitude national_phone_number website_uri google_maps_uri business_status primary_type types accepted_items note in_state_bbox passes_name_filter passes_state_filter confidence_score keep data_quality_status corrected_source_type corrected_accepted_items quality_reason final_keep manual_review_required

echo "Loading OK"
