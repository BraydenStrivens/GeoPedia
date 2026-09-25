"""
Derive South African postcode-prefix polygons from the reconstructed
four-digit postcode geography.

The four-digit postcode reconstruction is treated as the canonical base
geography. Its polygons are dissolved by progressively shorter postcode
prefixes to produce three-digit, two-digit, and one-digit postcode maps.

Deriving every coarser level from the same four-digit geography guarantees
that postcode boundaries remain spatially consistent throughout the quiz
hierarchy.

Input:

    data/intermediate/countries/south-africa/postcodes/
    postcodes-4.geojson

Outputs:

    data/intermediate/countries/south-africa/postcodes/
    postcodes-3.geojson

    data/intermediate/countries/south-africa/postcodes/
    postcodes-2.geojson

    data/intermediate/countries/south-africa/postcodes/
    postcodes-1.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-africa/process/dissolve-postcodes.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


POSTCODES_DIRECTORY = Path(
    "data/intermediate/countries/south-africa/postcodes"
)

INPUT_PATH = (
    POSTCODES_DIRECTORY
    / "postcodes-4.geojson"
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


def validate_postcode(
    feature: dict[str, Any],
) -> str:
    """Return and validate a feature's four-digit postcode."""
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
            f"Invalid postcode: {postcode!r}"
        )

    return postcode


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


def output_properties(
    prefix: str,
    digits: int,
) -> dict[str, str]:
    """Build hierarchy properties appropriate for one prefix level."""
    if digits == 3:
        return {
            "prefix_3": prefix,
            "prefix_2": prefix[:2],
            "prefix_1": prefix[:1],
        }

    if digits == 2:
        return {
            "prefix_2": prefix,
            "prefix_1": prefix[:1],
        }

    if digits == 1:
        return {
            "prefix_1": prefix,
        }

    raise ValueError(
        f"Unsupported prefix length: {digits}"
    )


def dissolve_level(
    source_features: list[
        dict[str, Any]
    ],
    digits: int,
) -> None:
    """Dissolve four-digit postcode geometries into one prefix level."""
    property_name = (
        f"prefix_{digits}"
    )

    output_path = (
        POSTCODES_DIRECTORY
        / f"postcodes-{digits}.geojson"
    )

    geometries_by_prefix: dict[
        str,
        list,
    ] = defaultdict(list)

    for feature in source_features:
        postcode = validate_postcode(
            feature
        )

        geometry_data = feature.get(
            "geometry"
        )

        if geometry_data is None:
            raise ValueError(
                f"Postcode {postcode} has no geometry."
            )

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            raise ValueError(
                f"Postcode {postcode} has empty geometry."
            )

        prefix = postcode[
            :digits
        ]

        geometries_by_prefix[
            prefix
        ].append(
            geometry
        )

    print()
    print(
        f"Dissolving {digits}-digit prefixes..."
    )
    print(
        f"Distinct prefixes:      "
        f"{len(geometries_by_prefix):,}"
    )

    output_features: list[
        dict[str, Any]
    ] = []

    polygon_count = 0
    multipolygon_count = 0
    total_parts = 0
    invalid_before_repair = 0
    invalid_after_repair = 0

    for prefix in sorted(
        geometries_by_prefix
    ):
        geometries = (
            geometries_by_prefix[
                prefix
            ]
        )

        dissolved = unary_union(
            geometries
        )

        if not dissolved.is_valid:
            invalid_before_repair += 1

            dissolved = (
                dissolved.buffer(0)
            )

        parts = polygon_parts(
            dissolved
        )

        if not parts:
            raise RuntimeError(
                f"Prefix {prefix} has no polygonal "
                "geometry after dissolve."
            )

        if len(parts) == 1:
            final_geometry = parts[
                0
            ]
        else:
            final_geometry = (
                unary_union(
                    parts
                )
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
                f"Unexpected geometry type "
                f"for {prefix}: "
                f"{final_geometry.geom_type}"
            )

        total_parts += part_count

        output_features.append(
            {
                "type": "Feature",
                "properties": (
                    output_properties(
                        prefix,
                        digits,
                    )
                ),
                "geometry": mapping(
                    final_geometry
                ),
            }
        )

    output_data = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    with output_path.open(
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
        output_path.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"Output features:        "
        f"{len(output_features):,}"
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
    print(
        f"Output size:            "
        f"{size_mb:.2f} MB"
    )
    print(
        f"Wrote:                  "
        f"{output_path}"
    )


def main() -> None:
    """Generate all postcode-prefix datasets from four-digit geography."""
    print(
        "Loading four-digit postcode geography..."
    )

    data = load_feature_collection(
        INPUT_PATH
    )

    features = data[
        "features"
    ]

    print(
        f"Four-digit postcodes:   "
        f"{len(features):,}"
    )

    distinct_postcodes = set()

    for feature in features:
        postcode = validate_postcode(
            feature
        )

        if postcode in distinct_postcodes:
            raise ValueError(
                f"Duplicate postcode feature: "
                f"{postcode}"
            )

        distinct_postcodes.add(
            postcode
        )

    print(
        f"Distinct postcodes:     "
        f"{len(distinct_postcodes):,}"
    )

    for digits in (
        3,
        2,
        1,
    ):
        dissolve_level(
            features,
            digits,
        )

    print()
    print(
        "Postcode prefix dissolve complete."
    )


if __name__ == "__main__":
    main()