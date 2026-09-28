"""
Generate the editable Taiwan township-to-area-code assignment file.

Source
------
data/intermediate/countries/taiwan/townships.geojson

Output
------
data/intermediate/countries/taiwan/area-codes/
    township-area-codes.json

Purpose
-------
The Plonk It Taiwan telephone map is GeoPedia's geographic reference for
full landline area codes. GeoPedia's MOI township/district polygons provide
the geographic construction units.

This script creates an editable assignment file containing every one of
Taiwan's 368 township/district features. Area-code assignments are initially
empty and are populated by comparing the townships against the georeferenced
Plonk It reference map.

A township may have multiple valid full area-code answers. Therefore
area_codes is ALWAYS an array, including for single-answer townships:

    "area_codes": ["037"]

or:

    "area_codes": ["035", "036"]

The assignment file is an intermediate source of truth. A later processing
script will use it together with the township geometry to:

1. Create unique full-area-code answer-set regions.
2. Derive two-significant-digit prefixes.
3. Derive one-significant-digit prefixes.
4. Dissolve identical answer sets into Polygon/MultiPolygon features.

Run from the GeoPedia project root:

    python scripts/countries/taiwan/generate/area-code-assignments.py
"""

from __future__ import annotations

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]

TOWNSHIPS_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "townships.geojson"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "township-area-codes.json"
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
        "Loading Taiwan townships..."
    )

    township_data = load_geojson(
        TOWNSHIPS_PATH
    )

    features = township_data[
        "features"
    ]

    if len(features) != 368:
        raise ValueError(
            f"Expected 368 Taiwan townships, "
            f"found {len(features)}."
        )

    assignments: list[dict] = []

    seen_ids: set[str] = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties.get(
            "township_id"
        )

        if not township_id:
            raise ValueError(
                "Township feature is missing township_id."
            )

        if township_id in seen_ids:
            raise ValueError(
                f"Duplicate township_id: {township_id}"
            )

        seen_ids.add(
            township_id
        )

        assignments.append(
            {
                "township_id": township_id,
                "township": properties.get(
                    "township"
                ),
                "township_native": properties.get(
                    "township_native"
                ),
                "county_id": properties.get(
                    "county_id"
                ),
                "county": properties.get(
                    "county"
                ),
                "area_codes": [],
            }
        )

    # Keep counties and their townships together while remaining
    # deterministic across regeneration.
    assignments.sort(
        key=lambda item: (
            item["county"] or "",
            item["township"] or "",
            item["township_id"],
        )
    )

    output = {
        "source": (
            "Plonk It Taiwan telephone area-code map "
            "+ MOI township geometry"
        ),
        "notes": [
            (
                "area_codes is always an array, including "
                "single-answer townships."
            ),
            (
                "Blue Plonk It area codes are retained as "
                "additional valid answers."
            ),
            (
                "08368 is retained as a geographic quiz answer "
                "despite the reference map marking its current "
                "region as no coverage."
            ),
        ],
        "assignments": assignments,
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
            indent=2,
        )

        file.write(
            "\n"
        )

    print()
    print(
        "Taiwan township area-code assignment skeleton generated."
    )
    print()
    print(
        f"Townships: {len(assignments)}"
    )
    print(
        f"Assigned:  0"
    )
    print(
        f"Unassigned: {len(assignments)}"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()