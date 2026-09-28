"""
Process Statistics Canada province and territory boundaries for GeoPedia.

Source:
    Statistics Canada 2021 Census province/territory boundary shapefile.

The source shapefile uses the NAD83 Statistics Canada Lambert projection rather
than WGS84 longitude/latitude coordinates.

The original Statistics Canada geometry is far more detailed than GeoPedia
needs for an interactive province/territory quiz. Some provinces contain tens
of thousands of tiny polygon components representing small islands and other
minor land fragments.

Processing pipeline:
    1. Read all 13 province and territory features.
    2. Repair invalid source geometry only when necessary.
    3. Remove polygon components smaller than the configured minimum area.
    4. Simplify remaining geometry in the projected Lambert coordinate system.
    5. Reproject the simplified geometry to WGS84 longitude/latitude.
    6. Repair geometry again only if reprojection introduces invalid topology.
    7. Remove any non-polygonal geometry produced by geometry repair.
    8. Round WGS84 coordinates to reduce unnecessary serialized precision.
    9. Keep only the properties required by GeoPedia.
    10. Add stable GeoJSON feature IDs.
    11. Validate the completed dataset.
    12. Write the final browser-ready GeoJSON file.

Why filtering happens before simplification:
    The source data contains extremely large numbers of tiny polygon components.
    For example, Nunavut contains tens of thousands of separate polygons.
    Simplifying polygons that will later be discarded would waste processing
    time and would not meaningfully reduce the final file size.

Why area filtering happens before reprojection:
    The Statistics Canada Lambert projection expresses coordinates in meters.
    That makes polygon area available in square meters, allowing the filtering
    threshold to represent a meaningful real-world area.

Why simplification happens before reprojection:
    The Lambert projection also allows simplification tolerance to be expressed
    directly in meters instead of approximate geographic degrees.

Geometry repair:
    Some Statistics Canada features contain ring self-intersections in the
    original source geometry. Simplification followed by reprojection can also
    occasionally introduce small topology problems. Invalid geometries are
    repaired individually with Shapely's make_valid() rather than modifying
    every feature.

Output:
    public/data/countries/canada/geojson/provinces.geojson
"""

import json
from pathlib import Path

import shapefile
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import (
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import transform
from shapely.validation import explain_validity


EXPECTED_FEATURE_COUNT = 13

# Remove separate polygon components smaller than this area.
#
# Statistics Canada's source data contains tens of thousands of tiny islands
# that add substantial file size but provide little value at province-quiz
# scale.
#
# A 5 km² threshold retains meaningful islands and coastline structure while
# eliminating the overwhelming majority of insignificant components.
MIN_POLYGON_AREA_KM2 = 5
MIN_POLYGON_AREA_M2 = (
    MIN_POLYGON_AREA_KM2 * 1_000_000
)

# Simplification occurs while coordinates are still expressed in meters.
#
# A 5 km tolerance is appropriate for a Canada-wide province/territory quiz,
# where sub-kilometer coastline detail is not useful for identifying regions.
SIMPLIFY_TOLERANCE_METERS = 5000

# WGS84 coordinates do not require full Python floating-point precision.
#
# Five decimal places provides roughly meter-level coordinate precision, which
# is already significantly more precise than the simplified quiz geometry.
COORDINATE_DECIMAL_PLACES = 5

PROJECT_ROOT = Path.cwd()

INPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "canada"
    / "statcan"
    / "lpr_000b21a_e"
)

INPUT_SHAPEFILE = (
    INPUT_DIRECTORY
    / "lpr_000b21a_e.shp"
)

INPUT_PROJECTION = (
    INPUT_DIRECTORY
    / "lpr_000b21a_e.prj"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "canada"
    / "geojson"
    / "provinces.geojson"
)


def validate_input_files() -> None:
    """
    Verify that all required Statistics Canada source files exist.
    """

    if not INPUT_SHAPEFILE.exists():
        raise FileNotFoundError(
            f"Shapefile not found: {INPUT_SHAPEFILE}"
        )

    if not INPUT_PROJECTION.exists():
        raise FileNotFoundError(
            f"Projection file not found: {INPUT_PROJECTION}"
        )


def read_source_crs() -> CRS:
    """
    Read the source coordinate reference system from the StatCan PRJ file.

    Returns:
        CRS:
            Parsed Statistics Canada source coordinate reference system.
    """

    projection_text = INPUT_PROJECTION.read_text(
        encoding="utf-8"
    )

    return CRS.from_wkt(projection_text)


def repair_geometry_if_needed(
    geometry,
    feature_name: str,
    stage: str,
):
    """
    Repair a geometry only when it is invalid.

    Valid geometries are returned unchanged.

    Args:
        geometry:
            Shapely geometry to validate.

        feature_name:
            Human-readable province or territory name used in log and error
            messages.

        stage:
            Description of the processing stage at which validation occurs.

    Returns:
        The original geometry when valid, otherwise a repaired geometry.

    Raises:
        ValueError:
            If the geometry is empty or remains invalid after repair.
    """

    if geometry.is_empty:
        raise ValueError(
            f"{feature_name} has empty geometry during {stage}."
        )

    if geometry.is_valid:
        return geometry

    validity_error = explain_validity(geometry)

    print(
        f"⚠ {feature_name} has invalid geometry during {stage}: "
        f"{validity_error}"
    )

    repaired_geometry = make_valid(geometry)

    if repaired_geometry.is_empty:
        raise ValueError(
            f"{feature_name} has empty geometry after repair "
            f"during {stage}."
        )

    if not repaired_geometry.is_valid:
        raise ValueError(
            f"{feature_name} is still invalid after repair "
            f"during {stage}: "
            f"{explain_validity(repaired_geometry)}"
        )

    print(
        f"✓ Repaired geometry for {feature_name} during {stage}."
    )

    return repaired_geometry


def extract_polygon_components(geometry) -> list[Polygon]:
    """
    Extract all polygon components from a Shapely geometry.

    make_valid() can return Polygon, MultiPolygon, or GeometryCollection
    geometries. GeoPedia only needs polygonal geometry for map regions.

    Args:
        geometry:
            Geometry from which polygon components should be extracted.

    Returns:
        list[Polygon]:
            All Polygon components found recursively within the geometry.
    """

    if isinstance(geometry, Polygon):
        return [geometry]

    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)

    if hasattr(geometry, "geoms"):
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            polygons.extend(
                extract_polygon_components(part)
            )

        return polygons

    return []


def build_polygon_geometry(
    polygons: list[Polygon],
    feature_name: str,
):
    """
    Rebuild a Polygon or MultiPolygon from polygon components.

    Args:
        polygons:
            Polygon components to combine.

        feature_name:
            Human-readable province or territory name used in error messages.

    Returns:
        Polygon | MultiPolygon:
            Polygon when exactly one component remains, otherwise MultiPolygon.

    Raises:
        ValueError:
            If no polygon components remain.
    """

    if not polygons:
        raise ValueError(
            f"{feature_name} has no polygon components remaining."
        )

    if len(polygons) == 1:
        return polygons[0]

    return MultiPolygon(polygons)


def filter_small_polygon_components(
    geometry,
    feature_name: str,
):
    """
    Remove polygon components smaller than the configured minimum area.

    Area is evaluated while the geometry remains in the Statistics Canada
    Lambert projection, where coordinates are measured in meters and polygon
    area is therefore measured in square meters.

    Args:
        geometry:
            Source polygonal geometry.

        feature_name:
            Human-readable province or territory name.

    Returns:
        Polygon | MultiPolygon:
            Geometry containing only polygon components whose area meets the
            configured minimum.

    Raises:
        ValueError:
            If no qualifying polygon components remain.
    """

    polygons = extract_polygon_components(
        geometry
    )

    retained_polygons = [
        polygon
        for polygon in polygons
        if polygon.area >= MIN_POLYGON_AREA_M2
    ]

    if not retained_polygons:
        raise ValueError(
            f"{feature_name} has no polygon components at or above "
            f"{MIN_POLYGON_AREA_KM2} km²."
        )

    return build_polygon_geometry(
        retained_polygons,
        feature_name,
    )


def simplify_geometry(
    geometry,
    feature_name: str,
):
    """
    Simplify polygon geometry while preserving topology.

    Simplification occurs in the source Lambert projection so the configured
    tolerance is expressed in meters.

    Args:
        geometry:
            Polygonal source geometry.

        feature_name:
            Human-readable province or territory name.

    Returns:
        Simplified geometry.

    Raises:
        ValueError:
            If simplification produces empty or invalid geometry.
    """

    simplified_geometry = geometry.simplify(
        SIMPLIFY_TOLERANCE_METERS,
        preserve_topology=True,
    )

    if simplified_geometry.is_empty:
        raise ValueError(
            f"{feature_name} has empty geometry after simplification."
        )

    if not simplified_geometry.is_valid:
        raise ValueError(
            f"{feature_name} has invalid geometry after simplification: "
            f"{explain_validity(simplified_geometry)}"
        )

    return simplified_geometry


def keep_polygonal_geometry(
    geometry,
    feature_name: str,
):
    """
    Remove non-polygonal parts from a geometry.

    Geometry repair can produce GeometryCollection values containing polygons
    alongside lines or points. Only polygonal geometry should be written to
    the final GeoJSON region dataset.

    Args:
        geometry:
            Geometry to normalize.

        feature_name:
            Human-readable province or territory name.

    Returns:
        Polygon | MultiPolygon:
            Polygon-only geometry.

    Raises:
        ValueError:
            If no polygon components remain.
    """

    polygons = extract_polygon_components(
        geometry
    )

    return build_polygon_geometry(
        polygons,
        feature_name,
    )


def round_coordinates(value):
    """
    Recursively round GeoJSON coordinate values.

    Args:
        value:
            Nested GeoJSON coordinate structure or individual numeric value.

    Returns:
        Coordinate structure with floating-point values rounded to the
        configured number of decimal places.
    """

    if isinstance(value, float):
        return round(
            value,
            COORDINATE_DECIMAL_PLACES,
        )

    if isinstance(value, tuple):
        return [
            round_coordinates(item)
            for item in value
        ]

    if isinstance(value, list):
        return [
            round_coordinates(item)
            for item in value
        ]

    return value


def geometry_to_rounded_geojson(
    geometry,
) -> dict:
    """
    Convert a Shapely geometry to GeoJSON and round its coordinates.

    Args:
        geometry:
            Final WGS84 polygonal geometry.

    Returns:
        dict:
            GeoJSON geometry object with rounded coordinates.
    """

    geojson_geometry = mapping(
        geometry
    )

    return {
        "type": geojson_geometry["type"],
        "coordinates": round_coordinates(
            geojson_geometry["coordinates"]
        ),
    }


def main() -> None:
    """
    Process the Statistics Canada province and territory dataset.
    """

    print(
        "Processing Canada Provinces and Territories..."
    )

    validate_input_files()

    source_crs = read_source_crs()

    transformer = Transformer.from_crs(
        source_crs,
        CRS.from_epsg(4326),
        always_xy=True,
    )

    reader = shapefile.Reader(
        str(INPUT_SHAPEFILE),
        encoding="cp1252",
    )

    print(
        f"Found {len(reader)} features."
    )

    if len(reader) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} provinces and territories "
            f"but found {len(reader)} features."
        )

    field_names = [
        field[0]
        for field in reader.fields[1:]
    ]

    processed_features = []

    province_ids: set[str] = set()
    province_names: set[str] = set()

    total_source_components = 0
    total_retained_components = 0

    for shape_record in reader.iterShapeRecords():
        properties = dict(
            zip(
                field_names,
                shape_record.record,
            )
        )

        pruid = properties.get(
            "PRUID"
        )
        name = properties.get(
            "PRENAME"
        )
        abbreviation = properties.get(
            "PREABBR"
        )

        if not pruid:
            raise ValueError(
                "Encountered a province or territory without PRUID."
            )

        if not name:
            raise ValueError(
                f"Province or territory {pruid} is missing PRENAME."
            )

        if not abbreviation:
            raise ValueError(
                f"{name} is missing PREABBR."
            )

        if pruid in province_ids:
            raise ValueError(
                f"Duplicate PRUID found: {pruid}"
            )

        if name in province_names:
            raise ValueError(
                f"Duplicate province or territory name found: {name}"
            )

        province_ids.add(
            pruid
        )
        province_names.add(
            name
        )

        source_geometry = shape(
            shape_record.shape.__geo_interface__
        )

        source_geometry = repair_geometry_if_needed(
            source_geometry,
            name,
            "source validation",
        )

        source_components = extract_polygon_components(
            source_geometry
        )

        if not source_components:
            raise ValueError(
                f"{name} has no polygon components in the source geometry."
            )

        source_component_count = len(
            source_components
        )

        total_source_components += (
            source_component_count
        )

        filtered_geometry = (
            filter_small_polygon_components(
                source_geometry,
                name,
            )
        )

        retained_component_count = len(
            extract_polygon_components(
                filtered_geometry
            )
        )

        total_retained_components += (
            retained_component_count
        )

        simplified_geometry = simplify_geometry(
            filtered_geometry,
            name,
        )

        projected_geometry = transform(
            transformer.transform,
            simplified_geometry,
        )

        projected_geometry = repair_geometry_if_needed(
            projected_geometry,
            name,
            "WGS84 reprojection",
        )

        projected_geometry = keep_polygonal_geometry(
            projected_geometry,
            name,
        )

        if projected_geometry.is_empty:
            raise ValueError(
                f"{name} has empty final geometry."
            )

        if not projected_geometry.is_valid:
            raise ValueError(
                f"{name} has invalid final geometry: "
                f"{explain_validity(projected_geometry)}"
            )

        print(
            f"  {name}: "
            f"{source_component_count:,} → "
            f"{retained_component_count:,} polygon components"
        )

        processed_features.append(
            {
                "type": "Feature",
                "id": pruid,
                "properties": {
                    "pruid": pruid,
                    "name": name,
                    "abbreviation": abbreviation,
                },
                "geometry": (
                    geometry_to_rounded_geojson(
                        projected_geometry
                    )
                ),
            }
        )

    if len(processed_features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} processed features "
            f"but found {len(processed_features)}."
        )

    if len(province_ids) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} unique PRUID values "
            f"but found {len(province_ids)}."
        )

    if len(province_names) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} unique province and "
            f"territory names but found {len(province_names)}."
        )

    processed = {
        "type": "FeatureCollection",
        "features": processed_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            processed,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    output_size_bytes = (
        OUTPUT_PATH.stat().st_size
    )

    output_size_kb = (
        output_size_bytes / 1024
    )

    output_size_mb = (
        output_size_kb / 1024
    )

    print("")
    print(
        f"✓ Found exactly {EXPECTED_FEATURE_COUNT} "
        "provinces and territories."
    )
    print(
        "✓ All features have names."
    )
    print(
        "✓ All features have abbreviations."
    )
    print(
        "✓ All PRUID values are unique."
    )
    print(
        "✓ All province and territory names are unique."
    )
    print(
        f"✓ Removed polygon components smaller than "
        f"{MIN_POLYGON_AREA_KM2} km²."
    )
    print(
        f"✓ Reduced polygon components from "
        f"{total_source_components:,} to "
        f"{total_retained_components:,}."
    )
    print(
        f"✓ Simplified geometry with a "
        f"{SIMPLIFY_TOLERANCE_METERS:,} meter tolerance."
    )
    print(
        "✓ Reprojected geometry to WGS84."
    )
    print(
        "✓ Kept polygonal geometry only."
    )
    print(
        f"✓ Rounded coordinates to "
        f"{COORDINATE_DECIMAL_PLACES} decimal places."
    )
    print(
        "✓ Validated final geometry."
    )
    print(
        "✓ Added stable GeoJSON feature IDs."
    )
    print(
        "✓ Removed unused Statistics Canada properties."
    )
    print("")
    print(
        "✓ Saved processed data to:"
    )
    print(
        f"  {OUTPUT_PATH}"
    )
    print(
        f"✓ Final file size: "
        f"{output_size_kb:,.0f} KB "
        f"({output_size_mb:.2f} MB)"
    )


if __name__ == "__main__":
    main()