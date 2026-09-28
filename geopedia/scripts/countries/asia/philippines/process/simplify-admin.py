"""
Simplify and publish GeoPedia's Philippines administrative GeoJSON datasets.

This script reads the full-detail intermediate administrative datasets created
by:

    scripts/countries/philippines/process/admin.py

Intermediate inputs
-------------------
    data/intermediate/countries/philippines/
        regions.geojson
        provinces.geojson
        municipalities-cities.geojson
        barangays.geojson

Public outputs
--------------
    public/data/countries/philippines/geojson/
        regions.geojson
        provinces.geojson
        municipalities-cities.geojson
        barangays.geojson

Simplification settings
-----------------------
The Philippines has unusually complex coastlines, many small islands, and a
very large number of administrative features. Its public map files are
therefore intentionally allowed to be larger than GeoPedia's typical country
datasets.

The simplification levels were selected after testing the processed source
geometry:

    Regions:                  weighted 0.4% keep-shapes
    Provinces:                weighted 0.4% keep-shapes
    Municipalities / Cities:  weighted 1%   keep-shapes
    Barangays:                weighted 3%   keep-shapes

Approximate tested output sizes were:

    Regions:                   2.15 MB
    Provinces:                 2.33 MB
    Municipalities / Cities:   8.02 MB
    Barangays:                51.27 MB

The barangay dataset is intentionally retained at approximately 51 MB for
initial testing. Its 42,048-feature map should be inspected in GeoPedia before
deciding whether stronger simplification is worthwhile.

Validation
----------
After Mapshaper finishes, this script validates that each public dataset:

- Exists.
- Is a GeoJSON FeatureCollection.
- Contains the expected number of features.
- Contains the expected GeoPedia properties on every feature.
- Contains a non-empty stable feature ID on every feature.
- Contains no duplicate stable feature IDs.
- Contains non-null geometry on every feature.

Mapshaper's `keep-shapes` option is used to reduce the risk of small polygon
features disappearing during aggressive simplification.

Requirements
------------
Mapshaper must be installed and available on PATH.

Run from the GeoPedia project root:

    python scripts/countries/philippines/process/simplify-admin.py
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

INTERMEDIATE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "philippines"
)

PUBLIC_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "philippines"
    / "geojson"
)


# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdminDataset:
    """Configuration for one Philippines administrative dataset."""

    label: str
    filename: str

    expected_count: int
    simplify_percentage: str

    id_property: str
    required_properties: tuple[str, ...]


DATASETS = (
    AdminDataset(
        label="Regions",
        filename="regions.geojson",
        expected_count=17,
        simplify_percentage="0.4%",
        id_property="region_id",
        required_properties=(
            "region_id",
            "region",
        ),
    ),
    AdminDataset(
        label="Provinces / Province-Level Units",
        filename="provinces.geojson",
        expected_count=84,
        simplify_percentage="0.4%",
        id_property="province_id",
        required_properties=(
            "region_id",
            "region",
            "province_id",
            "province",
        ),
    ),
    AdminDataset(
        label="Municipalities / Cities",
        filename="municipalities-cities.geojson",
        expected_count=1_642,
        simplify_percentage="1%",
        id_property="municipality_city_id",
        required_properties=(
            "region_id",
            "region",
            "province_id",
            "province",
            "municipality_city_id",
            "municipality_city",
        ),
    ),
    AdminDataset(
        label="Barangays",
        filename="barangays.geojson",
        expected_count=42_048,
        simplify_percentage="3%",
        id_property="barangay_id",
        required_properties=(
            "region_id",
            "region",
            "province_id",
            "province",
            "municipality_city_id",
            "municipality_city",
            "barangay_id",
            "barangay",
        ),
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def file_size_mb(
    path: Path,
) -> float:
    """Return a file size in MiB."""

    return (
        path.stat().st_size
        / (1024 * 1024)
    )


def require_non_empty_string(
    value: Any,
    *,
    dataset: AdminDataset,
    property_name: str,
    feature_number: int,
) -> str:
    """Validate and return a required non-empty string property."""

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{dataset.label}: feature {feature_number:,} has a non-string "
            f"{property_name!r} value."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{dataset.label}: feature {feature_number:,} has a blank "
            f"{property_name!r} value."
        )

    return value


# ---------------------------------------------------------------------------
# Mapshaper
# ---------------------------------------------------------------------------


def simplify_dataset(
    dataset: AdminDataset,
) -> Path:
    """Simplify one intermediate dataset and publish the result."""

    input_path = (
        INTERMEDIATE_DIRECTORY
        / dataset.filename
    )

    output_path = (
        PUBLIC_DIRECTORY
        / dataset.filename
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Intermediate dataset not found:\n{input_path}\n\n"
            "Run scripts/countries/philippines/process/admin.py first."
        )

    PUBLIC_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "npx.cmd",
        "mapshaper",
        str(
            input_path
        ),
        "-clean",
        "-simplify",
        "weighted",
        dataset.simplify_percentage,
        "keep-shapes",
        "-o",
        str(
            output_path
        ),
    ]

    print(
        f"Simplifying {dataset.label}..."
    )
    print(
        f"  Retained detail: {dataset.simplify_percentage}"
    )

    try:
        subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=True,
        )

    except FileNotFoundError as error:
        raise RuntimeError(
            "npx could not be found. Make sure Node.js/npm is installed "
            "and available on PATH."
        ) from error

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Mapshaper failed while simplifying {dataset.label}."
        ) from error

    if not output_path.exists():
        raise RuntimeError(
            f"Mapshaper completed without creating the expected output:\n"
            f"{output_path}"
        )

    return output_path


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_dataset(
    dataset: AdminDataset,
    path: Path,
) -> None:
    """Validate a simplified public GeoJSON dataset."""

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{dataset.label}: public GeoJSON root is not an object."
        )

    if data.get(
        "type"
    ) != "FeatureCollection":
        raise ValueError(
            f"{dataset.label}: expected a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{dataset.label}: GeoJSON does not contain a feature array."
        )

    if len(
        features
    ) != dataset.expected_count:
        raise ValueError(
            f"{dataset.label}: expected {dataset.expected_count:,} features "
            f"after simplification but found {len(features):,}."
        )

    seen_ids: set[str] = set()

    for feature_number, feature in enumerate(
        features,
        start=1,
    ):
        if not isinstance(
            feature,
            dict,
        ):
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} is not an "
                "object."
            )

        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} does not "
                "contain a properties object."
            )

        for property_name in dataset.required_properties:
            if property_name not in properties:
                raise ValueError(
                    f"{dataset.label}: feature {feature_number:,} is missing "
                    f"required property {property_name!r}."
                )

            require_non_empty_string(
                properties[
                    property_name
                ],
                dataset=dataset,
                property_name=property_name,
                feature_number=feature_number,
            )

        feature_id = require_non_empty_string(
            properties[
                dataset.id_property
            ],
            dataset=dataset,
            property_name=dataset.id_property,
            feature_number=feature_number,
        )

        if feature_id in seen_ids:
            raise ValueError(
                f"{dataset.label}: duplicate stable ID {feature_id!r} found "
                "after simplification."
            )

        seen_ids.add(
            feature_id
        )

        geometry = feature.get(
            "geometry"
        )

        if geometry is None:
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} ({feature_id}) "
                "has null geometry after simplification."
            )

        if not isinstance(
            geometry,
            dict,
        ):
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} ({feature_id}) "
                "has malformed geometry after simplification."
            )

        geometry_type = geometry.get(
            "type"
        )

        if geometry_type not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} ({feature_id}) "
                f"has unexpected geometry type {geometry_type!r}."
            )

        coordinates = geometry.get(
            "coordinates"
        )

        if not coordinates:
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} ({feature_id}) "
                "has empty coordinates after simplification."
            )

    if len(
        seen_ids
    ) != dataset.expected_count:
        raise ValueError(
            f"{dataset.label}: expected {dataset.expected_count:,} unique "
            f"IDs but found {len(seen_ids):,}."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Simplifying Philippines administrative datasets..."
    )
    print()

    results: list[
        tuple[
            AdminDataset,
            Path,
            float,
            float,
        ]
    ] = []

    for dataset in DATASETS:
        input_path = (
            INTERMEDIATE_DIRECTORY
            / dataset.filename
        )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Intermediate dataset not found:\n{input_path}"
            )

        before_size = file_size_mb(
            input_path
        )

        output_path = simplify_dataset(
            dataset
        )

        print(
            "  Validating..."
        )

        validate_dataset(
            dataset,
            output_path,
        )

        after_size = file_size_mb(
            output_path
        )

        reduction = (
            (
                before_size
                - after_size
            )
            / before_size
            * 100
        )

        results.append(
            (
                dataset,
                output_path,
                before_size,
                after_size,
            )
        )

        print(
            f"  Features:  {dataset.expected_count:,}"
        )
        print(
            f"  Before:    {before_size:.2f} MB"
        )
        print(
            f"  After:     {after_size:.2f} MB"
        )
        print(
            f"  Reduction: {reduction:.1f}%"
        )
        print(
            f"  Output:    {output_path.relative_to(PROJECT_ROOT)}"
        )
        print()

    print(
        "=" * 78
    )
    print(
        "Philippines administrative simplification complete."
    )
    print(
        "=" * 78
    )
    print()

    for (
        dataset,
        _,
        before_size,
        after_size,
    ) in results:
        reduction = (
            (
                before_size
                - after_size
            )
            / before_size
            * 100
        )

        print(
            f"{dataset.label}:"
        )
        print(
            f"  Features:  {dataset.expected_count:,}"
        )
        print(
            f"  Before:    {before_size:.2f} MB"
        )
        print(
            f"  After:     {after_size:.2f} MB"
        )
        print(
            f"  Reduction: {reduction:.1f}%"
        )
        print()

    print(
        "Public datasets are ready for quiz-data generation."
    )


if __name__ == "__main__":
    main()