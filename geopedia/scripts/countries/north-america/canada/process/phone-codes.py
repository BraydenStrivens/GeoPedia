"""
Process Canada's legacy telephone area-code regions for GeoPedia.

Source:
    GeoJSON used by HelloQuiz's Canada phone-code quiz.

    data/raw/countries/canada/helloquiz/phone-codes.geojson

The source contains 19 geographically distinct legacy Canadian area-code
regions that are useful for GeoGuessr-style geographic learning.

Modern overlay area codes are intentionally not represented because they
occupy the same geographic regions as older area codes and therefore do not
provide additional geographic information for this quiz.

The source GeoJSON stores only:

    {
        "AreaCode": "403"
    }

GeoPedia normalizes each feature to:

    {
        "area_code": "403",
        "provinces": ["AB"]
    }

The `provinces` property is always stored as a string array because some
telephone regions span multiple provinces or territories.

Examples:

    902 -> ["NS", "PE"]

    867 -> ["YT", "NT", "NU"]

Using a consistent array shape allows GeoPedia's existing `string-array`
property-grouping system to include a telephone region under every province
or territory it intersects.

Processing pipeline:
    1. Read and structurally validate the source GeoJSON.
    2. Verify that exactly the expected 19 legacy area codes are present.
    3. Convert each feature to Shapely geometry.
    4. Repair invalid source geometry only when necessary.
    5. Reproject WGS84 geometry to Statistics Canada Lambert (EPSG:3347).
    6. Remove separate polygon components smaller than 5 km².
    7. Simplify geometry using a 1,500 meter tolerance.
    8. Repair simplified geometry only when necessary.
    9. Keep polygonal geometry only.
    10. Reproject the result to WGS84.
    11. Round coordinates to five decimal places.
    12. Replace source properties with GeoPedia's normalized runtime properties.
    13. Add the area code as a stable GeoJSON feature ID.
    14. Validate the completed dataset.
    15. Write minified browser-ready GeoJSON.

Why geometry is projected before filtering and simplification:
    The source is WGS84 longitude/latitude GeoJSON. Geographic degrees are not
    suitable units for meaningful area or distance thresholds.

    EPSG:3347 expresses Canadian geography in meters, allowing the polygon-area
    threshold to use square meters and the simplification tolerance to use
    meters.

Why small polygon components are removed:
    The source contains many small coastal and island fragments. Very small
    components add file size and rendering work while providing little value
    when identifying large telephone regions on a Canada-wide quiz map.

Why the simplification tolerance is 1,500 meters:
    Telephone regions can have meaningful internal boundaries around populated
    parts of Canada, so they benefit from somewhat greater boundary precision
    than broad province-level geography.

    A 1.5 km tolerance substantially reduces geometry size while preserving the
    recognizable shape and relative position of the 19 regions.

Output:
    public/data/countries/canada/geojson/phone-codes.geojson
"""

import json
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import transform
from shapely.validation import explain_validity


# ---------------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 19

EXPECTED_AREA_CODES = {
    "204",
    "250",
    "306",
    "403",
    "416",
    "418",
    "450",
    "506",
    "514",
    "519",
    "604",
    "613",
    "705",
    "709",
    "780",
    "819",
    "867",
    "902",
    "905",
}


# ---------------------------------------------------------------------------
# Province / territory membership
# ---------------------------------------------------------------------------

"""
Province and territory abbreviations represented by each legacy telephone
area-code region.

The values intentionally use compact Canadian postal abbreviations. Quiz
configuration can map these raw values to full user-facing names through
`valueLabels`.

Every value is stored as a tuple here even when an area code belongs to only
one province. This mirrors the final GeoJSON's consistent string-array shape.
"""
PROVINCES_BY_AREA_CODE: dict[str, tuple[str, ...]] = {
    "204": ("MB",),
    "250": ("BC",),
    "306": ("SK",),
    "403": ("AB",),
    "416": ("ON",),
    "418": ("QC",),
    "450": ("QC",),
    "506": ("NB",),
    "514": ("QC",),
    "519": ("ON",),
    "604": ("BC",),
    "613": ("ON",),
    "705": ("ON",),
    "709": ("NL",),
    "780": ("AB",),
    "819": ("QC",),
    "867": ("YT", "NT", "NU"),
    "902": ("NS", "PE"),
    "905": ("ON",),
}

EXPECTED_PROVINCES = {
    "AB",
    "BC",
    "MB",
    "NB",
    "NL",
    "NS",
    "NT",
    "NU",
    "ON",
    "PE",
    "QC",
    "SK",
    "YT",
}


# ---------------------------------------------------------------------------
# Geometry settings
# ---------------------------------------------------------------------------

# Remove separate polygon components smaller than this area.
#
# Small coastal islands add substantial geometry detail without meaningfully
# improving a Canada-wide telephone-region quiz.
MIN_POLYGON_AREA_KM2 = 5

MIN_POLYGON_AREA_M2 = MIN_POLYGON_AREA_KM2 * 1_000_000


# Simplification happens after projection to EPSG:3347, where coordinates are
# expressed in meters.
#
# A 1.5 km tolerance keeps telephone-region boundaries more precise than the
# broader province map while substantially reducing runtime geometry size.
SIMPLIFY_TOLERANCE_METERS = 1_500


# Five decimal places is substantially more precise than the simplified source
# geometry requires while avoiding unnecessary floating-point serialization.
COORDINATE_DECIMAL_PLACES = 5


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path.cwd()

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "canada"
    / "helloquiz"
    / "phone-codes.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "canada"
    / "geojson"
    / "phone-codes.geojson"
)


# ---------------------------------------------------------------------------
# Coordinate transformations
# ---------------------------------------------------------------------------

# HelloQuiz's GeoJSON uses normal WGS84 longitude/latitude coordinates.
WGS84_CRS = "EPSG:4326"

# Statistics Canada Lambert provides meter-based coordinates suitable for
# Canada-wide distance and area operations.
CANADA_LAMBERT_CRS = "EPSG:3347"

TO_PROJECTED = Transformer.from_crs(
    WGS84_CRS,
    CANADA_LAMBERT_CRS,
    always_xy=True,
)

TO_WGS84 = Transformer.from_crs(
    CANADA_LAMBERT_CRS,
    WGS84_CRS,
    always_xy=True,
)


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------


def validate_input_file() -> None:
    """
    Verify that the expected source GeoJSON exists.
    """

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Canada phone-code source GeoJSON was not found:\n"
            f"  {INPUT_PATH}"
        )


def read_source_geojson() -> dict[str, Any]:
    """
    Read the source GeoJSON from disk.

    Returns:
        dict[str, Any]:
            Parsed source GeoJSON object.
    """

    with INPUT_PATH.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def validate_source_structure(
    source_geojson: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Validate the basic structure and expected contents of the source dataset.

    Args:
        source_geojson:
            Parsed HelloQuiz source GeoJSON.

    Returns:
        list[dict[str, Any]]:
            Validated source feature list.

    Raises:
        ValueError:
            If the source is malformed, contains unexpected area codes, has
            duplicate area codes, or does not contain exactly 19 features.
    """

    if source_geojson.get("type") != "FeatureCollection":
        raise ValueError(
            "Source GeoJSON must have type 'FeatureCollection'."
        )

    features = source_geojson.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Source GeoJSON must contain a 'features' array."
        )

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected Canada phone-code feature count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(features)}."
        )

    discovered_codes: list[str] = []

    for feature_index, feature in enumerate(features):
        if feature.get("type") != "Feature":
            raise ValueError(
                f"Source feature {feature_index} is not a GeoJSON Feature."
            )

        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Source feature {feature_index} has invalid properties."
            )

        area_code = properties.get("AreaCode")

        if not isinstance(area_code, str) or not area_code.strip():
            raise ValueError(
                f"Source feature {feature_index} is missing AreaCode."
            )

        area_code = area_code.strip()

        if area_code not in EXPECTED_AREA_CODES:
            raise ValueError(
                f"Unexpected source area code: {area_code}"
            )

        geometry = feature.get("geometry")

        if not isinstance(geometry, dict):
            raise ValueError(
                f"Area code {area_code} has no valid geometry object."
            )

        discovered_codes.append(area_code)

    if len(set(discovered_codes)) != len(discovered_codes):
        duplicate_codes = sorted(
            {
                area_code
                for area_code in discovered_codes
                if discovered_codes.count(area_code) > 1
            }
        )

        raise ValueError(
            "Duplicate source area codes found: "
            + ", ".join(duplicate_codes)
        )

    discovered_code_set = set(discovered_codes)

    missing_codes = EXPECTED_AREA_CODES - discovered_code_set
    unexpected_codes = discovered_code_set - EXPECTED_AREA_CODES

    if missing_codes:
        raise ValueError(
            "Source is missing expected area codes: "
            + ", ".join(sorted(missing_codes))
        )

    if unexpected_codes:
        raise ValueError(
            "Source contains unexpected area codes: "
            + ", ".join(sorted(unexpected_codes))
        )

    return features


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def repair_geometry_if_needed(
    geometry,
    area_code: str,
    stage: str,
):
    """
    Repair a geometry only when it is invalid.

    Valid geometries pass through unchanged so processing does not alter them
    unnecessarily.

    Args:
        geometry:
            Shapely geometry to inspect.

        area_code:
            Telephone area code used in diagnostics.

        stage:
            Human-readable processing stage.

    Returns:
        BaseGeometry:
            Original valid geometry or repaired geometry.

    Raises:
        ValueError:
            If geometry remains invalid or becomes empty after repair.
    """

    if geometry.is_empty:
        raise ValueError(
            f"Area code {area_code} has empty geometry during {stage}."
        )

    if geometry.is_valid:
        return geometry

    print(
        f"⚠ {area_code} has invalid geometry during {stage}: "
        f"{explain_validity(geometry)}"
    )

    repaired_geometry = make_valid(geometry)

    if repaired_geometry.is_empty:
        raise ValueError(
            f"Geometry repair produced empty geometry for "
            f"{area_code} during {stage}."
        )

    if not repaired_geometry.is_valid:
        raise ValueError(
            f"Could not repair geometry for {area_code} during {stage}: "
            f"{explain_validity(repaired_geometry)}"
        )

    print(
        f"✓ Repaired geometry for {area_code} during {stage}."
    )

    return repaired_geometry


def keep_polygonal_geometry(geometry):
    """
    Remove non-polygonal components from a Shapely geometry.

    `make_valid()` may occasionally produce GeometryCollections containing
    lines in addition to valid polygons. GeoPedia's feature maps require only
    polygonal geometry.

    Args:
        geometry:
            Shapely geometry to normalize.

    Returns:
        Polygon | MultiPolygon:
            Polygonal portion of the geometry.

    Raises:
        ValueError:
            If no polygonal geometry remains.
    """

    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []

        for component in geometry.geoms:
            if isinstance(component, Polygon):
                polygons.append(component)

            elif isinstance(component, MultiPolygon):
                polygons.extend(component.geoms)

        if not polygons:
            raise ValueError(
                "GeometryCollection contains no polygonal geometry."
            )

        if len(polygons) == 1:
            return polygons[0]

        return MultiPolygon(polygons)

    raise ValueError(
        f"Unsupported geometry type: {geometry.geom_type}"
    )


def get_polygon_components(geometry) -> list[Polygon]:
    """
    Return every individual Polygon contained by polygonal geometry.

    Args:
        geometry:
            Polygon or MultiPolygon geometry.

    Returns:
        list[Polygon]:
            Individual polygon components.
    """

    polygonal_geometry = keep_polygonal_geometry(geometry)

    if isinstance(polygonal_geometry, Polygon):
        return [polygonal_geometry]

    return list(polygonal_geometry.geoms)


def filter_small_polygon_components(geometry):
    """
    Remove polygon components smaller than the configured area threshold.

    Geometry must already be projected to EPSG:3347 so Shapely area values are
    expressed in square meters.

    Args:
        geometry:
            Projected Polygon or MultiPolygon.

    Returns:
        Polygon | MultiPolygon:
            Geometry containing only retained polygon components.

    Raises:
        ValueError:
            If every component is below the threshold.
    """

    retained_polygons = [
        polygon
        for polygon in get_polygon_components(geometry)
        if polygon.area >= MIN_POLYGON_AREA_M2
    ]

    if not retained_polygons:
        raise ValueError(
            "Area filtering removed every polygon component."
        )

    if len(retained_polygons) == 1:
        return retained_polygons[0]

    return MultiPolygon(retained_polygons)


def round_coordinates(value):
    """
    Recursively round GeoJSON coordinates to configured precision.

    Args:
        value:
            Nested GeoJSON coordinate structure or numeric coordinate.

    Returns:
        Any:
            Equivalent structure with floating-point values rounded.
    """

    if isinstance(value, float):
        return round(value, COORDINATE_DECIMAL_PLACES)

    if isinstance(value, tuple):
        return [
            round_coordinates(child_value)
            for child_value in value
        ]

    if isinstance(value, list):
        return [
            round_coordinates(child_value)
            for child_value in value
        ]

    return value


def create_geojson_geometry(geometry) -> dict[str, Any]:
    """
    Convert Shapely geometry to rounded GeoJSON geometry.

    Args:
        geometry:
            Final WGS84 Shapely geometry.

    Returns:
        dict[str, Any]:
            GeoJSON geometry object.
    """

    geometry_mapping = mapping(geometry)

    return {
        "type": geometry_mapping["type"],
        "coordinates": round_coordinates(
            geometry_mapping["coordinates"]
        ),
    }


# ---------------------------------------------------------------------------
# Feature processing
# ---------------------------------------------------------------------------


def process_feature(
    source_feature: dict[str, Any],
) -> dict[str, Any]:
    """
    Process one HelloQuiz telephone-region feature for GeoPedia.

    Args:
        source_feature:
            Raw source GeoJSON feature.

    Returns:
        dict[str, Any]:
            Browser-ready GeoPedia GeoJSON feature.
    """

    area_code = source_feature["properties"]["AreaCode"].strip()

    source_geometry = shape(source_feature["geometry"])

    source_geometry = repair_geometry_if_needed(
        source_geometry,
        area_code,
        "source validation",
    )

    source_geometry = keep_polygonal_geometry(source_geometry)

    source_component_count = len(
        get_polygon_components(source_geometry)
    )

    projected_geometry = transform(
        TO_PROJECTED.transform,
        source_geometry,
    )

    projected_geometry = repair_geometry_if_needed(
        projected_geometry,
        area_code,
        "projection",
    )

    projected_geometry = keep_polygonal_geometry(
        projected_geometry
    )

    filtered_geometry = filter_small_polygon_components(
        projected_geometry
    )

    retained_component_count = len(
        get_polygon_components(filtered_geometry)
    )

    simplified_geometry = filtered_geometry.simplify(
        SIMPLIFY_TOLERANCE_METERS,
        preserve_topology=True,
    )

    simplified_geometry = repair_geometry_if_needed(
        simplified_geometry,
        area_code,
        "simplification",
    )

    simplified_geometry = keep_polygonal_geometry(
        simplified_geometry
    )

    wgs84_geometry = transform(
        TO_WGS84.transform,
        simplified_geometry,
    )

    wgs84_geometry = repair_geometry_if_needed(
        wgs84_geometry,
        area_code,
        "WGS84 reprojection",
    )

    wgs84_geometry = keep_polygonal_geometry(
        wgs84_geometry
    )

    print(
        f"  {area_code}: "
        f"{source_component_count:,} → "
        f"{retained_component_count:,} polygon components"
    )

    return {
        "type": "Feature",
        "id": area_code,
        "properties": {
            "area_code": area_code,
            "provinces": list(
                PROVINCES_BY_AREA_CODE[area_code]
            ),
        },
        "geometry": create_geojson_geometry(
            wgs84_geometry
        ),
    }


# ---------------------------------------------------------------------------
# Final validation
# ---------------------------------------------------------------------------


def validate_final_features(
    features: list[dict[str, Any]],
) -> None:
    """
    Validate the completed GeoPedia phone-code feature set.

    Args:
        features:
            Fully processed GeoJSON features.

    Raises:
        ValueError:
            If any runtime invariant is violated.
    """

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Final dataset has unexpected feature count: "
            f"expected {EXPECTED_FEATURE_COUNT}, "
            f"found {len(features)}."
        )

    feature_ids = [
        str(feature.get("id", ""))
        for feature in features
    ]

    if len(set(feature_ids)) != len(feature_ids):
        raise ValueError(
            "Final dataset contains duplicate feature IDs."
        )

    final_area_codes: set[str] = set()
    discovered_provinces: set[str] = set()

    for feature in features:
        feature_id = str(feature["id"])

        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {feature_id} has invalid properties."
            )

        area_code = properties.get("area_code")

        if not isinstance(area_code, str):
            raise ValueError(
                f"Feature {feature_id} is missing area_code."
            )

        if feature_id != area_code:
            raise ValueError(
                f"Feature ID {feature_id} does not match "
                f"area_code {area_code}."
            )

        provinces = properties.get("provinces")

        if (
            not isinstance(provinces, list)
            or not provinces
            or not all(
                isinstance(province, str)
                for province in provinces
            )
        ):
            raise ValueError(
                f"Area code {area_code} has invalid provinces."
            )

        if len(set(provinces)) != len(provinces):
            raise ValueError(
                f"Area code {area_code} contains duplicate "
                "province values."
            )

        expected_provinces = list(
            PROVINCES_BY_AREA_CODE[area_code]
        )

        if provinces != expected_provinces:
            raise ValueError(
                f"Area code {area_code} has unexpected provinces: "
                f"{provinces}; expected {expected_provinces}."
            )

        unexpected_provinces = (
            set(provinces) - EXPECTED_PROVINCES
        )

        if unexpected_provinces:
            raise ValueError(
                f"Area code {area_code} contains unknown "
                "province/territory values: "
                + ", ".join(sorted(unexpected_provinces))
            )

        geometry = shape(feature["geometry"])

        if geometry.is_empty:
            raise ValueError(
                f"Area code {area_code} has empty final geometry."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Area code {area_code} has invalid final geometry: "
                f"{explain_validity(geometry)}"
            )

        if not isinstance(
            geometry,
            (Polygon, MultiPolygon),
        ):
            raise ValueError(
                f"Area code {area_code} has unsupported final "
                f"geometry type: {geometry.geom_type}"
            )

        final_area_codes.add(area_code)
        discovered_provinces.update(provinces)

    if final_area_codes != EXPECTED_AREA_CODES:
        missing_codes = EXPECTED_AREA_CODES - final_area_codes
        unexpected_codes = final_area_codes - EXPECTED_AREA_CODES

        messages: list[str] = []

        if missing_codes:
            messages.append(
                "missing: " + ", ".join(sorted(missing_codes))
            )

        if unexpected_codes:
            messages.append(
                "unexpected: "
                + ", ".join(sorted(unexpected_codes))
            )

        raise ValueError(
            "Final area-code set does not match expectations ("
            + "; ".join(messages)
            + ")."
        )

    if discovered_provinces != EXPECTED_PROVINCES:
        missing_provinces = (
            EXPECTED_PROVINCES - discovered_provinces
        )

        unexpected_provinces = (
            discovered_provinces - EXPECTED_PROVINCES
        )

        messages: list[str] = []

        if missing_provinces:
            messages.append(
                "missing: "
                + ", ".join(sorted(missing_provinces))
            )

        if unexpected_provinces:
            messages.append(
                "unexpected: "
                + ", ".join(sorted(unexpected_provinces))
            )

        raise ValueError(
            "Province/territory coverage does not match "
            "expectations ("
            + "; ".join(messages)
            + ")."
        )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_output(
    features: list[dict[str, Any]],
) -> None:
    """
    Write minified browser-ready GeoJSON.

    Args:
        features:
            Validated GeoPedia phone-code features.
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            output_geojson,
            output_file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Run the complete Canada phone-code processing pipeline.
    """

    validate_input_file()

    source_geojson = read_source_geojson()

    source_features = validate_source_structure(
        source_geojson
    )

    print(
        f"✓ Found exactly {EXPECTED_FEATURE_COUNT} "
        "legacy Canadian telephone regions."
    )

    print(
        "✓ Found expected area codes: "
        + ", ".join(sorted(EXPECTED_AREA_CODES))
    )

    mapping_codes = set(PROVINCES_BY_AREA_CODE)

    if mapping_codes != EXPECTED_AREA_CODES:
        missing_mappings = EXPECTED_AREA_CODES - mapping_codes
        unexpected_mappings = mapping_codes - EXPECTED_AREA_CODES

        messages: list[str] = []

        if missing_mappings:
            messages.append(
                "missing mappings: "
                + ", ".join(sorted(missing_mappings))
            )

        if unexpected_mappings:
            messages.append(
                "unexpected mappings: "
                + ", ".join(sorted(unexpected_mappings))
            )

        raise ValueError(
            "Province mapping does not match expected area codes ("
            + "; ".join(messages)
            + ")."
        )

    print(
        "✓ Province / territory mappings cover every area code."
    )

    processed_features = [
        process_feature(feature)
        for feature in source_features
    ]

    # Stable numeric ordering makes generated output deterministic and easier
    # to inspect in source control.
    processed_features.sort(
        key=lambda feature: int(feature["properties"]["area_code"])
    )

    validate_final_features(processed_features)

    print(
        f"\n✓ Found exactly {EXPECTED_FEATURE_COUNT} "
        "processed telephone regions."
    )
    print("✓ All area codes are unique.")
    print("✓ All GeoJSON feature IDs are stable.")
    print("✓ All features have province / territory grouping data.")
    print("✓ Found all 13 Canadian provinces and territories.")
    print(
        f"✓ Removed polygon components smaller than "
        f"{MIN_POLYGON_AREA_KM2} km²."
    )
    print(
        f"✓ Simplified geometry with a "
        f"{SIMPLIFY_TOLERANCE_METERS:,} meter tolerance."
    )
    print("✓ Reprojected final geometry to WGS84.")
    print(
        f"✓ Rounded coordinates to "
        f"{COORDINATE_DECIMAL_PLACES} decimal places."
    )
    print("✓ Validated final geometry.")
    print("✓ Removed unused source properties.")

    write_output(processed_features)

    output_size_bytes = OUTPUT_PATH.stat().st_size
    output_size_kb = output_size_bytes / 1024
    output_size_mb = output_size_kb / 1024

    print("\n✓ Saved processed data to:")
    print(f"  {OUTPUT_PATH}")

    print(
        f"✓ Final file size: "
        f"{output_size_kb:,.0f} KB "
        f"({output_size_mb:.2f} MB)"
    )


if __name__ == "__main__":
    main()