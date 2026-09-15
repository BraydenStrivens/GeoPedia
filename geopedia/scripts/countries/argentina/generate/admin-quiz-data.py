from collections import Counter
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "countries"
    / "argentina"
)

PROVINCES_INPUT = (
    PROCESSED_DIR / "provinces.geojson"
)

DEPARTMENTS_INPUT = (
    PROCESSED_DIR / "departments.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "argentina"
    / "data"
    / "admin.ts"
)


EXPECTED_PROVINCES = 24
EXPECTED_DEPARTMENTS = 526


def load_features(
    path: Path,
) -> list[dict]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features",
        [],
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path} has an invalid features array."
        )

    return features


def ts_string(
    value: str,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def get_properties(
    feature: dict,
) -> dict:
    properties = feature.get(
        "properties"
    )

    if not isinstance(
        properties,
        dict,
    ):
        raise ValueError(
            "GeoJSON feature is missing properties."
        )

    return properties


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
        properties = get_properties(
            feature
        )

        province_id = properties.get(
            "province_id"
        )

        province = properties.get(
            "province"
        )

        if not province_id or not province:
            raise ValueError(
                "Province feature is missing "
                "province_id or province."
            )

        records.append(
            {
                "id": str(
                    province_id
                ),
                "name": str(
                    province
                ),
            }
        )

    ids = [
        record["id"]
        for record in records
    ]

    if len(set(ids)) != len(ids):
        raise ValueError(
            "Province IDs are not unique."
        )

    records.sort(
        key=lambda record: record["id"]
    )

    entries = []

    for record in records:
        entries.append(
            (
                f"  {ts_string(record['id'])}: {{ "
                f"name: {ts_string(record['name'])}, "
                f"display: {ts_string(record['name'])} "
                f"}},"
            )
        )

    return entries


def generate_department_entries(
    features: list[dict],
) -> list[str]:
    if len(features) != EXPECTED_DEPARTMENTS:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENTS} departments, "
            f"found {len(features)}."
        )

    records = []

    for feature in features:
        properties = get_properties(
            feature
        )

        department_id = properties.get(
            "department_id"
        )

        department = properties.get(
            "department"
        )

        province_id = properties.get(
            "province_id"
        )

        province = properties.get(
            "province"
        )

        if (
            not department_id
            or not department
            or not province_id
            or not province
        ):
            raise ValueError(
                "Department feature is missing one or more "
                "required properties."
            )

        records.append(
            {
                "id": str(
                    department_id
                ),
                "name": str(
                    department
                ),
                "provinceId": str(
                    province_id
                ),
                "province": str(
                    province
                ),
            }
        )

    ids = [
        record["id"]
        for record in records
    ]

    if len(set(ids)) != len(ids):
        raise ValueError(
            "Department IDs are not unique."
        )

    name_counts = Counter(
        record["name"]
        for record in records
    )

    records.sort(
        key=lambda record: record["id"]
    )

    entries = []

    for record in records:
        name = record["name"]

        if name_counts[name] > 1:
            display = (
                f"{name} "
                f"({record['province']})"
            )
        else:
            display = name

        entries.append(
            (
                f"  {ts_string(record['id'])}: {{ "
                f"name: {ts_string(name)}, "
                f"display: {ts_string(display)}, "
                f"provinceId: {ts_string(record['provinceId'])} "
                f"}},"
            )
        )

    return entries


def build_typescript(
    province_entries: list[str],
    department_entries: list[str],
) -> str:
    lines = [
        "/**",
        " * Generated Argentina administrative quiz data.",
        " *",
        " * Do not edit manually.",
        " * Generated by:",
        " * scripts/countries/argentina/generate/admin-quiz-data.py",
        " */",
        "",
        "export const ARGENTINA_PROVINCES_BY_ID = {",
        *province_entries,
        "} as const;",
        "",
        "export const ARGENTINA_DEPARTMENTS_BY_ID = {",
        *department_entries,
        "} as const;",
        "",
    ]

    return "\n".join(
        lines
    )


def main() -> None:
    print(
        "Generating Argentina admin quiz data..."
    )

    province_features = load_features(
        PROVINCES_INPUT
    )

    department_features = load_features(
        DEPARTMENTS_INPUT
    )

    province_entries = (
        generate_province_entries(
            province_features
        )
    )

    department_entries = (
        generate_department_entries(
            department_features
        )
    )

    output = build_typescript(
        province_entries,
        department_entries,
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
        f"Provinces: {len(province_entries)}"
    )

    print(
        f"Departments: {len(department_entries)}"
    )

    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()