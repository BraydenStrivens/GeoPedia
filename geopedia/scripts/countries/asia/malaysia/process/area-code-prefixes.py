"""
Processes Malaysia's telephone area-code geography for GeoPedia.

The source HelloQuiz GeoJSON contains Malaysia's full geographic telephone
area codes, such as 032, 044, and 089. This script uses those features to
create GeoPedia's 2-digit and 1-digit area-code-prefix maps.

For GeoPedia's quiz naming, "2-digit" and "1-digit" refer to the significant
digits following Malaysia's fixed leading 0:

- 032 -> 2-digit prefix/full area code
- 03  -> 1-digit prefix

The 2-digit output preserves separate source features when the same area code
occurs in more than one geographic region. Each feature therefore receives a
stable unique `area_code_id`, while `area_code` remains the quiz answer.

The 1-digit output dissolves all features sharing the same first significant
digit.

Input
-----
data/raw/countries/malaysia/hello-quiz-area-codes.geojson

Outputs
-------
public/data/countries/malaysia/geojson/area-code-prefixes-2.geojson
public/data/countries/malaysia/geojson/area-code-prefixes-1.geojson

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/process/area-code-prefixes.py
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
    / "hello-quiz-area-codes.geojson"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "malaysia"
    / "geojson"
)

AREA_CODE_PREFIXES_2_PATH = (
    OUTPUT_DIRECTORY
    / "area-code-prefixes-2.geojson"
)

AREA_CODE_PREFIXES_1_PATH = (
    OUTPUT_DIRECTORY
    / "area-code-prefixes-1.geojson"
)


# ---------------------------------------------------------------------------
# Expected source data
# ---------------------------------------------------------------------------

EXPECTED_SOURCE_FEATURE_COUNT = 53

EXPECTED_SOURCE_COLUMNS = {
    "AreaCode",
    "geometry",
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_source() -> gpd.GeoDataFrame:
    """Load and validate the HelloQuiz area-code geography."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing HelloQuiz area-code GeoJSON: {INPUT_PATH}"
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
            "HelloQuiz area-code GeoJSON is missing required columns: "
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
            "HelloQuiz area-code GeoJSON has no CRS."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            "HelloQuiz area-code GeoJSON contains missing geometries."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            "HelloQuiz area-code GeoJSON contains empty geometries."
        )

    return frame


# ---------------------------------------------------------------------------
# Geometry repair
# ---------------------------------------------------------------------------


def repair_invalid_geometries(
    frame: gpd.GeoDataFrame,
    name: str,
) -> gpd.GeoDataFrame:
    """Repair invalid geometries while preserving feature properties."""

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
# 2-digit prefixes
# ---------------------------------------------------------------------------


def create_two_digit_prefixes(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Create the full 2-digit-prefix area-code geography."""

    frame = source[
        [
            "AreaCode",
            "geometry",
        ]
    ].copy()

    frame["area_code"] = (
        frame["AreaCode"]
        .astype(str)
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
        .str.zfill(3)
    )

    invalid_codes = frame.loc[
        ~frame["area_code"].str.fullmatch(
            r"0\d{2}"
        ),
        "area_code",
    ].tolist()

    if invalid_codes:
        raise ValueError(
            "Invalid Malaysian area codes: "
            + ", ".join(
                invalid_codes
            )
        )

    # The first significant digit plus Malaysia's leading trunk 0.
    #
    # Example:
    # 032 -> 03
    # 089 -> 08
    frame["area_code_1"] = (
        frame["area_code"].str[:2]
    )

    # `area_code` cannot serve as feature identity because a code may occur in
    # more than one disconnected source feature. Assign deterministic IDs in
    # source order, suffixing repeated codes.
    occurrence = (
        frame.groupby(
            "area_code"
        )
        .cumcount()
        + 1
    )

    counts = frame.groupby(
        "area_code"
    )["area_code"].transform(
        "size"
    )

    frame["area_code_id"] = frame["area_code"]

    duplicate_mask = counts > 1

    frame.loc[
        duplicate_mask,
        "area_code_id",
    ] = (
        frame.loc[
            duplicate_mask,
            "area_code",
        ]
        + "-"
        + occurrence.loc[
            duplicate_mask
        ].astype(str)
    )

    frame = frame[
        [
            "area_code_id",
            "area_code",
            "area_code_1",
            "geometry",
        ]
    ]

    frame = frame.sort_values(
        [
            "area_code",
            "area_code_id",
        ]
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
    """Dissolve the full area codes into 1-digit-prefix regions."""

    frame = two_digit[
        [
            "area_code_1",
            "geometry",
        ]
    ].copy()

    frame = frame.dissolve(
        by="area_code_1",
        as_index=False,
    )

    frame = frame.rename(
        columns={
            "area_code_1": "area_code",
        }
    )

    frame["area_code_id"] = (
        frame["area_code"]
    )

    frame = frame[
        [
            "area_code_id",
            "area_code",
            "geometry",
        ]
    ]

    frame = frame.sort_values(
        "area_code"
    ).reset_index(
        drop=True
    )

    return frame


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_geometry(
    frame: gpd.GeoDataFrame,
    name: str,
) -> None:
    """Validate generated geometry."""

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
    """Validate the generated 2-digit-prefix dataset."""

    if len(frame) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} 2-digit area-code "
            f"features but found {len(frame)}."
        )

    if frame["area_code_id"].duplicated().any():
        raise ValueError(
            "Generated 2-digit area-code feature IDs are not unique."
        )

    if not frame["area_code"].str.fullmatch(
        r"0\d{2}"
    ).all():
        raise ValueError(
            "Generated 2-digit area codes are invalid."
        )

    if not frame["area_code_1"].str.fullmatch(
        r"0\d"
    ).all():
        raise ValueError(
            "Generated 1-digit grouping values are invalid."
        )

    expected_groups = (
        frame["area_code"].str[:2]
    )

    if not frame["area_code_1"].equals(
        expected_groups
    ):
        raise ValueError(
            "One or more area_code_1 values do not match area_code."
        )

    validate_geometry(
        frame,
        "2-digit area-code GeoJSON",
    )


def validate_one_digit_prefixes(
    frame: gpd.GeoDataFrame,
    two_digit: gpd.GeoDataFrame,
) -> None:
    """Validate the dissolved 1-digit-prefix dataset."""

    expected_prefixes = set(
        two_digit["area_code_1"]
    )

    actual_prefixes = set(
        frame["area_code"]
    )

    if actual_prefixes != expected_prefixes:
        raise ValueError(
            "Generated 1-digit prefix set does not match the 2-digit "
            "source geography."
        )

    if frame["area_code_id"].duplicated().any():
        raise ValueError(
            "Generated 1-digit area-code feature IDs are not unique."
        )

    if not frame["area_code"].str.fullmatch(
        r"0\d"
    ).all():
        raise ValueError(
            "Generated 1-digit area-code prefixes are invalid."
        )

    validate_geometry(
        frame,
        "1-digit area-code GeoJSON",
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
    """Print a concise summary of the generated datasets."""

    unique_two_digit = sorted(
        two_digit["area_code"].unique()
    )

    duplicate_codes = sorted(
        two_digit.loc[
            two_digit["area_code"].duplicated(
                keep=False
            ),
            "area_code",
        ].unique()
    )

    print()
    print("2-digit area-code prefixes")
    print("--------------------------")
    print(
        f"Features: {len(two_digit):,}"
    )
    print(
        f"Unique codes: {len(unique_two_digit):,}"
    )
    print(
        "Codes: "
        + ", ".join(
            unique_two_digit
        )
    )

    if duplicate_codes:
        print(
            "Codes with multiple features: "
            + ", ".join(
                duplicate_codes
            )
        )

    print()
    print("1-digit area-code prefixes")
    print("--------------------------")
    print(
        f"Features: {len(one_digit):,}"
    )
    print(
        "Prefixes: "
        + ", ".join(
            one_digit["area_code"].tolist()
        )
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate Malaysia's 1- and 2-digit area-code-prefix geography."""

    print()
    print(
        "Processing Malaysia area-code prefixes..."
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
        "2-digit area-code GeoJSON",
    )

    validate_two_digit_prefixes(
        two_digit
    )

    one_digit = create_one_digit_prefixes(
        two_digit
    )

    one_digit = repair_invalid_geometries(
        one_digit,
        "1-digit area-code GeoJSON",
    )

    validate_one_digit_prefixes(
        one_digit,
        two_digit,
    )

    write_geojson(
        two_digit,
        AREA_CODE_PREFIXES_2_PATH,
    )

    write_geojson(
        one_digit,
        AREA_CODE_PREFIXES_1_PATH,
    )

    print_report(
        two_digit,
        one_digit,
    )

    print()
    print(
        "2-digit output: "
        + str(
            AREA_CODE_PREFIXES_2_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print(
        "1-digit output: "
        + str(
            AREA_CODE_PREFIXES_1_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print(
        "Malaysia area-code-prefix processing complete."
    )


if __name__ == "__main__":
    main()