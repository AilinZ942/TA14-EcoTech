from __future__ import annotations

import csv
import json
from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any

import shapefile


BASE_DIR = Path(__file__).resolve().parent
STANDARD_DIR = (
    BASE_DIR
    / "data_for_map"
    / "geoscape_lga_feb26_gda2020"
    / "Local Government Areas"
    / "Local Government Areas FEBRUARY 2026"
    / "Standard"
)
OUTPUT_DIR = BASE_DIR / "data_for_map" / "lga_converted"

STATE_FILES = [
    "nsw_lga.shp",
    "vic_lga.shp",
    "qld_lga.shp",
    "sa_lga.shp",
    "wa_lga.shp",
    "tas_lga.shp",
    "nt_lga.shp",
    "ot_lga.shp",
]


def json_ready(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    return value


def polygons_from_geometry(geometry: dict[str, Any]) -> list[Any]:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return list(geometry["coordinates"])
    raise ValueError(f"Unsupported geometry type: {geometry['type']}")


def ring_area_and_centroid(ring: list[list[float]] | tuple[tuple[float, float], ...]) -> tuple[float, float, float]:
    area2 = 0.0
    cx6 = 0.0
    cy6 = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        cross = x1 * y2 - x2 * y1
        area2 += cross
        cx6 += (x1 + x2) * cross
        cy6 += (y1 + y2) * cross

    if area2 == 0:
        return 0.0, 0.0, 0.0

    area = area2 / 2
    return area, cx6 / (3 * area2), cy6 / (3 * area2)


def geometry_centroid(polygons: list[Any]) -> tuple[float | None, float | None]:
    weighted_area = 0.0
    weighted_x = 0.0
    weighted_y = 0.0

    for polygon in polygons:
        for ring_index, ring in enumerate(polygon):
            area, cx, cy = ring_area_and_centroid(ring)
            if area == 0:
                continue
            # Exterior rings and holes can have different winding directions.
            # Use the first ring as positive area and holes as negative area.
            signed_area = abs(area) if ring_index == 0 else -abs(area)
            weighted_area += signed_area
            weighted_x += cx * signed_area
            weighted_y += cy * signed_area

    if weighted_area == 0:
        return None, None

    return weighted_x / weighted_area, weighted_y / weighted_area


def load_lgas() -> OrderedDict[tuple[str, str], dict[str, Any]]:
    lgas: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()

    for file_name in STATE_FILES:
        shp_path = STANDARD_DIR / file_name
        reader = shapefile.Reader(str(shp_path))

        for shape_record in reader.iterShapeRecords():
            record = {key: json_ready(value) for key, value in shape_record.record.as_dict().items()}
            polygons = polygons_from_geometry(shape_record.shape.__geo_interface__)
            key = (record["STATE"], record["LGA_PID"])

            if key not in lgas:
                lgas[key] = {
                    "lga_pid": record["LGA_PID"],
                    "lga_name": record["LGA_NAME"],
                    "abb_name": record["ABB_NAME"],
                    "state": record["STATE"],
                    "dt_create": record["DT_CREATE"],
                    "polygon_count": 0,
                    "source_polygon_ids": [],
                    "polygons": [],
                }

            lga = lgas[key]
            lga["polygon_count"] += len(polygons)
            lga["source_polygon_ids"].append(record["LG_PLY_PID"])
            lga["polygons"].extend(polygons)

    return lgas


def feature_from_lga(lga: dict[str, Any]) -> dict[str, Any]:
    polygons = lga["polygons"]
    centroid_lon, centroid_lat = geometry_centroid(polygons)
    geometry = (
        {"type": "Polygon", "coordinates": polygons[0]}
        if len(polygons) == 1
        else {"type": "MultiPolygon", "coordinates": polygons}
    )

    properties = {
        "lga_pid": lga["lga_pid"],
        "lga_name": lga["lga_name"],
        "abb_name": lga["abb_name"],
        "state": lga["state"],
        "dt_create": lga["dt_create"],
        "polygon_count": lga["polygon_count"],
        "source_polygon_ids": lga["source_polygon_ids"],
        "centroid_lon": centroid_lon,
        "centroid_lat": centroid_lat,
    }
    return {"type": "Feature", "properties": properties, "geometry": geometry}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lgas = load_lgas()
    features = [feature_from_lga(lga) for lga in lgas.values()]

    geojson_path = OUTPUT_DIR / "australia_lga_boundaries.geojson"
    with geojson_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(
            {"type": "FeatureCollection", "features": features},
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    jsonl_path = OUTPUT_DIR / "australia_lga_boundaries.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as file:
        for feature in features:
            file.write(json.dumps(feature, ensure_ascii=False, separators=(",", ":")) + "\n")

    csv_path = OUTPUT_DIR / "australia_lga_boundaries.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "lga_pid",
                "lga_name",
                "abb_name",
                "state",
                "dt_create",
                "polygon_count",
                "centroid_lon",
                "centroid_lat",
                "geometry_geojson",
            ],
        )
        writer.writeheader()
        for feature in features:
            row = dict(feature["properties"])
            row.pop("source_polygon_ids")
            row["geometry_geojson"] = json.dumps(
                feature["geometry"], ensure_ascii=False, separators=(",", ":")
            )
            writer.writerow(row)

    centroids_csv_path = OUTPUT_DIR / "australia_lga_centroids.csv"
    with centroids_csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "lga_pid",
                "lga_name",
                "abb_name",
                "state",
                "dt_create",
                "polygon_count",
                "centroid_lon",
                "centroid_lat",
            ],
        )
        writer.writeheader()
        for feature in features:
            row = dict(feature["properties"])
            row.pop("source_polygon_ids")
            writer.writerow(row)

    print(f"Converted {len(features)} LGA records")
    print(geojson_path)
    print(jsonl_path)
    print(csv_path)
    print(centroids_csv_path)


if __name__ == "__main__":
    main()
