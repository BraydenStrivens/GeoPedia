"""
Processes Panama's 2024 district boundaries for GeoPedia.

Source:
    data/raw/countries/panama/
    Panama_Distritos_Boundaries_2024_4679260270347429694.geojson

Output:
    public/data/countries/panama/geojson/districts.geojson

The source contains 82 district-level records. One record, ID 1000 in
Comarca Kuna Yala, represents a hierarchy placeholder named "No asignado"
rather than a normal quiz district.

This processor:

- validates the expected source schema,
- repairs invalid polygon geometries,
- simplifies the source geometry for web use,
- preserves the hierarchy placeholder geometry,
- marks quiz eligibility explicitly,
- keeps only GeoPedia runtime properties,
- validates the processed output,
- writes compact UTF-8 GeoJSON.
"""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


SOURCE_PATH = Path(
    "data/raw/countries/panama/"
    "Panama_Distritos_Boundaries_2024_4679260270347429694.geojson"
)

OUTPUT_PATH = Path(
    "public/data/countries/panama/geojson/districts.geojson"
)

EXPECTED_FEATURE_COUNT = 82
EXPECTED_QUIZ_FEATURE_COUNT = 81

NON_QUIZ_DISTRICT_IDS = {
    "1000",
}

# Roughly 55 meters at Panama's latitude.
#
# ADM2 contains substantially more geometry detail than GeoPedia needs for a
# country-scale district quiz. This keeps boundaries visually accurate while
# dramatically reducing runtime size.
SIMPLIFY_TOLERANCE = 0.0005


def polygonal_only(geometry: BaseGeometry) -> BaseGeometry:
    """
    Return only the polygonal portion of a repaired geometry.

    make_valid() can produce GeometryCollections containing polygons plus
    lower-dimensional artifacts. MapLibre fill layers only need the polygonal
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
        return sum(count_coordinates(part) for part in geometry.geoms)

    if isinstance(geometry, GeometryCollection):
        return sum(count_coordinates(part) for part in geometry.geoms)

    return 0


def validate_source(gdf: gpd.GeoDataFrame) -> None:
    """Validate assumptions GeoPedia relies on from the raw ADM2 source."""

    required_columns = {
        "ID_Distrito",
        "Provincia",
        "Distrito",
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

    ids = gdf["ID_Distrito"].astype(str).str.strip()
    provinces = gdf["Provincia"].astype(str).str.strip()
    names = gdf["Distrito"].astype(str).str.strip()

    if ids.isna().any() or (ids == "").any():
        raise ValueError("Source contains blank district IDs.")

    if provinces.isna().any() or (provinces == "").any():
        raise ValueError("Source contains blank province/comarca names.")

    if names.isna().any() or (names == "").any():
        raise ValueError("Source contains blank district names.")

    if ids.duplicated().any():
        duplicates = sorted(
            ids[ids.duplicated(keep=False)].unique()
        )

        raise ValueError(
            "Source contains duplicate district IDs: "
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
        types = sorted(
            invalid_types.geometry.geom_type.unique()
        )

        raise ValueError(
            "Non-polygonal geometries remain after repair: "
            + ", ".join(types)
        )

    return result


def simplify_geometries(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Simplify district boundaries while preserving polygon topology."""

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
    """Create GeoPedia's minimal runtime district feature collection."""

    result = gdf[
        [
            "ID_Distrito",
            "Provincia",
            "Distrito",
            "geometry",
        ]
    ].copy()

    result["id"] = (
        result["ID_Distrito"]
        .astype(str)
        .str.strip()
        .str.zfill(4)
    )

    result["provinceId"] = result["id"].str[:2]

    result["provinceName"] = (
        result["Provincia"]
        .astype(str)
        .str.strip()
    )

    result["name"] = (
        result["Distrito"]
        .astype(str)
        .str.strip()
    )

    result["quizEligible"] = ~result["id"].isin(
        NON_QUIZ_DISTRICT_IDS
    )

    result = result[
        [
            "id",
            "name",
            "provinceId",
            "provinceName",
            "quizEligible",
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
    """Validate the processed district GeoJSON before writing it."""

    if len(gdf) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} output features, "
            f"found {len(gdf)}."
        )

    if gdf["id"].nunique() != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Processed district IDs are not unique."
        )

    quiz_count = int(gdf["quizEligible"].sum())

    if quiz_count != EXPECTED_QUIZ_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_QUIZ_FEATURE_COUNT} quiz-eligible "
            f"districts, found {quiz_count}."
        )

    non_quiz_ids = set(
        gdf.loc[
            ~gdf["quizEligible"],
            "id",
        ]
    )

    if non_quiz_ids != NON_QUIZ_DISTRICT_IDS:
        raise ValueError(
            "Unexpected non-quiz district IDs. "
            f"Expected {sorted(NON_QUIZ_DISTRICT_IDS)}, "
            f"found {sorted(non_quiz_ids)}."
        )

    placeholder = gdf[
        gdf["id"] == "1000"
    ]

    if len(placeholder) != 1:
        raise ValueError(
            "Expected exactly one Kuna Yala hierarchy placeholder."
        )

    placeholder_name = placeholder.iloc[0]["name"]

    if placeholder_name != "No asignado":
        raise ValueError(
            "Unexpected name for district 1000. "
            f"Found {placeholder_name!r}."
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
    """Process Panama's district boundaries."""

    print("Panama districts processor")
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

    quiz_count = int(output["quizEligible"].sum())

    print(f"Output features: {len(output)}")
    print(f"Quiz-eligible districts: {quiz_count}")
    print(
        "Non-quiz hierarchy placeholders: "
        f"{len(output) - quiz_count}"
    )
    print()

    print("Non-quiz features:")

    for row in output[
        ~output["quizEligible"]
    ].itertuples():
        print(
            f"  {row.id}: {row.name} "
            f"({row.provinceName})"
        )

    print()
    print("District counts by province/comarca:")

    grouped = (
        output[
            output["quizEligible"]
        ]
        .groupby("provinceName")
        .size()
        .sort_index()
    )

    for province_name, count in grouped.items():
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