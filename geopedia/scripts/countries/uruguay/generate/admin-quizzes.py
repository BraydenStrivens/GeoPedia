from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

DEPARTMENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "uruguay"
    / "admin"
    / "departments.geojson"
)

MUNICIPALITIES_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "uruguay"
    / "admin"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "data"
    / "countries"
    / "uruguay"
    / "admin.ts"
)


EXPECTED_DEPARTMENT_COUNT = 19
EXPECTED_MUNICIPALITY_COUNT = 136


LOWERCASE_WORDS = {
    "de",
    "del",
    "la",
    "las",
    "los",
    "y",
}


def load_features(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find GeoJSON: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"GeoJSON has no valid feature array: {path}"
        )

    return features


def normalize_name(name: str) -> str:
    words = name.lower().split()

    result: list[str] = []

    for index, word in enumerate(words):
        if index > 0 and word in LOWERCASE_WORDS:
            result.append(word)
        else:
            result.append(
                word[:1].upper() + word[1:]
            )

    return " ".join(result)


def build_departments(
    features: list[dict],
) -> dict[str, str]:
    if len(features) != EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} departments, "
            f"found {len(features)}."
        )

    departments: dict[str, str] = {}

    for feature in features:
        properties = feature.get("properties", {})

        department_id = properties.get("department_id")
        department = properties.get("department")

        if not department_id or not department:
            raise ValueError(
                "Department feature is missing "
                "department_id or department."
            )

        if department_id in departments:
            raise ValueError(
                f"Duplicate department ID: {department_id}"
            )

        departments[department_id] = department

    return dict(
        sorted(
            departments.items(),
        )
    )


def build_municipalities(
    features: list[dict],
) -> dict[str, dict[str, str]]:
    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(features)}."
        )

    raw_entries: list[dict[str, str]] = []

    for feature in features:
        properties = feature.get("properties", {})

        municipality_id = properties.get(
            "municipality_id"
        )
        municipality = properties.get(
            "municipality"
        )
        department_id = properties.get(
            "department_id"
        )
        department = properties.get(
            "department"
        )

        if not all(
            [
                municipality_id,
                municipality,
                department_id,
                department,
            ]
        ):
            raise ValueError(
                "Municipality feature is missing required properties."
            )

        raw_entries.append(
            {
                "municipality_id": municipality_id,
                "municipality": normalize_name(
                    municipality
                ),
                "department_id": department_id,
                "department": department,
            }
        )

    name_counts: dict[str, int] = {}

    for entry in raw_entries:
        name = entry["municipality"]

        name_counts[name] = (
            name_counts.get(name, 0) + 1
        )

    municipalities: dict[
        str,
        dict[str, str],
    ] = {}

    for entry in raw_entries:
        municipality_id = entry["municipality_id"]
        municipality = entry["municipality"]
        department_id = entry["department_id"]
        department = entry["department"]

        if municipality_id in municipalities:
            raise ValueError(
                f"Duplicate municipality ID: "
                f"{municipality_id}"
            )

        display = municipality

        if name_counts[municipality] > 1:
            display = (
                f"{municipality} ({department})"
            )

        municipalities[municipality_id] = {
            "name": municipality,
            "display": display,
            "departmentId": department_id,
        }

    return dict(
        sorted(
            municipalities.items(),
        )
    )


def ts_string(value: str) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_departments(
    departments: dict[str, str],
) -> str:
    lines = [
        "export const URUGUAY_DEPARTMENTS_BY_ID = {",
    ]

    for department_id, name in departments.items():
        lines.append(
            f"  {ts_string(department_id)}: "
            f"{ts_string(name)},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_municipalities(
    municipalities: dict[
        str,
        dict[str, str],
    ],
) -> str:
    lines = [
        "export const URUGUAY_MUNICIPALITIES_BY_ID = {",
    ]

    for municipality_id, data in municipalities.items():
        lines.extend(
            [
                f"  {ts_string(municipality_id)}: {{",
                f"    name: {ts_string(data['name'])},",
                f"    display: {ts_string(data['display'])},",
                (
                    "    departmentId: "
                    f"{ts_string(data['departmentId'])},"
                ),
                "  },",
            ]
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    print("Generating Uruguay admin TypeScript data...")
    print()

    department_features = load_features(
        DEPARTMENTS_PATH
    )

    municipality_features = load_features(
        MUNICIPALITIES_PATH
    )

    departments = build_departments(
        department_features
    )

    municipalities = build_municipalities(
        municipality_features
    )

    output = (
        render_departments(departments)
        + "\n"
        + render_municipalities(municipalities)
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    duplicate_displays = [
        data["display"]
        for data in municipalities.values()
        if data["display"] != data["name"]
    ]

    print(
        f"Departments: {len(departments)}"
    )

    print(
        f"Municipalities: {len(municipalities)}"
    )

    print()
    print("Disambiguated municipality names:")

    for display in duplicate_displays:
        print(f"  {display}")

    print()
    print(
        f"Generated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()