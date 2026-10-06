"""
Compare Cambodia gazetteer administrative codes with the HumData/OCHA
administrative boundary GeoJSON files.

The gazetteer contains Khmer and Latin names in a nested hierarchy, while the
HumData files contain the boundary geometry needed by GeoPedia. This inspection
normalizes the gazetteer codes and determines whether features can be joined
reliably by administrative ID rather than by name.

The comparison covers:
    ADM1: Provinces
    ADM2: Districts
    ADM3: Communes

Villages are intentionally ignored.

Inputs:
    data/raw/countries/cambodia/cambodia_gazetteer.json

    data/raw/countries/cambodia/khm_admin_boundaries/
        khm_admin1.geojson
        khm_admin2.geojson
        khm_admin3.geojson

Usage:
    python scripts/countries/asia/cambodia/inspect/compare-gazetteer-humdata.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]

GAZETTEER_PATH = (
    PROJECT_ROOT
    / "data/raw/countries/cambodia/cambodia_gazetteer.json"
)

HUMDATA_DIR = (
    PROJECT_ROOT
    / "data/raw/countries/cambodia/khm_admin_boundaries"
)

HUMDATA_PATHS = {
    1: HUMDATA_DIR / "khm_admin1.geojson",
    2: HUMDATA_DIR / "khm_admin2.geojson",
    3: HUMDATA_DIR / "khm_admin3.geojson",
}

HUMDATA_ID_FIELDS = {
    1: "adm1_pcode",
    2: "adm2_pcode",
    3: "adm3_pcode",
}

HUMDATA_NAME_FIELDS = {
    1: "adm1_name",
    2: "adm2_name",
    3: "adm3_name",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def digits_only(value: Any) -> str:
    return "".join(character for character in str(value) if character.isdigit())


def normalize_province_code(raw_code: Any) -> str:
    """
    Normalize a gazetteer province code to the two-digit code used inside
    HumData PCodes.

    Example:
        01 -> 01
    """
    digits = digits_only(raw_code)

    if not digits:
        raise ValueError(f"Empty province code: {raw_code!r}")

    return digits[-2:].zfill(2)


def normalize_district_code(raw_code: Any) -> str:
    """
    Normalize a gazetteer district code to the four-digit code used inside
    HumData PCodes.

    Gazetteer example:
        000102 -> 0102
    """
    digits = digits_only(raw_code)

    if not digits:
        raise ValueError(f"Empty district code: {raw_code!r}")

    return digits[-4:].zfill(4)


def normalize_commune_code(
    raw_code: Any,
    district_code: str,
) -> str:
    """
    Normalize a gazetteer commune code to the six-digit code used inside
    HumData PCodes.

    Gazetteer commune codes may omit a leading zero.

    Example:
        district 0102 + commune 10201 -> 010201
    """
    digits = digits_only(raw_code)

    if not digits:
        raise ValueError(f"Empty commune code: {raw_code!r}")

    # The gazetteer examples omit the leading zero from six-digit codes.
    if len(digits) <= 6:
        candidate = digits.zfill(6)

        if candidate.startswith(district_code):
            return candidate

    # If formatting is stranger than expected, retain the commune suffix
    # and reconstruct the ID from the already-normalized parent district.
    if len(digits) >= 2:
        return district_code + digits[-2:]

    raise ValueError(
        f"Cannot normalize commune code {raw_code!r} "
        f"under district {district_code}"
    )


def build_gazetteer_records(
    gazetteer: list[dict[str, Any]],
) -> dict[int, list[dict[str, str]]]:
    records: dict[int, list[dict[str, str]]] = {
        1: [],
        2: [],
        3: [],
    }

    for province in gazetteer:
        province_code = normalize_province_code(province["code"])

        records[1].append(
            {
                "code": province_code,
                "khmer": province.get("khmer", ""),
                "latin": province.get("latin", ""),
                "parent": "",
            }
        )

        for district in province.get("districts", []):
            district_code = normalize_district_code(district["code"])

            records[2].append(
                {
                    "code": district_code,
                    "khmer": district.get("khmer", ""),
                    "latin": district.get("latin", ""),
                    "parent": province_code,
                }
            )

            for commune in district.get("communes", []):
                commune_code = normalize_commune_code(
                    commune["code"],
                    district_code,
                )

                records[3].append(
                    {
                        "code": commune_code,
                        "khmer": commune.get("khmer", ""),
                        "latin": commune.get("latin", ""),
                        "parent": district_code,
                    }
                )

    return records


def build_humdata_records(
    level: int,
) -> list[dict[str, str]]:
    data = load_json(HUMDATA_PATHS[level])

    id_field = HUMDATA_ID_FIELDS[level]
    name_field = HUMDATA_NAME_FIELDS[level]

    records: list[dict[str, str]] = []

    for feature in data.get("features", []):
        properties = feature.get("properties") or {}

        raw_pcode = str(properties.get(id_field, "")).strip()
        code = raw_pcode.removeprefix("KH")

        records.append(
            {
                "code": code,
                "name": str(properties.get(name_field, "")).strip(),
            }
        )

    return records


def print_duplicate_codes(
    label: str,
    records: list[dict[str, str]],
) -> None:
    counts = Counter(record["code"] for record in records)
    duplicates = sorted(
        code
        for code, count in counts.items()
        if count > 1
    )

    print(f"{label} duplicate codes: {len(duplicates):,}")

    for code in duplicates[:20]:
        print(f"  {code}: {counts[code]} occurrences")

    if len(duplicates) > 20:
        print(f"  ... {len(duplicates) - 20:,} more")


def compare_level(
    level: int,
    label: str,
    gazetteer_records: list[dict[str, str]],
) -> None:
    humdata_records = build_humdata_records(level)

    gazetteer_by_code = {
        record["code"]: record
        for record in gazetteer_records
    }

    humdata_by_code = {
        record["code"]: record
        for record in humdata_records
    }

    gazetteer_codes = set(gazetteer_by_code)
    humdata_codes = set(humdata_by_code)

    shared = sorted(gazetteer_codes & humdata_codes)
    gazetteer_only = sorted(gazetteer_codes - humdata_codes)
    humdata_only = sorted(humdata_codes - gazetteer_codes)

    print()
    print("=" * 80)
    print(label)
    print("=" * 80)

    print()
    print("COUNTS")
    print(f"Gazetteer records:       {len(gazetteer_records):,}")
    print(f"Gazetteer unique codes:  {len(gazetteer_codes):,}")
    print(f"HumData records:         {len(humdata_records):,}")
    print(f"HumData unique codes:    {len(humdata_codes):,}")

    print()
    print("CODE MATCHING")
    print(f"Shared codes:        {len(shared):,}")
    print(f"Gazetteer only:      {len(gazetteer_only):,}")
    print(f"HumData only:        {len(humdata_only):,}")

    print()
    print_duplicate_codes("Gazetteer", gazetteer_records)
    print_duplicate_codes("HumData", humdata_records)

    if gazetteer_only:
        print()
        print("GAZETTEER-ONLY FEATURES")

        for code in gazetteer_only:
            record = gazetteer_by_code[code]
            print(
                f"  {code}: "
                f"{record['latin']} | {record['khmer']}"
            )

    if humdata_only:
        print()
        print("HUMDATA-ONLY FEATURES")

        for code in humdata_only:
            record = humdata_by_code[code]
            print(f"  {code}: {record['name']}")

    name_differences: list[
        tuple[str, str, str, str]
    ] = []

    for code in shared:
        gazetteer_record = gazetteer_by_code[code]
        humdata_record = humdata_by_code[code]

        gazetteer_name = gazetteer_record["latin"]
        humdata_name = humdata_record["name"]

        if gazetteer_name.casefold() != humdata_name.casefold():
            name_differences.append(
                (
                    code,
                    gazetteer_name,
                    humdata_name,
                    gazetteer_record["khmer"],
                )
            )

    print()
    print("NAME CHECK")
    print(
        "Shared codes with different Latin/English names: "
        f"{len(name_differences):,}"
    )

    if name_differences:
        print()
        print("Name differences:")

        for (
            code,
            gazetteer_name,
            humdata_name,
            khmer_name,
        ) in name_differences:
            print(f"  {code}")
            print(f"    Gazetteer: {gazetteer_name}")
            print(f"    HumData:   {humdata_name}")
            print(f"    Khmer:     {khmer_name}")

    missing_khmer = [
        record
        for record in gazetteer_records
        if not record["khmer"].strip()
    ]

    missing_latin = [
        record
        for record in gazetteer_records
        if not record["latin"].strip()
    ]

    print()
    print("GAZETTEER NAME COMPLETENESS")
    print(f"Missing Khmer names: {len(missing_khmer):,}")
    print(f"Missing Latin names: {len(missing_latin):,}")

    complete_join = (
        len(shared) == len(humdata_codes)
        and not humdata_only
    )

    exact_set = gazetteer_codes == humdata_codes

    print()
    print("SUMMARY")
    print(
        "Every HumData feature has a gazetteer code match: "
        f"{'YES' if complete_join else 'NO'}"
    )
    print(
        "Gazetteer and HumData code sets are identical: "
        f"{'YES' if exact_set else 'NO'}"
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    gazetteer = load_json(GAZETTEER_PATH)

    if not isinstance(gazetteer, list):
        raise TypeError(
            "Expected the gazetteer root to be a JSON array."
        )

    records = build_gazetteer_records(gazetteer)

    print("Cambodia gazetteer vs HumData administrative-code comparison")

    compare_level(
        1,
        "ADM1 / Provinces",
        records[1],
    )

    compare_level(
        2,
        "ADM2 / Districts",
        records[2],
    )

    compare_level(
        3,
        "ADM3 / Communes",
        records[3],
    )


if __name__ == "__main__":
    main()