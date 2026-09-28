"""
Processes Panama's 2024 corregimiento boundaries for GeoPedia.

Source:
    data/raw/countries/panama/
    Panama_Corregimientos_Boundaries_2024_-2164041707231143700.geojson

Output:
    public/data/countries/panama/geojson/corregimientos.geojson

The source contains 699 polygon records representing 698 unique
corregimiento IDs. Multiple records sharing an ID represent separate geometry
pieces of the same administrative unit and are dissolved into one feature.

This processor:

- validates the expected source schema,
- verifies that duplicate IDs have consistent administrative metadata,
- dissolves multipart records by corregimiento ID,
- repairs invalid polygon geometries,
- simplifies the detailed source geometry for web use,
- preserves province and district hierarchy information,
- keeps only GeoPedia runtime properties,
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
    "Panama_Corregimientos_Boundaries_2024_-2164041707231143700.geojson"
)

OUTPUT_PATH = Path(
    "public/data/countries/panama/geojson/corregimientos.geojson"
)

EXPECTED_SOURCE_FEATURE_COUNT = 699
EXPECTED_CORREGIMIENTO_COUNT = 698

# Roughly 28 meters at Panama's latitude.
#
# Corregimientos are considerably smaller than provinces or districts, so a
# more conservative tolerance is used to retain useful local boundary detail.
SIMPLIFY_TOLERANCE = 0.00025


def polygonal_only(geometry: BaseGeometry) -> BaseGeometry:
    """
    Return only the polygonal portion of a repaired geometry.

    make_valid() can produce GeometryCollections containing polygons plus
    lower-dimensional artifacts. MapLibre fill layers only need polygonal
    components.
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
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    if isinstance(geometry, GeometryCollection):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    return 0


def validate_source(gdf: gpd.GeoDataFrame) -> None:
    """Validate assumptions GeoPedia relies on from the raw ADM3 source."""

    required_columns = {
        "ID_CORR",
        "Provincia",
        "Distrito",
        "Corregimiento",
        "geometry",
    }

    missing_columns = required_columns - set(gdf.columns)

    if missing_columns:
        raise ValueError(
            "Source is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if len(gdf) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} source features, "
            f"found {len(gdf)}."
        )

    ids = gdf["ID_CORR"].astype(str).str.strip()
    provinces = gdf["Provincia"].astype(str).str.strip()
    districts = gdf["Distrito"].astype(str).str.strip()
    names = gdf["Corregimiento"].astype(str).str.strip()

    for field_name, values in (
        ("corregimiento ID", ids),
        ("province/comarca name", provinces),
        ("district name", districts),
        ("corregimiento name", names),
    ):
        if values.isna().any() or (values == "").any():
            raise ValueError(
                f"Source contains blank {field_name} values."
            )

    if ids.nunique() != EXPECTED_CORREGIMIENTO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CORREGIMIENTO_COUNT} unique "
            f"corregimiento IDs, found {ids.nunique()}."
        )

    invalid_ids = ids[
        ~ids.str.fullmatch(r"\d{6}")
    ]

    if not invalid_ids.empty:
        raise ValueError(
            "Source contains malformed corregimiento IDs: "
            + ", ".join(sorted(invalid_ids.unique()))
        )

    if gdf.crs is None:
        raise ValueError("Source GeoJSON has no CRS.")

    if gdf.geometry.isna().any():
        raise ValueError("Source contains null geometries.")

    if gdf.geometry.is_empty.any():
        raise ValueError("Source contains empty geometries.")


def validate_duplicate_metadata(
    gdf: gpd.GeoDataFrame,
) -> None:
    """
    Verify that records sharing an ID describe the same administrative unit.

    Duplicate IDs may legitimately represent separate polygon pieces, but
    their province, district, and corregimiento names must agree before those
    geometries can safely be dissolved.
    """

    ids = gdf["ID_CORR"].astype(str).str.strip()

    duplicate_ids = sorted(
        ids[
            ids.duplicated(keep=False)
        ].unique()
    )

    print(f"Duplicated IDs before dissolve: {len(duplicate_ids)}")

    if not duplicate_ids:
        print("  None")
        return

    for corregimiento_id in duplicate_ids:
        rows = gdf[
            ids == corregimiento_id
        ]

        metadata = rows[
            [
                "Provincia",
                "Distrito",
                "Corregimiento",
            ]
        ].astype(str).apply(
            lambda column: column.str.strip()
        )

        unique_metadata = metadata.drop_duplicates()

        if len(unique_metadata) != 1:
            raise ValueError(
                "Cannot safely dissolve ID "
                f"{corregimiento_id}: administrative metadata differs "
                "between its source records."
            )

        row = unique_metadata.iloc[0]

        print(
            f"  {corregimiento_id}: "
            f"{row['Corregimiento']} "
            f"({row['Distrito']}, {row['Provincia']}) "
            f"- {len(rows)} geometry pieces"
        )


def repair_geometries(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Repair invalid source geometry and retain polygonal components only."""

    result = gdf.copy()

    invalid_before = int(
        (~result.geometry.is_valid).sum()
    )

    print(f"Invalid geometries before repair: {invalid_before}")

    result.geometry = result.geometry.make_valid()
    result.geometry = result.geometry.map(polygonal_only)

    if result.geometry.isna().any():
        raise ValueError(
            "Geometry repair produced null geometries."
        )

    if result.geometry.is_empty.any():
        raise ValueError(
            "Geometry repair produced empty geometries."
        )

    invalid_after = int(
        (~result.geometry.is_valid).sum()
    )

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
        types = sorted(
            invalid_types.geometry.geom_type.unique()
        )

        raise ValueError(
            "Non-polygonal geometries remain after repair: "
            + ", ".join(types)
        )

    return result


def dissolve_corregimientos(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve multiple geometry records belonging to the same ID."""

    result = gdf.copy()

    result["ID_CORR"] = (
        result["ID_CORR"]
        .astype(str)
        .str.strip()
    )

    for column in (
        "Provincia",
        "Distrito",
        "Corregimiento",
    ):
        result[column] = (
            result[column]
            .astype(str)
            .str.strip()
        )

    dissolved = result.dissolve(
        by="ID_CORR",
        aggfunc={
            "Provincia": "first",
            "Distrito": "first",
            "Corregimiento": "first",
        },
        as_index=False,
    )

    dissolved = gpd.GeoDataFrame(
        dissolved,
        geometry="geometry",
        crs=gdf.crs,
    )

    print(f"Features before dissolve: {len(gdf)}")
    print(f"Features after dissolve:  {len(dissolved)}")

    if len(dissolved) != EXPECTED_CORREGIMIENTO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CORREGIMIENTO_COUNT} features "
            f"after dissolve, found {len(dissolved)}."
        )

    return dissolved


def simplify_geometries(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Simplify corregimiento boundaries while preserving polygon topology."""

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

    print(
        f"Coordinates before simplification: "
        f"{coordinates_before:,}"
    )
    print(
        f"Coordinates after simplification:  "
        f"{coordinates_after:,}"
    )

    if coordinates_before:
        reduction = (
            1 - coordinates_after / coordinates_before
        ) * 100

        print(f"Coordinate reduction: {reduction:.1f}%")

    if result.geometry.isna().any():
        raise ValueError(
            "Simplification produced null geometries."
        )

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
    """Create GeoPedia's minimal runtime corregimiento collection."""

    result = gdf[
        [
            "ID_CORR",
            "Provincia",
            "Distrito",
            "Corregimiento",
            "geometry",
        ]
    ].copy()

    result["id"] = (
        result["ID_CORR"]
        .astype(str)
        .str.strip()
        .str.zfill(6)
    )

    # Panama's hierarchical IDs encode the parent district in the first
    # four digits and the province/comarca in the first two digits.
    result["districtId"] = result["id"].str[:4]
    result["provinceId"] = result["id"].str[:2]

    result["provinceName"] = (
        result["Provincia"]
        .astype(str)
        .str.strip()
    )

    result["districtName"] = (
        result["Distrito"]
        .astype(str)
        .str.strip()
    )

    result["name"] = (
        result["Corregimiento"]
        .astype(str)
        .str.strip()
    )

    result = result[
        [
            "id",
            "name",
            "districtId",
            "districtName",
            "provinceId",
            "provinceName",
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


def validate_output(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Validate the processed corregimiento GeoJSON before writing it."""

    if len(gdf) != EXPECTED_CORREGIMIENTO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CORREGIMIENTO_COUNT} output features, "
            f"found {len(gdf)}."
        )

    if gdf["id"].nunique() != EXPECTED_CORREGIMIENTO_COUNT:
        raise ValueError(
            "Processed corregimiento IDs are not unique."
        )

    if gdf["id"].duplicated().any():
        raise ValueError(
            "Processed data still contains duplicate IDs."
        )

    malformed_ids = gdf[
        ~gdf["id"].str.fullmatch(r"\d{6}")
    ]

    if not malformed_ids.empty:
        raise ValueError(
            "Processed data contains malformed IDs."
        )

    expected_district_ids = gdf["id"].str[:4]

    if not (
        gdf["districtId"] == expected_district_ids
    ).all():
        raise ValueError(
            "One or more district IDs do not match their "
            "corregimiento hierarchy."
        )

    expected_province_ids = gdf["id"].str[:2]

    if not (
        gdf["provinceId"] == expected_province_ids
    ).all():
        raise ValueError(
            "One or more province IDs do not match their "
            "corregimiento hierarchy."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            "Processed data contains null geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            "Processed data contains empty geometries."
        )

    if (~gdf.geometry.is_valid).any():
        raise ValueError(
            "Processed data contains invalid geometries."
        )

    invalid_geometry_types = set(
        gdf.geometry.geom_type.unique()
    ) - {"Polygon", "MultiPolygon"}

    if invalid_geometry_types:
        raise ValueError(
            "Processed data contains unsupported geometry types: "
            + ", ".join(sorted(invalid_geometry_types))
        )


def print_duplicate_names(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Print repeated names that the quiz config may need to disambiguate."""

    duplicate_names = sorted(
        gdf.loc[
            gdf["name"].duplicated(keep=False),
            "name",
        ].unique()
    )

    print(f"Repeated corregimiento names: {len(duplicate_names)}")

    if not duplicate_names:
        print("  None")
        return

    for name in duplicate_names:
        rows = gdf[
            gdf["name"] == name
        ]

        print()
        print(f"  {name}:")

        for row in rows.itertuples():
            print(
                f"    {row.id}: "
                f"{row.districtName}, {row.provinceName}"
            )


def write_geojson(
    gdf: gpd.GeoDataFrame,
) -> None:
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
    """Process Panama's corregimiento boundaries."""

    print("Panama corregimientos processor")
    print("=" * 72)
    print(f"Source: {SOURCE_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    print("Reading source...")
    source = gpd.read_file(SOURCE_PATH)

    validate_source(source)

    print(f"Source features: {len(source)}")
    print(
        "Unique source IDs: "
        f"{source['ID_CORR'].astype(str).str.strip().nunique()}"
    )
    print(f"Source CRS: {source.crs}")
    print()

    print("Checking duplicate IDs...")
    validate_duplicate_metadata(source)
    print()

    print("Repairing geometries...")
    repaired = repair_geometries(source)
    print()

    print("Dissolving multipart records...")
    dissolved = dissolve_corregimientos(repaired)
    print()

    print("Simplifying geometries...")
    simplified = simplify_geometries(dissolved)
    print()

    print("Building output...")
    output = build_output(simplified)

    validate_output(output)

    print(f"Output features: {len(output)}")
    print()

    print_duplicate_names(output)

    print()
    print("Corregimiento counts by province/comarca:")

    province_counts = (
        output.groupby("provinceName")
        .size()
        .sort_index()
    )

    for province_name, count in province_counts.items():
        print(f"  {province_name}: {count}")

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