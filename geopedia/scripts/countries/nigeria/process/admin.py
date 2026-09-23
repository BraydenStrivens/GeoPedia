"""
Process Nigeria's raw geoBoundaries administrative boundaries into GeoPedia's
canonical intermediate administrative GeoJSON files.

The raw ADM1 dataset contains Nigeria's 36 states plus the Abuja Federal
Capital Territory. The ADM2 dataset contains the 774 Local Government Areas
but does not identify each LGA's parent state, so that relationship is derived
spatially.

Inputs:
    data/raw/countries/nigeria/geoBoundaries-NGA-ADM1.geojson
    data/raw/countries/nigeria/geoBoundaries-NGA-ADM2.geojson

Outputs:
    data/intermediate/countries/nigeria/admin/states.geojson
    data/intermediate/countries/nigeria/admin/local-government-areas.geojson
"""

import json
from pathlib import Path

from shapely.geometry import shape


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "nigeria"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "nigeria"
    / "admin"
)

STATES_INPUT = RAW_DIR / "geoBoundaries-NGA-ADM1.geojson"
LGAS_INPUT = RAW_DIR / "geoBoundaries-NGA-ADM2.geojson"

STATES_OUTPUT = OUTPUT_DIR / "states.geojson"
LGAS_OUTPUT = OUTPUT_DIR / "local-government-areas.geojson"

EXPECTED_STATE_COUNT = 37
EXPECTED_LGA_COUNT = 774


def load_geojson(path: Path) -> dict:
    """Load a GeoJSON file and validate that it is a FeatureCollection."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    return data


def write_geojson(path: Path, features: list[dict]) -> None:
    """Write features as a compact GeoJSON FeatureCollection."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def process_states(raw_states: dict) -> list[dict]:
    """Convert raw ADM1 features into canonical GeoPedia state features."""
    features = []
    state_ids = set()

    for feature in raw_states["features"]:
        properties = feature.get("properties", {})

        state_id = properties.get("shapeISO", "").strip()
        state = properties.get("shapeName", "").strip()

        if not state_id:
            raise ValueError(
                f"State is missing shapeISO: {state!r}"
            )

        if not state:
            raise ValueError(
                f"State {state_id!r} is missing shapeName."
            )

        if state_id in state_ids:
            raise ValueError(
                f"Duplicate state ID: {state_id}"
            )

        state_ids.add(state_id)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "state_id": state_id,
                    "state": state,
                },
                "geometry": feature["geometry"],
            }
        )

    if len(features) != EXPECTED_STATE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_STATE_COUNT} states/FCT, "
            f"found {len(features)}."
        )

    return features


def build_state_lookup(
    state_features: list[dict],
) -> list[dict]:
    """
    Build the spatial lookup used to assign each LGA to its parent state.

    Prepared state geometries are retained alongside their canonical
    properties so each LGA only needs to derive its representative point once.
    """
    lookup = []

    for feature in state_features:
        geometry = shape(feature["geometry"])

        if geometry.is_empty:
            raise ValueError(
                "Empty state geometry for "
                f"{feature['properties']['state']!r}."
            )

        lookup.append(
            {
                "state_id": feature["properties"]["state_id"],
                "state": feature["properties"]["state"],
                "geometry": geometry,
            }
        )

    return lookup


def find_parent_state(
    lga_geometry,
    state_lookup: list[dict],
) -> dict:
    """
    Find an LGA's parent state using a point guaranteed to lie inside the LGA.

    The representative point avoids centroid problems for irregular polygons.
    Exactly one state must cover the point.
    """
    point = lga_geometry.representative_point()

    matches = [
        state
        for state in state_lookup
        if state["geometry"].covers(point)
    ]

    if len(matches) != 1:
        names = [
            state["state"]
            for state in matches
        ]

        raise ValueError(
            "Expected exactly one parent state, "
            f"found {len(matches)}: {names}"
        )

    return matches[0]


def process_lgas(
    raw_lgas: dict,
    state_lookup: list[dict],
) -> list[dict]:
    """
    Convert raw ADM2 features into canonical LGA features and derive each
    feature's parent state spatially.
    """
    features = []
    lga_ids = set()

    for feature in raw_lgas["features"]:
        properties = feature.get("properties", {})

        lga_id = properties.get("shapeID", "").strip()
        lga = properties.get("shapeName", "").strip()

        if not lga_id:
            raise ValueError(
                f"LGA is missing shapeID: {lga!r}"
            )

        if not lga:
            raise ValueError(
                f"LGA {lga_id!r} is missing shapeName."
            )

        if lga_id in lga_ids:
            raise ValueError(
                f"Duplicate LGA ID: {lga_id}"
            )

        lga_ids.add(lga_id)

        lga_geometry = shape(feature["geometry"])

        if lga_geometry.is_empty:
            raise ValueError(
                f"Empty LGA geometry for {lga!r}."
            )

        parent = find_parent_state(
            lga_geometry,
            state_lookup,
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "lga_id": lga_id,
                    "lga": lga,
                    "state_id": parent["state_id"],
                    "state": parent["state"],
                },
                "geometry": feature["geometry"],
            }
        )

    if len(features) != EXPECTED_LGA_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_LGA_COUNT} LGAs, "
            f"found {len(features)}."
        )

    return features


def validate_parent_counts(
    state_features: list[dict],
    lga_features: list[dict],
) -> None:
    """Ensure every state/FCT receives at least one LGA."""
    state_ids = {
        feature["properties"]["state_id"]
        for feature in state_features
    }

    represented_state_ids = {
        feature["properties"]["state_id"]
        for feature in lga_features
    }

    missing = state_ids - represented_state_ids

    if missing:
        raise ValueError(
            "States/FCT without any assigned LGAs: "
            f"{sorted(missing)}"
        )


def main() -> None:
    """Process Nigeria's ADM1 and ADM2 administrative datasets."""
    print("Processing Nigeria administrative boundaries...")
    print()

    raw_states = load_geojson(STATES_INPUT)
    raw_lgas = load_geojson(LGAS_INPUT)

    print(
        f"Raw states/FCT: {len(raw_states['features'])}"
    )
    print(
        f"Raw LGAs:       {len(raw_lgas['features'])}"
    )
    print()

    states = process_states(raw_states)

    state_lookup = build_state_lookup(states)

    lgas = process_lgas(
        raw_lgas,
        state_lookup,
    )

    validate_parent_counts(
        states,
        lgas,
    )

    write_geojson(
        STATES_OUTPUT,
        states,
    )

    write_geojson(
        LGAS_OUTPUT,
        lgas,
    )

    print("Nigeria administrative processing complete.")
    print(f"  States/FCT: {len(states)}")
    print(f"  LGAs:       {len(lgas)}")
    print()
    print(f"States: {STATES_OUTPUT}")
    print(f"LGAs:   {LGAS_OUTPUT}")


if __name__ == "__main__":
    main()