"""
Generates TypeScript dictionaries used by Bolivia's administrative quizzes.

Inputs:
    data/intermediate/countries/bolivia/admin/departments.geojson
    data/intermediate/countries/bolivia/admin/provinces.geojson
    data/intermediate/countries/bolivia/admin/municipalities.geojson

Output:
    src/data/countries/bolivia/admin.ts
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


INPUT_DIRECTORY = Path(
    "data/intermediate/countries/bolivia/admin"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/south-america/bolivia/data/admin.ts"
)

DEPARTMENTS_PATH = (
    INPUT_DIRECTORY / "departments.geojson"
)

PROVINCES_PATH = (
    INPUT_DIRECTORY / "provinces.geojson"
)

MUNICIPALITIES_PATH = (
    INPUT_DIRECTORY / "municipalities.geojson"
)


def load_features(
    path: Path,
) -> list[dict[str, Any]]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return features


def ts_string(
    value: str,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def generate_departments(
    features: list[dict[str, Any]],
) -> str:
    entries = []

    for feature in sorted(
        features,
        key=lambda item: item["properties"]["department_id"],
    ):
        properties = feature[
            "properties"
        ]

        department_id = properties[
            "department_id"
        ]

        department = properties[
            "department"
        ]

        entries.append(
            f"  {ts_string(department_id)}: "
            f"{ts_string(department)},"
        )

    return "\n".join(
        entries
    )


def generate_provinces(
    features: list[dict[str, Any]],
) -> str:
    entries = []

    for feature in sorted(
        features,
        key=lambda item: item["properties"]["province_id"],
    ):
        properties = feature[
            "properties"
        ]

        province_id = properties[
            "province_id"
        ]

        province = properties[
            "province"
        ]

        department_id = properties[
            "department_id"
        ]

        entries.append(
            f"  {ts_string(province_id)}: {{ "
            f"name: {ts_string(province)}, "
            f"departmentId: {ts_string(department_id)} "
            f"}},"
        )

    return "\n".join(
        entries
    )


def generate_municipalities(
    features: list[dict[str, Any]],
) -> str:
    entries = []

    for feature in sorted(
        features,
        key=lambda item: item["properties"]["municipality_id"],
    ):
        properties = feature[
            "properties"
        ]

        municipality_id = properties[
            "municipality_id"
        ]

        municipality = properties[
            "municipality"
        ]

        province_id = properties[
            "province_id"
        ]

        department_id = properties[
            "department_id"
        ]

        entries.append(
            f"  {ts_string(municipality_id)}: {{ "
            f"name: {ts_string(municipality)}, "
            f"provinceId: {ts_string(province_id)}, "
            f"departmentId: {ts_string(department_id)} "
            f"}},"
        )

    return "\n".join(
        entries
    )


def main() -> None:
    departments = load_features(
        DEPARTMENTS_PATH
    )

    provinces = load_features(
        PROVINCES_PATH
    )

    municipalities = load_features(
        MUNICIPALITIES_PATH
    )

    if len(departments) != 9:
        raise ValueError(
            f"Expected 9 departments, found {len(departments)}."
        )

    if len(provinces) != 112:
        raise ValueError(
            f"Expected 112 provinces, found {len(provinces)}."
        )

    if len(municipalities) != 339:
        raise ValueError(
            f"Expected 339 municipalities, found {len(municipalities)}."
        )

    output = f"""\
/**
 * Generated from Bolivia's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/bolivia/generate/admin-quiz-data.py
 */

export const BOLIVIA_DEPARTMENTS_BY_ID = {{
{generate_departments(departments)}
}} as const;

export const BOLIVIA_PROVINCES_BY_ID = {{
{generate_provinces(provinces)}
}} as const;

export const BOLIVIA_MUNICIPALITIES_BY_ID = {{
{generate_municipalities(municipalities)}
}} as const;
"""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print(
        "Generated Bolivia admin quiz data:"
    )

    print(
        f"  Departments:    {len(departments)}"
    )

    print(
        f"  Provinces:      {len(provinces)}"
    )

    print(
        f"  Municipalities: {len(municipalities)}"
    )

    print(
        f"\nOutput: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()