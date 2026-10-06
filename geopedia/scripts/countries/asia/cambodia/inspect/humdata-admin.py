"""
Inspects Cambodia's HumData administrative boundary dataset.

Reports feature counts, schemas, sample records, geometry types, missing
values, uniqueness, duplicate names, and representative values for fields
that may contain administrative names, codes, types, or parent relationships.

Input directory:
    data/raw/countries/cambodia/khm_admin_boundaries/

Run from the GeoPedia project root:
    python scripts/countries/asia/cambodia/inspect/humdata-admin.py
"""

import json
from collections import Counter
from pathlib import Path


BASE_DIR = Path(
    "data/raw/countries/cambodia/khm_admin_boundaries"
)

FILES = {
    "ADM0": BASE_DIR / "khm_admin0.geojson",
    "ADM1": BASE_DIR / "khm_admin1.geojson",
    "ADM2": BASE_DIR / "khm_admin2.geojson",
    "ADM3": BASE_DIR / "khm_admin3.geojson",
}


def is_empty(value) -> bool:
    return (
        value is None
        or (
            isinstance(value, str)
            and not value.strip()
        )
    )


def display_value(value, limit: int = 120) -> str:
    text = repr(value)

    if len(text) <= limit:
        return text

    return text[: limit - 3] + "..."


def inspect_file(level: str, path: Path) -> None:
    print()
    print("=" * 88)
    print(f"{level}: {path}")
    print("=" * 88)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    features = data.get("features", [])

    print(f"Feature count: {len(features):,}")
    print(f"GeoJSON type:  {data.get('type')}")
    print(f"CRS:           {data.get('crs')}")

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    field_counts = Counter()

    for feature in features:
        field_counts.update(
            feature.get("properties", {}).keys()
        )

    print("\nPROPERTY FIELDS:")

    for field, count in field_counts.items():
        print(
            f"  {field:<32} "
            f"{count:,}/{len(features):,}"
        )

    # ------------------------------------------------------------------
    # Sample records
    # ------------------------------------------------------------------

    print("\nFIRST 5 PROPERTY RECORDS:")

    for index, feature in enumerate(
        features[:5],
        start=1,
    ):
        print(f"\n  Feature {index}:")

        properties = feature.get("properties", {})

        for field, value in properties.items():
            print(
                f"    {field:<30} = "
                f"{display_value(value)}"
            )

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    geometry_types = Counter(
        (
            feature.get("geometry") or {}
        ).get("type")
        for feature in features
    )

    print("\nGEOMETRY TYPES:")

    for geometry_type, count in sorted(
        geometry_types.items(),
        key=lambda item: str(item[0]),
    ):
        print(
            f"  {str(geometry_type):<20} "
            f"{count:,}"
        )

    # ------------------------------------------------------------------
    # Missing values
    # ------------------------------------------------------------------

    print("\nMISSING / EMPTY VALUES:")

    found_missing = False

    for field in field_counts:
        missing = sum(
            is_empty(
                feature.get(
                    "properties",
                    {},
                ).get(field)
            )
            for feature in features
        )

        if missing:
            found_missing = True
            print(
                f"  {field:<32} "
                f"{missing:,}"
            )

    if not found_missing:
        print("  None")

    # ------------------------------------------------------------------
    # Field uniqueness
    # ------------------------------------------------------------------

    print("\nPROPERTY UNIQUENESS:")

    for field in field_counts:
        values = [
            str(
                feature.get(
                    "properties",
                    {},
                ).get(field)
            ).strip()
            for feature in features
            if not is_empty(
                feature.get(
                    "properties",
                    {},
                ).get(field)
            )
        ]

        counts = Counter(values)

        duplicate_groups = sum(
            count > 1
            for count in counts.values()
        )

        print(
            f"  {field:<32} "
            f"{len(counts):,} unique / "
            f"{len(values):,} populated / "
            f"{duplicate_groups:,} duplicate groups"
        )

    # ------------------------------------------------------------------
    # Values from likely administrative fields
    # ------------------------------------------------------------------

    interesting_fields = [
        field
        for field in field_counts
        if any(
            token in field.lower()
            for token in (
                "name",
                "code",
                "type",
                "adm",
                "parent",
                "pcode",
            )
        )
    ]

    print("\nVALUES FROM LIKELY ADMINISTRATIVE FIELDS:")

    for field in interesting_fields:
        values = [
            str(
                feature.get(
                    "properties",
                    {},
                ).get(field)
            ).strip()
            for feature in features
            if not is_empty(
                feature.get(
                    "properties",
                    {},
                ).get(field)
            )
        ]

        counts = Counter(values)

        print(f"\n  {field}:")

        for value, count in counts.most_common(15):
            print(
                f"    {count:>5} x "
                f"{display_value(value, 90)}"
            )

        if len(counts) > 15:
            print(
                f"    ... "
                f"{len(counts) - 15:,} more values"
            )

    # ------------------------------------------------------------------
    # Duplicate likely-name fields
    # ------------------------------------------------------------------

    name_fields = [
        field
        for field in field_counts
        if "name" in field.lower()
    ]

    print("\nDUPLICATE NAME VALUES:")

    found_duplicates = False

    for field in name_fields:
        values = [
            str(
                feature.get(
                    "properties",
                    {},
                ).get(field)
            ).strip()
            for feature in features
            if not is_empty(
                feature.get(
                    "properties",
                    {},
                ).get(field)
            )
        ]

        duplicates = [
            (value, count)
            for value, count in Counter(values).items()
            if count > 1
        ]

        if not duplicates:
            continue

        found_duplicates = True

        duplicates.sort(
            key=lambda item: (
                -item[1],
                item[0],
            )
        )

        print(f"\n  {field}:")

        for value, count in duplicates[:30]:
            print(
                f"    {count:>4} x "
                f"{display_value(value, 90)}"
            )

        if len(duplicates) > 30:
            print(
                f"    ... "
                f"{len(duplicates) - 30:,} more duplicate groups"
            )

    if not found_duplicates:
        print("  None")


def main() -> None:
    print(
        "Inspecting Cambodia HumData "
        "administrative boundaries..."
    )

    for level, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing input file: {path}"
            )

        inspect_file(level, path)

    print()
    print("=" * 88)
    print("CAMBODIA HUMDATA INSPECTION COMPLETE")
    print("=" * 88)


if __name__ == "__main__":
    main()