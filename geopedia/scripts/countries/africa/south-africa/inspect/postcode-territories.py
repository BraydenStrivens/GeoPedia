"""
Inspect reconstructed South African postcode territory sizes.

This diagnostic compares the unsimplified reconstructed four-digit postcode
geography with the cleaned OSM postcode observations used to create it.

For every postcode it reports:

- Observation count
- Polygon area
- Approximate territory width and height
- Maximum distance from any point in the generated territory to the nearest
  observation for that postcode

The maximum observation distance is especially useful for identifying sparse
postcode observations whose Voronoi cells have expanded far beyond the area
directly supported by their observations.

The script prints distribution statistics and the largest outliers by maximum
observation distance. A specific postcode can optionally be supplied to show
its individual statistics.

Inputs:

    data/intermediate/countries/south-africa/osm/
    postcode-points-cleaned.geojson

    data/intermediate/countries/south-africa/postcodes/
    postcodes-4.geojson

Examples:

    python scripts/countries/south-africa/inspect/postcode-territories.py

    python scripts/countries/south-africa/inspect/postcode-territories.py 9999

This script does not modify any data.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform


OBSERVATIONS_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points-cleaned.geojson"
)

POSTCODES_PATH = Path(
    "data/intermediate/countries/south-africa/postcodes/"
    "postcodes-4.geojson"
)

PROJECT = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2054",
    always_xy=True,
).transform

TOP_OUTLIERS = 50


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
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
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
            f"{path} has no valid features array."
        )

    return data


def load_observations() -> dict[
    str,
    list[Point],
]:
    """Load cleaned postcode observations grouped by postcode."""
    data = load_geojson(
        OBSERVATIONS_PATH
    )

    observations: dict[
        str,
        list[Point],
    ] = defaultdict(
        list
    )

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

        geometry = feature.get(
            "geometry"
        )

        if (
            not isinstance(
                postcode,
                str,
            )
            or geometry is None
        ):
            continue

        point = shape(
            geometry
        )

        if (
            point.is_empty
            or point.geom_type
            != "Point"
        ):
            continue

        projected_point = transform(
            PROJECT,
            point,
        )

        observations[
            postcode
        ].append(
            projected_point
        )

    return observations


def percentile(
    values: list[float],
    percentage: float,
) -> float:
    """Return a linearly interpolated percentile."""
    if not values:
        raise ValueError(
            "Cannot calculate percentile of an empty list."
        )

    ordered = sorted(
        values
    )

    if len(ordered) == 1:
        return ordered[
            0
        ]

    position = (
        percentage
        / 100.0
        * (
            len(ordered)
            - 1
        )
    )

    lower_index = math.floor(
        position
    )

    upper_index = math.ceil(
        position
    )

    if (
        lower_index
        == upper_index
    ):
        return ordered[
            lower_index
        ]

    fraction = (
        position
        - lower_index
    )

    return (
        ordered[
            lower_index
        ]
        * (
            1.0
            - fraction
        )
        + ordered[
            upper_index
        ]
        * fraction
    )


def geometry_vertices(
    geometry: Any,
) -> list[tuple[float, float]]:
    """
    Return exterior and interior ring vertices from a polygonal geometry.

    The maximum nearest-observation distance is evaluated at polygon vertices.
    For Voronoi-derived geometry, the farthest unsupported portions of a cell
    occur at its boundary, making these vertices useful for detecting
    excessively large territories.
    """
    vertices: list[
        tuple[float, float]
    ] = []

    polygons = (
        [geometry]
        if geometry.geom_type
        == "Polygon"
        else list(
            geometry.geoms
        )
    )

    for polygon in polygons:
        vertices.extend(
            polygon.exterior.coords
        )

        for interior in (
            polygon.interiors
        ):
            vertices.extend(
                interior.coords
            )

    return vertices


def maximum_observation_distance(
    geometry: Any,
    observations: list[Point],
) -> float:
    """
    Return the maximum distance from a polygon vertex to its nearest
    observation, in kilometers.
    """
    maximum_distance = 0.0

    for x, y in geometry_vertices(
        geometry
    ):
        vertex = Point(
            x,
            y,
        )

        nearest_distance = min(
            vertex.distance(
                observation
            )
            for observation in observations
        )

        maximum_distance = max(
            maximum_distance,
            nearest_distance,
        )

    return (
        maximum_distance
        / 1000.0
    )


def analyze() -> list[
    dict[str, Any]
]:
    """Analyze every reconstructed four-digit postcode territory."""
    print(
        f"Reading {OBSERVATIONS_PATH}..."
    )

    observations = (
        load_observations()
    )

    print(
        f"Reading {POSTCODES_PATH}..."
    )

    postcode_data = (
        load_geojson(
            POSTCODES_PATH
        )
    )

    results: list[
        dict[str, Any]
    ] = []

    for feature in postcode_data[
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
            or geometry_data is None
        ):
            continue

        postcode_observations = (
            observations.get(
                postcode,
                [],
            )
        )

        if not postcode_observations:
            raise ValueError(
                f"No cleaned observations found "
                f"for postcode {postcode}."
            )

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            raise ValueError(
                f"Empty geometry for postcode {postcode}."
            )

        projected_geometry = transform(
            PROJECT,
            geometry,
        )

        min_x, min_y, max_x, max_y = (
            projected_geometry.bounds
        )

        area_km2 = (
            projected_geometry.area
            / 1_000_000.0
        )

        width_km = (
            max_x
            - min_x
        ) / 1000.0

        height_km = (
            max_y
            - min_y
        ) / 1000.0

        max_distance_km = (
            maximum_observation_distance(
                projected_geometry,
                postcode_observations,
            )
        )

        results.append(
            {
                "postcode": postcode,
                "observations": len(
                    postcode_observations
                ),
                "area_km2": area_km2,
                "width_km": width_km,
                "height_km": height_km,
                "max_distance_km": (
                    max_distance_km
                ),
            }
        )

    return results


def print_distribution(
    results: list[
        dict[str, Any]
    ],
) -> None:
    """Print distributions for reconstructed territory measurements."""
    distances = [
        result[
            "max_distance_km"
        ]
        for result in results
    ]

    areas = [
        result[
            "area_km2"
        ]
        for result in results
    ]

    print()
    print(
        "Territory summary"
    )
    print(
        "-----------------"
    )
    print(
        f"Postcodes:              "
        f"{len(results):,}"
    )

    print()
    print(
        "Maximum distance from territory to nearest same-postcode observation"
    )
    print(
        "---------------------------------------------------------------"
    )

    for label, value in (
        (
            "Median",
            percentile(
                distances,
                50,
            ),
        ),
        (
            "P75",
            percentile(
                distances,
                75,
            ),
        ),
        (
            "P90",
            percentile(
                distances,
                90,
            ),
        ),
        (
            "P95",
            percentile(
                distances,
                95,
            ),
        ),
        (
            "P99",
            percentile(
                distances,
                99,
            ),
        ),
        (
            "Maximum",
            max(
                distances
            ),
        ),
    ):
        print(
            f"{label:<12} "
            f"{value:>10.2f} km"
        )

    print()
    print(
        "Territory area"
    )
    print(
        "--------------"
    )

    for label, value in (
        (
            "Median",
            percentile(
                areas,
                50,
            ),
        ),
        (
            "P75",
            percentile(
                areas,
                75,
            ),
        ),
        (
            "P90",
            percentile(
                areas,
                90,
            ),
        ),
        (
            "P95",
            percentile(
                areas,
                95,
            ),
        ),
        (
            "P99",
            percentile(
                areas,
                99,
            ),
        ),
        (
            "Maximum",
            max(
                areas
            ),
        ),
    ):
        print(
            f"{label:<12} "
            f"{value:>10.2f} km²"
        )


def print_result(
    result: dict[str, Any],
) -> None:
    """Print one postcode territory result."""
    print(
        f"{result['postcode']}  "
        f"obs={result['observations']:>5,}  "
        f"max-distance="
        f"{result['max_distance_km']:>7.2f} km  "
        f"area="
        f"{result['area_km2']:>10.2f} km²  "
        f"bounds="
        f"{result['width_km']:.1f}"
        f"×"
        f"{result['height_km']:.1f} km"
    )


def print_outliers(
    results: list[
        dict[str, Any]
    ],
) -> None:
    """Print the territories with the greatest unsupported reach."""
    ordered = sorted(
        results,
        key=lambda result: result[
            "max_distance_km"
        ],
        reverse=True,
    )

    print()
    print(
        f"Top {TOP_OUTLIERS} territories by maximum observation distance"
    )
    print(
        "-" * 72
    )

    for result in ordered[
        :TOP_OUTLIERS
    ]:
        print_result(
            result
        )


def print_specific_postcode(
    results: list[
        dict[str, Any]
    ],
    postcode: str,
) -> None:
    """Print the result for a requested postcode."""
    result = next(
        (
            result
            for result in results
            if result[
                "postcode"
            ]
            == postcode
        ),
        None,
    )

    if result is None:
        raise SystemExit(
            f"Postcode {postcode} "
            "was not found in the reconstructed geography."
        )

    ordered = sorted(
        results,
        key=lambda item: item[
            "max_distance_km"
        ],
        reverse=True,
    )

    rank = (
        ordered.index(
            result
        )
        + 1
    )

    print()
    print(
        f"Requested postcode: {postcode}"
    )
    print(
        "------------------------"
    )

    print_result(
        result
    )

    print(
        f"Maximum-distance rank: "
        f"{rank:,} of {len(results):,}"
    )


def main() -> None:
    """Analyze reconstructed postcode territories."""
    requested_postcode: (
        str
        | None
    ) = None

    if len(
        sys.argv
    ) > 2:
        raise SystemExit(
            "Usage: python "
            "scripts/countries/south-africa/inspect/"
            "postcode-territories.py [postcode]"
        )

    if len(
        sys.argv
    ) == 2:
        requested_postcode = (
            sys.argv[
                1
            ].strip()
        )

        if (
            len(
                requested_postcode
            )
            != 4
            or not requested_postcode.isdigit()
        ):
            raise SystemExit(
                "Postcode must contain exactly four digits."
            )

    results = analyze()

    if not results:
        raise SystemExit(
            "No postcode territories were analyzed."
        )

    print_distribution(
        results
    )

    print_outliers(
        results
    )

    if requested_postcode:
        print_specific_postcode(
            results,
            requested_postcode,
        )


if __name__ == "__main__":
    main()