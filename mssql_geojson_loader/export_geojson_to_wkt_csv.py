import csv
import json
from pathlib import Path


BASE_DIR = Path("/Users/pcw/Documents/MONASH/TA14/TA14-EcoTech/mssql_geojson_loader")
OUTPUT_DIR = BASE_DIR / "output"

INPUT_FILES = {
    "vic_lga_gda2020": Path("/Users/pcw/Downloads/vic_lga_gda2020.geojson"),
    "vic_loc_gda2020": Path("/Users/pcw/Downloads/vic_loc_gda2020.geojson"),
}


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def position_to_wkt(position):
    return f"{position[0]} {position[1]}"


def polygon_to_wkt(coordinates):
    rings = []
    for ring in coordinates:
        points = [position_to_wkt(point) for point in ring]
        rings.append(f"({', '.join(points)})")
    return f"POLYGON ({', '.join(rings)})"


def multipolygon_to_wkt(coordinates):
    polygons = []
    for polygon in coordinates:
        rings = []
        for ring in polygon:
            points = [position_to_wkt(point) for point in ring]
            rings.append(f"({', '.join(points)})")
        polygons.append(f"({', '.join(rings)})")
    return f"MULTIPOLYGON ({', '.join(polygons)})"


def geometry_to_wkt(geometry):
    if not geometry:
        return ""

    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geom_type == "Polygon":
        return polygon_to_wkt(coordinates)
    if geom_type == "MultiPolygon":
        return multipolygon_to_wkt(coordinates)

    raise ValueError(f"Unsupported geometry type: {geom_type}")


def export_geojson(input_path, output_path, property_columns):
    with input_path.open(encoding="utf-8") as src:
        data = json.load(src)

    fieldnames = property_columns + ["geometry_wkt", "source_file"]

    with output_path.open("w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for feature in data.get("features", []):
            row = {}
            properties = feature.get("properties", {})

            for column in property_columns:
                row[column] = clean_text(properties.get(column.upper()))

            row["geometry_wkt"] = geometry_to_wkt(feature.get("geometry"))
            row["source_file"] = input_path.name
            writer.writerow(row)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    export_geojson(
        INPUT_FILES["vic_lga_gda2020"],
        OUTPUT_DIR / "vic_lga_gda2020_wkt.csv",
        ["abb_name", "dt_create", "lga_name", "lga_pid", "lg_ply_pid", "state"],
    )

    export_geojson(
        INPUT_FILES["vic_loc_gda2020"],
        OUTPUT_DIR / "vic_loc_gda2020_wkt.csv",
        ["dt_create", "lc_ply_pid", "loc_class", "loc_name", "loc_pid", "state"],
    )


if __name__ == "__main__":
    main()
