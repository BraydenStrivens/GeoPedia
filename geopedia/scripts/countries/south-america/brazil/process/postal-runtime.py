"""
Build the runtime Brazil CEP-2 GeoJSON for GeoPedia.

Input:
    data/intermediate/countries/brazil/postal/
        postal-code-regions.geojson

Output:
    public/data/countries/brazil/geojson/
        postal-codes.geojson

The input has already been validated and dissolved by COMPLETE answer set.

For example:

    ["12"]
    ["12"]
    ["12", "13"]

The two ["12"] areas belong to one logical feature, even when geographically
disconnected. The ["12", "13"] feature remains separate because its complete
answer set differs.

This runtime processor:

1. Validates the intermediate feature structure.
2. Keeps only properties required by GeoPedia at runtime.
3. Projects the complete polygon coverage into a Brazil-wide metric CRS.
4. Simplifies the entire coverage together so shared boundaries remain shared.
5. Tries progressively larger tolerances and selects the smallest one that
   produces a minified GeoJSON no larger than TARGET_SIZE_BYTES.
6. Converts back to WGS84.
7. Rounds coordinates.
8. Revalidates feature count, answer coverage, answer sets, polygon geometry,
   and coverage topology.
9. Writes the final runtime GeoJSON.

The size target is intentionally 1,000,000 bytes rather than 1 MiB so a
reported file size below 1 MB also remains below the stricter decimal
definition of one megabyte.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(
    __file__
).resolve().parents[4]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "brazil"
    / "postal"
    / "postal-code-regions.geojson"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
    / "postal-codes.geojson"
)


# ---------------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------------

SOURCE_CRS = "EPSG:4326"

# SIRGAS 2000 / Brazil Polyconic.
#
# This is appropriate for nationwide Brazil processing and, unlike WGS84,
# gives simplification tolerances meaningful metric units.
PROCESSING_CRS = "EPSG:5880"

# Strict decimal-megabyte target.
TARGET_SIZE_BYTES = 1_000_000

# Six decimal places in geographic coordinates is already substantially more
# precise than this quiz requires while avoiding unnecessary runtime bytes.
COORDINATE_DECIMAL_PLACES = 6

# Try the smallest tolerances first so the highest-detail result satisfying the
# runtime size target is selected.
#
# 0 means no geometric simplification; metadata removal and minification alone
# may already be sufficient.
SIMPLIFY_TOLERANCES_METERS = [
    0,
    25,
    50,
    75,
    100,
    150,
    200,
    300,
    400,
    500,
    750,
    1_000,
    1_500,
    2_000,
    3_000,
    4_000,
    5_000,
]

EXPECTED_FEATURE_COUNT = 84
EXPECTED_DISTINCT_ANSWER_COUNT = 98
EXPECTED_MULTI_ANSWER_FEATURE_COUNT = 8

EXPECTED_RUNTIME_PROPERTIES = {
    "postal_code_id",
    "postal_codes",
    "first_digits",
    "states",
}


# ---------------------------------------------------------------------------
# Coordinate transformers
# ---------------------------------------------------------------------------

TO_PROCESSING_CRS = Transformer.from_crs(
    SOURCE_CRS,
    PROCESSING_CRS,
    always_xy=True,
).transform

TO_RUNTIME_CRS = Transformer.from_crs(
    PROCESSING_CRS,
    SOURCE_CRS,
    always_xy=True,
).transform


# ---------------------------------------------------------------------------
# General helpers
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


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    """
    Load a GeoJSON FeatureCollection.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Expected input GeoJSON to be a "
            "FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            "FeatureCollection has no valid features array."
        )

    return data


def normalize_string_array(
    value: Any,
    property_name: str,
    feature_id: str,
) -> tuple[str, ...]:
    """
    Normalize and validate one array-valued runtime property.
    """

    if not isinstance(
        value,
        list,
    ):
        raise ValueError(
            f"Feature {feature_id} property "
            f"{property_name!r} must be an array."
        )

    normalized: list[str] = []

    for item in value:
        if (
            not isinstance(
                item,
                str,
            )
            or not item.strip()
        ):
            raise ValueError(
                f"Feature {feature_id} property "
                f"{property_name!r} contains "
                f"invalid value {item!r}."
            )

        normalized.append(
            item.strip()
        )

    if not normalized:
        raise ValueError(
            f"Feature {feature_id} property "
            f"{property_name!r} is empty."
        )

    if len(normalized) != len(
        set(normalized)
    ):
        raise ValueError(
            f"Feature {feature_id} property "
            f"{property_name!r} contains duplicates."
        )

    return tuple(
        normalized
    )


def polygonal_only(
    geometry: BaseGeometry,
) -> Polygon | MultiPolygon:
    """
    Extract only polygonal content from a geometry.
    """

    if isinstance(
        geometry,
        Polygon,
    ):
        return geometry

    if isinstance(
        geometry,
        MultiPolygon,
    ):
        return geometry

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        polygon_parts: list[
            Polygon
        ] = []

        for part in geometry.geoms:
            if isinstance(
                part,
                Polygon,
            ):
                polygon_parts.append(
                    part
                )

            elif isinstance(
                part,
                MultiPolygon,
            ):
                polygon_parts.extend(
                    part.geoms
                )

        if not polygon_parts:
            raise ValueError(
                "GeometryCollection contains no polygonal geometry."
            )

        merged = unary_union(
            polygon_parts
        )

        if isinstance(
            merged,
            (Polygon, MultiPolygon),
        ):
            return merged

    raise ValueError(
        "Geometry could not be reduced to Polygon/MultiPolygon."
    )


def clean_geometry(
    geometry: BaseGeometry,
    feature_id: str,
) -> Polygon | MultiPolygon:
    """
    Repair and validate one polygonal feature.
    """

    if geometry.is_empty:
        raise ValueError(
            f"Feature {feature_id} has empty geometry."
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
            f"Feature {feature_id} became empty after repair."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Feature {feature_id} remains invalid after repair."
        )

    return geometry


def round_coordinates(
    value: Any,
) -> Any:
    """
    Recursively round coordinates inside a GeoJSON coordinate structure.
    """

    if isinstance(
        value,
        (list, tuple),
    ):
        # Coordinate pair.
        if (
            len(value) >= 2
            and isinstance(
                value[0],
                (int, float),
            )
            and isinstance(
                value[1],
                (int, float),
            )
        ):
            return [
                round(
                    number,
                    COORDINATE_DECIMAL_PLACES,
                )
                if isinstance(
                    number,
                    (int, float),
                )
                else number
                for number in value
            ]

        return [
            round_coordinates(
                item
            )
            for item in value
        ]

    return value


def count_coordinates(
    geometry: BaseGeometry,
) -> int:
    """
    Count coordinate vertices in Polygon/MultiPolygon geometry.
    """

    if isinstance(
        geometry,
        Polygon,
    ):
        count = len(
            geometry.exterior.coords
        )

        for interior in geometry.interiors:
            count += len(
                interior.coords
            )

        return count

    if isinstance(
        geometry,
        MultiPolygon,
    ):
        return sum(
            count_coordinates(
                part
            )
            for part in geometry.geoms
        )

    return 0


def count_polygon_parts(
    geometry: BaseGeometry,
) -> int:
    """
    Count Polygon components.
    """

    if isinstance(
        geometry,
        Polygon,
    ):
        return 1

    if isinstance(
        geometry,
        MultiPolygon,
    ):
        return len(
            geometry.geoms
        )

    return 0


def serialize_geojson(
    data: dict[str, Any],
) -> bytes:
    """
    Serialize compact UTF-8 GeoJSON exactly as it will be written.
    """

    text = json.dumps(
        data,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    )

    return text.encode(
        "utf-8"
    )


# ---------------------------------------------------------------------------
# Intermediate feature loading
# ---------------------------------------------------------------------------


def load_regions() -> list[
    dict[str, Any]
]:
    """
    Load and normalize the validated intermediate CEP-2 regions.
    """

    source = load_geojson(
        INPUT_FILE
    )

    features = source[
        "features"
    ]

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Expected "
            f"{EXPECTED_FEATURE_COUNT} intermediate features, "
            f"got {len(features)}."
        )

    regions: list[
        dict[str, Any]
    ] = []

    seen_ids: set[
        str
    ] = set()

    for index, feature in enumerate(
        features,
        start=1,
    ):
        feature_id_raw = feature.get(
            "id"
        )

        if (
            not isinstance(
                feature_id_raw,
                str,
            )
            or not feature_id_raw.strip()
        ):
            properties = feature.get(
                "properties",
                {},
            )

            feature_id_raw = properties.get(
                "id"
            )

        if (
            not isinstance(
                feature_id_raw,
                str,
            )
            or not feature_id_raw.strip()
        ):
            raise ValueError(
                f"Feature {index} has no valid ID."
            )

        feature_id = (
            feature_id_raw.strip()
        )

        if feature_id in seen_ids:
            raise ValueError(
                f"Duplicate feature ID: {feature_id}"
            )

        seen_ids.add(
            feature_id
        )

        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"Feature {feature_id} has invalid properties."
            )

        postal_codes = normalize_string_array(
            properties.get(
                "postal_codes"
            ),
            "postal_codes",
            feature_id,
        )

        postal_codes = tuple(
            sorted(
                postal_codes,
                key=postal_code_sort_key,
            )
        )

        for postal_code in postal_codes:
            if (
                len(postal_code) != 2
                or not postal_code.isdigit()
            ):
                raise ValueError(
                    f"Feature {feature_id} has invalid "
                    f"CEP-2 value {postal_code!r}."
                )

        first_digits = normalize_string_array(
            properties.get(
                "first_digits"
            ),
            "first_digits",
            feature_id,
        )

        expected_first_digits = tuple(
            sorted(
                {
                    postal_code[0]
                    for postal_code
                    in postal_codes
                }
            )
        )

        if tuple(
            sorted(first_digits)
        ) != expected_first_digits:
            raise ValueError(
                f"Feature {feature_id} has inconsistent "
                "first_digits."
            )

        states = normalize_string_array(
            properties.get(
                "states"
            ),
            "states",
            feature_id,
        )

        geometry_data = feature.get(
            "geometry"
        )

        if not isinstance(
            geometry_data,
            dict,
        ):
            raise ValueError(
                f"Feature {feature_id} has invalid geometry."
            )

        geometry = clean_geometry(
            shape(
                geometry_data
            ),
            feature_id,
        )

        regions.append(
            {
                "id": feature_id,
                "postal_codes": (
                    postal_codes
                ),
                "first_digits": (
                    expected_first_digits
                ),
                "states": tuple(
                    sorted(states)
                ),
                "geometry": geometry,
            }
        )

    return regions


# ---------------------------------------------------------------------------
# Semantic validation
# ---------------------------------------------------------------------------


def validate_semantics(
    regions: list[
        dict[str, Any]
    ],
) -> None:
    """
    Validate feature count and complete quiz-answer semantics.
    """

    if len(regions) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} regions, "
            f"got {len(regions)}."
        )

    answer_sets = [
        tuple(
            region[
                "postal_codes"
            ]
        )
        for region in regions
    ]

    if len(answer_sets) != len(
        set(answer_sets)
    ):
        raise ValueError(
            "Two runtime features have identical complete "
            "postal-code answer sets."
        )

    distinct_answers = {
        postal_code
        for region in regions
        for postal_code
        in region[
            "postal_codes"
        ]
    }

    if (
        len(distinct_answers)
        != EXPECTED_DISTINCT_ANSWER_COUNT
    ):
        raise ValueError(
            "Expected "
            f"{EXPECTED_DISTINCT_ANSWER_COUNT} distinct "
            "CEP-2 answers, got "
            f"{len(distinct_answers)}."
        )

    multi_answer_count = sum(
        1
        for region in regions
        if len(
            region[
                "postal_codes"
            ]
        )
        > 1
    )

    if (
        multi_answer_count
        != EXPECTED_MULTI_ANSWER_FEATURE_COUNT
    ):
        raise ValueError(
            "Expected "
            f"{EXPECTED_MULTI_ANSWER_FEATURE_COUNT} "
            "multi-answer features, got "
            f"{multi_answer_count}."
        )


# ---------------------------------------------------------------------------
# Coverage simplification
# ---------------------------------------------------------------------------


def project_regions(
    regions: list[
        dict[str, Any]
    ],
) -> list[
    dict[str, Any]
]:
    """
    Project every region into the Brazil-wide metric processing CRS.
    """

    projected: list[
        dict[str, Any]
    ] = []

    for region in regions:
        projected_geometry = transform(
            TO_PROCESSING_CRS,
            region[
                "geometry"
            ],
        )

        projected_geometry = clean_geometry(
            projected_geometry,
            region[
                "id"
            ],
        )

        projected.append(
            {
                **region,
                "geometry": (
                    projected_geometry
                ),
            }
        )

    return projected

def simplify_projected_regions(
    regions: list[
        dict[str, Any]
    ],
    tolerance_meters: float,
) -> list[
    dict[str, Any]
]:
    """
    Simplify each final CEP-2 feature in projected metric coordinates.

    The dissolved Brazil postal regions are not a mathematically exact Shapely
    coverage because the underlying municipality source contains small boundary
    inconsistencies. Therefore coverage_simplify() is intentionally not used.

    Each logical quiz feature is simplified independently while preserving its
    own topology. Complete answer sets and feature membership remain unchanged.
    """

    result: list[
        dict[str, Any]
    ] = []

    for region in regions:
        geometry = region[
            "geometry"
        ]

        if tolerance_meters > 0:
            geometry = geometry.simplify(
                tolerance_meters,
                preserve_topology=True,
            )

        geometry = clean_geometry(
            geometry,
            region[
                "id"
            ],
        )

        result.append(
            {
                **region,
                "geometry": geometry,
            }
        )

    return result

# ---------------------------------------------------------------------------
# Runtime GeoJSON construction
# ---------------------------------------------------------------------------


def build_runtime_geojson(
    projected_regions: list[
        dict[str, Any]
    ],
) -> tuple[
    dict[str, Any],
    list[BaseGeometry],
]:
    """
    Convert simplified projected regions back to WGS84 runtime GeoJSON.
    """

    features: list[
        dict[str, Any]
    ] = []

    rounded_geometries: list[
        BaseGeometry
    ] = []

    for region in projected_regions:
        runtime_geometry = transform(
            TO_RUNTIME_CRS,
            region[
                "geometry"
            ],
        )

        runtime_geometry = clean_geometry(
            runtime_geometry,
            region[
                "id"
            ],
        )

        geometry_mapping = mapping(
            runtime_geometry
        )

        geometry_mapping[
            "coordinates"
        ] = round_coordinates(
            geometry_mapping[
                "coordinates"
            ]
        )

        # Reparse the rounded geometry so validation checks the exact
        # coordinates that will actually be shipped to MapLibre.
        rounded_geometry = clean_geometry(
            shape(
                geometry_mapping
            ),
            region[
                "id"
            ],
        )

        rounded_geometries.append(
            rounded_geometry
        )

        features.append(
            {
                "type": "Feature",
                "id": region[
                    "id"
                ],
                "properties": {
                    "postal_code_id": region[
                        "id"
                    ],
                    "postal_codes": list(
                        region[
                            "postal_codes"
                        ]
                    ),
                    "first_digits": list(
                        region[
                            "first_digits"
                        ]
                    ),
                    "states": list(
                        region[
                            "states"
                        ]
                    ),
                },
                "geometry": (
                    geometry_mapping
                ),
            }
        )

    return (
        {
            "type": "FeatureCollection",
            "features": features,
        },
        rounded_geometries,
    )


def validate_runtime_geojson(
    data: dict[str, Any],
    rounded_geometries: list[
        BaseGeometry
    ],
) -> None:
    """
    Validate the exact runtime structure after coordinate rounding.
    """

    features = data.get(
        "features"
    )

    if (
        not isinstance(
            features,
            list,
        )
        or len(features)
        != EXPECTED_FEATURE_COUNT
    ):
        raise ValueError(
            "Runtime GeoJSON has an unexpected feature count."
        )

    seen_ids: set[
        str
    ] = set()

    answer_sets: set[
        tuple[str, ...]
    ] = set()

    answers: set[
        str
    ] = set()

    multi_answer_count = 0

    for feature in features:
        feature_id = feature.get(
            "id"
        )

        if (
            not isinstance(
                feature_id,
                str,
            )
            or not feature_id
        ):
            raise ValueError(
                "Runtime feature has invalid ID."
            )

        if feature_id in seen_ids:
            raise ValueError(
                f"Duplicate runtime feature ID: {feature_id}"
            )

        seen_ids.add(
            feature_id
        )

        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"Runtime feature {feature_id} has "
                "invalid properties."
            )

        if (
            set(properties)
            != EXPECTED_RUNTIME_PROPERTIES
        ):
            raise ValueError(
                f"Runtime feature {feature_id} has "
                "unexpected property set: "
                f"{sorted(properties)}"
            )
            
        if properties[
            "postal_code_id"
        ] != feature_id:
            raise ValueError(
                f"Runtime feature {feature_id} has "
                "postal_code_id that does not match "
                "its GeoJSON feature ID."
            )

        postal_codes = normalize_string_array(
            properties[
                "postal_codes"
            ],
            "postal_codes",
            feature_id,
        )

        answer_set = tuple(
            sorted(
                postal_codes,
                key=postal_code_sort_key,
            )
        )

        if answer_set in answer_sets:
            raise ValueError(
                "Duplicate complete runtime answer set: "
                f"{answer_set}"
            )

        answer_sets.add(
            answer_set
        )

        answers.update(
            answer_set
        )

        if len(
            answer_set
        ) > 1:
            multi_answer_count += 1

        first_digits = normalize_string_array(
            properties[
                "first_digits"
            ],
            "first_digits",
            feature_id,
        )

        expected_first_digits = tuple(
            sorted(
                {
                    postal_code[0]
                    for postal_code
                    in answer_set
                }
            )
        )

        if tuple(
            sorted(first_digits)
        ) != expected_first_digits:
            raise ValueError(
                f"Runtime feature {feature_id} has "
                "incorrect first_digits."
            )

        normalize_string_array(
            properties[
                "states"
            ],
            "states",
            feature_id,
        )

    if (
        len(answers)
        != EXPECTED_DISTINCT_ANSWER_COUNT
    ):
        raise ValueError(
            "Runtime answer count changed during processing."
        )

    if (
        multi_answer_count
        != EXPECTED_MULTI_ANSWER_FEATURE_COUNT
    ):
        raise ValueError(
            "Runtime multi-answer feature count changed."
        )

# ---------------------------------------------------------------------------
# Adaptive size selection
# ---------------------------------------------------------------------------


def choose_runtime_output(
    projected_regions: list[
        dict[str, Any]
    ],
) -> tuple[
    dict[str, Any],
    bytes,
    float,
    int,
    int,
]:
    """
    Select the smallest simplification tolerance meeting the size target.

    Returns:
        runtime GeoJSON
        serialized bytes
        chosen tolerance
        coordinate count
        polygon-part count
    """

    original_coordinate_count = sum(
        count_coordinates(
            region[
                "geometry"
            ]
        )
        for region in projected_regions
    )

    print()
    print(
        "Testing runtime simplification tolerances"
    )
    print(
        "-----------------------------------------"
    )
    print(
        "Original coordinates: "
        f"{original_coordinate_count:,}"
    )
    print(
        "Target size:          "
        f"{TARGET_SIZE_BYTES:,} bytes"
    )
    print()

    last_size: int | None = None

    for tolerance in (
        SIMPLIFY_TOLERANCES_METERS
    ):
        simplified = (
            simplify_projected_regions(
                projected_regions,
                tolerance,
            )
        )

        runtime_data, rounded_geometries = (
            build_runtime_geojson(
                simplified
            )
        )

        validate_runtime_geojson(
            runtime_data,
            rounded_geometries,
        )

        serialized = serialize_geojson(
            runtime_data
        )

        size_bytes = len(
            serialized
        )

        coordinate_count = sum(
            count_coordinates(
                geometry
            )
            for geometry
            in rounded_geometries
        )

        polygon_part_count = sum(
            count_polygon_parts(
                geometry
            )
            for geometry
            in rounded_geometries
        )

        reduction_percent = (
            (
                1
                - coordinate_count
                / original_coordinate_count
            )
            * 100
            if original_coordinate_count
            else 0
        )

        print(
            f"{tolerance:>5,g} m  "
            f"{size_bytes:>10,} bytes  "
            f"{coordinate_count:>9,} coords  "
            f"{reduction_percent:>5.1f}% reduction"
        )

        last_size = size_bytes

        if (
            size_bytes
            <= TARGET_SIZE_BYTES
        ):
            return (
                runtime_data,
                serialized,
                tolerance,
                coordinate_count,
                polygon_part_count,
            )

    raise ValueError(
        "No configured simplification tolerance "
        "reached the 1,000,000-byte target. "
        "Smallest tested result was "
        f"{last_size:,} bytes. Add another tolerance "
        "only after visually inspecting the current output."
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_runtime_file(
    serialized: bytes,
) -> None:
    """
    Write the exact validated runtime bytes.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_bytes(
        serialized
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Loading dissolved Brazil CEP-2 regions..."
    )

    regions = load_regions()

    validate_semantics(
        regions
    )

    print(
        f"Validated intermediate features: "
        f"{len(regions):,}"
    )

    distinct_answers = {
        postal_code
        for region in regions
        for postal_code
        in region[
            "postal_codes"
        ]
    }

    multi_answer_count = sum(
        1
        for region in regions
        if len(
            region[
                "postal_codes"
            ]
        )
        > 1
    )

    print(
        f"Distinct CEP-2 answers:        "
        f"{len(distinct_answers):,}"
    )

    print(
        f"Multi-answer features:         "
        f"{multi_answer_count:,}"
    )

    print(
        "Projecting complete coverage to EPSG:5880..."
    )

    projected_regions = project_regions(
        regions
    )

    (
        runtime_data,
        serialized,
        chosen_tolerance,
        coordinate_count,
        polygon_part_count,
    ) = choose_runtime_output(
        projected_regions
    )

    # Keep the variable referenced so the final validation occurs immediately
    # before writing exactly the selected result.
    rounded_geometries = [
        clean_geometry(
            shape(
                feature[
                    "geometry"
                ]
            ),
            str(
                feature[
                    "id"
                ]
            ),
        )
        for feature in runtime_data[
            "features"
        ]
    ]

    validate_runtime_geojson(
        runtime_data,
        rounded_geometries,
    )

    write_runtime_file(
        serialized
    )

    final_size = (
        OUTPUT_FILE.stat().st_size
    )

    if (
        final_size
        > TARGET_SIZE_BYTES
    ):
        raise ValueError(
            "Written file unexpectedly exceeds size target: "
            f"{final_size:,} bytes."
        )

    print()
    print(
        "Brazil CEP-2 runtime GeoJSON"
    )
    print(
        "----------------------------"
    )
    print(
        f"Features:               "
        f"{len(runtime_data['features']):>8,}"
    )
    print(
        f"Distinct answers:       "
        f"{len(distinct_answers):>8,}"
    )
    print(
        f"Multi-answer features:  "
        f"{multi_answer_count:>8,}"
    )
    print(
        f"Polygon parts:          "
        f"{polygon_part_count:>8,}"
    )
    print(
        f"Coordinates:            "
        f"{coordinate_count:>8,}"
    )
    print(
        f"Chosen tolerance:       "
        f"{chosen_tolerance:>8,g} m"
    )
    print(
        f"File size:              "
        f"{final_size:>8,} bytes"
    )
    print(
        f"File size:              "
        f"{final_size / 1_000_000:>8.3f} MB"
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


if __name__ == "__main__":
    main()