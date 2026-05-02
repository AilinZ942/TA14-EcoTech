-- EcoTech PostgreSQL schema.
-- Run once against the target database (local Postgres or AWS RDS).

DROP TABLE IF EXISTS health_merged CASCADE;
DROP TABLE IF EXISTS heavy_metal_state CASCADE;
DROP TABLE IF EXISTS heavy_metal_facility CASCADE;
DROP TABLE IF EXISTS australian_postcodes CASCADE;
DROP TABLE IF EXISTS location_lookup CASCADE;
DROP TABLE IF EXISTS ewaste_recycling_locations_curated CASCADE;
DROP TABLE IF EXISTS clean_ewaste_facilities_geocoded CASCADE;

CREATE TABLE health_merged (
    id              SERIAL PRIMARY KEY,
    year            INTEGER NOT NULL,
    sex             TEXT,
    cancer_type     TEXT,
    cancer_cases    DOUBLE PRECISION,
    cancer_deaths   DOUBLE PRECISION,
    fatality_ratio  DOUBLE PRECISION
);
CREATE INDEX idx_health_year       ON health_merged (year);
CREATE INDEX idx_health_sex        ON health_merged (sex);
CREATE INDEX idx_health_cancer     ON health_merged (cancer_type);

CREATE TABLE heavy_metal_state (
    id                       SERIAL PRIMARY KEY,
    report_year              INTEGER NOT NULL,
    state                    TEXT NOT NULL,
    metal                    TEXT NOT NULL,
    total_air_emission_kg    DOUBLE PRECISION,
    total_water_emission_kg  DOUBLE PRECISION,
    total_land_emission_kg   DOUBLE PRECISION,
    facility_count           INTEGER
);
CREATE INDEX idx_state_year   ON heavy_metal_state (report_year);
CREATE INDEX idx_state_state  ON heavy_metal_state (state);
CREATE INDEX idx_state_metal  ON heavy_metal_state (metal);

CREATE TABLE heavy_metal_facility (
    id                       SERIAL PRIMARY KEY,
    report_year              INTEGER NOT NULL,
    facility_id              TEXT,
    facility_name            TEXT,
    state                    TEXT,
    postcode                 TEXT,
    latitude                 DOUBLE PRECISION,
    longitude                DOUBLE PRECISION,
    metal                    TEXT,
    total_air_emission_kg    DOUBLE PRECISION,
    total_water_emission_kg  DOUBLE PRECISION,
    total_land_emission_kg   DOUBLE PRECISION
);
CREATE INDEX idx_fac_year     ON heavy_metal_facility (report_year);
CREATE INDEX idx_fac_state    ON heavy_metal_facility (state);
CREATE INDEX idx_fac_postcode ON heavy_metal_facility (postcode);


CREATE TABLE clean_ewaste_facilities_geocoded (
    id                    SERIAL PRIMARY KEY,
    facility_name         TEXT NOT NULL,
    address               TEXT,
    suburb                TEXT,
    postcode              TEXT,
    state                 TEXT,
    latitude              DOUBLE PRECISION,
    longitude             DOUBLE PRECISION
);
CREATE INDEX idx_geocoded_state ON clean_ewaste_facilities_geocoded (state);
CREATE INDEX idx_geocoded_postcode ON clean_ewaste_facilities_geocoded (postcode);
CREATE INDEX idx_geocoded_suburb ON clean_ewaste_facilities_geocoded (suburb);

CREATE TABLE ewaste_recycling_locations_curated (
    id                       SERIAL PRIMARY KEY,
    state_scope              TEXT,
    state_full_name          TEXT,
    provider_name            TEXT,
    search_query             TEXT,
    source_type              TEXT,
    verification_level       TEXT,
    place_id                 TEXT,
    display_name             TEXT,
    formatted_address        TEXT,
    suburb                   TEXT,
    state                    TEXT,
    postcode                 TEXT,
    latitude                 DOUBLE PRECISION,
    longitude                DOUBLE PRECISION,
    national_phone_number    TEXT,
    website_uri              TEXT,
    google_maps_uri          TEXT,
    business_status          TEXT,
    primary_type             TEXT,
    types                    TEXT,
    accepted_items           TEXT,
    note                     TEXT,
    in_state_bbox            BOOLEAN,
    passes_name_filter       BOOLEAN,
    passes_state_filter      BOOLEAN,
    confidence_score         DOUBLE PRECISION,
    keep                     BOOLEAN,
    data_quality_status      TEXT,
    corrected_source_type    TEXT,
    corrected_accepted_items TEXT,
    quality_reason           TEXT,
    final_keep               BOOLEAN,
    manual_review_required   BOOLEAN
);
CREATE INDEX idx_curated_state ON ewaste_recycling_locations_curated (state);
CREATE INDEX idx_curated_postcode ON ewaste_recycling_locations_curated (postcode);
CREATE INDEX idx_curated_suburb ON ewaste_recycling_locations_curated (suburb);
CREATE INDEX idx_curated_place_id ON ewaste_recycling_locations_curated (place_id);
CREATE INDEX idx_curated_final_keep ON ewaste_recycling_locations_curated (final_keep);

CREATE TABLE location_lookup (
    id           SERIAL PRIMARY KEY,
    state_code   TEXT,
    state_name   TEXT,
    council      TEXT,
    suburb       TEXT,
    postcode     TEXT
);
CREATE INDEX idx_location_lookup_state_postcode_suburb
    ON location_lookup (state_code, postcode, suburb);
CREATE INDEX idx_location_lookup_council ON location_lookup (council);

CREATE TABLE australian_postcodes (
    id                  SERIAL PRIMARY KEY,
    postcode            TEXT,
    locality            TEXT,
    state               TEXT,
    long                DOUBLE PRECISION,
    lat                 DOUBLE PRECISION,
    dc                  TEXT,
    type                TEXT,
    status              TEXT,
    sa3                 TEXT,
    sa3name             TEXT,
    sa4                 TEXT,
    sa4name             TEXT,
    region              TEXT,
    lat_precise         DOUBLE PRECISION,
    long_precise        DOUBLE PRECISION,
    sa1_code_2021       TEXT,
    sa1_name_2021       TEXT,
    sa2_code_2021       TEXT,
    sa2_name_2021       TEXT,
    sa3_code_2021       TEXT,
    sa3_name_2021       TEXT,
    sa4_code_2021       TEXT,
    sa4_name_2021       TEXT,
    ra_2011             TEXT,
    ra_2016             TEXT,
    ra_2021             TEXT,
    ra_2021_name        TEXT,
    mmm_2015            TEXT,
    mmm_2019            TEXT,
    ced                 TEXT,
    altitude            TEXT,
    chargezone          TEXT,
    phn_code            TEXT,
    phn_name            TEXT,
    lgaregion           TEXT,
    lgacode             TEXT,
    electorate          TEXT,
    electoraterating    TEXT,
    sed_code            TEXT,
    sed_name            TEXT
);
CREATE INDEX idx_postcodes_state_postcode_locality
    ON australian_postcodes (state, postcode, locality);
CREATE INDEX idx_postcodes_lga_region ON australian_postcodes (lgaregion);
