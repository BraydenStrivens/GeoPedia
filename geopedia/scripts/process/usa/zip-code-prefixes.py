"""
Generates GeoPedia ZIP-prefix maps from the 2020 Census ZCTA5 shapefile.

The Census source contains one polygon per 5-digit ZIP Code Tabulation Area
(ZCTA). This script:

1. Reads each 5-digit ZCTA.
2. Determines which US state(s) its geometry belongs to.
3. Groups ZCTAs by their first 1, 2, and 3 ZIP digits.
4. Dissolves polygons belonging to each prefix.
5. Combines the state memberships of those polygons.
6. Simplifies the final geometry.
7. Writes optimized GeoJSON files for GeoPedia.

Example:

    56258
      ↓
    1 digit: "5"
    2 digit: "56"
    3 digit: "562"

All ZIP values remain strings so leading zeroes are preserved.
"""

import json
from collections import defaultdict
from pathlib import Path

import shapefile
from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FILE = Path(
    "data/raw/us-post-codes-5-digit/tl_2020_us_zcta520.shp"
)

STATE_FILE = Path(
    "data/raw/cb_2025_us_state_500k/cb_2025_us_state_500k.shp"
)

OUTPUT_DIRECTORY = Path(
    "public/data"
)

SIMPLIFY_TOLERANCES = {
    1: 0.02,
    2: 0.015,
    3: 0.01,
}

# Prevents tiny border-touching/intersection artifacts from assigning
# a ZCTA to an additional state.
MIN_STATE_OVERLAP_RATIO = 0.01


# ---------------------------------------------------------------------------
# State data
# ---------------------------------------------------------------------------


def read_states():
    """
    Reads Census state and state-equivalent polygons.

    The STUSPS field provides the two-letter abbreviation used in the
    generated ZIP-prefix metadata.
    """
    reader = shapefile.Reader(
        str(STATE_FILE)
    )

    field_names = [
        field[0]
        for field in reader.fields[1:]
    ]

    abbreviation_index = (
        field_names.index("STUSPS")
    )

    states = []

    for shape_record in reader.iterShapeRecords():
        abbreviation = str(
            shape_record.record[
                abbreviation_index
            ]
        )

        geometry = shape(
            shape_record.shape.__geo_interface__
        )

        states.append(
            {
                "abbreviation": abbreviation,
                "geometry": geometry,
            }
        )

    return states\
        


def build_state_spatial_index(states):
    """
    Builds a spatial index so each ZCTA only needs to be checked against
    nearby states rather than all states.
    """
    geometries = [
        state["geometry"]
        for state in states
    ]

    tree = STRtree(geometries)

    return tree, geometries


def find_zcta_states(
    zcta_geometry,
    states,
    state_tree,
):
    """
    Returns all state abbreviations meaningfully overlapped by a ZCTA.

    A small minimum overlap ratio prevents polygons that merely touch a
    state boundary from being counted as belonging to both states.
    """
    matching_states = set()

    zcta_area = zcta_geometry.area

    if zcta_area == 0:
        return matching_states

    candidate_indexes = state_tree.query(
        zcta_geometry
    )

    for index in candidate_indexes:
        state = states[index]
        state_geometry = state["geometry"]

        intersection = (
            zcta_geometry.intersection(
                state_geometry
            )
        )

        if intersection.is_empty:
            continue

        overlap_ratio = (
            intersection.area
            / zcta_area
        )

        if (
            overlap_ratio
            >= MIN_STATE_OVERLAP_RATIO
        ):
            matching_states.add(
                state["abbreviation"]
            )

    return matching_states


# ---------------------------------------------------------------------------
# ZCTA reading
# ---------------------------------------------------------------------------


def read_zcta_features(
    states,
    state_tree,
):
    """
    Reads ZCTA values and geometries and attaches state membership to
    each ZCTA.
    """
    reader = shapefile.Reader(
        str(INPUT_FILE)
    )

    field_names = [
        field[0]
        for field in reader.fields[1:]
    ]

    zcta_index = field_names.index(
        "ZCTA5CE20"
    )

    features = []

    total = len(reader)

    for index, shape_record in enumerate(
        reader.iterShapeRecords(),
        start=1,
    ):
        if index % 1000 == 0:
            print(
                f"  State matching: "
                f"{index}/{total}"
            )

        zcta = str(
            shape_record.record[
                zcta_index
            ]
        ).zfill(5)

        geometry = shape(
            shape_record.shape.__geo_interface__
        )

        state_abbreviations = (
            find_zcta_states(
                geometry,
                states,
                state_tree,
            )
        )

        features.append(
            {
                "zcta": zcta,
                "geometry": geometry,
                "states": state_abbreviations,
            }
        )

    return features


# ---------------------------------------------------------------------------
# Prefix processing
# ---------------------------------------------------------------------------


def group_by_prefix(
    features,
    prefix_length,
):
    """
    Groups ZCTA geometries and state memberships by ZIP prefix.
    """
    groups = defaultdict(
        lambda: {
            "geometries": [],
            "states": set(),
        }
    )

    for feature in features:
        prefix = feature["zcta"][
            :prefix_length
        ]

        groups[prefix][
            "geometries"
        ].append(
            feature["geometry"]
        )

        groups[prefix][
            "states"
        ].update(
            feature["states"]
        )

    return groups


def build_geojson(
    groups,
    prefix_length,
):
    """
    Dissolves and simplifies each ZIP-prefix region while preserving
    the combined state memberships of its source ZCTAs.
    """
    tolerance = (
        SIMPLIFY_TOLERANCES[
            prefix_length
        ]
    )

    output_features = []

    total_groups = len(groups)

    for index, (
        prefix,
        group,
    ) in enumerate(
        sorted(groups.items()),
        start=1,
    ):
        print(
            f"  [{index}/{total_groups}] "
            f"Processing {prefix}"
        )

        dissolved = unary_union(
            group["geometries"]
        )

        simplified = (
            dissolved.simplify(
                tolerance,
                preserve_topology=True,
            )
        )

        output_features.append(
            {
                "type": "Feature",
                "id": prefix,
                "properties": {
                    "id": prefix,
                    "zip": prefix,
                    "states": sorted(
                        group["states"]
                    ),
                },
                "geometry": mapping(
                    simplified
                ),
            }
        )

    return {
        "type": "FeatureCollection",
        "features": output_features,
    }


def write_geojson(
    geojson,
    prefix_length,
):
    """
    Writes one optimized GeoJSON file for the requested prefix level.
    """
    output_file = (
        OUTPUT_DIRECTORY
        / f"us-zip-{prefix_length}.geojson"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_mb = (
        output_file.stat().st_size
        / 1024
        / 1024
    )

    print()
    print(
        f"Wrote {output_file}"
    )

    print(
        f"Features: "
        f"{len(geojson['features'])}"
    )

    print(
        f"Size: {size_mb:.2f} MB"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    if not INPUT_FILE.exists():
        print(
            f"ERROR: ZCTA file not found: "
            f"{INPUT_FILE}"
        )
        return

    if not STATE_FILE.exists():
        print(
            f"ERROR: State GeoJSON not found: "
            f"{STATE_FILE}"
        )
        return

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Reading state boundaries...")

    states = read_states()

    print(
        f"Loaded {len(states)} states."
    )

    state_tree, _ = (
        build_state_spatial_index(
            states
        )
    )

    print()
    print(
        "Reading ZCTAs and assigning states..."
    )

    features = read_zcta_features(
        states,
        state_tree,
    )

    print()
    print(
        f"Loaded {len(features)} ZCTAs."
    )

    for prefix_length in (
        1,
        2,
        3,
    ):
        print()
        print(
            f"Generating "
            f"{prefix_length}-digit "
            f"ZIP map..."
        )

        groups = group_by_prefix(
            features,
            prefix_length,
        )

        print(
            f"Unique prefixes: "
            f"{len(groups)}"
        )

        geojson = build_geojson(
            groups,
            prefix_length,
        )

        write_geojson(
            geojson,
            prefix_length,
        )


if __name__ == "__main__":
    main()