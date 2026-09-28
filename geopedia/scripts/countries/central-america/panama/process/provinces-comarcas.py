"""
Processes Panama's 2024 province/comarca boundaries for GeoPedia.

Source:
    data/raw/countries/panama/
    Panama_Province_Boundaries_2024_355929332618465870.geojson

Output:
    public/data/countries/panama/geojson/provinces-comarcas.geojson

The source contains Panama's 10 provinces and four province-level comarcas.
This processor:

- validates the expected source schema,
- repairs invalid polygon geometries,
- removes non-polygonal geometry produced by repairs,
- simplifies the very detailed source geometry for web use,
- keeps only the properties needed by GeoPedia,
- validates the processed result,
- writes compact UTF-8 GeoJSON.
"""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


SOURCE_PATH = Path(
    "data/raw/countries/panama/"
    "Panama_Province_Boundaries_2024_355929332618465870.geojson"
)

OUTPUT_PATH = Path(
    "public/data/countries/panama/geojson/"
    "provinces-comarcas.geojson"
)

EXPECTED_FEATURE_COUNT = 14

# Roughly 55 meters at Panama's latitude.
#
# The raw ADM1 file contains more than 1.3 million coordinates, which is far
# more detail than GeoPedia needs for a country-level quiz. This tolerance
# substantially reduces file size while retaining coastlines, islands, and
# administrative boundaries at normal quiz zoom levels.
SIMPLIFY_TOLERANCE = 0.0005


def polygonal_only(geometry: BaseGeometry) -> BaseGeometry:
    """
    Return only the polygonal portion of a repaired geometry.

    make_valid() can occasionally turn an invalid Polygon or MultiPolygon into
    a GeometryCollection containing polygons plus lower-dimensional artifacts
    such as lines. MapLibre fill layers need polygonal geometry, so those
    non-polygonal parts are discarded.
    """

    if geometry is None or geometry.is_empty:
        return geometry

    if isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            if isinstance(part, Polygon):
                polygons.append(part)

            elif isinstance(part, MultiPolygon):
                polygons.extend(part.geoms)

            elif isinstance(part, GeometryCollection):
                nested = polygonal_only(part)

                if isinstance(nested, Polygon):
                    polygons.append(nested)

                elif isinstance(nested, MultiPolygon):
                    polygons.extend(nested.geoms)

        if not polygons:
            return GeometryCollection()

        return unary_union(polygons)

    return GeometryCollection()


def count_coordinates(geometry: BaseGeometry) -> int:
    """Count coordinate pairs contained in a polygonal geometry."""

    if geometry is None or geometry.is_empty:
        return 0

    if isinstance(geometry, Polygon):
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if isinstance(geometry, MultiPolygon):
        return sum(count_coordinates(part) for part in geometry.geoms)

    if isinstance(geometry, GeometryCollection):
        return sum(count_coordinates(part) for part in geometry.geoms)

    return 0


def validate_source(gdf: gpd.GeoDataFrame) -> None:
    """Validate assumptions GeoPedia relies on from the raw ADM1 source."""

    required_columns = {
        "ID_PROV",
        "Provincia",
        "geometry",
    }

    missing_columns = required_columns - set(gdf.columns)

    if missing_columns:
        raise ValueError(
            "Source is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if len(gdf) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} source features, "
            f"found {len(gdf)}."
        )

    ids = gdf["ID_PROV"].astype(str).str.strip()
    names = gdf["Provincia"].astype(str).str.strip()

    if ids.isna().any() or (ids == "").any():
        raise ValueError("Source contains blank province/comarca IDs.")

    if names.isna().any() or (names == "").any():
        raise ValueError("Source contains blank province/comarca names.")

    if ids.duplicated().any():
        duplicates = sorted(ids[ids.duplicated(keep=False)].unique())

        raise ValueError(
            "Source contains duplicate province/comarca IDs: "
            + ", ".join(duplicates)
        )

    if names.duplicated().any():
        duplicates = sorted(
            names[names.duplicated(keep=False)].unique()
        )

        raise ValueError(
            "Source contains duplicate province/comarca names: "
            + ", ".join(duplicates)
        )

    if gdf.crs is None:
        raise ValueError("Source GeoJSON has no CRS.")

    if gdf.geometry.isna().any():
        raise ValueError("Source contains null geometries.")

    if gdf.geometry.is_empty.any():
        raise ValueError("Source contains empty geometries.")


def repair_geometries(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Repair invalid source geometry and retain polygonal components only."""

    result = gdf.copy()

    invalid_before = (~result.geometry.is_valid).sum()

    print(f"Invalid geometries before repair: {invalid_before}")

    result.geometry = result.geometry.make_valid()
    result.geometry = result.geometry.map(polygonal_only)

    if result.geometry.isna().any():
        raise ValueError("Geometry repair produced null geometries.")

    if result.geometry.is_empty.any():
        raise ValueError("Geometry repair produced empty geometries.")

    invalid_after = (~result.geometry.is_valid).sum()

    print(f"Invalid geometries after repair: {invalid_after}")

    if invalid_after:
        raise ValueError(
            f"{invalid_after} geometries remain invalid after repair."
        )

    invalid_types = result[
        ~result.geometry.geom_type.isin(
            {"Polygon", "MultiPolygon"}
        )
    ]

    if not invalid_types.empty:
        types = sorted(invalid_types.geometry.geom_type.unique())

        raise ValueError(
            "Non-polygonal geometries remain after repair: "
            + ", ".join(types)
        )

    return result


def simplify_geometries(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Simplify boundaries while preserving polygon topology."""

    result = gdf.copy()

    coordinates_before = sum(
        count_coordinates(geometry)
        for geometry in result.geometry
    )

    result.geometry = result.geometry.simplify(
        SIMPLIFY_TOLERANCE,
        preserve_topology=True,
    )

    coordinates_after = sum(
        count_coordinates(geometry)
        for geometry in result.geometry
    )

    print(f"Coordinates before simplification: {coordinates_before:,}")
    print(f"Coordinates after simplification:  {coordinates_after:,}")

    if coordinates_before:
        reduction = (
            1 - coordinates_after / coordinates_before
        ) * 100

        print(f"Coordinate reduction: {reduction:.1f}%")

    if result.geometry.is_empty.any():
        raise ValueError(
            "Simplification produced one or more empty geometries."
        )

    if (~result.geometry.is_valid).any():
        raise ValueError(
            "Simplification produced one or more invalid geometries."
        )

    return result


def build_output(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Create GeoPedia's minimal runtime ADM1 feature collection."""

    result = gdf[
        [
            "ID_PROV",
            "Provincia",
            "geometry",
        ]
    ].copy()

    result["id"] = (
        result["ID_PROV"]
        .astype(str)
        .str.strip()
        .str.zfill(2)
    )

    result["name"] = (
        result["Provincia"]
        .astype(str)
        .str.strip()
    )

    result["type"] = result["name"].map(
        lambda name: (
            "comarca"
            if name.startswith("Comarca ")
            else "province"
        )
    )

    result = result[
        [
            "id",
            "name",
            "type",
            "geometry",
        ]
    ]

    result = result.sort_values(
        "id",
        kind="stable",
    ).reset_index(drop=True)

    return gpd.GeoDataFrame(
        result,
        geometry="geometry",
        crs=gdf.crs,
    )


def validate_output(gdf: gpd.GeoDataFrame) -> None:
    """Validate the processed GeoJSON before writing it."""

    if len(gdf) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} output features, "
            f"found {len(gdf)}."
        )

    if gdf["id"].nunique() != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Processed province/comarca IDs are not unique."
        )

    if gdf["name"].nunique() != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Processed province/comarca names are not unique."
        )

    expected_types = {
        "province": 10,
        "comarca": 4,
    }

    actual_types = gdf["type"].value_counts().to_dict()

    if actual_types != expected_types:
        raise ValueError(
            "Unexpected province/comarca type counts. "
            f"Expected {expected_types}, found {actual_types}."
        )

    if gdf.geometry.isna().any():
        raise ValueError("Processed data contains null geometries.")

    if gdf.geometry.is_empty.any():
        raise ValueError("Processed data contains empty geometries.")

    if (~gdf.geometry.is_valid).any():
        raise ValueError("Processed data contains invalid geometries.")

    invalid_geometry_types = set(
        gdf.geometry.geom_type.unique()
    ) - {"Polygon", "MultiPolygon"}

    if invalid_geometry_types:
        raise ValueError(
            "Processed data contains unsupported geometry types: "
            + ", ".join(sorted(invalid_geometry_types))
        )


def write_geojson(gdf: gpd.GeoDataFrame) -> None:
    """Write compact UTF-8 GeoJSON to GeoPedia's public data directory."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson = gdf.to_json(
        drop_id=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    OUTPUT_PATH.write_text(
        geojson,
        encoding="utf-8",
    )


def main() -> None:
    """Process Panama's province/comarca boundaries."""

    print("Panama provinces & comarcas processor")
    print("=" * 72)
    print(f"Source: {SOURCE_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    print("Reading source...")
    source = gpd.read_file(SOURCE_PATH)

    validate_source(source)

    print(f"Source features: {len(source)}")
    print(f"Source CRS: {source.crs}")
    print()

    print("Repairing geometries...")
    repaired = repair_geometries(source)
    print()

    print("Simplifying geometries...")
    simplified = simplify_geometries(repaired)
    print()

    print("Building output...")
    output = build_output(simplified)

    validate_output(output)

    print(f"Output features: {len(output)}")
    print()
    print("Features:")

    for row in output.itertuples():
        print(
            f"  {row.id}: {row.name} "
            f"({row.type})"
        )

    print()
    print("Writing GeoJSON...")
    write_geojson(output)

    output_size = OUTPUT_PATH.stat().st_size

    print(
        f"Output size: {output_size / 1024:.1f} KB "
        f"({output_size:,} bytes)"
    )
    print()
    print("Done.")


if __name__ == "__main__":
    main()