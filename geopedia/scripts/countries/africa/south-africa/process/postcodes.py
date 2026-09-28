"""
Build experimental South African four-digit postcode polygons.

The cleaned OSM postcode observations are used as spatial samples of postcode
territory. A Voronoi tessellation assigns every location to its nearest
postcode observation. Voronoi cells belonging to observations with the same
four-digit postcode are then dissolved together.

The result is clipped to South Africa's national outline, which is constructed
by dissolving the unsimplified province geometries.

This is intentionally a first-pass reconstruction. It does not use wards,
distance limits, smoothing, or special rural-area heuristics. The intermediate
output is intended for inspection before the postcode geography is finalized.

Inputs:

    data/intermediate/countries/south-africa/osm/
    postcode-points-cleaned.geojson

    data/intermediate/countries/south-africa/admin/
    provinces.geojson

Output:

    data/intermediate/countries/south-africa/postcodes/
    postcodes-4.geojson

Output properties:

    postcode
        Full four-digit postcode.

    prefix_3
        First three digits.

    prefix_2
        First two digits.

    prefix_1
        First digit.

Run from the GeoPedia project root:

    python scripts/countries/south-africa/process/postcodes.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from shapely import voronoi_polygons
from shapely.geometry import MultiPoint, mapping, shape
from shapely.ops import unary_union


POSTCODES_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points-cleaned.geojson"
)

PROVINCES_PATH = Path(
    "data/intermediate/countries/south-africa/admin/"
    "provinces.geojson"
)

OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/postcodes/"
    "postcodes-4.geojson"
)


def load_feature_collection(
    path: Path,
) -> dict[str, Any]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
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
            f"{path} has no valid features array."
        )

    return data


def observation_postcode(
    feature: dict[str, Any],
) -> str:
    """Return and validate an observation's four-digit postcode."""
    properties = feature.get(
        "properties",
        {}
    )

    postcode = properties.get(
        "postcode"
    )

    if (
        not isinstance(postcode, str)
        or len(postcode) != 4
        or not postcode.isdigit()
    ):
        raise ValueError(
            f"Invalid postcode observation: {postcode!r}"
        )

    return postcode


def build_country_boundary(
    province_features: list[
        dict[str, Any]
    ],
):
    """Dissolve province geometries into the South Africa national outline."""
    geometries = []

    for feature in province_features:
        geometry_data = feature.get(
            "geometry"
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
            "No valid province geometries were found."
        )

    country = unary_union(
        geometries
    )

    if country.is_empty:
        raise ValueError(
            "South Africa boundary is empty after union."
        )

    if not country.is_valid:
        country = country.buffer(0)

    if country.is_empty:
        raise ValueError(
            "South Africa boundary became empty after repair."
        )

    return country


def polygon_parts(
    geometry,
) -> list:
    """Return all polygonal parts from a Shapely geometry."""
    if geometry.is_empty:
        return []

    if geometry.geom_type == "Polygon":
        return [
            geometry
        ]

    if geometry.geom_type == "MultiPolygon":
        return list(
            geometry.geoms
        )

    if geometry.geom_type == "GeometryCollection":
        parts = []

        for child in geometry.geoms:
            parts.extend(
                polygon_parts(
                    child
                )
            )

        return parts

    return []


def main() -> None:
    """Construct experimental four-digit postcode polygons."""
    print(
        "Loading cleaned postcode observations..."
    )

    postcode_data = load_feature_collection(
        POSTCODES_PATH
    )

    postcode_features = postcode_data[
        "features"
    ]

    print(
        f"Postcode observations: "
        f"{len(postcode_features):,}"
    )

    print("Loading provinces...")

    province_data = load_feature_collection(
        PROVINCES_PATH
    )

    province_features = province_data[
        "features"
    ]

    print(
        f"Provinces:             "
        f"{len(province_features):,}"
    )

    print()
    print(
        "Building South Africa boundary..."
    )

    country_boundary = (
        build_country_boundary(
            province_features
        )
    )

    print(
        f"Boundary type:         "
        f"{country_boundary.geom_type}"
    )
    print(
        f"Boundary valid:        "
        f"{country_boundary.is_valid}"
    )

    print()
    print(
        "Reading observation coordinates..."
    )

    coordinates: list[
        tuple[float, float]
    ] = []

    postcodes: list[str] = []

    seen_coordinates: dict[
        tuple[float, float],
        str,
    ] = {}

    duplicate_same_postcode = 0
    conflicting_coordinates = 0

    for feature in postcode_features:
        postcode = observation_postcode(
            feature
        )

        geometry = feature.get(
            "geometry"
        )

        if (
            not isinstance(
                geometry,
                dict,
            )
            or geometry.get("type")
            != "Point"
        ):
            raise ValueError(
                "Postcode observation does not contain "
                "Point geometry."
            )

        point_coordinates = geometry.get(
            "coordinates"
        )

        if (
            not isinstance(
                point_coordinates,
                list,
            )
            or len(point_coordinates) < 2
        ):
            raise ValueError(
                "Postcode observation has invalid coordinates."
            )

        coordinate = (
            float(
                point_coordinates[0]
            ),
            float(
                point_coordinates[1]
            ),
        )

        existing_postcode = (
            seen_coordinates.get(
                coordinate
            )
        )

        if existing_postcode is not None:
            if existing_postcode == postcode:
                duplicate_same_postcode += 1
                continue

            conflicting_coordinates += 1

            print(
                "WARNING: identical coordinate has "
                "different postcodes: "
                f"{existing_postcode} / {postcode} "
                f"at {coordinate}"
            )

            # Voronoi cannot create separate cells for identical
            # coordinates. Preserve the first observation here and
            # report the conflict for later inspection.
            continue

        seen_coordinates[
            coordinate
        ] = postcode

        coordinates.append(
            coordinate
        )

        postcodes.append(
            postcode
        )

    print(
        f"Unique coordinates:    "
        f"{len(coordinates):,}"
    )
    print(
        f"Duplicate same-code:   "
        f"{duplicate_same_postcode:,}"
    )
    print(
        f"Coordinate conflicts:  "
        f"{conflicting_coordinates:,}"
    )

    if len(coordinates) < 2:
        raise ValueError(
            "At least two unique postcode coordinates "
            "are required."
        )

    print()
    print(
        "Building Voronoi tessellation..."
    )

    points = MultiPoint(
        coordinates
    )

    voronoi = voronoi_polygons(
        points,
        extend_to=country_boundary.envelope,
        ordered=True,
    )

    cells = list(
        voronoi.geoms
    )

    if len(cells) != len(
        coordinates
    ):
        raise RuntimeError(
            "Voronoi cell count does not match "
            "observation coordinate count: "
            f"{len(cells):,} cells vs "
            f"{len(coordinates):,} coordinates."
        )

    print(
        f"Voronoi cells:         "
        f"{len(cells):,}"
    )

    print()
    print(
        "Clipping cells to South Africa and "
        "grouping by postcode..."
    )

    cells_by_postcode: dict[
        str,
        list,
    ] = defaultdict(list)

    empty_after_clip = 0

    for index, cell in enumerate(
        cells
    ):
        clipped = cell.intersection(
            country_boundary
        )

        parts = polygon_parts(
            clipped
        )

        if not parts:
            empty_after_clip += 1
            continue

        postcode = postcodes[
            index
        ]

        cells_by_postcode[
            postcode
        ].extend(
            parts
        )

    print(
        f"Postcodes with cells:  "
        f"{len(cells_by_postcode):,}"
    )
    print(
        f"Empty clipped cells:   "
        f"{empty_after_clip:,}"
    )

    print()
    print(
        "Dissolving Voronoi cells by postcode..."
    )

    output_features: list[
        dict[str, Any]
    ] = []

    invalid_before_repair = 0
    invalid_after_repair = 0
    polygon_count = 0
    multipolygon_count = 0
    total_parts = 0

    postcodes_without_geometry = []

    distinct_postcodes = sorted(
        set(postcodes)
    )

    for postcode in distinct_postcodes:
        postcode_cells = (
            cells_by_postcode.get(
                postcode,
                [],
            )
        )

        if not postcode_cells:
            postcodes_without_geometry.append(
                postcode
            )
            continue

        dissolved = unary_union(
            postcode_cells
        )

        if not dissolved.is_valid:
            invalid_before_repair += 1
            dissolved = dissolved.buffer(0)

        parts = polygon_parts(
            dissolved
        )

        if not parts:
            postcodes_without_geometry.append(
                postcode
            )
            continue

        if len(parts) == 1:
            final_geometry = parts[
                0
            ]
        else:
            final_geometry = unary_union(
                parts
            )

        if not final_geometry.is_valid:
            invalid_after_repair += 1

        if (
            final_geometry.geom_type
            == "Polygon"
        ):
            polygon_count += 1
            part_count = 1
        elif (
            final_geometry.geom_type
            == "MultiPolygon"
        ):
            multipolygon_count += 1
            part_count = len(
                final_geometry.geoms
            )
        else:
            raise RuntimeError(
                f"Unexpected final geometry type "
                f"for {postcode}: "
                f"{final_geometry.geom_type}"
            )

        total_parts += part_count

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "postcode": postcode,
                    "prefix_3": postcode[
                        :3
                    ],
                    "prefix_2": postcode[
                        :2
                    ],
                    "prefix_1": postcode[
                        :1
                    ],
                },
                "geometry": mapping(
                    final_geometry
                ),
            }
        )

    print()
    print("Geometry summary")
    print("----------------")
    print(
        f"Input postcodes:        "
        f"{len(distinct_postcodes):,}"
    )
    print(
        f"Output postcodes:       "
        f"{len(output_features):,}"
    )
    print(
        f"Without geometry:       "
        f"{len(postcodes_without_geometry):,}"
    )
    print(
        f"Polygons:               "
        f"{polygon_count:,}"
    )
    print(
        f"MultiPolygons:          "
        f"{multipolygon_count:,}"
    )
    print(
        f"Total polygon parts:    "
        f"{total_parts:,}"
    )
    print(
        f"Invalid before repair:  "
        f"{invalid_before_repair:,}"
    )
    print(
        f"Invalid after repair:   "
        f"{invalid_after_repair:,}"
    )

    if postcodes_without_geometry:
        print()
        print(
            "Postcodes without geometry:"
        )

        for postcode in (
            postcodes_without_geometry
        ):
            print(
                f"  {postcode}"
            )

    output_data = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        f"Writing {OUTPUT_PATH}..."
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output_data,
            file,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    size_mb = (
        OUTPUT_PATH.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"Output size:            "
        f"{size_mb:.2f} MB"
    )

    print()
    print("Postcode reconstruction complete.")


if __name__ == "__main__":
    main()