"""
Generates TypeScript data used by Paraguay's administrative quizzes.

Inputs:
    data/intermediate/countries/paraguay/admin/departments.geojson
    data/intermediate/countries/paraguay/admin/districts.geojson

Output:
    src/data/countries/paraguay/admin.ts
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


INPUT_DIRECTORY = Path(
    "data/intermediate/countries/paraguay/admin"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/south-america/paraguay/data/admin.ts"
)

DEPARTMENTS_PATH = (
    INPUT_DIRECTORY
    / "departments.geojson"
)

DISTRICTS_PATH = (
    INPUT_DIRECTORY
    / "districts.geojson"
)


def load_features(
    path: Path,
) -> list[dict[str, Any]]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return features


def format_name(
    value: str,
) -> str:
    """
    Converts source all-uppercase names to display case.

    Examples:
        ASUNCIÓN -> Asunción
        ALTO PARANÁ -> Alto Paraná
        SARGENTO JOSÉ FÉLIX LÓPEZ -> Sargento José Félix López
        AZOTE'Y -> Azote'y
    """
    return value.title()


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
    entries: list[str] = []

    for feature in sorted(
        features,
        key=lambda item:
        item["properties"]["department_id"],
    ):
        properties = feature[
            "properties"
        ]

        department_id = properties[
            "department_id"
        ]

        department = format_name(
            properties[
                "department"
            ]
        )

        entries.append(
            f"  {ts_string(department_id)}: "
            f"{ts_string(department)},"
        )

    return "\n".join(
        entries
    )


def generate_districts(
    features: list[dict[str, Any]],
) -> str:
    entries: list[str] = []

    for feature in sorted(
        features,
        key=lambda item:
        item["properties"]["district_id"],
    ):
        properties = feature[
            "properties"
        ]

        district_id = properties[
            "district_id"
        ]

        district = format_name(
            properties[
                "district"
            ]
        )

        department_id = properties[
            "department_id"
        ]

        entries.append(
            f"  {ts_string(district_id)}: {{ "
            f"name: {ts_string(district)}, "
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

    districts = load_features(
        DISTRICTS_PATH
    )

    if len(
        departments
    ) != 18:
        raise ValueError(
            f"Expected 18 departments, found {len(departments)}."
        )

    if len(
        districts
    ) != 250:
        raise ValueError(
            f"Expected 250 districts, found {len(districts)}."
        )

    output = f"""\
/**
 * Generated from Paraguay's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/paraguay/generate/admin-quiz-data.py
 */

export const PARAGUAY_DEPARTMENTS_BY_ID = {{
{generate_departments(departments)}
}} as const;

export const PARAGUAY_DISTRICTS_BY_ID = {{
{generate_districts(districts)}
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
        "Generated Paraguay admin quiz data:"
    )

    print(
        f"  Departments: {len(departments)}"
    )

    print(
        f"  Districts:   {len(districts)}"
    )

    print(
        f"\nOutput: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()