from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

POSTAL_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "ecuador"
    / "postal"
    / "geonames"
    / "EC.txt"
)

PROVINCES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "ecuador"
    / "geojson"
    / "provinces.geojson"
)

CANTONS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "ecuador"
    / "geojson"
    / "cantons.geojson"
)


# ---------------------------------------------------------------------------
# GeoNames postal columns
# ---------------------------------------------------------------------------

COUNTRY_CODE = 0
POSTAL_CODE = 1
PLACE_NAME = 2
ADMIN1_NAME = 3
ADMIN1_CODE = 4
ADMIN2_NAME = 5
ADMIN2_CODE = 6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_name(
    value: str,
) -> str:
    return (
        value
        .strip()
        .casefold()
        .replace("cantón ", "")
        .replace("canton ", "")
    )


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_postal_rows() -> list[list[str]]:
    rows: list[list[str]] = []

    with POSTAL_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.reader(
            file,
            delimiter="\t",
        )

        for line_number, row in enumerate(
            reader,
            start=1,
        ):
            if not row:
                continue

            if len(row) < 12:
                raise ValueError(
                    f"Postal row {line_number} has only "
                    f"{len(row)} columns."
                )

            postal_code = row[
                POSTAL_CODE
            ].strip()

            if (
                len(postal_code) != 6
                or not postal_code.isdigit()
            ):
                raise ValueError(
                    f"Postal row {line_number} has "
                    f"invalid postal code "
                    f"{postal_code!r}."
                )

            rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Administrative data
# ---------------------------------------------------------------------------

def load_provinces() -> dict[str, str]:
    data = load_geojson(
        PROVINCES_PATH
    )

    provinces: dict[str, str] = {}

    for feature in data["features"]:
        properties = feature[
            "properties"
        ]

        province_id = properties[
            "province_id"
        ]

        province = properties[
            "province"
        ]

        if not province_id.startswith(
            "EC"
        ):
            raise ValueError(
                f"Unexpected province ID: "
                f"{province_id}"
            )

        postal_prefix = province_id[2:]

        if len(postal_prefix) != 2:
            raise ValueError(
                f"Province ID {province_id} "
                "does not produce a 2-digit prefix."
            )

        if postal_prefix in provinces:
            raise ValueError(
                f"Duplicate province prefix: "
                f"{postal_prefix}"
            )

        provinces[
            postal_prefix
        ] = province

    return provinces


def load_cantons() -> dict[
    str,
    tuple[str, str],
]:
    data = load_geojson(
        CANTONS_PATH
    )

    cantons: dict[
        str,
        tuple[str, str],
    ] = {}

    for feature in data["features"]:
        properties = feature[
            "properties"
        ]

        canton_id = properties[
            "canton_id"
        ]

        canton = properties[
            "canton"
        ]

        province = properties[
            "province"
        ]

        if not canton_id.startswith(
            "EC"
        ):
            raise ValueError(
                f"Unexpected canton ID: "
                f"{canton_id}"
            )

        postal_prefix = canton_id[2:]

        if len(postal_prefix) != 4:
            raise ValueError(
                f"Canton ID {canton_id} "
                "does not produce a 4-digit prefix."
            )

        if postal_prefix in cantons:
            raise ValueError(
                f"Duplicate canton prefix: "
                f"{postal_prefix}"
            )

        cantons[
            postal_prefix
        ] = (
            canton,
            province,
        )

    return cantons


# ---------------------------------------------------------------------------
# Province analysis
# ---------------------------------------------------------------------------

def analyze_provinces(
    postal_rows: list[list[str]],
    provinces: dict[str, str],
) -> None:
    prefix_rows: dict[
        str,
        list[list[str]],
    ] = defaultdict(list)

    for row in postal_rows:
        prefix = row[
            POSTAL_CODE
        ][:2]

        prefix_rows[
            prefix
        ].append(row)

    matched_rows = 0
    mismatched_rows = 0
    unknown_prefix_rows = 0

    matched_prefixes: set[str] = set()
    mismatched_prefixes: set[str] = set()
    unknown_prefixes: set[str] = set()

    mismatch_details: Counter[
        tuple[str, str, str]
    ] = Counter()

    for prefix, rows in prefix_rows.items():
        expected_province = provinces.get(
            prefix
        )

        if expected_province is None:
            unknown_prefixes.add(
                prefix
            )

            unknown_prefix_rows += len(
                rows
            )

            continue

        prefix_has_mismatch = False

        for row in rows:
            geonames_province = row[
                ADMIN1_NAME
            ].strip()

            if (
                normalize_name(
                    geonames_province
                )
                == normalize_name(
                    expected_province
                )
            ):
                matched_rows += 1
            else:
                mismatched_rows += 1
                prefix_has_mismatch = True

                mismatch_details[
                    (
                        prefix,
                        expected_province,
                        geonames_province,
                    )
                ] += 1

        if prefix_has_mismatch:
            mismatched_prefixes.add(
                prefix
            )
        else:
            matched_prefixes.add(
                prefix
            )

    comparable_rows = (
        matched_rows
        + mismatched_rows
    )

    agreement = (
        matched_rows
        / comparable_rows
        * 100
        if comparable_rows
        else 0
    )

    print()
    print(
        "===== PROVINCE PREFIX TEST ====="
    )

    print(
        f"Administrative provinces: "
        f"{len(provinces):,}"
    )

    print(
        f"Postal prefixes observed: "
        f"{len(prefix_rows):,}"
    )

    print(
        f"Matching rows:            "
        f"{matched_rows:,}"
    )

    print(
        f"Mismatching rows:         "
        f"{mismatched_rows:,}"
    )

    print(
        f"Unknown-prefix rows:      "
        f"{unknown_prefix_rows:,}"
    )

    print(
        f"Agreement:                "
        f"{agreement:.2f}%"
    )

    print()
    print(
        "Unknown postal prefixes:"
    )

    if unknown_prefixes:
        for prefix in sorted(
            unknown_prefixes
        ):
            print(
                f"  {prefix}: "
                f"{len(prefix_rows[prefix]):,} rows"
            )
    else:
        print("  None")

    print()
    print(
        "Province mismatches:"
    )

    if mismatch_details:
        for (
            prefix,
            expected,
            actual,
        ), count in sorted(
            mismatch_details.items()
        ):
            print(
                f"  {prefix}: "
                f"expected {expected!r}, "
                f"GeoNames says {actual!r} "
                f"({count:,} rows)"
            )
    else:
        print("  None")


# ---------------------------------------------------------------------------
# Canton analysis
# ---------------------------------------------------------------------------

def analyze_cantons(
    postal_rows: list[list[str]],
    cantons: dict[
        str,
        tuple[str, str],
    ],
) -> None:
    prefix_rows: dict[
        str,
        list[list[str]],
    ] = defaultdict(list)

    for row in postal_rows:
        prefix = row[
            POSTAL_CODE
        ][:4]

        prefix_rows[
            prefix
        ].append(row)

    matched_rows = 0
    mismatched_rows = 0
    unknown_prefix_rows = 0

    exact_prefix_matches = 0
    clean_prefix_matches = 0
    mixed_prefix_matches = 0
    mismatch_only_prefixes = 0
    unknown_prefixes = 0

    mismatch_details: Counter[
        tuple[
            str,
            str,
            str,
            str,
        ]
    ] = Counter()

    for prefix, rows in sorted(
        prefix_rows.items()
    ):
        expected = cantons.get(
            prefix
        )

        if expected is None:
            unknown_prefixes += 1
            unknown_prefix_rows += len(
                rows
            )
            continue

        exact_prefix_matches += 1

        expected_canton, expected_province = (
            expected
        )

        prefix_matches = 0
        prefix_mismatches = 0

        for row in rows:
            geonames_canton = row[
                ADMIN2_NAME
            ].strip()

            geonames_province = row[
                ADMIN1_NAME
            ].strip()

            canton_matches = (
                normalize_name(
                    geonames_canton
                )
                == normalize_name(
                    expected_canton
                )
            )

            province_matches = (
                normalize_name(
                    geonames_province
                )
                == normalize_name(
                    expected_province
                )
            )

            if (
                canton_matches
                and province_matches
            ):
                matched_rows += 1
                prefix_matches += 1
            else:
                mismatched_rows += 1
                prefix_mismatches += 1

                mismatch_details[
                    (
                        prefix,
                        expected_canton,
                        geonames_canton,
                        geonames_province,
                    )
                ] += 1

        if (
            prefix_matches > 0
            and prefix_mismatches == 0
        ):
            clean_prefix_matches += 1

        elif (
            prefix_matches > 0
            and prefix_mismatches > 0
        ):
            mixed_prefix_matches += 1

        else:
            mismatch_only_prefixes += 1

    comparable_rows = (
        matched_rows
        + mismatched_rows
    )

    row_agreement = (
        matched_rows
        / comparable_rows
        * 100
        if comparable_rows
        else 0
    )

    observed_prefixes = len(
        prefix_rows
    )

    prefix_coverage = (
        exact_prefix_matches
        / observed_prefixes
        * 100
        if observed_prefixes
        else 0
    )

    admin_coverage = (
        exact_prefix_matches
        / len(cantons)
        * 100
        if cantons
        else 0
    )

    print()
    print(
        "===== CANTON PREFIX TEST ====="
    )

    print(
        f"Administrative cantons:   "
        f"{len(cantons):,}"
    )

    print(
        f"Postal prefixes observed: "
        f"{observed_prefixes:,}"
    )

    print(
        f"Prefixes existing as "
        f"canton IDs:               "
        f"{exact_prefix_matches:,}"
    )

    print(
        f"Postal-prefix coverage:   "
        f"{prefix_coverage:.2f}%"
    )

    print(
        f"Canton coverage:           "
        f"{admin_coverage:.2f}%"
    )

    print()
    print(
        f"Matching rows:             "
        f"{matched_rows:,}"
    )

    print(
        f"Mismatching rows:          "
        f"{mismatched_rows:,}"
    )

    print(
        f"Unknown-prefix rows:       "
        f"{unknown_prefix_rows:,}"
    )

    print(
        f"Row agreement:             "
        f"{row_agreement:.2f}%"
    )

    print()
    print(
        "Observed prefix quality:"
    )

    print(
        f"  Clean matches:           "
        f"{clean_prefix_matches:,}"
    )

    print(
        f"  Mixed matches:           "
        f"{mixed_prefix_matches:,}"
    )

    print(
        f"  Mismatch only:           "
        f"{mismatch_only_prefixes:,}"
    )

    print(
        f"  Unknown prefixes:        "
        f"{unknown_prefixes:,}"
    )

    print()
    print(
        "Canton mismatch combinations:"
    )

    if mismatch_details:
        for (
            prefix,
            expected_canton,
            actual_canton,
            actual_province,
        ), count in sorted(
            mismatch_details.items()
        ):
            print(
                f"  {prefix}: "
                f"expected {expected_canton!r}; "
                f"GeoNames says "
                f"{actual_canton!r}, "
                f"{actual_province!r} "
                f"({count:,} rows)"
            )
    else:
        print("  None")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Inspecting Ecuador postal/admin "
        "code relationships..."
    )

    postal_rows = load_postal_rows()

    provinces = load_provinces()
    cantons = load_cantons()

    print()
    print(
        f"Postal records: "
        f"{len(postal_rows):,}"
    )

    analyze_provinces(
        postal_rows,
        provinces,
    )

    analyze_cantons(
        postal_rows,
        cantons,
    )


if __name__ == "__main__":
    main()