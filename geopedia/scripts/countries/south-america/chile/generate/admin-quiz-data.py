"""
Generate Chile administrative quiz data from GeoPedia's canonical
intermediate GeoJSON.

Input
-----
data/intermediate/countries/chile/admin/

    regions.geojson
    provinces.geojson
    communes.geojson

Output
------
src/quiz/quizzes/countries/chile/data/admin.ts

The generated TypeScript contains the question labels and parent IDs needed
by Chile's administrative quiz configs. Geometry remains in the GeoJSON and
is not duplicated here.

Regenerate with:

    python scripts/countries/chile/generate/admin-quiz-data.py
"""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INTERMEDIATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "admin"
)

REGIONS_INPUT = INTERMEDIATE_DIR / "regions.geojson"
PROVINCES_INPUT = INTERMEDIATE_DIR / "provinces.geojson"
COMMUNES_INPUT = INTERMEDIATE_DIR / "communes.geojson"

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "chile"
    / "data"
    / "admin.ts"
)


EXPECTED_REGIONS = 16
EXPECTED_PROVINCES = 56
EXPECTED_COMMUNES = 345


# ---------------------------------------------------------------------------
# Region quiz labels
# ---------------------------------------------------------------------------

# The canonical GeoJSON retains Chile's full region names, such as
# "Región de Tarapacá". Quiz questions use shorter labels because every
# answer is already known to be a region.
#
# Using IDs here also avoids trying to infer abbreviations from variations
# such as "Región de", "Región del", and "Región Metropolitana de".
REGION_QUIZ_NAMES = {
    "CL01": "Tarapacá",
    "CL02": "Antofagasta",
    "CL03": "Atacama",
    "CL04": "Coquimbo",
    "CL05": "Valparaíso",
    "CL06": "Libertador Bernardo O'Higgins",
    "CL07": "Maule",
    "CL08": "Bío-Bío",
    "CL09": "La Araucanía",
    "CL10": "Los Lagos",
    "CL11": "Aysén del Gral. Ibáñez del Campo",
    "CL12": "Magallanes y Antártica Chilena",
    "CL13": "Metropolitana de Santiago",
    "CL14": "Los Ríos",
    "CL15": "Arica y Parinacota",
    "CL16": "Ñuble",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_features(path: Path) -> list[dict]:
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
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            "GeoJSON feature is missing properties."
        )

    return properties


def ts_string(value: str) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def validate_unique_ids(
    records: list[dict],
    label: str,
) -> None:
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

        region_id = str(region_id)

        if region_id not in REGION_QUIZ_NAMES:
            raise ValueError(
                f"No quiz label configured for region "
                f"{region_id}: {region}"
            )

        records.append(
            {
                "id": region_id,
                "name": REGION_QUIZ_NAMES[region_id],
            }
        )

    validate_unique_ids(
        records,
        "Region",
    )

    source_ids = {
        record["id"]
        for record in records
    }

    configured_ids = set(
        REGION_QUIZ_NAMES
    )

    if source_ids != configured_ids:
        missing = sorted(
            source_ids - configured_ids
        )

        extra = sorted(
            configured_ids - source_ids
        )

        raise ValueError(
            "Region quiz-name mapping does not match "
            f"the GeoJSON. Missing: {missing}; "
            f"extra: {extra}"
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
# Provinces
# ---------------------------------------------------------------------------

def generate_province_entries(
    features: list[dict],
) -> list[str]:
    if len(features) != EXPECTED_PROVINCES:
        raise ValueError(
            f"Expected {EXPECTED_PROVINCES} provinces, "
            f"found {len(features)}."
        )

    records = []

    for feature in features:
        properties = get_properties(feature)

        province_id = properties.get(
            "province_id"
        )

        province = properties.get(
            "province"
        )

        region_id = properties.get(
            "region_id"
        )

        if (
            not province_id
            or not province
            or not region_id
        ):
            raise ValueError(
                "Province feature is missing one or more "
                "required properties."
            )

        records.append(
            {
                "id": str(province_id),
                "name": str(province),
                "regionId": str(region_id),
            }
        )

    validate_unique_ids(
        records,
        "Province",
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
# Communes
# ---------------------------------------------------------------------------

def generate_commune_entries(
    features: list[dict],
) -> list[str]:
    if len(features) != EXPECTED_COMMUNES:
        raise ValueError(
            f"Expected {EXPECTED_COMMUNES} communes, "
            f"found {len(features)}."
        )

    records = []

    for feature in features:
        properties = get_properties(feature)

        commune_id = properties.get(
            "commune_id"
        )

        commune = properties.get(
            "commune"
        )

        province_id = properties.get(
            "province_id"
        )

        region_id = properties.get(
            "region_id"
        )

        if (
            not commune_id
            or not commune
            or not province_id
            or not region_id
        ):
            raise ValueError(
                "Commune feature is missing one or more "
                "required properties."
            )

        records.append(
            {
                "id": str(commune_id),
                "name": str(commune),
                "provinceId": str(province_id),
                "regionId": str(region_id),
            }
        )

    validate_unique_ids(
        records,
        "Commune",
    )

    records.sort(
        key=lambda record: record["id"]
    )

    return [
        (
            f"  {ts_string(record['id'])}: {{ "
            f"name: {ts_string(record['name'])}, "
            f"provinceId: {ts_string(record['provinceId'])}, "
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
    province_entries: list[str],
    commune_entries: list[str],
) -> str:
    lines = [
        "/**",
        " * Generated from Chile's processed administrative GeoJSON.",
        " *",
        " * Do not edit manually.",
        " * Regenerate with:",
        " * python scripts/countries/chile/generate/admin-quiz-data.py",
        " */",
        "",
        "export const CHILE_REGIONS_BY_ID = {",
        *region_entries,
        "} as const;",
        "",
        "export const CHILE_PROVINCES_BY_ID = {",
        *province_entries,
        "} as const;",
        "",
        "export const CHILE_COMMUNES_BY_ID = {",
        *commune_entries,
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
    print(
        "Generating Chile admin quiz data..."
    )

    region_features = load_features(
        REGIONS_INPUT
    )

    province_features = load_features(
        PROVINCES_INPUT
    )

    commune_features = load_features(
        COMMUNES_INPUT
    )

    region_entries = generate_region_entries(
        region_features
    )

    province_entries = generate_province_entries(
        province_features
    )

    commune_entries = generate_commune_entries(
        commune_features
    )

    output = build_typescript(
        region_entries,
        province_entries,
        commune_entries,
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
        f"Provinces: {len(province_entries)}"
    )

    print(
        f"Communes: {len(commune_entries)}"
    )

    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()