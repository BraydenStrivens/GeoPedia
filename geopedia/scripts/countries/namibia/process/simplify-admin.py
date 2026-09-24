"""
Simplifies Namibia's canonical administrative GeoJSON for runtime use.

The intermediate datasets retain the source boundary detail. This script
applies topology-preserving simplification to reduce download size while
retaining valid Polygon/MultiPolygon geometry and all canonical properties.

Administrative levels:
- Regions
- Constituencies

Input:
    data/intermediate/countries/namibia/admin/
        regions.geojson
        constituencies.geojson

Output:
    public/data/countries/namibia/geojson/
        regions.geojson
        constituencies.geojson

Run from the GeoPedia project root:
    python scripts/countries/namibia/process/simplify-admin.py
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
    / "namibia"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "namibia"
    / "geojson"
)

DATASETS = {
    "regions": {
        "filename": "regions.geojson",
        "tolerance": 0.001,
        "expected_count": 14,
    },
    "constituencies": {
        "filename": "constituencies.geojson",
        "tolerance": 0.001,
        "expected_count": 107,
    },
}


def load_geojson(path: Path) -> dict[str, Any]:
    """Loads and validates an intermediate GeoJSON FeatureCollection."""

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
    *,
    dataset_name: str,
    feature_index: int,
) -> dict[str, Any]:
    """
    Simplifies one feature while preserving topology and validating the
    resulting geometry.
    """

    geometry_data = feature.get("geometry")

    if not isinstance(geometry_data, dict):
        raise ValueError(
            f"{dataset_name} feature {feature_index} "
            "is missing valid geometry."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"{dataset_name} feature {feature_index} "
            "has empty input geometry."
        )

    simplified = geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified.is_empty:
        raise ValueError(
            f"{dataset_name} feature {feature_index} "
            "became empty after simplification."
        )

    if not simplified.is_valid:
        raise ValueError(
            f"{dataset_name} feature {feature_index} "
            "became invalid after simplification."
        )

    if simplified.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{dataset_name} feature {feature_index} "
            "became unsupported geometry type "
            f"{simplified.geom_type!r}."
        )

    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            f"{dataset_name} feature {feature_index} "
            "is missing valid properties."
        )

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": mapping(simplified),
    }


def simplify_dataset(
    dataset_name: str,
    config: dict[str, Any],
) -> tuple[Path, int, int, int]:
    """Simplifies and writes one Namibia administrative dataset."""

    filename = config["filename"]
    tolerance = config["tolerance"]
    expected_count = config["expected_count"]

    input_path = INPUT_DIR / filename
    output_path = OUTPUT_DIR / filename

    data = load_geojson(input_path)
    features = data["features"]

    if len(features) != expected_count:
        raise ValueError(
            f"{dataset_name} contains {len(features)} features; "
            f"expected {expected_count}."
        )

    simplified_features = [
        simplify_feature(
            feature,
            tolerance,
            dataset_name=dataset_name,
            feature_index=index,
        )
        for index, feature in enumerate(features)
    ]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": simplified_features,
            },
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    input_size = input_path.stat().st_size
    output_size = output_path.stat().st_size

    return (
        output_path,
        len(simplified_features),
        input_size,
        output_size,
    )


def main() -> None:
    """Simplifies Namibia's administrative runtime datasets."""

    print("Simplifying Namibia administrative data...")
    print()

    for dataset_name, config in DATASETS.items():
        (
            output_path,
            feature_count,
            input_size,
            output_size,
        ) = simplify_dataset(
            dataset_name,
            config,
        )

        reduction = (
            (1 - output_size / input_size) * 100
            if input_size
            else 0
        )

        print(
            f"{dataset_name.title():<16} "
            f"{feature_count:>4,} features | "
            f"{input_size / 1_000_000:>6.2f} MB -> "
            f"{output_size / 1_000_000:>6.2f} MB | "
            f"{reduction:>5.1f}% smaller | "
            f"tolerance {config['tolerance']}"
        )

        print(f"  {output_path}")

    print()
    print("Namibia administrative simplification complete.")


if __name__ == "__main__":
    main()