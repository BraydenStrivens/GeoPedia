"""
Builds Colombia's geographic fixed-line phone-code regions for GeoPedia.

Source:
    public/data/countries/colombia/geojson/departments.geojson

Output:
    public/data/countries/colombia/geojson/phone-codes.geojson

The administrative processor assigns one geographic fixed-line phone code to
each department-level feature. This processor dissolves departments sharing the
same code so the runtime map contains one logical feature per phone-code region.

Department IDs are retained as an array so quiz grouping can still filter phone
codes by the departments they cover.
"""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


SOURCE_PATH = Path(
    "public/data/countries/colombia/geojson/departments.geojson"
)

OUTPUT_PATH = Path(
    "public/data/countries/colombia/geojson/phone-codes.geojson"
)

EXPECTED_DEPARTMENT_COUNT = 33

EXPECTED_PHONE_CODES = {
    "601",
    "602",
    "604",
    "605",
    "606",
    "607",
    "608",
}


def polygonal_only(
    geometry: BaseGeometry,
) -> BaseGeometry:
    """
    Return only the polygonal portion of a geometry.

    Geometry repair can occasionally produce GeometryCollections containing
    lower-dimensional artifacts. GeoPedia's fill layers only require polygonal
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


def validate_source(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Validate the processed department data required by this processor."""
    required_columns = {
        "id",
        "name",
        "phone_code",
        "geometry",
    }

    missing_columns = required_columns - set(gdf.columns)

    if missing_columns:
        raise ValueError(
            "Department source is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if len(gdf) != EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} department features, "
            f"found {len(gdf)}."
        )

    if gdf.crs is None:
        raise ValueError(
            "Department GeoJSON has no CRS."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            "Department GeoJSON contains null geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            "Department GeoJSON contains empty geometries."
        )

    if (~gdf.geometry.is_valid).any():
        raise ValueError(
            "Department GeoJSON contains invalid geometries."
        )

    department_ids = gdf["id"].astype(str).str.strip()

    if department_ids.duplicated().any():
        raise ValueError(
            "Department GeoJSON contains duplicate IDs."
        )

    phone_codes = set(
        gdf["phone_code"]
        .astype(str)
        .str.strip()
        .tolist()
    )

    if phone_codes != EXPECTED_PHONE_CODES:
        missing = sorted(
            EXPECTED_PHONE_CODES - phone_codes
        )

        unexpected = sorted(
            phone_codes - EXPECTED_PHONE_CODES
        )

        raise ValueError(
            "Unexpected Colombia phone-code set. "
            f"Missing: {missing or 'none'}; "
            f"unexpected: {unexpected or 'none'}."
        )


def merge_geometries(
    geometries: list[BaseGeometry],
    region_id: str,
) -> BaseGeometry:
    """
    Merge source polygons into one valid phone-code geometry.

    A phone-code region may remain a MultiPolygon when its departments are not
    geographically contiguous.
    """
    geometry = unary_union(geometries)

    if not geometry.is_valid:
        geometry = geometry.make_valid()

    geometry = polygonal_only(geometry)

    if geometry is None or geometry.is_empty:
        raise ValueError(
            f"Phone code {region_id} produced an empty geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Phone code {region_id} produced an invalid geometry."
        )

    if not isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        raise ValueError(
            f"Phone code {region_id} produced unsupported geometry type "
            f"{geometry.geom_type}."
        )

    return geometry


def build_phone_code_regions(
    departments: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve departments into one feature for each phone code."""
    rows: list[dict] = []

    for phone_code in sorted(EXPECTED_PHONE_CODES):
        matching = departments[
            departments["phone_code"]
            .astype(str)
            .str.strip()
            == phone_code
        ]

        if matching.empty:
            raise ValueError(
                f"No departments found for phone code {phone_code}."
            )

        department_ids = sorted(
            matching["id"]
            .astype(str)
            .str.strip()
            .tolist()
        )

        geometry = merge_geometries(
            matching.geometry.tolist(),
            phone_code,
        )

        rows.append(
            {
                "id": phone_code,
                "phone_code": phone_code,
                "department_ids": department_ids,
                "geometry": geometry,
            }
        )

    result = gpd.GeoDataFrame(
        rows,
        geometry="geometry",
        crs=departments.crs,
    )

    return result


def validate_output(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Validate the completed runtime phone-code regions."""
    if len(gdf) != len(EXPECTED_PHONE_CODES):
        raise ValueError(
            f"Expected {len(EXPECTED_PHONE_CODES)} phone-code regions, "
            f"found {len(gdf)}."
        )

    if gdf["id"].duplicated().any():
        raise ValueError(
            "Phone-code output contains duplicate IDs."
        )

    if set(gdf["id"]) != EXPECTED_PHONE_CODES:
        raise ValueError(
            "Phone-code output does not contain the expected codes."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            "Phone-code output contains null geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            "Phone-code output contains empty geometries."
        )

    if (~gdf.geometry.is_valid).any():
        raise ValueError(
            "Phone-code output contains invalid geometries."
        )

    invalid_types = set(
        gdf.geometry.geom_type.unique()
    ) - {
        "Polygon",
        "MultiPolygon",
    }

    if invalid_types:
        raise ValueError(
            "Phone-code output contains unsupported geometry types: "
            + ", ".join(sorted(invalid_types))
        )


def write_geojson(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Write compact UTF-8 GeoJSON to GeoPedia's runtime data directory."""
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


def print_regions(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Print each phone code and the departments contained within it."""
    print("Phone-code regions:")

    for row in gdf.itertuples():
        department_ids = ", ".join(
            row.department_ids
        )

        print(
            f"  {row.phone_code}: "
            f"{department_ids}"
        )


def main() -> None:
    """Generate Colombia's merged fixed-line phone-code geography."""
    print("Colombia phone-code processor")
    print("=" * 72)
    print(f"Source: {SOURCE_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    print("Reading departments...")
    departments = gpd.read_file(SOURCE_PATH)

    validate_source(departments)

    print(f"Departments: {len(departments)}")
    print()

    print("Merging phone-code regions...")
    output = build_phone_code_regions(
        departments
    )

    validate_output(output)

    print_regions(output)

    print()
    print("Writing GeoJSON...")

    write_geojson(output)

    output_size = OUTPUT_PATH.stat().st_size

    print()
    print(
        f"Phone-code regions: {len(output)}"
    )
    print(
        f"Output size: {output_size / 1024:.1f} KB "
        f"({output_size:,} bytes)"
    )
    print()
    print("Done.")


if __name__ == "__main__":
    main()