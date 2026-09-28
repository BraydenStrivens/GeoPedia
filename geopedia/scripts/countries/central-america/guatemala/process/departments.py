"""
Process Guatemala department boundaries for GeoPedia.

Source:
    Humanitarian Data Exchange (HDX)
    Guatemala administrative boundaries dataset
    Administrative level 1 (departments)

Raw input:
    data/raw/countries/guatemala/gtm_admin_boundaries.geojson/
        gtm_admin1.geojson

Runtime output:
    public/data/countries/guatemala/geojson/departments.geojson

The source contains 22 ADM1 features. This processor:

- validates the expected HDX schema
- converts source department codes such as GT16 to compact GeoPedia IDs
  such as 16
- preserves Spanish department names
- repairs invalid Polygon/MultiPolygon geometry if necessary
- simplifies geometry in a projected CRS
- rounds runtime coordinates
- emits only the properties GeoPedia needs
- validates the completed runtime GeoJSON

Source feature example:
    {
        "adm1_name": "Alta Verapaz",
        "adm1_pcode": "GT16",
        ...
    }

Runtime feature example:
    {
        "type": "Feature",
        "id": "16",
        "properties": {
            "department_id": "16",
            "name": "Alta Verapaz"
        },
        "geometry": ...
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely import make_valid, set_precision
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import transform, unary_union


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "guatemala"
    / "gtm_admin_boundaries.geojson"
    / "gtm_admin1.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "guatemala"
    / "geojson"
    / "departments.geojson"
)


SOURCE_CRS = "EPSG:4326"

# Guatemala falls primarily within UTM zone 15N. Using a projected CRS lets
# simplification and precision operate in meters rather than degrees.
PROCESSING_CRS = "EPSG:32615"

SIMPLIFY_TOLERANCE_METERS = 100.0
PRECISION_GRID_METERS = 0.1
COORDINATE_DECIMAL_PLACES = 6

EXPECTED_DEPARTMENT_COUNT = 22

EXPECTED_SOURCE_PROPERTIES = {
    "adm1_name",
    "adm1_pcode",
}

EXPECTED_RUNTIME_PROPERTIES = {
    "department_id",
    "name",
}


TO_PROCESSING_CRS = Transformer.from_crs(
    SOURCE_CRS,
    PROCESSING_CRS,
    always_xy=True,
).transform

TO_RUNTIME_CRS = Transformer.from_crs(
    PROCESSING_CRS,
    SOURCE_CRS,
    always_xy=True,
).transform


def load_geojson(path: Path) -> dict[str, Any]:
    """Load a GeoJSON file and validate that it is a FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(f"Source file does not exist: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected FeatureCollection in {path}, "
            f"got {data.get('type')!r}."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"FeatureCollection in {path} does not contain "
            "a valid features array."
        )

    return data


def normalize_department_id(value: Any) -> str:
    """
    Convert an HDX ADM1 p-code such as GT16 into the GeoPedia ID "16".
    """

    if not isinstance(value, str):
        raise ValueError(
            f"Department p-code must be a string, got {value!r}."
        )

    if len(value) != 4 or not value.startswith("GT"):
        raise ValueError(
            f"Unexpected Guatemala ADM1 p-code format: {value!r}."
        )

    department_id = value[2:]

    if not department_id.isdigit():
        raise ValueError(
            f"Department p-code has non-numeric suffix: {value!r}."
        )

    numeric_id = int(department_id)

    if not 1 <= numeric_id <= EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Department ID is outside expected range 01-22: "
            f"{department_id!r}."
        )

    return department_id


def extract_polygonal_geometry(geometry: Any) -> Polygon | MultiPolygon:
    """
    Extract only polygonal geometry from a repaired Shapely geometry.

    Geometry repair can sometimes return a GeometryCollection containing
    polygons together with lines or points. GeoPedia only needs polygonal
    department boundaries.
    """

    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []

        for item in geometry.geoms:
            if isinstance(item, Polygon):
                polygons.append(item)
            elif isinstance(item, MultiPolygon):
                polygons.extend(item.geoms)

        if not polygons:
            raise ValueError(
                "Geometry contains no polygonal area after repair."
            )

        merged = unary_union(polygons)

        if isinstance(merged, (Polygon, MultiPolygon)):
            return merged

    raise ValueError(
        "Geometry could not be converted to Polygon or MultiPolygon."
    )


def repair_geometry(
    geometry_data: dict[str, Any],
) -> tuple[Polygon | MultiPolygon, bool]:
    """
    Repair and normalize one source geometry.

    Returns:
        A tuple containing:
        - repaired Polygon/MultiPolygon
        - whether the original geometry required validity repair
    """

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError("Source geometry is empty.")

    if not isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        raise ValueError(
            f"Expected Polygon or MultiPolygon, got "
            f"{geometry.geom_type!r}."
        )

    required_repair = not geometry.is_valid

    if required_repair:
        geometry = make_valid(geometry)

    geometry = extract_polygonal_geometry(geometry)

    projected = transform(
        TO_PROCESSING_CRS,
        geometry,
    )

    projected = set_precision(
        projected,
        PRECISION_GRID_METERS,
        mode="valid_output",
    )

    if not projected.is_valid:
        projected = make_valid(projected)
        projected = extract_polygonal_geometry(projected)

    simplified = projected.simplify(
        SIMPLIFY_TOLERANCE_METERS,
        preserve_topology=True,
    )

    simplified = extract_polygonal_geometry(simplified)

    if not simplified.is_valid:
        simplified = make_valid(simplified)
        simplified = extract_polygonal_geometry(simplified)

    runtime_geometry = transform(
        TO_RUNTIME_CRS,
        simplified,
    )

    runtime_geometry = extract_polygonal_geometry(runtime_geometry)

    if runtime_geometry.is_empty:
        raise ValueError("Processed geometry is empty.")

    if not runtime_geometry.is_valid:
        runtime_geometry = make_valid(runtime_geometry)
        runtime_geometry = extract_polygonal_geometry(runtime_geometry)

    return runtime_geometry, required_repair


def round_coordinates(value: Any) -> Any:
    """Recursively round GeoJSON coordinates to runtime precision."""

    if isinstance(value, float):
        return round(value, COORDINATE_DECIMAL_PLACES)

    if isinstance(value, list):
        return [
            round_coordinates(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            round_coordinates(item)
            for item in value
        ]

    return value


def geometry_to_geojson(
    geometry: Polygon | MultiPolygon,
) -> dict[str, Any]:
    """Convert a Shapely geometry into rounded GeoJSON geometry."""

    geometry_data = mapping(geometry)

    return {
        "type": geometry_data["type"],
        "coordinates": round_coordinates(
            geometry_data["coordinates"]
        ),
    }


def process_department(
    feature: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """
    Convert one HDX ADM1 source feature into GeoPedia runtime format.
    """

    if feature.get("type") != "Feature":
        raise ValueError(
            f"Expected GeoJSON Feature, got "
            f"{feature.get('type')!r}."
        )

    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            "Source feature does not contain valid properties."
        )

    missing_properties = (
        EXPECTED_SOURCE_PROPERTIES
        - properties.keys()
    )

    if missing_properties:
        raise ValueError(
            "Source feature is missing required properties: "
            f"{sorted(missing_properties)}"
        )

    name = properties.get("adm1_name")

    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f"Invalid department name: {name!r}."
        )

    name = name.strip()

    department_id = normalize_department_id(
        properties.get("adm1_pcode")
    )

    geometry_data = feature.get("geometry")

    if not isinstance(geometry_data, dict):
        raise ValueError(
            f"Department {department_id} has invalid geometry."
        )

    geometry, required_repair = repair_geometry(
        geometry_data
    )

    runtime_feature = {
        "type": "Feature",
        "id": department_id,
        "properties": {
            "department_id": department_id,
            "name": name,
        },
        "geometry": geometry_to_geojson(
            geometry
        ),
    }

    return runtime_feature, required_repair


def validate_runtime_geojson(
    geojson: dict[str, Any],
) -> None:
    """Validate the completed GeoPedia department FeatureCollection."""

    if geojson.get("type") != "FeatureCollection":
        raise ValueError(
            "Runtime output is not a FeatureCollection."
        )

    features = geojson.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Runtime output does not contain a features array."
        )

    if len(features) != EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} departments, "
            f"got {len(features)}."
        )

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for feature in features:
        if feature.get("type") != "Feature":
            raise ValueError(
                "Runtime output contains a non-Feature entry."
            )

        feature_id = feature.get("id")
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {feature_id!r} has invalid properties."
            )

        actual_properties = set(properties.keys())

        if actual_properties != EXPECTED_RUNTIME_PROPERTIES:
            raise ValueError(
                f"Feature {feature_id!r} has unexpected properties. "
                f"Expected {sorted(EXPECTED_RUNTIME_PROPERTIES)}, "
                f"got {sorted(actual_properties)}."
            )

        department_id = properties.get(
            "department_id"
        )

        name = properties.get("name")

        if feature_id != department_id:
            raise ValueError(
                f"Feature ID {feature_id!r} does not match "
                f"department_id {department_id!r}."
            )

        if not isinstance(department_id, str):
            raise ValueError(
                f"Invalid department_id: {department_id!r}."
            )

        if (
            len(department_id) != 2
            or not department_id.isdigit()
        ):
            raise ValueError(
                f"Invalid department_id format: "
                f"{department_id!r}."
            )

        numeric_id = int(department_id)

        if not 1 <= numeric_id <= EXPECTED_DEPARTMENT_COUNT:
            raise ValueError(
                f"Department ID outside expected range: "
                f"{department_id!r}."
            )

        if department_id in seen_ids:
            raise ValueError(
                f"Duplicate department ID: "
                f"{department_id!r}."
            )

        seen_ids.add(department_id)

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Department {department_id} has invalid "
                f"name {name!r}."
            )

        if name in seen_names:
            raise ValueError(
                f"Duplicate department name: {name!r}."
            )

        seen_names.add(name)

        geometry_data = feature.get("geometry")

        if not isinstance(geometry_data, dict):
            raise ValueError(
                f"Department {department_id} has invalid "
                "runtime geometry."
            )

        geometry = shape(geometry_data)

        if not isinstance(
            geometry,
            (Polygon, MultiPolygon),
        ):
            raise ValueError(
                f"Department {department_id} has unsupported "
                f"geometry type {geometry.geom_type!r}."
            )

        if geometry.is_empty:
            raise ValueError(
                f"Department {department_id} has empty geometry."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Department {department_id} has invalid "
                "runtime geometry."
            )

    expected_ids = {
        f"{value:02d}"
        for value in range(
            1,
            EXPECTED_DEPARTMENT_COUNT + 1,
        )
    }

    if seen_ids != expected_ids:
        missing = sorted(
            expected_ids - seen_ids
        )
        unexpected = sorted(
            seen_ids - expected_ids
        )

        raise ValueError(
            "Department IDs do not match expected 01-22 range. "
            f"Missing: {missing}; "
            f"unexpected: {unexpected}."
        )


def main() -> None:
    """Process Guatemala departments and write runtime GeoJSON."""

    source = load_geojson(SOURCE_PATH)

    source_features = source["features"]

    if len(source_features) != EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} source "
            f"departments, got {len(source_features)}."
        )

    runtime_features: list[dict[str, Any]] = []
    repaired_geometry_count = 0

    for index, source_feature in enumerate(
        source_features,
        start=1,
    ):
        try:
            runtime_feature, required_repair = (
                process_department(source_feature)
            )
        except Exception as error:
            raise ValueError(
                f"Failed to process source feature "
                f"{index}: {error}"
            ) from error

        runtime_features.append(runtime_feature)

        if required_repair:
            repaired_geometry_count += 1

    runtime_features.sort(
        key=lambda feature: int(feature["id"])
    )

    runtime_geojson = {
        "type": "FeatureCollection",
        "features": runtime_features,
    }

    validate_runtime_geojson(runtime_geojson)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            runtime_geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    output_size_mb = (
        OUTPUT_PATH.stat().st_size
        / (1024 * 1024)
    )

    print("Guatemala departments processed successfully.")
    print()
    print(
        f"Source features: "
        f"{len(source_features):,}"
    )
    print(
        f"Runtime features: "
        f"{len(runtime_features):,}"
    )
    print(
        "Invalid source geometries repaired: "
        f"{repaired_geometry_count:,}"
    )
    print(
        f"Output size: "
        f"{output_size_mb:.2f} MB"
    )
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


if __name__ == "__main__":
    main()