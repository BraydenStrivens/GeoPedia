"""
Generates the administrative quiz data used by GeoPedia's Dominican
Republic region, province, and municipality quizzes.

Sources:
    public/data/countries/dominican-republic/geojson/regions.geojson
    public/data/countries/dominican-republic/geojson/provinces.geojson
    public/data/countries/dominican-republic/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/countries/central-america/dominican-republic/data/admin.ts

Regions are keyed by their normalized 2-digit ONE IDs.

Provinces are keyed by their normalized 4-digit ONE IDs and reference
their parent region.

Municipalities are keyed by their normalized 6-digit ONE IDs and reference
their parent province and region.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

GEOJSON_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "dominican-republic"
    / "geojson"
)

REGIONS_PATH = (
    GEOJSON_DIRECTORY
    / "regions.geojson"
)

PROVINCES_PATH = (
    GEOJSON_DIRECTORY
    / "provinces.geojson"
)

MUNICIPALITIES_PATH = (
    GEOJSON_DIRECTORY
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "central-america"
    / "dominican-republic"
    / "data"
    / "admin.ts"
)


EXPECTED_REGION_COUNT = 10
EXPECTED_PROVINCE_COUNT = 32
EXPECTED_MUNICIPALITY_COUNT = 155


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


def validate_regions(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Validate and normalize Dominican Republic region records."""
    if len(features) != EXPECTED_REGION_COUNT:
        raise ValueError(
            "Unexpected region count: "
            f"{len(features)}. Expected {EXPECTED_REGION_COUNT}."
        )

    records: list[dict[str, str]] = []

    for feature in features:
        properties = get_properties(
            feature
        )

        region_id = require_string(
            properties,
            "region_id",
        )

        name = require_string(
            properties,
            "name",
        )

        if (
            len(region_id) != 2
            or not region_id.isdigit()
        ):
            raise ValueError(
                f"Invalid region ID: {region_id!r}"
            )

        records.append(
            {
                "region_id": region_id,
                "name": name,
            }
        )

    region_ids = [
        record["region_id"]
        for record in records
    ]

    if len(set(region_ids)) != len(region_ids):
        raise ValueError(
            "Region data contains duplicate region IDs."
        )

    return sorted(
        records,
        key=lambda record: record["region_id"],
    )


def validate_provinces(
    features: list[dict[str, Any]],
    region_ids: set[str],
) -> list[dict[str, str]]:
    """Validate and normalize Dominican Republic province records."""
    if len(features) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            "Unexpected province count: "
            f"{len(features)}. Expected {EXPECTED_PROVINCE_COUNT}."
        )

    records: list[dict[str, str]] = []

    for feature in features:
        properties = get_properties(
            feature
        )

        province_id = require_string(
            properties,
            "province_id",
        )

        name = require_string(
            properties,
            "name",
        )

        region_id = require_string(
            properties,
            "region_id",
        )

        if (
            len(province_id) != 4
            or not province_id.isdigit()
        ):
            raise ValueError(
                f"Invalid province ID: {province_id!r}"
            )

        if region_id not in region_ids:
            raise ValueError(
                "Province references an unknown region: "
                f"{province_id} -> {region_id}"
            )

        if province_id[:2] != region_id:
            raise ValueError(
                "Province/region hierarchy mismatch: "
                f"{province_id} -> {region_id}"
            )

        records.append(
            {
                "province_id": province_id,
                "name": name,
                "region_id": region_id,
            }
        )

    province_ids = [
        record["province_id"]
        for record in records
    ]

    if len(set(province_ids)) != len(province_ids):
        raise ValueError(
            "Province data contains duplicate province IDs."
        )

    return sorted(
        records,
        key=lambda record: record["province_id"],
    )


def validate_municipalities(
    features: list[dict[str, Any]],
    province_ids: set[str],
    region_ids: set[str],
) -> list[dict[str, str]]:
    """Validate and normalize Dominican Republic municipality records."""
    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            "Unexpected municipality count: "
            f"{len(features)}. "
            f"Expected {EXPECTED_MUNICIPALITY_COUNT}."
        )

    records: list[dict[str, str]] = []

    for feature in features:
        properties = get_properties(
            feature
        )

        municipality_id = require_string(
            properties,
            "municipality_id",
        )

        name = require_string(
            properties,
            "name",
        )

        province_id = require_string(
            properties,
            "province_id",
        )

        region_id = require_string(
            properties,
            "region_id",
        )

        if (
            len(municipality_id) != 6
            or not municipality_id.isdigit()
        ):
            raise ValueError(
                f"Invalid municipality ID: {municipality_id!r}"
            )

        if province_id not in province_ids:
            raise ValueError(
                "Municipality references an unknown province: "
                f"{municipality_id} -> {province_id}"
            )

        if region_id not in region_ids:
            raise ValueError(
                "Municipality references an unknown region: "
                f"{municipality_id} -> {region_id}"
            )

        if municipality_id[:4] != province_id:
            raise ValueError(
                "Municipality/province hierarchy mismatch: "
                f"{municipality_id} -> {province_id}"
            )

        if municipality_id[:2] != region_id:
            raise ValueError(
                "Municipality/region hierarchy mismatch: "
                f"{municipality_id} -> {region_id}"
            )

        if province_id[:2] != region_id:
            raise ValueError(
                "Province/region hierarchy mismatch: "
                f"{province_id} -> {region_id}"
            )

        records.append(
            {
                "municipality_id": municipality_id,
                "name": name,
                "province_id": province_id,
                "region_id": region_id,
            }
        )

    municipality_ids = [
        record["municipality_id"]
        for record in records
    ]

    if len(set(municipality_ids)) != len(municipality_ids):
        raise ValueError(
            "Municipality data contains duplicate municipality IDs."
        )

    return sorted(
        records,
        key=lambda record: record["municipality_id"],
    )


def build_regions(
    records: list[dict[str, str]],
) -> dict[str, str]:
    """Build the generated region dictionary."""
    return {
        record["region_id"]: record["name"]
        for record in records
    }


def build_provinces(
    records: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Build the generated province hierarchy."""
    return {
        record["province_id"]: {
            "name": record["name"],
            "regionId": record["region_id"],
        }
        for record in records
    }


def build_municipalities(
    records: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Build the generated municipality hierarchy."""
    return {
        record["municipality_id"]: {
            "name": record["name"],
            "provinceId": record["province_id"],
            "regionId": record["region_id"],
        }
        for record in records
    }


def ts_string(
    value: str,
) -> str:
    """Return a safely encoded TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_regions(
    regions: dict[str, str],
) -> str:
    """Render the region dictionary."""
    lines = [
        "export const DOMINICAN_REPUBLIC_REGIONS_BY_ID = {",
    ]

    for region_id, name in regions.items():
        lines.append(
            f"  {ts_string(region_id)}: {ts_string(name)},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_provinces(
    provinces: dict[str, dict[str, str]],
) -> str:
    """Render the province hierarchy."""
    lines = [
        "export const DOMINICAN_REPUBLIC_PROVINCES_BY_ID = {",
    ]

    for province_id, province in provinces.items():
        lines.append(
            f"  {ts_string(province_id)}: "
            "{ "
            f"name: {ts_string(province['name'])}, "
            f"regionId: {ts_string(province['regionId'])} "
            "},"
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
    """Render the municipality hierarchy."""
    lines = [
        "export const DOMINICAN_REPUBLIC_MUNICIPALITIES_BY_ID = {",
    ]

    for municipality_id, municipality in municipalities.items():
        lines.append(
            f"  {ts_string(municipality_id)}: "
            "{ "
            f"name: {ts_string(municipality['name'])}, "
            f"provinceId: {ts_string(municipality['provinceId'])}, "
            f"regionId: {ts_string(municipality['regionId'])} "
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
    regions: dict[str, str],
    provinces: dict[str, dict[str, str]],
    municipalities: dict[str, dict[str, str]],
) -> str:
    """Create the generated TypeScript admin-data module."""
    return f'''/**
 * Generated from the Dominican Republic's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/dominican-republic/generate/admin-quiz-data.py
 */

{render_regions(regions)}{render_provinces(provinces)}{render_municipalities(municipalities)}'''


def main() -> None:
    """Generate Dominican Republic administrative quiz data."""
    print(
        "Generating Dominican Republic administrative quiz data...\n"
    )

    region_records = validate_regions(
        load_features(
            REGIONS_PATH
        )
    )

    region_ids = {
        record["region_id"]
        for record in region_records
    }

    province_records = validate_provinces(
        load_features(
            PROVINCES_PATH
        ),
        region_ids,
    )

    province_ids = {
        record["province_id"]
        for record in province_records
    }

    municipality_records = validate_municipalities(
        load_features(
            MUNICIPALITIES_PATH
        ),
        province_ids,
        region_ids,
    )

    regions = build_regions(
        region_records
    )

    provinces = build_provinces(
        province_records
    )

    municipalities = build_municipalities(
        municipality_records
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            regions,
            provinces,
            municipalities,
        ),
        encoding="utf-8",
    )

    print(
        f"Regions:        {len(regions):,}"
    )
    print(
        f"Provinces:      {len(provinces):,}"
    )
    print(
        f"Municipalities: {len(municipalities):,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()