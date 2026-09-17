"""
Generates the administrative quiz data used by GeoPedia's Puerto Rico
municipality and barrio quizzes.

Inputs:
    public/data/countries/puerto-rico/geojson/municipalities.geojson
    public/data/countries/puerto-rico/geojson/barrios.geojson

Output:
    src/quiz/quizzes/countries/north-america/puerto-rico/data/admin.ts

Municipalities are keyed by Census county-equivalent GEOID.

Barrios are keyed by their stable barrio IDs and reference their parent
municipality. Duplicate barrio names are disambiguated by appending the
parent municipality name.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

GEOJSON_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
)

MUNICIPALITIES_PATH = (
    GEOJSON_DIRECTORY
    / "municipalities.geojson"
)

BARRIOS_PATH = (
    GEOJSON_DIRECTORY
    / "barrios.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "north-america"
    / "puerto-rico"
    / "data"
    / "admin.ts"
)


EXPECTED_MUNICIPALITY_COUNT = 78
EXPECTED_BARRIO_COUNT = 901


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

    return features


def read_municipalities(
    features: list[dict[str, Any]],
) -> dict[str, str]:
    """Load and validate Puerto Rico's municipalities."""
    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(features)}."
        )

    municipalities: dict[str, str] = {}

    for index, feature in enumerate(
        features,
        start=1,
    ):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Municipality feature {index} has invalid properties."
            )

        municipality_id = str(
            properties.get(
                "municipality_id",
                "",
            )
        ).strip()

        name = str(
            properties.get(
                "name",
                "",
            )
        ).strip()

        if not municipality_id:
            raise ValueError(
                f"Municipality feature {index} is missing municipality_id."
            )

        if not name:
            raise ValueError(
                f"Municipality {municipality_id} has a blank name."
            )

        if municipality_id in municipalities:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id}"
            )

        municipalities[
            municipality_id
        ] = name

    return dict(
        sorted(
            municipalities.items()
        )
    )


def read_barrios(
    features: list[dict[str, Any]],
    municipalities: dict[str, str],
) -> list[dict[str, str]]:
    """Load and validate Puerto Rico's barrio records."""
    if len(features) != EXPECTED_BARRIO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_BARRIO_COUNT} barrios, "
            f"found {len(features)}."
        )

    barrios: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for index, feature in enumerate(
        features,
        start=1,
    ):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Barrio feature {index} has invalid properties."
            )

        barrio_id = str(
            properties.get(
                "barrio_id",
                "",
            )
        ).strip()

        name = str(
            properties.get(
                "name",
                "",
            )
        ).strip()

        municipality_id = str(
            properties.get(
                "municipality_id",
                "",
            )
        ).strip()

        if not barrio_id:
            raise ValueError(
                f"Barrio feature {index} is missing barrio_id."
            )

        if barrio_id in seen_ids:
            raise ValueError(
                f"Duplicate barrio ID: {barrio_id}"
            )

        seen_ids.add(
            barrio_id
        )

        if not name:
            raise ValueError(
                f"Barrio {barrio_id} has a blank name."
            )

        if municipality_id not in municipalities:
            raise ValueError(
                f"Barrio {barrio_id} references unknown municipality "
                f"{municipality_id!r}."
            )

        barrios.append(
            {
                "id": barrio_id,
                "name": name,
                "municipality_id": municipality_id,
            }
        )

    return sorted(
        barrios,
        key=lambda barrio: barrio["id"],
    )


def build_barrios(
    records: list[dict[str, str]],
    municipalities: dict[str, str],
) -> dict[str, dict[str, str]]:
    """
    Build the generated barrio hierarchy.

    Barrio names repeated across Puerto Rico are disambiguated by their
    parent municipality.
    """
    name_counts = Counter(
        record["name"]
        for record in records
    )

    barrios: dict[str, dict[str, str]] = {}

    for record in records:
        name = record["name"]

        if name_counts[name] > 1:
            name = (
                f"{name} "
                f"({municipalities[record['municipality_id']]})"
            )

        barrios[
            record["id"]
        ] = {
            "name": name,
            "municipalityId": record["municipality_id"],
        }

    return barrios


def ts_string(
    value: str,
) -> str:
    """Return a safely encoded TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_municipalities(
    municipalities: dict[str, str],
) -> str:
    """Render Puerto Rico's municipality dictionary."""
    lines = [
        "export const PUERTO_RICO_MUNICIPALITIES_BY_ID = {",
    ]

    for municipality_id, name in municipalities.items():
        lines.append(
            f"  {ts_string(municipality_id)}: {ts_string(name)},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def render_barrios(
    barrios: dict[str, dict[str, str]],
) -> str:
    """Render Puerto Rico's barrio hierarchy."""
    lines = [
        "export const PUERTO_RICO_BARRIOS_BY_ID = {",
    ]

    for barrio_id, barrio in barrios.items():
        lines.append(
            f"  {ts_string(barrio_id)}: "
            "{ "
            f"name: {ts_string(barrio['name'])}, "
            f"municipalityId: {ts_string(barrio['municipalityId'])} "
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
    municipalities: dict[str, str],
    barrios: dict[str, dict[str, str]],
) -> str:
    """Create the generated TypeScript admin-data module."""
    return f'''/**
 * Generated from Puerto Rico's processed administrative GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/puerto-rico/generate/admin-quiz-data.py
 */

{render_municipalities(municipalities)}{render_barrios(barrios)}'''


def main() -> None:
    """Generate Puerto Rico's administrative quiz data."""
    print(
        "Generating Puerto Rico administrative quiz data...\n"
    )

    municipalities = read_municipalities(
        load_features(
            MUNICIPALITIES_PATH
        )
    )

    barrio_records = read_barrios(
        load_features(
            BARRIOS_PATH
        ),
        municipalities,
    )

    barrios = build_barrios(
        barrio_records,
        municipalities,
    )

    repeated_barrio_names = {
        name
        for name, count in Counter(
            record["name"]
            for record in barrio_records
        ).items()
        if count > 1
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            municipalities,
            barrios,
        ),
        encoding="utf-8",
    )

    print(
        f"Municipalities:             {len(municipalities):,}"
    )
    print(
        f"Barrios:                    {len(barrios):,}"
    )
    print(
        "Repeated barrio name groups: "
        f"{len(repeated_barrio_names):,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()