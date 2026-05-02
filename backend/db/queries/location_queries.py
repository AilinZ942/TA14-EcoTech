"""SQL strings for location/disposal features."""

SELECT_DISPOSAL_ITEMS = """
    SELECT
        facility_name,
        address,
        suburb,
        postcode,
        state,
        latitude,
        longitude,
        ewaste_category,
        ewaste_match_text,
        ewaste_match_column,
        source,
        source_file,
        coord_source,
        dedupe_key,
        accepted_items,
        note,
        national_phone_number,
        website_uri,
        google_maps_uri,
        business_status,
        data_quality_status,
        quality_reason
    FROM (
        SELECT
            facility_name,
            address,
            suburb,
            postcode,
            state,
            latitude,
            longitude,
            NULL::TEXT AS ewaste_category,
            NULL::TEXT AS ewaste_match_text,
            NULL::TEXT AS ewaste_match_column,
            'local_csv_geocoded' AS source,
            NULL::TEXT AS source_file,
            NULL::TEXT AS coord_source,
            NULL::TEXT AS dedupe_key,
            NULL::TEXT AS accepted_items,
            NULL::TEXT AS note,
            NULL::TEXT AS national_phone_number,
            NULL::TEXT AS website_uri,
            NULL::TEXT AS google_maps_uri,
            NULL::TEXT AS business_status,
            NULL::TEXT AS data_quality_status,
            NULL::TEXT AS quality_reason
        FROM clean_ewaste_facilities_geocoded
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL

        UNION ALL

        SELECT
            COALESCE(display_name, provider_name) AS facility_name,
            formatted_address AS address,
            suburb,
            postcode,
            state,
            latitude,
            longitude,
            COALESCE(corrected_source_type, source_type) AS ewaste_category,
            COALESCE(corrected_accepted_items, accepted_items) AS ewaste_match_text,
            COALESCE(corrected_source_type, source_type) AS ewaste_match_column,
            'local_csv_curated' AS source,
            'ewaste_recycling_locations_curated.csv' AS source_file,
            'google_places' AS coord_source,
            place_id AS dedupe_key,
            COALESCE(corrected_accepted_items, accepted_items) AS accepted_items,
            note,
            national_phone_number,
            website_uri,
            google_maps_uri,
            business_status,
            data_quality_status,
            quality_reason
        FROM ewaste_recycling_locations_curated
        WHERE COALESCE(final_keep, TRUE) = TRUE
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
    ) AS disposal_items
    ORDER BY state, suburb, facility_name
"""

SELECT_LOCATION_LOOKUP = """
    SELECT
        state_code,
        state_name,
        council,
        suburb,
        postcode
    FROM location_lookup
    ORDER BY state_code, suburb, council
"""

SELECT_POSTCODES = """
    SELECT
        postcode,
        locality,
        state,
        long,
        lat,
        region,
        lat_precise,
        long_precise,
        lgaregion
    FROM australian_postcodes
    ORDER BY state, postcode, locality
"""
