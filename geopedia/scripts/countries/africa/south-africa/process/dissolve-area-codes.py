"""
Dissolve classified South Africa wards into telephone area-code regions.

This script converts GeoPedia's ward-level South Africa telephone area-code
classification into two geographic datasets:

1. Full geographic telephone area-code regions.
2. One-digit geographic prefix regions, using the first digit after the
   national trunk prefix 0.

The input ward classification is produced by:
    scripts/countries/south-africa/process/area-codes.py

010 is treated as an alternative Johannesburg code whose geographic region is
represented by the same dissolved feature as 011. The shared feature exposes
["010", "011"] as its accepted area-code answers while retaining 011 as its
stable geographic feature ID.

Input:
    data/intermediate/countries/south-africa/area-codes/
    classified-wards.geojson

Outputs:
    data/intermediate/countries/south-africa/area-codes/
    area-codes.geojson

    data/intermediate/countries/south-africa/area-codes/
    area-code-prefixes.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/process/dissolve-area-codes.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


INPUT_PATH = Path(
    "data/intermediate/countries/south-africa/area-codes/"
    "classified-wards.geojson"
)

AREA_CODES_OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/area-codes/"
    "area-codes.geojson"
)

PREFIXES_OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/area-codes/"
    "area-code-prefixes.geojson"
)


def load_feature_collection(
    path: Path,
) -> list[dict[str, Any]]:
    """
    Load and validate a GeoJSON FeatureCollection.
    """
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
            "Input must be a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Input has no valid features array."
        )

    return features


def dissolve_area_codes(
    features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Dissolve classified ward geometries by full geographic area code.
    """
    geometries_by_code: defaultdict[
        str,
        list[Any],
    ] = defaultdict(list)

    ward_counts: defaultdict[
        str,
        int,
    ] = defaultdict(int)

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        area_code = properties.get(
            "area_code"
        )

        if not isinstance(
            area_code,
            str,
        ):
            raise ValueError(
                "Every ward must have an area_code "
                "before dissolving."
            )

        geometry_data = feature.get(
            "geometry"
        )

        if not geometry_data:
            raise ValueError(
                f"Ward in area code {area_code} "
                "has no geometry."
            )

        geometries_by_code[
            area_code
        ].append(
            shape(
                geometry_data
            )
        )

        ward_counts[
            area_code
        ] += 1

    output: list[
        dict[str, Any]
    ] = []

    for area_code in sorted(
        geometries_by_code
    ):
        print(
            f"  Dissolving {area_code}: "
            f"{ward_counts[area_code]:,} wards"
        )

        dissolved = unary_union(
            geometries_by_code[
                area_code
            ]
        )

        output.append(
            {
                "type": "Feature",
                "geometry": mapping(
                    dissolved
                ),
                "properties": {
                    "area_code_id": (
                        "010 / 011"
                        if area_code == "011"
                        else area_code
                    ),
                    "area_codes": (
                        ["010", "011"]
                        if area_code == "011"
                        else [area_code]
                    ),
                    "area_code_label": (
                        "010 / 011"
                        if area_code == "011"
                        else area_code
                    ),
                    "prefix_1": area_code[1],
                    "ward_count": (
                        ward_counts[
                            area_code
                        ]
                    ),
                },
            }
        )

    return output


def dissolve_prefixes(
    features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Dissolve classified ward geometries by one-digit geographic prefix.
    """
    geometries_by_prefix: defaultdict[
        str,
        list[Any],
    ] = defaultdict(list)

    ward_counts: defaultdict[
        str,
        int,
    ] = defaultdict(int)

    area_codes_by_prefix: defaultdict[
        str,
        set[str],
    ] = defaultdict(set)

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        area_code = properties.get(
            "area_code"
        )

        prefix = properties.get(
            "prefix_1"
        )

        if not isinstance(
            area_code,
            str,
        ):
            raise ValueError(
                "Every ward must have an area_code."
            )

        if not isinstance(
            prefix,
            str,
        ):
            raise ValueError(
                "Every ward must have prefix_1."
            )

        geometry_data = feature.get(
            "geometry"
        )

        if not geometry_data:
            raise ValueError(
                f"Ward in prefix {prefix} "
                "has no geometry."
            )

        geometries_by_prefix[
            prefix
        ].append(
            shape(
                geometry_data
            )
        )

        ward_counts[
            prefix
        ] += 1

        area_codes_by_prefix[
            prefix
        ].add(
            area_code
        )

    output: list[
        dict[str, Any]
    ] = []

    for prefix in sorted(
        geometries_by_prefix
    ):
        print(
            f"  Dissolving prefix {prefix}: "
            f"{ward_counts[prefix]:,} wards"
        )

        dissolved = unary_union(
            geometries_by_prefix[
                prefix
            ]
        )

        output.append(
            {
                "type": "Feature",
                "geometry": mapping(
                    dissolved
                ),
                "properties": {
                    "prefix_id": prefix,
                    "prefix_1": prefix,
                    "area_codes": sorted(
                        area_codes_by_prefix[
                            prefix
                        ]
                    ),
                    "ward_count": (
                        ward_counts[
                            prefix
                        ]
                    ),
                },
            }
        )

    return output


def write_feature_collection(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    """
    Write features as a compact GeoJSON FeatureCollection.
    """
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": features,
            },
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def print_geometry_diagnostics(
    label: str,
    features: list[dict[str, Any]],
    id_property: str,
) -> None:
    """
    Print geometry type, validity, and disconnected-part diagnostics.
    """
    print()
    print(label)

    for feature in features:
        properties = feature[
            "properties"
        ]

        identifier = properties[
            id_property
        ]

        geometry = shape(
            feature[
                "geometry"
            ]
        )

        if geometry.geom_type == "Polygon":
            part_count = 1

        elif geometry.geom_type == "MultiPolygon":
            part_count = len(
                geometry.geoms
            )

        else:
            part_count = 0

        print(
            f"  {identifier}: "
            f"{geometry.geom_type:<12} "
            f"parts={part_count:<4} "
            f"valid={geometry.is_valid}"
        )


def main() -> None:
    print("Loading classified wards...")

    ward_features = load_feature_collection(
        INPUT_PATH
    )

    print(
        f"Loaded {len(ward_features):,} wards."
    )

    if len(ward_features) != 4392:
        print(
            "WARNING: expected 4,392 wards."
        )

    print()
    print("Dissolving full area codes...")

    area_code_features = (
        dissolve_area_codes(
            ward_features
        )
    )

    print()
    print("Dissolving one-digit prefixes...")

    prefix_features = dissolve_prefixes(
        ward_features
    )

    print_geometry_diagnostics(
        "Area-code geometry diagnostics:",
        area_code_features,
        "area_code_id",
    )

    print_geometry_diagnostics(
        "Prefix geometry diagnostics:",
        prefix_features,
        "prefix_id",
    )

    write_feature_collection(
        AREA_CODES_OUTPUT_PATH,
        area_code_features,
    )

    write_feature_collection(
        PREFIXES_OUTPUT_PATH,
        prefix_features,
    )

    print()
    print("=" * 72)
    print("DISSOLVE SUMMARY")
    print("=" * 72)

    print(
        f"Input wards:          "
        f"{len(ward_features):,}"
    )

    print(
        f"Area-code features:   "
        f"{len(area_code_features):,}"
    )

    print(
        f"Prefix features:      "
        f"{len(prefix_features):,}"
    )

    area_size = (
        AREA_CODES_OUTPUT_PATH.stat().st_size
        / (1024 * 1024)
    )

    prefix_size = (
        PREFIXES_OUTPUT_PATH.stat().st_size
        / (1024 * 1024)
    )

    print()
    print("Wrote:")
    print(
        f"  {AREA_CODES_OUTPUT_PATH}"
    )
    print(
        f"  {area_size:.2f} MB"
    )

    print()
    print(
        f"  {PREFIXES_OUTPUT_PATH}"
    )
    print(
        f"  {prefix_size:.2f} MB"
    )


if __name__ == "__main__":
    main()