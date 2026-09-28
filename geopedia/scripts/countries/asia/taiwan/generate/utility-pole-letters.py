"""
Generate Taiwan utility-pole first-letter quiz geometry.

Source
------
data/raw/countries/taiwan/utility-pole-letters/hello-quiz-grid.geojson

Output
------
public/data/countries/taiwan/geojson/utility-pole-letters.geojson

Taiwan utility-pole plates begin with a letter identifying a large
geographic grid region.

The raw Hello Quiz GeoJSON already contains the utility-pole letter regions
clipped to the intended geographic boundaries. Each source feature stores
its letter in the PLATE_CODE property.

This script:

1. Loads the clipped Hello Quiz utility-pole region GeoJSON.
2. Validates that it contains exactly the expected 20 letter regions.
3. Validates each feature's geometry and PLATE_CODE.
4. Renames PLATE_CODE to GeoPedia's utility_pole_letter property.
5. Writes one Polygon or MultiPolygon feature per letter.

No additional clipping or boundary adjustment is performed because the
source geometry already contains the intended region boundaries.

The generated feature schema is:

    {
        "utility_pole_letter": "A"
    }

Because the quiz answer and player-facing label are identical, no separate
display property is needed in the question data.

Run from the GeoPedia project root:

    python scripts/countries/taiwan/generate/utility-pole-letters.py

Requires:
    shapely
"""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import mapping, shape


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]

GRID_PATH = (
    ROOT
    / "data"
    / "raw"
    / "countries"
    / "taiwan"
    / "utility-pole-letters"
    / "hello-quiz-grid.geojson"
)

OUTPUT_PATH = (
    ROOT
    / "public"
    / "data"
    / "countries"
    / "taiwan"
    / "geojson"
    / "utility-pole-letters.geojson"
)


# ---------------------------------------------------------------------------
# Expected data
# ---------------------------------------------------------------------------

EXPECTED_LETTERS = {
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "T", 
    "U",
    "V", 
    "W",
}

EXPECTED_LETTER_FEATURES = len(
    EXPECTED_LETTERS
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Missing source file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Loading Taiwan utility-pole regions..."
    )

    source_data = load_geojson(
        GRID_PATH
    )

    source_features = source_data[
        "features"
    ]

    # -----------------------------------------------------------------------
    # Validate and normalize features
    # -----------------------------------------------------------------------

    print(
        "Validating utility-pole regions..."
    )

    output_features: list[dict] = []
    found_letters: set[str] = set()

    for feature in source_features:
        properties = feature.get(
            "properties"
        )

        if not isinstance(properties, dict):
            raise ValueError(
                "Source feature is missing valid properties."
            )

        letter = properties.get(
            "PLATE_CODE"
        )

        if not isinstance(letter, str):
            raise ValueError(
                "Source feature is missing a valid "
                "PLATE_CODE."
            )

        letter = letter.strip().upper()

        if letter not in EXPECTED_LETTERS:
            raise ValueError(
                f"Unexpected utility-pole letter: "
                f"{letter!r}."
            )

        if letter in found_letters:
            raise ValueError(
                f"Duplicate utility-pole letter: "
                f"{letter}."
            )

        geometry_data = feature.get(
            "geometry"
        )

        if geometry_data is None:
            raise ValueError(
                f"Letter {letter} has no geometry."
            )

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            raise ValueError(
                f"Letter {letter} has empty geometry."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Letter {letter} has invalid geometry."
            )

        if geometry.geom_type not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError(
                f"Letter {letter} has unexpected geometry "
                f"type {geometry.geom_type!r}."
            )

        found_letters.add(
            letter
        )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "utility_pole_letter": letter,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    # -----------------------------------------------------------------------
    # Validate complete letter set
    # -----------------------------------------------------------------------

    if found_letters != EXPECTED_LETTERS:
        missing = (
            EXPECTED_LETTERS
            - found_letters
        )

        unexpected = (
            found_letters
            - EXPECTED_LETTERS
        )

        raise ValueError(
            "Utility-pole letter set does not match "
            "the expected letters.\n"
            f"Missing: {sorted(missing)}\n"
            f"Unexpected: {sorted(unexpected)}"
        )

    if len(output_features) != EXPECTED_LETTER_FEATURES:
        raise ValueError(
            f"Expected {EXPECTED_LETTER_FEATURES} output "
            f"features, found {len(output_features)}."
        )

    # Keep generated output deterministic.
    output_features.sort(
        key=lambda feature: feature[
            "properties"
        ]["utility_pole_letter"]
    )

    # -----------------------------------------------------------------------
    # Write output
    # -----------------------------------------------------------------------

    output = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print()
    print(
        "Taiwan utility-pole letter geometry generated."
    )
    print()
    print(
        f"Source features:    {len(source_features)}"
    )
    print(
        f"Letter features:    {len(output_features)}"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()