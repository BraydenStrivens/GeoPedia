"""
Inspect the raw Philippines administrative-boundary GeoJSON datasets.

This script performs pre-processing diagnostics on Admin 1 through Admin 4
before GeoPedia converts them into its public quiz datasets.

Raw inputs
----------
    data/raw/countries/philippines/phl_admin_boundaries/
        phl_admin1.geojson
        phl_admin2.geojson
        phl_admin3.geojson
        phl_admin4.geojson

Administrative levels
---------------------
    Admin 1: Regions
    Admin 2: Provinces / province-level units
    Admin 3: Municipalities / cities
    Admin 4: Barangays

The source dataset may place some cities at Admin 2 and others at Admin 3.
That is expected and is not considered an error by this inspector.

Why this script streams the files
---------------------------------
The source GeoJSON files are extremely large, especially Admin 3 and Admin 4.
Loading an entire file into Python merely to inspect it would consume a large
amount of memory.

`ijson` streams one GeoJSON feature at a time. Only summary statistics,
name/ID counters, parent relationships, and a limited number of diagnostic
examples are retained in memory.

Diagnostics
-----------
For each administrative level the script reports:

- Total feature count
- Unique stable pcodes
- Missing or blank pcodes
- Duplicate pcodes
- Unique names
- Missing or blank names
- Number of distinct duplicated names
- Number of records participating in duplicated names
- Maximum occurrences of one name
- Examples of duplicated names
- Duplicate names within the same immediate parent
- Missing parent IDs/names
- Number of distinct immediate parents
- Child records whose parent ID maps to conflicting parent names
- Geometry types
- Null geometries
- Empty geometries
- Invalid geometries
- Reasons and examples for invalid geometries

Duplicate names are not automatically errors. Many Philippine municipalities,
cities, and barangays legitimately share names. The diagnostics help determine
where GeoPedia question displays may eventually need parent-based
disambiguation.

Invalid geometries are reported from the raw source before any cleaning or
simplification is performed.

Dependencies
------------
    pip install ijson shapely

Run from the GeoPedia project root:

    python scripts/countries/philippines/inspect/admin.py
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ijson
from shapely.geometry import shape
from shapely.validation import explain_validity


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "philippines"
    / "phl_admin_boundaries"
)


# ---------------------------------------------------------------------------
# Inspection settings
# ---------------------------------------------------------------------------

MAX_EXAMPLES = 20


# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdminDataset:
    """Description of one raw administrative-boundary dataset."""

    level: int
    label: str
    filename: str
    name_property: str
    id_property: str
    parent_name_property: str | None
    parent_id_property: str | None


DATASETS = (
    AdminDataset(
        level=1,
        label="Admin 1 — Regions",
        filename="phl_admin1.geojson",
        name_property="adm1_name",
        id_property="adm1_pcode",
        parent_name_property=None,
        parent_id_property=None,
    ),
    AdminDataset(
        level=2,
        label="Admin 2 — Provinces / Province-Level Units",
        filename="phl_admin2.geojson",
        name_property="adm2_name",
        id_property="adm2_pcode",
        parent_name_property="adm1_name",
        parent_id_property="adm1_pcode",
    ),
    AdminDataset(
        level=3,
        label="Admin 3 — Municipalities / Cities",
        filename="phl_admin3.geojson",
        name_property="adm3_name",
        id_property="adm3_pcode",
        parent_name_property="adm2_name",
        parent_id_property="adm2_pcode",
    ),
    AdminDataset(
        level=4,
        label="Admin 4 — Barangays",
        filename="phl_admin4.geojson",
        name_property="adm4_name",
        id_property="adm4_pcode",
        parent_name_property="adm3_name",
        parent_id_property="adm3_pcode",
    ),
)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def normalize_string(
    value: Any,
) -> str | None:
    """Normalize a source property to a stripped string or None."""

    if value is None:
        return None

    text = str(
        value
    ).strip()

    return text or None


def format_number(
    value: int,
) -> str:
    """Format an integer with thousands separators."""

    return f"{value:,}"


def print_examples(
    examples: list[str],
) -> None:
    """Print an indented list of diagnostic examples."""

    if not examples:
        print("    None")
        return

    for example in examples[
        :MAX_EXAMPLES
    ]:
        print(
            f"    {example}"
        )


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------


def inspect_dataset(
    dataset: AdminDataset,
) -> None:
    """Stream and inspect one administrative GeoJSON dataset."""

    path = (
        RAW_DIRECTORY
        / dataset.filename
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Raw administrative dataset does not exist:\n{path}"
        )

    print(
        "=" * 78
    )
    print(
        dataset.label
    )
    print(
        "=" * 78
    )
    print(
        f"Source: {path.relative_to(PROJECT_ROOT)}"
    )
    print(
        f"Size:   {path.stat().st_size / (1024 * 1024):.1f} MB"
    )
    print()

    # -----------------------------------------------------------------------
    # General counters
    # -----------------------------------------------------------------------

    record_count = 0

    id_counts: Counter[str] = Counter()
    name_counts: Counter[str] = Counter()

    missing_id_count = 0
    missing_name_count = 0

    missing_id_examples: list[str] = []
    missing_name_examples: list[str] = []

    # -----------------------------------------------------------------------
    # Parent diagnostics
    # -----------------------------------------------------------------------

    parent_id_counts: Counter[str] = Counter()

    missing_parent_id_count = 0
    missing_parent_name_count = 0

    missing_parent_id_examples: list[str] = []
    missing_parent_name_examples: list[str] = []

    # parent ID -> names observed for that parent ID
    parent_names_by_id: dict[
        str,
        set[str],
    ] = defaultdict(
        set
    )

    # (parent ID, child name) -> number of occurrences.
    #
    # This tells us whether a duplicated child name also occurs more than
    # once inside the same immediate parent.
    names_within_parent: Counter[
        tuple[str, str]
    ] = Counter()

    # -----------------------------------------------------------------------
    # Geometry diagnostics
    # -----------------------------------------------------------------------

    geometry_type_counts: Counter[str] = Counter()

    null_geometry_count = 0
    empty_geometry_count = 0
    invalid_geometry_count = 0
    geometry_error_count = 0

    null_geometry_examples: list[str] = []
    empty_geometry_examples: list[str] = []
    invalid_geometry_examples: list[str] = []
    geometry_error_examples: list[str] = []

    invalid_reason_counts: Counter[str] = Counter()

    # -----------------------------------------------------------------------
    # Stream GeoJSON features
    # -----------------------------------------------------------------------

    with path.open(
        "rb"
    ) as file:
        features = ijson.items(
            file,
            "features.item",
        )

        for feature in features:
            record_count += 1

            properties = feature.get(
                "properties"
            )

            if not isinstance(
                properties,
                dict,
            ):
                properties = {}

            feature_id = normalize_string(
                properties.get(
                    dataset.id_property
                )
            )

            feature_name = normalize_string(
                properties.get(
                    dataset.name_property
                )
            )

            diagnostic_label = (
                f"record {record_count}"
            )

            if feature_id:
                diagnostic_label += (
                    f" | {feature_id}"
                )

            if feature_name:
                diagnostic_label += (
                    f" | {feature_name}"
                )

            # ----------------------------------------------------------------
            # ID
            # ----------------------------------------------------------------

            if feature_id is None:
                missing_id_count += 1

                if len(
                    missing_id_examples
                ) < MAX_EXAMPLES:
                    missing_id_examples.append(
                        diagnostic_label
                    )

            else:
                id_counts[
                    feature_id
                ] += 1

            # ----------------------------------------------------------------
            # Name
            # ----------------------------------------------------------------

            if feature_name is None:
                missing_name_count += 1

                if len(
                    missing_name_examples
                ) < MAX_EXAMPLES:
                    missing_name_examples.append(
                        diagnostic_label
                    )

            else:
                name_counts[
                    feature_name
                ] += 1

            # ----------------------------------------------------------------
            # Parent
            # ----------------------------------------------------------------

            if (
                dataset.parent_id_property is not None
                and dataset.parent_name_property is not None
            ):
                parent_id = normalize_string(
                    properties.get(
                        dataset.parent_id_property
                    )
                )

                parent_name = normalize_string(
                    properties.get(
                        dataset.parent_name_property
                    )
                )

                if parent_id is None:
                    missing_parent_id_count += 1

                    if len(
                        missing_parent_id_examples
                    ) < MAX_EXAMPLES:
                        missing_parent_id_examples.append(
                            diagnostic_label
                        )

                else:
                    parent_id_counts[
                        parent_id
                    ] += 1

                if parent_name is None:
                    missing_parent_name_count += 1

                    if len(
                        missing_parent_name_examples
                    ) < MAX_EXAMPLES:
                        missing_parent_name_examples.append(
                            diagnostic_label
                        )

                if (
                    parent_id is not None
                    and parent_name is not None
                ):
                    parent_names_by_id[
                        parent_id
                    ].add(
                        parent_name
                    )

                if (
                    parent_id is not None
                    and feature_name is not None
                ):
                    names_within_parent[
                        (
                            parent_id,
                            feature_name,
                        )
                    ] += 1

            # ----------------------------------------------------------------
            # Geometry
            # ----------------------------------------------------------------

            geometry_data = feature.get(
                "geometry"
            )

            if geometry_data is None:
                null_geometry_count += 1

                if len(
                    null_geometry_examples
                ) < MAX_EXAMPLES:
                    null_geometry_examples.append(
                        diagnostic_label
                    )

                continue

            source_geometry_type = normalize_string(
                geometry_data.get(
                    "type"
                )
                if isinstance(
                    geometry_data,
                    dict,
                )
                else None
            )

            if source_geometry_type is not None:
                geometry_type_counts[
                    source_geometry_type
                ] += 1
            else:
                geometry_type_counts[
                    "<missing>"
                ] += 1

            try:
                geometry = shape(
                    geometry_data
                )

            except Exception as error:
                geometry_error_count += 1

                if len(
                    geometry_error_examples
                ) < MAX_EXAMPLES:
                    geometry_error_examples.append(
                        f"{diagnostic_label} | "
                        f"{type(error).__name__}: {error}"
                    )

                continue

            if geometry.is_empty:
                empty_geometry_count += 1

                if len(
                    empty_geometry_examples
                ) < MAX_EXAMPLES:
                    empty_geometry_examples.append(
                        diagnostic_label
                    )

                continue

            if not geometry.is_valid:
                invalid_geometry_count += 1

                reason = explain_validity(
                    geometry
                )

                invalid_reason_counts[
                    reason.split(
                        "[",
                        1,
                    )[0]
                ] += 1

                if len(
                    invalid_geometry_examples
                ) < MAX_EXAMPLES:
                    invalid_geometry_examples.append(
                        f"{diagnostic_label} | {reason}"
                    )

    # -----------------------------------------------------------------------
    # Derived duplicate statistics
    # -----------------------------------------------------------------------

    duplicate_ids = {
        feature_id: count
        for feature_id, count in id_counts.items()
        if count > 1
    }

    duplicate_names = {
        name: count
        for name, count in name_counts.items()
        if count > 1
    }

    duplicate_id_record_count = sum(
        duplicate_ids.values()
    )

    duplicate_name_record_count = sum(
        duplicate_names.values()
    )

    maximum_name_occurrences = max(
        name_counts.values(),
        default=0,
    )

    duplicate_names_within_parent = {
        key: count
        for key, count in names_within_parent.items()
        if count > 1
    }

    duplicate_within_parent_record_count = sum(
        duplicate_names_within_parent.values()
    )

    conflicting_parent_names = {
        parent_id: names
        for parent_id, names in parent_names_by_id.items()
        if len(
            names
        ) > 1
    }

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------

    print(
        "Records"
    )
    print(
        f"  Total records:             {format_number(record_count)}"
    )
    print()

    print(
        "Stable IDs"
    )
    print(
        f"  Unique IDs:                {format_number(len(id_counts))}"
    )
    print(
        f"  Missing/blank IDs:         {format_number(missing_id_count)}"
    )
    print(
        f"  Distinct duplicate IDs:    {format_number(len(duplicate_ids))}"
    )
    print(
        f"  Records with duplicate ID: {format_number(duplicate_id_record_count)}"
    )

    if duplicate_ids:
        print(
            "  Duplicate ID examples:"
        )

        print_examples(
            [
                f"{feature_id} ({count} records)"
                for feature_id, count in sorted(
                    duplicate_ids.items(),
                    key=lambda item: (
                        -item[1],
                        item[0],
                    ),
                )
            ]
        )

    if missing_id_count:
        print(
            "  Missing ID examples:"
        )
        print_examples(
            missing_id_examples
        )

    print()

    print(
        "Names"
    )
    print(
        f"  Unique names:              {format_number(len(name_counts))}"
    )
    print(
        f"  Missing/blank names:       {format_number(missing_name_count)}"
    )
    print(
        f"  Distinct duplicated names: {format_number(len(duplicate_names))}"
    )
    print(
        f"  Records using duplicates:  {format_number(duplicate_name_record_count)}"
    )
    print(
        f"  Max occurrences of a name: {format_number(maximum_name_occurrences)}"
    )

    if duplicate_names:
        print(
            "  Most frequent duplicate names:"
        )

        print_examples(
            [
                f"{name!r} ({count} records)"
                for name, count in sorted(
                    duplicate_names.items(),
                    key=lambda item: (
                        -item[1],
                        item[0].casefold(),
                    ),
                )
            ]
        )

    if missing_name_count:
        print(
            "  Missing name examples:"
        )
        print_examples(
            missing_name_examples
        )

    print()

    if dataset.parent_id_property is not None:
        print(
            "Immediate parent relationships"
        )
        print(
            f"  Distinct parent IDs:        {format_number(len(parent_id_counts))}"
        )
        print(
            f"  Missing parent IDs:         {format_number(missing_parent_id_count)}"
        )
        print(
            f"  Missing parent names:       {format_number(missing_parent_name_count)}"
        )
        print(
            "  Duplicate names within "
            f"parent: {format_number(len(duplicate_names_within_parent))}"
        )
        print(
            "  Records in same-parent "
            f"duplicates: {format_number(duplicate_within_parent_record_count)}"
        )
        print(
            "  Parent IDs with conflicting "
            f"names: {format_number(len(conflicting_parent_names))}"
        )

        if duplicate_names_within_parent:
            print(
                "  Same-parent duplicate examples:"
            )

            examples = []

            for (
                parent_id,
                name,
            ), count in sorted(
                duplicate_names_within_parent.items(),
                key=lambda item: (
                    -item[1],
                    item[0][0],
                    item[0][1].casefold(),
                ),
            ):
                parent_names = parent_names_by_id.get(
                    parent_id,
                    set(),
                )

                parent_label = (
                    next(
                        iter(
                            parent_names
                        )
                    )
                    if len(
                        parent_names
                    ) == 1
                    else "?"
                )

                examples.append(
                    f"{name!r} ({count} records) | "
                    f"parent {parent_id} | {parent_label}"
                )

            print_examples(
                examples
            )

        if conflicting_parent_names:
            print(
                "  Conflicting parent-name examples:"
            )

            print_examples(
                [
                    f"{parent_id}: {sorted(names)!r}"
                    for parent_id, names in sorted(
                        conflicting_parent_names.items()
                    )
                ]
            )

        if missing_parent_id_count:
            print(
                "  Missing parent-ID examples:"
            )
            print_examples(
                missing_parent_id_examples
            )

        if missing_parent_name_count:
            print(
                "  Missing parent-name examples:"
            )
            print_examples(
                missing_parent_name_examples
            )

        print()

    print(
        "Geometry"
    )

    print(
        "  Geometry types:"
    )

    if geometry_type_counts:
        for geometry_type, count in sorted(
            geometry_type_counts.items()
        ):
            print(
                f"    {geometry_type}: {format_number(count)}"
            )
    else:
        print(
            "    None"
        )

    print(
        f"  Null geometries:           {format_number(null_geometry_count)}"
    )
    print(
        f"  Empty geometries:          {format_number(empty_geometry_count)}"
    )
    print(
        f"  Invalid geometries:        {format_number(invalid_geometry_count)}"
    )
    print(
        f"  Geometry parse errors:     {format_number(geometry_error_count)}"
    )

    if invalid_reason_counts:
        print(
            "  Invalidity reasons:"
        )

        for reason, count in invalid_reason_counts.most_common():
            print(
                f"    {reason}: {format_number(count)}"
            )

    if invalid_geometry_examples:
        print(
            "  Invalid geometry examples:"
        )
        print_examples(
            invalid_geometry_examples
        )

    if null_geometry_examples:
        print(
            "  Null geometry examples:"
        )
        print_examples(
            null_geometry_examples
        )

    if empty_geometry_examples:
        print(
            "  Empty geometry examples:"
        )
        print_examples(
            empty_geometry_examples
        )

    if geometry_error_examples:
        print(
            "  Geometry parse-error examples:"
        )
        print_examples(
            geometry_error_examples
        )

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Inspecting Philippines administrative boundaries..."
    )
    print(
        "Large files are streamed one feature at a time."
    )
    print()

    for dataset in DATASETS:
        inspect_dataset(
            dataset
        )

    print(
        "=" * 78
    )
    print(
        "Philippines administrative-boundary inspection complete."
    )
    print(
        "=" * 78
    )


if __name__ == "__main__":
    main()