"""
Inspect Indonesia administrative-boundary GeoJSON files for GeoPedia.

This script examines the four administrative levels used by GeoPedia:

    Admin 1 - Provinces
    Admin 2 - Regencies / Cities / Districts
    Admin 3 - Sub-Districts
    Admin 4 - Villages

Input directory
---------------
    data/raw/countries/indonesia/idn_admin_boundaries.geojson/

Files
-----
    idn_admin1.geojson
    idn_admin2.geojson
    idn_admin3.geojson
    idn_admin4.geojson

Purpose
-------
The raw Indonesia datasets are very large, especially Admin 4. This inspector
therefore streams features with ijson instead of loading complete GeoJSON
FeatureCollections into memory.

For each administrative level it reports:

    - feature count
    - geometry types
    - source property names
    - representative property values
    - candidate ID/name/parent fields
    - null or blank property counts
    - duplicate values for likely name fields
    - maximum duplicate-name occurrence
    - geometry validity
    - empty geometries
    - geographic bounds

The output is intended to determine the exact schema and any normalization
required before creating:

    scripts/countries/indonesia/process/admin.py

Expected source counts
----------------------
According to the source website:

    Admin 1:    34
    Admin 2:   522
    Admin 3: 7,069
    Admin 4: 81,912

The script reports count mismatches but continues inspection so the actual
contents of the downloaded files can still be examined.

Requirements
------------
    pip install ijson shapely

Run from the GeoPedia project root:

    python scripts/countries/indonesia/inspect/admin.py
"""

from __future__ import annotations
import sys

from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

import ijson
from shapely.geometry import shape


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "indonesia"
    / "idn_admin_boundaries.geojson"
)

REPORT_PATH = Path(__file__).resolve().parent / "admin-report.txt"


# ---------------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------------

DATASETS = (
    {
        "level": 1,
        "label": "Admin 1",
        "description": "Provinces",
        "path": RAW_DIRECTORY / "idn_admin1.geojson",
        "expected_count": 34,
    },
    {
        "level": 2,
        "label": "Admin 2",
        "description": "Regencies / Cities / Districts",
        "path": RAW_DIRECTORY / "idn_admin2.geojson",
        "expected_count": 522,
    },
    {
        "level": 3,
        "label": "Admin 3",
        "description": "Sub-Districts",
        "path": RAW_DIRECTORY / "idn_admin3.geojson",
        "expected_count": 7_069,
    },
    {
        "level": 4,
        "label": "Admin 4",
        "description": "Villages",
        "path": RAW_DIRECTORY / "idn_admin4.geojson",
        "expected_count": 81_912,
    },
)

SAMPLE_FEATURE_COUNT = 5
TOP_DUPLICATE_COUNT = 20


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_value(
    value: Any,
) -> str:
    """Return a compact printable representation of a property value."""

    if isinstance(
        value,
        str,
    ):
        return repr(
            value
        )

    return repr(
        value
    )


def is_blank(
    value: Any,
) -> bool:
    """Return whether a property value should be considered null or blank."""

    if value is None:
        return True

    if isinstance(
        value,
        str,
    ):
        return not value.strip()

    return False


def is_likely_name_property(
    property_name: str,
    values: list[Any],
) -> bool:
    """
    Identify properties worth examining for duplicate administrative names.

    The property name is used as a first-pass signal, while the sampled values
    prevent numeric ID/code fields from being treated as names.
    """

    lower_name = property_name.lower()

    name_signals = (
        "name",
        "nama",
    )

    if not any(
        signal in lower_name
        for signal in name_signals
    ):
        return False

    non_blank_values = [
        value
        for value in values
        if not is_blank(
            value
        )
    ]

    if not non_blank_values:
        return False

    return all(
        isinstance(
            value,
            str,
        )
        for value in non_blank_values
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def update_bounds(
    current_bounds: tuple[
        float,
        float,
        float,
        float,
    ] | None,
    geometry_bounds: tuple[
        float,
        float,
        float,
        float,
    ],
) -> tuple[
    float,
    float,
    float,
    float,
]:
    """Expand accumulated bounds with one geometry's bounds."""

    min_x, min_y, max_x, max_y = geometry_bounds

    if current_bounds is None:
        return (
            min_x,
            min_y,
            max_x,
            max_y,
        )

    return (
        min(
            current_bounds[0],
            min_x,
        ),
        min(
            current_bounds[1],
            min_y,
        ),
        max(
            current_bounds[2],
            max_x,
        ),
        max(
            current_bounds[3],
            max_y,
        ),
    )


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------


def inspect_dataset(
    dataset: dict[str, Any],
) -> None:
    """Stream and inspect one administrative GeoJSON dataset."""

    path: Path = dataset[
        "path"
    ]

    if not path.exists():
        raise FileNotFoundError(
            f"Required source file not found:\n{path}"
        )

    print(
        "=" * 80
    )
    print(
        f"{dataset['label']} - {dataset['description']}"
    )
    print(
        "=" * 80
    )
    print(
        f"File: {path.relative_to(PROJECT_ROOT)}"
    )
    print(
        f"Size: {path.stat().st_size / (1024 * 1024):,.2f} MB"
    )
    print()

    feature_count = 0

    geometry_types: Counter[str] = Counter()

    empty_geometry_count = 0
    invalid_geometry_count = 0

    bounds: tuple[
        float,
        float,
        float,
        float,
    ] | None = None

    all_property_names: set[str] = set()

    property_value_counts: dict[
        str,
        Counter[Any],
    ] = {}

    property_blank_counts: Counter[str] = Counter()

    property_samples: dict[
        str,
        list[Any],
    ] = {}

    sample_features: list[
        dict[str, Any]
    ] = []

    with path.open(
        "rb",
    ) as file:
        for feature in ijson.items(
            file,
            "features.item",
        ):
            feature_count += 1

            properties = feature.get(
                "properties"
            )

            if not isinstance(
                properties,
                dict,
            ):
                properties = {}

            if len(
                sample_features
            ) < SAMPLE_FEATURE_COUNT:
                sample_features.append(
                    dict(
                        properties
                    )
                )

            for (
                property_name,
                value,
            ) in properties.items():
                all_property_names.add(
                    property_name
                )

                if property_name not in property_value_counts:
                    property_value_counts[
                        property_name
                    ] = Counter()

                if property_name not in property_samples:
                    property_samples[
                        property_name
                    ] = []

                if is_blank(
                    value
                ):
                    property_blank_counts[
                        property_name
                    ] += 1

                else:
                    # ijson may produce Decimal for JSON numbers. Decimal is
                    # hashable, so it can safely be counted directly.
                    try:
                        property_value_counts[
                            property_name
                        ][
                            value
                        ] += 1

                    except TypeError:
                        # Complex JSON properties are uncommon in these
                        # administrative datasets. Convert any encountered
                        # structure to a stable printable representation.
                        normalized_value = repr(
                            value
                        )

                        property_value_counts[
                            property_name
                        ][
                            normalized_value
                        ] += 1

                samples = property_samples[
                    property_name
                ]

                if (
                    len(
                        samples
                    )
                    < SAMPLE_FEATURE_COUNT
                    and value not in samples
                ):
                    samples.append(
                        value
                    )

            geometry_data = feature.get(
                "geometry"
            )

            if not isinstance(
                geometry_data,
                dict,
            ):
                empty_geometry_count += 1
                continue

            geometry_type = geometry_data.get(
                "type"
            )

            if isinstance(
                geometry_type,
                str,
            ):
                geometry_types[
                    geometry_type
                ] += 1

            try:
                geometry = shape(
                    geometry_data
                )

            except Exception as error:
                invalid_geometry_count += 1

                if invalid_geometry_count <= 10:
                    print(
                        f"WARNING: feature {feature_count:,} could not be "
                        f"parsed by Shapely: {error}"
                    )

                continue

            if geometry.is_empty:
                empty_geometry_count += 1
                continue

            if not geometry.is_valid:
                invalid_geometry_count += 1

                if invalid_geometry_count <= 10:
                    print(
                        f"WARNING: feature {feature_count:,} has invalid "
                        "geometry."
                    )

            bounds = update_bounds(
                bounds,
                geometry.bounds,
            )

    print(
        "FEATURE COUNT"
    )
    print(
        f"  Actual:   {feature_count:,}"
    )
    print(
        f"  Expected: {dataset['expected_count']:,}"
    )

    if feature_count == dataset[
        "expected_count"
    ]:
        print(
            "  Status:   MATCH"
        )
    else:
        print(
            "  Status:   MISMATCH"
        )

    print()
    print(
        "GEOMETRY"
    )

    if geometry_types:
        for (
            geometry_type,
            count,
        ) in sorted(
            geometry_types.items()
        ):
            print(
                f"  {geometry_type}: {count:,}"
            )
    else:
        print(
            "  No geometry types found."
        )

    print(
        f"  Empty/unreadable: {empty_geometry_count:,}"
    )
    print(
        f"  Invalid:          {invalid_geometry_count:,}"
    )

    if bounds is not None:
        print(
            "  Bounds:           "
            f"{bounds[0]:.12f},"
            f"{bounds[1]:.12f},"
            f"{bounds[2]:.12f},"
            f"{bounds[3]:.12f}"
        )

    print()
    print(
        "PROPERTY SCHEMA"
    )

    for property_name in sorted(
        all_property_names
    ):
        counts = property_value_counts.get(
            property_name,
            Counter(),
        )

        blank_count = property_blank_counts.get(
            property_name,
            0,
        )

        samples = property_samples.get(
            property_name,
            [],
        )

        print()
        print(
            f"  {property_name}"
        )
        print(
            f"    Unique non-blank: {len(counts):,}"
        )
        print(
            f"    Null/blank:       {blank_count:,}"
        )

        if samples:
            formatted_samples = ", ".join(
                format_value(
                    value
                )
                for value in samples
            )

            print(
                f"    Samples:          {formatted_samples}"
            )

    print()
    print(
        "SAMPLE FEATURES"
    )

    for (
        index,
        properties,
    ) in enumerate(
        sample_features,
        start=1,
    ):
        print()
        print(
            f"  Feature {index}:"
        )

        for property_name in sorted(
            properties
        ):
            print(
                f"    {property_name}: "
                f"{format_value(properties[property_name])}"
            )

    print()
    print(
        "LIKELY NAME-FIELD DUPLICATES"
    )

    likely_name_properties: list[
        str
    ] = []

    for property_name in sorted(
        all_property_names
    ):
        samples = property_samples.get(
            property_name,
            [],
        )

        if is_likely_name_property(
            property_name,
            samples,
        ):
            likely_name_properties.append(
                property_name
            )

    if not likely_name_properties:
        print(
            "  No likely name properties detected automatically."
        )

    for property_name in likely_name_properties:
        counts = property_value_counts[
            property_name
        ]

        duplicate_values = [
            (
                value,
                count,
            )
            for (
                value,
                count,
            ) in counts.items()
            if count > 1
        ]

        duplicate_values.sort(
            key=lambda item: (
                -item[1],
                str(
                    item[0]
                ),
            )
        )

        duplicated_feature_count = sum(
            count
            for (
                _,
                count,
            ) in duplicate_values
        )

        max_occurrence = (
            duplicate_values[0][1]
            if duplicate_values
            else 1
        )

        print()
        print(
            f"  {property_name}"
        )
        print(
            f"    Unique names:              {len(counts):,}"
        )
        print(
            f"    Distinct duplicate names:  {len(duplicate_values):,}"
        )
        print(
            f"    Features with dup. names:  {duplicated_feature_count:,}"
        )
        print(
            f"    Maximum occurrence:        {max_occurrence:,}"
        )

        if duplicate_values:
            print(
                f"    Top {min(TOP_DUPLICATE_COUNT, len(duplicate_values))} "
                "duplicates:"
            )

            for (
                value,
                count,
            ) in duplicate_values[
                :TOP_DUPLICATE_COUNT
            ]:
                print(
                    f"      {count:>5,}  {format_value(value)}"
                )

    print()
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Inspecting Indonesia administrative boundaries..."
    )
    print()

    for dataset in DATASETS:
        inspect_dataset(
            dataset
        )

    print(
        "=" * 80
    )
    print(
        "Indonesia administrative-boundary inspection complete."
    )
    print(
        "=" * 80
    )


if __name__ == "__main__":
    original_stdout = sys.stdout

    try:
        with REPORT_PATH.open(
            "w",
            encoding="utf-8",
        ) as report_file:
            sys.stdout = report_file
            main()

    finally:
        sys.stdout = original_stdout

    print(
        f"Inspection complete. Report written to:\n"
        f"{REPORT_PATH.relative_to(PROJECT_ROOT)}"
    )