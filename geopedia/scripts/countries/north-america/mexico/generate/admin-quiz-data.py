"""
Generates the administrative quiz data used by Mexico's state and
municipality quizzes.

Source:
    public/data/countries/mexico/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/countries/north-america/mexico/data/admin.ts

The generated data contains:
    - Mexican states/entities keyed by their two-digit INEGI ID.
    - Municipalities keyed by their five-digit INEGI municipality ID.

Municipality names are disambiguated only when necessary. If a municipality
name occurs in multiple states, its state abbreviation is appended. If the
same name occurs multiple times within one state, its three-digit local
municipality code is appended as well.
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
    / "mexico"
    / "geojson"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "north-america"
    / "mexico"
    / "data"
    / "admin.ts"
)


EXPECTED_MUNICIPALITY_COUNT = 2478
EXPECTED_STATE_COUNT = 32

EXPECTED_STATE_IDS = {
    f"{state_id:02d}"
    for state_id in range(
        1,
        EXPECTED_STATE_COUNT + 1,
    )
}


MEXICO_STATE_NAMES_BY_ID = {
    "01": "Aguascalientes",
    "02": "Baja California",
    "03": "Baja California Sur",
    "04": "Campeche",
    "05": "Coahuila de Zaragoza",
    "06": "Colima",
    "07": "Chiapas",
    "08": "Chihuahua",
    "09": "Ciudad de México",
    "10": "Durango",
    "11": "Guanajuato",
    "12": "Guerrero",
    "13": "Hidalgo",
    "14": "Jalisco",
    "15": "México",
    "16": "Michoacán de Ocampo",
    "17": "Morelos",
    "18": "Nayarit",
    "19": "Nuevo León",
    "20": "Oaxaca",
    "21": "Puebla",
    "22": "Querétaro",
    "23": "Quintana Roo",
    "24": "San Luis Potosí",
    "25": "Sinaloa",
    "26": "Sonora",
    "27": "Tabasco",
    "28": "Tamaulipas",
    "29": "Tlaxcala",
    "30": "Veracruz de Ignacio de la Llave",
    "31": "Yucatán",
    "32": "Zacatecas",
}

MEXICO_STATE_ABBREVIATIONS_BY_ID = {
    "01": "Ags.",
    "02": "B.C.",
    "03": "B.C.S.",
    "04": "Camp.",
    "05": "Coah.",
    "06": "Col.",
    "07": "Chis.",
    "08": "Chih.",
    "09": "CDMX",
    "10": "Dgo.",
    "11": "Gto.",
    "12": "Gro.",
    "13": "Hgo.",
    "14": "Jal.",
    "15": "Méx.",
    "16": "Mich.",
    "17": "Mor.",
    "18": "Nay.",
    "19": "N.L.",
    "20": "Oax.",
    "21": "Pue.",
    "22": "Qro.",
    "23": "Q. Roo",
    "24": "S.L.P.",
    "25": "Sin.",
    "26": "Son.",
    "27": "Tab.",
    "28": "Tamps.",
    "29": "Tlax.",
    "30": "Ver.",
    "31": "Yuc.",
    "32": "Zac.",
}


def to_typescript_string(
    value: str,
) -> str:
    """Convert a Python string into a safe TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def load_features() -> list[dict[str, Any]]:
    """Load and validate Mexico's processed municipality GeoJSON."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Missing processed Mexico municipality GeoJSON:\n"
            f"  {INPUT_PATH}\n\n"
            "Run the municipality processor first."
        )

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Municipality GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Municipality GeoJSON does not contain a feature list."
        )

    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            "Unexpected municipality count: "
            f"expected {EXPECTED_MUNICIPALITY_COUNT:,}, "
            f"found {len(features):,}."
        )

    return features


def extract_municipalities(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract and validate Mexico's municipality hierarchy."""
    municipalities: list[dict[str, str]] = []

    municipality_ids: set[str] = set()
    state_ids: set[str] = set()

    for feature in features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "Found municipality feature with invalid properties."
            )

        feature_id = feature.get("id")
        municipality_id = properties.get(
            "municipality_id"
        )
        name = properties.get("name")
        state_id = properties.get("state_id")

        if (
            not isinstance(municipality_id, str)
            or not municipality_id
        ):
            raise ValueError(
                f"Feature {feature_id!r} has an invalid municipality_id."
            )

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Municipality {municipality_id} has an invalid name."
            )

        if (
            not isinstance(state_id, str)
            or not state_id
        ):
            raise ValueError(
                f"Municipality {municipality_id} has an invalid state_id."
            )

        if feature_id != municipality_id:
            raise ValueError(
                f"Feature ID {feature_id!r} does not match "
                f"municipality_id {municipality_id!r}."
            )

        if len(municipality_id) != 5:
            raise ValueError(
                f"Municipality ID {municipality_id!r} is not five digits."
            )

        if len(state_id) != 2:
            raise ValueError(
                f"State ID {state_id!r} is not two digits."
            )

        if not municipality_id.startswith(
            state_id
        ):
            raise ValueError(
                f"Municipality {municipality_id} does not belong to "
                f"state ID {state_id}."
            )

        if state_id not in MEXICO_STATE_NAMES_BY_ID:
            raise ValueError(
                f"Municipality {municipality_id} uses unknown "
                f"state ID {state_id}."
            )

        if (
            state_id
            not in MEXICO_STATE_ABBREVIATIONS_BY_ID
        ):
            raise ValueError(
                f"Municipality {municipality_id} has no configured "
                f"state abbreviation for {state_id}."
            )

        if municipality_id in municipality_ids:
            raise ValueError(
                f"Duplicate municipality ID {municipality_id}."
            )

        municipality_ids.add(
            municipality_id
        )
        state_ids.add(
            state_id
        )

        municipalities.append(
            {
                "municipality_id": municipality_id,
                "municipality_code": municipality_id[-3:],
                "name": name,
                "state_id": state_id,
            }
        )

    if state_ids != EXPECTED_STATE_IDS:
        missing = sorted(
            EXPECTED_STATE_IDS - state_ids
        )
        unexpected = sorted(
            state_ids - EXPECTED_STATE_IDS
        )

        raise ValueError(
            "Unexpected set of state IDs in municipality data.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    municipalities.sort(
        key=lambda municipality:
        municipality["municipality_id"]
    )

    return municipalities


def create_display_names(
    municipalities: list[dict[str, str]],
) -> dict[str, str]:
    """Create unique municipality display names with minimal disambiguation."""
    name_counts = Counter(
        municipality["name"]
        for municipality in municipalities
    )

    name_state_counts = Counter(
        (
            municipality["name"],
            municipality["state_id"],
        )
        for municipality in municipalities
    )

    display_names: dict[str, str] = {}

    for municipality in municipalities:
        municipality_id = municipality[
            "municipality_id"
        ]
        municipality_code = municipality[
            "municipality_code"
        ]
        name = municipality["name"]
        state_id = municipality["state_id"]

        if name_counts[name] == 1:
            display = name

        elif (
            name_state_counts[
                (name, state_id)
            ]
            == 1
        ):
            state_abbreviation = (
                MEXICO_STATE_ABBREVIATIONS_BY_ID[
                    state_id
                ]
            )

            display = (
                f"{name} ({state_abbreviation})"
            )

        else:
            state_abbreviation = (
                MEXICO_STATE_ABBREVIATIONS_BY_ID[
                    state_id
                ]
            )

            display = (
                f"{name} "
                f"({state_abbreviation} "
                f"{municipality_code})"
            )

        display_names[
            municipality_id
        ] = display

    duplicate_displays = [
        display
        for display, count
        in Counter(
            display_names.values()
        ).items()
        if count > 1
    ]

    if duplicate_displays:
        raise ValueError(
            "Generated municipality display names are not unique:\n"
            + "\n".join(
                f"  {display}"
                for display
                in sorted(
                    duplicate_displays
                )
            )
        )

    return display_names


def render_states() -> str:
    """Render the state ID-to-name dictionary."""
    lines = [
        "export const MEXICO_STATES_BY_ID = {",
    ]

    for (
        state_id,
        name,
    ) in MEXICO_STATE_NAMES_BY_ID.items():
        lines.append(
            f"  {to_typescript_string(state_id)}: "
            f"{to_typescript_string(name)},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_municipalities(
    municipalities: list[dict[str, str]],
    display_names: dict[str, str],
) -> str:
    """Render the municipality hierarchy dictionary."""
    lines = [
        "export const MEXICO_MUNICIPALITIES_BY_ID = {",
    ]

    for municipality in municipalities:
        municipality_id = municipality[
            "municipality_id"
        ]
        name = municipality["name"]
        state_id = municipality["state_id"]
        display = display_names[
            municipality_id
        ]

        properties = [
            f"name: {to_typescript_string(name)}",
            f"stateId: {to_typescript_string(state_id)}",
        ]

        if display != name:
            properties.append(
                f"display: {to_typescript_string(display)}"
            )

        lines.append(
            f"  {to_typescript_string(municipality_id)}: "
            f"{{ {', '.join(properties)} }},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def create_source(
    municipalities: list[dict[str, str]],
    display_names: dict[str, str],
) -> str:
    """Create the generated TypeScript admin data module."""
    states = render_states()
    municipality_data = render_municipalities(
        municipalities,
        display_names,
    )

    return f'''/**
 * Generated from Mexico's processed municipality GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/mexico/generate/admin-quiz-data.py
 */

{states}{municipality_data}'''


def main() -> None:
    """Generate Mexico's administrative quiz data."""
    print(
        "Generating Mexico administrative quiz data...\n"
    )

    features = load_features()

    municipalities = extract_municipalities(
        features
    )

    display_names = create_display_names(
        municipalities
    )

    name_counts = Counter(
        municipality["name"]
        for municipality in municipalities
    )

    name_state_counts = Counter(
        (
            municipality["name"],
            municipality["state_id"],
        )
        for municipality in municipalities
    )

    duplicated_names = {
        name
        for name, count
        in name_counts.items()
        if count > 1
    }

    municipalities_with_duplicate_names = sum(
        count
        for name, count
        in name_counts.items()
        if name in duplicated_names
    )

    same_state_duplicate_groups = {
        pair
        for pair, count
        in name_state_counts.items()
        if count > 1
    }

    municipalities_needing_local_code = sum(
        count
        for pair, count
        in name_state_counts.items()
        if pair in same_state_duplicate_groups
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            municipalities,
            display_names,
        ),
        encoding="utf-8",
    )

    print(
        f"States/entities:       "
        f"{len(MEXICO_STATE_NAMES_BY_ID):,}"
    )
    print(
        f"Municipalities:        "
        f"{len(municipalities):,}"
    )
    print(
        f"Unique names:          "
        f"{len(name_counts):,}"
    )
    print(
        f"Duplicated names:      "
        f"{len(duplicated_names):,} "
        f"({municipalities_with_duplicate_names:,} municipalities)"
    )
    print(
        f"Local-code displays:   "
        f"{municipalities_needing_local_code:,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()