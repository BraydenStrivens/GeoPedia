"""
Process INEGI's 2025 Mexican state boundaries into GeoPedia runtime GeoJSON.

Source
------
INEGI Marco Geoestadístico Integrado 2025:

    data/raw/countries/mexico/mg_2025_integrado/
        conjunto_de_datos/
            00ent.shp
            00ent.shx
            00ent.dbf
            00ent.prj
            00ent.cpg

The `00ent` layer contains Mexico's 32 first-level federal entities:
31 states plus Ciudad de México.

Relevant source fields:
    CVE_ENT -> two-digit INEGI state/entity identifier
    NOMGEO  -> entity name

The source `.cpg` declares its encoding as `88591`, which PyShp does not
recognize as an encoding name. The DBF is therefore opened explicitly using
Latin-1 (`latin1`), which corresponds to ISO-8859-1.

Processing pipeline
-------------------
1. Read all 32 INEGI entity features.
2. Validate state IDs and names.
3. Convert source geometries to Shapely.
4. Repair invalid source geometry only when necessary.
5. Keep polygonal geometry only.
6. Reproject to a metric CRS for area filtering and simplification.
7. Remove separate polygon components smaller than 5 km².
8. Simplify geometry with a 2,500 meter tolerance while preserving topology.
9. Repair and retain polygonal geometry again after simplification.
10. Reproject to WGS84 for browser use.
11. Round coordinates to 5 decimal places.
12. Remove all unused INEGI properties.
13. Validate the processed FeatureCollection.
14. Write compact runtime GeoJSON.

Output
------
    public/data/countries/mexico/geojson/states.geojson

Each output feature has the form:

    {
        "type": "Feature",
        "id": "14",
        "properties": {
            "state_id": "14",
            "name": "Jalisco"
        },
        "geometry": ...
    }

State abbreviations and state codes are intentionally not stored in this
runtime GeoJSON. Those are quiz-specific data and can be mapped separately
from the stable INEGI state ID.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import shapefile
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform
from shapely.validation import explain_validity


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "mexico"
    / "mg_2025_integrado"
    / "conjunto_de_datos"
)

SOURCE_SHP = SOURCE_DIR / "00ent.shp"
SOURCE_PRJ = SOURCE_DIR / "00ent.prj"

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "mexico"
    / "geojson"
    / "states.geojson"
)


# ---------------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 32

EXPECTED_STATE_IDS = {
    f"{state_id:02d}"
    for state_id in range(1, EXPECTED_FEATURE_COUNT + 1)
}


# ---------------------------------------------------------------------------
# Geometry processing settings
# ---------------------------------------------------------------------------

MIN_POLYGON_AREA_KM2 = 5
MIN_POLYGON_AREA_M2 = MIN_POLYGON_AREA_KM2 * 1_000_000

SIMPLIFY_TOLERANCE_METERS = 2_500

COORDINATE_DECIMAL_PLACES = 5

WGS84_CRS = CRS.from_epsg(4326)

# EPSG:6372 is Mexico ITRF2008 / LCC, a projected CRS designed for Mexico.
# Using a Mexico-specific metric projection gives us meaningful square-meter
# areas and meter-based simplification tolerances.
MEXICO_METRIC_CRS = CRS.from_epsg(6372)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def repair_geometry_if_needed(geometry: BaseGeometry) -> BaseGeometry:
    """
    Repair invalid geometry while leaving already-valid geometry untouched.

    `make_valid()` can change geometry structure, so it is only applied when
    Shapely reports that a source or processed geometry is invalid.
    """

    if geometry.is_valid:
        return geometry

    repaired = make_valid(geometry)

    if repaired.is_empty:
        raise ValueError(
            "Geometry became empty while attempting to repair "
            f"invalid geometry: {explain_validity(geometry)}"
        )

    return repaired


def keep_polygonal_geometry(geometry: BaseGeometry) -> Polygon | MultiPolygon:
    """
    Extract only Polygon and MultiPolygon content from a Shapely geometry.

    Geometry repair can occasionally return a GeometryCollection containing
    valid polygonal components alongside lines or points. GeoPedia's feature
    maps require polygonal geometry, so non-polygon components are discarded.
    """

    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        return geometry

    if geometry.geom_type == "GeometryCollection":
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            if isinstance(part, Polygon):
                polygons.append(part)
            elif isinstance(part, MultiPolygon):
                polygons.extend(part.geoms)

        if not polygons:
            raise ValueError(
                "GeometryCollection contains no polygonal geometry."
            )

        if len(polygons) == 1:
            return polygons[0]

        return MultiPolygon(polygons)

    raise ValueError(
        f"Expected polygonal geometry, found {geometry.geom_type}."
    )


def get_polygon_components(
    geometry: Polygon | MultiPolygon,
) -> list[Polygon]:
    """Return every top-level Polygon component in a polygonal geometry."""

    if isinstance(geometry, Polygon):
        return [geometry]

    return list(geometry.geoms)


def remove_small_polygon_components(
    geometry: Polygon | MultiPolygon,
) -> tuple[Polygon | MultiPolygon, int, int]:
    """
    Remove separate polygon components smaller than the configured area.

    This removes tiny offshore islands and geometry fragments that provide
    little quiz value while contributing disproportionately to runtime file
    size.

    Interior holes are preserved.

    Returns:
        processed geometry,
        original polygon-component count,
        retained polygon-component count
    """

    polygons = get_polygon_components(geometry)
    retained = [
        polygon
        for polygon in polygons
        if polygon.area >= MIN_POLYGON_AREA_M2
    ]

    if not retained:
        # A state should never disappear entirely because of the component
        # threshold. Keeping the largest component makes this helper defensive
        # against unexpected source geometry.
        retained = [max(polygons, key=lambda polygon: polygon.area)]

    if len(retained) == 1:
        processed: Polygon | MultiPolygon = retained[0]
    else:
        processed = MultiPolygon(retained)

    return processed, len(polygons), len(retained)


def round_coordinates(value: Any) -> Any:
    """
    Recursively round coordinate values in a GeoJSON-compatible structure.

    Five decimal places is approximately meter-level precision at these
    latitudes and is more than sufficient for GeoPedia's map rendering.
    """

    if isinstance(value, float):
        return round(value, COORDINATE_DECIMAL_PLACES)

    if isinstance(value, list):
        return [round_coordinates(item) for item in value]

    if isinstance(value, tuple):
        return [round_coordinates(item) for item in value]

    return value


# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------


def load_source_crs() -> CRS:
    """
    Read the source coordinate reference system from INEGI's `.prj` file.

    Reading the supplied CRS metadata is preferable to assuming a particular
    projection and keeps the processor tied directly to the downloaded source.
    """

    if not SOURCE_PRJ.exists():
        raise FileNotFoundError(
            f"Missing source projection file:\n  {SOURCE_PRJ}"
        )

    wkt = SOURCE_PRJ.read_text(encoding="utf-8").strip()

    if not wkt:
        raise ValueError(
            f"Source projection file is empty:\n  {SOURCE_PRJ}"
        )

    return CRS.from_wkt(wkt)


def normalize_source_record(record: shapefile._Record) -> tuple[str, str]:
    """
    Extract and validate the state ID and state name from an INEGI DBF record.
    """

    state_id = str(record["CVE_ENT"]).strip()
    name = str(record["NOMGEO"]).strip()

    if not state_id:
        raise ValueError("Found a state with an empty CVE_ENT value.")

    if not name:
        raise ValueError(
            f"State {state_id} has an empty NOMGEO value."
        )

    return state_id, name


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_source_records(
    records: list[tuple[shapefile.Shape, shapefile._Record]],
) -> None:
    """Validate the basic structure and identity of the INEGI source layer."""

    if len(records) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected INEGI entity count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(records)}."
        )

    state_ids: list[str] = []
    names: list[str] = []

    for _, record in records:
        state_id, name = normalize_source_record(record)
        state_ids.append(state_id)
        names.append(name)

    if len(set(state_ids)) != len(state_ids):
        raise ValueError("INEGI source contains duplicate CVE_ENT values.")

    if len(set(names)) != len(names):
        raise ValueError("INEGI source contains duplicate state names.")

    actual_state_ids = set(state_ids)

    if actual_state_ids != EXPECTED_STATE_IDS:
        missing = sorted(EXPECTED_STATE_IDS - actual_state_ids)
        unexpected = sorted(actual_state_ids - EXPECTED_STATE_IDS)

        raise ValueError(
            "Unexpected INEGI state ID set.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    print(f"✓ Found exactly {EXPECTED_FEATURE_COUNT} Mexican states/entities.")
    print("✓ Found expected INEGI state IDs 01 through 32.")
    print("✓ All state names are unique.")


def validate_output(feature_collection: dict[str, Any]) -> None:
    """Validate the final GeoJSON before writing it to disk."""

    if feature_collection.get("type") != "FeatureCollection":
        raise ValueError("Output is not a GeoJSON FeatureCollection.")

    features = feature_collection.get("features")

    if not isinstance(features, list):
        raise ValueError("Output FeatureCollection has no feature list.")

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected processed state count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(features)}."
        )

    state_ids: list[str] = []
    names: list[str] = []

    for feature in features:
        if feature.get("type") != "Feature":
            raise ValueError("Processed output contains a non-Feature item.")

        feature_id = feature.get("id")
        properties = feature.get("properties")
        geometry_data = feature.get("geometry")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {feature_id!r} has invalid properties."
            )

        state_id = properties.get("state_id")
        name = properties.get("name")

        if not isinstance(state_id, str) or not state_id:
            raise ValueError(
                f"Feature {feature_id!r} has an invalid state_id."
            )

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Feature {feature_id!r} has an invalid name."
            )

        if feature_id != state_id:
            raise ValueError(
                f"Feature ID {feature_id!r} does not match "
                f"state_id {state_id!r}."
            )

        if set(properties) != {"state_id", "name"}:
            raise ValueError(
                f"Feature {state_id} contains unexpected properties: "
                f"{sorted(properties)}"
            )

        if geometry_data is None:
            raise ValueError(f"Feature {state_id} has no geometry.")

        geometry = shape(geometry_data)

        if geometry.is_empty:
            raise ValueError(
                f"Feature {state_id} ({name}) has empty geometry."
            )

        if not isinstance(geometry, (Polygon, MultiPolygon)):
            raise ValueError(
                f"Feature {state_id} ({name}) has non-polygon geometry "
                f"{geometry.geom_type}."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Feature {state_id} ({name}) has invalid final geometry: "
                f"{explain_validity(geometry)}"
            )

        state_ids.append(state_id)
        names.append(name)

    if set(state_ids) != EXPECTED_STATE_IDS:
        raise ValueError("Processed output has an unexpected state ID set.")

    if len(set(state_ids)) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Processed output contains duplicate state IDs.")

    if len(set(names)) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Processed output contains duplicate state names.")

    print()
    print(f"✓ Found exactly {EXPECTED_FEATURE_COUNT} processed states.")
    print("✓ All state IDs are unique.")
    print("✓ All state names are unique.")
    print("✓ All GeoJSON feature IDs are stable.")
    print("✓ Validated final geometry.")
    print("✓ Removed unused INEGI properties.")


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def main() -> None:
    """Process INEGI state boundaries into GeoPedia runtime GeoJSON."""

    if not SOURCE_SHP.exists():
        raise FileNotFoundError(
            f"Missing INEGI state shapefile:\n  {SOURCE_SHP}"
        )

    source_crs = load_source_crs()

    print("Mexico states processor")
    print("-----------------------")
    print(f"Source: {SOURCE_SHP}")
    print(f"Source CRS: {source_crs.to_string()}")
    print()

    # INEGI's `.cpg` contains `88591`, which denotes ISO-8859-1 but is not
    # recognized by PyShp as a valid Python codec name.
    reader = shapefile.Reader(
        str(SOURCE_SHP),
        encoding="latin1",
    )

    try:
        records = list(reader.iterShapeRecords())
    finally:
        reader.close()

    source_records = [
        (shape_record.shape, shape_record.record)
        for shape_record in records
    ]

    validate_source_records(source_records)

    source_to_metric = Transformer.from_crs(
        source_crs,
        MEXICO_METRIC_CRS,
        always_xy=True,
    )

    metric_to_wgs84 = Transformer.from_crs(
        MEXICO_METRIC_CRS,
        WGS84_CRS,
        always_xy=True,
    )

    features: list[dict[str, Any]] = []

    total_source_components = 0
    total_retained_components = 0

    print()

    for source_shape, record in source_records:
        state_id, name = normalize_source_record(record)

        source_geo_interface = source_shape.__geo_interface__
        geometry = shape(source_geo_interface)

        if geometry.is_empty:
            raise ValueError(
                f"Source geometry is empty for {state_id} ({name})."
            )

        if not geometry.is_valid:
            print(
                f"  Repairing {name}: "
                f"{explain_validity(geometry)}"
            )

        geometry = repair_geometry_if_needed(geometry)
        polygonal_geometry = keep_polygonal_geometry(geometry)

        metric_geometry = transform(
            source_to_metric.transform,
            polygonal_geometry,
        )

        metric_geometry = repair_geometry_if_needed(metric_geometry)
        metric_geometry = keep_polygonal_geometry(metric_geometry)

        (
            metric_geometry,
            source_component_count,
            retained_component_count,
        ) = remove_small_polygon_components(metric_geometry)

        total_source_components += source_component_count
        total_retained_components += retained_component_count

        simplified_geometry = metric_geometry.simplify(
            SIMPLIFY_TOLERANCE_METERS,
            preserve_topology=True,
        )

        simplified_geometry = repair_geometry_if_needed(
            simplified_geometry
        )
        simplified_geometry = keep_polygonal_geometry(
            simplified_geometry
        )

        wgs84_geometry = transform(
            metric_to_wgs84.transform,
            simplified_geometry,
        )

        wgs84_geometry = repair_geometry_if_needed(wgs84_geometry)
        wgs84_geometry = keep_polygonal_geometry(wgs84_geometry)

        geojson_geometry = mapping(wgs84_geometry)
        rounded_coordinates = round_coordinates(
            geojson_geometry["coordinates"]
        )

        feature = {
            "type": "Feature",
            "id": state_id,
            "properties": {
                "state_id": state_id,
                "name": name,
            },
            "geometry": {
                "type": geojson_geometry["type"],
                "coordinates": rounded_coordinates,
            },
        }

        features.append(feature)

        print(
            f"  {state_id} {name}: "
            f"{source_component_count} → "
            f"{retained_component_count} polygon components"
        )

    features.sort(
        key=lambda feature: int(feature["properties"]["state_id"])
    )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    validate_output(feature_collection)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(
            feature_collection,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    file_size_bytes = OUTPUT_PATH.stat().st_size
    file_size_kb = file_size_bytes / 1024
    file_size_mb = file_size_kb / 1024

    print(
        f"✓ Removed polygon components smaller than "
        f"{MIN_POLYGON_AREA_KM2} km²."
    )
    print(
        f"✓ Polygon components: "
        f"{total_source_components:,} → "
        f"{total_retained_components:,}."
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

    print()
    print("✓ Saved processed data to:")
    print(f"  {OUTPUT_PATH}")
    print(
        f"✓ Final file size: "
        f"{file_size_kb:,.0f} KB ({file_size_mb:.2f} MB)"
    )


if __name__ == "__main__":
    main()