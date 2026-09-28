"""
Process Ghana's raw geoBoundaries administrative data into GeoPedia's
canonical intermediate administrative GeoJSON.

Inputs
------
data/raw/countries/ghana/geoBoundaries-GHA-ADM1.geojson
data/raw/countries/ghana/geoBoundaries-GHA-ADM2.geojson

Outputs
-------
data/intermediate/countries/ghana/admin/regions.geojson
data/intermediate/countries/ghana/admin/districts.geojson

Ghana's geoBoundaries ADM2 dataset does not contain an explicit parent-region
property. Each district is therefore assigned to its ADM1 region spatially
using an interior representative point.

Canonical properties
--------------------
Regions:
    region_id
    region

Districts:
    district_id
    district
    region_id
    region

ADM1 `shapeISO` values are retained as region IDs. ADM2 has no shapeISO
values, so its geoBoundaries `shapeID` values are retained as district IDs.
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "ghana"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ghana"
    / "admin"
)

REGIONS_INPUT_PATH = (
    RAW_DIR
    / "geoBoundaries-GHA-ADM1.geojson"
)

DISTRICTS_INPUT_PATH = (
    RAW_DIR
    / "geoBoundaries-GHA-ADM2.geojson"
)

REGIONS_OUTPUT_PATH = (
    OUTPUT_DIR
    / "regions.geojson"
)

DISTRICTS_OUTPUT_PATH = (
    OUTPUT_DIR
    / "districts.geojson"
)


EXPECTED_REGION_COUNT = 16
EXPECTED_DISTRICT_COUNT = 260


# ---------------------------------------------------------------------------
# Loading and source validation
# ---------------------------------------------------------------------------


def load_source(
    path: Path,
    expected_count: int,
    expected_type: str,
) -> gpd.GeoDataFrame:
    """Load and validate one raw geoBoundaries administrative dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Source GeoJSON not found: {path}"
        )

    frame = gpd.read_file(
        path
    )

    if len(frame) != expected_count:
        raise ValueError(
            f"Unexpected {expected_type} feature count: "
            f"expected {expected_count}, found {len(frame)}."
        )

    required_columns = {
        "shapeName",
        "shapeISO",
        "shapeID",
        "shapeGroup",
        "shapeType",
        "geometry",
    }

    missing_columns = (
        required_columns
        - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            f"{expected_type} source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if frame.crs is None:
        raise ValueError(
            f"{expected_type} source has no CRS."
        )

    if frame.crs.to_epsg() != 4326:
        raise ValueError(
            f"{expected_type} source has unexpected CRS: "
            f"{frame.crs}"
        )

    if frame["shapeName"].isna().any():
        raise ValueError(
            f"{expected_type} source contains null names."
        )

    if frame["shapeID"].isna().any():
        raise ValueError(
            f"{expected_type} source contains null shape IDs."
        )

    if frame["shapeID"].duplicated().any():
        raise ValueError(
            f"{expected_type} source contains duplicate shape IDs."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            f"{expected_type} source contains null geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            f"{expected_type} source contains empty geometry."
        )

    unexpected_groups = set(
        frame["shapeGroup"].dropna().astype(str)
    ) - {"GHA"}

    if unexpected_groups:
        raise ValueError(
            f"{expected_type} source contains unexpected shapeGroup "
            f"values: {sorted(unexpected_groups)}"
        )

    unexpected_types = set(
        frame["shapeType"].dropna().astype(str)
    ) - {expected_type}

    if unexpected_types:
        raise ValueError(
            f"{expected_type} source contains unexpected shapeType "
            f"values: {sorted(unexpected_types)}"
        )

    return frame


# ---------------------------------------------------------------------------
# Canonical administrative data
# ---------------------------------------------------------------------------


def process_regions(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Convert Ghana ADM1 features into GeoPedia's canonical region schema.

    geoBoundaries provides compact ISO-style ADM1 identifiers such as GH-AA
    and GH-WN, so those are preserved as GeoPedia's stable region IDs.
    """
    if source["shapeISO"].isna().any():
        raise ValueError(
            "Region source contains null shapeISO values."
        )

    region_ids = (
        source["shapeISO"]
        .astype(str)
        .str.strip()
    )

    if (
        region_ids
        == ""
    ).any():
        raise ValueError(
            "Region source contains empty shapeISO values."
        )

    if region_ids.duplicated().any():
        raise ValueError(
            "Region source contains duplicate shapeISO values."
        )

    if source["shapeName"].duplicated().any():
        raise ValueError(
            "Region source contains duplicate names."
        )

    output = gpd.GeoDataFrame(
        {
            "region_id": region_ids,
            "region": source[
                "shapeName"
            ].astype(str),
        },
        geometry=source.geometry.copy(),
        crs=source.crs,
    )

    return output


def assign_district_parents(
    districts: gpd.GeoDataFrame,
    regions: gpd.GeoDataFrame,
) -> list[tuple[str, str]]:
    """
    Resolve each district's parent region using an interior point.

    `representative_point()` guarantees a point inside each district geometry,
    avoiding the potential problem of a polygon centroid falling outside an
    irregularly shaped district.

    Exactly one region must cover each representative point. Ambiguous or
    unresolved relationships are rejected rather than silently guessed.
    """
    parent_data: list[
        tuple[str, str]
    ] = []

    for index, district in districts.iterrows():
        district_name = str(
            district["shapeName"]
        )

        point = (
            district.geometry
            .representative_point()
        )

        matches = regions[
            regions.geometry.covers(
                point
            )
        ]

        if len(matches) != 1:
            matching_regions = (
                matches["region"]
                .astype(str)
                .tolist()
            )

            raise ValueError(
                "Could not uniquely resolve parent region for "
                f"district {district_name!r} at source index {index}. "
                f"Matched {len(matches)} regions: "
                f"{matching_regions}"
            )

        parent = matches.iloc[0]

        parent_data.append(
            (
                str(
                    parent["region_id"]
                ),
                str(
                    parent["region"]
                ),
            )
        )

    return parent_data


def process_districts(
    source: gpd.GeoDataFrame,
    regions: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Convert Ghana ADM2 features into GeoPedia's canonical district schema.

    geoBoundaries does not provide ADM2 ISO codes or parent-region metadata.
    Its stable `shapeID` therefore becomes GeoPedia's district ID, while the
    parent region is derived spatially from the processed ADM1 geometry.
    """
    if source["shapeName"].duplicated().any():
        raise ValueError(
            "District source contains duplicate names."
        )

    district_ids = (
        source["shapeID"]
        .astype(str)
        .str.strip()
    )

    if (
        district_ids
        == ""
    ).any():
        raise ValueError(
            "District source contains empty shapeID values."
        )

    if district_ids.duplicated().any():
        raise ValueError(
            "District source contains duplicate shapeID values."
        )

    parent_data = (
        assign_district_parents(
            source,
            regions,
        )
    )

    region_ids = [
        region_id
        for region_id, _ in parent_data
    ]

    region_names = [
        region_name
        for _, region_name in parent_data
    ]

    output = gpd.GeoDataFrame(
        {
            "district_id": district_ids,
            "district": source[
                "shapeName"
            ].astype(str),
            "region_id": region_ids,
            "region": region_names,
        },
        geometry=source.geometry.copy(),
        crs=source.crs,
    )

    return output


# ---------------------------------------------------------------------------
# Final validation
# ---------------------------------------------------------------------------


def validate_output(
    regions: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
) -> None:
    """Validate the completed Ghana administrative hierarchy."""
    if len(regions) != EXPECTED_REGION_COUNT:
        raise ValueError(
            "Processed region count changed unexpectedly: "
            f"{len(regions)}"
        )

    if len(districts) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Processed district count changed unexpectedly: "
            f"{len(districts)}"
        )

    if regions["region_id"].duplicated().any():
        raise ValueError(
            "Processed regions contain duplicate IDs."
        )

    if districts["district_id"].duplicated().any():
        raise ValueError(
            "Processed districts contain duplicate IDs."
        )

    if regions["region"].duplicated().any():
        raise ValueError(
            "Processed regions contain duplicate names."
        )

    if districts["district"].duplicated().any():
        raise ValueError(
            "Processed districts contain duplicate names."
        )

    valid_region_ids = set(
        regions["region_id"].astype(str)
    )

    district_region_ids = set(
        districts["region_id"].astype(str)
    )

    unknown_parent_ids = (
        district_region_ids
        - valid_region_ids
    )

    if unknown_parent_ids:
        raise ValueError(
            "Districts reference unknown region IDs: "
            f"{sorted(unknown_parent_ids)}"
        )

    if districts["region_id"].isna().any():
        raise ValueError(
            "Processed districts contain missing parent regions."
        )

    if regions.geometry.isna().any():
        raise ValueError(
            "Processed regions contain null geometry."
        )

    if districts.geometry.isna().any():
        raise ValueError(
            "Processed districts contain null geometry."
        )

    if regions.geometry.is_empty.any():
        raise ValueError(
            "Processed regions contain empty geometry."
        )

    if districts.geometry.is_empty.any():
        raise ValueError(
            "Processed districts contain empty geometry."
        )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_compact_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """Write canonical intermediate GeoJSON as compact UTF-8 JSON."""
    geojson = json.loads(
        frame.to_json(
            ensure_ascii=False,
            drop_id=True,
        )
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
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
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Process Ghana's ADM1 and ADM2 geoBoundaries datasets."""
    print(
        "Processing Ghana administrative boundaries..."
    )

    raw_regions = load_source(
        REGIONS_INPUT_PATH,
        EXPECTED_REGION_COUNT,
        "ADM1",
    )

    raw_districts = load_source(
        DISTRICTS_INPUT_PATH,
        EXPECTED_DISTRICT_COUNT,
        "ADM2",
    )

    regions = process_regions(
        raw_regions
    )

    districts = process_districts(
        raw_districts,
        regions,
    )

    validate_output(
        regions,
        districts,
    )

    write_compact_geojson(
        regions,
        REGIONS_OUTPUT_PATH,
    )

    write_compact_geojson(
        districts,
        DISTRICTS_OUTPUT_PATH,
    )

    print()
    print(
        "Ghana administrative processing complete."
    )
    print(
        f"  Regions:   {len(regions)}"
    )
    print(
        f"  Districts: {len(districts)}"
    )
    print()
    print(
        f"Regions:   {REGIONS_OUTPUT_PATH}"
    )
    print(
        f"Districts: {DISTRICTS_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()