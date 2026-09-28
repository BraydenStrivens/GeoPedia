"""Process Costa Rica province boundaries for GeoPedia.

This script converts the raw Costa Rica ADM1 administrative-boundary
dataset into the compact runtime GeoJSON used by GeoPedia.

Processing:
- Validates the expected seven Costa Rica provinces.
- Converts source pcodes such as CR1 into province IDs such as 1.
- Keeps only the runtime properties needed by GeoPedia.
- Simplifies geometry in a projected CRS.
- Preserves topology during simplification.
- Converts the result back to EPSG:4326.
- Validates the processed dataset.
- Writes compact GeoJSON.

Input:
    data/raw/countries/costa-rica/cri_admin_boundaries.geojson/
        cri_admin1.geojson

Output:
    public/data/countries/costa-rica/geojson/provinces.geojson

Runtime properties:
    province_id
    name
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "costa-rica"
    / "cri_admin_boundaries.geojson"
    / "cri_admin1.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "costa-rica"
    / "geojson"
    / "provinces.geojson"
)

EXPECTED_PROVINCES = {
    "1": "San José",
    "2": "Alajuela",
    "3": "Cartago",
    "4": "Heredia",
    "5": "Guanacaste",
    "6": "Puntarenas",
    "7": "Limón",
}

EXPECTED_SOURCE_COLUMNS = {
    "adm1_name",
    "adm1_pcode",
    "geometry",
}

EXPECTED_CRS = "EPSG:4326"

# Costa Rica falls within UTM zone 16N.
PROJECTED_CRS = "EPSG:32616"

SIMPLIFY_TOLERANCE_METERS = 25


def count_coordinates(geometry) -> int:
    """Count coordinate pairs in a Polygon or MultiPolygon geometry."""
    if geometry is None or geometry.is_empty:
        return 0

    if geometry.geom_type == "Polygon":
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if geometry.geom_type == "MultiPolygon":
        return sum(
            count_coordinates(polygon)
            for polygon in geometry.geoms
        )

    if hasattr(geometry, "geoms"):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    return 0


def format_bytes(byte_count: int) -> str:
    """Format a byte count using convenient binary units."""
    if byte_count < 1024:
        return f"{byte_count:,} bytes"

    if byte_count < 1024**2:
        return (
            f"{byte_count / 1024:.2f} KB "
            f"({byte_count:,} bytes)"
        )

    return (
        f"{byte_count / 1024**2:.2f} MB "
        f"({byte_count:,} bytes)"
    )


def validate_source(frame: gpd.GeoDataFrame) -> None:
    """Validate the raw ADM1 source before processing."""
    if frame.empty:
        raise ValueError(
            "Costa Rica ADM1 source dataset is empty."
        )

    if frame.crs is None:
        raise ValueError(
            "Costa Rica ADM1 source dataset has no CRS."
        )

    if frame.crs.to_string() != EXPECTED_CRS:
        raise ValueError(
            "Unexpected Costa Rica ADM1 CRS: "
            f"{frame.crs}. Expected {EXPECTED_CRS}."
        )

    missing_columns = (
        EXPECTED_SOURCE_COLUMNS - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "Costa Rica ADM1 source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if len(frame) != len(EXPECTED_PROVINCES):
        raise ValueError(
            "Unexpected Costa Rica ADM1 feature count: "
            f"{len(frame)}. "
            f"Expected {len(EXPECTED_PROVINCES)}."
        )

    if frame["adm1_name"].isna().any():
        raise ValueError(
            "Costa Rica ADM1 contains a blank province name."
        )

    if frame["adm1_pcode"].isna().any():
        raise ValueError(
            "Costa Rica ADM1 contains a blank province pcode."
        )

    if frame["adm1_name"].duplicated().any():
        raise ValueError(
            "Costa Rica ADM1 contains duplicate province names."
        )

    if frame["adm1_pcode"].duplicated().any():
        raise ValueError(
            "Costa Rica ADM1 contains duplicate province pcodes."
        )

    invalid_geometry = (
        frame.geometry.isna()
        | frame.geometry.is_empty
        | ~frame.geometry.is_valid
    )

    if invalid_geometry.any():
        raise ValueError(
            "Costa Rica ADM1 contains invalid, empty, "
            "or null geometry."
        )


def build_runtime_frame(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Create normalized GeoPedia province records."""
    frame = source[
        [
            "adm1_pcode",
            "adm1_name",
            "geometry",
        ]
    ].copy()

    frame["province_id"] = (
        frame["adm1_pcode"]
        .astype(str)
        .str.removeprefix("CR")
    )

    frame["name"] = (
        frame["adm1_name"]
        .astype(str)
        .str.strip()
    )

    frame = frame[
        [
            "province_id",
            "name",
            "geometry",
        ]
    ]

    return frame


def validate_normalized_data(
    frame: gpd.GeoDataFrame,
) -> None:
    """Validate normalized province IDs and names."""
    actual = dict(
        zip(
            frame["province_id"],
            frame["name"],
        )
    )

    if actual != EXPECTED_PROVINCES:
        raise ValueError(
            "Costa Rica province IDs/names do not match "
            "the expected administrative hierarchy.\n"
            f"Expected: {EXPECTED_PROVINCES}\n"
            f"Actual:   {actual}"
        )

    for province_id in frame["province_id"]:
        if (
            len(province_id) != 1
            or not province_id.isdigit()
        ):
            raise ValueError(
                "Invalid Costa Rica province ID: "
                f"{province_id!r}"
            )


def simplify_geometry(
    frame: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Simplify province geometry using a meter-based tolerance."""
    projected = frame.to_crs(
        PROJECTED_CRS
    )

    projected["geometry"] = (
        projected.geometry.simplify(
            tolerance=SIMPLIFY_TOLERANCE_METERS,
            preserve_topology=True,
        )
    )

    return projected.to_crs(
        EXPECTED_CRS
    )


def validate_processed(
    frame: gpd.GeoDataFrame,
) -> None:
    """Validate the final processed runtime dataset."""
    if len(frame) != len(EXPECTED_PROVINCES):
        raise ValueError(
            "Processed province count changed unexpectedly."
        )

    if frame["province_id"].duplicated().any():
        raise ValueError(
            "Processed provinces contain duplicate IDs."
        )

    invalid_geometry = (
        frame.geometry.isna()
        | frame.geometry.is_empty
        | ~frame.geometry.is_valid
    )

    if invalid_geometry.any():
        raise ValueError(
            "Processed provinces contain invalid, empty, "
            "or null geometry."
        )

    geometry_types = set(
        frame.geometry.geom_type
    )

    unexpected_types = (
        geometry_types
        - {
            "Polygon",
            "MultiPolygon",
        }
    )

    if unexpected_types:
        raise ValueError(
            "Processed provinces contain unexpected "
            f"geometry types: {sorted(unexpected_types)}"
        )


def write_compact_geojson(
    frame: gpd.GeoDataFrame,
) -> int:
    """Write the runtime dataset as compact UTF-8 GeoJSON."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        frame.to_json(
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

    return len(
        content.encode("utf-8")
    )


def main() -> None:
    """Process Costa Rica ADM1 boundaries into runtime provinces."""
    print("Reading:")
    print(SOURCE_PATH)
    print()

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"Source file does not exist: {SOURCE_PATH}"
        )

    source = gpd.read_file(
        SOURCE_PATH
    )

    validate_source(
        source
    )

    source_coordinate_count = int(
        source.geometry.apply(
            count_coordinates
        ).sum()
    )

    print(
        f"Source features: {len(source)}"
    )
    print(
        f"Source coordinates: {source_coordinate_count:,}"
    )
    print()

    frame = build_runtime_frame(
        source
    )

    validate_normalized_data(
        frame
    )

    print("Normalized provinces:")

    for _, row in frame.sort_values(
        "province_id"
    ).iterrows():
        print(
            f"  {row['province_id']} | {row['name']}"
        )

    print()
    print(
        "Simplifying geometry with "
        f"{SIMPLIFY_TOLERANCE_METERS} m tolerance..."
    )

    frame = simplify_geometry(
        frame
    )

    validate_processed(
        frame
    )

    processed_coordinate_count = int(
        frame.geometry.apply(
            count_coordinates
        ).sum()
    )

    reduction = (
        1
        - processed_coordinate_count
        / source_coordinate_count
    ) * 100

    output_size = write_compact_geojson(
        frame
    )

    print()
    print(
        f"Processed coordinates: "
        f"{processed_coordinate_count:,}"
    )
    print(
        f"Coordinate reduction: {reduction:.2f}%"
    )
    print(
        f"Output size: {format_bytes(output_size)}"
    )
    print()
    print("Wrote:")
    print(OUTPUT_PATH)
    print()
    print(
        "Costa Rica province processing and validation passed."
    )


if __name__ == "__main__":
    main()