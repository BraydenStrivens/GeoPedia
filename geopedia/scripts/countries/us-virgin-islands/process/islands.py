"""Process U.S. Virgin Islands island geography for GeoPedia.

This processor extracts the three U.S. Virgin Islands county-equivalent
features from GeoPedia's processed U.S. counties dataset.

The Census county-equivalent GEOID is retained as the stable island ID.

Input:
    public/data/countries/usa/geojson/counties.geojson

Output:
    public/data/countries/us-virgin-islands/geojson/islands.geojson

Runtime properties:
    island_id
    name

The source is already a processed GeoPedia runtime dataset, so its geometry
is preserved without additional simplification.
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
    / "usa"
    / "geojson"
    / "counties.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "us-virgin-islands"
    / "geojson"
    / "islands.geojson"
)

EXPECTED_ISLANDS = {
    "78010": "St. Croix",
    "78020": "St. John",
    "78030": "St. Thomas",
}


def load_islands() -> gpd.GeoDataFrame:
    """Load the three USVI county-equivalent features."""
    print("Reading U.S. counties from:")
    print(INPUT_PATH)
    print()

    counties = gpd.read_file(INPUT_PATH)

    if counties.empty:
        raise ValueError("GeoPedia U.S. counties dataset is empty.")

    if counties.crs is None:
        raise ValueError("GeoPedia U.S. counties dataset has no CRS.")

    required_columns = {
        "geoid",
        "name",
        "state",
        "geometry",
    }

    missing_columns = required_columns - set(counties.columns)

    if missing_columns:
        raise ValueError(
            "U.S. counties dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    islands = counties[
        counties["state"] == "VI"
    ].copy()

    if len(islands) != len(EXPECTED_ISLANDS):
        raise ValueError(
            f"Expected {len(EXPECTED_ISLANDS)} USVI islands, "
            f"found {len(islands)}."
        )

    islands["geoid"] = (
        islands["geoid"]
        .astype(str)
        .str.strip()
    )

    islands["name"] = (
        islands["name"]
        .astype(str)
        .str.strip()
    )

    return islands


def normalize_islands(
    islands: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Normalize island properties for GeoPedia runtime use."""
    actual_islands = dict(
        zip(
            islands["geoid"],
            islands["name"],
        )
    )

    if actual_islands != EXPECTED_ISLANDS:
        raise ValueError(
            "USVI island records do not match the expected GEOIDs "
            "and names.\n"
            f"Expected: {EXPECTED_ISLANDS}\n"
            f"Found: {actual_islands}"
        )

    islands = islands[
        [
            "geoid",
            "name",
            "geometry",
        ]
    ].copy()

    islands = islands.rename(
        columns={
            "geoid": "island_id",
        }
    )

    islands = islands.sort_values(
        "island_id"
    ).reset_index(
        drop=True
    )

    return islands


def validate_islands(
    islands: gpd.GeoDataFrame,
) -> None:
    """Validate processed island records and geometry."""
    if len(islands) != len(EXPECTED_ISLANDS):
        raise ValueError(
            f"Expected {len(EXPECTED_ISLANDS)} islands, "
            f"found {len(islands)}."
        )

    if islands["island_id"].duplicated().any():
        raise ValueError("Duplicate island IDs found.")

    if islands["name"].duplicated().any():
        raise ValueError("Duplicate island names found.")

    invalid_geometries = islands[
        islands.geometry.isna()
        | islands.geometry.is_empty
        | ~islands.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        raise ValueError(
            "Invalid island geometry found for: "
            f"{invalid_geometries['name'].tolist()}"
        )

    invalid_geometry_types = islands[
        ~islands.geometry.geom_type.isin(
            ["Polygon", "MultiPolygon"]
        )
    ]

    if len(invalid_geometry_types) > 0:
        raise ValueError(
            "Unexpected island geometry types found."
        )

    if islands.crs is None:
        raise ValueError("Processed islands have no CRS.")

    if str(islands.crs).upper() != "EPSG:4326":
        islands.to_crs(
            "EPSG:4326",
            inplace=True,
        )


def write_geojson(
    islands: gpd.GeoDataFrame,
) -> int:
    """Write compact UTF-8 runtime GeoJSON and return its byte size."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        islands.to_json(
            drop_id=True,
        )
    )

    content = json.dumps(
        geojson,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )

    return len(content.encode("utf-8"))


def main() -> None:
    """Process U.S. Virgin Islands island geography."""
    islands = load_islands()

    islands = normalize_islands(
        islands
    )

    validate_islands(
        islands
    )

    output_size = write_geojson(
        islands
    )

    print("U.S. Virgin Islands processed successfully.")
    print(f"Features written: {len(islands)}")
    print()

    for _, row in islands.iterrows():
        print(
            f"  {row['island_id']}: "
            f"{row['name']}"
        )

    print()
    print("Geometry simplification: none")
    print(
        f"Output size: {output_size / 1024:.2f} KB "
        f"({output_size:,} bytes)"
    )
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


if __name__ == "__main__":
    main()