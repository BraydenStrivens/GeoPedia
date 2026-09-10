"""Process Costa Rica canton boundaries for GeoPedia.

This script converts the raw Costa Rica ADM2 administrative-boundary
dataset into the compact runtime GeoJSON used by GeoPedia.

Processing:
- Validates the expected 84 Costa Rica cantons.
- Converts source pcodes such as CR201 into canton IDs such as 201.
- Converts parent pcodes such as CR2 into province IDs such as 2.
- Validates the canton/province code hierarchy.
- Keeps only the runtime properties needed by GeoPedia.
- Simplifies geometry in a projected CRS.
- Preserves topology during simplification.
- Converts the result back to EPSG:4326.
- Validates the processed dataset.
- Writes compact GeoJSON.

Input:
    data/raw/countries/costa-rica/cri_admin_boundaries.geojson/
        cri_admin2.geojson

Output:
    public/data/countries/costa-rica/geojson/cantons.geojson

Runtime properties:
    canton_id
    name
    province_id
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
    / "cri_admin2.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "costa-rica"
    / "geojson"
    / "cantons.geojson"
)

EXPECTED_CANTON_COUNT = 84

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
    "adm2_name",
    "adm2_pcode",
    "adm1_name",
    "adm1_pcode",
    "geometry",
}

EXPECTED_CRS = "EPSG:4326"

# Costa Rica falls primarily within UTM zone 16N.
PROJECTED_CRS = "EPSG:32616"

SIMPLIFY_TOLERANCE_METERS = 10


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


def strip_cr_prefix(value: str) -> str:
    """Remove the CR prefix from a Costa Rica administrative pcode."""
    value = str(value).strip()

    if not value.startswith("CR"):
        raise ValueError(
            f"Unexpected Costa Rica pcode: {value!r}"
        )

    return value[2:]


def validate_source(frame: gpd.GeoDataFrame) -> None:
    """Validate the raw ADM2 source before processing."""
    if frame.empty:
        raise ValueError(
            "Costa Rica ADM2 source dataset is empty."
        )

    if frame.crs is None:
        raise ValueError(
            "Costa Rica ADM2 source dataset has no CRS."
        )

    if frame.crs.to_string() != EXPECTED_CRS:
        raise ValueError(
            "Unexpected Costa Rica ADM2 CRS: "
            f"{frame.crs}. Expected {EXPECTED_CRS}."
        )

    missing_columns = (
        EXPECTED_SOURCE_COLUMNS - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "Costa Rica ADM2 source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if len(frame) != EXPECTED_CANTON_COUNT:
        raise ValueError(
            "Unexpected Costa Rica ADM2 feature count: "
            f"{len(frame)}. Expected {EXPECTED_CANTON_COUNT}."
        )

    required_text_columns = [
        "adm2_name",
        "adm2_pcode",
        "adm1_name",
        "adm1_pcode",
    ]

    for column in required_text_columns:
        if frame[column].isna().any():
            raise ValueError(
                f"Costa Rica ADM2 contains a null {column} value."
            )

        if (
            frame[column]
            .astype(str)
            .str.strip()
            .eq("")
            .any()
        ):
            raise ValueError(
                f"Costa Rica ADM2 contains a blank {column} value."
            )

    if frame["adm2_name"].duplicated().any():
        raise ValueError(
            "Costa Rica ADM2 contains duplicate canton names."
        )

    if frame["adm2_pcode"].duplicated().any():
        raise ValueError(
            "Costa Rica ADM2 contains duplicate canton pcodes."
        )

    invalid_geometry = (
        frame.geometry.isna()
        | frame.geometry.is_empty
        | ~frame.geometry.is_valid
    )

    if invalid_geometry.any():
        raise ValueError(
            "Costa Rica ADM2 contains invalid, empty, "
            "or null geometry."
        )


def build_runtime_frame(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Create normalized GeoPedia canton records."""
    frame = source[
        [
            "adm2_pcode",
            "adm2_name",
            "adm1_pcode",
            "adm1_name",
            "geometry",
        ]
    ].copy()

    frame["canton_id"] = frame["adm2_pcode"].apply(
        strip_cr_prefix
    )

    frame["province_id"] = frame["adm1_pcode"].apply(
        strip_cr_prefix
    )

    frame["name"] = (
        frame["adm2_name"]
        .astype(str)
        .str.strip()
    )

    frame["province_name"] = (
        frame["adm1_name"]
        .astype(str)
        .str.strip()
    )

    return frame


def validate_normalized_data(
    frame: gpd.GeoDataFrame,
) -> None:
    """Validate normalized canton IDs and their province hierarchy."""
    if frame["canton_id"].duplicated().any():
        raise ValueError(
            "Normalized Costa Rica cantons contain duplicate IDs."
        )

    if frame["name"].duplicated().any():
        raise ValueError(
            "Normalized Costa Rica cantons contain duplicate names."
        )

    for _, row in frame.iterrows():
        canton_id = row["canton_id"]
        province_id = row["province_id"]
        province_name = row["province_name"]

        if (
            len(canton_id) != 3
            or not canton_id.isdigit()
        ):
            raise ValueError(
                f"Invalid Costa Rica canton ID: {canton_id!r}"
            )

        if (
            len(province_id) != 1
            or not province_id.isdigit()
        ):
            raise ValueError(
                f"Invalid Costa Rica province ID: {province_id!r}"
            )

        if canton_id[0] != province_id:
            raise ValueError(
                "Costa Rica canton hierarchy mismatch: "
                f"canton {canton_id} belongs to source province "
                f"{province_id}."
            )

        expected_province_name = EXPECTED_PROVINCES.get(
            province_id
        )

        if expected_province_name is None:
            raise ValueError(
                "Costa Rica canton references an unexpected "
                f"province ID: {province_id!r}"
            )

        if province_name != expected_province_name:
            raise ValueError(
                "Costa Rica canton province name mismatch for "
                f"{canton_id}: expected "
                f"{expected_province_name!r}, got "
                f"{province_name!r}."
            )


def simplify_geometry(
    frame: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Simplify canton geometry using a meter-based tolerance."""
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
    if len(frame) != EXPECTED_CANTON_COUNT:
        raise ValueError(
            "Processed canton count changed unexpectedly."
        )

    if frame["canton_id"].duplicated().any():
        raise ValueError(
            "Processed cantons contain duplicate IDs."
        )

    invalid_geometry = (
        frame.geometry.isna()
        | frame.geometry.is_empty
        | ~frame.geometry.is_valid
    )

    if invalid_geometry.any():
        raise ValueError(
            "Processed cantons contain invalid, empty, "
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
            "Processed cantons contain unexpected geometry types: "
            f"{sorted(unexpected_types)}"
        )


def prepare_runtime_output(
    frame: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Keep only properties required by the GeoPedia runtime."""
    return frame[
        [
            "canton_id",
            "name",
            "province_id",
            "geometry",
        ]
    ].copy()


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
    """Process Costa Rica ADM2 boundaries into runtime cantons."""
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

    province_counts = (
        frame.groupby(
            [
                "province_id",
                "province_name",
            ]
        )
        .size()
        .sort_index()
    )

    print("Cantons by province:")

    for (
        province_id,
        province_name,
    ), count in province_counts.items():
        print(
            f"  {province_id} | "
            f"{province_name}: {count}"
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

    runtime_frame = prepare_runtime_output(
        frame
    )

    output_size = write_compact_geojson(
        runtime_frame
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
        "Costa Rica canton processing and validation passed."
    )


if __name__ == "__main__":
    main()