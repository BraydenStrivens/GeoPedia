"""
Process INEGI's 2025 Mexican municipality boundaries into GeoPedia runtime
GeoJSON.

Source
------
INEGI Marco Geoestadístico Integrado 2025:

    data/raw/countries/mexico/mg_2025_integrado/
        conjunto_de_datos/
            00mun.shp
            00mun.shx
            00mun.dbf
            00mun.prj
            00mun.cpg

The `00mun` layer contains Mexico's municipality-level administrative units.

Relevant source fields:
    CVEGEO  -> globally unique five-digit municipality identifier
    CVE_ENT -> two-digit INEGI state/entity identifier
    CVE_MUN -> three-digit municipality identifier within its state
    NOMGEO  -> municipality name

The source `.cpg` declares its encoding as `88591`, which PyShp does not
recognize as a Python codec name. The DBF is therefore opened explicitly with
Latin-1 (`latin1`), corresponding to ISO-8859-1.

Processing pipeline
-------------------
1. Read all 2,478 INEGI municipality features.
2. Validate municipality IDs, state IDs, and names.
3. Convert source geometries to Shapely.
4. Repair invalid source geometry only when necessary.
5. Keep polygonal geometry only.
6. Reproject to a Mexico-specific metric CRS.
7. Remove separate polygon components smaller than 1 km².
8. Simplify geometry with a 1,000 meter tolerance while preserving topology.
9. Repair and retain polygonal geometry again after simplification.
10. Reproject to WGS84 for browser use.
11. Round coordinates to 5 decimal places.
12. Remove unused INEGI properties.
13. Validate the processed FeatureCollection.
14. Write compact runtime GeoJSON.

Output
------
    public/data/countries/mexico/geojson/municipalities.geojson

Each output feature has the form:

    {
        "type": "Feature",
        "id": "01001",
        "properties": {
            "municipality_id": "01001",
            "name": "Aguascalientes",
            "state_id": "01"
        },
        "geometry": ...
    }

Quiz-specific display disambiguation is intentionally not stored in the
GeoJSON. The municipality quiz generator can append state abbreviations only
when duplicate municipality names require them.
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

SOURCE_SHP = SOURCE_DIR / "00mun.shp"
SOURCE_PRJ = SOURCE_DIR / "00mun.prj"

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "mexico"
    / "geojson"
    / "municipalities.geojson"
)


# ---------------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 2478
EXPECTED_STATE_COUNT = 32

EXPECTED_STATE_IDS = {
    f"{state_id:02d}"
    for state_id in range(1, EXPECTED_STATE_COUNT + 1)
}


# ---------------------------------------------------------------------------
# Geometry processing settings
# ---------------------------------------------------------------------------

# Municipality boundaries are much smaller than state boundaries, so use a
# smaller component threshold than the states processor.
MIN_POLYGON_AREA_KM2 = 1
MIN_POLYGON_AREA_M2 = MIN_POLYGON_AREA_KM2 * 1_000_000

# Smaller than the 2,500 m state tolerance so municipality boundaries retain
# enough local detail for quiz interaction.
SIMPLIFY_TOLERANCE_METERS = 1_000

COORDINATE_DECIMAL_PLACES = 5

WGS84_CRS = CRS.from_epsg(4326)

# Mexico ITRF2008 / LCC. This gives us meaningful square-meter areas and
# meter-based simplification tolerances across the country.
MEXICO_METRIC_CRS = CRS.from_epsg(6372)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def repair_geometry_if_needed(geometry: BaseGeometry) -> BaseGeometry:
    """
    Repair invalid geometry while leaving valid geometry unchanged.

    `make_valid()` can change geometry structure, so it is only applied when
    Shapely reports an invalid source or processed geometry.
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

    Geometry repair can return a GeometryCollection containing polygonal and
    non-polygonal pieces. GeoPedia's feature maps require polygonal geometry,
    so lines and points are discarded.
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

    Tiny islands and geometry fragments can add substantial file size while
    providing little quiz value.

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
        # Never allow an entire municipality to disappear because every
        # component fell below the threshold.
        retained = [max(polygons, key=lambda polygon: polygon.area)]

    if len(retained) == 1:
        processed: Polygon | MultiPolygon = retained[0]
    else:
        processed = MultiPolygon(retained)

    return processed, len(polygons), len(retained)


def round_coordinates(value: Any) -> Any:
    """
    Recursively round coordinate values in a GeoJSON-compatible structure.

    Five decimal places is more than sufficient for browser rendering at the
    scales used by GeoPedia's municipality quizzes.
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


def normalize_source_record(
    record: shapefile._Record,
) -> tuple[str, str, str, str]:
    """
    Extract and validate municipality identity fields from an INEGI record.

    Returns:
        municipality_id,
        state_id,
        municipality_code,
        municipality_name
    """

    municipality_id = str(record["CVEGEO"]).strip()
    state_id = str(record["CVE_ENT"]).strip()
    municipality_code = str(record["CVE_MUN"]).strip()
    name = str(record["NOMGEO"]).strip()

    if not municipality_id:
        raise ValueError("Found municipality with empty CVEGEO.")

    if not state_id:
        raise ValueError(
            f"Municipality {municipality_id} has empty CVE_ENT."
        )

    if not municipality_code:
        raise ValueError(
            f"Municipality {municipality_id} has empty CVE_MUN."
        )

    if not name:
        raise ValueError(
            f"Municipality {municipality_id} has empty NOMGEO."
        )

    expected_id = f"{state_id}{municipality_code}"

    if municipality_id != expected_id:
        raise ValueError(
            f"Municipality {municipality_id} has inconsistent identifiers: "
            f"CVE_ENT={state_id}, CVE_MUN={municipality_code}, "
            f"expected CVEGEO={expected_id}."
        )

    return municipality_id, state_id, municipality_code, name


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_source_records(
    records: list[tuple[shapefile.Shape, shapefile._Record]],
) -> None:
    """Validate the basic structure of the INEGI municipality layer."""

    if len(records) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected INEGI municipality count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(records)}."
        )

    municipality_ids: list[str] = []
    state_ids: set[str] = set()
    names: list[str] = []

    for _, record in records:
        municipality_id, state_id, _, name = normalize_source_record(record)

        municipality_ids.append(municipality_id)
        state_ids.add(state_id)
        names.append(name)

    if len(set(municipality_ids)) != len(municipality_ids):
        raise ValueError(
            "INEGI source contains duplicate CVEGEO municipality IDs."
        )

    if state_ids != EXPECTED_STATE_IDS:
        missing = sorted(EXPECTED_STATE_IDS - state_ids)
        unexpected = sorted(state_ids - EXPECTED_STATE_IDS)

        raise ValueError(
            "Unexpected INEGI state ID set in municipality layer.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    print(
        f"✓ Found exactly {EXPECTED_FEATURE_COUNT:,} "
        "Mexican municipalities."
    )
    print("✓ All municipality IDs are unique.")
    print("✓ Found all 32 INEGI state/entity IDs.")
    print(
        f"✓ Municipality names include "
        f"{len(set(names)):,} unique values."
    )


def validate_output(feature_collection: dict[str, Any]) -> None:
    """Validate the final GeoJSON before writing it to disk."""

    if feature_collection.get("type") != "FeatureCollection":
        raise ValueError("Output is not a GeoJSON FeatureCollection.")

    features = feature_collection.get("features")

    if not isinstance(features, list):
        raise ValueError("Output FeatureCollection has no feature list.")

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected processed municipality count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(features)}."
        )

    municipality_ids: list[str] = []
    state_ids: set[str] = set()

    for feature in features:
        if feature.get("type") != "Feature":
            raise ValueError(
                "Processed output contains a non-Feature item."
            )

        feature_id = feature.get("id")
        properties = feature.get("properties")
        geometry_data = feature.get("geometry")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {feature_id!r} has invalid properties."
            )

        municipality_id = properties.get("municipality_id")
        name = properties.get("name")
        state_id = properties.get("state_id")

        if not isinstance(municipality_id, str) or not municipality_id:
            raise ValueError(
                f"Feature {feature_id!r} has an invalid municipality_id."
            )

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Feature {feature_id!r} has an invalid name."
            )

        if not isinstance(state_id, str) or not state_id:
            raise ValueError(
                f"Feature {feature_id!r} has an invalid state_id."
            )

        if feature_id != municipality_id:
            raise ValueError(
                f"Feature ID {feature_id!r} does not match "
                f"municipality_id {municipality_id!r}."
            )

        if not municipality_id.startswith(state_id):
            raise ValueError(
                f"Municipality {municipality_id} does not begin with "
                f"state ID {state_id}."
            )

        expected_properties = {
            "municipality_id",
            "name",
            "state_id",
        }

        if set(properties) != expected_properties:
            raise ValueError(
                f"Feature {municipality_id} contains unexpected properties: "
                f"{sorted(properties)}"
            )

        if geometry_data is None:
            raise ValueError(
                f"Feature {municipality_id} has no geometry."
            )

        geometry = shape(geometry_data)

        if geometry.is_empty:
            raise ValueError(
                f"Feature {municipality_id} ({name}) has empty geometry."
            )

        if not isinstance(geometry, (Polygon, MultiPolygon)):
            raise ValueError(
                f"Feature {municipality_id} ({name}) has non-polygon "
                f"geometry {geometry.geom_type}."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Feature {municipality_id} ({name}) has invalid final "
                f"geometry: {explain_validity(geometry)}"
            )

        municipality_ids.append(municipality_id)
        state_ids.add(state_id)

    if len(set(municipality_ids)) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Processed output contains duplicate municipality IDs."
        )

    if state_ids != EXPECTED_STATE_IDS:
        raise ValueError(
            "Processed output does not contain all 32 state IDs."
        )

    print()
    print(
        f"✓ Found exactly {EXPECTED_FEATURE_COUNT:,} "
        "processed municipalities."
    )
    print("✓ All municipality IDs are unique.")
    print("✓ All GeoJSON feature IDs are stable.")
    print("✓ All 32 states/entities are represented.")
    print("✓ Validated final geometry.")
    print("✓ Removed unused INEGI properties.")


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def main() -> None:
    """Process INEGI municipality boundaries into GeoPedia runtime GeoJSON."""

    if not SOURCE_SHP.exists():
        raise FileNotFoundError(
            f"Missing INEGI municipality shapefile:\n  {SOURCE_SHP}"
        )

    source_crs = load_source_crs()

    print("Mexico municipalities processor")
    print("------------------------------")
    print(f"Source: {SOURCE_SHP}")
    print(f"Source CRS: {source_crs.to_string()}")
    print()

    # INEGI's `.cpg` contains `88591`, which represents ISO-8859-1 but is
    # not accepted by PyShp as a Python codec name.
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
    repaired_source_count = 0

    print()

    for index, (source_shape, record) in enumerate(
        source_records,
        start=1,
    ):
        (
            municipality_id,
            state_id,
            _municipality_code,
            name,
        ) = normalize_source_record(record)

        geometry = shape(source_shape.__geo_interface__)

        if geometry.is_empty:
            raise ValueError(
                f"Source geometry is empty for "
                f"{municipality_id} ({name})."
            )

        if not geometry.is_valid:
            repaired_source_count += 1
            print(
                f"  Repairing {municipality_id} {name}: "
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

        feature = {
            "type": "Feature",
            "id": municipality_id,
            "properties": {
                "municipality_id": municipality_id,
                "name": name,
                "state_id": state_id,
            },
            "geometry": {
                "type": geojson_geometry["type"],
                "coordinates": round_coordinates(
                    geojson_geometry["coordinates"]
                ),
            },
        }

        features.append(feature)

        # Avoid printing all 2,478 municipalities. Emit periodic progress plus
        # any feature whose polygon-component count was reduced.
        if (
            source_component_count != retained_component_count
            or index % 250 == 0
            or index == EXPECTED_FEATURE_COUNT
        ):
            print(
                f"  [{index:>4}/{EXPECTED_FEATURE_COUNT}] "
                f"{municipality_id} {name}: "
                f"{source_component_count} → "
                f"{retained_component_count} polygon components"
            )

    features.sort(
        key=lambda feature: feature["properties"]["municipality_id"]
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
        f"✓ Repaired {repaired_source_count:,} invalid source geometries."
    )
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