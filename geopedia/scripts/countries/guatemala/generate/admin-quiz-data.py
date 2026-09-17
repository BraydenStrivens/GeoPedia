"""
Generates the administrative quiz data used by GeoPedia's Guatemala
department and municipality quizzes.

Source:
    public/data/countries/guatemala/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/countries/central-america/guatemala/data/admin.ts

Department names are maintained by this generator and keyed by their
two-digit administrative IDs.

Municipalities are generated from the processed runtime GeoJSON, keyed by
their four-digit administrative IDs, and reference their parent department.

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
    / "countries"
    / "central-america"
    / "guatemala"
    / "data"
    / "admin.ts"
)


EXPECTED_MUNICIPALITY_COUNT = 342

DEPARTMENTS_BY_ID = {
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


def load_features() -> list[dict[str, Any]]:
    """Load and validate the processed municipality FeatureCollection."""
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"Municipality GeoJSON does not exist:\n  {SOURCE_PATH}"
        )

    with SOURCE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected a GeoJSON FeatureCollection: {SOURCE_PATH}"
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

    return features


def read_municipalities(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract and validate Guatemala's municipality records."""
    municipalities: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for index, feature in enumerate(
        features,
        start=1,
    ):
        feature_id = feature.get("id")
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {index} does not contain valid properties."
            )

        municipality_id = properties.get(
            "municipality_id"
        )
        name = properties.get(
            "name"
        )
        department_id = properties.get(
            "department_id"
        )

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

        seen_ids.add(
            municipality_id
        )

        if (
            not isinstance(name, str)
            or not name.strip()
        ):
            raise ValueError(
                f"Municipality {municipality_id} has "
                f"invalid name {name!r}."
            )

        name = name.strip()

        if (
            not isinstance(department_id, str)
            or department_id not in DEPARTMENTS_BY_ID
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

    return sorted(
        municipalities,
        key=lambda municipality: municipality["id"],
    )


def build_municipalities(
    records: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """
    Build the generated municipality hierarchy.

    Duplicate municipality names are disambiguated with their department.
    """
    name_counts = Counter(
        record["name"]
        for record in records
    )

    municipalities: dict[str, dict[str, str]] = {}

    for record in records:
        name = record["name"]

        if name_counts[name] > 1:
            name = (
                f"{name} "
                f"({DEPARTMENTS_BY_ID[record['department_id']]})"
            )

        municipalities[
            record["id"]
        ] = {
            "name": name,
            "departmentId": record["department_id"],
        }

    generated_names = [
        municipality["name"]
        for municipality in municipalities.values()
    ]

    duplicate_names = sorted(
        name
        for name, count in Counter(
            generated_names
        ).items()
        if count > 1
    )

    if duplicate_names:
        raise ValueError(
            "Department-based municipality disambiguation did not "
            "produce unique names:\n"
            + "\n".join(
                f"  {name}"
                for name in duplicate_names
            )
        )

    return municipalities


def ts_string(
    value: str,
) -> str:
    """Return a safely encoded TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_departments() -> str:
    """Render Guatemala's department dictionary."""
    lines = [
        "export const GUATEMALA_DEPARTMENTS_BY_ID = {",
    ]

    for department_id, name in DEPARTMENTS_BY_ID.items():
        lines.append(
            f"  {ts_string(department_id)}: {ts_string(name)},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_municipalities(
    municipalities: dict[str, dict[str, str]],
) -> str:
    """Render Guatemala's municipality hierarchy."""
    lines = [
        "export const GUATEMALA_MUNICIPALITIES_BY_ID = {",
    ]

    for municipality_id, municipality in municipalities.items():
        lines.append(
            f"  {ts_string(municipality_id)}: "
            "{ "
            f"name: {ts_string(municipality['name'])}, "
            f"departmentId: {ts_string(municipality['departmentId'])} "
            "},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def create_source(
    municipalities: dict[str, dict[str, str]],
) -> str:
    """Create the generated TypeScript admin-data module."""
    return f'''/**
 * Generated administrative data for Guatemala.
 *
 * Municipality data is generated from GeoPedia's processed administrative
 * GeoJSON. Department names are maintained by this generator.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/guatemala/generate/admin-quiz-data.py
 */

{render_departments()}{render_municipalities(municipalities)}'''


def main() -> None:
    """Generate Guatemala's administrative quiz data."""
    print(
        "Generating Guatemala administrative quiz data...\n"
    )

    features = load_features()

    municipality_records = read_municipalities(
        features
    )

    municipalities = build_municipalities(
        municipality_records
    )

    duplicate_source_names = {
        name
        for name, count in Counter(
            record["name"]
            for record in municipality_records
        ).items()
        if count > 1
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            municipalities
        ),
        encoding="utf-8",
    )

    print(
        f"Departments:              {len(DEPARTMENTS_BY_ID):,}"
    )
    print(
        f"Municipalities:           {len(municipalities):,}"
    )
    print(
        "Disambiguated name groups: "
        f"{len(duplicate_source_names):,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()