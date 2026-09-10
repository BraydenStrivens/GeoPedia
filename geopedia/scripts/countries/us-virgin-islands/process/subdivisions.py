"""Process U.S. Virgin Islands subdivisions for GeoPedia.

This processor converts the GeoBoundaries VIR ADM3 dataset into GeoPedia's
runtime subdivision dataset.

GeoBoundaries does not provide the parent island for each feature, so each
subdivision is assigned to St. Croix, St. John, or St. Thomas by finding
the GeoPedia island polygon with the greatest projected-area overlap.

The GeoBoundaries shapeID is retained as the stable subdivision ID.

Inputs:
    data/raw/countries/us-virgin-islands/
        geoBoundaries-VIR-ADM3-all/
            geoBoundaries-VIR-ADM3.geojson

    public/data/countries/us-virgin-islands/geojson/islands.geojson

Output:
    public/data/countries/us-virgin-islands/geojson/subdivisions.geojson

Runtime properties:
    subdivision_id
    name
    island_id

The source geometry is small and already suitable for runtime use, so no
geometry simplification is performed.
"""

import json
from collections import Counter
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "us-virgin-islands"
    / "geoBoundaries-VIR-ADM3-all"
    / "geoBoundaries-VIR-ADM3.geojson"
)

ISLANDS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "us-virgin-islands"
    / "geojson"
    / "islands.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "us-virgin-islands"
    / "geojson"
    / "subdivisions.geojson"
)

AREA_CRS = "EPSG:32620"

EXPECTED_SUBDIVISION_COUNT = 20

EXPECTED_COUNTS_BY_ISLAND = {
    "78010": 9,
    "78020": 4,
    "78030": 7,
}

EXPECTED_ISLAND_NAMES = {
    "78010": "St. Croix",
    "78020": "St. John",
    "78030": "St. Thomas",
}


def load_subdivisions() -> gpd.GeoDataFrame:
    """Load and validate the raw GeoBoundaries subdivision dataset."""
    print("Reading GeoBoundaries subdivisions from:")
    print(INPUT_PATH)
    print()

    subdivisions = gpd.read_file(
        INPUT_PATH
    )

    if subdivisions.empty:
        raise ValueError(
            "GeoBoundaries subdivision dataset is empty."
        )

    if subdivisions.crs is None:
        raise ValueError(
            "GeoBoundaries subdivision dataset has no CRS."
        )

    required_columns = {
        "shapeName",
        "shapeID",
        "geometry",
    }

    missing_columns = (
        required_columns - set(subdivisions.columns)
    )

    if missing_columns:
        raise ValueError(
            "GeoBoundaries subdivision dataset is missing required "
            f"columns: {sorted(missing_columns)}"
        )

    if len(subdivisions) != EXPECTED_SUBDIVISION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SUBDIVISION_COUNT} subdivisions, "
            f"found {len(subdivisions)}."
        )

    subdivisions["shapeName"] = (
        subdivisions["shapeName"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    subdivisions["shapeID"] = (
        subdivisions["shapeID"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if (subdivisions["shapeName"] == "").any():
        raise ValueError(
            "One or more subdivisions have a blank name."
        )

    if (subdivisions["shapeID"] == "").any():
        raise ValueError(
            "One or more subdivisions have a blank shapeID."
        )

    if subdivisions["shapeID"].duplicated().any():
        raise ValueError(
            "Duplicate GeoBoundaries shapeIDs found."
        )

    invalid_geometries = subdivisions[
        subdivisions.geometry.isna()
        | subdivisions.geometry.is_empty
        | ~subdivisions.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        raise ValueError(
            "Invalid subdivision geometry found for: "
            f"{invalid_geometries['shapeName'].tolist()}"
        )

    return subdivisions


def load_islands() -> gpd.GeoDataFrame:
    """Load GeoPedia's processed U.S. Virgin Islands island polygons."""
    if not ISLANDS_PATH.exists():
        raise FileNotFoundError(
            "Processed USVI islands file does not exist. "
            "Run process/islands.py first.\n"
            f"Expected: {ISLANDS_PATH}"
        )

    islands = gpd.read_file(
        ISLANDS_PATH
    )

    required_columns = {
        "island_id",
        "name",
        "geometry",
    }

    missing_columns = (
        required_columns - set(islands.columns)
    )

    if missing_columns:
        raise ValueError(
            "Processed island dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    islands["island_id"] = (
        islands["island_id"]
        .astype(str)
        .str.strip()
    )

    actual_islands = dict(
        zip(
            islands["island_id"],
            islands["name"],
        )
    )

    if actual_islands != EXPECTED_ISLAND_NAMES:
        raise ValueError(
            "Processed island records do not match expected islands.\n"
            f"Expected: {EXPECTED_ISLAND_NAMES}\n"
            f"Found: {actual_islands}"
        )

    return islands


def assign_parent_islands(
    subdivisions: gpd.GeoDataFrame,
    islands: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Assign each subdivision to the island with greatest area overlap."""
    subdivisions_projected = subdivisions.to_crs(
        AREA_CRS
    )

    islands_projected = islands.to_crs(
        AREA_CRS
    )

    island_ids: list[str] = []
    overlap_ratios: list[float] = []

    for index, subdivision in subdivisions_projected.iterrows():
        geometry = subdivision.geometry
        total_area = geometry.area

        if total_area <= 0:
            raise ValueError(
                f"Subdivision at index {index} has zero area."
            )

        best_island_id: str | None = None
        best_overlap_area = -1.0

        for _, island in islands_projected.iterrows():
            overlap_area = geometry.intersection(
                island.geometry
            ).area

            if overlap_area > best_overlap_area:
                best_overlap_area = overlap_area
                best_island_id = island["island_id"]

        if best_island_id is None:
            raise ValueError(
                "Could not assign parent island to subdivision "
                f"{subdivision['shapeName']}."
            )

        island_ids.append(
            str(best_island_id)
        )

        overlap_ratios.append(
            best_overlap_area / total_area
        )

    result = subdivisions.copy()

    result["island_id"] = island_ids
    result["_overlap_ratio"] = overlap_ratios

    return result


def normalize_subdivisions(
    subdivisions: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Normalize subdivision properties for GeoPedia runtime use."""
    subdivisions = subdivisions.rename(
        columns={
            "shapeID": "subdivision_id",
            "shapeName": "name",
        }
    )

    subdivisions = subdivisions[
        [
            "subdivision_id",
            "name",
            "island_id",
            "_overlap_ratio",
            "geometry",
        ]
    ].copy()

    subdivisions = subdivisions.sort_values(
        [
            "island_id",
            "name",
            "subdivision_id",
        ]
    ).reset_index(
        drop=True
    )

    return subdivisions


def validate_subdivisions(
    subdivisions: gpd.GeoDataFrame,
) -> None:
    """Validate processed subdivision records and parent assignments."""
    if len(subdivisions) != EXPECTED_SUBDIVISION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SUBDIVISION_COUNT} subdivisions, "
            f"found {len(subdivisions)}."
        )

    if subdivisions["subdivision_id"].duplicated().any():
        raise ValueError(
            "Duplicate subdivision IDs found."
        )

    actual_island_ids = set(
        subdivisions["island_id"]
    )

    if actual_island_ids != set(EXPECTED_COUNTS_BY_ISLAND):
        raise ValueError(
            "Unexpected parent island IDs. "
            f"Found: {sorted(actual_island_ids)}"
        )

    actual_counts = Counter(
        subdivisions["island_id"]
    )

    if dict(actual_counts) != EXPECTED_COUNTS_BY_ISLAND:
        raise ValueError(
            "Subdivision counts by island do not match expectations.\n"
            f"Expected: {EXPECTED_COUNTS_BY_ISLAND}\n"
            f"Found: {dict(actual_counts)}"
        )

    weak_assignments = subdivisions[
        subdivisions["_overlap_ratio"] < 0.50
    ]

    if len(weak_assignments) > 0:
        details = [
            (
                row["name"],
                row["island_id"],
                row["_overlap_ratio"],
            )
            for _, row in weak_assignments.iterrows()
        ]

        raise ValueError(
            "One or more subdivision parent assignments have less "
            f"than 50% overlap: {details}"
        )

    invalid_geometries = subdivisions[
        subdivisions.geometry.isna()
        | subdivisions.geometry.is_empty
        | ~subdivisions.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        raise ValueError(
            "Invalid processed subdivision geometry found."
        )

    invalid_geometry_types = subdivisions[
        ~subdivisions.geometry.geom_type.isin(
            ["Polygon", "MultiPolygon"]
        )
    ]

    if len(invalid_geometry_types) > 0:
        raise ValueError(
            "Unexpected subdivision geometry types found."
        )

    if subdivisions.crs is None:
        raise ValueError(
            "Processed subdivisions have no CRS."
        )


def write_geojson(
    subdivisions: gpd.GeoDataFrame,
) -> int:
    """Write compact UTF-8 runtime GeoJSON and return its byte size."""
    runtime = subdivisions[
        [
            "subdivision_id",
            "name",
            "island_id",
            "geometry",
        ]
    ].copy()

    if str(runtime.crs).upper() != "EPSG:4326":
        runtime = runtime.to_crs(
            "EPSG:4326"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        runtime.to_json(
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
    """Process U.S. Virgin Islands subdivisions."""
    subdivisions = load_subdivisions()
    islands = load_islands()

    subdivisions = assign_parent_islands(
        subdivisions,
        islands,
    )

    subdivisions = normalize_subdivisions(
        subdivisions
    )

    validate_subdivisions(
        subdivisions
    )

    output_size = write_geojson(
        subdivisions
    )

    print("U.S. Virgin Islands subdivisions processed successfully.")
    print(
        f"Features written: {len(subdivisions)}"
    )
    print()

    for island_id, island_name in EXPECTED_ISLAND_NAMES.items():
        island_rows = subdivisions[
            subdivisions["island_id"] == island_id
        ]

        print(
            f"{island_name} ({island_id}): "
            f"{len(island_rows)}"
        )

        for _, row in island_rows.iterrows():
            print(
                f"  {row['name']} | "
                f"{row['subdivision_id']} | "
                f"{row['_overlap_ratio']:.2%}"
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