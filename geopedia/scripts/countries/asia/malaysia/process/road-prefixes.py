"""
Create Malaysia's state-road-prefix GeoJSON.

This script derives the geography used by GeoPedia's Malaysian state road
prefix quiz from the finalized public states GeoJSON.

Malaysia's three federal territories require special handling because the
quiz represents state road-prefix geography rather than the administrative
state/federal-territory map:

- Kuala Lumpur is dissolved into Selangor.
- Putrajaya is dissolved into Selangor.
- Labuan is removed because it has no state road prefix.

The resulting dataset contains Malaysia's 13 states, with each feature
assigned its state road prefix.

Input
-----
public/data/countries/malaysia/geojson/states.geojson

Output
------
public/data/countries/malaysia/geojson/road-prefixes.geojson

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/process/road-prefixes.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "malaysia"
    / "geojson"
)

STATES_PATH = GEOJSON_DIR / "states.geojson"
OUTPUT_PATH = GEOJSON_DIR / "road-prefixes.geojson"


# ---------------------------------------------------------------------------
# Road-prefix data
# ---------------------------------------------------------------------------

ROAD_PREFIXES: dict[str, str] = {
    "Perak": "A",
    "Selangor": "B",
    "Pahang": "C",
    "Kelantan": "D",
    "Johor": "J",
    "Kedah": "K",
    "Malacca": "M",
    "Negeri Sembilan": "N",
    "Penang": "P",
    "Sarawak": "Q",
    "Perlis": "R",
    "Sabah": "SA",
    "Terengganu": "T",
}

FEDERAL_TERRITORIES_TO_MERGE: dict[str, str] = {
    "Kuala Lumpur": "Selangor",
    "Putrajaya": "Selangor",
}

FEDERAL_TERRITORIES_TO_REMOVE = {
    "Labuan",
}

EXPECTED_SOURCE_FEATURE_COUNT = 16
EXPECTED_OUTPUT_FEATURE_COUNT = 13


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_states() -> gpd.GeoDataFrame:
    """Load and validate Malaysia's finalized public states GeoJSON."""

    if not STATES_PATH.exists():
        raise FileNotFoundError(
            f"Missing Malaysia states GeoJSON: {STATES_PATH}"
        )

    states = gpd.read_file(
        STATES_PATH
    )

    expected_properties = {
        "state_id",
        "state",
        "geometry",
    }

    missing_properties = (
        expected_properties
        - set(states.columns)
    )

    if missing_properties:
        raise ValueError(
            "Malaysia states GeoJSON is missing required properties: "
            + ", ".join(
                sorted(missing_properties)
            )
        )

    if len(states) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_FEATURE_COUNT} state/federal-territory "
            f"features but found {len(states)}."
        )

    if states["state"].isna().any():
        raise ValueError(
            "Malaysia states GeoJSON contains missing state names."
        )

    if states["state"].duplicated().any():
        raise ValueError(
            "Malaysia states GeoJSON contains duplicate state names."
        )

    if states.geometry.isna().any():
        raise ValueError(
            "Malaysia states GeoJSON contains missing geometries."
        )

    if states.geometry.is_empty.any():
        raise ValueError(
            "Malaysia states GeoJSON contains empty geometries."
        )

    invalid_count = int(
        (~states.geometry.is_valid).sum()
    )

    if invalid_count:
        raise ValueError(
            f"Malaysia states GeoJSON contains {invalid_count:,} invalid "
            f"geometries."
        )

    return states


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def create_road_prefix_geography(
    states: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Convert state/federal-territory geography into road-prefix geography.

    Kuala Lumpur and Putrajaya are assigned to Selangor before dissolving.
    Labuan is removed entirely.
    """

    source_names = set(
        states["state"]
    )

    required_names = (
        set(ROAD_PREFIXES)
        | set(FEDERAL_TERRITORIES_TO_MERGE)
        | FEDERAL_TERRITORIES_TO_REMOVE
    )

    missing_names = (
        required_names
        - source_names
    )

    if missing_names:
        raise ValueError(
            "Required states/federal territories are missing from the "
            "source GeoJSON: "
            + ", ".join(
                sorted(missing_names)
            )
        )

    road_prefixes = states.copy()

    # Labuan has no state road prefix and is not represented in this quiz.
    road_prefixes = road_prefixes[
        ~road_prefixes["state"].isin(
            FEDERAL_TERRITORIES_TO_REMOVE
        )
    ].copy()

    # Assign Kuala Lumpur and Putrajaya to Selangor so their polygons become
    # part of Selangor when the geometries are dissolved.
    road_prefixes["road_state"] = (
        road_prefixes["state"]
        .replace(
            FEDERAL_TERRITORIES_TO_MERGE
        )
    )

    # Dissolve the reassigned federal-territory polygons into their state.
    road_prefixes = (
        road_prefixes[
            [
                "road_state",
                "geometry",
            ]
        ]
        .dissolve(
            by="road_state",
            as_index=False,
        )
    )

    road_prefixes["road_prefix"] = (
        road_prefixes["road_state"]
        .map(
            ROAD_PREFIXES
        )
    )

    if road_prefixes["road_prefix"].isna().any():
        missing_prefix_states = (
            road_prefixes.loc[
                road_prefixes["road_prefix"].isna(),
                "road_state",
            ]
            .tolist()
        )

        raise ValueError(
            "Missing road prefixes for: "
            + ", ".join(
                missing_prefix_states
            )
        )

    # Prefixes are unique across the 13 resulting state features, so the
    # prefix itself provides a stable feature identity for this map.
    road_prefixes["road_prefix_id"] = (
        road_prefixes["road_prefix"]
    )

    road_prefixes = road_prefixes.rename(
        columns={
            "road_state": "state",
        }
    )

    road_prefixes = road_prefixes[
        [
            "road_prefix_id",
            "road_prefix",
            "state",
            "geometry",
        ]
    ]

    road_prefixes = road_prefixes.sort_values(
        by="road_prefix",
        key=lambda series: series.str.casefold(),
    ).reset_index(
        drop=True
    )

    return road_prefixes


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_output(
    road_prefixes: gpd.GeoDataFrame,
) -> None:
    """Validate the completed state-road-prefix geography."""

    if len(road_prefixes) != EXPECTED_OUTPUT_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_OUTPUT_FEATURE_COUNT} road-prefix features "
            f"but found {len(road_prefixes)}."
        )

    if road_prefixes["state"].duplicated().any():
        raise ValueError(
            "Road-prefix GeoJSON contains duplicate state names."
        )

    if road_prefixes["road_prefix"].duplicated().any():
        raise ValueError(
            "Road-prefix GeoJSON contains duplicate road prefixes."
        )

    if road_prefixes["road_prefix_id"].duplicated().any():
        raise ValueError(
            "Road-prefix GeoJSON contains duplicate road-prefix IDs."
        )

    actual_states = set(
        road_prefixes["state"]
    )

    expected_states = set(
        ROAD_PREFIXES
    )

    if actual_states != expected_states:
        missing = (
            expected_states
            - actual_states
        )

        unexpected = (
            actual_states
            - expected_states
        )

        raise ValueError(
            "Road-prefix state set does not match the expected 13 states. "
            f"Missing: {sorted(missing)}; "
            f"unexpected: {sorted(unexpected)}."
        )

    actual_mapping = dict(
        zip(
            road_prefixes["state"],
            road_prefixes["road_prefix"],
        )
    )

    if actual_mapping != ROAD_PREFIXES:
        raise ValueError(
            "Generated state-to-road-prefix mapping does not match the "
            "configured mapping."
        )

    if road_prefixes.geometry.isna().any():
        raise ValueError(
            "Road-prefix GeoJSON contains missing geometries."
        )

    if road_prefixes.geometry.is_empty.any():
        raise ValueError(
            "Road-prefix GeoJSON contains empty geometries."
        )

    invalid_count = int(
        (~road_prefixes.geometry.is_valid).sum()
    )

    if invalid_count:
        raise ValueError(
            f"Road-prefix GeoJSON contains {invalid_count:,} invalid "
            f"geometries."
        )


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def write_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """Write compact UTF-8 GeoJSON."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    geojson: dict[str, Any] = json.loads(
        frame.to_json(
            drop_id=True,
        )
    )

    path.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_report(
    road_prefixes: gpd.GeoDataFrame,
) -> None:
    """Print the generated state-to-road-prefix mapping."""

    print()
    print("State road prefixes")
    print("-------------------")

    for _, row in road_prefixes.sort_values(
        "state"
    ).iterrows():
        print(
            f"  {row['state']}: {row['road_prefix']}"
        )

    print()
    print(
        f"Features: {len(road_prefixes):,}"
    )

    print(
        "Invalid geometries: "
        f"{int((~road_prefixes.geometry.is_valid).sum()):,}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate Malaysia's state-road-prefix geography."""

    print()
    print(
        "Processing Malaysia state road-prefix geography..."
    )

    states = load_states()

    print()
    print(
        f"Source state/federal-territory features: {len(states):,}"
    )
    print(
        "Removing: Labuan"
    )
    print(
        "Dissolving into Selangor: Kuala Lumpur, Putrajaya"
    )

    road_prefixes = create_road_prefix_geography(
        states
    )

    validate_output(
        road_prefixes
    )

    write_geojson(
        road_prefixes,
        OUTPUT_PATH,
    )

    print_report(
        road_prefixes
    )

    print()
    print(
        "Output: "
        + str(
            OUTPUT_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print(
        "Malaysia state road-prefix processing complete."
    )


if __name__ == "__main__":
    main()