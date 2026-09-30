"""
Processes Malaysia's 2-digit postal-code-prefix geography for GeoPedia.

The source GeoJSON comes from HelloQuiz and represents Malaysia's 2-digit
postal-code prefixes. Its source property is named `AreaCode`, despite the
features representing postal codes.

This script:

- Renames the source `AreaCode` values to GeoPedia's `post_code` property.
- Preserves every 2-digit prefix as a zero-padded string.
- Adds `post_code_1` for grouping the 2-digit quiz by first digit.
- Discards source City and label-coordinate metadata that is not needed at
  runtime.
- Dissolves the 2-digit features by first digit to create the 1-digit map.
- Validates both generated datasets.

Input
-----
data/raw/countries/malaysia/hello-quiz-postal-codes.geojson

Outputs
-------
public/data/countries/malaysia/geojson/postal-prefixes-2.geojson
public/data/countries/malaysia/geojson/postal-prefixes-1.geojson

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/process/postal-prefixes.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely import make_valid


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "malaysia"
    / "hello-quiz-postal-codes.geojson"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "malaysia"
    / "geojson"
)

POSTAL_PREFIXES_2_PATH = (
    OUTPUT_DIRECTORY
    / "postal-prefixes-2.geojson"
)

POSTAL_PREFIXES_1_PATH = (
    OUTPUT_DIRECTORY
    / "postal-prefixes-1.geojson"
)


# ---------------------------------------------------------------------------
# Expected source data
# ---------------------------------------------------------------------------

EXPECTED_SOURCE_FEATURE_COUNT = 83

EXPECTED_SOURCE_COLUMNS = {
    "AreaCode",
    "City",
    "labelx",
    "labely",
    "geometry",
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_source() -> gpd.GeoDataFrame:
    """Load and validate the HelloQuiz postal-code-prefix geography."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing HelloQuiz postal-code GeoJSON: {INPUT_PATH}"
        )

    frame = gpd.read_file(
        INPUT_PATH
    )

    missing_columns = (
        EXPECTED_SOURCE_COLUMNS
        - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "HelloQuiz postal-code GeoJSON is missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    if len(frame) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} source features "
            f"but found {len(frame)}."
        )

    if frame.crs is None:
        raise ValueError(
            "HelloQuiz postal-code GeoJSON has no CRS."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            "HelloQuiz postal-code GeoJSON contains missing geometries."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            "HelloQuiz postal-code GeoJSON contains empty geometries."
        )

    return frame


# ---------------------------------------------------------------------------
# 2-digit prefixes
# ---------------------------------------------------------------------------


def create_two_digit_prefixes(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Create GeoPedia's canonical 2-digit postal-prefix geography."""

    frame = source[
        [
            "AreaCode",
            "geometry",
        ]
    ].copy()

    # GeoPandas may infer values such as 01 or 06 numerically depending on the
    # source representation. Normalize every prefix back to exactly two digits.
    frame["post_code"] = (
        frame["AreaCode"]
        .astype(str)
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
        .str.zfill(2)
    )

    invalid_prefixes = frame.loc[
        ~frame["post_code"].str.fullmatch(
            r"\d{2}"
        ),
        "post_code",
    ].tolist()

    if invalid_prefixes:
        raise ValueError(
            "Invalid 2-digit postal-code prefixes: "
            + ", ".join(
                invalid_prefixes
            )
        )

    if frame["post_code"].duplicated().any():
        duplicates = (
            frame.loc[
                frame["post_code"].duplicated(
                    keep=False
                ),
                "post_code",
            ]
            .sort_values()
            .unique()
            .tolist()
        )

        raise ValueError(
            "Duplicate 2-digit postal-code prefixes: "
            + ", ".join(
                duplicates
            )
        )

    frame["post_code_1"] = (
        frame["post_code"].str[0]
    )

    frame = frame[
        [
            "post_code",
            "post_code_1",
            "geometry",
        ]
    ]

    frame = frame.sort_values(
        "post_code"
    ).reset_index(
        drop=True
    )

    return frame


# ---------------------------------------------------------------------------
# 1-digit prefixes
# ---------------------------------------------------------------------------


def create_one_digit_prefixes(
    two_digit: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve the 2-digit geography into 1-digit postal-prefix regions."""

    frame = two_digit[
        [
            "post_code_1",
            "geometry",
        ]
    ].copy()

    frame = frame.dissolve(
        by="post_code_1",
        as_index=False,
    )

    frame = frame.rename(
        columns={
            "post_code_1": "post_code",
        }
    )

    frame = frame[
        [
            "post_code",
            "geometry",
        ]
    ]

    frame = frame.sort_values(
        "post_code"
    ).reset_index(
        drop=True
    )

    return frame
  

def repair_invalid_geometries(
    frame: gpd.GeoDataFrame,
    name: str,
) -> gpd.GeoDataFrame:
    """Repair invalid geometries while preserving all feature properties."""

    frame = frame.copy()

    invalid_before = int(
        (~frame.geometry.is_valid).sum()
    )

    if invalid_before == 0:
        print(
            f"{name} invalid geometries: 0 -> 0"
        )

        return frame

    invalid_mask = (
        ~frame.geometry.is_valid
    )

    frame.loc[
        invalid_mask,
        "geometry",
    ] = frame.loc[
        invalid_mask,
        "geometry",
    ].geometry.apply(
        make_valid
    )

    invalid_after = int(
        (~frame.geometry.is_valid).sum()
    )

    print(
        f"{name} invalid geometries: "
        f"{invalid_before:,} -> {invalid_after:,}"
    )

    if invalid_after:
        raise ValueError(
            f"{name} still contains {invalid_after:,} invalid geometries "
            f"after repair."
        )

    return frame


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_geometry(
    frame: gpd.GeoDataFrame,
    name: str,
) -> None:
    """Validate common geometry requirements for a generated dataset."""

    if frame.geometry.isna().any():
        raise ValueError(
            f"{name} contains missing geometries."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            f"{name} contains empty geometries."
        )

    invalid_count = int(
        (~frame.geometry.is_valid).sum()
    )

    if invalid_count:
        raise ValueError(
            f"{name} contains {invalid_count:,} invalid geometries."
        )


def validate_two_digit_prefixes(
    frame: gpd.GeoDataFrame,
) -> None:
    """Validate the generated 2-digit postal-prefix dataset."""

    if len(frame) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} 2-digit prefixes "
            f"but found {len(frame)}."
        )

    if frame["post_code"].duplicated().any():
        raise ValueError(
            "Generated 2-digit postal prefixes are not unique."
        )

    if not frame["post_code"].str.fullmatch(
        r"\d{2}"
    ).all():
        raise ValueError(
            "Generated 2-digit postal prefixes are not all two digits."
        )

    if not frame["post_code_1"].str.fullmatch(
        r"\d"
    ).all():
        raise ValueError(
            "Generated 1-digit grouping properties are invalid."
        )

    expected_first_digits = (
        frame["post_code"].str[0]
    )

    if not frame["post_code_1"].equals(
        expected_first_digits
    ):
        raise ValueError(
            "One or more post_code_1 values do not match post_code."
        )

    validate_geometry(
        frame,
        "2-digit postal-prefix GeoJSON",
    )


def validate_one_digit_prefixes(
    frame: gpd.GeoDataFrame,
    two_digit: gpd.GeoDataFrame,
) -> None:
    """Validate the dissolved 1-digit postal-prefix dataset."""

    expected_prefixes = set(
        two_digit["post_code_1"]
    )

    actual_prefixes = set(
        frame["post_code"]
    )

    if actual_prefixes != expected_prefixes:
        raise ValueError(
            "Generated 1-digit prefix set does not match the 2-digit "
            "source geography."
        )

    if frame["post_code"].duplicated().any():
        raise ValueError(
            "Generated 1-digit postal prefixes are not unique."
        )

    if not frame["post_code"].str.fullmatch(
        r"\d"
    ).all():
        raise ValueError(
            "Generated 1-digit postal prefixes are invalid."
        )

    validate_geometry(
        frame,
        "1-digit postal-prefix GeoJSON",
    )


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def write_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """Write compact UTF-8 GeoJSON."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson: dict[str, Any] = json.loads(
        frame.to_json(
            drop_id=True,
        )
    )

    path.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_report(
    two_digit: gpd.GeoDataFrame,
    one_digit: gpd.GeoDataFrame,
) -> None:
    """Print a concise summary of the generated postal-prefix datasets."""

    print()
    print("2-digit postal prefixes")
    print("-----------------------")
    print(
        f"Features: {len(two_digit):,}"
    )
    print(
        "Prefixes: "
        + ", ".join(
            two_digit["post_code"].tolist()
        )
    )

    print()
    print("1-digit postal prefixes")
    print("-----------------------")
    print(
        f"Features: {len(one_digit):,}"
    )
    print(
        "Prefixes: "
        + ", ".join(
            one_digit["post_code"].tolist()
        )
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate Malaysia's 1- and 2-digit postal-prefix geography."""

    print()
    print(
        "Processing Malaysia postal-code prefixes..."
    )

    source = load_source()

    print()
    print(
        f"Source features: {len(source):,}"
    )

    two_digit = create_two_digit_prefixes(
        source
    )

    two_digit = repair_invalid_geometries(
        two_digit,
        "2-digit postal-prefix GeoJSON",
    )

    validate_two_digit_prefixes(
        two_digit
    )

    one_digit = create_one_digit_prefixes(
        two_digit
    )

    one_digit = repair_invalid_geometries(
        one_digit,
        "1-digit postal-prefix GeoJSON",
    )

    validate_one_digit_prefixes(
        one_digit,
        two_digit,
    )

    write_geojson(
        two_digit,
        POSTAL_PREFIXES_2_PATH,
    )

    write_geojson(
        one_digit,
        POSTAL_PREFIXES_1_PATH,
    )

    print_report(
        two_digit,
        one_digit,
    )

    print()
    print(
        "2-digit output: "
        + str(
            POSTAL_PREFIXES_2_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print(
        "1-digit output: "
        + str(
            POSTAL_PREFIXES_1_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print(
        "Malaysia postal-prefix processing complete."
    )


if __name__ == "__main__":
    main()