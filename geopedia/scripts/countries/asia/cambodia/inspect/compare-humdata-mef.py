"""
Compares Cambodia's MEF administrative-name dataset with the HumData/OCHA
administrative boundary datasets.

MEF provides official Khmer/English administrative names and numeric codes.
HumData provides GeoJSON geometry, hierarchy, and PCodes.

This inspection verifies that the two sources can be joined safely by code:
    MEF 01     <-> HumData KH01
    MEF 0102   <-> HumData KH0102
    MEF 010201 <-> HumData KH010201

It also validates MEF hierarchy and name consistency and reports English-name
differences without treating those differences as join failures.

Inputs:
    data/raw/countries/cambodia/mef-admin-data.json
    data/raw/countries/cambodia/khm_admin_boundaries/khm_admin1.geojson
    data/raw/countries/cambodia/khm_admin_boundaries/khm_admin2.geojson
    data/raw/countries/cambodia/khm_admin_boundaries/khm_admin3.geojson

Run from the GeoPedia project root:
    python scripts/countries/asia/cambodia/inspect/compare-humdata-mef.py
"""

import json
from collections import defaultdict
from pathlib import Path


MEF_PATH = Path(
    "data/raw/countries/cambodia/mef-admin-data.json"
)

HUMDATA_DIR = Path(
    "data/raw/countries/cambodia/khm_admin_boundaries"
)

LEVELS = {
    "province": {
        "mef_code": "province_code",
        "mef_en": "province_en",
        "mef_kh": "province_kh",
        "humdata_file": "khm_admin1.geojson",
        "humdata_code": "adm1_pcode",
        "humdata_name": "adm1_name",
        "expected_count": 25,
    },
    "district": {
        "mef_code": "district_code",
        "mef_en": "district_en",
        "mef_kh": "district_kh",
        "humdata_file": "khm_admin2.geojson",
        "humdata_code": "adm2_pcode",
        "humdata_name": "adm2_name",
        "expected_count": 197,
    },
    "commune": {
        "mef_code": "commune_code",
        "mef_en": "commune_en",
        "mef_kh": "commune_kh",
        "humdata_file": "khm_admin3.geojson",
        "humdata_code": "adm3_pcode",
        "humdata_name": "adm3_name",
        "expected_count": 1633,
    },
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_mef_code(value) -> str:
    """
    Returns an MEF code as a zero-preserving string.
    """
    if value is None:
        return ""

    return str(value).strip()


def normalize_humdata_code(value) -> str:
    """
    Converts a HumData PCode such as KH010201 to the corresponding
    MEF-style code 010201.
    """
    if value is None:
        return ""

    code = str(value).strip()

    if code.upper().startswith("KH"):
        return code[2:]

    return code


def collect_mef_level(records, config):
    """
    Deduplicates village-level MEF rows into one entry per administrative
    code while retaining every observed English and Khmer name for
    consistency checks.
    """
    entries = defaultdict(
        lambda: {
            "english": set(),
            "khmer": set(),
        }
    )

    for record in records:
        code = normalize_mef_code(
            record.get(config["mef_code"])
        )

        if not code:
            continue

        english = record.get(config["mef_en"])
        khmer = record.get(config["mef_kh"])

        if english is not None:
            english = str(english).strip()

            if english:
                entries[code]["english"].add(english)

        if khmer is not None:
            khmer = str(khmer).strip()

            if khmer:
                entries[code]["khmer"].add(khmer)

    return entries


def collect_humdata_level(config):
    path = HUMDATA_DIR / config["humdata_file"]
    geojson = load_json(path)

    entries = {}

    duplicate_codes = []

    for feature in geojson["features"]:
        properties = feature.get("properties", {})

        raw_code = properties.get(
            config["humdata_code"]
        )

        code = normalize_humdata_code(raw_code)

        if not code:
            continue

        if code in entries:
            duplicate_codes.append(code)

        entries[code] = {
            "pcode": raw_code,
            "name": properties.get(
                config["humdata_name"]
            ),
        }

    return entries, duplicate_codes


def print_code_list(title, codes, entries=None):
    print(f"\n{title}: {len(codes):,}")

    if not codes:
        print("  None")
        return

    for code in sorted(codes):
        if entries and code in entries:
            entry = entries[code]

            english = sorted(
                entry.get("english", [])
            )

            khmer = sorted(
                entry.get("khmer", [])
            )

            details = []

            if english:
                details.append(
                    f"EN={english}"
                )

            if khmer:
                details.append(
                    f"KH={khmer}"
                )

            suffix = (
                " | " + " | ".join(details)
                if details
                else ""
            )

            print(f"  {code}{suffix}")
        else:
            print(f"  {code}")


def inspect_level(
    level_name,
    config,
    mef_records,
):
    print()
    print("=" * 72)
    print(level_name.upper())
    print("=" * 72)

    mef = collect_mef_level(
        mef_records,
        config,
    )

    humdata, humdata_duplicate_codes = (
        collect_humdata_level(config)
    )

    mef_codes = set(mef)
    humdata_codes = set(humdata)

    matched = mef_codes & humdata_codes
    only_mef = mef_codes - humdata_codes
    only_humdata = humdata_codes - mef_codes

    inconsistent_english = {
        code: entry["english"]
        for code, entry in mef.items()
        if len(entry["english"]) != 1
    }

    inconsistent_khmer = {
        code: entry["khmer"]
        for code, entry in mef.items()
        if len(entry["khmer"]) != 1
    }

    missing_english = {
        code
        for code, entry in mef.items()
        if not entry["english"]
    }

    missing_khmer = {
        code
        for code, entry in mef.items()
        if not entry["khmer"]
    }

    english_name_differences = []

    for code in sorted(matched):
        mef_names = mef[code]["english"]

        humdata_name = humdata[code]["name"]

        if len(mef_names) != 1:
            continue

        mef_name = next(iter(mef_names))

        if mef_name != humdata_name:
            english_name_differences.append(
                (
                    code,
                    mef_name,
                    humdata_name,
                )
            )

    expected = config["expected_count"]

    print(f"Expected count:        {expected:,}")
    print(f"MEF unique codes:      {len(mef):,}")
    print(f"HumData unique codes:  {len(humdata):,}")
    print(f"Matched codes:         {len(matched):,}")
    print(f"Only in MEF:           {len(only_mef):,}")
    print(f"Only in HumData:       {len(only_humdata):,}")

    print(
        f"MEF missing English:   "
        f"{len(missing_english):,}"
    )
    print(
        f"MEF missing Khmer:     "
        f"{len(missing_khmer):,}"
    )
    print(
        f"Inconsistent English:  "
        f"{len(inconsistent_english):,}"
    )
    print(
        f"Inconsistent Khmer:    "
        f"{len(inconsistent_khmer):,}"
    )
    print(
        f"HumData duplicate IDs: "
        f"{len(humdata_duplicate_codes):,}"
    )
    print(
        f"English name differs:  "
        f"{len(english_name_differences):,}"
    )

    if only_mef:
        print_code_list(
            "Codes only in MEF",
            only_mef,
            mef,
        )

    if only_humdata:
        print_code_list(
            "Codes only in HumData",
            only_humdata,
        )

    if inconsistent_english:
        print("\nInconsistent MEF English names:")

        for code in sorted(inconsistent_english):
            print(
                f"  {code}: "
                f"{sorted(inconsistent_english[code])}"
            )

    if inconsistent_khmer:
        print("\nInconsistent MEF Khmer names:")

        for code in sorted(inconsistent_khmer):
            print(
                f"  {code}: "
                f"{sorted(inconsistent_khmer[code])}"
            )

    if english_name_differences:
        print("\nEnglish-name differences:")
        print(
            "  (Informational only; codes are "
            "the intended join key.)"
        )

        for code, mef_name, humdata_name in (
            english_name_differences
        ):
            print(
                f"  {code}: "
                f"MEF={mef_name!r} | "
                f"HumData={humdata_name!r}"
            )

    perfect_code_match = (
        len(mef) == expected
        and len(humdata) == expected
        and not only_mef
        and not only_humdata
        and not humdata_duplicate_codes
    )

    names_consistent = (
        not missing_english
        and not missing_khmer
        and not inconsistent_english
        and not inconsistent_khmer
    )

    return perfect_code_match, names_consistent


def inspect_mef_hierarchy(records):
    print()
    print("=" * 72)
    print("MEF HIERARCHY")
    print("=" * 72)

    district_prefix_errors = []
    commune_prefix_errors = []
    village_prefix_errors = []

    district_parents = defaultdict(set)
    commune_parents = defaultdict(set)

    for record in records:
        province = normalize_mef_code(
            record.get("province_code")
        )
        district = normalize_mef_code(
            record.get("district_code")
        )
        commune = normalize_mef_code(
            record.get("commune_code")
        )
        village = normalize_mef_code(
            record.get("village_code")
        )

        if (
            province
            and district
            and not district.startswith(province)
        ):
            district_prefix_errors.append(
                (province, district)
            )

        if (
            district
            and commune
            and not commune.startswith(district)
        ):
            commune_prefix_errors.append(
                (district, commune)
            )

        if (
            commune
            and village
            and not village.startswith(commune)
        ):
            village_prefix_errors.append(
                (commune, village)
            )

        if district and province:
            district_parents[district].add(
                province
            )

        if commune and district:
            commune_parents[commune].add(
                district
            )

    multi_parent_districts = {
        code: parents
        for code, parents in district_parents.items()
        if len(parents) != 1
    }

    multi_parent_communes = {
        code: parents
        for code, parents in commune_parents.items()
        if len(parents) != 1
    }

    print(
        f"District prefix errors: "
        f"{len(district_prefix_errors):,}"
    )
    print(
        f"Commune prefix errors:  "
        f"{len(commune_prefix_errors):,}"
    )
    print(
        f"Village prefix errors:  "
        f"{len(village_prefix_errors):,}"
    )
    print(
        f"District parent errors: "
        f"{len(multi_parent_districts):,}"
    )
    print(
        f"Commune parent errors:  "
        f"{len(multi_parent_communes):,}"
    )

    return not any(
        (
            district_prefix_errors,
            commune_prefix_errors,
            village_prefix_errors,
            multi_parent_districts,
            multi_parent_communes,
        )
    )


def main():
    mef_records = load_json(MEF_PATH)

    if not isinstance(mef_records, list):
        raise RuntimeError(
            "Expected MEF raw data to be a JSON array."
        )

    print("Cambodia MEF / HumData comparison")
    print("=" * 72)
    print(
        f"MEF village-level records: "
        f"{len(mef_records):,}"
    )

    results = []

    for level_name, config in LEVELS.items():
        results.append(
            inspect_level(
                level_name,
                config,
                mef_records,
            )
        )

    hierarchy_ok = inspect_mef_hierarchy(
        mef_records
    )

    all_codes_match = all(
        code_match
        for code_match, _ in results
    )

    all_names_consistent = all(
        names_consistent
        for _, names_consistent in results
    )

    print()
    print("=" * 72)
    print("FINAL RESULT")
    print("=" * 72)

    print(
        f"All administrative codes match: "
        f"{'YES' if all_codes_match else 'NO'}"
    )

    print(
        f"MEF names internally consistent: "
        f"{'YES' if all_names_consistent else 'NO'}"
    )

    print(
        f"MEF hierarchy valid: "
        f"{'YES' if hierarchy_ok else 'NO'}"
    )

    if (
        all_codes_match
        and all_names_consistent
        and hierarchy_ok
    ):
        print()
        print(
            "MEF and HumData can be joined safely "
            "by administrative code."
        )
        print(
            "Use MEF English/Khmer names and codes "
            "with HumData geometry."
        )
    else:
        print()
        print(
            "Review the mismatches above before "
            "combining the datasets."
        )


if __name__ == "__main__":
    main()