"""Location/disposal business logic backed by PostgreSQL tables."""

from __future__ import annotations

import math
import re
from collections import OrderedDict

from db.connection import get_cursor
from db.queries import location_queries as q
from models.location_model import (
    DisposalLocationItem,
    LocationLookupRow,
    LocationProfile,
    PostcodeRow,
)

DEFAULT_SEARCH_STATE = "VIC"
NEARBY_PROFILE_LIMIT = 6
SEARCH_RANGE_VALUES = {"exact", "auto", "10", "20", "50", "100", "state"}


def clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_state(value) -> str:
    return clean_text(value).upper()


def normalize_bool(value) -> bool:
    return clean_text(value).lower() in {"1", "true", "t", "yes", "y"}


def normalize_lookup_key(value) -> str:
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


def canonical_key(*parts) -> str:
    return "|".join(clean_text(part).lower() for part in parts if clean_text(part))


def to_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


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


def read_rows(sql):
    with get_cursor() as (_, cur):
        cur.execute(sql)
        return [dict(row) for row in cur.fetchall()]


def load_disposal_items() -> list[DisposalLocationItem]:
    return [DisposalLocationItem.from_row(row) for row in read_rows(q.SELECT_DISPOSAL_ITEMS)]


def load_lookup_rows() -> tuple[list[LocationLookupRow], list[PostcodeRow]]:
    with get_cursor() as (_, cur):
        cur.execute(q.SELECT_LOCATION_LOOKUP)
        location_rows = [LocationLookupRow.from_row(dict(row)) for row in cur.fetchall()]

        cur.execute(q.SELECT_POSTCODES)
        postcode_rows = [PostcodeRow.from_row(dict(row)) for row in cur.fetchall()]

    return location_rows, postcode_rows


def build_location_lookup(rows: list[LocationLookupRow]) -> dict[str, dict]:
    lookup = {}
    for row in rows:
        key = canonical_key(row.state_code, row.postcode, row.suburb)
        if key:
            lookup[key] = {
                "state_full_name": row.state_name,
                "council": row.council,
            }
    return lookup


def build_postcode_lookup(rows: list[PostcodeRow]) -> dict[str, dict]:
    lookup = {}
    for row in rows:
        key = canonical_key(row.state, row.postcode, row.locality)
        if key:
            lookup[key] = {
                "postcode_latitude": row.lat_precise or row.lat,
                "postcode_longitude": row.long_precise or row.long,
                "lga_region": row.lgaregion,
                "region": row.region,
            }
    return lookup


def build_location_profiles(
    location_rows: list[LocationLookupRow],
    postcode_rows: list[PostcodeRow],
) -> list[LocationProfile]:
    profiles: dict[str, LocationProfile] = OrderedDict()

    def ensure_profile(tier, state, label, match_type):
        state_code = normalize_state(state)
        label_text = clean_text(label)
        if not state_code or not label_text:
            return None

        key = f"{tier}|{state_code}|{normalize_lookup_key(label_text)}"
        if key not in profiles:
            profiles[key] = LocationProfile(
                key=key,
                label=label_text,
                state=state_code,
                tier=tier,
                match_type=match_type,
                aliases={normalize_lookup_key(label_text)},
            )
        return profiles[key]

    def add_profile_location(profile, suburb="", postcode="", council="", point=None):
        if not profile:
            return

        suburb_key = normalize_lookup_key(suburb)
        council_key = normalize_lookup_key(council)
        postcode_text = clean_text(postcode)

        if suburb_key:
            profile.suburbs.add(suburb_key)
        if council_key:
            profile.councils.add(council_key)
        if postcode_text:
            profile.postcodes.add(postcode_text)
        if point and point.get("latitude") is not None and point.get("longitude") is not None:
            profile.points.append(point)

    for row in location_rows:
        state_code = row.state_code
        suburb = row.suburb
        postcode = row.postcode
        council = row.council
        state_name = row.state_name or state_label_from_code(state_code)

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
        latitude = row.lat_precise or row.lat
        longitude = row.long_precise or row.long
        point = None
        if latitude is not None and longitude is not None:
            point = {"latitude": latitude, "longitude": longitude}

        add_profile_location(
            ensure_profile("suburb", row.state, row.locality, "suburb"),
            suburb=row.locality,
            postcode=row.postcode,
            council=row.lgaregion,
            point=point,
        )
        add_profile_location(
            ensure_profile("council", row.state, row.lgaregion, "lga_region"),
            suburb=row.locality,
            postcode=row.postcode,
            council=row.lgaregion,
            point=point,
        )
        add_profile_location(
            ensure_profile("state", row.state, state_label_from_code(row.state), "state"),
            suburb=row.locality,
            postcode=row.postcode,
            council=row.lgaregion,
            point=point,
        )

    built_profiles = []
    for profile in profiles.values():
        points = profile.points
        if points:
            profile.center = {
                "latitude": sum(point["latitude"] for point in points) / len(points),
                "longitude": sum(point["longitude"] for point in points) / len(points),
            }
        profile.bounds = bounds_from_points(points)
        built_profiles.append(profile)

    return built_profiles


def enrich_with_lookup(item: DisposalLocationItem, location_lookup, postcode_lookup) -> DisposalLocationItem:
    lookup_key = canonical_key(item.state, item.postcode, item.suburb)

    location_data = location_lookup.get(lookup_key, {})
    postcode_data = postcode_lookup.get(lookup_key, {})

    enriched = item.to_dict()
    enriched.update({key: value for key, value in location_data.items() if value})
    enriched.update({key: value for key, value in postcode_data.items() if value not in ("", None)})

    if enriched.get("latitude") is None:
        enriched["latitude"] = postcode_data.get("postcode_latitude")
    if enriched.get("longitude") is None:
        enriched["longitude"] = postcode_data.get("postcode_longitude")

    return DisposalLocationItem.from_row(enriched)


def dedupe_items(items: list[DisposalLocationItem]) -> list[DisposalLocationItem]:
    deduped = []
    seen = set()

    for item in items:
        key = (
            clean_text(item.dedupe_key)
            or canonical_key(item.facility_name, item.postcode, item.state)
            or canonical_key(item.address, item.latitude, item.longitude)
        )

        if not key or key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped


def item_search_text(item: DisposalLocationItem) -> str:
    return " ".join(
        clean_text(getattr(item, key))
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


def item_matches_profile(item: DisposalLocationItem, profile: LocationProfile) -> bool:
    if normalize_state(item.state) != profile.state:
        return False

    if profile.tier == "state":
        return True

    item_suburb = normalize_lookup_key(item.suburb)
    item_council = normalize_lookup_key(item.council)
    item_lga = normalize_lookup_key(item.lga_region)
    item_postcode = clean_text(item.postcode)

    if profile.tier == "suburb":
        return item_suburb in profile.suburbs or item_postcode in profile.postcodes

    return (
        item_council in profile.aliases
        or item_lga in profile.aliases
        or item_suburb in profile.suburbs
        or item_postcode in profile.postcodes
    )


def profile_focus_area(profile: LocationProfile) -> dict:
    return profile.to_focus_area()


def state_profile_for(state, profiles):
    state_code = normalize_state(state)
    for profile in profiles:
        if profile.tier == "state" and profile.state == state_code:
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
        if normalized in profile.aliases:
            match_rank = 0
        elif profile.tier == "suburb" and normalized in profile.suburbs:
            match_rank = 1
        elif postcode in profile.postcodes:
            match_rank = 2
        elif normalized in profile.suburbs:
            match_rank = 3

        if match_rank is not None:
            candidates.append((match_rank, profile))

    if candidates:
        tier_rank = {"council": 0, "suburb": 1, "state": 2}
        candidates.sort(
            key=lambda entry: (
                entry[1].state != DEFAULT_SEARCH_STATE,
                entry[0],
                tier_rank.get(entry[1].tier, 99),
                entry[1].label,
            )
        )
        return candidates[0][1]

    for profile in profiles:
        if profile.state == DEFAULT_SEARCH_STATE and normalized in normalize_lookup_key(profile.label):
            return profile

    for profile in profiles:
        if normalized in normalize_lookup_key(profile.label):
            return profile

    return None


def nearest_profiles(base_profile, profiles, tier):
    distances = []
    for profile in profiles:
        if (
            profile.tier != tier
            or profile.key == base_profile.key
            or profile.state != base_profile.state
        ):
            continue

        distance = haversine_km(base_profile.center, profile.center)
        if distance is None:
            continue

        distances.append((distance, profile))

    distances.sort(key=lambda entry: entry[0])
    return [profile for _, profile in distances[:NEARBY_PROFILE_LIMIT]]


def build_fallback_candidates(profile, profiles):
    candidates = [("exact", profile)]

    if profile.tier == "suburb":
        candidates.extend(("nearby_suburb", nearby) for nearby in nearest_profiles(profile, profiles, "suburb"))
        parent_councils = [
            candidate
            for candidate in profiles
            if candidate.tier == "council"
            and candidate.state == profile.state
            and profile.suburbs & candidate.suburbs
        ]
        candidates.extend(("parent_council", candidate) for candidate in parent_councils)
        for parent in parent_councils[:1]:
            candidates.extend(
                ("nearby_council", nearby)
                for nearby in nearest_profiles(parent, profiles, "council")
            )

    if profile.tier == "council":
        candidates.extend(
            ("nearby_council", nearby)
            for nearby in nearest_profiles(profile, profiles, "council")
        )

    state_profile = state_profile_for(profile.state, profiles)
    if state_profile:
        candidates.append(("state", state_profile))

    deduped = []
    seen = set()
    for fallback_type, candidate in candidates:
        if candidate.key in seen:
            continue
        seen.add(candidate.key)
        deduped.append((fallback_type, candidate))

    return deduped


def fallback_message(query, fallback_type, source_profile, matched_profile):
    if fallback_type == "exact":
        tier_label = {
            "suburb": "suburb",
            "council": "city council",
            "state": "state",
        }.get(matched_profile.tier, "area")
        return f"Showing disposal locations in the matched {tier_label}: {matched_profile.label}."

    if fallback_type == "nearby_suburb":
        return (
            f"No disposal locations were found in '{query}'. "
            f"Showing nearby suburb results from {matched_profile.label}."
        )

    if fallback_type == "parent_council":
        return (
            f"No disposal locations were found in '{query}' or its nearest suburbs. "
            f"Showing results in the wider council area: {matched_profile.label}."
        )

    if fallback_type == "nearby_council":
        return (
            f"No disposal locations were found in {source_profile.label}. "
            f"Showing nearby city council results from {matched_profile.label}."
        )

    return (
        f"No disposal locations were found in {source_profile.label} or nearby areas. "
        f"Showing state-wide results for {matched_profile.label}."
    )


def normalize_search_range(value):
    range_value = clean_text(value).lower() or "exact"
    return range_value if range_value in SEARCH_RANGE_VALUES else "exact"


def state_fallback(items, profile, query, message_prefix):
    fallback = [item for item in items if normalize_state(item.state) == profile.state]
    return fallback, {
        "query": query,
        "mode": "fallback",
        "label": profile.label,
        "tier": profile.tier,
        "match_type": profile.match_type,
        "message": f"{message_prefix} Showing all locations in {profile.state}.",
        "match_count": len(fallback),
        "search_range": "state",
        "focus_area": profile_focus_area(profile),
    }


def no_fallback_result(query, message):
    return [], {
        "query": query,
        "mode": "none",
        "message": message,
        "match_count": 0,
    }


def filter_items_for_search(items, search_text, search_range, profiles):
    query = clean_text(search_text)
    if not query:
        return items, None

    selected_range = normalize_search_range(search_range)
    profile = resolve_search_profile(query, profiles)

    if profile:
        matched_location = [item for item in items if item_matches_profile(item, profile)]

        if selected_range == "exact":
            if matched_location:
                return matched_location, {
                    "query": query,
                    "mode": "exact",
                    "label": profile.label,
                    "tier": profile.tier,
                    "match_type": profile.match_type,
                    "message": "",
                    "match_count": len(matched_location),
                    "search_range": selected_range,
                    "focus_area": profile_focus_area(profile),
                }

            return no_fallback_result(
                query,
                f"No exact disposal locations were found for '{query}'. Choose a wider search range to see nearby alternatives.",
            )

        if selected_range == "state":
            return state_fallback(items, profile, query, f"Showing all locations in the selected state for '{query}'.")

        if selected_range in {"10", "20", "50", "100", "auto"}:
            ranges_to_try = [10, 20, 50, 100] if selected_range == "auto" else [int(selected_range)]
            for distance_km in ranges_to_try:
                nearby = nearby_items(items, profile, distance_km)
                if nearby:
                    return nearby, {
                        "query": query,
                        "mode": "range" if matched_location else "fallback",
                        "label": profile.label,
                        "tier": profile.tier,
                        "match_type": profile.match_type,
                        "distance_km": distance_km,
                        "search_range": selected_range,
                        "message": f"Showing disposal locations within {distance_km}km of '{query}'.",
                        "match_count": len(nearby),
                        "focus_area": profile_focus_area(profile),
                    }

            max_distance_km = ranges_to_try[-1]
            return no_fallback_result(
                query,
                f"No disposal locations within {max_distance_km}km were found for '{query}'. Choose State-wide to see all locations in {profile.state}.",
            )

        if matched_location:
            return matched_location, {
                "query": query,
                "mode": "exact",
                "label": profile.label,
                "tier": profile.tier,
                "match_type": profile.match_type,
                "message": "",
                "match_count": len(matched_location),
                "search_range": selected_range,
                "focus_area": profile_focus_area(profile),
            }

        return no_fallback_result(
            query,
            f"No exact disposal locations were found for '{query}'. Choose a wider search range to see nearby alternatives.",
        )

    exact = [item for item in items if query.lower() in item_search_text(item)]
    if exact:
        return exact, {
            "query": query,
            "mode": "exact",
            "search_range": selected_range,
            "match_count": len(exact),
        }

    return no_fallback_result(query, f"No disposal locations match '{query}'.")


def nearby_items(items, profile, max_distance_km):
    if not profile.center:
        return []

    results = []
    for item in items:
        if item.latitude is None or item.longitude is None:
            continue
        distance = haversine_km(profile.center, {"latitude": item.latitude, "longitude": item.longitude})
        if distance is None or distance > max_distance_km:
            continue
        results.append((distance, item))

    results.sort(key=lambda entry: entry[0])
    return [item for _, item in results]


def enrich_items(items, location_lookup, postcode_lookup):
    return [enrich_with_lookup(item, location_lookup, postcode_lookup) for item in items]


def search_disposal_locations(search_text="", search_range="exact") -> dict:
    location_rows, postcode_rows = load_lookup_rows()
    location_lookup = build_location_lookup(location_rows)
    postcode_lookup = build_postcode_lookup(postcode_rows)
    profiles = build_location_profiles(location_rows, postcode_rows)

    items = dedupe_items(load_disposal_items())
    items = enrich_items(items, location_lookup, postcode_lookup)
    filtered_items, search_meta = filter_items_for_search(items, search_text, search_range, profiles)

    return {
        "items": [item.to_dict() for item in filtered_items],
        "meta": {
            "pipeline": "database",
            "source": "clean_ewaste_facilities_geocoded+ewaste_recycling_locations_curated",
            "row_count": len(filtered_items),
            "search": search_meta,
        },
    }
