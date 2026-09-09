"""
Process Guatemala municipality boundaries for GeoPedia.

Source:
    Humanitarian Data Exchange (HDX)
    Guatemala administrative boundaries dataset
    Administrative level 2 (municipalities)

Raw inputs:
    data/raw/countries/guatemala/gtm_admin_boundaries.geojson/
        gtm_admin1.geojson
        gtm_admin2.geojson

Runtime output:
    public/data/countries/guatemala/geojson/municipalities.geojson

The ADM2 source contains 342 municipality features. Each municipality already
includes both its own ADM2 p-code and the p-code of its parent department, so
no spatial join is required.

This processor:

- validates the expected HDX ADM1 and ADM2 schemas
- converts municipality codes such as GT0411 to compact GeoPedia IDs such
  as 0411
- converts parent department codes such as GT04 to 04
- validates every municipality's department against the ADM1 source
- preserves Spanish municipality names
- repairs invalid Polygon/MultiPolygon geometry if necessary
- simplifies geometry in a projected CRS
- rounds runtime coordinates
- emits only the properties GeoPedia needs
- reports duplicate municipality names for later quiz-display disambiguation
- validates the completed runtime GeoJSON

Source feature example:
    {
        "adm2_name": "Acatenango",
        "adm2_pcode": "GT0411",
        "adm1_name": "Chimaltenango",
        "adm1_pcode": "GT04",
        ...
    }

Runtime feature example:
    {
        "type": "Feature",
        "id": "0411",
        "properties": {
            "municipality_id": "0411",
            "name": "Acatenango",
            "department_id": "04"
        },
        "geometry": ...
    }
"""

from __future__ import annotations

import json
from collections import defaultdict
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

RAW_DATA_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "guatemala"
    / "gtm_admin_boundaries.geojson"
)

ADM1_SOURCE_PATH = (
    RAW_DATA_DIRECTORY
    / "gtm_admin1.geojson"
)

ADM2_SOURCE_PATH = (
    RAW_DATA_DIRECTORY
    / "gtm_admin2.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "guatemala"
    / "geojson"
    / "municipalities.geojson"
)


SOURCE_CRS = "EPSG:4326"

# Guatemala falls primarily within UTM zone 15N. Using a projected CRS lets
# simplification and precision operate in meters rather than degrees.
PROCESSING_CRS = "EPSG:32615"

SIMPLIFY_TOLERANCE_METERS = 100.0
PRECISION_GRID_METERS = 0.1
COORDINATE_DECIMAL_PLACES = 6

EXPECTED_DEPARTMENT_COUNT = 22
EXPECTED_MUNICIPALITY_COUNT = 342

EXPECTED_ADM1_PROPERTIES = {
    "adm1_name",
    "adm1_pcode",
}

EXPECTED_ADM2_PROPERTIES = {
    "adm2_name",
    "adm2_pcode",
    "adm1_name",
    "adm1_pcode",
}

EXPECTED_RUNTIME_PROPERTIES = {
    "municipality_id",
    "name",
    "department_id",
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
        raise FileNotFoundError(
            f"Source file does not exist: {path}"
        )

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
    Convert an HDX ADM1 p-code such as GT04 into GeoPedia ID "04".
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


def normalize_municipality_id(value: Any) -> str:
    """
    Convert an HDX ADM2 p-code such as GT0411 into GeoPedia ID "0411".
    """

    if not isinstance(value, str):
        raise ValueError(
            f"Municipality p-code must be a string, got {value!r}."
        )

    if len(value) != 6 or not value.startswith("GT"):
        raise ValueError(
            f"Unexpected Guatemala ADM2 p-code format: {value!r}."
        )

    municipality_id = value[2:]

    if not municipality_id.isdigit():
        raise ValueError(
            f"Municipality p-code has non-numeric suffix: {value!r}."
        )

    return municipality_id


def load_departments() -> dict[str, str]:
    """
    Load and validate ADM1 department IDs and names.

    Returns:
        Mapping of normalized department ID to department name.
    """

    source = load_geojson(ADM1_SOURCE_PATH)
    features = source["features"]

    if len(features) != EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} ADM1 features, "
            f"got {len(features)}."
        )

    departments: dict[str, str] = {}

    for index, feature in enumerate(
        features,
        start=1,
    ):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"ADM1 feature {index} has invalid properties."
            )

        missing_properties = (
            EXPECTED_ADM1_PROPERTIES
            - properties.keys()
        )

        if missing_properties:
            raise ValueError(
                f"ADM1 feature {index} is missing required "
                f"properties: {sorted(missing_properties)}"
            )

        department_id = normalize_department_id(
            properties.get("adm1_pcode")
        )

        name = properties.get("adm1_name")

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"ADM1 feature {index} has invalid "
                f"department name {name!r}."
            )

        name = name.strip()

        if department_id in departments:
            raise ValueError(
                f"Duplicate department ID in ADM1 source: "
                f"{department_id!r}."
            )

        departments[department_id] = name

    expected_ids = {
        f"{value:02d}"
        for value in range(
            1,
            EXPECTED_DEPARTMENT_COUNT + 1,
        )
    }

    actual_ids = set(departments)

    if actual_ids != expected_ids:
        missing = sorted(
            expected_ids - actual_ids
        )
        unexpected = sorted(
            actual_ids - expected_ids
        )

        raise ValueError(
            "ADM1 department IDs do not match expected 01-22 range. "
            f"Missing: {missing}; "
            f"unexpected: {unexpected}."
        )

    return departments


def extract_polygonal_geometry(
    geometry: Any,
) -> Polygon | MultiPolygon:
    """
    Extract polygonal content from a repaired Shapely geometry.

    Geometry repair can produce GeometryCollections containing polygons,
    lines, or points. GeoPedia municipality boundaries only need polygonal
    components.
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
    Repair, simplify, and normalize one municipality geometry.

    Returns:
        A tuple containing:
        - processed Polygon/MultiPolygon
        - whether the original source geometry required validity repair
    """

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            "Source geometry is empty."
        )

    if not isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        raise ValueError(
            f"Expected Polygon or MultiPolygon, "
            f"got {geometry.geom_type!r}."
        )

    required_repair = not geometry.is_valid

    if required_repair:
        geometry = make_valid(geometry)

    geometry = extract_polygonal_geometry(
        geometry
    )

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
        projected = extract_polygonal_geometry(
            projected
        )

    simplified = projected.simplify(
        SIMPLIFY_TOLERANCE_METERS,
        preserve_topology=True,
    )

    simplified = extract_polygonal_geometry(
        simplified
    )

    if not simplified.is_valid:
        simplified = make_valid(simplified)
        simplified = extract_polygonal_geometry(
            simplified
        )

    runtime_geometry = transform(
        TO_RUNTIME_CRS,
        simplified,
    )

    runtime_geometry = extract_polygonal_geometry(
        runtime_geometry
    )

    if runtime_geometry.is_empty:
        raise ValueError(
            "Processed geometry is empty."
        )

    if not runtime_geometry.is_valid:
        runtime_geometry = make_valid(
            runtime_geometry
        )
        runtime_geometry = extract_polygonal_geometry(
            runtime_geometry
        )

    return runtime_geometry, required_repair


def round_coordinates(value: Any) -> Any:
    """Recursively round GeoJSON coordinates to runtime precision."""

    if isinstance(value, float):
        return round(
            value,
            COORDINATE_DECIMAL_PLACES,
        )

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


def process_municipality(
    feature: dict[str, Any],
    departments: dict[str, str],
) -> tuple[dict[str, Any], bool]:
    """
    Convert one HDX ADM2 source feature into GeoPedia runtime format.
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
        EXPECTED_ADM2_PROPERTIES
        - properties.keys()
    )

    if missing_properties:
        raise ValueError(
            "Source feature is missing required properties: "
            f"{sorted(missing_properties)}"
        )

    municipality_id = normalize_municipality_id(
        properties.get("adm2_pcode")
    )

    department_id = normalize_department_id(
        properties.get("adm1_pcode")
    )

    name = properties.get("adm2_name")

    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f"Municipality {municipality_id} has invalid "
            f"name {name!r}."
        )

    name = name.strip()

    source_department_name = properties.get(
        "adm1_name"
    )

    if (
        not isinstance(source_department_name, str)
        or not source_department_name.strip()
    ):
        raise ValueError(
            f"Municipality {municipality_id} has invalid "
            f"parent department name "
            f"{source_department_name!r}."
        )

    source_department_name = (
        source_department_name.strip()
    )

    expected_department_name = departments.get(
        department_id
    )

    if expected_department_name is None:
        raise ValueError(
            f"Municipality {municipality_id} references "
            f"unknown department {department_id!r}."
        )

    if source_department_name != expected_department_name:
        raise ValueError(
            f"Municipality {municipality_id} has parent "
            f"department name {source_department_name!r}, "
            f"but ADM1 {department_id} is "
            f"{expected_department_name!r}."
        )

    # Guatemala ADM2 codes are hierarchical. The first two digits of the
    # municipality ID should equal the parent ADM1 department ID.
    if municipality_id[:2] != department_id:
        raise ValueError(
            f"Municipality {municipality_id} does not match "
            f"parent department {department_id}."
        )

    geometry_data = feature.get("geometry")

    if not isinstance(geometry_data, dict):
        raise ValueError(
            f"Municipality {municipality_id} has invalid geometry."
        )

    geometry, required_repair = repair_geometry(
        geometry_data
    )

    runtime_feature = {
        "type": "Feature",
        "id": municipality_id,
        "properties": {
            "municipality_id": municipality_id,
            "name": name,
            "department_id": department_id,
        },
        "geometry": geometry_to_geojson(
            geometry
        ),
    }

    return runtime_feature, required_repair


def get_duplicate_names(
    features: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Return municipality names that occur more than once nationwide.

    The runtime GeoJSON keeps the canonical municipality name unchanged.
    Duplicate-name disambiguation belongs in the generated quiz display text.
    """

    by_name: dict[str, list[dict[str, Any]]] = defaultdict(
        list
    )

    for feature in features:
        properties = feature["properties"]
        by_name[properties["name"]].append(
            feature
        )

    return {
        name: matching_features
        for name, matching_features in by_name.items()
        if len(matching_features) > 1
    }


def validate_runtime_geojson(
    geojson: dict[str, Any],
    departments: dict[str, str],
) -> None:
    """Validate the completed GeoPedia municipality FeatureCollection."""

    if geojson.get("type") != "FeatureCollection":
        raise ValueError(
            "Runtime output is not a FeatureCollection."
        )

    features = geojson.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Runtime output does not contain a features array."
        )

    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"got {len(features)}."
        )

    seen_ids: set[str] = set()

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

        actual_properties = set(
            properties.keys()
        )

        if actual_properties != EXPECTED_RUNTIME_PROPERTIES:
            raise ValueError(
                f"Feature {feature_id!r} has unexpected properties. "
                f"Expected {sorted(EXPECTED_RUNTIME_PROPERTIES)}, "
                f"got {sorted(actual_properties)}."
            )

        municipality_id = properties.get(
            "municipality_id"
        )
        name = properties.get("name")
        department_id = properties.get(
            "department_id"
        )

        if feature_id != municipality_id:
            raise ValueError(
                f"Feature ID {feature_id!r} does not match "
                f"municipality_id {municipality_id!r}."
            )

        if (
            not isinstance(municipality_id, str)
            or len(municipality_id) != 4
            or not municipality_id.isdigit()
        ):
            raise ValueError(
                f"Invalid municipality_id format: "
                f"{municipality_id!r}."
            )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: "
                f"{municipality_id!r}."
            )

        seen_ids.add(municipality_id)

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Municipality {municipality_id} has invalid "
                f"name {name!r}."
            )

        if (
            not isinstance(department_id, str)
            or len(department_id) != 2
            or not department_id.isdigit()
        ):
            raise ValueError(
                f"Municipality {municipality_id} has invalid "
                f"department_id {department_id!r}."
            )

        if department_id not in departments:
            raise ValueError(
                f"Municipality {municipality_id} references "
                f"unknown department {department_id!r}."
            )

        if municipality_id[:2] != department_id:
            raise ValueError(
                f"Municipality {municipality_id} does not match "
                f"department {department_id}."
            )

        geometry_data = feature.get("geometry")

        if not isinstance(geometry_data, dict):
            raise ValueError(
                f"Municipality {municipality_id} has invalid "
                "runtime geometry."
            )

        geometry = shape(
            geometry_data
        )

        if not isinstance(
            geometry,
            (Polygon, MultiPolygon),
        ):
            raise ValueError(
                f"Municipality {municipality_id} has unsupported "
                f"geometry type {geometry.geom_type!r}."
            )

        if geometry.is_empty:
            raise ValueError(
                f"Municipality {municipality_id} has empty geometry."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Municipality {municipality_id} has invalid "
                "runtime geometry."
            )


def main() -> None:
    """Process Guatemala municipalities and write runtime GeoJSON."""

    departments = load_departments()

    source = load_geojson(
        ADM2_SOURCE_PATH
    )

    source_features = source["features"]

    if len(source_features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} source "
            f"municipalities, got {len(source_features)}."
        )

    runtime_features: list[dict[str, Any]] = []
    repaired_geometry_count = 0

    department_counts: dict[str, int] = defaultdict(
        int
    )

    for index, source_feature in enumerate(
        source_features,
        start=1,
    ):
        try:
            runtime_feature, required_repair = (
                process_municipality(
                    source_feature,
                    departments,
                )
            )
        except Exception as error:
            raise ValueError(
                f"Failed to process ADM2 source feature "
                f"{index}: {error}"
            ) from error

        runtime_features.append(
            runtime_feature
        )

        department_id = runtime_feature[
            "properties"
        ]["department_id"]

        department_counts[
            department_id
        ] += 1

        if required_repair:
            repaired_geometry_count += 1

    runtime_features.sort(
        key=lambda feature: int(feature["id"])
    )

    runtime_geojson = {
        "type": "FeatureCollection",
        "features": runtime_features,
    }

    validate_runtime_geojson(
        runtime_geojson,
        departments,
    )

    duplicate_names = get_duplicate_names(
        runtime_features
    )

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

    print(
        "Guatemala municipalities processed successfully."
    )
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
        f"Departments referenced: "
        f"{len(department_counts):,}"
    )

    print(
        "Invalid source geometries repaired: "
        f"{repaired_geometry_count:,}"
    )

    print(
        f"Duplicate municipality names: "
        f"{len(duplicate_names):,}"
    )

    if duplicate_names:
        print()

        print("Duplicate names:")

        for name in sorted(
            duplicate_names
        ):
            matching_features = duplicate_names[
                name
            ]

            displays = []

            for feature in matching_features:
                properties = feature[
                    "properties"
                ]

                department_id = properties[
                    "department_id"
                ]

                displays.append(
                    f"{properties['municipality_id']} "
                    f"({departments[department_id]})"
                )

            print(
                f"  {name}: "
                + ", ".join(displays)
            )

    print()

    print(
        f"Output size: "
        f"{output_size_mb:.2f} MB"
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )

    print(
        "Validation passed."
    )


if __name__ == "__main__":
    main()