"""
Create Ghana's runtime geographic fixed-line area-code GeoJSON.

Input
-----
public/data/countries/ghana/geojson/regions.geojson

Output
------
public/data/countries/ghana/geojson/area-codes.geojson

Ghana's current administrative regions are dissolved into the geographic
areas represented by the fixed-line numbering plan. Several current regions
were created by subdividing older regions and therefore share the fixed-line
area code of their historical parent region.

The already-simplified region geometry is reused directly, so this derived
dataset does not require another simplification pass.

Only properties required by the runtime map and quiz are retained:

    area_code
    regions

The `regions` property provides the map's hover label by listing the current
administrative regions represented by each area-code feature.
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
    / "ghana"
    / "geojson"
    / "regions.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "ghana"
    / "geojson"
    / "area-codes.geojson"
)


EXPECTED_REGION_COUNT = 16
EXPECTED_OUTPUT_FEATURE_COUNT = 10

EXPECTED_AREA_CODES = {
    "030",
    "031",
    "032",
    "033",
    "034",
    "035",
    "036",
    "037",
    "038",
    "039",
}


# ---------------------------------------------------------------------------
# Geographic area-code definitions
# ---------------------------------------------------------------------------

# Current administrative regions are grouped according to the geographic
# fixed-line numbering areas represented by Ghana's 030-039 codes.
AREA_CODE_REGIONS = [
    {
        "area_code": "030",
        "regions": [
            "Greater Accra Region",
        ],
    },
    {
        "area_code": "031",
        "regions": [
            "Western Region",
            "Western North Region",
        ],
    },
    {
        "area_code": "032",
        "regions": [
            "Ashanti Region",
        ],
    },
    {
        "area_code": "033",
        "regions": [
            "Central Region",
        ],
    },
    {
        "area_code": "034",
        "regions": [
            "Eastern Region",
        ],
    },
    {
        "area_code": "035",
        "regions": [
            "Ahafo Region",
            "Bono Region",
            "Bono East Region",
        ],
    },
    {
        "area_code": "036",
        "regions": [
            "Volta Region",
            "Oti Region",
        ],
    },
    {
        "area_code": "037",
        "regions": [
            "Northern Region",
            "North East Region",
            "Savannah Region",
        ],
    },
    {
        "area_code": "038",
        "regions": [
            "Upper East Region",
        ],
    },
    {
        "area_code": "039",
        "regions": [
            "Upper West Region",
        ],
    },
]


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------


def load_regions() -> gpd.GeoDataFrame:
    """Load and validate Ghana's simplified runtime region geometry."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Region GeoJSON not found: {INPUT_PATH}"
        )

    frame = gpd.read_file(
        INPUT_PATH
    )

    if len(frame) != EXPECTED_REGION_COUNT:
        raise ValueError(
            "Unexpected region count: "
            f"expected {EXPECTED_REGION_COUNT}, "
            f"found {len(frame)}."
        )

    required_properties = {
        "region_id",
        "region",
    }

    missing_properties = (
        required_properties
        - set(frame.columns)
    )

    if missing_properties:
        raise ValueError(
            "Region GeoJSON is missing required properties: "
            f"{sorted(missing_properties)}"
        )

    if frame["region_id"].isna().any():
        raise ValueError(
            "Region GeoJSON contains a null region_id."
        )

    if frame["region_id"].duplicated().any():
        raise ValueError(
            "Region GeoJSON contains duplicate region IDs."
        )

    if frame["region"].isna().any():
        raise ValueError(
            "Region GeoJSON contains a null region name."
        )

    if frame["region"].duplicated().any():
        raise ValueError(
            "Region GeoJSON contains duplicate region names."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            "Region GeoJSON contains null geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            "Region GeoJSON contains empty geometry."
        )

    return frame


def validate_area_code_regions(
    regions: gpd.GeoDataFrame,
) -> None:
    """
    Validate Ghana's configured geographic fixed-line numbering regions.

    Every current administrative region must occur exactly once, and every
    expected 030-039 area code must occur exactly once.
    """
    source_regions = set(
        regions["region"].astype(str)
    )

    configured_regions: list[str] = []
    configured_area_codes: list[str] = []

    for definition in AREA_CODE_REGIONS:
        area_code = definition[
            "area_code"
        ]

        region_names = definition[
            "regions"
        ]

        if (
            not isinstance(area_code, str)
            or len(area_code) != 3
            or not area_code.isdigit()
        ):
            raise ValueError(
                f"Invalid area code: {area_code!r}"
            )

        if not region_names:
            raise ValueError(
                f"Area code {area_code} has no regions."
            )

        configured_area_codes.append(
            area_code
        )

        configured_regions.extend(
            region_names
        )

    duplicate_regions = {
        region
        for region in configured_regions
        if configured_regions.count(region) > 1
    }

    if duplicate_regions:
        raise ValueError(
            "Regions assigned to multiple area codes: "
            f"{sorted(duplicate_regions)}"
        )

    configured_region_set = set(
        configured_regions
    )

    missing_regions = (
        source_regions
        - configured_region_set
    )

    unknown_regions = (
        configured_region_set
        - source_regions
    )

    if missing_regions:
        raise ValueError(
            "Regions without area-code assignments: "
            f"{sorted(missing_regions)}"
        )

    if unknown_regions:
        raise ValueError(
            "Area-code definitions reference unknown regions: "
            f"{sorted(unknown_regions)}"
        )

    if len(configured_area_codes) != len(
        set(configured_area_codes)
    ):
        raise ValueError(
            "Area-code definitions contain duplicate area codes."
        )

    represented_area_codes = set(
        configured_area_codes
    )

    if represented_area_codes != EXPECTED_AREA_CODES:
        raise ValueError(
            "Area-code set does not match expected 030-039 codes. "
            f"Found: {sorted(represented_area_codes)}"
        )


# ---------------------------------------------------------------------------
# Feature construction
# ---------------------------------------------------------------------------


def build_area_code_features(
    regions: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve Ghana's 16 current regions into 10 fixed-line areas."""
    output_rows = []

    for definition in AREA_CODE_REGIONS:
        area_code = definition[
            "area_code"
        ]

        region_names = definition[
            "regions"
        ]

        members = regions[
            regions["region"].isin(
                region_names
            )
        ]

        if len(members) != len(
            region_names
        ):
            found_names = set(
                members["region"].astype(str)
            )

            missing_names = (
                set(region_names)
                - found_names
            )

            raise ValueError(
                "Could not resolve every region for "
                f"area code {area_code}: "
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
                f"for {area_code}."
            )

        hover_label = " / ".join(
            region_names
        )

        output_rows.append(
            {
                "area_code": area_code,
                "regions": hover_label,
                "geometry": geometry,
            }
        )

    output = gpd.GeoDataFrame(
        output_rows,
        geometry="geometry",
        crs=regions.crs,
    )

    if len(output) != EXPECTED_OUTPUT_FEATURE_COUNT:
        raise ValueError(
            "Unexpected area-code feature count: "
            f"expected {EXPECTED_OUTPUT_FEATURE_COUNT}, "
            f"found {len(output)}."
        )

    if output["area_code"].duplicated().any():
        raise ValueError(
            "Generated area codes are not unique."
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
    """Write Ghana's runtime area-code dataset as compact UTF-8 GeoJSON."""
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


def main() -> None:
    """Create Ghana's runtime geographic fixed-line area-code GeoJSON."""
    print(
        "Processing Ghana fixed-line area codes..."
    )

    regions = load_regions()

    validate_area_code_regions(
        regions
    )

    output = build_area_code_features(
        regions
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
        "Ghana fixed-line area-code processing complete."
    )
    print(
        f"  Source regions:   {len(regions)}"
    )
    print(
        f"  Runtime features: {len(output)}"
    )
    print(
        f"  Quiz answers:     {len(EXPECTED_AREA_CODES)}"
    )
    print(
        f"  Output size:      {output_size:.2f} MB"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()