"""
Generates the administrative data used by Brazil's quiz configurations.

Sources:
    public/data/countries/brazil/geojson/regions.geojson
    public/data/countries/brazil/geojson/states.geojson
    public/data/countries/brazil/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/countries/south-america/brazil/data/admin.ts

The processed administrative GeoJSON is the canonical source for region,
state, and municipality IDs, names, and hierarchy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

REGIONS_SOURCE_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
    / "regions.geojson"
)

STATES_SOURCE_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
    / "states.geojson"
)

MUNICIPALITIES_SOURCE_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "south-america"
    / "brazil"
    / "data"
    / "admin.ts"
)

EXPECTED_REGION_COUNT = 5
EXPECTED_STATE_COUNT = 27
EXPECTED_MUNICIPALITY_COUNT = 5_573


def quote(value: str) -> str:
    """Serialize a string as a valid TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def load_features(
    path: Path,
    label: str,
) -> list[dict[str, Any]]:
    """Load and validate one processed GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"{label} GeoJSON was not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

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
    properties: dict[str, Any],
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


def build_regions(
    features: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Extract Brazil's region IDs and names."""
    if len(features) != EXPECTED_REGION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} regions, "
            f"found {len(features)}."
        )

    entries: list[tuple[str, str]] = []
    seen_ids: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Region feature {index} has invalid properties."
            )

        region_id = require_string(
            properties,
            "id",
            f"Region feature {index}",
        )

        name = require_string(
            properties,
            "name",
            f"Region {region_id}",
        )

        if region_id in seen_ids:
            raise ValueError(
                f"Duplicate region ID: {region_id}"
            )

        seen_ids.add(region_id)

        entries.append(
            (
                region_id,
                name,
            )
        )

    entries.sort(key=lambda entry: entry[0])

    return entries


def build_states(
    features: list[dict[str, Any]],
) -> list[tuple[str, str, str]]:
    """Extract Brazil's state IDs, names, and parent region IDs."""
    if len(features) != EXPECTED_STATE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_STATE_COUNT} states, "
            f"found {len(features)}."
        )

    entries: list[tuple[str, str, str]] = []
    seen_ids: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"State feature {index} has invalid properties."
            )

        state_id = require_string(
            properties,
            "id",
            f"State feature {index}",
        )

        name = require_string(
            properties,
            "name",
            f"State {state_id}",
        )

        region_id = require_string(
            properties,
            "region_id",
            f"State {state_id}",
        )

        if state_id in seen_ids:
            raise ValueError(
                f"Duplicate state ID: {state_id}"
            )

        seen_ids.add(state_id)

        entries.append(
            (
                state_id,
                name,
                region_id,
            )
        )

    entries.sort(key=lambda entry: entry[0])

    return entries


def build_municipalities(
    features: list[dict[str, Any]],
) -> list[tuple[str, str, str]]:
    """Extract municipality IDs, names, and parent state IDs."""
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

        state_id = require_string(
            properties,
            "state_id",
            f"Municipality {municipality_id}",
        )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id}"
            )

        seen_ids.add(municipality_id)

        entries.append(
            (
                municipality_id,
                name,
                state_id,
            )
        )

    entries.sort(key=lambda entry: entry[0])

    return entries


def validate_hierarchy(
    regions: list[tuple[str, str]],
    states: list[tuple[str, str, str]],
    municipalities: list[tuple[str, str, str]],
) -> dict[str, str]:
    """
    Validate the administrative hierarchy.

    Returns a state-to-region lookup so municipality entries can include both
    their direct state parent and their derived region parent.
    """
    region_ids = {
        region_id
        for region_id, _ in regions
    }

    state_to_region: dict[str, str] = {}

    for state_id, _, region_id in states:
        if region_id not in region_ids:
            raise ValueError(
                f"State {state_id} references unknown region "
                f"{region_id}."
            )

        state_to_region[state_id] = region_id

    for municipality_id, _, state_id in municipalities:
        if state_id not in state_to_region:
            raise ValueError(
                f"Municipality {municipality_id} references unknown "
                f"state {state_id}."
            )

    return state_to_region


def format_regions(
    regions: list[tuple[str, str]],
) -> str:
    """Format Brazil's region dictionary."""
    lines = "\n".join(
        f"  {quote(region_id)}: {quote(name)},"
        for region_id, name in regions
    )

    return f"""export const BRAZIL_REGIONS_BY_ID = {{
{lines}
}} as const;"""


def format_states(
    states: list[tuple[str, str, str]],
) -> str:
    """Format Brazil's state dictionary."""
    lines = "\n".join(
        (
            f"  {quote(state_id)}: {{ "
            f"name: {quote(name)}, "
            f"regionId: {quote(region_id)} "
            f"}},"
        )
        for state_id, name, region_id in states
    )

    return f"""export const BRAZIL_STATES_BY_ID = {{
{lines}
}} as const;"""


def format_municipalities(
    municipalities: list[tuple[str, str, str]],
    state_to_region: dict[str, str],
) -> str:
    """Format Brazil's municipality dictionary."""
    lines = "\n".join(
        (
            f"  {quote(municipality_id)}: {{ "
            f"name: {quote(name)}, "
            f"stateId: {quote(state_id)}, "
            f"regionId: {quote(state_to_region[state_id])} "
            f"}},"
        )
        for municipality_id, name, state_id in municipalities
    )

    return f"""export const BRAZIL_MUNICIPALITIES_BY_ID = {{
{lines}
}} as const;"""


def create_source(
    regions: list[tuple[str, str]],
    states: list[tuple[str, str, str]],
    municipalities: list[tuple[str, str, str]],
    state_to_region: dict[str, str],
) -> str:
    """Create the generated Brazil administrative data module."""
    return f'''/**
 * Generated from Brazil's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/brazil/generate/admin-quiz-data.py
 */

{format_regions(regions)}

{format_states(states)}

{format_municipalities(municipalities, state_to_region)}
'''


def main() -> None:
    """Generate Brazil's administrative quiz data."""
    print("Generating Brazil administrative quiz data...\n")

    region_features = load_features(
        REGIONS_SOURCE_PATH,
        "Region",
    )

    state_features = load_features(
        STATES_SOURCE_PATH,
        "State",
    )

    municipality_features = load_features(
        MUNICIPALITIES_SOURCE_PATH,
        "Municipality",
    )

    regions = build_regions(
        region_features,
    )

    states = build_states(
        state_features,
    )

    municipalities = build_municipalities(
        municipality_features,
    )

    state_to_region = validate_hierarchy(
        regions,
        states,
        municipalities,
    )

    source = create_source(
        regions,
        states,
        municipalities,
        state_to_region,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print(f"Regions:        {len(regions):,}")
    print(f"States:         {len(states):,}")
    print(f"Municipalities: {len(municipalities):,}")
    print(f"\nGenerated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()