"""Process Puerto Rico ZIP Code Tabulation Areas for GeoPedia.

This processor extracts Puerto Rico ZCTAs from the national 2020 Census ZCTA
shapefile using Puerto Rico's processed municipality geometry as a spatial
filter.

The source Census geometry is preserved without simplification. Runtime
properties are reduced to only those required by GeoPedia:

    zip_code
    prefix_3

Inputs:
    data/raw/countries/usa/census/zip-codes/
        tl_2020_us_zcta520/tl_2020_us_zcta520.shp

    public/data/countries/puerto-rico/geojson/municipalities.geojson

Output:
    public/data/countries/puerto-rico/geojson/zip-codes.geojson
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

ZCTA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "usa"
    / "census"
    / "zip-codes"
    / "tl_2020_us_zcta520"
    / "tl_2020_us_zcta520.shp"
)

MUNICIPALITIES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "zip-codes.geojson"
)

EXPECTED_ZCTA_COUNT = 132

EXPECTED_PREFIXES = {
    "006",
    "007",
    "009",
}


def find_zcta_column(columns: list[str]) -> str:
    """Find the source column containing the five-digit ZCTA identifier."""
    candidates = [
        "ZCTA5CE20",
        "GEOID20",
        "ZCTA5CE10",
        "GEOID10",
    ]

    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise ValueError(
        "Could not identify the ZCTA code column. "
        f"Available columns: {columns}"
    )


def load_municipalities() -> gpd.GeoDataFrame:
    """Load and validate Puerto Rico's processed municipality geometry."""
    print("Reading municipalities from:")
    print(MUNICIPALITIES_PATH)
    print()

    municipalities = gpd.read_file(
        MUNICIPALITIES_PATH
    )

    if municipalities.empty:
        raise ValueError(
            "Puerto Rico municipality dataset is empty."
        )

    if municipalities.crs is None:
        raise ValueError(
            "Puerto Rico municipality dataset has no CRS."
        )

    if len(municipalities) != 78:
        raise ValueError(
            f"Expected 78 municipalities, found {len(municipalities)}."
        )

    invalid_geometries = municipalities[
        municipalities.geometry.isna()
        | municipalities.geometry.is_empty
        | ~municipalities.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        raise ValueError(
            "Puerto Rico municipality dataset contains invalid geometry."
        )

    print(f"Municipalities: {len(municipalities)}")
    print(f"CRS: {municipalities.crs}")
    print()

    return municipalities


def load_candidate_zctas(
    municipalities: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Load national ZCTA features within Puerto Rico's bounding box."""
    bounds = municipalities.total_bounds

    bbox = (
        bounds[0],
        bounds[1],
        bounds[2],
        bounds[3],
    )

    print("Reading candidate ZCTAs from:")
    print(ZCTA_PATH)
    print()

    print(
        "Puerto Rico bounding box: "
        f"({bbox[0]:.6f}, {bbox[1]:.6f}) -> "
        f"({bbox[2]:.6f}, {bbox[3]:.6f})"
    )
    print()

    zctas = gpd.read_file(
        ZCTA_PATH,
        bbox=bbox,
    )

    if zctas.empty:
        raise ValueError(
            "No ZCTA features were returned for Puerto Rico's bounding box."
        )

    if zctas.crs is None:
        raise ValueError(
            "Census ZCTA source has no CRS."
        )

    print(
        f"Candidate ZCTAs from bounding box: {len(zctas)}"
    )
    print(f"Source CRS: {zctas.crs}")
    print()

    return zctas


def filter_puerto_rico_zctas(
    zctas: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Keep only ZCTAs whose geometry intersects Puerto Rico."""
    municipalities = municipalities.to_crs(
        zctas.crs
    )

    puerto_rico_geometry = (
        municipalities.geometry.union_all()
    )

    zctas = zctas[
        zctas.geometry.intersects(
            puerto_rico_geometry
        )
    ].copy()

    if len(zctas) != EXPECTED_ZCTA_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ZCTA_COUNT} Puerto Rico ZCTAs, "
            f"found {len(zctas)}."
        )

    print(
        "Puerto Rico ZCTAs after spatial filtering: "
        f"{len(zctas)}"
    )
    print()

    return zctas


def normalize_zctas(
    zctas: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Normalize ZIP IDs and reduce properties to GeoPedia runtime fields."""
    zcta_column = find_zcta_column(
        list(zctas.columns)
    )

    print(
        f"Using Census ZCTA column: {zcta_column}"
    )
    print()

    zctas["zip_code"] = (
        zctas[zcta_column]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    invalid_zip_codes = zctas[
        ~zctas["zip_code"].str.fullmatch(
            r"\d{5}"
        )
    ]

    if len(invalid_zip_codes) > 0:
        values = (
            invalid_zip_codes["zip_code"]
            .tolist()
        )

        raise ValueError(
            f"Invalid five-digit ZIP codes found: {values}"
        )

    duplicate_zip_codes = sorted(
        zctas.loc[
            zctas["zip_code"].duplicated(
                keep=False
            ),
            "zip_code",
        ].unique()
    )

    if duplicate_zip_codes:
        raise ValueError(
            "Duplicate ZIP codes found: "
            f"{duplicate_zip_codes}"
        )

    zctas["prefix_3"] = (
        zctas["zip_code"].str[:3]
    )

    prefixes = set(
        zctas["prefix_3"].unique()
    )

    if prefixes != EXPECTED_PREFIXES:
        raise ValueError(
            "Unexpected 3-digit ZIP prefixes. "
            f"Expected {sorted(EXPECTED_PREFIXES)}, "
            f"found {sorted(prefixes)}."
        )

    invalid_geometries = zctas[
        zctas.geometry.isna()
        | zctas.geometry.is_empty
        | ~zctas.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        zip_codes = (
            invalid_geometries["zip_code"]
            .tolist()
        )

        raise ValueError(
            "Invalid ZCTA geometry found for ZIP codes: "
            f"{zip_codes}"
        )

    invalid_geometry_types = zctas[
        ~zctas.geometry.geom_type.isin(
            [
                "Polygon",
                "MultiPolygon",
            ]
        )
    ]

    if len(invalid_geometry_types) > 0:
        rows = [
            (
                row["zip_code"],
                row.geometry.geom_type,
            )
            for _, row in invalid_geometry_types.iterrows()
        ]

        raise ValueError(
            "Unexpected ZCTA geometry types: "
            f"{rows}"
        )

    #
    # Keep only runtime properties required by the map and quiz. Geometry is
    # intentionally preserved exactly as supplied by the Census source.
    #
    zctas = zctas[
        [
            "zip_code",
            "prefix_3",
            "geometry",
        ]
    ].copy()

    zctas = zctas.sort_values(
        "zip_code"
    ).reset_index(
        drop=True
    )

    #
    # GeoPedia runtime GeoJSON uses WGS84 longitude/latitude coordinates.
    #
    zctas = zctas.to_crs(
        "EPSG:4326"
    )

    return zctas


def validate_processed_zctas(
    zctas: gpd.GeoDataFrame,
) -> None:
    """Validate the final Puerto Rico ZIP dataset."""
    if len(zctas) != EXPECTED_ZCTA_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ZCTA_COUNT} processed ZCTAs, "
            f"found {len(zctas)}."
        )

    if zctas["zip_code"].nunique() != EXPECTED_ZCTA_COUNT:
        raise ValueError(
            "Processed ZIP codes are not unique."
        )

    prefixes = set(
        zctas["prefix_3"].unique()
    )

    if prefixes != EXPECTED_PREFIXES:
        raise ValueError(
            "Processed prefix set does not match expected prefixes."
        )

    expected_columns = {
        "zip_code",
        "prefix_3",
        "geometry",
    }

    if set(zctas.columns) != expected_columns:
        raise ValueError(
            "Unexpected processed columns. "
            f"Expected {sorted(expected_columns)}, "
            f"found {sorted(zctas.columns)}."
        )

    if str(zctas.crs).upper() != "EPSG:4326":
        raise ValueError(
            f"Expected output CRS EPSG:4326, found {zctas.crs}."
        )


def write_geojson(
    zctas: gpd.GeoDataFrame,
) -> int:
    """Write compact UTF-8 GeoJSON and return its byte size."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = json.loads(
        zctas.to_json(
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


def format_megabytes(
    byte_count: int,
) -> str:
    """Format a byte count as binary megabytes."""
    return f"{byte_count / (1024 * 1024):.2f} MB"


def print_summary(
    zctas: gpd.GeoDataFrame,
    output_size: int,
) -> None:
    """Print a concise processing summary."""
    print()
    print("Puerto Rico ZIP codes processed successfully.")
    print(f"Features written: {len(zctas)}")
    print(
        "3-digit prefixes: "
        f"{', '.join(sorted(EXPECTED_PREFIXES))}"
    )

    print()
    print("Prefix counts:")

    prefix_counts = (
        zctas["prefix_3"]
        .value_counts()
        .sort_index()
    )

    for prefix, count in prefix_counts.items():
        print(
            f"  {prefix}: {count}"
        )

    print()
    print(
        "Geometry simplification: none"
    )
    print(
        f"Output size: {format_megabytes(output_size)} "
        f"({output_size:,} bytes)"
    )
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


def main() -> None:
    """Process Puerto Rico's Census ZCTA geometry for GeoPedia."""
    municipalities = load_municipalities()

    zctas = load_candidate_zctas(
        municipalities
    )

    zctas = filter_puerto_rico_zctas(
        zctas,
        municipalities,
    )

    zctas = normalize_zctas(
        zctas
    )

    validate_processed_zctas(
        zctas
    )

    output_size = write_geojson(
        zctas
    )

    print_summary(
        zctas,
        output_size,
    )


if __name__ == "__main__":
    main()