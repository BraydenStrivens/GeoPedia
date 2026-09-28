"""
Generate reusable Nigeria administrative quiz data from GeoPedia's canonical
intermediate GeoJSON files.

The generated TypeScript contains only quiz-support metadata. Geometry remains
in the runtime GeoJSON files.

Inputs:
    data/intermediate/countries/nigeria/admin/states.geojson
    data/intermediate/countries/nigeria/admin/local-government-areas.geojson

Output:
    src/quiz/quizzes/countries/africa/nigeria/data/admin.ts
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
    / "nigeria"
    / "admin"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "nigeria"
    / "data"
    / "admin.ts"
)

STATES_INPUT = INPUT_DIR / "states.geojson"
LGAS_INPUT = INPUT_DIR / "local-government-areas.geojson"

EXPECTED_STATE_COUNT = 37
EXPECTED_LGA_COUNT = 774


def load_features(
    path: Path,
    expected_count: int,
) -> list[dict]:
    """Load and validate a canonical GeoJSON FeatureCollection."""
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


def ts_string(value: str) -> str:
    """Serialize a string using JSON-compatible TypeScript syntax."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def build_states(
    features: list[dict],
) -> list[dict[str, str]]:
    """Extract and validate state/FCT quiz metadata."""
    states = []
    seen_ids = set()

    for feature in features:
        properties = feature.get("properties", {})

        state_id = properties.get("state_id")
        state = properties.get("state")

        if not isinstance(state_id, str) or not state_id:
            raise ValueError(
                "State feature has an invalid state_id."
            )

        if not isinstance(state, str) or not state:
            raise ValueError(
                f"State {state_id!r} has an invalid name."
            )

        if state_id in seen_ids:
            raise ValueError(
                f"Duplicate state ID: {state_id}"
            )

        seen_ids.add(state_id)

        states.append(
            {
                "id": state_id,
                "name": state,
            }
        )

    return sorted(
        states,
        key=lambda item: item["name"],
    )


def build_lgas(
    features: list[dict],
) -> list[dict[str, str]]:
    """
    Extract LGA quiz metadata and disambiguate duplicate LGA names using their
    parent state for question display.
    """
    raw_lgas = []

    seen_ids = set()

    for feature in features:
        properties = feature.get("properties", {})

        lga_id = properties.get("lga_id")
        lga = properties.get("lga")
        state_id = properties.get("state_id")
        state = properties.get("state")

        values = {
            "lga_id": lga_id,
            "lga": lga,
            "state_id": state_id,
            "state": state,
        }

        for key, value in values.items():
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"LGA feature has invalid {key}: {value!r}"
                )

        if lga_id in seen_ids:
            raise ValueError(
                f"Duplicate LGA ID: {lga_id}"
            )

        seen_ids.add(lga_id)

        raw_lgas.append(
            {
                "id": lga_id,
                "name": lga,
                "stateId": state_id,
                "state": state,
            }
        )

    name_counts = Counter(
        item["name"]
        for item in raw_lgas
    )

    lgas = []

    for item in raw_lgas:
        display = item["name"]

        if name_counts[item["name"]] > 1:
            display = (
                f"{item['name']} "
                f"({item['state']})"
            )

        lgas.append(
            {
                **item,
                "display": display,
            }
        )

    displays = [
        item["display"]
        for item in lgas
    ]

    if len(displays) != len(set(displays)):
        duplicates = sorted(
            name
            for name, count in Counter(displays).items()
            if count > 1
        )

        raise ValueError(
            "LGA displays are still duplicated after "
            f"state disambiguation: {duplicates}"
        )

    return sorted(
        lgas,
        key=lambda item: (
            item["state"],
            item["name"],
        ),
    )


def render_states(
    states: list[dict[str, str]],
) -> str:
    """Render the state/FCT lookup as TypeScript."""
    lines = [
        "export const NIGERIA_STATES_BY_ID = {",
    ]

    for item in states:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def render_lgas(
    lgas: list[dict[str, str]],
) -> str:
    """Render the LGA lookup as TypeScript."""
    lines = [
        "export const NIGERIA_LGAS_BY_ID = {",
    ]

    for item in lgas:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    display: {ts_string(item['display'])},",
                f"    stateId: {ts_string(item['stateId'])},",
                f"    state: {ts_string(item['state'])},",
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def write_output(
    states: list[dict[str, str]],
    lgas: list[dict[str, str]],
) -> None:
    """Write the generated TypeScript quiz-support module."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = f"""/**
 * Generated Nigeria administrative quiz-support data.
 *
 * Do not edit this file manually.
 *
 * Regenerate with:
 *   python scripts/countries/nigeria/generate/admin-quiz-data.py
 */

{render_states(states)}

{render_lgas(lgas)}
"""

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )


def main() -> None:
    """Generate Nigeria's reusable administrative quiz metadata."""
    print("Generating Nigeria administrative quiz data...")
    print()

    state_features = load_features(
        STATES_INPUT,
        EXPECTED_STATE_COUNT,
    )

    lga_features = load_features(
        LGAS_INPUT,
        EXPECTED_LGA_COUNT,
    )

    states = build_states(state_features)
    lgas = build_lgas(lga_features)

    write_output(
        states,
        lgas,
    )

    duplicate_names = sum(
        count - 1
        for count in Counter(
            item["name"]
            for item in lgas
        ).values()
        if count > 1
    )

    print("Nigeria administrative quiz-data generation complete.")
    print(f"  States/FCT: {len(states)}")
    print(f"  LGAs:       {len(lgas)}")
    print(
        "  Duplicate LGA entries requiring "
        f"disambiguation: {duplicate_names}"
    )
    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()