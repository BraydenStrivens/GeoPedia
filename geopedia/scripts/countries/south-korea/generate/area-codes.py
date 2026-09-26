"""
Generate South Korea telephone area-code GeoJSON for GeoPedia.

South Korea's geographic telephone area codes correspond to the 17
province-level administrative features used by GeoPedia. This script derives
two quiz-specific datasets from the already simplified province GeoJSON.

The full area-code dataset preserves the 17 province geometries and adds:
    area_code
    area_code_prefix

The prefix dataset dissolves those 17 features by the first significant digit
of the area code, producing five geographic regions:
    2, 3, 4, 5, 6

Inputs:
    public/data/countries/south-korea/geojson/provinces.geojson

Outputs:
    public/data/countries/south-korea/geojson/area-codes.geojson
    public/data/countries/south-korea/geojson/area-code-prefixes.geojson

Area-code source:
    Plonkit South Korea telephone area-code diagram.

Run from the GeoPedia project root:

    python scripts/countries/south-korea/generate/area-codes.py
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

GEOJSON_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "south-korea"
    / "geojson"
)

PROVINCES_INPUT = GEOJSON_DIR / "provinces.geojson"

AREA_CODES_OUTPUT = GEOJSON_DIR / "area-codes.geojson"

AREA_CODE_PREFIXES_OUTPUT = (
    GEOJSON_DIR / "area-code-prefixes.geojson"
)


EXPECTED_PROVINCE_COUNT = 17
EXPECTED_PREFIX_COUNT = 5


# Canonical province ID -> geographic telephone area code.
#
# Province IDs come from GeoPedia's canonical 2018 South Korea
# administrative dataset. Strings are used so leading zeroes are preserved.
AREA_CODES_BY_PROVINCE_ID = {
    "11": "02",   # Seoul
    "21": "051",  # Busan
    "22": "053",  # Daegu
    "23": "032",  # Incheon
    "24": "062",  # Gwangju
    "25": "042",  # Daejeon
    "26": "052",  # Ulsan
    "29": "044",  # Sejongsi
    "31": "031",  # Gyeonggi-do
    "32": "033",  # Gangwon-do
    "33": "043",  # Chungcheongbuk-do
    "34": "041",  # Chungcheongnam-do
    "35": "063",  # Jeollabuk-do
    "36": "061",  # Jeollanam-do
    "37": "054",  # Gyeongsangbuk-do
    "38": "055",  # Gyeongsangnam-do
    "39": "064",  # Jeju-do
}


def validate_provinces(
    provinces: gpd.GeoDataFrame,
) -> None:
    """Validate the province dataset required by area-code generation."""

    if len(provinces) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            f"Province GeoJSON has {len(provinces)} features; "
            f"expected {EXPECTED_PROVINCE_COUNT}."
        )

    required_columns = {
        "province_id",
        "province",
        "native_province",
        "geometry",
    }

    missing_columns = (
        required_columns
        - set(provinces.columns)
    )

    if missing_columns:
        raise ValueError(
            "Province GeoJSON is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    province_ids = set(
        provinces["province_id"].astype(str)
    )

    mapped_ids = set(
        AREA_CODES_BY_PROVINCE_ID
    )

    missing_codes = (
        province_ids
        - mapped_ids
    )

    unknown_ids = (
        mapped_ids
        - province_ids
    )

    if missing_codes:
        raise ValueError(
            "Area codes are missing for province IDs: "
            + ", ".join(sorted(missing_codes))
        )

    if unknown_ids:
        raise ValueError(
            "Area-code mapping contains unknown province IDs: "
            + ", ".join(sorted(unknown_ids))
        )

    if provinces.geometry.isna().any():
        raise ValueError(
            "Province GeoJSON contains null geometries."
        )

    if provinces.geometry.is_empty.any():
        raise ValueError(
            "Province GeoJSON contains empty geometries."
        )


def build_area_codes(
    provinces: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Add telephone area-code metadata to the province geometries.
    """

    area_codes = provinces[
        [
            "province_id",
            "province",
            "native_province",
            "geometry",
        ]
    ].copy()

    area_codes["province_id"] = (
        area_codes["province_id"].astype(str)
    )

    area_codes["area_code"] = (
        area_codes["province_id"].map(
            AREA_CODES_BY_PROVINCE_ID
        )
    )

    # Remove the leading zero and take the first significant digit.
    #
    # Examples:
    #   02  -> 2
    #   031 -> 3
    #   044 -> 4
    #   055 -> 5
    #   064 -> 6
    area_codes["area_code_prefix"] = (
        area_codes["area_code"]
        .str.lstrip("0")
        .str[0]
    )

    return area_codes


def build_area_code_prefixes(
    area_codes: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Dissolve province geometries into first-significant-digit regions.
    """

    prefixes = area_codes[
        [
            "area_code_prefix",
            "geometry",
        ]
    ].dissolve(
        by="area_code_prefix",
        as_index=False,
    )

    prefixes = prefixes[
        [
            "area_code_prefix",
            "geometry",
        ]
    ]

    return prefixes


def validate_area_codes(
    area_codes: gpd.GeoDataFrame,
) -> None:
    """Validate the generated full area-code dataset."""

    if len(area_codes) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            f"Generated {len(area_codes)} area-code features; "
            f"expected {EXPECTED_PROVINCE_COUNT}."
        )

    if area_codes["area_code"].isna().any():
        raise ValueError(
            "Generated area-code dataset contains missing area codes."
        )

    if area_codes["area_code_prefix"].isna().any():
        raise ValueError(
            "Generated area-code dataset contains missing prefixes."
        )

    if area_codes["area_code"].duplicated().any():
        duplicates = sorted(
            area_codes.loc[
                area_codes["area_code"].duplicated(
                    keep=False
                ),
                "area_code",
            ].unique()
        )

        raise ValueError(
            "Duplicate geographic area codes: "
            + ", ".join(duplicates)
        )

    actual_prefixes = set(
        area_codes["area_code_prefix"]
    )

    expected_prefixes = {
        "2",
        "3",
        "4",
        "5",
        "6",
    }

    if actual_prefixes != expected_prefixes:
        raise ValueError(
            "Unexpected area-code prefixes. "
            f"Found: {sorted(actual_prefixes)}"
        )


def validate_prefixes(
    prefixes: gpd.GeoDataFrame,
) -> None:
    """Validate the generated dissolved prefix dataset."""

    if len(prefixes) != EXPECTED_PREFIX_COUNT:
        raise ValueError(
            f"Generated {len(prefixes)} prefix features; "
            f"expected {EXPECTED_PREFIX_COUNT}."
        )

    if prefixes["area_code_prefix"].duplicated().any():
        raise ValueError(
            "Generated prefix dataset contains duplicate prefixes."
        )

    if prefixes.geometry.isna().any():
        raise ValueError(
            "Generated prefix dataset contains null geometries."
        )

    if prefixes.geometry.is_empty.any():
        raise ValueError(
            "Generated prefix dataset contains empty geometries."
        )


def write_geojson(
    data: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """Write a GeoDataFrame as GeoJSON."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_file(
        path,
        driver="GeoJSON",
    )


def write_question_data(
    area_codes: gpd.GeoDataFrame,
) -> None:
    """
    Write the two static TypeScript question sets used by the quizzes.
    """

    output_path = (
        PROJECT_ROOT
        / "src"
        / "quiz"
        / "quizzes"
        / "countries"
        / "asia"
        / "south-korea"
        / "data"
        / "areaCodeQuestions.ts"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    area_code_rows = (
        area_codes[
            [
                "province_id",
                "area_code",
            ]
        ]
        .sort_values("area_code")
        .to_dict("records")
    )

    lines = [
        "/**",
        " * Generated South Korea telephone area-code questions.",
        " *",
        " * Do not edit this file manually.",
        " *",
        " * Regenerate with:",
        " *   python scripts/countries/south-korea/generate/area-codes.py",
        " */",
        "",
        'import type { FeatureQuizQuestion } from "@/types/quiz";',
        "",
        "export const SOUTH_KOREA_AREA_CODE_QUESTIONS: "
        "FeatureQuizQuestion[] = [",
    ]

    for row in area_code_rows:
        lines.append(
            f'  {{ answer: "{row["province_id"]}", '
            f'display: "{row["area_code"]}" }},'
        )

    lines.extend(
        [
            "];",
            "",
            "export const SOUTH_KOREA_AREA_CODE_PREFIX_QUESTIONS: "
            "FeatureQuizQuestion[] = [",
            '  { answer: "2", display: "02-" },',
            '  { answer: "3", display: "03-" },',
            '  { answer: "4", display: "04-" },',
            '  { answer: "5", display: "05-" },',
            '  { answer: "6", display: "06-" },',
            "];",
            "",
        ]
    )

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        f"Wrote question data: {output_path}"
    )


def main() -> None:
    """Generate South Korea's geographic telephone area-code datasets."""

    print(
        "Generating South Korea telephone "
        "area-code data..."
    )
    print()

    if not PROVINCES_INPUT.exists():
        raise FileNotFoundError(
            f"Province GeoJSON not found: {PROVINCES_INPUT}"
        )

    print("Reading provinces...")
    provinces = gpd.read_file(
        PROVINCES_INPUT
    )

    validate_provinces(
        provinces
    )

    print("Building area-code features...")
    area_codes = build_area_codes(
        provinces
    )

    validate_area_codes(
        area_codes
    )

    print("Building area-code prefix features...")
    prefixes = build_area_code_prefixes(
        area_codes
    )

    validate_prefixes(
        prefixes
    )

    print("Writing area codes...")
    write_geojson(
        area_codes,
        AREA_CODES_OUTPUT,
    )

    print("Writing area-code prefixes...")
    write_geojson(
        prefixes,
        AREA_CODE_PREFIXES_OUTPUT,
    )

    print("Writing question data...")
    write_question_data(
        area_codes
    )

    print()
    print(
        "South Korea telephone area-code "
        "generation complete."
    )
    print(
        f"Area-code features: {len(area_codes)}"
    )
    print(
        f"Prefix features:    {len(prefixes)}"
    )

    print()
    print("Features by prefix:")

    counts = (
        area_codes
        .groupby("area_code_prefix")
        .size()
    )

    for prefix, count in counts.items():
        print(
            f"  0{prefix}-: {count} provinces"
        )

    print()
    print("Output files:")
    print(f"  {AREA_CODES_OUTPUT}")
    print(f"  {AREA_CODE_PREFIXES_OUTPUT}")


if __name__ == "__main__":
    main()