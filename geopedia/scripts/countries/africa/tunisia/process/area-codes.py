"""
Create Tunisia's runtime geographic landline area-code GeoJSON.

Input
-----
public/data/countries/tunisia/geojson/governorates.geojson

Output
------
public/data/countries/tunisia/geojson/area-codes.geojson

The already-simplified governorate geometry is reused directly so this derived
dataset does not require another simplification pass.

Tunisia's 24 governorates are dissolved into eight geographic landline
area-code regions. Most regions have one valid area code, while Grand Tunis
uses 70, 71, and 79.

Only properties required by the runtime map and quiz are retained:

    area_code_id
    area_codes
    governorates

The `governorates` property provides the map's hover label by listing all
governorates represented by the geographic area-code feature.
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "tunisia"
    / "geojson"
    / "governorates.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "tunisia"
    / "geojson"
    / "area-codes.geojson"
)


EXPECTED_GOVERNORATE_COUNT = 24
EXPECTED_OUTPUT_FEATURE_COUNT = 8

EXPECTED_AREA_CODES = {
    "70",
    "71",
    "72",
    "73",
    "74",
    "75",
    "76",
    "77",
    "78",
    "79",
}


# ---------------------------------------------------------------------------
# Geographic area-code definitions
# ---------------------------------------------------------------------------

# Each entry defines one geographic landline area-code region.
#
# Governorate names intentionally match the canonical `governorate` property
# in Tunisia's processed administrative GeoJSON.
AREA_CODE_REGIONS = [
    {
        "area_codes": ["70", "71", "79"],
        "governorates": [
            "Tunis",
            "Ariana",
            "Ben Arous",
            "Manubah",
        ],
    },
    {
        "area_codes": ["72"],
        "governorates": [
            "Bizerte",
            "Nabeul",
            "Zaghouan",
        ],
    },
    {
        "area_codes": ["73"],
        "governorates": [
            "Sousse",
            "Monastir",
            "Mahdia",
        ],
    },
    {
        "area_codes": ["74"],
        "governorates": [
            "Sfax",
        ],
    },
    {
        "area_codes": ["75"],
        "governorates": [
            "Gabès",
            "Médenine",
            "Tataouine",
            "Kebili",
        ],
    },
    {
        "area_codes": ["76"],
        "governorates": [
            "Gafsa",
            "Tozeur",
            "Sidi Bou Zid",
        ],
    },
    {
        "area_codes": ["77"],
        "governorates": [
            "Kairouan",
            "Kassérine",
        ],
    },
    {
        "area_codes": ["78"],
        "governorates": [
            "Béja",
            "Jendouba",
            "Le Kef",
            "Siliana",
        ],
    },
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_governorates() -> gpd.GeoDataFrame:
    """Load and validate Tunisia's simplified governorate runtime geometry."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Governorate GeoJSON not found: {INPUT_PATH}"
        )

    frame = gpd.read_file(
        INPUT_PATH
    )

    if len(frame) != EXPECTED_GOVERNORATE_COUNT:
        raise ValueError(
            "Unexpected governorate count: "
            f"expected {EXPECTED_GOVERNORATE_COUNT}, "
            f"found {len(frame)}."
        )

    required_properties = {
        "governorate_id",
        "governorate",
    }

    missing_properties = (
        required_properties
        - set(frame.columns)
    )

    if missing_properties:
        raise ValueError(
            "Governorate GeoJSON is missing required properties: "
            f"{sorted(missing_properties)}"
        )

    if frame["governorate_id"].isna().any():
        raise ValueError(
            "Governorate GeoJSON contains a null governorate_id."
        )

    if frame["governorate_id"].duplicated().any():
        raise ValueError(
            "Governorate GeoJSON contains duplicate governorate IDs."
        )

    if frame["governorate"].isna().any():
        raise ValueError(
            "Governorate GeoJSON contains a null governorate name."
        )

    if frame["governorate"].duplicated().any():
        raise ValueError(
            "Governorate GeoJSON contains duplicate governorate names."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            "Governorate GeoJSON contains null geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            "Governorate GeoJSON contains empty geometry."
        )

    return frame


# ---------------------------------------------------------------------------
# Definition validation
# ---------------------------------------------------------------------------


def validate_area_code_regions(
    governorates: gpd.GeoDataFrame,
) -> None:
    """
    Validate the configured geographic area-code regions.

    Every source governorate must appear exactly once, and every expected
    geographic landline area code must be represented exactly once.
    """
    source_governorates = set(
        governorates["governorate"].astype(str)
    )

    configured_governorates: list[str] = []
    configured_area_codes: list[str] = []

    for region in AREA_CODE_REGIONS:
        area_codes = region[
            "area_codes"
        ]

        region_governorates = region[
            "governorates"
        ]

        if not area_codes:
            raise ValueError(
                "Area-code region has no area codes."
            )

        if not region_governorates:
            raise ValueError(
                "Area-code region has no governorates."
            )

        for area_code in area_codes:
            if (
                not isinstance(area_code, str)
                or len(area_code) != 2
                or not area_code.isdigit()
            ):
                raise ValueError(
                    f"Invalid area code: {area_code!r}"
                )

            configured_area_codes.append(
                area_code
            )

        for governorate in region_governorates:
            if not isinstance(
                governorate,
                str,
            ):
                raise ValueError(
                    "Area-code region contains a non-string "
                    "governorate name."
                )

            configured_governorates.append(
                governorate
            )

    duplicate_governorates = {
        governorate
        for governorate in configured_governorates
        if configured_governorates.count(
            governorate
        ) > 1
    }

    if duplicate_governorates:
        raise ValueError(
            "Governorates assigned to multiple area-code regions: "
            f"{sorted(duplicate_governorates)}"
        )

    configured_governorate_set = set(
        configured_governorates
    )

    missing_governorates = (
        source_governorates
        - configured_governorate_set
    )

    unknown_governorates = (
        configured_governorate_set
        - source_governorates
    )

    if missing_governorates:
        raise ValueError(
            "Governorates without area-code assignments: "
            f"{sorted(missing_governorates)}"
        )

    if unknown_governorates:
        raise ValueError(
            "Area-code definitions reference unknown governorates: "
            f"{sorted(unknown_governorates)}"
        )

    duplicate_area_codes = {
        area_code
        for area_code in configured_area_codes
        if configured_area_codes.count(
            area_code
        ) > 1
    }

    if duplicate_area_codes:
        raise ValueError(
            "Area codes assigned to multiple geographic regions: "
            f"{sorted(duplicate_area_codes)}"
        )

    represented_area_codes = set(
        configured_area_codes
    )

    if represented_area_codes != EXPECTED_AREA_CODES:
        missing_area_codes = (
            EXPECTED_AREA_CODES
            - represented_area_codes
        )

        unexpected_area_codes = (
            represented_area_codes
            - EXPECTED_AREA_CODES
        )

        raise ValueError(
            "Area-code answer set does not match expectations. "
            f"Missing: {sorted(missing_area_codes)}. "
            f"Unexpected: {sorted(unexpected_area_codes)}."
        )


# ---------------------------------------------------------------------------
# Feature construction
# ---------------------------------------------------------------------------


def create_area_code_id(
    area_codes: list[str],
) -> str:
    """
    Create a stable scalar map identity from a complete area-code set.

    Examples:
        ["72"]             -> "72"
        ["70", "71", "79"] -> "70-71-79"
    """
    return "-".join(
        sorted(
            area_codes,
            key=int,
        )
    )


def build_area_code_features(
    governorates: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve governorates into Tunisia's eight landline area-code regions."""
    output_rows = []

    for region in AREA_CODE_REGIONS:
        area_codes = sorted(
            region["area_codes"],
            key=int,
        )

        governorate_names = region[
            "governorates"
        ]

        members = governorates[
            governorates[
                "governorate"
            ].isin(
                governorate_names
            )
        ]

        if len(members) != len(
            governorate_names
        ):
            found_names = set(
                members[
                    "governorate"
                ].astype(str)
            )

            missing_names = (
                set(governorate_names)
                - found_names
            )

            raise ValueError(
                "Could not resolve every governorate for "
                f"area codes {area_codes}: "
                f"{sorted(missing_names)}"
            )

        geometry = (
            members.geometry.union_all()
        )

        if (
            geometry is None
            or geometry.is_empty
        ):
            raise ValueError(
                "Area-code dissolve produced empty geometry "
                f"for {area_codes}."
            )

        hover_label = " / ".join(
            governorate_names
        )

        output_rows.append(
            {
                "area_code_id": create_area_code_id(
                    area_codes
                ),
                "area_codes": area_codes,
                "governorates": hover_label,
                "geometry": geometry,
            }
        )

    output = gpd.GeoDataFrame(
        output_rows,
        geometry="geometry",
        crs=governorates.crs,
    )

    if len(output) != EXPECTED_OUTPUT_FEATURE_COUNT:
        raise ValueError(
            "Unexpected area-code feature count: "
            f"expected {EXPECTED_OUTPUT_FEATURE_COUNT}, "
            f"found {len(output)}."
        )

    if output[
        "area_code_id"
    ].duplicated().any():
        raise ValueError(
            "Generated area_code_id values are not unique."
        )

    if output.geometry.isna().any():
        raise ValueError(
            "Generated area-code data contains null geometry."
        )

    if output.geometry.is_empty.any():
        raise ValueError(
            "Generated area-code data contains empty geometry."
        )

    return output


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_compact_geojson(
    frame: gpd.GeoDataFrame,
) -> None:
    """Write the runtime area-code dataset as compact UTF-8 GeoJSON."""
    geojson = json.loads(
        frame.to_json(
            ensure_ascii=False,
            drop_id=True,
        )
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Create Tunisia's runtime geographic landline area-code GeoJSON."""
    print(
        "Processing Tunisia landline area codes..."
    )

    governorates = load_governorates()

    validate_area_code_regions(
        governorates
    )

    output = build_area_code_features(
        governorates
    )

    write_compact_geojson(
        output
    )

    output_size = (
        OUTPUT_PATH.stat().st_size
        / (1024 * 1024)
    )

    print()
    print(
        "Tunisia landline area-code processing complete."
    )
    print(
        f"  Source governorates: {len(governorates)}"
    )
    print(
        f"  Runtime features:    {len(output)}"
    )
    print(
        f"  Quiz answers:        {len(EXPECTED_AREA_CODES)}"
    )
    print(
        f"  Output size:         {output_size:.2f} MB"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()