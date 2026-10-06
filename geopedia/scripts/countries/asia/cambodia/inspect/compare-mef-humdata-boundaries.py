"""
Compare MEF-hosted Cambodia boundary GeoJSON files with the local HumData/OCHA
administrative boundary files.

This inspection determines whether the MEF boundary downloads are identical to,
or materially different from, the HumData/OCHA 2018 boundary data already in
GeoPedia. It compares feature counts, schemas, populated fields, Khmer text,
administrative codes, properties, geometry, and whole-file SHA-256 hashes.

Inputs:
    data/raw/countries/cambodia/mef/
        CambodiaProvinceBoundaries.geojson
        CambodiaDistrictBoundaries.geojson
        CambodiaCommuneBoundaries.geojson

    data/raw/countries/cambodia/khm_admin_boundaries/
        khm_admin1.geojson
        khm_admin2.geojson
        khm_admin3.geojson

Usage:
    python scripts/countries/asia/cambodia/inspect/compare-mef-humdata-boundaries.py
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]

MEF_DIR = PROJECT_ROOT / "data/raw/countries/cambodia/mef"
HUMDATA_DIR = PROJECT_ROOT / "data/raw/countries/cambodia/khm_admin_boundaries"

LEVELS = [
    {
        "label": "ADM1 / Provinces",
        "level": 1,
        "mef": MEF_DIR / "CambodiaProvinceBoundaries.geojson",
        "humdata": HUMDATA_DIR / "khm_admin1.geojson",
        "id_field": "adm1_pcode",
    },
    {
        "label": "ADM2 / Districts",
        "level": 2,
        "mef": MEF_DIR / "CambodiaDistrictBoundaries.geojson",
        "humdata": HUMDATA_DIR / "khm_admin2.geojson",
        "id_field": "adm2_pcode",
    },
    {
        "label": "ADM3 / Communes",
        "level": 3,
        "mef": MEF_DIR / "CambodiaCommuneBoundaries.geojson",
        "humdata": HUMDATA_DIR / "khm_admin3.geojson",
        "id_field": "adm3_pcode",
    },
]

KHMER_RE = re.compile(r"[\u1780-\u17FF]")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def feature_properties(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        feature.get("properties") or {}
        for feature in data.get("features", [])
    ]


def all_property_names(data: dict[str, Any]) -> list[str]:
    names: set[str] = set()

    for properties in feature_properties(data):
        names.update(properties.keys())

    return sorted(names)


def is_populated(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, dict)):
        return bool(value)

    return True


def populated_count(data: dict[str, Any], field: str) -> int:
    return sum(
        1
        for properties in feature_properties(data)
        if is_populated(properties.get(field))
    )


def khmer_values(data: dict[str, Any]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []

    for properties in feature_properties(data):
        for field, value in properties.items():
            if isinstance(value, str) and KHMER_RE.search(value):
                found.append((field, value))

    return found


def geometry_types(data: dict[str, Any]) -> Counter[str]:
    return Counter(
        (feature.get("geometry") or {}).get("type", "<missing>")
        for feature in data.get("features", [])
    )


def id_map(
    data: dict[str, Any],
    id_field: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    result: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []

    for feature in data.get("features", []):
        properties = feature.get("properties") or {}
        raw_id = properties.get(id_field)

        if not is_populated(raw_id):
            continue

        feature_id = str(raw_id).strip()

        if feature_id in result:
            duplicates.append(feature_id)
        else:
            result[feature_id] = feature

    return result, sorted(set(duplicates))


def print_field_population(
    title: str,
    data: dict[str, Any],
    fields: list[str],
) -> None:
    feature_count = len(data.get("features", []))

    print(title)

    for field in fields:
        count = populated_count(data, field)
        print(f"  {field:<24} {count:>5} / {feature_count}")


def compare_level(config: dict[str, Any]) -> None:
    label = config["label"]
    level = config["level"]
    mef_path: Path = config["mef"]
    humdata_path: Path = config["humdata"]
    id_field: str = config["id_field"]

    print()
    print("=" * 80)
    print(label)
    print("=" * 80)

    for path in (mef_path, humdata_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")

    mef = load_json(mef_path)
    humdata = load_json(humdata_path)

    mef_features = mef.get("features", [])
    humdata_features = humdata.get("features", [])

    mef_hash = sha256(mef_path)
    humdata_hash = sha256(humdata_path)

    print()
    print("FILES")
    print(f"MEF:      {mef_path.relative_to(PROJECT_ROOT)}")
    print(f"HumData:  {humdata_path.relative_to(PROJECT_ROOT)}")
    print(f"MEF size:      {mef_path.stat().st_size:,} bytes")
    print(f"HumData size:  {humdata_path.stat().st_size:,} bytes")

    print()
    print("SHA-256")
    print(f"MEF:      {mef_hash}")
    print(f"HumData:  {humdata_hash}")
    print(f"Byte-identical: {'YES' if mef_hash == humdata_hash else 'NO'}")

    print()
    print("FEATURE COUNTS")
    print(f"MEF:      {len(mef_features):,}")
    print(f"HumData:  {len(humdata_features):,}")
    print(
        "Same count: "
        f"{'YES' if len(mef_features) == len(humdata_features) else 'NO'}"
    )

    print()
    print("GEOMETRY TYPES")
    print(f"MEF:      {dict(geometry_types(mef))}")
    print(f"HumData:  {dict(geometry_types(humdata))}")

    mef_fields = all_property_names(mef)
    humdata_fields = all_property_names(humdata)

    print()
    print("PROPERTY SCHEMA")
    print(f"MEF fields ({len(mef_fields)}):")
    for field in mef_fields:
        print(f"  {field}")

    print()
    print(f"HumData fields ({len(humdata_fields)}):")
    for field in humdata_fields:
        print(f"  {field}")

    mef_only_fields = sorted(set(mef_fields) - set(humdata_fields))
    humdata_only_fields = sorted(set(humdata_fields) - set(mef_fields))

    print()
    print("SCHEMA DIFFERENCES")
    print(
        "MEF-only fields: "
        + (", ".join(mef_only_fields) if mef_only_fields else "None")
    )
    print(
        "HumData-only fields: "
        + (", ".join(humdata_only_fields) if humdata_only_fields else "None")
    )

    interesting_fields = sorted(
        set(mef_fields)
        | set(humdata_fields)
    )

    print()
    print_field_population(
        "MEF POPULATED FIELDS",
        mef,
        interesting_fields,
    )

    print()
    print_field_population(
        "HUMDATA POPULATED FIELDS",
        humdata,
        interesting_fields,
    )

    mef_khmer = khmer_values(mef)
    humdata_khmer = khmer_values(humdata)

    print()
    print("KHMER TEXT")
    print(f"MEF Khmer property values:      {len(mef_khmer):,}")
    print(f"HumData Khmer property values:  {len(humdata_khmer):,}")

    if mef_khmer:
        print()
        print("Sample MEF Khmer values:")
        for field, value in mef_khmer[:10]:
            print(f"  {field}: {value}")

    if humdata_khmer:
        print()
        print("Sample HumData Khmer values:")
        for field, value in humdata_khmer[:10]:
            print(f"  {field}: {value}")

    # Explicitly inspect the alternate/native name fields used by the
    # HumData Cambodia administrative schema.
    native_fields = [
        f"adm{level}_name1",
        f"adm{level}_name2",
        f"adm{level}_name3",
    ]

    print()
    print("NATIVE / ALTERNATE NAME FIELDS")

    for field in native_fields:
        if field not in mef_fields and field not in humdata_fields:
            continue

        mef_count = populated_count(mef, field)
        humdata_count = populated_count(humdata, field)

        print(
            f"{field}: "
            f"MEF {mef_count:,}/{len(mef_features):,}, "
            f"HumData {humdata_count:,}/{len(humdata_features):,}"
        )

    mef_by_id, mef_duplicate_ids = id_map(mef, id_field)
    humdata_by_id, humdata_duplicate_ids = id_map(humdata, id_field)

    mef_ids = set(mef_by_id)
    humdata_ids = set(humdata_by_id)

    shared_ids = sorted(mef_ids & humdata_ids)
    mef_only_ids = sorted(mef_ids - humdata_ids)
    humdata_only_ids = sorted(humdata_ids - mef_ids)

    print()
    print(f"ADMINISTRATIVE IDS ({id_field})")
    print(f"MEF unique IDs:       {len(mef_ids):,}")
    print(f"HumData unique IDs:   {len(humdata_ids):,}")
    print(f"Shared IDs:           {len(shared_ids):,}")
    print(f"MEF-only IDs:         {len(mef_only_ids):,}")
    print(f"HumData-only IDs:     {len(humdata_only_ids):,}")
    print(f"MEF duplicate IDs:    {len(mef_duplicate_ids):,}")
    print(f"HumData duplicate IDs:{len(humdata_duplicate_ids):,}")

    if mef_only_ids:
        print()
        print("MEF-only IDs:")
        for feature_id in mef_only_ids[:50]:
            print(f"  {feature_id}")

        if len(mef_only_ids) > 50:
            print(f"  ... {len(mef_only_ids) - 50:,} more")

    if humdata_only_ids:
        print()
        print("HumData-only IDs:")
        for feature_id in humdata_only_ids[:50]:
            print(f"  {feature_id}")

        if len(humdata_only_ids) > 50:
            print(f"  ... {len(humdata_only_ids) - 50:,} more")

    property_differences: list[
        tuple[str, dict[str, tuple[Any, Any]]]
    ] = []

    geometry_differences: list[str] = []

    for feature_id in shared_ids:
        mef_feature = mef_by_id[feature_id]
        humdata_feature = humdata_by_id[feature_id]

        mef_properties = mef_feature.get("properties") or {}
        humdata_properties = humdata_feature.get("properties") or {}

        differing_fields: dict[str, tuple[Any, Any]] = {}

        for field in sorted(
            set(mef_properties) | set(humdata_properties)
        ):
            mef_value = mef_properties.get(field)
            humdata_value = humdata_properties.get(field)

            if mef_value != humdata_value:
                differing_fields[field] = (
                    mef_value,
                    humdata_value,
                )

        if differing_fields:
            property_differences.append(
                (feature_id, differing_fields)
            )

        if mef_feature.get("geometry") != humdata_feature.get("geometry"):
            geometry_differences.append(feature_id)

    print()
    print("MATCHING-ID COMPARISON")
    print(
        "Features with property differences: "
        f"{len(property_differences):,} / {len(shared_ids):,}"
    )
    print(
        "Features with geometry differences: "
        f"{len(geometry_differences):,} / {len(shared_ids):,}"
    )

    if property_differences:
        print()
        print("Sample property differences:")

        for feature_id, differences in property_differences[:10]:
            print(f"  {feature_id}")

            for field, (mef_value, humdata_value) in differences.items():
                print(f"    {field}")
                print(f"      MEF:     {mef_value!r}")
                print(f"      HumData: {humdata_value!r}")

    if geometry_differences:
        print()
        print("Sample IDs with geometry differences:")

        for feature_id in geometry_differences[:20]:
            print(f"  {feature_id}")

    same_ids = mef_ids == humdata_ids
    same_schema = set(mef_fields) == set(humdata_fields)
    same_properties = not property_differences
    same_geometry = not geometry_differences

    print()
    print("SUMMARY")
    print(f"Same feature count:       {'YES' if len(mef_features) == len(humdata_features) else 'NO'}")
    print(f"Same ID set:              {'YES' if same_ids else 'NO'}")
    print(f"Same property schema:     {'YES' if same_schema else 'NO'}")
    print(f"Same properties by ID:    {'YES' if same_properties else 'NO'}")
    print(f"Same geometry by ID:      {'YES' if same_geometry else 'NO'}")
    print(f"Byte-identical files:     {'YES' if mef_hash == humdata_hash else 'NO'}")
    print(f"MEF contains Khmer text:  {'YES' if mef_khmer else 'NO'}")


def main() -> None:
    print("Cambodia MEF vs HumData boundary comparison")

    for config in LEVELS:
        compare_level(config)


if __name__ == "__main__":
    main()