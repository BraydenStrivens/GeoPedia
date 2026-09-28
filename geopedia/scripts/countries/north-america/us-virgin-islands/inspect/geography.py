"""Inspect existing GeoPedia and Census geography for the U.S. Virgin Islands.

This diagnostic script investigates two potential GeoPedia quiz datasets:

1. U.S. county-equivalent features already present in GeoPedia's processed
   U.S. counties dataset.
2. Census ZIP Code Tabulation Areas (ZCTAs) from the national 2020 ZCTA
   shapefile.

The county-equivalent features are identified using state == "VI". Their
combined geometry is then used to spatially identify U.S. Virgin Islands
ZCTAs from the national Census source.

The script reports:

- County-equivalent count, IDs, names, and geometry types.
- ZCTA count and ZIP codes.
- Unique 1-, 2-, and 3-digit ZIP prefixes.
- ZCTA counts for each prefix.
- Geographic bounds and disconnected polygon counts for each prefix.
- Total, average, smallest, and largest ZCTA coordinate counts.
- Approximate compact runtime GeoJSON size.

The script does not write runtime data.

Inputs:
    public/data/countries/usa/geojson/counties.geojson

    data/raw/countries/usa/census/zip-codes/
        tl_2020_us_zcta520/tl_2020_us_zcta520.shp
"""

from collections import Counter
from pathlib import Path

import geopandas as gpd
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]

COUNTIES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "usa"
    / "geojson"
    / "counties.geojson"
)

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

EXPECTED_COUNTY_EQUIVALENT_COUNT = 3

# U.S. Virgin Islands lies in UTM zone 20N. A projected CRS lets us calculate
# meaningful polygon overlap ratios instead of measuring area in degrees.
AREA_CRS = "EPSG:32620"


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


def count_polygon_parts(geometry) -> int:
    """Count polygon components in a geometry."""
    if geometry is None or geometry.is_empty:
        return 0

    if isinstance(geometry, Polygon):
        return 1

    if isinstance(geometry, MultiPolygon):
        return len(geometry.geoms)

    if hasattr(geometry, "geoms"):
        return sum(
            count_polygon_parts(part)
            for part in geometry.geoms
        )

    return 0


def count_coordinates(geometry) -> int:
    """Count all coordinate positions in a Shapely geometry."""
    if geometry is None or geometry.is_empty:
        return 0

    if isinstance(geometry, Point):
        return 1

    if isinstance(geometry, LineString):
        return len(geometry.coords)

    if isinstance(geometry, Polygon):
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if isinstance(
        geometry,
        (
            MultiPoint,
            MultiLineString,
            MultiPolygon,
            GeometryCollection,
        ),
    ):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    if hasattr(geometry, "geoms"):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    raise TypeError(
        f"Unsupported geometry type: {geometry.geom_type}"
    )


def format_bytes(byte_count: int) -> str:
    """Format a byte count using readable binary units."""
    value = float(byte_count)

    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{byte_count} B"


def load_county_equivalents() -> gpd.GeoDataFrame:
    """Load and inspect U.S. Virgin Islands county-equivalent features."""
    print("Reading U.S. counties from:")
    print(COUNTIES_PATH)
    print()

    counties = gpd.read_file(
        COUNTIES_PATH
    )

    if counties.empty:
        raise ValueError(
            "GeoPedia U.S. counties dataset is empty."
        )

    if counties.crs is None:
        raise ValueError(
            "GeoPedia U.S. counties dataset has no CRS."
        )

    required_columns = {
        "geoid",
        "name",
        "state",
        "geometry",
    }

    missing_columns = (
        required_columns - set(counties.columns)
    )

    if missing_columns:
        raise ValueError(
            "U.S. counties dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    usvi = counties[
        counties["state"] == "VI"
    ].copy()

    if len(usvi) != EXPECTED_COUNTY_EQUIVALENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_COUNTY_EQUIVALENT_COUNT} "
            "U.S. Virgin Islands county-equivalent features, "
            f"found {len(usvi)}."
        )

    invalid_geometries = usvi[
        usvi.geometry.isna()
        | usvi.geometry.is_empty
        | ~usvi.geometry.is_valid
    ]

    if len(invalid_geometries) > 0:
        raise ValueError(
            "U.S. Virgin Islands county-equivalent dataset contains "
            "invalid geometry."
        )

    usvi = usvi.sort_values(
        "geoid"
    ).reset_index(
        drop=True
    )

    print("=" * 72)
    print("COUNTY EQUIVALENTS")
    print("=" * 72)
    print(f"Features: {len(usvi)}")
    print(f"CRS: {usvi.crs}")
    print()

    for _, row in usvi.iterrows():
        full_name = (
            row["fullName"]
            if "fullName" in usvi.columns
            else row["name"]
        )

        print(
            f"{row['geoid']} | "
            f"{row['name']} | "
            f"{full_name} | "
            f"{row.geometry.geom_type}"
        )

    print()

    bounds = usvi.total_bounds

    print("Combined bounds:")
    print(
        f"  ({bounds[0]:.6f}, {bounds[1]:.6f}) -> "
        f"({bounds[2]:.6f}, {bounds[3]:.6f})"
    )
    print()

    return usvi


def load_candidate_zctas(
    usvi: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Load national ZCTA features within the USVI bounding box."""
    bounds = usvi.total_bounds

    bbox = (
        bounds[0],
        bounds[1],
        bounds[2],
        bounds[3],
    )

    print("Reading candidate ZCTAs from:")
    print(ZCTA_PATH)
    print()

    zctas = gpd.read_file(
        ZCTA_PATH,
        bbox=bbox,
    )

    if zctas.empty:
        raise ValueError(
            "No ZCTAs were returned for the U.S. Virgin Islands "
            "bounding box."
        )

    if zctas.crs is None:
        raise ValueError(
            "Census ZCTA source has no CRS."
        )

    print("=" * 72)
    print("ZCTA SOURCE")
    print("=" * 72)
    print(
        f"Candidate features from bounding box: "
        f"{len(zctas)}"
    )
    print(f"CRS: {zctas.crs}")
    print(
        f"Columns: {list(zctas.columns)}"
    )
    print()

    return zctas


def filter_usvi_zctas(
    zctas: gpd.GeoDataFrame,
    usvi: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Keep ZCTAs that spatially intersect the U.S. Virgin Islands."""
    usvi = usvi.to_crs(
        zctas.crs
    )

    usvi_geometry = (
        usvi.geometry.union_all()
    )

    zctas = zctas[
        zctas.geometry.intersects(
            usvi_geometry
        )
    ].copy()

    if zctas.empty:
        raise ValueError(
            "No ZCTAs intersect the U.S. Virgin Islands geometry."
        )

    print("=" * 72)
    print("SPATIAL FILTER")
    print("=" * 72)
    print(
        "ZCTAs intersecting U.S. Virgin Islands: "
        f"{len(zctas)}"
    )
    print()

    return zctas


def calculate_overlap_ratios(
    zctas: gpd.GeoDataFrame,
    usvi: gpd.GeoDataFrame,
) -> list[float]:
    """Calculate how much of each ZCTA overlaps the USVI boundary."""
    zctas_projected = zctas.to_crs(
        AREA_CRS
    )

    usvi_projected = usvi.to_crs(
        AREA_CRS
    )

    usvi_geometry = (
        usvi_projected.geometry.union_all()
    )

    overlap_ratios: list[float] = []

    for geometry in zctas_projected.geometry:
        total_area = geometry.area

        if total_area <= 0:
            overlap_ratios.append(0.0)
            continue

        overlap_area = geometry.intersection(
            usvi_geometry
        ).area

        overlap_ratios.append(
            overlap_area / total_area
        )

    return overlap_ratios


def normalize_zctas(
    zctas: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, str]:
    """Normalize Census ZCTA identifiers as five-digit strings."""
    zcta_column = find_zcta_column(
        list(zctas.columns)
    )

    print(
        f"Using ZIP/ZCTA column: {zcta_column}"
    )
    print()

    zctas["zip_code"] = (
        zctas[zcta_column]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    invalid_codes = zctas[
        ~zctas["zip_code"].str.fullmatch(
            r"\d{5}"
        )
    ]

    if len(invalid_codes) > 0:
        raise ValueError(
            "Found invalid five-digit ZCTA values:\n"
            f"{invalid_codes[[zcta_column, 'zip_code']]}"
        )

    if zctas["zip_code"].duplicated().any():
        duplicates = sorted(
            zctas.loc[
                zctas["zip_code"].duplicated(
                    keep=False
                ),
                "zip_code",
            ].unique()
        )

        raise ValueError(
            f"Duplicate ZCTA codes found: {duplicates}"
        )

    zctas = zctas.sort_values(
        "zip_code"
    ).reset_index(
        drop=True
    )

    return zctas, zcta_column


def print_zctas(
    zctas: gpd.GeoDataFrame,
    zcta_column: str,
    usvi: gpd.GeoDataFrame,
) -> None:
    """Print USVI ZCTA identifiers and overlap diagnostics."""
    overlap_ratios = calculate_overlap_ratios(
        zctas,
        usvi,
    )

    zctas["usvi_overlap"] = overlap_ratios

    print("=" * 72)
    print("U.S. VIRGIN ISLANDS ZCTAS")
    print("=" * 72)
    print(
        f"5-digit ZCTAs: {len(zctas)}"
    )
    print()

    for _, row in zctas.iterrows():
        print(
            f"{row['zip_code']} | "
            f"USVI overlap: {row['usvi_overlap']:.2%}"
        )

    suspicious = zctas[
        zctas["usvi_overlap"] < 0.50
    ]

    if len(suspicious) > 0:
        print()
        print(
            "WARNING: ZCTAs with less than 50% of their polygon "
            "inside the U.S. Virgin Islands county-equivalent geometry:"
        )

        for _, row in suspicious.iterrows():
            print(
                f"  {row[zcta_column]}: "
                f"{row['usvi_overlap']:.2%}"
            )

    print()


def print_geometry_summary(
    zctas: gpd.GeoDataFrame,
) -> None:
    """Print ZCTA coordinate-count and runtime-size diagnostics."""
    coordinate_counts = [
        count_coordinates(geometry)
        for geometry in zctas.geometry
    ]

    if not coordinate_counts:
        raise ValueError(
            "Cannot calculate geometry statistics for an empty dataset."
        )

    total_coordinates = sum(
        coordinate_counts
    )

    largest_index = max(
        range(len(coordinate_counts)),
        key=coordinate_counts.__getitem__,
    )

    largest_zip = (
        zctas.iloc[largest_index]["zip_code"]
    )

    largest_count = (
        coordinate_counts[largest_index]
    )

    smallest_count = min(
        coordinate_counts
    )

    average_count = (
        total_coordinates / len(coordinate_counts)
    )

    runtime_preview = zctas[
        [
            "zip_code",
            "geometry",
        ]
    ].copy()

    runtime_preview["prefix_3"] = (
        runtime_preview["zip_code"].str[:3]
    )

    runtime_preview = runtime_preview[
        [
            "zip_code",
            "prefix_3",
            "geometry",
        ]
    ]

    geojson_text = runtime_preview.to_json(
        drop_id=True,
        separators=(",", ":"),
    )

    geojson_size = len(
        geojson_text.encode("utf-8")
    )

    print("=" * 72)
    print("ZCTA GEOMETRY")
    print("=" * 72)
    print(
        f"Total coordinates: "
        f"{total_coordinates:,}"
    )
    print(
        f"Average coordinates per ZCTA: "
        f"{average_count:,.1f}"
    )
    print(
        f"Smallest ZCTA coordinate count: "
        f"{smallest_count:,}"
    )
    print(
        f"Largest ZCTA coordinate count: "
        f"{largest_count:,} ({largest_zip})"
    )
    print(
        "Approximate compact unsimplified runtime GeoJSON size: "
        f"{format_bytes(geojson_size)} "
        f"({geojson_size:,} bytes)"
    )
    print()


def print_prefix_summary(
    zctas: gpd.GeoDataFrame,
    prefix_length: int,
) -> None:
    """Print count and geography statistics for one ZIP-prefix length."""
    prefix_column = (
        f"prefix_{prefix_length}"
    )

    zctas = zctas.copy()

    zctas[prefix_column] = (
        zctas["zip_code"].str[:prefix_length]
    )

    counts = Counter(
        zctas[prefix_column]
    )

    print("=" * 72)
    print(
        f"{prefix_length}-DIGIT PREFIXES"
    )
    print("=" * 72)
    print(
        f"Unique prefixes: {len(counts)}"
    )
    print()

    for prefix in sorted(counts):
        prefix_rows = zctas[
            zctas[prefix_column] == prefix
        ]

        dissolved = (
            prefix_rows.geometry.union_all()
        )

        min_x, min_y, max_x, max_y = (
            dissolved.bounds
        )

        polygon_parts = count_polygon_parts(
            dissolved
        )

        print(
            f"{prefix}: "
            f"{len(prefix_rows)} ZCTAs | "
            f"{polygon_parts} polygon part(s) | "
            f"bounds "
            f"({min_x:.4f}, {min_y:.4f}) -> "
            f"({max_x:.4f}, {max_y:.4f})"
        )

    print()


def main() -> None:
    """Inspect existing GeoPedia geography for the U.S. Virgin Islands."""
    usvi = load_county_equivalents()

    zctas = load_candidate_zctas(
        usvi
    )

    zctas = filter_usvi_zctas(
        zctas,
        usvi,
    )

    zctas, zcta_column = normalize_zctas(
        zctas
    )

    print_zctas(
        zctas,
        zcta_column,
        usvi,
    )

    print_geometry_summary(
        zctas
    )

    for prefix_length in (1, 2, 3):
        print_prefix_summary(
            zctas,
            prefix_length,
        )

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(
        f"County equivalents: {len(usvi)}"
    )
    print(
        f"5-digit ZCTAs: "
        f"{zctas['zip_code'].nunique()}"
    )

    for prefix_length in (3, 2, 1):
        count = (
            zctas["zip_code"]
            .str[:prefix_length]
            .nunique()
        )

        print(
            f"{prefix_length}-digit prefixes: "
            f"{count}"
        )

    print()
    print("Inspection complete.")


if __name__ == "__main__":
    main()