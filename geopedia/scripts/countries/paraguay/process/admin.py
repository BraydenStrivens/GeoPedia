"""
Processes Paraguay's ADM1 and ADM2 shapefiles into GeoPedia's
intermediate administrative GeoJSON format.

Hierarchy:
    ADM1 -> Department-level units
            (17 departments + Asunción)
    ADM2 -> Districts

Inputs:
    data/raw/countries/paraguay/pry_adm_dgeec_2020_shp/
        pry_admbnda_adm1_DGEEC_2020.shp
        pry_admbnda_adm2_DGEEC_2020.shp

Outputs:
    data/intermediate/countries/paraguay/admin/departments.geojson
    data/intermediate/countries/paraguay/admin/districts.geojson

The source shapefiles use EPSG:4674. Output is reprojected to EPSG:4326.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import mapping


RAW_DIRECTORY = Path(
    "data/raw/countries/paraguay/pry_adm_dgeec_2020_shp"
)

INTERMEDIATE_DIRECTORY = Path(
    "data/intermediate/countries/paraguay/admin"
)

ADM1_PATH = (
    RAW_DIRECTORY
    / "pry_admbnda_adm1_DGEEC_2020.shp"
)

ADM2_PATH = (
    RAW_DIRECTORY
    / "pry_admbnda_adm2_DGEEC_2020.shp"
)

DEPARTMENTS_OUTPUT_PATH = (
    INTERMEDIATE_DIRECTORY
    / "departments.geojson"
)

DISTRICTS_OUTPUT_PATH = (
    INTERMEDIATE_DIRECTORY
    / "districts.geojson"
)


EXPECTED_DEPARTMENT_COUNT = 18
EXPECTED_DISTRICT_COUNT = 250

OUTPUT_CRS = "EPSG:4326"


def require_string(
    properties: dict[str, Any],
    key: str,
) -> str:
    value = properties.get(
        key
    )

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f'Missing string property "{key}".'
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f'Empty string property "{key}".'
        )

    return value


def load_layer(
    path: Path,
) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
        )

    gdf = gpd.read_file(
        path
    )

    if gdf.crs is None:
        raise ValueError(
            f"{path} has no CRS."
        )

    if gdf.empty:
        raise ValueError(
            f"{path} contains no features."
        )

    return gdf.to_crs(
        OUTPUT_CRS
    )


def validate_geometry(
    geometry: Any,
    feature_id: str,
) -> None:
    if geometry is None:
        raise ValueError(
            f"{feature_id} has no geometry."
        )

    if geometry.is_empty:
        raise ValueError(
            f"{feature_id} has empty geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{feature_id} has unsupported geometry type: "
            f"{geometry.geom_type}"
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{feature_id} has invalid geometry."
        )


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
    gdf: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:
    features: list[
        dict[str, Any]
    ] = []

    seen_ids: set[str] = set()

    for _, row in gdf.iterrows():
        source_properties = row.to_dict()

        department_id = require_string(
            source_properties,
            "ADM1_PCODE",
        )

        department = require_string(
            source_properties,
            "ADM1_ES",
        )

        if department_id in seen_ids:
            raise ValueError(
                f"Duplicate department ID: {department_id}"
            )

        seen_ids.add(
            department_id
        )

        geometry = row.geometry

        validate_geometry(
            geometry,
            department_id,
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "department_id": department_id,
                    "department": department,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    features.sort(
        key=lambda feature:
        feature["properties"]["department_id"]
    )

    return features


def process_districts(
    gdf: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:
    features: list[
        dict[str, Any]
    ] = []

    seen_ids: set[str] = set()

    for _, row in gdf.iterrows():
        source_properties = row.to_dict()

        district_id = require_string(
            source_properties,
            "ADM2_PCODE",
        )

        district = require_string(
            source_properties,
            "ADM2_ES",
        )

        department_id = require_string(
            source_properties,
            "ADM1_PCODE",
        )

        department = require_string(
            source_properties,
            "ADM1_ES",
        )

        if district_id in seen_ids:
            raise ValueError(
                f"Duplicate district ID: {district_id}"
            )

        seen_ids.add(
            district_id
        )

        if not district_id.startswith(
            department_id
        ):
            raise ValueError(
                f"District {district_id} does not belong to "
                f"department {department_id}."
            )

        geometry = row.geometry

        validate_geometry(
            geometry,
            district_id,
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "district_id": district_id,
                    "district": district,
                    "department_id": department_id,
                    "department": department,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    features.sort(
        key=lambda feature:
        feature["properties"]["district_id"]
    )

    return features


def validate_counts(
    departments: list[dict[str, Any]],
    districts: list[dict[str, Any]],
) -> None:
    if (
        len(departments)
        != EXPECTED_DEPARTMENT_COUNT
    ):
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} departments "
            f"but found {len(departments)}."
        )

    if (
        len(districts)
        != EXPECTED_DISTRICT_COUNT
    ):
        raise ValueError(
            f"Expected {EXPECTED_DISTRICT_COUNT} districts "
            f"but found {len(districts)}."
        )


def validate_hierarchy(
    departments: list[dict[str, Any]],
    districts: list[dict[str, Any]],
) -> None:
    department_names_by_id = {
        feature["properties"]["department_id"]:
        feature["properties"]["department"]
        for feature in departments
    }

    for feature in districts:
        properties = feature[
            "properties"
        ]

        department_id = properties[
            "department_id"
        ]

        department = properties[
            "department"
        ]

        expected_department = (
            department_names_by_id.get(
                department_id
            )
        )

        if expected_department is None:
            raise ValueError(
                f"District {properties['district_id']} references "
                f"unknown department {department_id}."
            )

        if department != expected_department:
            raise ValueError(
                f"District {properties['district_id']} has department "
                f"name {department!r}, but {department_id} is "
                f"{expected_department!r}."
            )


def main() -> None:
    print(
        "Processing Paraguay administrative boundaries...\n"
    )

    adm1 = load_layer(
        ADM1_PATH
    )

    adm2 = load_layer(
        ADM2_PATH
    )

    departments = process_departments(
        adm1
    )

    districts = process_districts(
        adm2
    )

    validate_counts(
        departments,
        districts,
    )

    validate_hierarchy(
        departments,
        districts,
    )

    write_geojson(
        DEPARTMENTS_OUTPUT_PATH,
        departments,
    )

    write_geojson(
        DISTRICTS_OUTPUT_PATH,
        districts,
    )

    print(
        f"Departments: {len(departments)}"
    )

    print(
        f"Districts:   {len(districts)}"
    )

    print(
        f"Output CRS:  {OUTPUT_CRS}"
    )

    print(
        "\nOutputs:"
    )

    print(
        f"  {DEPARTMENTS_OUTPUT_PATH}"
    )

    print(
        f"  {DISTRICTS_OUTPUT_PATH}"
    )

    print(
        "\nParaguay administrative processing complete."
    )


if __name__ == "__main__":
    main()