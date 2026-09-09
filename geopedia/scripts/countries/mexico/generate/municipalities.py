"""
Generate the GeoPedia Mexico Municipalities quiz configuration.

Input
-----
    public/data/countries/mexico/geojson/municipalities.geojson

Output
------
    src/quiz/quizzes/mexico/mexicoMunicipalitiesQuiz.ts

The generated quiz contains all 2,478 Mexican municipalities and groups them
by their parent INEGI state/entity ID.

Municipality names are disambiguated only when necessary:

    Aguascalientes
        -> Aguascalientes

    Tuxpan in Jalisco
        -> Tuxpan (Jal.)

    San Juan Mixtepec 20208 in Oaxaca
        -> San Juan Mixtepec (Oax. 208)

A state abbreviation is appended when a municipality name occurs more than
once nationwide. If the same municipality name occurs multiple times within
the same state, the three-digit municipality code is appended as well.

This keeps the majority of quiz prompts short while ensuring every generated
display name is unique.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

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
    / "mexico"
    / "mexicoMunicipalitiesQuiz.ts"
)


# ---------------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------------

EXPECTED_MUNICIPALITY_COUNT = 2478
EXPECTED_STATE_COUNT = 32

EXPECTED_STATE_IDS = {
    f"{state_id:02d}"
    for state_id in range(1, EXPECTED_STATE_COUNT + 1)
}


# ---------------------------------------------------------------------------
# State metadata
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def escape_typescript_string(value: str) -> str:
    """Escape text for use inside a double-quoted TypeScript string."""

    return (
        value
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def load_features() -> list[dict[str, Any]]:
    """Load and validate the processed Mexico municipality GeoJSON."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Missing processed Mexico municipality GeoJSON:\n"
            f"  {INPUT_PATH}\n\n"
            "Run the municipality processor first."
        )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
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
    """Extract and validate the fields needed by the quiz generator."""

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
        municipality_id = properties.get("municipality_id")
        name = properties.get("name")
        state_id = properties.get("state_id")

        if not isinstance(municipality_id, str) or not municipality_id:
            raise ValueError(
                f"Feature {feature_id!r} has an invalid municipality_id."
            )

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Municipality {municipality_id} has an invalid name."
            )

        if not isinstance(state_id, str) or not state_id:
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

        if not municipality_id.startswith(state_id):
            raise ValueError(
                f"Municipality {municipality_id} does not belong to "
                f"state ID {state_id}."
            )

        if state_id not in MEXICO_STATE_NAMES_BY_ID:
            raise ValueError(
                f"Municipality {municipality_id} uses unknown "
                f"state ID {state_id}."
            )

        if state_id not in MEXICO_STATE_ABBREVIATIONS_BY_ID:
            raise ValueError(
                f"Municipality {municipality_id} has no configured "
                f"state abbreviation for {state_id}."
            )

        if municipality_id in municipality_ids:
            raise ValueError(
                f"Duplicate municipality ID {municipality_id}."
            )

        municipality_ids.add(municipality_id)
        state_ids.add(state_id)

        municipalities.append(
            {
                "municipality_id": municipality_id,
                "municipality_code": municipality_id[-3:],
                "name": name,
                "state_id": state_id,
            }
        )

    if state_ids != EXPECTED_STATE_IDS:
        missing = sorted(EXPECTED_STATE_IDS - state_ids)
        unexpected = sorted(state_ids - EXPECTED_STATE_IDS)

        raise ValueError(
            "Unexpected set of state IDs in municipality data.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    municipalities.sort(
        key=lambda municipality: municipality["municipality_id"]
    )

    return municipalities


def create_display_names(
    municipalities: list[dict[str, str]],
) -> dict[str, str]:
    """
    Create unique quiz display names with minimal disambiguation.

    Nationwide-unique names remain unchanged.

    If a name occurs in more than one state, the state abbreviation is
    appended. If the same name occurs more than once within a single state,
    the municipality's three-digit local code is also appended.
    """

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
        municipality_id = municipality["municipality_id"]
        municipality_code = municipality["municipality_code"]
        name = municipality["name"]
        state_id = municipality["state_id"]

        if name_counts[name] == 1:
            display = name

        elif name_state_counts[(name, state_id)] == 1:
            state_abbreviation = (
                MEXICO_STATE_ABBREVIATIONS_BY_ID[state_id]
            )

            display = f"{name} ({state_abbreviation})"

        else:
            state_abbreviation = (
                MEXICO_STATE_ABBREVIATIONS_BY_ID[state_id]
            )

            display = (
                f"{name} "
                f"({state_abbreviation} {municipality_code})"
            )

        display_names[municipality_id] = display

    duplicate_displays = [
        display
        for display, count in Counter(display_names.values()).items()
        if count > 1
    ]

    if duplicate_displays:
        raise ValueError(
            "Generated municipality display names are not unique:\n"
            + "\n".join(
                f"  {display}"
                for display in sorted(duplicate_displays)
            )
        )

    return display_names


def render_state_names_constant() -> str:
    """Render the TypeScript state-name lookup used by quiz grouping."""

    lines = [
        "/**",
        " * Full Mexican state/entity names keyed by their two-digit INEGI ID.",
        " */",
        "const MEXICO_STATE_NAMES_BY_ID = {",
    ]

    for state_id, name in MEXICO_STATE_NAMES_BY_ID.items():
        escaped_name = escape_typescript_string(name)

        lines.append(
            f'  "{state_id}": "{escaped_name}",'
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_questions_constant(
    municipalities: list[dict[str, str]],
    display_names: dict[str, str],
) -> str:
    """Render the generated TypeScript municipality question array."""

    lines = [
        "/**",
        " * All Mexican municipality questions keyed by INEGI municipality ID.",
        " * Duplicate municipality names are disambiguated with state",
        " * abbreviations and, when necessary, municipality codes.",
        " */",
        "const MEXICO_MUNICIPALITY_QUESTIONS = [",
    ]

    for municipality in municipalities:
        municipality_id = municipality["municipality_id"]
        display = escape_typescript_string(
            display_names[municipality_id]
        )

        lines.extend(
            [
                "  {",
                f'    answer: "{municipality_id}",',
                f'    display: "{display}",',
                "  },",
            ]
        )

    lines.extend(
        [
            "];",
            "",
        ]
    )

    return "\n".join(lines)


def render_quiz_file(
    municipalities: list[dict[str, str]],
    display_names: dict[str, str],
) -> str:
    """Render the complete TypeScript quiz configuration file."""

    state_names = render_state_names_constant()
    questions = render_questions_constant(
        municipalities,
        display_names,
    )

    return f'''import type {{ FeatureQuiz }} from "@/quiz/types/quiz";

{state_names}{questions}/**
 * Quiz configuration for all Mexican municipalities, grouped by state.
 */
export const mexicoMunicipalitiesQuiz: FeatureQuiz = {{
  id: "mexico-municipalities",
  name: "Mexico Municipalities",
  description: `Learn all ${{MEXICO_MUNICIPALITY_QUESTIONS.length}} municipalities of Mexico, with filters that let you practice municipalities from any desired state or combination of states.`,
  kind: "feature",
  mapId: "mexico-municipalities",
  answerProperty: "municipality_id",
  answerType: "single",
  baseMapLayers: {{
    subdivisionLabels: false,
  }},
  grouping: {{
    properties: [
      {{
        property: "state_id",
        label: "State",
        valueType: "string",
        valueLabels: MEXICO_STATE_NAMES_BY_ID,
      }},
    ],
  }},
  questions: MEXICO_MUNICIPALITY_QUESTIONS,
}};
'''


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate the Mexico Municipalities TypeScript quiz configuration."""

    print("Mexico municipalities quiz generator")
    print("-------------------------------------")
    print(f"Input: {INPUT_PATH}")
    print()

    features = load_features()
    municipalities = extract_municipalities(features)
    display_names = create_display_names(municipalities)

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
        for name, count in name_counts.items()
        if count > 1
    }

    municipalities_with_duplicate_names = sum(
        count
        for name, count in name_counts.items()
        if name in duplicated_names
    )

    same_state_duplicate_groups = {
        pair
        for pair, count in name_state_counts.items()
        if count > 1
    }

    municipalities_needing_local_code = sum(
        count
        for pair, count in name_state_counts.items()
        if pair in same_state_duplicate_groups
    )

    print(
        f"✓ Loaded exactly {len(municipalities):,} municipalities."
    )
    print("✓ Found all 32 Mexican states/entities.")
    print(
        f"✓ Found {len(name_counts):,} unique municipality names."
    )
    print(
        f"✓ Found {len(duplicated_names):,} duplicated names affecting "
        f"{municipalities_with_duplicate_names:,} municipalities."
    )
    print(
        f"✓ Found {len(same_state_duplicate_groups):,} same-state "
        f"duplicate-name groups affecting "
        f"{municipalities_needing_local_code:,} municipalities."
    )
    print("✓ Generated unique display names for every municipality.")

    output = render_quiz_file(
        municipalities,
        display_names,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print()
    print("✓ Saved generated quiz config to:")
    print(f"  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()