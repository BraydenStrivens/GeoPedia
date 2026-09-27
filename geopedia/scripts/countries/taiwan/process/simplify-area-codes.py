"""
Simplify Taiwan telephone area-code quiz GeoJSON files for GeoPedia.

This script takes the full-resolution Taiwan telephone-area-code geometry
produced by:

    scripts/countries/taiwan/generate/area-codes.py

and creates the optimized GeoJSON files served by the GeoPedia website.

Inputs
------
Full-resolution generated geometry:

    data/intermediate/countries/taiwan/area-codes/
        area-codes.geojson
        area-code-prefix-2.geojson
        area-code-prefix-1.geojson

Outputs
-------
Simplified public geometry:

    public/data/countries/taiwan/geojson/
        area-codes.geojson
        area-code-prefix-2.geojson
        area-code-prefix-1.geojson

Simplification
--------------
Mapshaper is used with weighted Visvalingam simplification and
`keep-shapes`.

The initial retained-coordinate percentage is 5%.

These datasets have already been dissolved from Taiwan's 368 township
polygons into much larger telephone regions, so most of the original
coordinate density is unnecessary for GeoPedia's interactive maps.

If visual inspection shows that 5% retains substantially more detail than
needed, the percentage can be reduced later. If important coastline or
region-boundary detail is lost, it can be increased.

Validation
----------
The script verifies before and after simplification that:

- The expected feature count is preserved.
- Every feature retains its stable `id`.
- `id` still equals the complete `area_codes` answer set joined by "-".
- `area_codes` remains a non-empty string array.
- `prefix_1` and `prefix_2` remain string arrays where required.
- No feature IDs are added, removed, or duplicated.
- Quiz properties are unchanged by simplification.

Expected feature counts:

    Detailed area codes:  32
    2-digit prefixes:     28
    1-digit prefixes:      7

This script changes geometry only. It must never change quiz semantics.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
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
    / "taiwan"
    / "area-codes"
)

PUBLIC_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "taiwan"
    / "geojson"
)


# ---------------------------------------------------------------------------
# Simplification settings
# ---------------------------------------------------------------------------

SIMPLIFY_PERCENTAGE = 5

MAPSHAPER_SIMPLIFY_METHOD = "weighted"


# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Dataset:
    """Definition of one generated telephone-area-code dataset."""

    filename: str
    label: str
    expected_feature_count: int
    required_array_properties: tuple[str, ...]


DATASETS = (
    Dataset(
        filename="area-codes.geojson",
        label="Detailed area codes",
        expected_feature_count=32,
        required_array_properties=(
            "area_codes",
            "prefix_1",
            "prefix_2",
        ),
    ),
    Dataset(
        filename="area-code-prefix-2.geojson",
        label="2-digit prefixes",
        expected_feature_count=28,
        required_array_properties=(
            "area_codes",
            "prefix_1",
        ),
    ),
    Dataset(
        filename="area-code-prefix-1.geojson",
        label="1-digit prefixes",
        expected_feature_count=7,
        required_array_properties=(
            "area_codes",
        ),
    ),
)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    """Load and minimally validate a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required GeoJSON does not exist:\n{path}"
        )

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
            f"{path} does not contain a JSON object."
        )

    if data.get(
        "type"
    ) != "FeatureCollection":
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
            f"{path} does not contain a features array."
        )

    return data


# ---------------------------------------------------------------------------
# Property validation
# ---------------------------------------------------------------------------


def make_feature_id(
    area_codes: list[str],
) -> str:
    """Reconstruct the expected stable ID from an answer set."""

    if not area_codes:
        raise ValueError(
            "Cannot construct an ID from an empty area_codes array."
        )

    return "-".join(
        area_codes
    )


def validate_string_array(
    value: Any,
    *,
    feature_id: str,
    property_name: str,
) -> list[str]:
    """Validate a GeoPedia string-array quiz property."""

    if not isinstance(
        value,
        list,
    ):
        raise ValueError(
            f"{feature_id!r} property {property_name!r} "
            "is not an array."
        )

    if not value:
        raise ValueError(
            f"{feature_id!r} property {property_name!r} "
            "is an empty array."
        )

    for item in value:
        if not isinstance(
            item,
            str,
        ):
            raise ValueError(
                f"{feature_id!r} property {property_name!r} "
                f"contains a non-string value: {item!r}"
            )

        if not item:
            raise ValueError(
                f"{feature_id!r} property {property_name!r} "
                "contains an empty string."
            )

    return value


def extract_quiz_properties(
    data: dict[str, Any],
    dataset: Dataset,
) -> dict[str, dict[str, Any]]:
    """
    Validate a dataset and return quiz properties indexed by feature ID.

    The returned data is later used to verify that Mapshaper changed only
    geometry and did not alter any quiz semantics.
    """

    features = data[
        "features"
    ]

    if len(
        features
    ) != dataset.expected_feature_count:
        raise ValueError(
            f"{dataset.label} expected "
            f"{dataset.expected_feature_count} features but found "
            f"{len(features)}."
        )

    properties_by_id: dict[
        str,
        dict[str, Any],
    ] = {}

    for feature in features:
        if not isinstance(
            feature,
            dict,
        ):
            raise ValueError(
                f"{dataset.label} contains a non-object feature."
            )

        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"{dataset.label} contains a feature without properties."
            )

        feature_id = properties.get(
            "id"
        )

        if not isinstance(
            feature_id,
            str,
        ) or not feature_id:
            raise ValueError(
                f"{dataset.label} contains a feature without a valid id."
            )

        if feature_id in properties_by_id:
            raise ValueError(
                f"{dataset.label} contains duplicate ID "
                f"{feature_id!r}."
            )

        area_codes = validate_string_array(
            properties.get(
                "area_codes"
            ),
            feature_id=feature_id,
            property_name="area_codes",
        )

        expected_id = make_feature_id(
            area_codes
        )

        if feature_id != expected_id:
            raise ValueError(
                f"{dataset.label} feature {feature_id!r} has "
                f"area_codes={area_codes!r}, which implies ID "
                f"{expected_id!r}."
            )

        for property_name in dataset.required_array_properties:
            validate_string_array(
                properties.get(
                    property_name
                ),
                feature_id=feature_id,
                property_name=property_name,
            )

        # Copy only the semantic quiz properties. Geometry and any
        # Mapshaper-generated metadata are intentionally excluded.
        quiz_properties = {
            property_name: properties[
                property_name
            ]
            for property_name in (
                "id",
                *dataset.required_array_properties,
            )
        }

        properties_by_id[
            feature_id
        ] = quiz_properties

    return properties_by_id


# ---------------------------------------------------------------------------
# Mapshaper
# ---------------------------------------------------------------------------


def find_mapshaper() -> str:
    """
    Find Mapshaper on PATH.

    On Windows npm commonly installs mapshaper as mapshaper.cmd, while
    other environments generally expose it as mapshaper.
    """

    candidates = (
        "mapshaper",
        "mapshaper.cmd",
    )

    for candidate in candidates:
        executable = shutil.which(
            candidate
        )

        if executable is not None:
            return executable

    raise RuntimeError(
        "Mapshaper was not found on PATH.\n"
        "Install it with:\n\n"
        "    npm install -g mapshaper"
    )


def simplify_with_mapshaper(
    mapshaper: str,
    source_path: Path,
    output_path: Path,
) -> None:
    """Simplify one GeoJSON dataset using Mapshaper."""

    command = [
        mapshaper,
        str(
            source_path
        ),
        "-clean",
        "-simplify",
        MAPSHAPER_SIMPLIFY_METHOD,
        f"{SIMPLIFY_PERCENTAGE}%",
        "keep-shapes",
        "-o",
        "format=geojson",
        str(
            output_path
        ),
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Mapshaper simplification failed.\n\n"
            f"Command:\n{' '.join(command)}\n\n"
            f"stdout:\n{result.stdout}\n\n"
            f"stderr:\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# File-size helpers
# ---------------------------------------------------------------------------


def file_size_kb(
    path: Path,
) -> float:
    """Return a file size in KiB."""

    return (
        path.stat().st_size
        / 1024
    )


def reduction_percentage(
    original_size: float,
    simplified_size: float,
) -> float:
    """Calculate the percentage reduction in file size."""

    if original_size <= 0:
        return 0.0

    return (
        1.0
        - (
            simplified_size
            / original_size
        )
    ) * 100.0


# ---------------------------------------------------------------------------
# Dataset processing
# ---------------------------------------------------------------------------


def process_dataset(
    mapshaper: str,
    dataset: Dataset,
    temporary_directory: Path,
) -> None:
    """Validate, simplify, revalidate, and publish one dataset."""

    source_path = (
        INTERMEDIATE_DIRECTORY
        / dataset.filename
    )

    public_path = (
        PUBLIC_DIRECTORY
        / dataset.filename
    )

    temporary_path = (
        temporary_directory
        / dataset.filename
    )

    print(
        f"Simplifying {dataset.label}..."
    )

    # -----------------------------------------------------------------------
    # Validate full-resolution source
    # -----------------------------------------------------------------------

    source_data = load_geojson(
        source_path
    )

    source_properties = extract_quiz_properties(
        source_data,
        dataset,
    )

    source_size = file_size_kb(
        source_path
    )

    # -----------------------------------------------------------------------
    # Simplify into a temporary file
    # -----------------------------------------------------------------------

    simplify_with_mapshaper(
        mapshaper,
        source_path,
        temporary_path,
    )

    # -----------------------------------------------------------------------
    # Validate simplified result BEFORE publishing it
    # -----------------------------------------------------------------------

    simplified_data = load_geojson(
        temporary_path
    )

    simplified_properties = extract_quiz_properties(
        simplified_data,
        dataset,
    )

    if source_properties != simplified_properties:
        source_ids = set(
            source_properties
        )

        simplified_ids = set(
            simplified_properties
        )

        missing_ids = sorted(
            source_ids
            - simplified_ids
        )

        unexpected_ids = sorted(
            simplified_ids
            - source_ids
        )

        changed_ids = sorted(
            feature_id
            for feature_id in (
                source_ids
                & simplified_ids
            )
            if source_properties[
                feature_id
            ]
            != simplified_properties[
                feature_id
            ]
        )

        raise ValueError(
            f"{dataset.label} quiz properties changed during "
            "simplification. "
            f"Missing IDs={missing_ids}, "
            f"unexpected IDs={unexpected_ids}, "
            f"changed IDs={changed_ids}"
        )

    simplified_size = file_size_kb(
        temporary_path
    )

    # -----------------------------------------------------------------------
    # Publish only after successful validation
    # -----------------------------------------------------------------------

    PUBLIC_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copyfile(
        temporary_path,
        public_path,
    )

    reduction = reduction_percentage(
        source_size,
        simplified_size,
    )

    print(
        f"  Features:  {dataset.expected_feature_count}"
    )
    print(
        f"  Before:    {source_size:.1f} KB"
    )
    print(
        f"  After:     {simplified_size:.1f} KB"
    )
    print(
        f"  Reduction: {reduction:.1f}%"
    )
    print(
        f"  Output:    {public_path.relative_to(PROJECT_ROOT)}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Locating Mapshaper..."
    )

    mapshaper = find_mapshaper()

    print(
        f"Mapshaper: {mapshaper}"
    )
    print(
        f"Simplification: weighted {SIMPLIFY_PERCENTAGE}% keep-shapes"
    )
    print()

    with tempfile.TemporaryDirectory(
        prefix="geopedia-taiwan-area-codes-"
    ) as temporary_directory_string:
        temporary_directory = Path(
            temporary_directory_string
        )

        for index, dataset in enumerate(
            DATASETS
        ):
            if index > 0:
                print()

            process_dataset(
                mapshaper,
                dataset,
                temporary_directory,
            )

    print()
    print(
        "Taiwan telephone-area-code simplification complete."
    )


if __name__ == "__main__":
    main()