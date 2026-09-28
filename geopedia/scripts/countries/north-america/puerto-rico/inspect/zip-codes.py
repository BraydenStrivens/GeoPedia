"""Inspect Census ZCTA records that intersect Puerto Rico.

This diagnostic script uses GeoPedia's processed Puerto Rico municipality
geometry to identify Puerto Rico ZCTAs from the national 2020 Census ZCTA
shapefile.

It reports:

- Source schema and CRS.
- Number of Puerto Rico ZCTAs.
- Unique 1-, 2-, and 3-digit ZIP prefixes.
- ZCTA counts for each prefix.
- Approximate geographic bounds for each prefix.
- Whether individual prefixes form multiple disconnected geographic pieces.
- Total coordinate count across Puerto Rico ZCTAs.
- Average and largest ZCTA coordinate counts.
- Approximate unsimplified runtime GeoJSON size.

The script does not write runtime data. Its purpose is to determine which
ZIP-code granularity and geometry processing are appropriate for GeoPedia
before a processor or quiz configuration is created.

Inputs:
    data/raw/countries/usa/census/zip-codes/
        tl_2020_us_zcta520/tl_2020_us_zcta520.shp

    public/data/countries/puerto-rico/geojson/municipalities.geojson
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

# Puerto Rico falls within UTM zone 20N. Using a projected CRS lets us compare
# overlap areas rather than relying on areas measured in longitude/latitude.
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
    """Count polygon components in a dissolved prefix geometry."""
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


def print_geometry_summary(
    zctas: gpd.GeoDataFrame,
) -> None:
    """Print coordinate-count and unsimplified GeoJSON size diagnostics."""
    coordinate_counts = [
        count_coordinates(geometry)
        for geometry in zctas.geometry
    ]

    total_coordinates = sum(coordinate_counts)

    if not coordinate_counts:
        raise ValueError(
            "Cannot calculate geometry statistics for an empty dataset."
        )

    largest_index = max(
        range(len(coordinate_counts)),
        key=coordinate_counts.__getitem__,
    )

    largest_zip = zctas.iloc[largest_index]["zip_code"]
    largest_count = coordinate_counts[largest_index]

    smallest_count = min(coordinate_counts)
    average_count = total_coordinates / len(coordinate_counts)

    #
    # Estimate the size of the runtime data rather than the full Census schema.
    # These are the only properties currently expected to be useful in the
    # processed GeoPedia ZIP dataset.
    #
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

    print()
    print("=" * 72)
    print("GEOMETRY")
    print("=" * 72)
    print(f"ZCTAs: {len(zctas)}")
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


def print_prefix_summary(
    zctas: gpd.GeoDataFrame,
    prefix_length: int,
) -> None:
    """Print geographic and count statistics for one ZIP-prefix length."""
    prefix_column = f"prefix_{prefix_length}"

    zctas = zctas.copy()
    zctas[prefix_column] = zctas["zip_code"].str[:prefix_length]

    print()
    print("=" * 72)
    print(f"{prefix_length}-DIGIT PREFIXES")
    print("=" * 72)

    counts = Counter(zctas[prefix_column])

    print(f"Unique prefixes: {len(counts)}")
    print()

    for prefix in sorted(counts):
        prefix_rows = zctas[
            zctas[prefix_column] == prefix
        ]

        dissolved = prefix_rows.geometry.union_all()

        min_x, min_y, max_x, max_y = dissolved.bounds
        polygon_parts = count_polygon_parts(dissolved)

        print(
            f"{prefix}: "
            f"{len(prefix_rows)} ZCTAs | "
            f"{polygon_parts} polygon part(s) | "
            f"bounds "
            f"({min_x:.4f}, {min_y:.4f}) -> "
            f"({max_x:.4f}, {max_y:.4f})"
        )


def main() -> None:
    """Inspect Puerto Rico ZCTAs and ZIP-prefix geography."""
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

    print(f"Municipalities: {len(municipalities)}")
    print(
        f"Municipality CRS: {municipalities.crs}"
    )
    print()

    #
    # Reading the entire national 819 MB shapefile is unnecessary. GeoPandas
    # can first restrict the read to Puerto Rico's geographic bounding box.
    #
    municipality_bounds = municipalities.total_bounds

    bbox = (
        municipality_bounds[0],
        municipality_bounds[1],
        municipality_bounds[2],
        municipality_bounds[3],
    )

    print("Puerto Rico municipality bounds:")
    print(
        f"  ({bbox[0]:.6f}, {bbox[1]:.6f}) -> "
        f"({bbox[2]:.6f}, {bbox[3]:.6f})"
    )
    print()

    print("Reading candidate ZCTAs from:")
    print(ZCTA_PATH)
    print()

    zctas = gpd.read_file(
        ZCTA_PATH,
        bbox=bbox,
    )

    if zctas.empty:
        raise ValueError(
            "No ZCTAs were returned for Puerto Rico's bounding box."
        )

    if zctas.crs is None:
        raise ValueError(
            "ZCTA source has no CRS."
        )

    print("SOURCE")
    print("=" * 72)
    print(
        f"Candidate features from bbox: "
        f"{len(zctas)}"
    )
    print(f"CRS: {zctas.crs}")
    print(
        f"Columns: {list(zctas.columns)}"
    )
    print()

    zcta_column = find_zcta_column(
        list(zctas.columns)
    )

    print(
        f"Using ZIP/ZCTA column: "
        f"{zcta_column}"
    )
    print()

    #
    # Normalize both datasets to the same geographic CRS before spatial
    # filtering.
    #
    municipalities = municipalities.to_crs(
        zctas.crs
    )

    puerto_rico_geometry = (
        municipalities.geometry.union_all()
    )

    #
    # The bounding-box read may include features near Puerto Rico that do not
    # actually belong to it. Require a real geometry intersection.
    #
    zctas = zctas[
        zctas.geometry.intersects(
            puerto_rico_geometry
        )
    ].copy()

    print("SPATIAL FILTER")
    print("=" * 72)
    print(
        "ZCTAs intersecting Puerto Rico municipalities: "
        f"{len(zctas)}"
    )
    print()

    if zctas.empty:
        raise ValueError(
            "No ZCTAs intersect Puerto Rico municipality geometry."
        )

    #
    # Calculate overlap proportions as an additional diagnostic. A legitimate
    # Puerto Rico ZCTA should overlap Puerto Rico substantially; tiny overlaps
    # could indicate a geometry edge case.
    #
    zctas_projected = zctas.to_crs(
        AREA_CRS
    )

    municipalities_projected = (
        municipalities.to_crs(
            AREA_CRS
        )
    )

    puerto_rico_projected = (
        municipalities_projected.geometry.union_all()
    )

    overlap_ratios: list[float] = []

    for geometry in zctas_projected.geometry:
        total_area = geometry.area

        if total_area <= 0:
            overlap_ratios.append(0.0)
            continue

        overlap_area = geometry.intersection(
            puerto_rico_projected
        ).area

        overlap_ratios.append(
            overlap_area / total_area
        )

    zctas["puerto_rico_overlap"] = (
        overlap_ratios
    )

    suspicious = zctas[
        zctas["puerto_rico_overlap"] < 0.50
    ]

    if len(suspicious) > 0:
        print(
            "WARNING: ZCTAs with less than 50% of their polygon "
            "inside Puerto Rico municipality geometry:"
        )

        for _, row in suspicious.iterrows():
            print(
                f"  {row[zcta_column]}: "
                f"{row['puerto_rico_overlap']:.2%}"
            )

        print()

    #
    # Normalize the five-digit ZIP/ZCTA identifier. Keep it as a string so
    # leading zeroes are preserved.
    #
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

    print("PUERTO RICO ZCTAS")
    print("=" * 72)
    print(
        f"5-digit ZCTAs: {len(zctas)}"
    )
    print()

    for zip_code in zctas["zip_code"]:
        print(zip_code)

    #
    # Geometry diagnostics determine whether the processor should simplify
    # these raw Census polygons before placing them in public/data.
    #
    print_geometry_summary(
        zctas
    )

    #
    # Prefix summaries determine which prefix levels are useful as quiz
    # grouping properties.
    #
    for prefix_length in (1, 2, 3):
        print_prefix_summary(
            zctas,
            prefix_length,
        )

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

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