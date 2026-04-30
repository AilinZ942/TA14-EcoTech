from __future__ import annotations

import os
import csv
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
import psycopg2.extras
from psycopg2 import pool

from login import login_required


load_dotenv()

location_bp = Blueprint("location", __name__)

connection_pool = None
DATA_FOR_MAP_DIR = Path(__file__).resolve().parent / "data_for_map"
DEFAULT_SEARCH_STATE = "VIC"
NEARBY_PROFILE_LIMIT = 6

CSV_SOURCE_FILES = {
    "geocoded_facilities": "clean_ewaste_facilities_geocoded.csv",
    "curated_locations": "ewaste_recycling_locations_curated.csv",
    "location_lookup": "location_lookup.csv",
    "postcodes": "australian_postcodes.csv",
}


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
            port=int(os.environ.get("DB_PORT", "5432")),
        )
    except Exception as exc:
        raise RuntimeError("Database unavailable") from exc

    return connection_pool


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_bool(value):
    return clean_text(value).lower() in {"1", "true", "yes", "y"}


def normalize_state(value):
    return clean_text(value).upper()


def to_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def canonical_key(*parts):
    return "|".join(clean_text(part).lower() for part in parts if clean_text(part))


def normalize_lookup_key(value):
    text = clean_text(value).upper()
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
    text = (
        text.replace("THE CITY OF ", "")
        .replace("CITY OF ", "")
        .replace(" CITY COUNCIL", "")
        .replace(" COUNCIL", "")
        .replace(" SHIRE", "")
        .replace("-", " ")
        .replace("_", " ")
        .replace(".", "")
    )
    return re.sub(r"\s+", " ", text).strip()


def read_csv_rows(filename):
    path = DATA_FOR_MAP_DIR / filename
    if not path.exists():
        raise RuntimeError(f"CSV file missing: {filename}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_to_disposal_item(row):
    return {
        "facility_name": clean_text(row.get("facility_name")),
        "address": clean_text(row.get("address")),
        "suburb": clean_text(row.get("suburb")),
        "postcode": clean_text(row.get("postcode")),
        "state": normalize_state(row.get("state")),
        "latitude": to_float(row.get("latitude")),
        "longitude": to_float(row.get("longitude")),
        "ewaste_category": clean_text(row.get("ewaste_category")),
        "ewaste_match_text": clean_text(row.get("ewaste_match_text")),
        "ewaste_match_column": clean_text(row.get("ewaste_match_column")),
        "source": clean_text(row.get("source", "cloud_database")),
        "source_file": clean_text(row.get("source_file")),
        "coord_source": clean_text(row.get("coord_source")),
        "dedupe_key": clean_text(row.get("dedupe_key")),
        "accepted_items": clean_text(row.get("accepted_items")),
        "note": clean_text(row.get("note")),
        "national_phone_number": clean_text(row.get("national_phone_number")),
        "website_uri": clean_text(row.get("website_uri")),
        "google_maps_uri": clean_text(row.get("google_maps_uri")),
        "business_status": clean_text(row.get("business_status")),
        "data_quality_status": clean_text(row.get("data_quality_status")),
        "quality_reason": clean_text(row.get("quality_reason")),
    }


def fetch_cloud_disposal_locations():
    pool_instance = get_connection_pool()
    conn = pool_instance.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM ewaste_facilities
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
                ORDER BY suburb, facility_name
                """
            )
            rows = cur.fetchall()

        return {
            "items": [row_to_disposal_item(row) for row in rows],
            "meta": {
                "pipeline": "cloud_database",
                "source": "postgresql",
                "row_count": len(rows),
            },
        }
    finally:
        pool_instance.putconn(conn)


def build_location_lookup(rows):
    lookup = {}
    for row in rows:
        key = canonical_key(row.get("state_code"), row.get("postcode"), row.get("suburb"))
        if key:
            lookup[key] = {
                "state_full_name": clean_text(row.get("state_name")),
                "council": clean_text(row.get("council")),
            }
    return lookup


def build_postcode_lookup(rows):
    lookup = {}
    for row in rows:
        key = canonical_key(row.get("state"), row.get("postcode"), row.get("locality"))
        if key:
            lookup[key] = {
                "postcode_latitude": to_float(row.get("Lat_precise") or row.get("lat")),
                "postcode_longitude": to_float(row.get("Long_precise") or row.get("long")),
                "lga_region": clean_text(row.get("lgaregion")),
                "region": clean_text(row.get("region")),
            }
    return lookup


def load_lookup_context():
    location_rows = read_csv_rows(CSV_SOURCE_FILES["location_lookup"])
    postcode_rows = read_csv_rows(CSV_SOURCE_FILES["postcodes"])
    profiles = build_location_profiles(location_rows, postcode_rows)
    return {
        "location_rows": location_rows,
        "postcode_rows": postcode_rows,
        "location_lookup": build_location_lookup(location_rows),
        "postcode_lookup": build_postcode_lookup(postcode_rows),
        "profiles": profiles,
    }


def enrich_with_lookup(item, location_lookup, postcode_lookup):
    lookup_key = canonical_key(item.get("state"), item.get("postcode"), item.get("suburb"))

    location_data = location_lookup.get(lookup_key, {})
    postcode_data = postcode_lookup.get(lookup_key, {})

    enriched = {
        **item,
        **{key: value for key, value in location_data.items() if value},
        **{key: value for key, value in postcode_data.items() if value not in ("", None)},
    }

    if enriched.get("latitude") is None:
        enriched["latitude"] = postcode_data.get("postcode_latitude")
    if enriched.get("longitude") is None:
        enriched["longitude"] = postcode_data.get("postcode_longitude")

    return enriched


def bounds_from_points(points):
    valid_points = [
        point
        for point in points
        if point and point.get("latitude") is not None and point.get("longitude") is not None
    ]
    if not valid_points:
        return None

    return {
        "minLatitude": min(point["latitude"] for point in valid_points),
        "maxLatitude": max(point["latitude"] for point in valid_points),
        "minLongitude": min(point["longitude"] for point in valid_points),
        "maxLongitude": max(point["longitude"] for point in valid_points),
    }


def state_label_from_code(state_code):
    return {
        "ACT": "Australian Capital Territory",
        "NSW": "New South Wales",
        "NT": "Northern Territory",
        "QLD": "Queensland",
        "SA": "South Australia",
        "TAS": "Tasmania",
        "VIC": "Victoria",
        "WA": "Western Australia",
    }.get(normalize_state(state_code), normalize_state(state_code))


def haversine_km(first, second):
    if not first or not second:
        return None

    first_lat = first.get("latitude")
    first_lon = first.get("longitude")
    second_lat = second.get("latitude")
    second_lon = second.get("longitude")
    if None in (first_lat, first_lon, second_lat, second_lon):
        return None

    radius_km = 6371
    lat1 = math.radians(first_lat)
    lat2 = math.radians(second_lat)
    delta_lat = math.radians(second_lat - first_lat)
    delta_lon = math.radians(second_lon - first_lon)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_location_profiles(location_rows, postcode_rows):
    profiles = {}

    def ensure_profile(tier, state, label, match_type):
        state_code = normalize_state(state)
        label_text = clean_text(label)
        if not state_code or not label_text:
            return None

        key = f"{tier}|{state_code}|{normalize_lookup_key(label_text)}"
        if key not in profiles:
            profiles[key] = {
                "key": key,
                "label": label_text,
                "state": state_code,
                "tier": tier,
                "match_type": match_type,
                "aliases": {normalize_lookup_key(label_text)},
                "suburbs": set(),
                "councils": set(),
                "postcodes": set(),
                "points": [],
            }
        return profiles[key]

    def add_profile_location(profile, suburb="", postcode="", council="", point=None):
        if not profile:
            return

        suburb_key = normalize_lookup_key(suburb)
        council_key = normalize_lookup_key(council)
        postcode_text = clean_text(postcode)

        if suburb_key:
            profile["suburbs"].add(suburb_key)
        if council_key:
            profile["councils"].add(council_key)
        if postcode_text:
            profile["postcodes"].add(postcode_text)
        if point and point.get("latitude") is not None and point.get("longitude") is not None:
            profile["points"].append(point)

    for row in location_rows:
        state_code = row.get("state_code")
        suburb = row.get("suburb")
        postcode = row.get("postcode")
        council = row.get("council")
        state_name = row.get("state_name") or state_label_from_code(state_code)

        add_profile_location(
            ensure_profile("suburb", state_code, suburb, "suburb"),
            suburb=suburb,
            postcode=postcode,
            council=council,
        )
        add_profile_location(
            ensure_profile("council", state_code, council, "council"),
            suburb=suburb,
            postcode=postcode,
            council=council,
        )
        add_profile_location(
            ensure_profile("state", state_code, state_name, "state"),
            suburb=suburb,
            postcode=postcode,
            council=council,
        )

    for row in postcode_rows:
        state_code = row.get("state")
        suburb = row.get("locality")
        postcode = row.get("postcode")
        council = row.get("lgaregion")
        latitude = to_float(row.get("Lat_precise") or row.get("lat"))
        longitude = to_float(row.get("Long_precise") or row.get("long"))
        point = None
        if latitude is not None and longitude is not None:
            point = {"latitude": latitude, "longitude": longitude}

        add_profile_location(
            ensure_profile("suburb", state_code, suburb, "suburb"),
            suburb=suburb,
            postcode=postcode,
            council=council,
            point=point,
        )
        add_profile_location(
            ensure_profile("council", state_code, council, "lga_region"),
            suburb=suburb,
            postcode=postcode,
            council=council,
            point=point,
        )
        add_profile_location(
            ensure_profile("state", state_code, state_label_from_code(state_code), "state"),
            suburb=suburb,
            postcode=postcode,
            council=council,
            point=point,
        )

    built_profiles = []
    for profile in profiles.values():
        points = profile["points"]
        center = None
        if points:
            center = {
                "latitude": sum(point["latitude"] for point in points) / len(points),
                "longitude": sum(point["longitude"] for point in points) / len(points),
            }

        built_profiles.append(
            {
                **profile,
                "aliases": {value for value in profile["aliases"] if value},
                "suburbs": {value for value in profile["suburbs"] if value},
                "councils": {value for value in profile["councils"] if value},
                "postcodes": {value for value in profile["postcodes"] if value},
                "bounds": bounds_from_points(points),
                "center": center,
            }
        )

    return built_profiles


def item_search_text(item):
    return " ".join(
        clean_text(item.get(key))
        for key in (
            "facility_name",
            "address",
            "suburb",
            "postcode",
            "state",
            "state_full_name",
            "ewaste_category",
            "ewaste_match_text",
            "source",
            "source_file",
            "council",
            "lga_region",
            "region",
            "accepted_items",
        )
    ).lower()


def item_matches_profile(item, profile):
    if normalize_state(item.get("state")) != profile["state"]:
        return False

    if profile["tier"] == "state":
        return True

    item_suburb = normalize_lookup_key(item.get("suburb"))
    item_council = normalize_lookup_key(item.get("council"))
    item_lga = normalize_lookup_key(item.get("lga_region"))
    item_postcode = clean_text(item.get("postcode"))

    if profile["tier"] == "suburb":
        return item_suburb in profile["suburbs"] or item_postcode in profile["postcodes"]

    return (
        item_council in profile["aliases"]
        or item_lga in profile["aliases"]
        or item_suburb in profile["suburbs"]
        or item_postcode in profile["postcodes"]
    )


def profile_focus_area(profile):
    return {
        "label": profile["label"],
        "tier": profile["tier"],
        "bounds": profile["bounds"],
        "center": profile["center"],
    }


def profile_meta(query, mode, profile, message, count, fallback_chain=None):
    return {
        "query": query,
        "mode": mode,
        "label": profile["label"],
        "tier": profile["tier"],
        "match_type": profile["match_type"],
        "message": message,
        "match_count": count,
        "fallback_chain": fallback_chain or [],
        "focus_area": profile_focus_area(profile),
    }


def state_profile_for(state, profiles):
    state_code = normalize_state(state)
    for profile in profiles:
        if profile["tier"] == "state" and profile["state"] == state_code:
            return profile
    return None


def resolve_search_profile(query, profiles):
    normalized = normalize_lookup_key(query)
    if not normalized:
        return None

    state_aliases = {
        "VICTORIA": "VIC",
        "VIC": "VIC",
        "NEW SOUTH WALES": "NSW",
        "NSW": "NSW",
        "QUEENSLAND": "QLD",
        "QLD": "QLD",
        "SOUTH AUSTRALIA": "SA",
        "SA": "SA",
        "WESTERN AUSTRALIA": "WA",
        "WA": "WA",
        "TASMANIA": "TAS",
        "TAS": "TAS",
        "NORTHERN TERRITORY": "NT",
        "NT": "NT",
        "AUSTRALIAN CAPITAL TERRITORY": "ACT",
        "ACT": "ACT",
    }
    if normalized in state_aliases:
        return state_profile_for(state_aliases[normalized], profiles)

    postcode = clean_text(query)
    candidates = []
    for profile in profiles:
        match_rank = None
        if normalized in profile["aliases"]:
            match_rank = 0
        elif profile["tier"] == "suburb" and normalized in profile["suburbs"]:
            match_rank = 1
        elif postcode in profile["postcodes"]:
            match_rank = 2
        elif normalized in profile["suburbs"]:
            match_rank = 3

        if match_rank is not None:
            candidates.append((match_rank, profile))

    if candidates:
        tier_rank = {"council": 0, "suburb": 1, "state": 2}
        candidates.sort(
            key=lambda entry: (
                entry[1]["state"] != DEFAULT_SEARCH_STATE,
                entry[0],
                tier_rank.get(entry[1]["tier"], 99),
                entry[1]["label"],
            )
        )
        return candidates[0][1]

    for profile in profiles:
        if profile["state"] == DEFAULT_SEARCH_STATE and normalized in normalize_lookup_key(profile["label"]):
            return profile

    for profile in profiles:
        if normalized in normalize_lookup_key(profile["label"]):
            return profile

    return None


def nearest_profiles(base_profile, profiles, tier):
    distances = []
    for profile in profiles:
        if (
            profile["tier"] != tier
            or profile["key"] == base_profile["key"]
            or profile["state"] != base_profile["state"]
        ):
            continue

        distance = haversine_km(base_profile.get("center"), profile.get("center"))
        if distance is None:
            continue

        distances.append((distance, profile))

    distances.sort(key=lambda entry: entry[0])
    return [profile for _, profile in distances[:NEARBY_PROFILE_LIMIT]]


def build_fallback_candidates(profile, profiles):
    candidates = [("exact", profile)]

    if profile["tier"] == "suburb":
        candidates.extend(("nearby_suburb", nearby) for nearby in nearest_profiles(profile, profiles, "suburb"))
        parent_councils = [
            candidate
            for candidate in profiles
            if candidate["tier"] == "council"
            and candidate["state"] == profile["state"]
            and profile["suburbs"] & candidate["suburbs"]
        ]
        candidates.extend(("parent_council", candidate) for candidate in parent_councils)
        for parent in parent_councils[:1]:
            candidates.extend(
                ("nearby_council", nearby)
                for nearby in nearest_profiles(parent, profiles, "council")
            )

    if profile["tier"] == "council":
        candidates.extend(
            ("nearby_council", nearby)
            for nearby in nearest_profiles(profile, profiles, "council")
        )

    state_profile = state_profile_for(profile["state"], profiles)
    if state_profile:
        candidates.append(("state", state_profile))

    deduped = []
    seen = set()
    for fallback_type, candidate in candidates:
        if candidate["key"] in seen:
            continue
        seen.add(candidate["key"])
        deduped.append((fallback_type, candidate))

    return deduped


def fallback_message(query, fallback_type, source_profile, matched_profile):
    if fallback_type == "exact":
        tier_label = {
            "suburb": "suburb",
            "council": "city council",
            "state": "state",
        }.get(matched_profile["tier"], "area")
        return f"Showing disposal locations in the matched {tier_label}: {matched_profile['label']}."

    if fallback_type == "nearby_suburb":
        return (
            f"No disposal locations were found in '{query}'. "
            f"Showing nearby suburb results from {matched_profile['label']}."
        )

    if fallback_type == "parent_council":
        return (
            f"No disposal locations were found in '{query}' or its nearest suburbs. "
            f"Showing results in the wider council area: {matched_profile['label']}."
        )

    if fallback_type == "nearby_council":
        return (
            f"No disposal locations were found in {source_profile['label']}. "
            f"Showing nearby city council results from {matched_profile['label']}."
        )

    return (
        f"No disposal locations were found in {source_profile['label']} or nearby areas. "
        f"Showing state-wide results for {matched_profile['label']}."
    )


def filter_items_for_search(items, query, profiles):
    query_text = clean_text(query)
    if not query_text:
        return items, None

    profile = resolve_search_profile(query_text, profiles)
    if profile:
        attempted = []
        for fallback_type, candidate in build_fallback_candidates(profile, profiles):
            attempted.append(
                {
                    "type": fallback_type,
                    "tier": candidate["tier"],
                    "label": candidate["label"],
                }
            )
            matched_items = [item for item in items if item_matches_profile(item, candidate)]
            if matched_items:
                mode = "exact" if fallback_type == "exact" else "fallback"
                return matched_items, profile_meta(
                    query_text,
                    mode,
                    candidate,
                    fallback_message(query_text, fallback_type, profile, candidate),
                    len(matched_items),
                    attempted,
                )

    exact_items = [item for item in items if query_text.lower() in item_search_text(item)]
    if exact_items:
        return exact_items, {
            "query": query_text,
            "mode": "exact",
            "message": "",
            "match_count": len(exact_items),
        }

    return [], {
        "query": query_text,
        "mode": "none",
        "message": f"No disposal locations match '{query_text}'.",
        "match_count": 0,
    }


def csv_geocoded_row_to_item(row):
    return row_to_disposal_item(
        {
            **row,
            "source": "local_csv_geocoded",
            "ewaste_category": row.get("ewaste_match_text"),
        }
    )


def csv_curated_row_to_item(row):
    if row.get("final_keep") and not normalize_bool(row.get("final_keep")):
        return None

    return row_to_disposal_item(
        {
            "facility_name": row.get("display_name") or row.get("provider_name"),
            "address": row.get("formatted_address"),
            "suburb": row.get("suburb"),
            "postcode": row.get("postcode"),
            "state": row.get("state"),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "ewaste_category": row.get("corrected_source_type") or row.get("source_type"),
            "ewaste_match_text": row.get("corrected_accepted_items") or row.get("accepted_items"),
            "accepted_items": row.get("corrected_accepted_items") or row.get("accepted_items"),
            "note": row.get("note"),
            "national_phone_number": row.get("national_phone_number"),
            "website_uri": row.get("website_uri"),
            "google_maps_uri": row.get("google_maps_uri"),
            "business_status": row.get("business_status"),
            "data_quality_status": row.get("data_quality_status"),
            "quality_reason": row.get("quality_reason"),
            "source": "local_csv_curated",
            "source_file": CSV_SOURCE_FILES["curated_locations"],
            "coord_source": "google_places",
            "dedupe_key": row.get("place_id"),
        }
    )


def fetch_local_csv_disposal_locations():
    csv_rows = {
        name: read_csv_rows(filename)
        for name, filename in CSV_SOURCE_FILES.items()
    }

    items = []
    for row in csv_rows["geocoded_facilities"]:
        items.append(csv_geocoded_row_to_item(row))

    for row in csv_rows["curated_locations"]:
        item = csv_curated_row_to_item(row)
        if item:
            items.append(item)

    location_items = [
        item
        for item in items
        if item and item.get("latitude") is not None and item.get("longitude") is not None
    ]

    return {
        "items": location_items,
        "meta": {
            "pipeline": "local_csv",
            "source": "backend/data_for_map",
            "row_count": len(location_items),
            "csv_files": {
                CSV_SOURCE_FILES[name]: len(rows)
                for name, rows in csv_rows.items()
            },
        },
    }


def dedupe_items(items):
    deduped = []
    seen = set()

    for item in items:
        key = (
            clean_text(item.get("dedupe_key"))
            or canonical_key(item.get("facility_name"), item.get("postcode"), item.get("state"))
            or canonical_key(item.get("address"), item.get("latitude"), item.get("longitude"))
        )

        if not key or key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped


def fetch_all_disposal_locations(search_text=""):
    pipeline_jobs = {
        "cloud_database": fetch_cloud_disposal_locations,
        "local_csv": fetch_local_csv_disposal_locations,
    }

    results = {}
    errors = {}

    with ThreadPoolExecutor(max_workers=len(pipeline_jobs)) as executor:
        futures = {
            executor.submit(fetcher): name
            for name, fetcher in pipeline_jobs.items()
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                errors[name] = str(exc)

    lookup_context = load_lookup_context()

    items = dedupe_items(
        item
        for result in results.values()
        for item in result["items"]
    )
    items = [
        enrich_with_lookup(
            item,
            lookup_context["location_lookup"],
            lookup_context["postcode_lookup"],
        )
        for item in items
    ]
    items, search_meta = filter_items_for_search(
        items,
        search_text,
        lookup_context["profiles"],
    )

    if not items and errors and not results:
        raise RuntimeError("; ".join(f"{name}: {message}" for name, message in errors.items()))

    return {
        "items": items,
        "meta": {
            "pipeline": "parallel",
            "source": "+".join(results.keys()),
            "row_count": len(items),
            "pipelines": {
                name: result["meta"]
                for name, result in results.items()
            },
            "errors": errors,
            "search": search_meta,
        },
    }


@location_bp.route("/map/disposal-locations", methods=["GET"])
@login_required
def search_all_disposal_locations():
    try:
        payload = fetch_all_disposal_locations(
            search_text=request.args.get("searchText", ""),
        )
    except RuntimeError as exc:
        return jsonify({"detail": str(exc)}), 503

    return jsonify(payload)
