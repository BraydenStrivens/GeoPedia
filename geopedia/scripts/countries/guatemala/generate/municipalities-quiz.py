"""
Generate Guatemala's municipality quiz configuration for GeoPedia.

Input:
    public/data/countries/guatemala/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/guatemala/guatemalaMunicipalitiesQuiz.ts

The processed runtime GeoJSON contains 342 municipalities with stable
four-digit municipality IDs and parent department IDs.

Municipality names that are unique nationwide are displayed unchanged.
Duplicate municipality names are disambiguated by appending the parent
department name.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "guatemala"
    / "geojson"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "guatemala"
    / "guatemalaMunicipalitiesQuiz.ts"
)

EXPECTED_MUNICIPALITY_COUNT = 342

DEPARTMENT_NAMES_BY_ID = {
    "01": "Guatemala",
    "02": "El Progreso",
    "03": "Sacatepéquez",
    "04": "Chimaltenango",
    "05": "Escuintla",
    "06": "Santa Rosa",
    "07": "Sololá",
    "08": "Totonicapán",
    "09": "Quetzaltenango",
    "10": "Suchitepéquez",
    "11": "Retalhuleu",
    "12": "San Marcos",
    "13": "Huehuetenango",
    "14": "Quiché",
    "15": "Baja Verapaz",
    "16": "Alta Verapaz",
    "17": "Petén",
    "18": "Izabal",
    "19": "Zacapa",
    "20": "Chiquimula",
    "21": "Jalapa",
    "22": "Jutiapa",
}


def load_geojson() -> dict[str, Any]:
    """Load and validate the processed municipality FeatureCollection."""

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"Municipality GeoJSON does not exist: {SOURCE_PATH}"
        )

    with SOURCE_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected FeatureCollection, got {data.get('type')!r}."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Municipality GeoJSON does not contain a valid features array."
        )

    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"got {len(features)}."
        )

    return data


def escape_typescript_string(value: str) -> str:
    """Escape a value for use inside a TypeScript double-quoted string."""

    return (
        value
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def read_municipalities(
    data: dict[str, Any],
) -> list[dict[str, str]]:
    """Extract and validate municipality quiz data from runtime features."""

    municipalities: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for index, feature in enumerate(
        data["features"],
        start=1,
    ):
        feature_id = feature.get("id")
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {index} does not contain valid properties."
            )

        municipality_id = properties.get("municipality_id")
        name = properties.get("name")
        department_id = properties.get("department_id")

        if feature_id != municipality_id:
            raise ValueError(
                f"Feature {index} ID {feature_id!r} does not match "
                f"municipality_id {municipality_id!r}."
            )

        if (
            not isinstance(municipality_id, str)
            or len(municipality_id) != 4
            or not municipality_id.isdigit()
        ):
            raise ValueError(
                f"Invalid municipality ID: {municipality_id!r}."
            )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id!r}."
            )

        seen_ids.add(municipality_id)

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Municipality {municipality_id} has invalid name {name!r}."
            )

        if (
            not isinstance(department_id, str)
            or department_id not in DEPARTMENT_NAMES_BY_ID
        ):
            raise ValueError(
                f"Municipality {municipality_id} has invalid "
                f"department ID {department_id!r}."
            )

        if municipality_id[:2] != department_id:
            raise ValueError(
                f"Municipality {municipality_id} does not match "
                f"department {department_id}."
            )

        municipalities.append(
            {
                "id": municipality_id,
                "name": name,
                "department_id": department_id,
            }
        )

    municipalities.sort(
        key=lambda municipality: int(municipality["id"])
    )

    return municipalities


def create_typescript(
    municipalities: list[dict[str, str]],
) -> str:
    """Generate the complete Guatemala municipality quiz TypeScript file."""

    name_counts = Counter(
        municipality["name"]
        for municipality in municipalities
    )

    lines = [
        'import { GUATEMALA_DEPARTMENT_NAMES_BY_ID } from '
        '"@/constants/guatemalaSubdivisions";',
        'import type { FeatureQuiz } from "@/types/quiz";',
        "",
        "/**",
        " * All Guatemalan municipality questions keyed by municipality ID.",
        " * Duplicate municipality names are disambiguated with their parent",
        " * department names.",
        " */",
        "const GUATEMALA_MUNICIPALITY_QUESTIONS = [",
    ]

    for municipality in municipalities:
        municipality_id = municipality["id"]
        name = municipality["name"]
        department_id = municipality["department_id"]

        if name_counts[name] > 1:
            display = (
                f"{name} "
                f"({DEPARTMENT_NAMES_BY_ID[department_id]})"
            )
        else:
            display = name

        escaped_display = escape_typescript_string(display)

        lines.extend(
            [
                "  {",
                f'    answer: "{municipality_id}",',
                f'    display: "{escaped_display}",',
                "  },",
            ]
        )

    lines.extend(
        [
            "];",
            "",
            "/**",
            " * Quiz configuration for all Guatemalan municipalities,",
            " * grouped by department.",
            " */",
            "export const guatemalaMunicipalitiesQuiz: FeatureQuiz = {",
            '  id: "guatemala-municipalities",',
            '  name: "Guatemala Municipalities",',
            "  description: `Learn all "
            "${GUATEMALA_MUNICIPALITY_QUESTIONS.length} municipalities "
            "of Guatemala, with filters that let you practice municipalities "
            "from any desired department or combination of departments.`,",
            "",
            '  kind: "feature",',
            '  mapId: "guatemala-municipalities",',
            "",
            '  answerProperty: "municipality_id",',
            '  answerType: "single",',
            "",
            "  grouping: {",
            "    properties: [",
            "      {",
            '        property: "department_id",',
            '        label: "Department",',
            '        valueType: "string",',
            "        valueLabels: GUATEMALA_DEPARTMENT_NAMES_BY_ID,",
            "      },",
            "    ],",
            "  },",
            "",
            "  questions: GUATEMALA_MUNICIPALITY_QUESTIONS,",
            "};",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Generate and write the Guatemala municipality quiz."""

    data = load_geojson()
    municipalities = read_municipalities(data)

    name_counts = Counter(
        municipality["name"]
        for municipality in municipalities
    )

    duplicate_names = sorted(
        name
        for name, count in name_counts.items()
        if count > 1
    )

    typescript = create_typescript(municipalities)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        typescript,
        encoding="utf-8",
    )

    print("Guatemala municipality quiz generated successfully.")
    print()
    print(f"Questions: {len(municipalities):,}")
    print(f"Departments: {len(DEPARTMENT_NAMES_BY_ID):,}")
    print(f"Duplicate names disambiguated: {len(duplicate_names):,}")

    if duplicate_names:
        print()
        print("Duplicate names:")

        for name in duplicate_names:
            print(f"  {name}")

    print()
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


if __name__ == "__main__":
    main()