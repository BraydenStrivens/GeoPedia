"""
Build Brazil's final CEP-2 geographic regions for GeoPedia.

Input:
    data/intermediate/countries/brazil/postal/
        municipalities-with-cep2.geojson

Output:
    data/intermediate/countries/brazil/postal/
        postal-code-regions.geojson

Each source municipality already has a complete set of valid two-digit
postal-code answers.

Municipalities are dissolved ONLY when their complete answer sets are
identical.

For example:

    M1 -> ["12"]
    M2 -> ["12"]
    M3 -> ["12", "13"]

M1 and M2 may be merged.

M3 remains a separate multi-answer feature. It must not be merged into
either the "12" or "13" region independently because that would duplicate
its geometry and create overlapping quiz features.

Disconnected polygons with the same complete answer set may belong to the
same GeoJSON feature as a MultiPolygon. This is intentional: they represent
the same quiz semantics.

State memberships are combined across all municipalities contributing to a
final feature so GeoPedia can later support state-based filtering.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely import make_valid
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FILE = Path(
    "data/intermediate/countries/brazil/postal/"
    "municipalities-with-cep2.geojson"
)

OUTPUT_FILE = Path(
    "data/intermediate/countries/brazil/postal/"
    "postal-code-regions.geojson"
)

CEP2_RE = re.compile(r"\d{2}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def postal_code_sort_key(
    value: str,
) -> tuple[int, int | str]:
    """
    Return a deterministic numeric-first sort key.
    """

    try:
        return (0, int(value))

    except ValueError:
        return (1, value)


def normalize_array(
    value: Any,
) -> list[Any]:
    """
    Convert common GeoPandas/NumPy array-like values into Python lists.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if hasattr(value, "tolist"):
        converted = value.tolist()

        if isinstance(converted, list):
            return converted

        return [converted]

    return [value]


def normalize_postal_codes(
    value: Any,
    feature_name: str,
) -> tuple[str, ...]:
    """
    Normalize one municipality's complete CEP-2 answer set.
    """

    raw_values = normalize_array(value)

    postal_codes: set[str] = set()

    for raw_value in raw_values:
        postal_code = str(
            raw_value
        ).strip()

        if not CEP2_RE.fullmatch(
            postal_code
        ):
            raise ValueError(
                "Invalid CEP-2 value "
                f"{postal_code!r} for "
                f"{feature_name}."
            )

        postal_codes.add(
            postal_code
        )

    if not postal_codes:
        raise ValueError(
            f"{feature_name} has no CEP-2 answers."
        )

    return tuple(
        sorted(
            postal_codes,
            key=postal_code_sort_key,
        )
    )


def polygonal_only(
    geometry: BaseGeometry,
) -> BaseGeometry:
    """
    Keep only Polygon/MultiPolygon portions of a geometry.
    """

    if geometry.is_empty:
        return geometry

    if isinstance(
        geometry,
        (Polygon, MultiPolygon),
    ):
        return geometry

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        polygon_parts: list[
            BaseGeometry
        ] = []

        for part in geometry.geoms:
            if isinstance(
                part,
                (Polygon, MultiPolygon),
            ):
                polygon_parts.append(
                    part
                )

        if not polygon_parts:
            return Polygon()

        return unary_union(
            polygon_parts
        )

    return Polygon()


def clean_geometry(
    geometry: BaseGeometry,
    feature_name: str,
) -> BaseGeometry:
    """
    Validate and normalize one polygonal source geometry.
    """

    if geometry is None:
        raise ValueError(
            f"{feature_name} has no geometry."
        )

    if geometry.is_empty:
        raise ValueError(
            f"{feature_name} has empty geometry."
        )

    if not geometry.is_valid:
        geometry = make_valid(
            geometry
        )

    geometry = polygonal_only(
        geometry
    )

    if geometry.is_empty:
        raise ValueError(
            f"{feature_name} contains no polygonal geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{feature_name} remains invalid after repair."
        )

    return geometry


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_municipalities() -> gpd.GeoDataFrame:
    """
    Load and validate the municipality-level CEP-2 assignment GeoJSON.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    municipalities = gpd.read_file(
        INPUT_FILE
    )

    required_columns = {
        "id",
        "name",
        "state",
        "postal_codes",
        "geometry",
    }

    missing_columns = (
        required_columns
        - set(
            municipalities.columns
        )
    )

    if missing_columns:
        raise ValueError(
            "Input GeoJSON is missing required columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    if municipalities.crs is None:
        raise ValueError(
            "Input GeoJSON has no CRS."
        )

    if municipalities.empty:
        raise ValueError(
            "Input GeoJSON contains no municipalities."
        )

    return municipalities


# ---------------------------------------------------------------------------
# Region construction
# ---------------------------------------------------------------------------


def build_regions(
    municipalities: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:
    """
    Dissolve municipalities by their COMPLETE CEP-2 answer sets.
    """

    geometry_groups: dict[
        tuple[str, ...],
        list[BaseGeometry],
    ] = defaultdict(list)

    state_groups: dict[
        tuple[str, ...],
        set[str],
    ] = defaultdict(set)

    municipality_id_groups: dict[
        tuple[str, ...],
        list[str],
    ] = defaultdict(list)

    municipality_name_groups: dict[
        tuple[str, ...],
        list[str],
    ] = defaultdict(list)

    print(
        "Grouping municipalities by complete CEP-2 answer set..."
    )

    for (
        _,
        municipality,
    ) in municipalities.iterrows():
        municipality_id = str(
            municipality["id"]
        ).strip()

        municipality_name = str(
            municipality["name"]
        ).strip()

        state = str(
            municipality["state"]
        ).strip()

        feature_name = (
            f"{state} {municipality_name} "
            f"({municipality_id})"
        )

        answer_set = (
            normalize_postal_codes(
                municipality[
                    "postal_codes"
                ],
                feature_name,
            )
        )

        geometry = clean_geometry(
            municipality.geometry,
            feature_name,
        )

        geometry_groups[
            answer_set
        ].append(
            geometry
        )

        if state:
            state_groups[
                answer_set
            ].add(
                state
            )

        municipality_id_groups[
            answer_set
        ].append(
            municipality_id
        )

        municipality_name_groups[
            answer_set
        ].append(
            municipality_name
        )

    print(
        "Distinct complete answer sets: "
        f"{len(geometry_groups):,}"
    )

    regions: list[
        dict[str, Any]
    ] = []

    for answer_set in sorted(
        geometry_groups,
        key=lambda values: tuple(
            postal_code_sort_key(
                value
            )
            for value in values
        ),
    ):
        geometries = (
            geometry_groups[
                answer_set
            ]
        )

        merged_geometry = unary_union(
            geometries
        )

        merged_geometry = (
            polygonal_only(
                merged_geometry
            )
        )

        if merged_geometry.is_empty:
            raise ValueError(
                "CEP-2 answer set "
                f"{answer_set} produced empty geometry."
            )

        if not merged_geometry.is_valid:
            merged_geometry = make_valid(
                merged_geometry
            )

            merged_geometry = (
                polygonal_only(
                    merged_geometry
                )
            )

        if (
            merged_geometry.is_empty
            or not merged_geometry.is_valid
        ):
            raise ValueError(
                "CEP-2 answer set "
                f"{answer_set} produced invalid geometry."
            )

        states = sorted(
            state_groups[
                answer_set
            ]
        )

        municipality_ids = sorted(
            municipality_id_groups[
                answer_set
            ]
        )

        municipality_names = sorted(
            municipality_name_groups[
                answer_set
            ]
        )

        first_digits = sorted(
            {
                postal_code[0]
                for postal_code
                in answer_set
            }
        )

        region_id = (
            "cep2-"
            + "-".join(
                answer_set
            )
        )

        regions.append(
            {
                "id": region_id,
                "postal_codes": list(
                    answer_set
                ),
                "first_digits": (
                    first_digits
                ),
                "states": states,
                "municipality_count": len(
                    geometries
                ),
                "municipality_ids": (
                    municipality_ids
                ),
                "municipality_names": (
                    municipality_names
                ),
                "geometry": (
                    merged_geometry
                ),
            }
        )

    return regions


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_regions(
    municipalities: gpd.GeoDataFrame,
    regions: list[dict[str, Any]],
) -> None:
    """
    Validate the final dissolved region structure.
    """

    print(
        "Validating dissolved regions..."
    )

    source_answer_sets: set[
        tuple[str, ...]
    ] = set()

    source_answers: set[
        str
    ] = set()

    for (
        _,
        municipality,
    ) in municipalities.iterrows():
        answer_set = (
            normalize_postal_codes(
                municipality[
                    "postal_codes"
                ],
                str(
                    municipality[
                        "name"
                    ]
                ),
            )
        )

        source_answer_sets.add(
            answer_set
        )

        source_answers.update(
            answer_set
        )

    output_answer_sets = {
        tuple(
            region[
                "postal_codes"
            ]
        )
        for region in regions
    }

    output_answers = {
        postal_code
        for region in regions
        for postal_code
        in region[
            "postal_codes"
        ]
    }

    if (
        output_answer_sets
        != source_answer_sets
    ):
        raise ValueError(
            "Final answer-set collection does not match "
            "the municipality assignments."
        )

    if output_answers != source_answers:
        raise ValueError(
            "Final CEP-2 answer coverage does not match "
            "the municipality assignments."
        )

    source_municipality_count = len(
        municipalities
    )

    output_municipality_count = sum(
        region[
            "municipality_count"
        ]
        for region in regions
    )

    if (
        output_municipality_count
        != source_municipality_count
    ):
        raise ValueError(
            "Municipality count changed during dissolve: "
            f"{source_municipality_count:,} -> "
            f"{output_municipality_count:,}."
        )

    ids = [
        region["id"]
        for region in regions
    ]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Duplicate final feature IDs."
        )

    print(
        "Validation passed."
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_geojson(
    municipalities: gpd.GeoDataFrame,
    regions: list[dict[str, Any]],
) -> None:
    """
    Write native GeoJSON while preserving array-valued quiz properties.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    features = []

    for region in regions:
        properties = {
            "id": region[
                "id"
            ],
            "postal_codes": region[
                "postal_codes"
            ],
            "first_digits": region[
                "first_digits"
            ],
            "states": region[
                "states"
            ],
            "municipality_count": region[
                "municipality_count"
            ],
            "municipality_ids": region[
                "municipality_ids"
            ],
            "municipality_names": region[
                "municipality_names"
            ],
        }

        features.append(
            {
                "type": "Feature",
                "id": region[
                    "id"
                ],
                "properties": properties,
                "geometry": mapping(
                    region[
                        "geometry"
                    ]
                ),
            }
        )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            feature_collection,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_summary(
    municipalities: gpd.GeoDataFrame,
    regions: list[dict[str, Any]],
) -> None:
    """
    Print a compact inspection summary.
    """

    all_answers = sorted(
        {
            postal_code
            for region in regions
            for postal_code
            in region[
                "postal_codes"
            ]
        },
        key=postal_code_sort_key,
    )

    single_answer_regions = [
        region
        for region in regions
        if len(
            region[
                "postal_codes"
            ]
        )
        == 1
    ]

    multi_answer_regions = [
        region
        for region in regions
        if len(
            region[
                "postal_codes"
            ]
        )
        > 1
    ]

    polygon_count = 0

    for region in regions:
        geometry = region[
            "geometry"
        ]

        if isinstance(
            geometry,
            Polygon,
        ):
            polygon_count += 1

        elif isinstance(
            geometry,
            MultiPolygon,
        ):
            polygon_count += len(
                geometry.geoms
            )

    print()
    print(
        "Brazil CEP-2 dissolved regions"
    )
    print(
        "------------------------------"
    )
    print(
        f"Source municipalities:   "
        f"{len(municipalities):>6,}"
    )
    print(
        f"Final features:          "
        f"{len(regions):>6,}"
    )
    print(
        f"Single-answer features:  "
        f"{len(single_answer_regions):>6,}"
    )
    print(
        f"Multi-answer features:   "
        f"{len(multi_answer_regions):>6,}"
    )
    print(
        f"Polygon parts:           "
        f"{polygon_count:>6,}"
    )
    print(
        f"Distinct CEP-2 answers:  "
        f"{len(all_answers):>6,}"
    )

    print()
    print(
        "Multi-answer features"
    )
    print(
        "---------------------"
    )

    for region in multi_answer_regions:
        answers = ", ".join(
            region[
                "postal_codes"
            ]
        )

        states = ", ".join(
            region[
                "states"
            ]
        )

        municipality_names = ", ".join(
            region[
                "municipality_names"
            ]
        )

        print(
            f"[{answers}] "
            f"states=[{states}] "
            f"municipalities="
            f"{region['municipality_count']}: "
            f"{municipality_names}"
        )

    print()
    print(
        "Output"
    )
    print(
        "------"
    )
    print(
        OUTPUT_FILE
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Loading municipality CEP-2 assignments..."
    )

    municipalities = (
        load_municipalities()
    )

    print(
        f"Municipalities: "
        f"{len(municipalities):,}"
    )

    regions = build_regions(
        municipalities
    )

    validate_regions(
        municipalities,
        regions,
    )

    print(
        "Writing dissolved CEP-2 regions..."
    )

    write_geojson(
        municipalities,
        regions,
    )

    print_summary(
        municipalities,
        regions,
    )


if __name__ == "__main__":
    main()