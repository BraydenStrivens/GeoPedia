"""
Generates Bolivia's geographic telephone area-code regions.

Bolivia's nine departments are grouped into three landline calling zones:

    2 -> La Paz, Oruro, Potosí
    3 -> Santa Cruz, Beni, Pando
    4 -> Cochabamba, Chuquisaca, Tarija

Input:
    data/intermediate/countries/bolivia/admin/departments.geojson

Outputs:
    data/intermediate/countries/bolivia/area-codes/area-codes.geojson
    public/data/countries/bolivia/geojson/area-codes.geojson
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


INPUT_PATH = Path(
    "data/intermediate/countries/bolivia/admin/departments.geojson"
)

INTERMEDIATE_OUTPUT_PATH = Path(
    "data/intermediate/countries/bolivia/area-codes/area-codes.geojson"
)

RUNTIME_OUTPUT_PATH = Path(
    "public/data/countries/bolivia/geojson/area-codes.geojson"
)


EXPECTED_DEPARTMENT_COUNT = 9
EXPECTED_AREA_CODE_COUNT = 3

RUNTIME_SIMPLIFICATION_TOLERANCE = 0.01


AREA_CODE_BY_DEPARTMENT_ID = {
    "BO01": "4",  # Chuquisaca
    "BO02": "2",  # La Paz
    "BO03": "4",  # Cochabamba
    "BO04": "2",  # Oruro
    "BO05": "2",  # Potosí
    "BO06": "4",  # Tarija
    "BO07": "3",  # Santa Cruz
    "BO08": "3",  # Beni
    "BO09": "3",  # Pando
}


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


def create_area_code_features(
    department_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    geometries_by_code: dict[
        str,
        list[Any],
    ] = {}

    department_ids_by_code: dict[
        str,
        list[str],
    ] = {}

    departments_by_code: dict[
        str,
        list[str],
    ] = {}

    seen_department_ids: set[str] = set()

    for feature in department_features:
        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                "Department feature has invalid properties."
            )

        department_id = require_string(
            properties,
            "department_id",
        )

        department = require_string(
            properties,
            "department",
        )

        if department_id in seen_department_ids:
            raise ValueError(
                f"Duplicate department ID: {department_id}"
            )

        seen_department_ids.add(
            department_id
        )

        area_code = AREA_CODE_BY_DEPARTMENT_ID.get(
            department_id
        )

        if area_code is None:
            raise ValueError(
                f"No area code configured for {department_id}."
            )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            geometry_data,
            dict,
        ):
            raise ValueError(
                f"{department_id} has invalid geometry."
            )

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            raise ValueError(
                f"{department_id} has empty geometry."
            )

        geometries_by_code.setdefault(
            area_code,
            [],
        ).append(
            geometry
        )

        department_ids_by_code.setdefault(
            area_code,
            [],
        ).append(
            department_id
        )

        departments_by_code.setdefault(
            area_code,
            [],
        ).append(
            department
        )

    expected_department_ids = set(
        AREA_CODE_BY_DEPARTMENT_ID
    )

    if seen_department_ids != expected_department_ids:
        missing = sorted(
            expected_department_ids
            - seen_department_ids
        )

        extra = sorted(
            seen_department_ids
            - expected_department_ids
        )

        raise ValueError(
            "Department IDs do not match area-code configuration. "
            f"Missing: {missing}; Extra: {extra}"
        )

    output_features: list[
        dict[str, Any]
    ] = []

    for area_code in sorted(
        geometries_by_code,
        key=int,
    ):
        merged_geometry = unary_union(
            geometries_by_code[
                area_code
            ]
        )

        if merged_geometry.is_empty:
            raise ValueError(
                f"Area code {area_code} produced empty geometry."
            )

        if not merged_geometry.is_valid:
            merged_geometry = (
                merged_geometry.buffer(0)
            )

        if (
            merged_geometry.is_empty
            or not merged_geometry.is_valid
        ):
            raise ValueError(
                f"Area code {area_code} produced invalid geometry."
            )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "area_code": area_code,
                    "department_ids": sorted(
                        department_ids_by_code[
                            area_code
                        ]
                    ),
                    "departments": sorted(
                        departments_by_code[
                            area_code
                        ]
                    ),
                },
                "geometry": mapping(
                    merged_geometry
                ),
            }
        )

    return output_features


def create_runtime_features(
    features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output_features: list[
        dict[str, Any]
    ] = []

    for feature in features:
        geometry = shape(
            feature["geometry"]
        )

        simplified = geometry.simplify(
            RUNTIME_SIMPLIFICATION_TOLERANCE,
            preserve_topology=True,
        )

        if simplified.is_empty:
            raise ValueError(
                "Simplification produced empty geometry."
            )

        if not simplified.is_valid:
            simplified = simplified.buffer(
                0
            )

        if (
            simplified.is_empty
            or not simplified.is_valid
        ):
            raise ValueError(
                "Unable to repair simplified geometry."
            )

        output_features.append(
            {
                "type": "Feature",
                "properties": feature[
                    "properties"
                ],
                "geometry": mapping(
                    simplified
                ),
            }
        )

    return output_features


def main() -> None:
    print(
        "Generating Bolivia area-code regions...\n"
    )

    data = load_geojson(
        INPUT_PATH
    )

    department_features = data[
        "features"
    ]

    if (
        len(department_features)
        != EXPECTED_DEPARTMENT_COUNT
    ):
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} departments "
            f"but found {len(department_features)}."
        )

    area_code_features = (
        create_area_code_features(
            department_features
        )
    )

    if (
        len(area_code_features)
        != EXPECTED_AREA_CODE_COUNT
    ):
        raise ValueError(
            f"Expected {EXPECTED_AREA_CODE_COUNT} area-code regions "
            f"but generated {len(area_code_features)}."
        )

    write_geojson(
        INTERMEDIATE_OUTPUT_PATH,
        area_code_features,
    )

    runtime_features = (
        create_runtime_features(
            area_code_features
        )
    )

    write_geojson(
        RUNTIME_OUTPUT_PATH,
        runtime_features,
    )

    intermediate_size = (
        INTERMEDIATE_OUTPUT_PATH
        .stat()
        .st_size
    )

    runtime_size = (
        RUNTIME_OUTPUT_PATH
        .stat()
        .st_size
    )

    print(
        f"Area-code regions: {len(area_code_features)}"
    )

    print(
        "Area codes:        "
        + ", ".join(
            feature["properties"][
                "area_code"
            ]
            for feature in area_code_features
        )
    )

    print()

    for feature in area_code_features:
        properties = feature[
            "properties"
        ]

        print(
            f"  {properties['area_code']}: "
            + ", ".join(
                properties[
                    "departments"
                ]
            )
        )

    print()

    print(
        f"Intermediate: {intermediate_size / 1_000_000:.3f} MB"
    )

    print(
        f"Runtime:      {runtime_size / 1_000_000:.3f} MB"
    )

    print(
        f"Output:       {RUNTIME_OUTPUT_PATH}"
    )

    print(
        "\nBolivia area-code generation complete."
    )


if __name__ == "__main__":
    main()