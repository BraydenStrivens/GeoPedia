"""
Experiment with local-evidence reconstruction of South African postal prefixes.

This script creates two experimental 1-digit postal-prefix maps from the
cleaned OSM postcode observations:

1. Nearest-observation classification
   Each sample location receives the prefix of its nearest postcode
   observation. This approximates the behavior of the current Voronoi-based
   reconstruction at the prefix level.

2. Local weighted-evidence classification
   Each sample location examines nearby postcode observations and sums their
   distance-decayed evidence by 1-digit prefix. Prefixes with several nearby
   observations can therefore outweigh a sparse competing prefix even when
   one of the sparse prefix's observations is slightly closer.

The experiment operates on a regular projected grid covering South Africa.
Only cells whose centers fall inside the country are classified. Classified
cells are converted to polygons and dissolved by prefix.

This is intentionally separate from the production postcode pipeline. Its
purpose is to compare reconstruction methods visually before changing
postcodes.py.

Inputs:

    data/intermediate/countries/south-africa/osm/
    postcode-points-cleaned.geojson

    data/intermediate/countries/south-africa/admin/
    provinces.geojson

Outputs:

    data/intermediate/countries/south-africa/postcodes/experiments/
    prefix-1-nearest.geojson

    data/intermediate/countries/south-africa/postcodes/experiments/
    prefix-1-weighted.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-africa/experiments/weighted-postcode-prefixes.py

Requirements:

    shapely
    pyproj
    scipy
    numpy
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import (
    box,
    mapping,
    shape,
)
from shapely.ops import (
    transform,
    unary_union,
)


OBSERVATIONS_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points-cleaned.geojson"
)

PROVINCES_PATH = Path(
    "data/intermediate/countries/south-africa/admin/"
    "provinces.geojson"
)

OUTPUT_DIR = Path(
    "data/intermediate/countries/south-africa/postcodes/"
    "experiments"
)

NEAREST_OUTPUT_PATH = (
    OUTPUT_DIR
    / "prefix-1-nearest.geojson"
)

WEIGHTED_OUTPUT_PATH = (
    OUTPUT_DIR
    / "prefix-1-weighted.geojson"
)

# A 1 km grid is detailed enough for this experiment while keeping the
# classification computationally manageable.
GRID_SIZE_METERS = 1_000.0

# Only observations within this distance contribute to weighted evidence.
# If none exist, the nearest observation is used as a fallback.
EVIDENCE_RADIUS_METERS = 100_000.0

# Prevent observations extremely close to a grid point from producing
# effectively infinite evidence.
MIN_DISTANCE_METERS = 1_000.0

# Evidence falls according to inverse distance raised to this exponent.
#
# 1.0 gives broad surrounding observations substantial influence.
# 2.0 behaves much more like nearest-neighbor classification.
#
# Starting at 1.5 gives local clusters meaningful influence without allowing
# large numbers of distant observations to dominate too aggressively.
DISTANCE_POWER = 1.5

# Coordinate reference systems.
SOURCE_CRS = "EPSG:4326"

# South Africa / Lo31.
PROJECTED_CRS = "EPSG:2054"

TO_PROJECTED = Transformer.from_crs(
    SOURCE_CRS,
    PROJECTED_CRS,
    always_xy=True,
).transform

TO_WGS84 = Transformer.from_crs(
    PROJECTED_CRS,
    SOURCE_CRS,
    always_xy=True,
).transform


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if (
        data.get("type")
        != "FeatureCollection"
    ):
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def load_country_geometry():
    """
    Load the unsimplified province boundaries and dissolve them into the
    national South African boundary.
    """
    data = load_geojson(
        PROVINCES_PATH
    )

    geometries = []

    for feature in data[
        "features"
    ]:
        geometry_data = (
            feature.get(
                "geometry"
            )
        )

        if geometry_data is None:
            continue

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            continue

        geometries.append(
            geometry
        )

    if not geometries:
        raise ValueError(
            "No province geometries were loaded."
        )

    country = unary_union(
        geometries
    )

    if not country.is_valid:
        country = country.buffer(
            0
        )

    return transform(
        TO_PROJECTED,
        country,
    )


def load_observations() -> tuple[
    np.ndarray,
    np.ndarray,
]:
    """
    Load cleaned postcode observations.

    Returns projected XY coordinates and an integer prefix value for every
    observation.
    """
    data = load_geojson(
        OBSERVATIONS_PATH
    )

    coordinates: list[
        tuple[float, float]
    ] = []

    prefixes: list[int] = []

    for feature in data[
        "features"
    ]:
        properties = feature.get(
            "properties",
            {},
        )

        postcode = properties.get(
            "postcode"
        )

        geometry_data = feature.get(
            "geometry"
        )

        if (
            not isinstance(
                postcode,
                str,
            )
            or len(postcode) != 4
            or not postcode.isdigit()
            or geometry_data is None
        ):
            continue

        geometry = shape(
            geometry_data
        )

        if (
            geometry.is_empty
            or geometry.geom_type
            != "Point"
        ):
            continue

        projected = transform(
            TO_PROJECTED,
            geometry,
        )

        coordinates.append(
            (
                projected.x,
                projected.y,
            )
        )

        prefixes.append(
            int(
                postcode[0]
            )
        )

    if not coordinates:
        raise ValueError(
            "No postcode observations were loaded."
        )

    return (
        np.asarray(
            coordinates,
            dtype=np.float64,
        ),
        np.asarray(
            prefixes,
            dtype=np.int8,
        ),
    )


def classify_weighted_point(
    point: np.ndarray,
    observation_coordinates: np.ndarray,
    observation_prefixes: np.ndarray,
    tree: cKDTree,
) -> int:
    """
    Classify one location using local distance-weighted prefix evidence.

    Every observation inside EVIDENCE_RADIUS_METERS contributes:

        1 / distance ** DISTANCE_POWER

    Evidence is summed separately for each 1-digit prefix. The prefix with
    the greatest total evidence wins.

    The nearest observation is used when no observations fall inside the
    configured evidence radius.
    """
    nearby_indices = (
        tree.query_ball_point(
            point,
            r=EVIDENCE_RADIUS_METERS,
        )
    )

    if not nearby_indices:
        _, nearest_index = (
            tree.query(
                point,
                k=1,
            )
        )

        return int(
            observation_prefixes[
                nearest_index
            ]
        )

    nearby_coordinates = (
        observation_coordinates[
            nearby_indices
        ]
    )

    differences = (
        nearby_coordinates
        - point
    )

    distances = np.sqrt(
        np.sum(
            differences
            * differences,
            axis=1,
        )
    )

    distances = np.maximum(
        distances,
        MIN_DISTANCE_METERS,
    )

    weights = (
        1.0
        / np.power(
            distances,
            DISTANCE_POWER,
        )
    )

    evidence = np.zeros(
        10,
        dtype=np.float64,
    )

    nearby_prefixes = (
        observation_prefixes[
            nearby_indices
        ]
    )

    np.add.at(
        evidence,
        nearby_prefixes,
        weights,
    )

    maximum = np.max(
        evidence
    )

    winners = np.flatnonzero(
        np.isclose(
            evidence,
            maximum,
        )
    )

    if len(winners) == 1:
        return int(
            winners[0]
        )

    # Extremely unlikely exact evidence ties are resolved using the prefix
    # belonging to the nearest observation.
    _, nearest_index = (
        tree.query(
            point,
            k=1,
        )
    )

    return int(
        observation_prefixes[
            nearest_index
        ]
    )


def classify_grid(
    country,
    observation_coordinates: np.ndarray,
    observation_prefixes: np.ndarray,
) -> tuple[
    dict[int, list[Any]],
    dict[int, list[Any]],
    Counter,
]:
    """
    Classify South Africa on a regular grid using both reconstruction methods.

    Returns cell polygons grouped by prefix for the nearest-observation and
    weighted-evidence classifications.
    """
    tree = cKDTree(
        observation_coordinates
    )

    min_x, min_y, max_x, max_y = (
        country.bounds
    )

    start_x = (
        math.floor(
            min_x
            / GRID_SIZE_METERS
        )
        * GRID_SIZE_METERS
    )

    start_y = (
        math.floor(
            min_y
            / GRID_SIZE_METERS
        )
        * GRID_SIZE_METERS
    )

    end_x = (
        math.ceil(
            max_x
            / GRID_SIZE_METERS
        )
        * GRID_SIZE_METERS
    )

    end_y = (
        math.ceil(
            max_y
            / GRID_SIZE_METERS
        )
        * GRID_SIZE_METERS
    )

    nearest_cells: dict[
        int,
        list[Any],
    ] = {
        prefix: []
        for prefix in range(
            10
        )
    }

    weighted_cells: dict[
        int,
        list[Any],
    ] = {
        prefix: []
        for prefix in range(
            10
        )
    }

    changes: Counter = Counter()

    total_columns = int(
        round(
            (
                end_x
                - start_x
            )
            / GRID_SIZE_METERS
        )
    )

    total_rows = int(
        round(
            (
                end_y
                - start_y
            )
            / GRID_SIZE_METERS
        )
    )

    print(
        f"Grid: "
        f"{total_columns:,} × "
        f"{total_rows:,} "
        f"({total_columns * total_rows:,} possible cells)"
    )

    processed_inside = 0

    for row in range(
        total_rows
    ):
        y0 = (
            start_y
            + row
            * GRID_SIZE_METERS
        )

        y1 = (
            y0
            + GRID_SIZE_METERS
        )

        center_y = (
            y0
            + GRID_SIZE_METERS
            / 2.0
        )

        if (
            row % 100
            == 0
        ):
            print(
                f"Processing row "
                f"{row:,} / "
                f"{total_rows:,}..."
            )

        for column in range(
            total_columns
        ):
            x0 = (
                start_x
                + column
                * GRID_SIZE_METERS
            )

            x1 = (
                x0
                + GRID_SIZE_METERS
            )

            center_x = (
                x0
                + GRID_SIZE_METERS
                / 2.0
            )

            center = np.asarray(
                [
                    center_x,
                    center_y,
                ],
                dtype=np.float64,
            )

            # Checking the center avoids creating and intersecting a polygon
            # for every grid location outside South Africa.
            from shapely.geometry import Point

            center_point = Point(
                center_x,
                center_y,
            )

            if not country.covers(
                center_point
            ):
                continue

            processed_inside += 1

            _, nearest_index = (
                tree.query(
                    center,
                    k=1,
                )
            )

            nearest_prefix = int(
                observation_prefixes[
                    nearest_index
                ]
            )

            weighted_prefix = (
                classify_weighted_point(
                    center,
                    observation_coordinates,
                    observation_prefixes,
                    tree,
                )
            )

            cell = box(
                x0,
                y0,
                x1,
                y1,
            )

            nearest_cells[
                nearest_prefix
            ].append(
                cell
            )

            weighted_cells[
                weighted_prefix
            ].append(
                cell
            )

            if (
                nearest_prefix
                != weighted_prefix
            ):
                changes[
                    (
                        nearest_prefix,
                        weighted_prefix,
                    )
                ] += 1

    print(
        f"Cells inside South Africa: "
        f"{processed_inside:,}"
    )

    changed_cells = sum(
        changes.values()
    )

    print(
        f"Cells changed by weighting: "
        f"{changed_cells:,}"
    )

    if processed_inside:
        print(
            f"Changed percentage: "
            f"{(
                changed_cells
                / processed_inside
                * 100.0
            ):.2f}%"
        )

    return (
        nearest_cells,
        weighted_cells,
        changes,
    )


def cells_to_features(
    cells_by_prefix: dict[
        int,
        list[Any],
    ],
    country,
) -> list[dict[str, Any]]:
    """
    Dissolve classified grid cells by prefix and clip them to South Africa.
    """
    features: list[
        dict[str, Any]
    ] = []

    for prefix in range(
        10
    ):
        cells = cells_by_prefix[
            prefix
        ]

        if not cells:
            continue

        print(
            f"Dissolving prefix "
            f"{prefix} "
            f"({len(cells):,} cells)..."
        )

        geometry = unary_union(
            cells
        )

        geometry = geometry.intersection(
            country
        )

        if geometry.is_empty:
            continue

        if not geometry.is_valid:
            geometry = geometry.buffer(
                0
            )

        wgs84_geometry = transform(
            TO_WGS84,
            geometry,
        )

        value = str(
            prefix
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "prefix_1": value,
                    "prefix_1_display": (
                        f"{value}---"
                    ),
                },
                "geometry": mapping(
                    wgs84_geometry
                ),
            }
        )

    return features


def write_geojson(
    path: Path,
    features: list[
        dict[str, Any]
    ],
) -> None:
    """Write a GeoJSON FeatureCollection."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    size_mb = (
        path.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"Wrote {path} "
        f"({size_mb:.2f} MB)"
    )


def print_changes(
    changes: Counter,
) -> None:
    """Print the most common nearest-to-weighted classification changes."""
    if not changes:
        print(
            "No classifications changed."
        )

        return

    print()
    print(
        "Most common classification changes"
    )
    print(
        "----------------------------------"
    )

    for (
        nearest_prefix,
        weighted_prefix,
    ), count in changes.most_common(
        30
    ):
        area_km2 = (
            count
            * (
                GRID_SIZE_METERS
                / 1000.0
            )
            ** 2
        )

        print(
            f"{nearest_prefix}--- -> "
            f"{weighted_prefix}---: "
            f"{count:,} cells "
            f"(~{area_km2:,.0f} km²)"
        )


def main() -> None:
    """Generate the experimental 1-digit prefix maps."""
    print(
        f"Reading {OBSERVATIONS_PATH}..."
    )

    (
        observation_coordinates,
        observation_prefixes,
    ) = load_observations()

    print(
        f"Observations: "
        f"{len(observation_coordinates):,}"
    )

    print()
    print(
        "Observations by prefix"
    )
    print(
        "----------------------"
    )

    prefix_counts = Counter(
        int(prefix)
        for prefix in observation_prefixes
    )

    for prefix in range(
        10
    ):
        print(
            f"{prefix}---: "
            f"{prefix_counts[prefix]:,}"
        )

    print()
    print(
        f"Reading {PROVINCES_PATH}..."
    )

    country = (
        load_country_geometry()
    )

    print()
    print(
        "Experiment parameters"
    )
    print(
        "---------------------"
    )
    print(
        f"Grid size:        "
        f"{GRID_SIZE_METERS / 1000:.1f} km"
    )
    print(
        f"Evidence radius:  "
        f"{EVIDENCE_RADIUS_METERS / 1000:.1f} km"
    )
    print(
        f"Distance power:   "
        f"{DISTANCE_POWER:.2f}"
    )
    print(
        f"Minimum distance: "
        f"{MIN_DISTANCE_METERS / 1000:.1f} km"
    )

    print()

    (
        nearest_cells,
        weighted_cells,
        changes,
    ) = classify_grid(
        country,
        observation_coordinates,
        observation_prefixes,
    )

    print_changes(
        changes
    )

    print()
    print(
        "Building nearest-observation geography..."
    )

    nearest_features = (
        cells_to_features(
            nearest_cells,
            country,
        )
    )

    write_geojson(
        NEAREST_OUTPUT_PATH,
        nearest_features,
    )

    print()
    print(
        "Building weighted-evidence geography..."
    )

    weighted_features = (
        cells_to_features(
            weighted_cells,
            country,
        )
    )

    write_geojson(
        WEIGHTED_OUTPUT_PATH,
        weighted_features,
    )

    print()
    print(
        "Done."
    )
    print(
        f"Nearest:  {NEAREST_OUTPUT_PATH}"
    )
    print(
        f"Weighted: {WEIGHTED_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()