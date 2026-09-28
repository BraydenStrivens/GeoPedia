"""
Generates the administrative data used by Colombia's quiz configurations.

Sources:
    public/data/countries/colombia/geojson/departments.geojson
    public/data/countries/colombia/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/countries/south-america/colombia/data/admin.ts

The processed administrative GeoJSON is the canonical source for department
and municipality IDs, names, and hierarchy.
"""

from __future__ import annotations

import json
from pathlib import Path


DEPARTMENTS_SOURCE_PATH = Path(
    "public/data/countries/colombia/geojson/departments.geojson"
)

MUNICIPALITIES_SOURCE_PATH = Path(
    "public/data/countries/colombia/geojson/municipalities.geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/south-america/colombia/data/admin.ts"
)

EXPECTED_DEPARTMENT_COUNT = 33
EXPECTED_MUNICIPALITY_COUNT = 1_122


def quote(value: str) -> str:
    """Serialize a string as a valid TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def load_feature_collection(
    path: Path,
    label: str,
) -> list[dict]:
    """Load and validate one processed GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"{label} GeoJSON was not found: {path}"
        )

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{label} GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{label} GeoJSON is missing its features array."
        )

    return features


def require_string(
    properties: dict,
    property_name: str,
    label: str,
) -> str:
    """Read and validate one required string property."""
    value = properties.get(property_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{label} is missing a valid {property_name}."
        )

    return value.strip()


def build_departments(
    features: list[dict],
) -> list[tuple[str, str]]:
    """Extract Colombia's department IDs and names."""
    if len(features) != EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} departments, "
            f"found {len(features)}."
        )

    entries: list[tuple[str, str]] = []
    seen_ids: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Department feature {index} has invalid properties."
            )

        # Colombia's administrative runtime data uses department_id for the
        # stable parent ID. The department map's name property may be named
        # either department or name depending on the processing source.
        department_id = require_string(
            properties,
            "id",
            f"Department feature {index}",
        )

        department_name = require_string(
            properties,
            "name",
            f"Department {department_id}",
        )

        department_name = department_name.strip()

        if department_id in seen_ids:
            raise ValueError(
                f"Duplicate department ID: {department_id}"
            )

        seen_ids.add(department_id)

        entries.append(
            (
                department_id,
                department_name,
            )
        )

    entries.sort(key=lambda entry: entry[0])

    return entries


def build_municipalities(
    features: list[dict],
) -> list[tuple[str, str, str]]:
    """Extract municipality IDs, names, and parent department IDs."""
    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(features)}."
        )

    entries: list[tuple[str, str, str]] = []
    seen_ids: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Municipality feature {index} has invalid properties."
            )

        municipality_id = require_string(
            properties,
            "id",
            f"Municipality feature {index}",
        )

        name = require_string(
            properties,
            "name",
            f"Municipality {municipality_id}",
        )

        department_id = require_string(
            properties,
            "department_id",
            f"Municipality {municipality_id}",
        )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id}"
            )

        seen_ids.add(municipality_id)

        feature_id = feature.get("id")

        if (
            feature_id is not None
            and str(feature_id) != municipality_id
        ):
            raise ValueError(
                f"Municipality {municipality_id} has GeoJSON feature "
                f"ID {feature_id}, which does not match its ID."
            )

        entries.append(
            (
                municipality_id,
                name,
                department_id,
            )
        )

    entries.sort(key=lambda entry: entry[0])

    return entries


def validate_hierarchy(
    departments: list[tuple[str, str]],
    municipalities: list[tuple[str, str, str]],
) -> None:
    """Validate every municipality's parent department."""
    department_ids = {
        department_id
        for department_id, _ in departments
    }

    for municipality_id, _, department_id in municipalities:
        if department_id not in department_ids:
            raise ValueError(
                f"Municipality {municipality_id} references unknown "
                f"department {department_id}."
            )


def format_departments(
    departments: list[tuple[str, str]],
) -> str:
    """Format Colombia's department dictionary."""
    lines = "\n".join(
        f"  {quote(department_id)}: {quote(name)},"
        for department_id, name in departments
    )

    return f"""export const COLOMBIA_DEPARTMENTS_BY_ID = {{
{lines}
}} as const;"""


def format_municipalities(
    municipalities: list[tuple[str, str, str]],
) -> str:
    """Format Colombia's municipality dictionary."""
    lines = "\n".join(
        (
            f"  {quote(municipality_id)}: {{ "
            f"name: {quote(name)}, "
            f"departmentId: {quote(department_id)} "
            f"}},"
        )
        for municipality_id, name, department_id in municipalities
    )

    return f"""export const COLOMBIA_MUNICIPALITIES_BY_ID = {{
{lines}
}} as const;"""


def create_source(
    departments: list[tuple[str, str]],
    municipalities: list[tuple[str, str, str]],
) -> str:
    """Create the generated Colombia administrative data module."""
    return f'''/**
 * Generated from Colombia's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/colombia/generate/admin-quiz-data.py
 */

{format_departments(departments)}

{format_municipalities(municipalities)}
'''


def main() -> None:
    """Generate Colombia's administrative quiz data."""
    print("Generating Colombia administrative quiz data...\n")

    department_features = load_feature_collection(
        DEPARTMENTS_SOURCE_PATH,
        "Department",
    )

    municipality_features = load_feature_collection(
        MUNICIPALITIES_SOURCE_PATH,
        "Municipality",
    )

    departments = build_departments(
        department_features,
    )

    municipalities = build_municipalities(
        municipality_features,
    )

    validate_hierarchy(
        departments,
        municipalities,
    )

    source = create_source(
        departments,
        municipalities,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print(f"Departments:    {len(departments):,}")
    print(f"Municipalities: {len(municipalities):,}")
    print(f"\nGenerated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()