"""
Compare Ghana's researched postcode-district mapping against GeoPedia's
canonical administrative data.

Inputs
------
data/raw/countries/ghana/postcode-districts.csv
data/intermediate/countries/ghana/admin/regions.geojson
data/intermediate/countries/ghana/admin/districts.geojson

This script does not modify any data. It normalizes names for comparison,
reports exact and normalized matches, identifies unmatched records on either
side, detects multiple postcode codes mapping to one administrative district,
and verifies the postcode region assignments against GeoPedia's hierarchy.

Run
---
python scripts/countries/ghana/inspect/postcode-district-matches.py
"""

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

POSTCODE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "ghana"
    / "postcode-districts.csv"
)

REGIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ghana"
    / "admin"
    / "regions.geojson"
)

DISTRICTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ghana"
    / "admin"
    / "districts.geojson"
)


EXPECTED_REGION_COUNT = 16
EXPECTED_DISTRICT_COUNT = 260


# Administrative suffixes are omitted by many postcode sources but appear
# frequently in administrative boundary datasets.
ADMIN_SUFFIXES = {
    "district",
    "municipal",
    "municipality",
    "metropolitan",
    "metropolis",
    "assembly",
}


def normalize_name(value: str) -> str:
    """
    Normalize an administrative name for comparison.

    The original source values remain untouched. Normalization only assists
    with detecting likely matches despite punctuation, capitalization,
    diacritics, or administrative suffix differences.
    """
    value = unicodedata.normalize(
        "NFKD",
        str(value),
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    value = value.casefold()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    words = [
        word
        for word in value.split()
        if word not in ADMIN_SUFFIXES
    ]

    return " ".join(words)


def load_data():
    """Load and minimally validate all comparison datasets."""
    if not POSTCODE_PATH.exists():
        raise FileNotFoundError(
            f"Postcode CSV not found: {POSTCODE_PATH}"
        )

    if not REGIONS_PATH.exists():
        raise FileNotFoundError(
            f"Region GeoJSON not found: {REGIONS_PATH}"
        )

    if not DISTRICTS_PATH.exists():
        raise FileNotFoundError(
            f"District GeoJSON not found: {DISTRICTS_PATH}"
        )

    postcodes = pd.read_csv(
        POSTCODE_PATH,
        dtype=str,
        keep_default_na=False,
    )

    regions = gpd.read_file(
        REGIONS_PATH
    )

    districts = gpd.read_file(
        DISTRICTS_PATH
    )

    required_postcode_columns = {
        "region",
        "district",
        "postcode_district_code",
    }

    missing = (
        required_postcode_columns
        - set(postcodes.columns)
    )

    if missing:
        raise ValueError(
            "Postcode CSV is missing columns: "
            f"{sorted(missing)}"
        )

    if len(regions) != EXPECTED_REGION_COUNT:
        raise ValueError(
            "Unexpected canonical region count: "
            f"{len(regions)}"
        )

    if len(districts) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected canonical district count: "
            f"{len(districts)}"
        )

    return postcodes, regions, districts


def main() -> None:
    """Compare postcode mappings with Ghana's canonical admin hierarchy."""
    postcodes, regions, districts = load_data()

    postcodes = postcodes.copy()
    regions = regions.copy()
    districts = districts.copy()

    postcodes["region_key"] = (
        postcodes["region"].map(
            normalize_name
        )
    )

    postcodes["district_key"] = (
        postcodes["district"].map(
            normalize_name
        )
    )

    regions["region_key"] = (
        regions["region"].map(
            normalize_name
        )
    )

    districts["region_key"] = (
        districts["region"].map(
            normalize_name
        )
    )

    districts["district_key"] = (
        districts["district"].map(
            normalize_name
        )
    )

    print(
        "Comparing Ghana postcode districts with canonical admin data..."
    )
    print()

    print("=== COUNTS ===")
    print(
        f"Canonical regions:          {len(regions)}"
    )
    print(
        f"Canonical districts:        {len(districts)}"
    )
    print(
        f"Postcode rows:              {len(postcodes)}"
    )
    print(
        "Distinct postcode codes:    "
        f"{postcodes['postcode_district_code'].nunique()}"
    )
    print()

    # ------------------------------------------------------------------
    # Region comparison
    # ------------------------------------------------------------------

    canonical_region_keys = set(
        regions["region_key"]
    )

    postcode_region_keys = set(
        postcodes["region_key"]
    )

    unmatched_postcode_regions = (
        postcode_region_keys
        - canonical_region_keys
    )

    missing_postcode_regions = (
        canonical_region_keys
        - postcode_region_keys
    )

    print("=== REGION MATCHING ===")
    print(
        "Postcode regions not matching canonical regions:",
        len(unmatched_postcode_regions),
    )

    for key in sorted(
        unmatched_postcode_regions
    ):
        names = sorted(
            set(
                postcodes.loc[
                    postcodes["region_key"] == key,
                    "region",
                ]
            )
        )

        print(
            f"  POSTCODE ONLY: {names}"
        )

    print(
        "Canonical regions absent from postcode data:",
        len(missing_postcode_regions),
    )

    for key in sorted(
        missing_postcode_regions
    ):
        names = sorted(
            set(
                regions.loc[
                    regions["region_key"] == key,
                    "region",
                ]
            )
        )

        print(
            f"  CANONICAL ONLY: {names}"
        )

    print()

    # ------------------------------------------------------------------
    # District matching
    # ------------------------------------------------------------------

    canonical_lookup = {}

    for _, row in districts.iterrows():
        key = (
            row["region_key"],
            row["district_key"],
        )

        canonical_lookup.setdefault(
            key,
            [],
        ).append(row)

    postcode_lookup = {}

    for _, row in postcodes.iterrows():
        key = (
            row["region_key"],
            row["district_key"],
        )

        postcode_lookup.setdefault(
            key,
            [],
        ).append(row)

    matched_keys = (
        set(canonical_lookup)
        & set(postcode_lookup)
    )

    canonical_only = (
        set(canonical_lookup)
        - set(postcode_lookup)
    )

    postcode_only = (
        set(postcode_lookup)
        - set(canonical_lookup)
    )

    print("=== DISTRICT MATCHING ===")
    print(
        f"Matched canonical districts: {len(matched_keys)}"
    )
    print(
        f"Canonical districts unmatched: {len(canonical_only)}"
    )
    print(
        f"Postcode rows unmatched:        "
        f"{sum(len(postcode_lookup[key]) for key in postcode_only)}"
    )
    print()

    if canonical_only:
        print(
            "--- CANONICAL DISTRICTS WITHOUT A POSTCODE MATCH ---"
        )

        for key in sorted(
            canonical_only
        ):
            for row in canonical_lookup[key]:
                print(
                    f"  {row['region']} | "
                    f"{row['district']} | "
                    f"{row['district_id']}"
                )

        print()

    if postcode_only:
        print(
            "--- POSTCODE ENTRIES WITHOUT A CANONICAL MATCH ---"
        )

        for key in sorted(
            postcode_only
        ):
            for row in postcode_lookup[key]:
                print(
                    f"  {row['region']} | "
                    f"{row['district']} | "
                    f"{row['postcode_district_code']}"
                )

        print()

    # ------------------------------------------------------------------
    # Multiple codes per matched canonical district
    # ------------------------------------------------------------------

    print(
        "=== MULTIPLE POSTCODE CODES PER MATCHED DISTRICT ==="
    )

    multiple_code_count = 0

    for key in sorted(
        matched_keys
    ):
        postcode_rows = (
            postcode_lookup[key]
        )

        codes = sorted(
            {
                str(
                    row[
                        "postcode_district_code"
                    ]
                )
                for row in postcode_rows
            }
        )

        if len(codes) <= 1:
            continue

        multiple_code_count += 1

        canonical_row = (
            canonical_lookup[key][0]
        )

        print(
            f"  {canonical_row['region']} | "
            f"{canonical_row['district']} | "
            f"{', '.join(codes)}"
        )

    if multiple_code_count == 0:
        print("  None")

    print()

    # ------------------------------------------------------------------
    # Duplicate postcode codes
    # ------------------------------------------------------------------

    code_groups = (
        postcodes.groupby(
            "postcode_district_code"
        )
    )

    duplicated_codes = []

    for code, group in code_groups:
        if len(group) > 1:
            duplicated_codes.append(
                (
                    code,
                    group,
                )
            )

    print(
        "=== POSTCODE CODES USED BY MULTIPLE SOURCE ROWS ==="
    )

    if not duplicated_codes:
        print("  None")
    else:
        for code, group in duplicated_codes:
            print(
                f"  {code}:"
            )

            for _, row in group.iterrows():
                print(
                    f"    {row['region']} | "
                    f"{row['district']}"
                )

    print()

    # ------------------------------------------------------------------
    # Prefix / region relationship
    # ------------------------------------------------------------------

    print(
        "=== FIRST-CHARACTER PREFIXES BY REGION ==="
    )

    postcodes["prefix"] = (
        postcodes[
            "postcode_district_code"
        ]
        .astype(str)
        .str[0]
    )

    region_prefixes = (
        postcodes.groupby("region")[
            "prefix"
        ]
        .apply(
            lambda values: sorted(
                set(values)
            )
        )
    )

    for region, prefixes in (
        region_prefixes.items()
    ):
        print(
            f"  {region}: "
            f"{', '.join(prefixes)}"
        )

    print()

    regions_with_multiple_prefixes = (
        region_prefixes[
            region_prefixes.map(len) > 1
        ]
    )

    print(
        "Regions with multiple first-character prefixes:",
        len(regions_with_multiple_prefixes),
    )

    for region, prefixes in (
        regions_with_multiple_prefixes.items()
    ):
        print(
            f"  {region}: "
            f"{', '.join(prefixes)}"
        )

    print()
    print(
        "Comparison complete."
    )


if __name__ == "__main__":
    main()