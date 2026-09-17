"""
Generates the administrative quiz data used by GeoPedia's United States
state and county quizzes.

Source:
    public/data/us-counties.geojson

Output:
    src/quiz/quizzes/countries/north-america/usa/data/admin.ts

States are keyed by their two-letter abbreviation. Counties are keyed by
their five-digit Census GEOID and reference their parent state abbreviation.

County names remain unchanged when unique nationwide. When the same full
county name occurs in multiple states, the state name is appended to keep
the generated quiz labels unambiguous.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "usa"
    / "geojson"
    / "counties.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "north-america"
    / "usa"
    / "data"
    / "admin.ts"
)


def load_features() -> list[dict[str, Any]]:
    """Load and validate the processed US county GeoJSON."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Missing processed US county GeoJSON:\n"
            f"  {INPUT_PATH}"
        )

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "US county GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "US county GeoJSON does not contain a feature list."
        )

    if not features:
        raise ValueError(
            "US county GeoJSON contains no features."
        )

    return features


def extract_admin_data(
    features: list[dict[str, Any]],
) -> tuple[
    dict[str, str],
    dict[str, dict[str, str]],
]:
    """
    Extract and validate state and county administrative data.

    Duplicate county names are disambiguated by appending their state name.
    """
    extracted_counties: list[dict[str, str]] = []

    states: dict[str, str] = {}
    county_ids: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"County feature {index} has invalid properties."
            )

        feature_id = feature.get("id")
        geoid = properties.get("geoid")
        county_name = properties.get("fullName")
        state_abbreviation = properties.get("state")
        state_name = properties.get("stateName")

        if (
            not isinstance(geoid, str)
            or not geoid
        ):
            raise ValueError(
                f"County feature {index} has an invalid geoid."
            )

        if len(geoid) != 5 or not geoid.isdigit():
            raise ValueError(
                f"County GEOID {geoid!r} is not a five-digit "
                "Census GEOID."
            )

        if feature_id != geoid:
            raise ValueError(
                f"Feature ID {feature_id!r} does not match "
                f"county GEOID {geoid!r}."
            )

        if (
            not isinstance(county_name, str)
            or not county_name
        ):
            raise ValueError(
                f"County {geoid} has an invalid fullName."
            )

        if (
            not isinstance(state_abbreviation, str)
            or not state_abbreviation
        ):
            raise ValueError(
                f"County {geoid} has an invalid state abbreviation."
            )

        if (
            len(state_abbreviation) != 2
            or not state_abbreviation.isalpha()
            or state_abbreviation.upper()
            != state_abbreviation
        ):
            raise ValueError(
                f"County {geoid} has an invalid state abbreviation "
                f"{state_abbreviation!r}."
            )

        if (
            not isinstance(state_name, str)
            or not state_name
        ):
            raise ValueError(
                f"County {geoid} has an invalid stateName."
            )

        existing_state_name = states.get(
            state_abbreviation
        )

        if (
            existing_state_name is not None
            and existing_state_name != state_name
        ):
            raise ValueError(
                f"State abbreviation {state_abbreviation} has "
                f"conflicting names: {existing_state_name!r} and "
                f"{state_name!r}."
            )

        states[state_abbreviation] = state_name

        if geoid in county_ids:
            raise ValueError(
                f"Duplicate county GEOID {geoid}."
            )

        county_ids.add(geoid)

        extracted_counties.append(
            {
                "id": geoid,
                "name": county_name,
                "stateId": state_abbreviation,
                "stateName": state_name,
            }
        )

    county_name_counts = Counter(
        county["name"]
        for county in extracted_counties
    )

    counties: dict[str, dict[str, str]] = {}

    for county in extracted_counties:
        county_id = county["id"]
        county_name = county["name"]

        if county_name_counts[county_name] > 1:
            display_name = (
                f'{county_name}, {county["stateId"]}'
            )
        else:
            display_name = county_name

        counties[county_id] = {
            "name": display_name,
            "stateId": county["stateId"],
        }

    duplicate_generated_names = [
        name
        for name, count in Counter(
            county["name"]
            for county in counties.values()
        ).items()
        if count > 1
    ]

    if duplicate_generated_names:
        raise ValueError(
            "Generated county names are not unique:\n"
            + "\n".join(
                f"  {name}"
                for name in sorted(
                    duplicate_generated_names
                )
            )
        )

    return (
        dict(sorted(states.items())),
        dict(sorted(counties.items())),
    )


def ts_string(
    value: str,
) -> str:
    """Return a safely encoded TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_states(
    states: dict[str, str],
) -> str:
    """Render the state abbreviation-to-name dictionary."""
    lines = [
        "export const US_SUBDIVISION_BY_ABBREVIATION = {",
    ]

    for state_abbreviation, state_name in states.items():
        lines.append(
            f"  {ts_string(state_abbreviation)}: "
            f"{ts_string(state_name)},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_counties(
    counties: dict[str, dict[str, str]],
) -> str:
    """Render the county administrative hierarchy."""
    lines = [
        "export const US_COUNTIES_BY_ID = {",
    ]

    for county_id, county in counties.items():
        lines.append(
            f"  {ts_string(county_id)}: "
            "{ "
            f"name: {ts_string(county['name'])}, "
            f"stateId: {ts_string(county['stateId'])} "
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
    states: dict[str, str],
    counties: dict[str, dict[str, str]],
) -> str:
    """Create the generated TypeScript admin-data module."""
    state_source = render_states(
        states
    )

    county_source = render_counties(
        counties
    )

    return f'''/**
 * Generated from the United States processed county GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/usa/generate/admin-quiz-data.py
 */

{state_source}{county_source}'''


def main() -> None:
    """Generate United States administrative quiz data."""
    print(
        "Generating US administrative quiz data...\n"
    )

    features = load_features()

    states, counties = extract_admin_data(
        features
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            states,
            counties,
        ),
        encoding="utf-8",
    )

    disambiguated_count = sum(
        1
        for county in counties.values()
        if ", " in county["name"]
    )

    print(
        f"States/entities:       {len(states):,}"
    )
    print(
        f"Counties:              {len(counties):,}"
    )
    print(
        f"Disambiguated counties: {disambiguated_count:,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()