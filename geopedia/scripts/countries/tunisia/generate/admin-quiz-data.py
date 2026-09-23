"""
Generate Tunisia administrative quiz data from processed GeoJSON.

Input
-----
data/intermediate/countries/tunisia/admin/

    governorates.geojson
    delegations.geojson
    municipalities.geojson

Output
------
src/quiz/quizzes/countries/tunisia/data/admin.ts

The generated TypeScript contains canonical administrative metadata used by
Tunisia's feature quizzes. Geometry is intentionally excluded because runtime
map geometry is loaded separately from public GeoJSON files.

Quiz display labels are generated in both the source Latin-script name and
Arabic native name. Duplicate names within an administrative level are
disambiguated using parent administrative names. The nearest parent is used
first, with higher parent levels added only when necessary.

Generated file. Do not edit manually.
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "tunisia"
    / "admin"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "tunisia"
    / "data"
    / "admin.ts"
)


EXPECTED_COUNTS = {
    "governorates": 24,
    "delegations": 264,
    "municipalities": 2084,
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_features(
    filename: str,
    expected_count: int,
) -> list[dict[str, Any]]:
    """Load and validate one processed administrative FeatureCollection."""
    path = INPUT_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} has an invalid features array."
        )

    if len(features) != expected_count:
        raise ValueError(
            f"{filename}: expected {expected_count} features, "
            f"found {len(features)}."
        )

    return features


def get_properties(
    feature: dict[str, Any],
) -> dict[str, Any]:
    """Return a feature's properties."""
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            "Feature is missing properties."
        )

    return properties


def require_string(
    properties: dict[str, Any],
    property_name: str,
) -> str:
    """Return a required non-empty string property."""
    value = properties.get(property_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Missing or invalid property: {property_name}"
        )

    return value.strip()


# ---------------------------------------------------------------------------
# Display disambiguation
# ---------------------------------------------------------------------------


def find_duplicate_values(
    records: list[dict[str, str]],
    property_name: str,
) -> set[str]:
    """Return values that occur more than once for a property."""
    counts = Counter(
        record[property_name]
        for record in records
    )

    return {
        value
        for value, count in counts.items()
        if count > 1
    }


def labels_are_unique(
    labels: list[str],
) -> bool:
    """Return whether every generated label is unique."""
    return len(labels) == len(set(labels))


def create_disambiguated_labels(
    records: list[dict[str, str]],
    name_property: str,
    parent_properties: list[str],
) -> dict[str, str]:
    """
    Create unique display labels for one language.

    Names that are already unique are returned unchanged.

    For duplicate names, parent administrative names are appended beginning
    with the nearest parent. Additional higher-level parents are added only
    when the previous label is still ambiguous.

    The returned dictionary is keyed by each record's canonical `id`.
    """
    duplicate_names = find_duplicate_values(
        records,
        name_property,
    )

    labels = {
        record["id"]: record[name_property]
        for record in records
    }

    if not duplicate_names:
        return labels

    duplicate_records = [
        record
        for record in records
        if record[name_property] in duplicate_names
    ]

    unresolved_ids = {
        record["id"]
        for record in duplicate_records
    }

    parent_parts: dict[str, list[str]] = {
        record["id"]: []
        for record in duplicate_records
    }

    for parent_property in parent_properties:
        for record in duplicate_records:
            record_id = record["id"]

            if record_id not in unresolved_ids:
                continue

            parent_value = record[parent_property]

            parent_parts[record_id].append(
                parent_value
            )

            labels[record_id] = (
                f"{record[name_property]} "
                f"({', '.join(parent_parts[record_id])})"
            )

        label_counts = Counter(
            labels[record["id"]]
            for record in duplicate_records
            if record["id"] in unresolved_ids
        )

        newly_resolved = {
            record["id"]
            for record in duplicate_records
            if (
                record["id"] in unresolved_ids
                and label_counts[labels[record["id"]]] == 1
            )
        }

        unresolved_ids -= newly_resolved

        if not unresolved_ids:
            break

    if unresolved_ids:
        unresolved_labels = [
            labels[record_id]
            for record_id in sorted(unresolved_ids)
        ]

        raise ValueError(
            "Could not uniquely disambiguate labels using "
            f"available parent levels: {unresolved_labels}"
        )

    all_labels = [
        labels[record["id"]]
        for record in records
    ]

    if not labels_are_unique(all_labels):
        raise ValueError(
            f"Generated {name_property} labels are not unique."
        )

    return labels


# ---------------------------------------------------------------------------
# Canonical records
# ---------------------------------------------------------------------------


def create_governorate_records(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Create generator records for Tunisia's wilayat."""
    records = []

    for feature in features:
        properties = get_properties(feature)

        records.append(
            {
                "id": require_string(
                    properties,
                    "governorate_id",
                ),
                "name": require_string(
                    properties,
                    "governorate",
                ),
                "native_name": require_string(
                    properties,
                    "native_governorate",
                ),
                "region_id": require_string(
                    properties,
                    "region_id",
                ),
                "region": require_string(
                    properties,
                    "region",
                ),
                "native_region": require_string(
                    properties,
                    "native_region",
                ),
            }
        )

    return records


def create_delegation_records(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Create generator records for Tunisia's mutamadiyat."""
    records = []

    for feature in features:
        properties = get_properties(feature)

        records.append(
            {
                "id": require_string(
                    properties,
                    "delegation_id",
                ),
                "name": require_string(
                    properties,
                    "delegation",
                ),
                "native_name": require_string(
                    properties,
                    "native_delegation",
                ),
                "governorate_id": require_string(
                    properties,
                    "governorate_id",
                ),
                "governorate": require_string(
                    properties,
                    "governorate",
                ),
                "native_governorate": require_string(
                    properties,
                    "native_governorate",
                ),
                "region_id": require_string(
                    properties,
                    "region_id",
                ),
                "region": require_string(
                    properties,
                    "region",
                ),
                "native_region": require_string(
                    properties,
                    "native_region",
                ),
            }
        )

    return records


def create_municipality_records(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Create generator records for Tunisia's baladiyat."""
    records = []

    for feature in features:
        properties = get_properties(feature)

        records.append(
            {
                "id": require_string(
                    properties,
                    "municipality_id",
                ),
                "name": require_string(
                    properties,
                    "municipality",
                ),
                "native_name": require_string(
                    properties,
                    "native_municipality",
                ),
                "delegation_id": require_string(
                    properties,
                    "delegation_id",
                ),
                "delegation": require_string(
                    properties,
                    "delegation",
                ),
                "native_delegation": require_string(
                    properties,
                    "native_delegation",
                ),
                "governorate_id": require_string(
                    properties,
                    "governorate_id",
                ),
                "governorate": require_string(
                    properties,
                    "governorate",
                ),
                "native_governorate": require_string(
                    properties,
                    "native_governorate",
                ),
                "region_id": require_string(
                    properties,
                    "region_id",
                ),
                "region": require_string(
                    properties,
                    "region",
                ),
                "native_region": require_string(
                    properties,
                    "native_region",
                ),
            }
        )

    return records


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def ts_string(value: str) -> str:
    """Serialize a Python string as a TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def generate_governorates(
    records: list[dict[str, str]],
) -> str:
    """Generate the governorate metadata constant."""
    displays = create_disambiguated_labels(
        records,
        "name",
        ["region"],
    )

    native_displays = create_disambiguated_labels(
        records,
        "native_name",
        ["native_region"],
    )

    lines = [
        "export const TUNISIA_GOVERNORATES_BY_ID = {"
    ]

    for record in records:
        record_id = record["id"]

        lines.extend(
            [
                f"  {ts_string(record_id)}: {{",
                f"    name: {ts_string(record['name'])},",
                (
                    "    nativeName: "
                    f"{ts_string(record['native_name'])},"
                ),
                f"    display: {ts_string(displays[record_id])},",
                (
                    "    nativeDisplay: "
                    f"{ts_string(native_displays[record_id])},"
                ),
                (
                    "    regionId: "
                    f"{ts_string(record['region_id'])},"
                ),
                f"    region: {ts_string(record['region'])},",
                (
                    "    nativeRegion: "
                    f"{ts_string(record['native_region'])},"
                ),
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def generate_delegations(
    records: list[dict[str, str]],
) -> str:
    """Generate the delegation metadata constant."""
    displays = create_disambiguated_labels(
        records,
        "name",
        [
            "governorate",
            "region",
        ],
    )

    native_displays = create_disambiguated_labels(
        records,
        "native_name",
        [
            "native_governorate",
            "native_region",
        ],
    )

    lines = [
        "export const TUNISIA_DELEGATIONS_BY_ID = {"
    ]

    for record in records:
        record_id = record["id"]

        lines.extend(
            [
                f"  {ts_string(record_id)}: {{",
                f"    name: {ts_string(record['name'])},",
                (
                    "    nativeName: "
                    f"{ts_string(record['native_name'])},"
                ),
                f"    display: {ts_string(displays[record_id])},",
                (
                    "    nativeDisplay: "
                    f"{ts_string(native_displays[record_id])},"
                ),
                (
                    "    governorateId: "
                    f"{ts_string(record['governorate_id'])},"
                ),
                (
                    "    governorate: "
                    f"{ts_string(record['governorate'])},"
                ),
                (
                    "    nativeGovernorate: "
                    f"{ts_string(record['native_governorate'])},"
                ),
                (
                    "    regionId: "
                    f"{ts_string(record['region_id'])},"
                ),
                f"    region: {ts_string(record['region'])},",
                (
                    "    nativeRegion: "
                    f"{ts_string(record['native_region'])},"
                ),
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def generate_municipalities(
    records: list[dict[str, str]],
) -> str:
    """Generate the municipality metadata constant."""
    displays = create_disambiguated_labels(
        records,
        "name",
        [
            "delegation",
            "governorate",
            "region",
        ],
    )

    native_displays = create_disambiguated_labels(
        records,
        "native_name",
        [
            "native_delegation",
            "native_governorate",
            "native_region",
        ],
    )

    lines = [
        "export const TUNISIA_MUNICIPALITIES_BY_ID = {"
    ]

    for record in records:
        record_id = record["id"]

        lines.extend(
            [
                f"  {ts_string(record_id)}: {{",
                f"    name: {ts_string(record['name'])},",
                (
                    "    nativeName: "
                    f"{ts_string(record['native_name'])},"
                ),
                f"    display: {ts_string(displays[record_id])},",
                (
                    "    nativeDisplay: "
                    f"{ts_string(native_displays[record_id])},"
                ),
                (
                    "    delegationId: "
                    f"{ts_string(record['delegation_id'])},"
                ),
                (
                    "    delegation: "
                    f"{ts_string(record['delegation'])},"
                ),
                (
                    "    nativeDelegation: "
                    f"{ts_string(record['native_delegation'])},"
                ),
                (
                    "    governorateId: "
                    f"{ts_string(record['governorate_id'])},"
                ),
                (
                    "    governorate: "
                    f"{ts_string(record['governorate'])},"
                ),
                (
                    "    nativeGovernorate: "
                    f"{ts_string(record['native_governorate'])},"
                ),
                (
                    "    regionId: "
                    f"{ts_string(record['region_id'])},"
                ),
                f"    region: {ts_string(record['region'])},",
                (
                    "    nativeRegion: "
                    f"{ts_string(record['native_region'])},"
                ),
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def generate_typescript(
    governorates: list[dict[str, str]],
    delegations: list[dict[str, str]],
    municipalities: list[dict[str, str]],
) -> str:
    """Generate the complete Tunisia administrative TypeScript module."""
    sections = [
        (
            "/**\n"
            " * Generated Tunisia administrative quiz metadata.\n"
            " *\n"
            " * Includes English/source and Arabic native names, parent\n"
            " * hierarchy metadata, and unique quiz display labels.\n"
            " *\n"
            " * Generated by:\n"
            " * scripts/countries/tunisia/generate/admin-quiz-data.py\n"
            " *\n"
            " * Do not edit manually.\n"
            " */"
        ),
        generate_governorates(
            governorates
        ),
        generate_delegations(
            delegations
        ),
        generate_municipalities(
            municipalities
        ),
    ]

    return "\n\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate Tunisia's administrative quiz metadata."""
    print(
        "Generating Tunisia administrative quiz data..."
    )

    governorate_features = load_features(
        "governorates.geojson",
        EXPECTED_COUNTS["governorates"],
    )

    delegation_features = load_features(
        "delegations.geojson",
        EXPECTED_COUNTS["delegations"],
    )

    municipality_features = load_features(
        "municipalities.geojson",
        EXPECTED_COUNTS["municipalities"],
    )

    governorates = create_governorate_records(
        governorate_features
    )

    delegations = create_delegation_records(
        delegation_features
    )

    municipalities = create_municipality_records(
        municipality_features
    )

    output = generate_typescript(
        governorates,
        delegations,
        municipalities,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print()
    print(
        "Tunisia administrative quiz data generated."
    )
    print(
        f"  Governorates:   {len(governorates)}"
    )
    print(
        f"  Delegations:    {len(delegations)}"
    )
    print(
        f"  Municipalities: {len(municipalities)}"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()