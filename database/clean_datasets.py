import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


BASE_DIR = Path("/Users/pcw/Documents/MONASH/TA14/TA14-EcoTech/database")
INPUTS = {
    "ewaste": Path("/Users/pcw/Downloads/clean_ewaste_facilities_geocoded.csv"),
    "lga": Path("/Users/pcw/Downloads/vic_lga_gda2020.geojson"),
    "locality": Path("/Users/pcw/Downloads/vic_loc_gda2020.geojson"),
}


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def clean_decimal(value):
    value = clean_text(value)
    if not value:
        return ""
    try:
        return format(Decimal(value), "f")
    except InvalidOperation:
        return ""


def clean_int(value):
    value = clean_text(value)
    if not value:
        return ""
    try:
        return str(int(value))
    except ValueError:
        return ""


def clean_bool(value):
    value = clean_text(value).lower()
    if value in {"true", "1", "yes", "y"}:
        return "1"
    if value in {"false", "0", "no", "n"}:
        return "0"
    return ""


def geojson_position_to_wkt(position):
    return f"{position[0]} {position[1]}"


def polygon_to_wkt(coordinates):
    rings = []
    for ring in coordinates:
        points = [geojson_position_to_wkt(point) for point in ring]
        rings.append(f"({', '.join(points)})")
    return f"POLYGON ({', '.join(rings)})"


def geometry_to_wkt(geometry):
    if not geometry:
        return ""
    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geom_type == "Polygon":
        return polygon_to_wkt(coordinates)
    return json.dumps(geometry, ensure_ascii=False)


def export_ewaste_csv():
    output_path = BASE_DIR / "clean_ewaste_facilities_geocoded_clean.csv"
    columns = [
        "facility_name",
        "address",
        "suburb",
        "postcode",
        "state",
        "latitude",
        "longitude",
        "coord_source",
        "duplicate_count",
        "source_file",
        "source_provenance",
        "ewaste_match_flag",
        "ewaste_match_text",
        "ewaste_match_column",
        "review_flag",
        "dedupe_key",
        "original_latitude",
        "original_longitude",
        "original_coord_source",
        "maptiler_query",
        "maptiler_place_name",
        "maptiler_match_score",
        "maptiler_feature_id",
    ]

    with INPUTS["ewaste"].open(newline="", encoding="utf-8-sig") as src, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=columns)
        writer.writeheader()

        for row in reader:
            cleaned = {
                "facility_name": clean_text(row.get("facility_name")),
                "address": clean_text(row.get("address")),
                "suburb": clean_text(row.get("suburb")),
                "postcode": clean_text(row.get("postcode")),
                "state": clean_text(row.get("state")).upper(),
                "latitude": clean_decimal(row.get("latitude")),
                "longitude": clean_decimal(row.get("longitude")),
                "coord_source": clean_text(row.get("coord_source")).lower(),
                "duplicate_count": clean_int(row.get("duplicate_count")),
                "source_file": clean_text(row.get("source_file")),
                "source_provenance": clean_text(row.get("source_provenance")),
                "ewaste_match_flag": clean_bool(row.get("ewaste_match_flag")),
                "ewaste_match_text": clean_text(row.get("ewaste_match_text")),
                "ewaste_match_column": clean_text(row.get("ewaste_match_column")).lower(),
                "review_flag": clean_text(row.get("review_flag")),
                "dedupe_key": clean_text(row.get("dedupe_key")).lower(),
                "original_latitude": clean_decimal(row.get("original_latitude")),
                "original_longitude": clean_decimal(row.get("original_longitude")),
                "original_coord_source": clean_text(row.get("original_coord_source")).lower(),
                "maptiler_query": clean_text(row.get("maptiler_query")),
                "maptiler_place_name": clean_text(row.get("maptiler_place_name")),
                "maptiler_match_score": clean_decimal(row.get("maptiler_match_score")),
                "maptiler_feature_id": clean_text(row.get("maptiler_feature_id")),
            }
            writer.writerow(cleaned)


def export_geojson_csv(input_key, output_name, property_mapping):
    output_path = BASE_DIR / output_name
    columns = list(property_mapping.values()) + ["geometry_wkt"]

    with INPUTS[input_key].open(encoding="utf-8") as src:
        data = json.load(src)

    with output_path.open("w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=columns)
        writer.writeheader()

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            row = {}
            for source_key, target_key in property_mapping.items():
                value = props.get(source_key)
                if target_key == "dt_create":
                    row[target_key] = clean_text(value)
                else:
                    row[target_key] = clean_text(value)
            row["geometry_wkt"] = geometry_to_wkt(feature.get("geometry"))
            writer.writerow(row)


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    export_ewaste_csv()
    export_geojson_csv(
        "lga",
        "vic_lga_gda2020_clean.csv",
        {
            "ABB_NAME": "abb_name",
            "DT_CREATE": "dt_create",
            "LGA_NAME": "lga_name",
            "LGA_PID": "lga_pid",
            "LG_PLY_PID": "lg_ply_pid",
            "STATE": "state",
        },
    )
    export_geojson_csv(
        "locality",
        "vic_loc_gda2020_clean.csv",
        {
            "DT_CREATE": "dt_create",
            "LC_PLY_PID": "lc_ply_pid",
            "LOC_CLASS": "loc_class",
            "LOC_NAME": "loc_name",
            "LOC_PID": "loc_pid",
            "STATE": "state",
        },
    )


if __name__ == "__main__":
    main()
