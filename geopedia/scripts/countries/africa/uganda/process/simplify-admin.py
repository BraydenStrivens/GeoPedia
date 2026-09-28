"""
Simplifies Uganda's canonical administrative GeoJSON for runtime use.

The canonical intermediate datasets retain the source boundary detail. This
script creates smaller runtime versions while preserving topology.

Administrative levels:
- Regions
- Districts
- Counties
- Sub-counties

Input:
    data/intermediate/countries/uganda/admin/
        regions.geojson
        districts.geojson
        counties.geojson
        sub-counties.geojson

Output:
    public/data/countries/uganda/geojson/
        regions.geojson
        districts.geojson
        counties.geojson
        sub-counties.geojson

Run from the GeoPedia project root:
    python scripts/countries/uganda/process/simplify-admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "uganda"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "uganda"
    / "geojson"
)

DATASETS = {
    "regions": {
        "filename": "regions.geojson",
        "tolerance": 0.002,
        "expected_count": 4,
    },
    "districts": {
        "filename": "districts.geojson",
        "tolerance": 0.002,
        "expected_count": 135,
    },
    "counties": {
        "filename": "counties.geojson",
        "tolerance": 0.002,
        "expected_count": 203,
    },
    "sub-counties": {
        "filename": "sub-counties.geojson",
        "tolerance": 0.0015,
        "expected_count": 1520,
    },
}


def load_geojson(path: Path) -> dict[str, Any]:
    """Loads and validates a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} is missing a valid features array."
        )

    return data


def simplify_feature(
    feature: dict[str, Any],
    tolerance: float,
    dataset_name: str,
) -> dict[str, Any]:
    """Simplifies one feature while preserving its canonical properties."""

    properties = feature.get("properties")
    geometry_data = feature.get("geometry")

    if not isinstance(properties, dict):
        raise ValueError(
            f"{dataset_name} contains a feature without valid properties."
        )

    if not isinstance(geometry_data, dict):
        raise ValueError(
            f"{dataset_name} contains a feature without valid geometry."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"{dataset_name} contains an empty source geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{dataset_name} contains an invalid source geometry."
        )

    simplified = geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified.is_empty:
        raise ValueError(
            f"{dataset_name} contains a geometry that became empty "
            "after simplification."
        )

    if not simplified.is_valid:
        raise ValueError(
            f"{dataset_name} contains a geometry that became invalid "
            "after simplification."
        )

    if simplified.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{dataset_name} produced unexpected geometry type "
            f"{simplified.geom_type!r}."
        )

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": mapping(simplified),
    }


def process_dataset(
    name: str,
    filename: str,
    tolerance: float,
    expected_count: int,
) -> tuple[Path, int, int]:
    """Simplifies one canonical administrative dataset."""

    input_path = INPUT_DIR / filename
    output_path = OUTPUT_DIR / filename

    source = load_geojson(input_path)
    features = source["features"]

    if len(features) != expected_count:
        raise ValueError(
            f"Unexpected {name} feature count: "
            f"{len(features)} (expected {expected_count})."
        )

    simplified_features = [
        simplify_feature(
            feature,
            tolerance,
            name,
        )
        for feature in features
    ]

    if len(simplified_features) != expected_count:
        raise ValueError(
            f"{name} feature count changed during simplification."
        )

    output = {
        "type": "FeatureCollection",
        "features": simplified_features,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    return (
        output_path,
        input_path.stat().st_size,
        output_path.stat().st_size,
    )


def main() -> None:
    """Creates all simplified Uganda administrative runtime datasets."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Uganda administrative simplification complete.")
    print()

    for name, config in DATASETS.items():
        output_path, input_size, output_size = process_dataset(
            name,
            config["filename"],
            config["tolerance"],
            config["expected_count"],
        )

        reduction = (
            (1 - output_size / input_size) * 100
            if input_size
            else 0
        )

        print(
            f"{name.title():<14} "
            f"{config['expected_count']:>4} features | "
            f"tolerance {config['tolerance']:<7} | "
            f"{input_size / 1_000_000:>6.2f} MB -> "
            f"{output_size / 1_000_000:>6.2f} MB | "
            f"{reduction:>5.1f}% reduction"
        )

    print()
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()