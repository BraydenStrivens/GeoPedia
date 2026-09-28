"""
Simplify processed Lesotho administrative boundaries for GeoPedia.

Inputs:

    data/intermediate/countries/lesotho/admin/
        districts.geojson
        constituencies.geojson

Outputs:

    public/data/countries/lesotho/geojson/
        districts.geojson
        constituencies.geojson

Mapshaper is used with Douglas-Peucker interval simplification while
preserving polygon topology and feature properties.

Simplification tolerances:

    Districts:       0.0025 degrees
    Constituencies:  0.0015 degrees

Run from the GeoPedia project root:

    python scripts/countries/lesotho/process/simplify-admin.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


INPUT_DIR = Path(
    "data/intermediate/countries/lesotho/admin"
)

OUTPUT_DIR = Path(
    "public/data/countries/lesotho/geojson"
)

DATASETS = (
    {
        "name": "Districts",
        "input": INPUT_DIR / "districts.geojson",
        "output": OUTPUT_DIR / "districts.geojson",
        "id_property": "district_id",
        "tolerance": 0.0025,
    },
    {
        "name": "Constituencies",
        "input": INPUT_DIR / "constituencies.geojson",
        "output": OUTPUT_DIR / "constituencies.geojson",
        "id_property": "constituency_id",
        "tolerance": 0.0015,
    },
)


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if (
        data.get("type")
        != "FeatureCollection"
    ):
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def validate_dataset(
    path: Path,
    id_property: str,
) -> tuple[
    int,
    set[str],
]:
    """
    Validate polygon geometry and unique feature IDs.

    Returns the feature count and complete set of IDs so the simplified
    output can be checked against the source.
    """
    data = load_geojson(
        path
    )

    ids: set[str] = set()

    for index, feature in enumerate(
        data["features"]
    ):
        properties = feature.get(
            "properties",
            {},
        )

        feature_id = properties.get(
            id_property
        )

        if not isinstance(
            feature_id,
            str,
        ):
            raise ValueError(
                f"{path}: feature {index} is missing "
                f"{id_property}."
            )

        if feature_id in ids:
            raise ValueError(
                f"{path}: duplicate {id_property} "
                f"{feature_id}."
            )

        geometry = feature.get(
            "geometry"
        )

        if not isinstance(
            geometry,
            dict,
        ):
            raise ValueError(
                f"{path}: feature {feature_id} "
                "has no geometry."
            )

        geometry_type = geometry.get(
            "type"
        )

        if geometry_type not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError(
                f"{path}: feature {feature_id} has "
                f"unexpected geometry type {geometry_type}."
            )

        ids.add(
            feature_id
        )

    return (
        len(data["features"]),
        ids,
    )


def file_size_mb(
    path: Path,
) -> float:
    """Return a file's size in megabytes."""
    return (
        path.stat().st_size
        / 1024
        / 1024
    )


def run_mapshaper(
    input_path: Path,
    output_path: Path,
    tolerance: float,
) -> None:
    """Simplify one GeoJSON dataset with Mapshaper."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "npx",
        "mapshaper",
        str(input_path),
        "-simplify",
        "dp",
        f"interval={tolerance}",
        "keep-shapes",
        "-o",
        "format=geojson",
        "precision=0.000001",
        "force",
        str(output_path),
    ]

    subprocess.run(
        command,
        check=True,
        shell=True,
    )


def process_dataset(
    dataset: dict[str, Any],
) -> None:
    """Validate, simplify, and verify one administrative dataset."""
    name = dataset[
        "name"
    ]

    input_path = dataset[
        "input"
    ]

    output_path = dataset[
        "output"
    ]

    id_property = dataset[
        "id_property"
    ]

    tolerance = dataset[
        "tolerance"
    ]

    print(
        f"Processing {name}..."
    )

    (
        input_count,
        input_ids,
    ) = validate_dataset(
        input_path,
        id_property,
    )

    input_size = file_size_mb(
        input_path
    )

    print(
        f"  Input features: "
        f"{input_count:,}"
    )

    print(
        f"  Input size:     "
        f"{input_size:.2f} MB"
    )

    print(
        f"  Tolerance:      "
        f"{tolerance}"
    )

    run_mapshaper(
        input_path,
        output_path,
        tolerance,
    )

    (
        output_count,
        output_ids,
    ) = validate_dataset(
        output_path,
        id_property,
    )

    if (
        output_count
        != input_count
    ):
        raise ValueError(
            f"{name}: feature count changed from "
            f"{input_count:,} to {output_count:,}."
        )

    if (
        output_ids
        != input_ids
    ):
        missing = (
            input_ids
            - output_ids
        )

        added = (
            output_ids
            - input_ids
        )

        raise ValueError(
            f"{name}: feature IDs changed during simplification. "
            f"Missing={sorted(missing)}, "
            f"Added={sorted(added)}"
        )

    output_size = file_size_mb(
        output_path
    )

    reduction = (
        (
            input_size
            - output_size
        )
        / input_size
        * 100.0
        if input_size
        else 0.0
    )

    print(
        f"  Output features:"
        f" {output_count:,}"
    )

    print(
        f"  Output size:    "
        f" {output_size:.2f} MB"
    )

    print(
        f"  Reduction:      "
        f" {reduction:.1f}%"
    )

    print(
        f"  Wrote "
        f"{output_path}"
    )

    print()


def main() -> None:
    """Simplify all Lesotho administrative datasets."""
    print(
        "Simplifying Lesotho administrative boundaries..."
    )

    print()

    for dataset in DATASETS:
        process_dataset(
            dataset
        )

    print(
        "Done."
    )


if __name__ == "__main__":
    main()