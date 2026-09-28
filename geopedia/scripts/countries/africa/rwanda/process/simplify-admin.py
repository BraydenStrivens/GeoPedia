"""
Simplifies Rwanda's canonical administrative GeoJSON for runtime use.

The canonical intermediate datasets retain the full geoBoundaries geometry.
This script creates smaller runtime datasets while preserving polygon topology.

Administrative levels:
- Intara (Provinces)
- Uturere (Districts)
- Imirenge (Sectors)
- Utugali (Cells)
- Imidugudu (Villages)

The village dataset is intentionally allowed to remain comparatively large.
It contains nearly 15,000 features and exists primarily as an extreme
completionist quiz rather than a typical GeoPedia learning experience.

Input:
    data/intermediate/countries/rwanda/admin/
        provinces.geojson
        districts.geojson
        sectors.geojson
        cells.geojson
        villages.geojson

Output:
    public/data/countries/rwanda/geojson/
        provinces.geojson
        districts.geojson
        sectors.geojson
        cells.geojson
        villages.geojson

Run from the GeoPedia project root:
    python scripts/countries/rwanda/process/simplify-admin.py
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
    / "rwanda"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "rwanda"
    / "geojson"
)

DATASETS = {
    "provinces": {
        "filename": "provinces.geojson",
        "tolerance": 0.002,
        "expected_count": 5,
    },
    "districts": {
        "filename": "districts.geojson",
        "tolerance": 0.0015,
        "expected_count": 30,
    },
    "sectors": {
        "filename": "sectors.geojson",
        "tolerance": 0.001,
        "expected_count": 416,
    },
    "cells": {
        "filename": "cells.geojson",
        "tolerance": 0.00075,
        "expected_count": 2148,
    },
    "villages": {
        "filename": "villages.geojson",
        "tolerance": 0.0005,
        "expected_count": 14815,
    },
}

FALLBACK_TOLERANCES = [
    0.0004,
    0.0003,
    0.00025,
    0.0002,
    0.0001,
]


def load_geojson(path: Path) -> dict[str, Any]:
    """Loads and validates a canonical GeoJSON FeatureCollection."""

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
    """
    Simplifies one feature while preserving its canonical properties.

    If the requested tolerance produces an invalid polygon, progressively
    smaller fallback tolerances are tried for that feature alone. This allows
    unusually fragile geometries to retain more detail without reducing the
    simplification applied to the rest of the dataset.
    """

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

    tolerances = [
        tolerance,
        *[
            fallback
            for fallback in FALLBACK_TOLERANCES
            if fallback < tolerance
        ],
    ]

    for current_tolerance in tolerances:
        simplified = geometry.simplify(
            current_tolerance,
            preserve_topology=True,
        )

        if simplified.is_empty:
            continue

        if not simplified.is_valid:
            continue

        if simplified.geom_type not in {
            "Polygon",
            "MultiPolygon",
        }:
            continue

        if current_tolerance != tolerance:
            feature_id = (
                properties.get("village_id")
                or properties.get("cell_id")
                or properties.get("sector_id")
                or properties.get("district_id")
                or properties.get("province_id")
                or "unknown"
            )

            print(
                f"  Used fallback tolerance {current_tolerance} "
                f"for {dataset_name} feature {feature_id}"
            )

        return {
            "type": "Feature",
            "properties": properties,
            "geometry": mapping(simplified),
        }

    raise ValueError(
        f"{dataset_name} contains a geometry that could not be "
        "safely simplified at any configured tolerance."
    )
    

def process_dataset(
    name: str,
    filename: str,
    tolerance: float,
    expected_count: int,
) -> tuple[Path, int, int]:
    """Simplifies one Rwanda administrative dataset."""

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
    """Creates all simplified Rwanda administrative runtime datasets."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Rwanda administrative simplification complete.")
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
            f"{name.title():<12} "
            f"{config['expected_count']:>6,} features | "
            f"tolerance {config['tolerance']:<7} | "
            f"{input_size / 1_000_000:>7.2f} MB -> "
            f"{output_size / 1_000_000:>7.2f} MB | "
            f"{reduction:>5.1f}% reduction"
        )

    print()
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()