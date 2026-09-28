"""
Process Namibia's geographic telephone area-code polygons for GeoPedia.

The source GeoJSON contains seven polygons with numeric AreaCode properties.
This script validates the source geometry and converts each code to GeoPedia's
canonical zero-padded area_code property.

The source is already small enough for runtime use, so no geometry
simplification is performed.

Input:
    data/raw/countries/namibia/helloquiz_area_codes.geojson

Output:
    public/data/countries/namibia/geojson/area-codes.geojson
"""

import json
from pathlib import Path

from shapely.geometry import shape


SOURCE_PATH = Path(
    "data/raw/countries/namibia/helloquiz_area_codes.geojson"
)

OUTPUT_PATH = Path(
    "public/data/countries/namibia/geojson/area-codes.geojson"
)

EXPECTED_CODES = {
    "061",
    "062",
    "063",
    "064",
    "065",
    "066",
    "067",
}


def load_feature_collection(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def process_feature(feature: dict) -> dict:
    """Convert one source area-code feature to the canonical schema."""

    properties = feature.get("properties") or {}

    raw_code = properties.get("AreaCode")

    if not isinstance(raw_code, int):
        raise ValueError(
            f"Invalid AreaCode value: {raw_code!r}"
        )

    area_code = f"0{raw_code}"

    geometry_data = feature.get("geometry")

    if geometry_data is None:
        raise ValueError(
            f"Area code {area_code} has no geometry."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"Area code {area_code} has empty geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Area code {area_code} has invalid geometry."
        )

    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(
            f"Area code {area_code} has unsupported geometry type "
            f"{geometry.geom_type}."
        )

    return {
        "type": "Feature",
        "properties": {
            "area_code": area_code,
        },
        "geometry": geometry_data,
    }


def main() -> None:
    """Process Namibia's area-code polygons for runtime use."""

    print("Processing Namibia area codes...")
    print()

    source = load_feature_collection(SOURCE_PATH)

    processed_features = [
        process_feature(feature)
        for feature in source["features"]
    ]

    processed_features.sort(
        key=lambda feature: feature["properties"]["area_code"]
    )

    codes = [
        feature["properties"]["area_code"]
        for feature in processed_features
    ]

    if len(codes) != len(set(codes)):
        raise ValueError(
            "Duplicate area codes found in source data."
        )

    actual_codes = set(codes)

    if actual_codes != EXPECTED_CODES:
        missing = sorted(EXPECTED_CODES - actual_codes)
        unexpected = sorted(actual_codes - EXPECTED_CODES)

        raise ValueError(
            "Unexpected Namibia area-code set. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )

    output = {
        "type": "FeatureCollection",
        "features": processed_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_kb = OUTPUT_PATH.stat().st_size / 1000

    print(
        f"Area codes    {len(processed_features):>3} features | "
        f"{size_kb:.1f} KB"
    )
    print()
    print(f"Output: {OUTPUT_PATH}")
    print()
    print("Namibia area-code processing complete.")


if __name__ == "__main__":
    main()