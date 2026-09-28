"""
Generate reusable Kenya administrative quiz-support data from GeoPedia's
canonical intermediate administrative GeoJSON files.

County, sub-county, and ward geometry remains in the runtime GeoJSON files.
This generated module contains only names, display names, and hierarchy
metadata needed by quiz configurations.

Duplicate ward names are disambiguated using their parent sub-county. If that
is still insufficient, the parent county is also included.

Inputs:
    data/intermediate/countries/kenya/admin/counties.geojson
    data/intermediate/countries/kenya/admin/sub-counties.geojson
    data/intermediate/countries/kenya/admin/wards.geojson

Output:
    src/quiz/quizzes/countries/africa/kenya/data/admin.ts
"""

import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "kenya"
    / "admin"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "kenya"
    / "data"
    / "admin.ts"
)

COUNTIES_INPUT = INPUT_DIR / "counties.geojson"
SUB_COUNTIES_INPUT = INPUT_DIR / "sub-counties.geojson"
WARDS_INPUT = INPUT_DIR / "wards.geojson"

EXPECTED_COUNTY_COUNT = 47
EXPECTED_SUB_COUNTY_COUNT = 290
EXPECTED_WARD_COUNT = 1452


def load_features(
    path: Path,
    expected_count: int,
) -> list[dict]:
    """Load and validate features from a canonical GeoJSON file."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features", [])

    if len(features) != expected_count:
        raise ValueError(
            f"{path.name} has {len(features)} features; "
            f"expected {expected_count}."
        )

    return features


def require_string(
    properties: dict,
    key: str,
    level: str,
) -> str:
    """Read and validate one required canonical string property."""
    value = properties.get(key)

    if not isinstance(value, str) or not value:
        raise ValueError(
            f"{level} feature has invalid {key}: {value!r}"
        )

    return value


def ts_string(value: str) -> str:
    """Serialize a string using JSON-compatible TypeScript syntax."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def build_counties(
    features: list[dict],
) -> list[dict[str, str]]:
    """Extract and validate county quiz metadata."""
    counties = []
    seen_ids = set()
    seen_names = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        county_id = require_string(
            properties,
            "county_id",
            "County",
        )

        county = require_string(
            properties,
            "county",
            "County",
        )

        if county_id in seen_ids:
            raise ValueError(
                f"Duplicate county ID: {county_id}"
            )

        if county in seen_names:
            raise ValueError(
                f"Duplicate county name: {county}"
            )

        seen_ids.add(county_id)
        seen_names.add(county)

        counties.append(
            {
                "id": county_id,
                "name": county,
            }
        )

    return sorted(
        counties,
        key=lambda item: item["name"],
    )


def build_sub_counties(
    features: list[dict],
) -> list[dict[str, str]]:
    """Extract and validate sub-county quiz and hierarchy metadata."""
    sub_counties = []
    seen_ids = set()
    seen_names = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        sub_county_id = require_string(
            properties,
            "sub_county_id",
            "Sub-county",
        )

        sub_county = require_string(
            properties,
            "sub_county",
            "Sub-county",
        )

        county_id = require_string(
            properties,
            "county_id",
            "Sub-county",
        )

        county = require_string(
            properties,
            "county",
            "Sub-county",
        )

        if sub_county_id in seen_ids:
            raise ValueError(
                f"Duplicate sub-county ID: {sub_county_id}"
            )

        if sub_county in seen_names:
            raise ValueError(
                f"Duplicate sub-county name: {sub_county}"
            )

        seen_ids.add(sub_county_id)
        seen_names.add(sub_county)

        sub_counties.append(
            {
                "id": sub_county_id,
                "name": sub_county,
                "countyId": county_id,
                "county": county,
            }
        )

    return sorted(
        sub_counties,
        key=lambda item: (
            item["county"],
            item["name"],
        ),
    )


def build_wards(
    features: list[dict],
) -> list[dict[str, str]]:
    """
    Extract ward metadata and create disambiguated quiz displays where possible.

    Duplicate ward names first receive their parent sub-county. County names are
    added when the same name also occurs across counties. If identically named
    wards occur within the same sub-county and county, their displays remain
    identical because the administrative hierarchy provides no truthful way to
    distinguish them.
    """
    wards = []
    seen_ids = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        ward_id = require_string(
            properties,
            "ward_id",
            "Ward",
        )

        ward = require_string(
            properties,
            "ward",
            "Ward",
        )

        sub_county_id = require_string(
            properties,
            "sub_county_id",
            "Ward",
        )

        sub_county = require_string(
            properties,
            "sub_county",
            "Ward",
        )

        county_id = require_string(
            properties,
            "county_id",
            "Ward",
        )

        county = require_string(
            properties,
            "county",
            "Ward",
        )

        if ward_id in seen_ids:
            raise ValueError(
                f"Duplicate ward ID: {ward_id}"
            )

        seen_ids.add(ward_id)

        wards.append(
            {
                "id": ward_id,
                "name": ward,
                "display": ward,
                "subCountyId": sub_county_id,
                "subCounty": sub_county,
                "countyId": county_id,
                "county": county,
            }
        )

    name_counts = Counter(
        item["name"]
        for item in wards
    )

    for item in wards:
        if name_counts[item["name"]] > 1:
            item["display"] = (
                f"{item['name']} "
                f"({item['subCounty']})"
            )

    duplicate_groups: dict[
        tuple[str, str],
        list[dict[str, str]],
    ] = {}

    for item in wards:
        if name_counts[item["name"]] <= 1:
            continue

        key = (
            item["name"],
            item["subCounty"],
        )

        duplicate_groups.setdefault(
            key,
            [],
        ).append(item)

    for group in duplicate_groups.values():
        counties = {
            item["county"]
            for item in group
        }

        if len(counties) <= 1:
            continue

        for item in group:
            item["display"] = (
                f"{item['name']} "
                f"({item['subCounty']}, {item['county']})"
            )

    return sorted(
        wards,
        key=lambda item: (
            item["county"],
            item["subCounty"],
            item["name"],
        ),
    )


def render_counties(
    counties: list[dict[str, str]],
) -> str:
    """Render the county lookup as TypeScript."""
    lines = [
        "export const KENYA_COUNTIES_BY_ID = {",
    ]

    for item in counties:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def render_sub_counties(
    sub_counties: list[dict[str, str]],
) -> str:
    """Render the sub-county lookup as TypeScript."""
    lines = [
        "export const KENYA_SUB_COUNTIES_BY_ID = {",
    ]

    for item in sub_counties:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    countyId: {ts_string(item['countyId'])},",
                f"    county: {ts_string(item['county'])},",
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def render_wards(
    wards: list[dict[str, str]],
) -> str:
    """Render the ward lookup as TypeScript."""
    lines = [
        "export const KENYA_WARDS_BY_ID = {",
    ]

    for item in wards:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    display: {ts_string(item['display'])},",
                f"    subCountyId: {ts_string(item['subCountyId'])},",
                f"    subCounty: {ts_string(item['subCounty'])},",
                f"    countyId: {ts_string(item['countyId'])},",
                f"    county: {ts_string(item['county'])},",
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def write_output(
    counties: list[dict[str, str]],
    sub_counties: list[dict[str, str]],
    wards: list[dict[str, str]],
) -> None:
    """Write the generated TypeScript quiz-support module."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = f"""/**
 * Generated Kenya administrative quiz-support data.
 *
 * Do not edit this file manually.
 *
 * Regenerate with:
 *   python scripts/countries/kenya/generate/admin-quiz-data.py
 */

{render_counties(counties)}

{render_sub_counties(sub_counties)}

{render_wards(wards)}
"""

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )


def main() -> None:
    """Generate Kenya's reusable administrative quiz metadata."""
    print("Generating Kenya administrative quiz data...")
    print()

    county_features = load_features(
        COUNTIES_INPUT,
        EXPECTED_COUNTY_COUNT,
    )

    sub_county_features = load_features(
        SUB_COUNTIES_INPUT,
        EXPECTED_SUB_COUNTY_COUNT,
    )

    ward_features = load_features(
        WARDS_INPUT,
        EXPECTED_WARD_COUNT,
    )

    counties = build_counties(
        county_features
    )

    sub_counties = build_sub_counties(
        sub_county_features
    )

    wards = build_wards(
        ward_features
    )

    write_output(
        counties,
        sub_counties,
        wards,
    )

    duplicated_ward_names = sum(
        1
        for count in Counter(
            item["name"]
            for item in wards
        ).values()
        if count > 1
    )

    disambiguated_wards = sum(
        1
        for item in wards
        if item["display"] != item["name"]
    )

    print(
        "Kenya administrative quiz-data "
        "generation complete."
    )
    print(
        f"  Counties:             {len(counties)}"
    )
    print(
        f"  Sub-counties:         {len(sub_counties)}"
    )
    print(
        f"  Wards:                {len(wards)}"
    )
    print(
        f"  Duplicate ward names: {duplicated_ward_names}"
    )
    print(
        f"  Disambiguated wards:  {disambiguated_wards}"
    )
    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()