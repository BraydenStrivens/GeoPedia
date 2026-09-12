"""
Processes Bolivia's administrative boundary GeoJSON files into GeoPedia's
simplified intermediate format.

Hierarchy:
    ADM1 -> Departments
    ADM2 -> Provinces
    ADM3 -> Municipalities

Inputs:
    data/raw/countries/bolivia/bol_admin_boundaries.geojson/bol_admin1.geojson
    data/raw/countries/bolivia/bol_admin_boundaries.geojson/bol_admin2.geojson
    data/raw/countries/bolivia/bol_admin_boundaries.geojson/bol_admin3.geojson

Outputs:
    data/intermediate/countries/bolivia/admin/departments.geojson
    data/intermediate/countries/bolivia/admin/provinces.geojson
    data/intermediate/countries/bolivia/admin/municipalities.geojson
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RAW_DIRECTORY = Path(
    "data/raw/countries/bolivia/bol_admin_boundaries.geojson"
)

INTERMEDIATE_DIRECTORY = Path(
    "data/intermediate/countries/bolivia/admin"
)

ADM1_PATH = RAW_DIRECTORY / "bol_admin1.geojson"
ADM2_PATH = RAW_DIRECTORY / "bol_admin2.geojson"
ADM3_PATH = RAW_DIRECTORY / "bol_admin3.geojson"

DEPARTMENTS_OUTPUT_PATH = (
    INTERMEDIATE_DIRECTORY / "departments.geojson"
)

PROVINCES_OUTPUT_PATH = (
    INTERMEDIATE_DIRECTORY / "provinces.geojson"
)

MUNICIPALITIES_OUTPUT_PATH = (
    INTERMEDIATE_DIRECTORY / "municipalities.geojson"
)


EXPECTED_DEPARTMENT_COUNT = 9
EXPECTED_PROVINCE_COUNT = 112
EXPECTED_MUNICIPALITY_COUNT = 339


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def require_string(
    properties: dict[str, Any],
    key: str,
) -> str:
    value = properties.get(key)

    if not isinstance(value, str):
        raise ValueError(
            f'Missing string property "{key}".'
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f'Empty string property "{key}".'
        )

    return value


def validate_geometry(
    feature: dict[str, Any],
    feature_id: str,
) -> dict[str, Any]:
    geometry = feature.get("geometry")

    if not isinstance(geometry, dict):
        raise ValueError(
            f"{feature_id} has invalid geometry."
        )

    geometry_type = geometry.get("type")

    if geometry_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{feature_id} has unsupported geometry type: "
            f"{geometry_type!r}"
        )

    return geometry


def write_geojson(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def process_departments(
    source_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output_features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for feature in source_features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM1 feature has invalid properties."
            )

        department_id = require_string(
            properties,
            "adm1_pcode",
        )

        department = require_string(
            properties,
            "adm1_name",
        )

        if department_id in seen_ids:
            raise ValueError(
                f"Duplicate department ID: {department_id}"
            )

        seen_ids.add(
            department_id
        )

        geometry = validate_geometry(
            feature,
            department_id,
        )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "department_id": department_id,
                    "department": department,
                },
                "geometry": geometry,
            }
        )

    return output_features


def process_provinces(
    source_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output_features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for feature in source_features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM2 feature has invalid properties."
            )

        province_id = require_string(
            properties,
            "adm2_pcode",
        )

        province = require_string(
            properties,
            "adm2_name",
        )

        department_id = require_string(
            properties,
            "adm1_pcode",
        )

        department = require_string(
            properties,
            "adm1_name",
        )

        if province_id in seen_ids:
            raise ValueError(
                f"Duplicate province ID: {province_id}"
            )

        seen_ids.add(
            province_id
        )

        if not province_id.startswith(
            department_id
        ):
            raise ValueError(
                f"Province {province_id} does not belong to "
                f"department {department_id}."
            )

        geometry = validate_geometry(
            feature,
            province_id,
        )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "province_id": province_id,
                    "province": province,
                    "department_id": department_id,
                    "department": department,
                },
                "geometry": geometry,
            }
        )

    return output_features


def process_municipalities(
    source_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output_features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for feature in source_features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM3 feature has invalid properties."
            )

        municipality_id = require_string(
            properties,
            "adm3_pcode",
        )

        municipality = require_string(
            properties,
            "adm3_name",
        )

        province_id = require_string(
            properties,
            "adm2_pcode",
        )

        province = require_string(
            properties,
            "adm2_name",
        )

        department_id = require_string(
            properties,
            "adm1_pcode",
        )

        department = require_string(
            properties,
            "adm1_name",
        )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id}"
            )

        seen_ids.add(
            municipality_id
        )

        if not municipality_id.startswith(
            province_id
        ):
            raise ValueError(
                f"Municipality {municipality_id} does not belong to "
                f"province {province_id}."
            )

        if not province_id.startswith(
            department_id
        ):
            raise ValueError(
                f"Province {province_id} does not belong to "
                f"department {department_id}."
            )

        geometry = validate_geometry(
            feature,
            municipality_id,
        )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "municipality_id": municipality_id,
                    "municipality": municipality,
                    "province_id": province_id,
                    "province": province,
                    "department_id": department_id,
                    "department": department,
                },
                "geometry": geometry,
            }
        )

    return output_features


def validate_count(
    label: str,
    features: list[dict[str, Any]],
    expected_count: int,
) -> None:
    actual_count = len(features)

    if actual_count != expected_count:
        raise ValueError(
            f"{label}: expected {expected_count} features "
            f"but found {actual_count}."
        )


def main() -> None:
    print(
        "Processing Bolivia administrative boundaries...\n"
    )

    adm1 = load_geojson(
        ADM1_PATH
    )

    adm2 = load_geojson(
        ADM2_PATH
    )

    adm3 = load_geojson(
        ADM3_PATH
    )

    departments = process_departments(
        adm1["features"]
    )

    provinces = process_provinces(
        adm2["features"]
    )

    municipalities = process_municipalities(
        adm3["features"]
    )

    validate_count(
        "Departments",
        departments,
        EXPECTED_DEPARTMENT_COUNT,
    )

    validate_count(
        "Provinces",
        provinces,
        EXPECTED_PROVINCE_COUNT,
    )

    validate_count(
        "Municipalities",
        municipalities,
        EXPECTED_MUNICIPALITY_COUNT,
    )

    write_geojson(
        DEPARTMENTS_OUTPUT_PATH,
        departments,
    )

    write_geojson(
        PROVINCES_OUTPUT_PATH,
        provinces,
    )

    write_geojson(
        MUNICIPALITIES_OUTPUT_PATH,
        municipalities,
    )

    print(
        f"Departments:    {len(departments)}"
    )

    print(
        f"Provinces:      {len(provinces)}"
    )

    print(
        f"Municipalities: {len(municipalities)}"
    )

    print(
        "\nOutputs:"
    )

    print(
        f"  {DEPARTMENTS_OUTPUT_PATH}"
    )

    print(
        f"  {PROVINCES_OUTPUT_PATH}"
    )

    print(
        f"  {MUNICIPALITIES_OUTPUT_PATH}"
    )

    print(
        "\nBolivia administrative processing complete."
    )


if __name__ == "__main__":
    main()