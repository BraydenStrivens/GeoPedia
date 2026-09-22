"""
Generate Senegal administrative quiz data from GeoPedia's canonical
intermediate GeoJSON.

Input
-----
data/intermediate/countries/senegal/admin/

    regions.geojson
    departments.geojson
    arrondissements.geojson

Output
------
src/quiz/quizzes/countries/senegal/data/admin.ts

The generated TypeScript contains the question labels and parent IDs needed
by Senegal's administrative quiz configs. Geometry remains in the GeoJSON and
is not duplicated here.

Regenerate with:

    python scripts/countries/senegal/generate/admin-quiz-data.py
"""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INTERMEDIATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "senegal"
    / "admin"
)

REGIONS_INPUT = INTERMEDIATE_DIR / "regions.geojson"
DEPARTMENTS_INPUT = INTERMEDIATE_DIR / "departments.geojson"
ARRONDISSEMENTS_INPUT = INTERMEDIATE_DIR / "arrondissements.geojson"

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "senegal"
    / "data"
    / "admin.ts"
)


EXPECTED_REGIONS = 14
EXPECTED_DEPARTMENTS = 46
EXPECTED_ARRONDISSEMENTS = 125


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_features(path: Path) -> list[dict]:
    """Load and return the features from a GeoJSON FeatureCollection."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features", [])

    if not isinstance(features, list):
        raise ValueError(
            f"{path} has an invalid features array."
        )

    return features


def get_properties(feature: dict) -> dict:
    """Return a feature's properties or raise an error."""
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            "GeoJSON feature is missing properties."
        )

    return properties


def ts_string(value: str) -> str:
    """Encode a string as a TypeScript-compatible string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def validate_unique_ids(
    records: list[dict],
    label: str,
) -> None:
    """Verify that generated records have unique IDs."""
    ids = [
        record["id"]
        for record in records
    ]

    if len(set(ids)) != len(ids):
        raise ValueError(
            f"{label} IDs are not unique."
        )


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------


def generate_region_entries(
    features: list[dict],
) -> list[str]:
    """Generate Senegal region quiz-data entries."""
    if len(features) != EXPECTED_REGIONS:
        raise ValueError(
            f"Expected {EXPECTED_REGIONS} regions, "
            f"found {len(features)}."
        )

    records = []

    for feature in features:
        properties = get_properties(feature)

        region_id = properties.get("region_id")
        region = properties.get("region")

        if not region_id or not region:
            raise ValueError(
                "Region feature is missing "
                "region_id or region."
            )

        records.append(
            {
                "id": str(region_id),
                "name": str(region),
            }
        )

    validate_unique_ids(
        records,
        "Region",
    )

    records.sort(
        key=lambda record: record["id"]
    )

    return [
        (
            f"  {ts_string(record['id'])}: "
            f"{ts_string(record['name'])},"
        )
        for record in records
    ]


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------


def generate_department_entries(
    features: list[dict],
) -> list[str]:
    """Generate Senegal department quiz-data entries."""
    if len(features) != EXPECTED_DEPARTMENTS:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENTS} departments, "
            f"found {len(features)}."
        )

    records = []

    for feature in features:
        properties = get_properties(feature)

        department_id = properties.get(
            "department_id"
        )

        department = properties.get(
            "department"
        )

        region_id = properties.get(
            "region_id"
        )

        if (
            not department_id
            or not department
            or not region_id
        ):
            raise ValueError(
                "Department feature is missing one or more "
                "required properties."
            )

        records.append(
            {
                "id": str(department_id),
                "name": str(department),
                "regionId": str(region_id),
            }
        )

    validate_unique_ids(
        records,
        "Department",
    )

    records.sort(
        key=lambda record: record["id"]
    )

    return [
        (
            f"  {ts_string(record['id'])}: {{ "
            f"name: {ts_string(record['name'])}, "
            f"regionId: {ts_string(record['regionId'])} "
            f"}},"
        )
        for record in records
    ]


# ---------------------------------------------------------------------------
# Arrondissements
# ---------------------------------------------------------------------------


def generate_arrondissement_entries(
    features: list[dict],
) -> list[str]:
    """Generate Senegal arrondissement quiz-data entries."""
    if len(features) != EXPECTED_ARRONDISSEMENTS:
        raise ValueError(
            f"Expected {EXPECTED_ARRONDISSEMENTS} arrondissements, "
            f"found {len(features)}."
        )

    records = []

    for feature in features:
        properties = get_properties(feature)

        arrondissement_id = properties.get(
            "arrondissement_id"
        )

        arrondissement = properties.get(
            "arrondissement"
        )

        department_id = properties.get(
            "department_id"
        )

        region_id = properties.get(
            "region_id"
        )

        if (
            not arrondissement_id
            or not arrondissement
            or not department_id
            or not region_id
        ):
            raise ValueError(
                "Arrondissement feature is missing one or more "
                "required properties."
            )

        records.append(
            {
                "id": str(arrondissement_id),
                "name": str(arrondissement),
                "departmentId": str(department_id),
                "regionId": str(region_id),
            }
        )

    validate_unique_ids(
        records,
        "Arrondissement",
    )

    records.sort(
        key=lambda record: record["id"]
    )

    return [
        (
            f"  {ts_string(record['id'])}: {{ "
            f"name: {ts_string(record['name'])}, "
            f"departmentId: {ts_string(record['departmentId'])}, "
            f"regionId: {ts_string(record['regionId'])} "
            f"}},"
        )
        for record in records
    ]


# ---------------------------------------------------------------------------
# TypeScript output
# ---------------------------------------------------------------------------


def build_typescript(
    region_entries: list[str],
    department_entries: list[str],
    arrondissement_entries: list[str],
) -> str:
    """Build the generated Senegal administrative TypeScript module."""
    lines = [
        "/**",
        " * Generated from Senegal's processed administrative GeoJSON.",
        " *",
        " * Do not edit manually.",
        " * Regenerate with:",
        " * python scripts/countries/senegal/generate/admin-quiz-data.py",
        " */",
        "",
        "export const SENEGAL_REGIONS_BY_ID = {",
        *region_entries,
        "} as const;",
        "",
        "export const SENEGAL_DEPARTMENTS_BY_ID = {",
        *department_entries,
        "} as const;",
        "",
        "export const SENEGAL_ARRONDISSEMENTS_BY_ID = {",
        *arrondissement_entries,
        "} as const;",
        "",
    ]

    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate all Senegal administrative quiz data."""
    print(
        "Generating Senegal admin quiz data..."
    )

    region_features = load_features(
        REGIONS_INPUT
    )

    department_features = load_features(
        DEPARTMENTS_INPUT
    )

    arrondissement_features = load_features(
        ARRONDISSEMENTS_INPUT
    )

    region_entries = generate_region_entries(
        region_features
    )

    department_entries = generate_department_entries(
        department_features
    )

    arrondissement_entries = generate_arrondissement_entries(
        arrondissement_features
    )

    output = build_typescript(
        region_entries,
        department_entries,
        arrondissement_entries,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print(
        f"Regions: {len(region_entries)}"
    )

    print(
        f"Departments: {len(department_entries)}"
    )

    print(
        f"Arrondissements: {len(arrondissement_entries)}"
    )

    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()