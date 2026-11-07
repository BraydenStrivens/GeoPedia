"""
Inspect Thailand's raw administrative GeoJSON datasets.

Examines ADM1, ADM2, and ADM3 to determine:
- feature counts
- available properties
- administrative IDs and parent IDs
- English and Thai/native name fields
- missing property values
- duplicate IDs and names
- geometry types
- dataset metadata
- representative feature properties

Geometry coordinates are not analyzed, keeping the inspection practical for
Thailand's very large raw administrative files.

Inputs:
    data/raw/countries/thailand/tha_admin_boundaries.geojson/
        tha_admin1.geojson
        tha_admin2.geojson
        tha_admin3.geojson

Usage:
    python scripts/countries/asia/thailand/inspect/admin.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = (
    PROJECT_ROOT
    / "data/raw/countries/thailand/tha_admin_boundaries.geojson"
)

FILES = {
    "ADM1": RAW_DIR / "tha_admin1.geojson",
    "ADM2": RAW_DIR / "tha_admin2.geojson",
    "ADM3": RAW_DIR / "tha_admin3.geojson",
}


# Fields commonly used by OCHA/HumData administrative boundary datasets.
NAME_FIELD_CANDIDATES = (
    "adm1_en",
    "adm2_en",
    "adm3_en",
    "adm1_name",
    "adm2_name",
    "adm3_name",
    "name",
    "name_en",
    "name_th",
    "name_tha",
    "name_local",
    "name_native",
)

ID_FIELD_CANDIDATES = (
    "adm1_pcode",
    "adm2_pcode",
    "adm3_pcode",
    "pcode",
    "id",
)


def load_geojson(path: Path) -> dict[str, Any]:
    print(f"Loading {path.name}...")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_missing(value: Any) -> bool:
    return (
        value is None
        or value == ""
        or (
            isinstance(value, str)
            and value.strip() == ""
        )
    )


def print_heading(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def inspect_top_level(data: dict[str, Any]) -> None:
    print("\nTop-level keys:")
    for key in data:
        if key == "features":
            continue

        value = data[key]

        if isinstance(value, (dict, list)):
            preview = json.dumps(
                value,
                ensure_ascii=False,
            )

            if len(preview) > 500:
                preview = preview[:500] + "..."

            print(f"  {key}: {preview}")
        else:
            print(f"  {key}: {value!r}")


def get_all_property_names(
    features: list[dict[str, Any]],
) -> list[str]:
    names: set[str] = set()

    for feature in features:
        properties = feature.get("properties") or {}
        names.update(properties.keys())

    return sorted(names)


def inspect_properties(
    features: list[dict[str, Any]],
    property_names: list[str],
) -> None:
    print("\nProperties:")

    for property_name in property_names:
        values = [
            (feature.get("properties") or {}).get(property_name)
            for feature in features
        ]

        present_values = [
            value
            for value in values
            if not is_missing(value)
        ]

        unique_values = {
            str(value)
            for value in present_values
        }

        missing_count = len(values) - len(present_values)

        print(
            f"  {property_name:<24} "
            f"present={len(present_values):>6,}  "
            f"missing={missing_count:>6,}  "
            f"unique={len(unique_values):>6,}"
        )


def inspect_name_fields(
    features: list[dict[str, Any]],
    property_names: list[str],
) -> None:
    print("\nPotential name / language fields:")

    candidates = [
        name
        for name in property_names
        if (
            "name" in name.lower()
            or "lang" in name.lower()
            or name.lower() in NAME_FIELD_CANDIDATES
        )
    ]

    if not candidates:
        print("  NONE FOUND")
        return

    for field in candidates:
        values = [
            (feature.get("properties") or {}).get(field)
            for feature in features
        ]

        present = [
            value
            for value in values
            if not is_missing(value)
        ]

        unique = {
            str(value)
            for value in present
        }

        missing = len(values) - len(present)

        print()
        print(f"  {field}")
        print(f"    present: {len(present):,}")
        print(f"    missing: {missing:,}")
        print(f"    unique:  {len(unique):,}")

        print("    samples:")

        for value in present[:10]:
            print(f"      {value!r}")


def inspect_id_fields(
    features: list[dict[str, Any]],
    property_names: list[str],
) -> None:
    print("\nPotential ID / hierarchy fields:")

    candidates = [
        name
        for name in property_names
        if (
            "pcode" in name.lower()
            or name.lower().endswith("_id")
            or name.lower() in ID_FIELD_CANDIDATES
        )
    ]

    if not candidates:
        print("  NONE FOUND")
        return

    for field in candidates:
        values = [
            (feature.get("properties") or {}).get(field)
            for feature in features
        ]

        present = [
            value
            for value in values
            if not is_missing(value)
        ]

        counts = Counter(
            str(value)
            for value in present
        )

        duplicate_values = [
            value
            for value, count in counts.items()
            if count > 1
        ]

        print(
            f"  {field:<24} "
            f"present={len(present):>6,}  "
            f"unique={len(counts):>6,}  "
            f"duplicates={len(duplicate_values):>6,}"
        )

        samples = list(counts.keys())[:5]

        if samples:
            print(
                " " * 28
                + "samples="
                + ", ".join(repr(value) for value in samples)
            )


def inspect_geometry_types(
    features: list[dict[str, Any]],
) -> None:
    counts = Counter(
        (feature.get("geometry") or {}).get("type", "MISSING")
        for feature in features
    )

    print("\nGeometry types:")

    for geometry_type, count in sorted(counts.items()):
        print(f"  {geometry_type:<20} {count:>6,}")


def inspect_duplicates(
    features: list[dict[str, Any]],
    property_names: list[str],
) -> None:
    print("\nDuplicate name fields:")

    candidates = [
        name
        for name in property_names
        if "name" in name.lower()
    ]

    if not candidates:
        print("  NONE FOUND")
        return

    for field in candidates:
        values = [
            (feature.get("properties") or {}).get(field)
            for feature in features
        ]

        counts = Counter(
            str(value)
            for value in values
            if not is_missing(value)
        )

        duplicate_groups = {
            value: count
            for value, count in counts.items()
            if count > 1
        }

        duplicate_features = sum(
            duplicate_groups.values()
        )

        print(
            f"  {field:<24} "
            f"unique={len(counts):>6,}  "
            f"duplicate groups={len(duplicate_groups):>6,}  "
            f"duplicate features={duplicate_features:>6,}"
        )

        for value, count in sorted(
            duplicate_groups.items(),
            key=lambda item: (-item[1], item[0]),
        )[:10]:
            print(
                f"    {count:>3}x  {value}"
            )


def inspect_sample_features(
    features: list[dict[str, Any]],
) -> None:
    print("\nSample feature properties:")

    sample_indexes = list(
        dict.fromkeys(
            [
                0,
                1,
                2,
                len(features) // 2,
                len(features) - 1,
            ]
        )
    )

    for index in sample_indexes:
        if not 0 <= index < len(features):
            continue

        properties = (
            features[index].get("properties")
            or {}
        )

        print()
        print(f"  Feature {index:,}:")

        for key, value in properties.items():
            print(
                f"    {key}: {value!r}"
            )


def inspect_dataset(
    level: str,
    path: Path,
) -> None:
    print_heading(
        f"{level} — {path.name}"
    )

    print(
        f"File size: {path.stat().st_size / (1024 * 1024):,.2f} MB"
    )

    data = load_geojson(path)

    features = data.get("features", [])

    print(f"Features: {len(features):,}")

    inspect_top_level(data)

    property_names = get_all_property_names(features)

    inspect_properties(
        features,
        property_names,
    )

    inspect_name_fields(
        features,
        property_names,
    )

    inspect_id_fields(
        features,
        property_names,
    )

    inspect_geometry_types(features)

    inspect_duplicates(
        features,
        property_names,
    )

    inspect_sample_features(features)

    # Release the very large object before loading the next level.
    del data
    del features


def main() -> None:
    print("Thailand administrative boundary inspection")
    print(f"Source: {RAW_DIR.relative_to(PROJECT_ROOT)}")

    for level, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing input file: {path}"
            )

        inspect_dataset(
            level,
            path,
        )

    print_heading("INSPECTION COMPLETE")


if __name__ == "__main__":
    main()