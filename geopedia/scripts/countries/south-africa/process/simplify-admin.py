"""
Simplify South Africa's administrative boundaries for GeoPedia.

The processed administrative GeoJSON files contain very detailed source
geometry and are too large for efficient runtime use. This script simplifies
each administrative level independently while preserving GeoPedia's
canonical feature properties.

Inputs:
    data/intermediate/countries/south-africa/admin/provinces.geojson
    data/intermediate/countries/south-africa/admin/districts.geojson
    data/intermediate/countries/south-africa/admin/municipalities.geojson
    data/intermediate/countries/south-africa/admin/wards.geojson

Outputs:
    public/data/countries/south-africa/geojson/provinces.geojson
    public/data/countries/south-africa/geojson/districts.geojson
    public/data/countries/south-africa/geojson/municipalities.geojson
    public/data/countries/south-africa/geojson/wards.geojson

Each administrative level has its own simplification tolerance so the
geometry/detail tradeoff can be tuned independently.

The simplifier validates that:
    - every expected feature is retained
    - canonical feature IDs are unchanged
    - feature properties are unchanged
    - geometries remain non-empty and valid
    - geometries remain Polygon or MultiPolygon

Run:
    python scripts/countries/south-africa/process/simplify-admin.py
"""

import json
from pathlib import Path

from shapely.geometry import mapping, shape


INPUT_ROOT = Path(
    "data/intermediate/countries/south-africa/admin"
)

OUTPUT_ROOT = Path(
    "public/data/countries/south-africa/geojson"
)


# Tune these independently after inspecting the generated maps.
PROVINCE_TOLERANCE = 0.01
DISTRICT_TOLERANCE = 0.0075
MUNICIPALITY_TOLERANCE = 0.005
WARD_TOLERANCE = 0.0025


LEVELS = [
    {
        "label": "Provinces",
        "filename": "provinces.geojson",
        "id_property": "province_id",
        "expected_count": 9,
        "tolerance": PROVINCE_TOLERANCE,
    },
    {
        "label": "Districts",
        "filename": "districts.geojson",
        "id_property": "district_id",
        "expected_count": 52,
        "tolerance": DISTRICT_TOLERANCE,
    },
    {
        "label": "Municipalities",
        "filename": "municipalities.geojson",
        "id_property": "municipality_id",
        "expected_count": 213,
        "tolerance": MUNICIPALITY_TOLERANCE,
    },
    {
        "label": "Wards",
        "filename": "wards.geojson",
        "id_property": "ward_id",
        "expected_count": 4392,
        "tolerance": WARD_TOLERANCE,
    },
]


def load_feature_collection(path: Path) -> dict:
    """Load and validate an intermediate GeoJSON FeatureCollection."""

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


def validate_geometry(
    geometry,
    context: str,
) -> None:
    """Validate a simplified polygonal geometry."""

    if geometry.is_empty:
        raise ValueError(
            f"{context}: geometry is empty."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{context}: geometry is invalid."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{context}: simplification produced unsupported "
            f"geometry type {geometry.geom_type!r}."
        )


def simplify_features(
    features: list[dict],
    id_property: str,
    tolerance: float,
    expected_count: int,
    label: str,
) -> list[dict]:
    """Simplify one administrative level and validate the result."""

    if len(features) != expected_count:
        raise ValueError(
            f"{label}: expected {expected_count} features, "
            f"found {len(features)}."
        )

    simplified_features = []
    source_ids = set()
    output_ids = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"{label} feature {index}: invalid properties."
            )

        feature_id = properties.get(id_property)

        if not isinstance(feature_id, str) or not feature_id:
            raise ValueError(
                f"{label} feature {index}: invalid "
                f"{id_property}: {feature_id!r}"
            )

        if feature_id in source_ids:
            raise ValueError(
                f"{label}: duplicate source ID {feature_id!r}."
            )

        source_ids.add(feature_id)

        geometry_data = feature.get("geometry")

        if geometry_data is None:
            raise ValueError(
                f"{label} {feature_id}: missing geometry."
            )

        source_geometry = shape(geometry_data)

        validate_geometry(
            source_geometry,
            f"{label} {feature_id} source",
        )

        simplified_geometry = source_geometry.simplify(
            tolerance,
            preserve_topology=True,
        )

        validate_geometry(
            simplified_geometry,
            f"{label} {feature_id} simplified",
        )

        if feature_id in output_ids:
            raise ValueError(
                f"{label}: duplicate output ID {feature_id!r}."
            )

        output_ids.add(feature_id)

        simplified_features.append(
            {
                "type": "Feature",
                "properties": properties.copy(),
                "geometry": mapping(simplified_geometry),
            }
        )

    if source_ids != output_ids:
        missing = sorted(source_ids - output_ids)
        extra = sorted(output_ids - source_ids)

        raise ValueError(
            f"{label}: feature IDs changed during simplification. "
            f"Missing: {missing}; extra: {extra}"
        )

    return simplified_features


def write_geojson(
    path: Path,
    features: list[dict],
) -> None:
    """Write a simplified runtime GeoJSON FeatureCollection."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def format_size(size_bytes: int) -> str:
    """Format a file size in megabytes."""

    return f"{size_bytes / 1_000_000:.2f} MB"


def simplify_level(config: dict) -> None:
    """Simplify and write one administrative level."""

    label = config["label"]
    filename = config["filename"]
    id_property = config["id_property"]
    expected_count = config["expected_count"]
    tolerance = config["tolerance"]

    input_path = INPUT_ROOT / filename
    output_path = OUTPUT_ROOT / filename

    data = load_feature_collection(input_path)

    simplified_features = simplify_features(
        data["features"],
        id_property,
        tolerance,
        expected_count,
        label,
    )

    write_geojson(
        output_path,
        simplified_features,
    )

    input_size = input_path.stat().st_size
    output_size = output_path.stat().st_size

    reduction = (
        (1 - output_size / input_size) * 100
        if input_size
        else 0
    )

    print(
        f"{label:<16} "
        f"{len(simplified_features):>5} features | "
        f"tolerance {tolerance:<7g} | "
        f"{format_size(input_size):>9} -> "
        f"{format_size(output_size):>9} | "
        f"{reduction:>5.1f}% smaller"
    )


def main() -> None:
    """Simplify all South African administrative boundary levels."""

    print("Simplifying South Africa administrative boundaries...")
    print()

    for config in LEVELS:
        simplify_level(config)

    print()
    print(f"Output: {OUTPUT_ROOT}")
    print()
    print("South Africa administrative simplification complete.")


if __name__ == "__main__":
    main()