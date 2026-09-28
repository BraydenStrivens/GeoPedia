"""
Generates the administrative quiz data used by GeoPedia's Costa Rica
administrative and postal-code quizzes.

Sources:
    public/data/countries/costa-rica/geojson/cantons.geojson
    public/data/countries/costa-rica/geojson/districts.geojson

Output:
    src/quiz/quizzes/countries/central-america/costa-rica/data/admin.ts

Cantons are keyed by their 3-digit administrative IDs and reference their
parent province.

Districts are keyed by their 5-digit administrative IDs and reference their
parent canton and province. Duplicate district names are disambiguated by
their canton name.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

CANTONS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "costa-rica"
    / "geojson"
    / "cantons.geojson"
)

DISTRICTS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "costa-rica"
    / "geojson"
    / "districts.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "central-america"
    / "costa-rica"
    / "data"
    / "admin.ts"
)


EXPECTED_CANTON_COUNT = 84
EXPECTED_DISTRICT_COUNT = 492

PROVINCES_BY_ID = {
    "1": "San José",
    "2": "Alajuela",
    "3": "Cartago",
    "4": "Heredia",
    "5": "Guanacaste",
    "6": "Puntarenas",
    "7": "Limón",
}

EXPECTED_PROVINCE_IDS = set(
    PROVINCES_BY_ID
)


def load_features(
    path: Path,
) -> list[dict[str, Any]]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file does not exist:\n  {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected a GeoJSON FeatureCollection: {path}"
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"GeoJSON contains no valid features array: {path}"
        )

    if not features:
        raise ValueError(
            f"GeoJSON contains no features: {path}"
        )

    return features


def get_properties(
    feature: dict[str, Any],
) -> dict[str, Any]:
    """Return and validate a feature's properties."""
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            "GeoJSON feature contains no valid properties object."
        )

    return properties


def require_string(
    properties: dict[str, Any],
    property_name: str,
) -> str:
    """Read and validate a required non-empty string property."""
    value = properties.get(
        property_name
    )

    if not isinstance(value, str):
        raise ValueError(
            f"Property {property_name!r} must be a string. "
            f"Got: {value!r}"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"Property {property_name!r} cannot be blank."
        )

    return value


def validate_cantons(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Validate and normalize Costa Rica's canton records."""
    if len(features) != EXPECTED_CANTON_COUNT:
        raise ValueError(
            "Unexpected processed canton count: "
            f"{len(features)}. Expected {EXPECTED_CANTON_COUNT}."
        )

    records: list[dict[str, str]] = []

    for feature in features:
        properties = get_properties(
            feature
        )

        canton_id = require_string(
            properties,
            "canton_id",
        )

        name = require_string(
            properties,
            "name",
        )

        province_id = require_string(
            properties,
            "province_id",
        )

        if (
            len(canton_id) != 3
            or not canton_id.isdigit()
        ):
            raise ValueError(
                f"Invalid canton ID: {canton_id!r}"
            )

        if province_id not in EXPECTED_PROVINCE_IDS:
            raise ValueError(
                f"Invalid province ID: {province_id!r}"
            )

        if canton_id[0] != province_id:
            raise ValueError(
                "Canton/province hierarchy mismatch: "
                f"{canton_id} -> {province_id}"
            )

        records.append(
            {
                "canton_id": canton_id,
                "name": name,
                "province_id": province_id,
            }
        )

    canton_ids = [
        record["canton_id"]
        for record in records
    ]

    if len(set(canton_ids)) != len(canton_ids):
        raise ValueError(
            "Processed canton data contains duplicate canton IDs."
        )

    canton_names = [
        record["name"]
        for record in records
    ]

    if len(set(canton_names)) != len(canton_names):
        raise ValueError(
            "Processed canton data contains duplicate canton names."
        )

    return sorted(
        records,
        key=lambda record: record["canton_id"],
    )


def validate_districts(
    features: list[dict[str, Any]],
    canton_names_by_id: dict[str, str],
) -> list[dict[str, str]]:
    """Validate and normalize Costa Rica's district records."""
    if len(features) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected processed district count: "
            f"{len(features)}. Expected {EXPECTED_DISTRICT_COUNT}."
        )

    records: list[dict[str, str]] = []

    for feature in features:
        properties = get_properties(
            feature
        )

        district_id = require_string(
            properties,
            "district_id",
        )

        name = require_string(
            properties,
            "name",
        )

        canton_id = require_string(
            properties,
            "canton_id",
        )

        province_id = require_string(
            properties,
            "province_id",
        )

        if (
            len(district_id) != 5
            or not district_id.isdigit()
        ):
            raise ValueError(
                f"Invalid district ID: {district_id!r}"
            )

        if canton_id not in canton_names_by_id:
            raise ValueError(
                "District references an unknown canton: "
                f"{district_id} -> {canton_id}"
            )

        if province_id not in EXPECTED_PROVINCE_IDS:
            raise ValueError(
                "District references an unknown province: "
                f"{district_id} -> {province_id}"
            )

        if district_id[:3] != canton_id:
            raise ValueError(
                "District/canton hierarchy mismatch: "
                f"{district_id} -> {canton_id}"
            )

        if district_id[0] != province_id:
            raise ValueError(
                "District/province hierarchy mismatch: "
                f"{district_id} -> {province_id}"
            )

        if canton_id[0] != province_id:
            raise ValueError(
                "Canton/province hierarchy mismatch: "
                f"{canton_id} -> {province_id}"
            )

        records.append(
            {
                "district_id": district_id,
                "name": name,
                "canton_id": canton_id,
                "province_id": province_id,
            }
        )

    district_ids = [
        record["district_id"]
        for record in records
    ]

    if len(set(district_ids)) != len(district_ids):
        raise ValueError(
            "Processed district data contains duplicate district IDs."
        )

    return sorted(
        records,
        key=lambda record: record["district_id"],
    )


def build_cantons(
    records: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Build the generated canton hierarchy."""
    return {
        record["canton_id"]: {
            "name": record["name"],
            "provinceId": record["province_id"],
        }
        for record in records
    }


def build_districts(
    records: list[dict[str, str]],
    canton_names_by_id: dict[str, str],
) -> dict[str, dict[str, str]]:
    """
    Build the generated district hierarchy.

    Duplicate district names are disambiguated with their canton name.
    """
    name_counts = Counter(
        record["name"]
        for record in records
    )

    districts: dict[str, dict[str, str]] = {}

    for record in records:
        name = record["name"]

        if name_counts[name] > 1:
            name = (
                f"{name} "
                f"({canton_names_by_id[record['canton_id']]})"
            )

        districts[
            record["district_id"]
        ] = {
            "name": name,
            "cantonId": record["canton_id"],
            "provinceId": record["province_id"],
        }

    generated_names = [
        district["name"]
        for district in districts.values()
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
            "Canton-based district disambiguation did not produce "
            "unique names:\n"
            + "\n".join(
                f"  {name}"
                for name in duplicate_names
            )
        )

    return districts


def ts_string(
    value: str,
) -> str:
    """Return a safely encoded TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )

def render_provinces() -> str:
    """Render Costa Rica's province dictionary."""
    lines = [
        "export const COSTA_RICA_PROVINCES_BY_ID = {",
    ]

    for province_id, province_name in PROVINCES_BY_ID.items():
        lines.append(
            f"  {ts_string(province_id)}: "
            f"{ts_string(province_name)},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)

def render_cantons(
    cantons: dict[str, dict[str, str]],
) -> str:
    """Render Costa Rica's canton dictionary."""
    lines = [
        "export const COSTA_RICA_CANTONS_BY_ID = {",
    ]

    for canton_id, canton in cantons.items():
        lines.append(
            f"  {ts_string(canton_id)}: "
            "{ "
            f"name: {ts_string(canton['name'])}, "
            f"provinceId: {ts_string(canton['provinceId'])} "
            "},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_districts(
    districts: dict[str, dict[str, str]],
) -> str:
    """Render Costa Rica's district dictionary."""
    lines = [
        "export const COSTA_RICA_DISTRICTS_BY_ID = {",
    ]

    for district_id, district in districts.items():
        lines.append(
            f"  {ts_string(district_id)}: "
            "{ "
            f"name: {ts_string(district['name'])}, "
            f"cantonId: {ts_string(district['cantonId'])}, "
            f"provinceId: {ts_string(district['provinceId'])} "
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
    provinces: dict[str, str],
    cantons: dict[str, dict[str, str]],
    districts: dict[str, dict[str, str]],
) -> str:
    """Create the generated TypeScript admin-data module."""
    return f'''/**
* Generated administrative data for Costa Rica.
*
* Canton and district data are generated from GeoPedia's processed
* administrative GeoJSON. Province names are maintained by this generator.
*
* Do not edit manually.
* Regenerate with:
* python scripts/countries/costa-rica/generate/admin-quiz-data.py
*/

{render_provinces()}{render_cantons(cantons)}{render_districts(districts)}'''


def main() -> None:
    """Generate Costa Rica's administrative quiz data."""
    print(
        "Generating Costa Rica administrative quiz data...\n"
    )

    canton_features = load_features(
        CANTONS_PATH
    )

    district_features = load_features(
        DISTRICTS_PATH
    )

    canton_records = validate_cantons(
        canton_features
    )

    canton_names_by_id = {
        record["canton_id"]: record["name"]
        for record in canton_records
    }

    district_records = validate_districts(
        district_features,
        canton_names_by_id,
    )

    cantons = build_cantons(
        canton_records
    )

    districts = build_districts(
        district_records,
        canton_names_by_id,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            PROVINCES_BY_ID,
            cantons,
            districts,
        ),
        encoding="utf-8",
    )

    disambiguated_districts = sum(
        1
        for record in district_records
        if Counter(
            item["name"]
            for item in district_records
        )[record["name"]] > 1
    )

    print(
        f"Provinces:               {len(PROVINCES_BY_ID):,}"
    )
    print(
        f"Cantons:                 {len(cantons):,}"
    )
    print(
        f"Districts:               {len(districts):,}"
    )
    print(
        f"Disambiguated districts: {disambiguated_districts:,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()