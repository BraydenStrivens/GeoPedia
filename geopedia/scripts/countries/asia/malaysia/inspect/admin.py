"""
Inspect Malaysia's raw geoBoundaries administrative boundary datasets.

This script performs a read-only inspection of the ADM1, ADM2, and ADM3
GeoJSON files before GeoPedia processes or simplifies them.

For each administrative level it reports:
- File size
- Feature count
- Available property names
- Example feature properties
- Geometry-type counts
- Missing or duplicate boundary names
- Missing or duplicate boundary IDs
- Coordinate counts
- Coordinate-count statistics
- Parent-related properties supplied by geoBoundaries

The inspection is intended to determine:
- Which source properties should become GeoPedia's stable IDs and names
- Whether ADM2 -> ADM1 and ADM3 -> ADM2 hierarchy can be derived directly
- Whether names require normalization or disambiguation
- Appropriate geometry simplification levels

Inputs
------
data/raw/countries/malaysia/geoBoundaries-MYS-ADM1.geojson
data/raw/countries/malaysia/geoBoundaries-MYS-ADM2.geojson
data/raw/countries/malaysia/geoBoundaries-MYS-ADM3.geojson

Outputs
-------
Console inspection report only. No files are modified or generated.

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/inspect/admin-boundaries.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "malaysia"
)

FILES = {
    "ADM1": RAW_DIR / "geoBoundaries-MYS-ADM1.geojson",
    "ADM2": RAW_DIR / "geoBoundaries-MYS-ADM2.geojson",
    "ADM3": RAW_DIR / "geoBoundaries-MYS-ADM3.geojson",
}


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def count_coordinates(value: Any) -> int:
    """
    Count coordinate positions recursively within a GeoJSON coordinate array.

    A coordinate position is recognized as a numeric longitude/latitude pair.
    """

    if not isinstance(value, list):
        return 0

    if (
        len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    ):
        return 1

    return sum(
        count_coordinates(child)
        for child in value
    )


def format_number(value: float | int) -> str:
    """Format a numeric value with thousands separators."""

    if isinstance(value, float):
        return f"{value:,.1f}"

    return f"{value:,}"


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------


def inspect_file(
    level: str,
    path: Path,
) -> None:
    """Inspect and print statistics for one administrative GeoJSON file."""

    print("=" * 80)
    print(level)
    print("=" * 80)
    print()

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        print()
        return

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        geojson = json.load(file)

    features = geojson.get(
        "features",
        [],
    )

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} does not contain a valid GeoJSON feature array."
        )

    file_size = path.stat().st_size

    print(f"File: {path.relative_to(PROJECT_ROOT)}")
    print(f"File size: {file_size:,} bytes")
    print(f"Features: {len(features):,}")
    print()

    # -----------------------------------------------------------------------
    # Property schema
    # -----------------------------------------------------------------------

    property_names: set[str] = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        if isinstance(properties, dict):
            property_names.update(
                properties.keys()
            )

    print("Property names:")

    for property_name in sorted(property_names):
        print(f"  {property_name}")

    print()

    print("Example properties:")

    if features:
        example_properties = features[0].get(
            "properties",
            {},
        )

        print(
            json.dumps(
                example_properties,
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print("  None")

    print()

    # -----------------------------------------------------------------------
    # Geometry
    # -----------------------------------------------------------------------

    geometry_types = Counter(
        feature.get("geometry", {}).get("type", "MISSING")
        for feature in features
    )

    print("Geometry types:")

    for geometry_type, count in sorted(
        geometry_types.items()
    ):
        print(
            f"  {geometry_type}: {count:,}"
        )

    print()

    coordinate_counts = [
        count_coordinates(
            feature.get(
                "geometry",
                {},
            ).get(
                "coordinates",
                [],
            )
        )
        for feature in features
    ]

    total_coordinates = sum(
        coordinate_counts
    )

    print("Coordinate statistics:")
    print(
        f"  Total: {format_number(total_coordinates)}"
    )

    if coordinate_counts:
        print(
            f"  Minimum per feature: "
            f"{format_number(min(coordinate_counts))}"
        )
        print(
            f"  Maximum per feature: "
            f"{format_number(max(coordinate_counts))}"
        )
        print(
            f"  Average per feature: "
            f"{format_number(total_coordinates / len(coordinate_counts))}"
        )

    print()

    # -----------------------------------------------------------------------
    # Common geoBoundaries properties
    # -----------------------------------------------------------------------

    inspect_property(
        features,
        "shapeName",
        "Boundary names",
    )

    inspect_property(
        features,
        "shapeID",
        "Boundary IDs",
    )

    # Print potentially useful hierarchy/source fields independently so we can
    # see whether this particular geoBoundaries release contains them.
    hierarchy_properties = [
        "shapeGroup",
        "shapeType",
        "shapeISO",
        "shapeGroup",
    ]

    print("Potential hierarchy/source properties:")

    found_hierarchy_property = False

    for property_name in dict.fromkeys(
        hierarchy_properties
    ):
        if property_name not in property_names:
            continue

        found_hierarchy_property = True

        values = Counter(
            str(
                feature.get(
                    "properties",
                    {},
                ).get(
                    property_name
                )
            )
            for feature in features
        )

        print(
            f"  {property_name}: "
            f"{len(values):,} unique value(s)"
        )

        for value, count in values.most_common(10):
            print(
                f"    {value!r}: {count:,}"
            )

        if len(values) > 10:
            print(
                f"    ... {len(values) - 10:,} more"
            )

    if not found_hierarchy_property:
        print("  None found")

    print()


def inspect_property(
    features: list[dict[str, Any]],
    property_name: str,
    label: str,
) -> None:
    """
    Report missing, unique, and duplicate values for a feature property.

    Duplicate groups are printed in full because duplicate administrative names
    are important when deciding whether GeoPedia needs parent-qualified labels.
    """

    values: list[str] = []
    missing = 0

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        value = properties.get(
            property_name
        )

        if value is None or str(value).strip() == "":
            missing += 1
            continue

        values.append(
            str(value).strip()
        )

    counts = Counter(
        values
    )

    duplicates = {
        value: count
        for value, count in counts.items()
        if count > 1
    }

    print(f"{label} ({property_name}):")
    print(f"  Present: {len(values):,}")
    print(f"  Missing: {missing:,}")
    print(f"  Unique: {len(counts):,}")
    print(
        f"  Duplicate values: {len(duplicates):,}"
    )

    if duplicates:
        print("  Duplicates:")

        for value, count in sorted(
            duplicates.items()
        ):
            print(
                f"    {value!r}: {count:,}"
            )

    print()
    
def inspect_name_patterns(
    level: str,
    path: Path,
) -> None:
    """
    Inspect recurring administrative prefixes in boundary names.

    Names are not modified. This report helps determine whether prefixes such
    as MUKIM, DAERAH, BANDAR, or PEKAN carry useful administrative meaning and
    should be preserved in GeoPedia's processed data.
    """

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        geojson = json.load(file)

    names = [
        str(
            feature.get(
                "properties",
                {},
            ).get(
                "shapeName",
                "",
            )
        ).strip()
        for feature in geojson.get("features", [])
    ]

    first_words = Counter(
        name.split()[0]
        for name in names
        if name
    )

    uppercase_names = [
        name
        for name in names
        if name == name.upper()
    ]

    print("=" * 80)
    print(f"{level} NAME PATTERNS")
    print("=" * 80)
    print()

    print("Most common first words:")

    for word, count in first_words.most_common(30):
        print(f"  {word}: {count:,}")

    print()
    print(
        f"Entirely uppercase names: "
        f"{len(uppercase_names):,} / {len(names):,}"
    )

    print()
    print("First 50 names:")

    for name in sorted(
        names,
        key=str.casefold,
    )[:50]:
        print(f"  {name}")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Inspect all raw Malaysia administrative boundary datasets."""

    print()
    print("Malaysia administrative boundary inspection")
    print()

    for level, path in FILES.items():
        inspect_file(
            level,
            path,
        )
        
    print()
    print("Administrative name-pattern inspection")
    print()

    for level, path in FILES.items():
        inspect_name_patterns(
            level,
            path,
        )

    print("=" * 80)
    print("Inspection complete")
    print("=" * 80)


if __name__ == "__main__":
    main()