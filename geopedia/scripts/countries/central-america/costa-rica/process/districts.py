"""Process Costa Rica district boundaries for GeoPedia.

This script converts the raw Costa Rica ADM3 administrative-boundary
dataset into the compact runtime GeoJSON used by GeoPedia.

Processing:
- Validates the expected 492 Costa Rica districts.
- Converts source pcodes such as CR10101 into district IDs such as 10101.
- Converts parent pcodes such as CR101 and CR1 into canton/province IDs.
- Validates the district/canton/province hierarchy.
- Keeps only the runtime properties needed by GeoPedia.
- Simplifies geometry in a projected CRS.
- Preserves topology during simplification.
- Converts the result back to EPSG:4326.
- Validates the processed dataset.
- Writes compact GeoJSON.

Because Costa Rica's 5-digit district codes are also postal codes,
the normalized district_id can be reused directly by the full
5-digit postal-code quiz.

Input:
    data/raw/countries/costa-rica/cri_admin_boundaries.geojson/
        cri_admin3.geojson

Output:
    public/data/countries/costa-rica/geojson/districts.geojson

Runtime properties:
    district_id
    name
    canton_id
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
    / "cri_admin3.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "costa-rica"
    / "geojson"
    / "districts.geojson"
)

EXPECTED_DISTRICT_COUNT = 492

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
    "adm3_name",
    "adm3_pcode",
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
    """Count coordinate pairs in polygonal geometry."""
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

    normalized = value[2:]

    if not normalized:
        raise ValueError(
            f"Costa Rica pcode contains no numeric portion: {value!r}"
        )

    return normalized


def validate_source(frame: gpd.GeoDataFrame) -> None:
    """Validate the raw ADM3 source before processing."""
    if frame.empty:
        raise ValueError(
            "Costa Rica ADM3 source dataset is empty."
        )

    if frame.crs is None:
        raise ValueError(
            "Costa Rica ADM3 source dataset has no CRS."
        )

    if frame.crs.to_string() != EXPECTED_CRS:
        raise ValueError(
            "Unexpected Costa Rica ADM3 CRS: "
            f"{frame.crs}. Expected {EXPECTED_CRS}."
        )

    missing_columns = (
        EXPECTED_SOURCE_COLUMNS - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "Costa Rica ADM3 source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if len(frame) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected Costa Rica ADM3 feature count: "
            f"{len(frame)}. Expected {EXPECTED_DISTRICT_COUNT}."
        )

    required_text_columns = [
        "adm3_name",
        "adm3_pcode",
        "adm2_name",
        "adm2_pcode",
        "adm1_name",
        "adm1_pcode",
    ]

    for column in required_text_columns:
        if frame[column].isna().any():
            raise ValueError(
                f"Costa Rica ADM3 contains a null {column} value."
            )

        if (
            frame[column]
            .astype(str)
            .str.strip()
            .eq("")
            .any()
        ):
            raise ValueError(
                f"Costa Rica ADM3 contains a blank {column} value."
            )

    if frame["adm3_pcode"].duplicated().any():
        raise ValueError(
            "Costa Rica ADM3 contains duplicate district pcodes."
        )

    invalid_geometry = (
        frame.geometry.isna()
        | frame.geometry.is_empty
        | ~frame.geometry.is_valid
    )

    if invalid_geometry.any():
        raise ValueError(
            "Costa Rica ADM3 contains invalid, empty, "
            "or null geometry."
        )


def build_runtime_frame(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Create normalized GeoPedia district records."""
    frame = source[
        [
            "adm3_pcode",
            "adm3_name",
            "adm2_pcode",
            "adm2_name",
            "adm1_pcode",
            "adm1_name",
            "geometry",
        ]
    ].copy()

    frame["district_id"] = frame["adm3_pcode"].apply(
        strip_cr_prefix
    )

    frame["canton_id"] = frame["adm2_pcode"].apply(
        strip_cr_prefix
    )

    frame["province_id"] = frame["adm1_pcode"].apply(
        strip_cr_prefix
    )

    frame["name"] = (
        frame["adm3_name"]
        .astype(str)
        .str.strip()
    )

    frame["canton_name"] = (
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
    """Validate normalized district IDs and administrative hierarchy."""
    if frame["district_id"].duplicated().any():
        raise ValueError(
            "Normalized Costa Rica districts contain duplicate IDs."
        )

    for _, row in frame.iterrows():
        district_id = row["district_id"]
        canton_id = row["canton_id"]
        province_id = row["province_id"]
        province_name = row["province_name"]

        if (
            len(district_id) != 5
            or not district_id.isdigit()
        ):
            raise ValueError(
                f"Invalid Costa Rica district ID: {district_id!r}"
            )

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

        if district_id[:3] != canton_id:
            raise ValueError(
                "Costa Rica district/canton hierarchy mismatch: "
                f"district {district_id} belongs to source canton "
                f"{canton_id}."
            )

        if district_id[0] != province_id:
            raise ValueError(
                "Costa Rica district/province hierarchy mismatch: "
                f"district {district_id} belongs to source province "
                f"{province_id}."
            )

        if canton_id[0] != province_id:
            raise ValueError(
                "Costa Rica canton/province hierarchy mismatch: "
                f"canton {canton_id} belongs to source province "
                f"{province_id}."
            )

        expected_province_name = EXPECTED_PROVINCES.get(
            province_id
        )

        if expected_province_name is None:
            raise ValueError(
                "Costa Rica district references an unexpected "
                f"province ID: {province_id!r}"
            )

        if province_name != expected_province_name:
            raise ValueError(
                "Costa Rica district province name mismatch for "
                f"{district_id}: expected "
                f"{expected_province_name!r}, got "
                f"{province_name!r}."
            )


def print_duplicate_names(
    frame: gpd.GeoDataFrame,
) -> None:
    """Report district names that occur more than once."""
    duplicate_rows = frame[
        frame["name"].duplicated(
            keep=False
        )
    ].copy()

    if duplicate_rows.empty:
        print("Duplicate district names: 0")
        return

    duplicate_names = sorted(
        duplicate_rows["name"].unique()
    )

    print(
        f"Duplicate district names: {len(duplicate_names)}"
    )

    for name in duplicate_names:
        matches = duplicate_rows[
            duplicate_rows["name"] == name
        ].sort_values(
            [
                "province_id",
                "canton_id",
                "district_id",
            ]
        )

        locations = [
            (
                f"{row['district_id']} | "
                f"{row['canton_name']} | "
                f"{row['province_name']}"
            )
            for _, row in matches.iterrows()
        ]

        print(
            f"  {name}:"
        )

        for location in locations:
            print(
                f"    {location}"
            )


def simplify_geometry(
    frame: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Simplify district geometry using a meter-based tolerance."""
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
    if len(frame) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Processed district count changed unexpectedly."
        )

    if frame["district_id"].duplicated().any():
        raise ValueError(
            "Processed districts contain duplicate IDs."
        )

    invalid_geometry = (
        frame.geometry.isna()
        | frame.geometry.is_empty
        | ~frame.geometry.is_valid
    )

    if invalid_geometry.any():
        invalid_rows = frame.loc[
            invalid_geometry,
            [
                "district_id",
                "name",
            ],
        ]

        raise ValueError(
            "Processed districts contain invalid, empty, "
            "or null geometry:\n"
            f"{invalid_rows.to_string(index=False)}"
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
            "Processed districts contain unexpected geometry types: "
            f"{sorted(unexpected_types)}"
        )


def prepare_runtime_output(
    frame: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Keep only properties required by the GeoPedia runtime."""
    return frame[
        [
            "district_id",
            "name",
            "canton_id",
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
    """Process Costa Rica ADM3 boundaries into runtime districts."""
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

    print("Districts by province:")

    for (
        province_id,
        province_name,
    ), count in province_counts.items():
        print(
            f"  {province_id} | "
            f"{province_name}: {count}"
        )

    print()
    print_duplicate_names(
        frame
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
        "Costa Rica district processing and validation passed."
    )


if __name__ == "__main__":
    main()