"""
Generate Taiwan telephone area-code quiz GeoJSON files.

This script converts GeoPedia's verified township-level Taiwan telephone
area-code classification into the final GeoJSON files used by the three
telephone-code map quizzes.

Inputs
------
Taiwan township geometry:
    data/intermediate/countries/taiwan/admin/townships.geojson

Verified township -> R01-R32 assignments:
    data/intermediate/countries/taiwan/area-codes/
    township-area-code-color-regions.json

Outputs
-------
Detailed area codes:
    public/data/countries/taiwan/geojson/area-codes.geojson

2-digit significant prefixes:
    public/data/countries/taiwan/geojson/area-code-prefix-2.geojson

1-digit significant prefixes:
    public/data/countries/taiwan/geojson/area-code-prefix-1.geojson

Generation model
----------------
The verified intermediate classification assigns every one of Taiwan's
368 townships to one of 32 geographic telephone regions, R01-R32.

The final GeoJSON files do not expose R01-R32 as quiz answers. Instead,
geometry is dissolved according to the complete answer set appropriate
for each quiz.

For example, a detailed region with:

    area_codes = ["043", "0422", "0423", "0424", "0427"]

produces:

Detailed quiz:
    area_codes = ["043", "0422", "0423", "0424", "0427"]
    prefix_1   = ["4"]
    prefix_2   = ["42", "43"]

2-digit prefix quiz:
    area_codes = ["42", "43"]
    prefix_1   = ["4"]

1-digit prefix quiz:
    area_codes = ["4"]

Features are dissolved by the COMPLETE answer set. An answer array such
as ["42", "43"] therefore represents one multi-answer geographic feature;
it is not split into separate overlapping "42" and "43" polygons.

Feature IDs
-----------
Every generated feature receives a stable `id` property formed by joining
its complete area_codes array with "-".

Examples:

    ["02"]                         -> "02"
    ["032", "034"]                 -> "032-034"
    ["42", "43"]                   -> "42-43"
    ["043", "0422", "0423"]        -> "043-0422-0423"

These IDs can be used as MapLibre promoteId values.

Grouping properties
-------------------
The detailed area-code GeoJSON contains:

    area_codes: string[]
    prefix_1:   string[]
    prefix_2:   string[]

The 2-digit prefix GeoJSON contains:

    area_codes: string[]
    prefix_1:   string[]

The 1-digit prefix GeoJSON contains:

    area_codes: string[]

GeoPedia quiz configs can therefore use `valueType: "string-array"` for
the grouping properties.

Prefix derivation ignores Taiwan's leading domestic trunk "0".

Examples:

    02    -> significant digits 2
    032   -> significant digits 32
    0422  -> significant digits 422
    08362 -> significant digits 8362

Important
---------
This script does NOT classify township geometry. Classification belongs
to classify-area-codes.py.

If the verified township assignments change, rerun that script first and
then rerun this generator.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

TOWNSHIPS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "townships.geojson"
)

ASSIGNMENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "township-area-code-color-regions.json"
)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
#
# This generator intentionally writes full-resolution geometry to the
# intermediate data tree.
#
# The generated files are source geometry for the separate simplification
# step. They should not be served directly by the application because the
# original township geometry contains far more coordinate detail than the
# map quizzes require.
# ---------------------------------------------------------------------------

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
)

DETAILED_OUTPUT_PATH = (
    OUTPUT_DIRECTORY
    / "area-codes.geojson"
)

PREFIX_2_OUTPUT_PATH = (
    OUTPUT_DIRECTORY
    / "area-code-prefix-2.geojson"
)

PREFIX_1_OUTPUT_PATH = (
    OUTPUT_DIRECTORY
    / "area-code-prefix-1.geojson"
)


# ---------------------------------------------------------------------------
# Expected source structure
# ---------------------------------------------------------------------------

EXPECTED_TOWNSHIP_COUNT = 368
EXPECTED_DETAILED_REGION_COUNT = 32

EXPECTED_REGION_IDS = {
    f"R{number:02d}"
    for number in range(
        1,
        EXPECTED_DETAILED_REGION_COUNT + 1,
    )
}


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def load_json(
    path: Path,
) -> Any:
    """Load a UTF-8 JSON file."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required input file does not exist:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )


def write_geojson(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    """Write a compact GeoJSON FeatureCollection."""

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


# ---------------------------------------------------------------------------
# Classification-data helpers
# ---------------------------------------------------------------------------


def get_assignment_records(
    data: Any,
) -> list[dict[str, Any]]:
    """
    Locate the 368 township assignment records in the classifier output.

    The function supports either a root-level list or a dictionary
    containing one township-shaped list.
    """

    if isinstance(
        data,
        list,
    ):
        return data

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Area-code assignment JSON must contain either a list or "
            "an object containing the township assignment list."
        )

    likely_keys = (
        "townships",
        "assignments",
        "results",
        "features",
    )

    for key in likely_keys:
        value = data.get(
            key
        )

        if not isinstance(
            value,
            list,
        ):
            continue

        if value and all(
            isinstance(
                item,
                dict,
            )
            and "township_id" in item
            for item in value
        ):
            return value

    candidates: list[
        list[dict[str, Any]]
    ] = []

    for value in data.values():
        if not isinstance(
            value,
            list,
        ):
            continue

        if not value:
            continue

        if all(
            isinstance(
                item,
                dict,
            )
            and "township_id" in item
            for item in value
        ):
            candidates.append(
                value
            )

    if len(
        candidates
    ) == 1:
        return candidates[0]

    raise ValueError(
        "Could not uniquely locate the township assignment list in "
        f"{ASSIGNMENTS_PATH}."
    )


def get_township_id(
    feature: dict[str, Any],
) -> str:
    """Read a stable township_id from a township GeoJSON feature."""

    properties = feature.get(
        "properties"
    )

    if not isinstance(
        properties,
        dict,
    ):
        raise ValueError(
            "Township GeoJSON feature is missing a properties object."
        )

    township_id = properties.get(
        "township_id"
    )

    if township_id is None:
        raise ValueError(
            "Township GeoJSON feature is missing township_id."
        )

    return str(
        township_id
    )


# ---------------------------------------------------------------------------
# Telephone-code helpers
# ---------------------------------------------------------------------------


def significant_digits(
    area_code: str,
) -> str:
    """
    Return an area's significant digits after removing the leading 0.

    Examples:
        02    -> 2
        032   -> 32
        0422  -> 422
        08362 -> 8362
    """

    code = str(
        area_code
    ).strip()

    if not code:
        raise ValueError(
            "Encountered an empty telephone area code."
        )

    if not code.isdigit():
        raise ValueError(
            "Telephone area code must contain only digits: "
            f"{code!r}"
        )

    if not code.startswith(
        "0"
    ):
        raise ValueError(
            "Detailed Taiwan telephone area code does not begin with "
            f"the expected trunk zero: {code!r}"
        )

    significant = code[1:]

    if not significant:
        raise ValueError(
            f"Area code has no significant digits: {code!r}"
        )

    return significant


def unique_preserving_order(
    values: Iterable[str],
) -> list[str]:
    """Return unique strings while preserving their first-seen order."""

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if value in seen:
            continue

        seen.add(
            value
        )

        result.append(
            value
        )

    return result


def derive_prefix_1_from_detailed_codes(
    area_codes: list[str],
) -> list[str]:
    """Derive unique 1-digit significant prefixes from detailed codes."""

    return unique_preserving_order(
        significant_digits(
            code
        )[:1]
        for code in area_codes
    )


def derive_prefix_2_from_detailed_codes(
    area_codes: list[str],
) -> list[str]:
    """
    Derive unique 2-digit significant prefixes from detailed codes.

    If a code has only one significant digit, that complete value is
    retained rather than inventing a second digit.

    Example:
        ["02"] -> ["2"]
    """

    return unique_preserving_order(
        significant_digits(
            code
        )[:2]
        for code in area_codes
    )


def derive_prefix_1_from_prefix_2(
    prefix_2: list[str],
) -> list[str]:
    """
    Derive the 1-digit grouping property for a 2-digit-prefix feature.
    """

    result: list[str] = []

    for prefix in prefix_2:
        value = str(
            prefix
        ).strip()

        if not value:
            raise ValueError(
                "Encountered an empty 2-digit prefix."
            )

        if not value.isdigit():
            raise ValueError(
                f"2-digit prefix must contain only digits: {value!r}"
            )

        result.append(
            value[:1]
        )

    return unique_preserving_order(
        result
    )


def normalize_detailed_area_codes(
    value: Any,
    *,
    region_id: str,
) -> list[str]:
    """Validate a detailed region's area_codes array."""

    if not isinstance(
        value,
        list,
    ):
        raise ValueError(
            f"{region_id} area_codes must be an array."
        )

    normalized: list[str] = []

    for item in value:
        if not isinstance(
            item,
            str,
        ):
            raise ValueError(
                f"{region_id} contains a non-string area code: "
                f"{item!r}"
            )

        code = item.strip()

        significant_digits(
            code
        )

        if code not in normalized:
            normalized.append(
                code
            )

    if not normalized:
        raise ValueError(
            f"{region_id} has no area codes."
        )

    return normalized


def make_feature_id(
    area_codes: list[str],
) -> str:
    """
    Create the stable feature ID from the complete answer set.

    Examples:
        ["02"] -> "02"
        ["032", "034"] -> "032-034"
        ["42", "43"] -> "42-43"
    """

    if not area_codes:
        raise ValueError(
            "Cannot create a feature ID from an empty area_codes array."
        )

    return "-".join(
        area_codes
    )


def answer_set_key(
    answers: list[str],
) -> tuple[str, ...]:
    """
    Convert an answer array to the immutable dissolve key.

    Answer order is intentionally preserved because it is also used for
    the generated feature ID and user-facing answer order.
    """

    if not answers:
        raise ValueError(
            "Cannot create an answer-set key from an empty array."
        )

    return tuple(
        answers
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def dissolve_geometries(
    geometries: list[Any],
    *,
    feature_id: str,
) -> Any:
    """Union a set of geometries and validate the result."""

    if not geometries:
        raise ValueError(
            f"No geometries were supplied for {feature_id!r}."
        )

    dissolved = unary_union(
        geometries
    )

    if dissolved.is_empty:
        raise ValueError(
            f"{feature_id!r} dissolved to empty geometry."
        )

    if not dissolved.is_valid:
        repaired = dissolved.buffer(
            0
        )

        if repaired.is_empty or not repaired.is_valid:
            raise ValueError(
                f"{feature_id!r} produced invalid geometry and "
                "could not be repaired."
            )

        dissolved = repaired

    return dissolved


# ---------------------------------------------------------------------------
# Detailed region construction
# ---------------------------------------------------------------------------


def build_detailed_features(
    assignments: list[dict[str, Any]],
    township_geometry_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build the detailed telephone area-code features.

    Township geometries are first grouped by R01-R32. Those Rxx regions
    are then dissolved again by their complete detailed area_codes answer
    set so that the final file follows the same answer-set rule as the
    prefix files.
    """

    region_geometries: dict[
        str,
        list[Any],
    ] = defaultdict(
        list
    )

    region_area_codes: dict[
        str,
        list[str],
    ] = {}

    seen_township_ids: set[str] = set()

    for assignment in assignments:
        raw_township_id = assignment.get(
            "township_id"
        )

        if raw_township_id is None:
            raise ValueError(
                "Township assignment is missing township_id."
            )

        township_id = str(
            raw_township_id
        )

        if township_id in seen_township_ids:
            raise ValueError(
                f"Duplicate township assignment: {township_id}"
            )

        seen_township_ids.add(
            township_id
        )

        geometry_data = township_geometry_by_id.get(
            township_id
        )

        if geometry_data is None:
            raise ValueError(
                "Assignment references a township that does not exist "
                f"in the geometry file: {township_id}"
            )

        region_id = assignment.get(
            "region_id"
        )

        if not isinstance(
            region_id,
            str,
        ):
            raise ValueError(
                f"Township {township_id} has no valid region_id."
            )

        if region_id not in EXPECTED_REGION_IDS:
            raise ValueError(
                f"Township {township_id} has unexpected region "
                f"{region_id!r}."
            )

        area_codes = normalize_detailed_area_codes(
            assignment.get(
                "area_codes"
            ),
            region_id=region_id,
        )

        existing_codes = region_area_codes.get(
            region_id
        )

        if existing_codes is None:
            region_area_codes[
                region_id
            ] = area_codes

        elif existing_codes != area_codes:
            raise ValueError(
                f"Inconsistent area_codes within {region_id}: "
                f"{existing_codes!r} vs {area_codes!r}"
            )

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            raise ValueError(
                f"Township {township_id} has empty geometry."
            )

        region_geometries[
            region_id
        ].append(
            geometry
        )

    geometry_township_ids = set(
        township_geometry_by_id
    )

    if seen_township_ids != geometry_township_ids:
        missing_assignments = sorted(
            geometry_township_ids
            - seen_township_ids
        )

        unknown_assignments = sorted(
            seen_township_ids
            - geometry_township_ids
        )

        raise ValueError(
            "Township assignment/geometry mismatch. "
            f"Missing assignments={missing_assignments}, "
            f"unknown assignments={unknown_assignments}"
        )

    actual_region_ids = set(
        region_geometries
    )

    if actual_region_ids != EXPECTED_REGION_IDS:
        missing_regions = sorted(
            EXPECTED_REGION_IDS
            - actual_region_ids
        )

        unexpected_regions = sorted(
            actual_region_ids
            - EXPECTED_REGION_IDS
        )

        raise ValueError(
            "Detailed region set does not match R01-R32. "
            f"Missing={missing_regions}, "
            f"unexpected={unexpected_regions}"
        )

    # -----------------------------------------------------------------------
    # First dissolve the verified R01-R32 regions.
    # -----------------------------------------------------------------------

    verified_regions: list[
        tuple[list[str], Any]
    ] = []

    for region_number in range(
        1,
        EXPECTED_DETAILED_REGION_COUNT + 1,
    ):
        region_id = f"R{region_number:02d}"

        geometry = dissolve_geometries(
            region_geometries[
                region_id
            ],
            feature_id=region_id,
        )

        verified_regions.append(
            (
                region_area_codes[
                    region_id
                ],
                geometry,
            )
        )

    # -----------------------------------------------------------------------
    # Then dissolve regions sharing the same COMPLETE detailed answer set.
    # -----------------------------------------------------------------------

    geometries_by_answer_set: dict[
        tuple[str, ...],
        list[Any],
    ] = defaultdict(
        list
    )

    for area_codes, geometry in verified_regions:
        key = answer_set_key(
            area_codes
        )

        geometries_by_answer_set[
            key
        ].append(
            geometry
        )

    features: list[
        dict[str, Any]
    ] = []

    for area_codes_tuple, geometries in geometries_by_answer_set.items():
        area_codes = list(
            area_codes_tuple
        )

        feature_id = make_feature_id(
            area_codes
        )

        geometry = dissolve_geometries(
            geometries,
            feature_id=feature_id,
        )

        prefix_1 = derive_prefix_1_from_detailed_codes(
            area_codes
        )

        prefix_2 = derive_prefix_2_from_detailed_codes(
            area_codes
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": feature_id,
                    "area_codes": area_codes,
                    "prefix_1": prefix_1,
                    "prefix_2": prefix_2,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    return features


# ---------------------------------------------------------------------------
# Prefix feature construction
# ---------------------------------------------------------------------------


def build_prefix_2_features(
    detailed_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Generate the 2-digit significant-prefix map.

    Geometry is dissolved by the COMPLETE prefix_2 answer set.

    Example:
        ["42", "43"]

    remains one multi-answer feature rather than becoming overlapping
    "42" and "43" features.
    """

    geometries_by_answer_set: dict[
        tuple[str, ...],
        list[Any],
    ] = defaultdict(
        list
    )

    for feature in detailed_features:
        properties = feature[
            "properties"
        ]

        prefix_2 = properties[
            "prefix_2"
        ]

        key = answer_set_key(
            prefix_2
        )

        geometries_by_answer_set[
            key
        ].append(
            shape(
                feature[
                    "geometry"
                ]
            )
        )

    features: list[
        dict[str, Any]
    ] = []

    for prefix_2_tuple, geometries in geometries_by_answer_set.items():
        area_codes = list(
            prefix_2_tuple
        )

        feature_id = make_feature_id(
            area_codes
        )

        geometry = dissolve_geometries(
            geometries,
            feature_id=feature_id,
        )

        prefix_1 = derive_prefix_1_from_prefix_2(
            area_codes
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": feature_id,
                    "area_codes": area_codes,
                    "prefix_1": prefix_1,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    return features


def build_prefix_1_features(
    detailed_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Generate the 1-digit significant-prefix map.

    Geometry is dissolved by the COMPLETE prefix_1 answer set.
    """

    geometries_by_answer_set: dict[
        tuple[str, ...],
        list[Any],
    ] = defaultdict(
        list
    )

    for feature in detailed_features:
        properties = feature[
            "properties"
        ]

        prefix_1 = properties[
            "prefix_1"
        ]

        key = answer_set_key(
            prefix_1
        )

        geometries_by_answer_set[
            key
        ].append(
            shape(
                feature[
                    "geometry"
                ]
            )
        )

    features: list[
        dict[str, Any]
    ] = []

    for prefix_1_tuple, geometries in geometries_by_answer_set.items():
        area_codes = list(
            prefix_1_tuple
        )

        feature_id = make_feature_id(
            area_codes
        )

        geometry = dissolve_geometries(
            geometries,
            feature_id=feature_id,
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": feature_id,
                    "area_codes": area_codes,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    return features


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------


def validate_feature_ids(
    features: list[dict[str, Any]],
    *,
    dataset_name: str,
) -> None:
    """Validate IDs, arrays, and duplicate answer sets."""

    ids: set[str] = set()

    for feature in features:
        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"{dataset_name} feature is missing properties."
            )

        feature_id = properties.get(
            "id"
        )

        area_codes = properties.get(
            "area_codes"
        )

        if not isinstance(
            area_codes,
            list,
        ) or not area_codes:
            raise ValueError(
                f"{dataset_name} feature has invalid area_codes."
            )

        expected_id = make_feature_id(
            area_codes
        )

        if feature_id != expected_id:
            raise ValueError(
                f"{dataset_name} feature ID {feature_id!r} does not "
                f"match answer set {area_codes!r}. Expected "
                f"{expected_id!r}."
            )

        if feature_id in ids:
            raise ValueError(
                f"{dataset_name} contains duplicate feature ID "
                f"{feature_id!r}."
            )

        ids.add(
            feature_id
        )


def validate_detailed_features(
    features: list[dict[str, Any]],
) -> None:
    """Validate the detailed area-code output."""

    validate_feature_ids(
        features,
        dataset_name="Detailed area-code dataset",
    )

    for feature in features:
        properties = feature[
            "properties"
        ]

        if not isinstance(
            properties.get(
                "prefix_1"
            ),
            list,
        ):
            raise ValueError(
                f"{properties['id']} prefix_1 is not an array."
            )

        if not isinstance(
            properties.get(
                "prefix_2"
            ),
            list,
        ):
            raise ValueError(
                f"{properties['id']} prefix_2 is not an array."
            )


def validate_prefix_2_features(
    features: list[dict[str, Any]],
) -> None:
    """Validate the 2-digit-prefix output."""

    validate_feature_ids(
        features,
        dataset_name="2-digit prefix dataset",
    )

    for feature in features:
        properties = feature[
            "properties"
        ]

        if not isinstance(
            properties.get(
                "prefix_1"
            ),
            list,
        ):
            raise ValueError(
                f"{properties['id']} prefix_1 is not an array."
            )


def validate_prefix_1_features(
    features: list[dict[str, Any]],
) -> None:
    """Validate the 1-digit-prefix output."""

    validate_feature_ids(
        features,
        dataset_name="1-digit prefix dataset",
    )


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------


def file_size_kb(
    path: Path,
) -> float:
    """Return a file's size in KiB."""

    return (
        path.stat().st_size
        / 1024
    )


def print_dataset_summary(
    label: str,
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    """Print a compact generated-dataset summary."""

    print(
        f"{label}:"
    )
    print(
        f"  Features: {len(features)}"
    )
    print(
        f"  Size:     {file_size_kb(path):.1f} KB"
    )
    print(
        f"  Output:   {path.relative_to(PROJECT_ROOT)}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Loading Taiwan townships..."
    )

    township_geojson = load_json(
        TOWNSHIPS_PATH
    )

    township_features = township_geojson.get(
        "features"
    )

    if not isinstance(
        township_features,
        list,
    ):
        raise ValueError(
            "Township GeoJSON does not contain a features array."
        )

    print(
        "Loading verified telephone-region assignments..."
    )

    assignment_data = load_json(
        ASSIGNMENTS_PATH
    )

    assignments = get_assignment_records(
        assignment_data
    )

    print()
    print(
        f"Township geometries:    {len(township_features)}"
    )
    print(
        f"Township assignments:   {len(assignments)}"
    )

    if len(
        township_features
    ) != EXPECTED_TOWNSHIP_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_TOWNSHIP_COUNT} township geometries, "
            f"found {len(township_features)}."
        )

    if len(
        assignments
    ) != EXPECTED_TOWNSHIP_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_TOWNSHIP_COUNT} township assignments, "
            f"found {len(assignments)}."
        )

    # -----------------------------------------------------------------------
    # Index township geometry
    # -----------------------------------------------------------------------

    township_geometry_by_id: dict[
        str,
        dict[str, Any],
    ] = {}

    for feature in township_features:
        township_id = get_township_id(
            feature
        )

        if township_id in township_geometry_by_id:
            raise ValueError(
                f"Duplicate township geometry ID: {township_id}"
            )

        geometry = feature.get(
            "geometry"
        )

        if geometry is None:
            raise ValueError(
                f"Township {township_id} has no geometry."
            )

        township_geometry_by_id[
            township_id
        ] = geometry

    # -----------------------------------------------------------------------
    # Generate all three quiz geometries
    # -----------------------------------------------------------------------

    print()
    print(
        "Generating detailed area-code regions..."
    )

    detailed_features = build_detailed_features(
        assignments,
        township_geometry_by_id,
    )

    print(
        "Generating 2-digit prefix regions..."
    )

    prefix_2_features = build_prefix_2_features(
        detailed_features
    )

    print(
        "Generating 1-digit prefix regions..."
    )

    prefix_1_features = build_prefix_1_features(
        detailed_features
    )

    # -----------------------------------------------------------------------
    # Validate generated datasets
    # -----------------------------------------------------------------------

    validate_detailed_features(
        detailed_features
    )

    validate_prefix_2_features(
        prefix_2_features
    )

    validate_prefix_1_features(
        prefix_1_features
    )

    # We know the source classification contains exactly 32 verified Rxx
    # regions. If two Rxx regions intentionally share an identical complete
    # answer set, the detailed output may contain fewer than 32 features
    # because this generator correctly dissolves by answer set.
    if len(
        detailed_features
    ) > EXPECTED_DETAILED_REGION_COUNT:
        raise ValueError(
            "Detailed generation unexpectedly produced more than "
            f"{EXPECTED_DETAILED_REGION_COUNT} features."
        )

    # -----------------------------------------------------------------------
    # Write public GeoJSON
    # -----------------------------------------------------------------------

    write_geojson(
        DETAILED_OUTPUT_PATH,
        detailed_features,
    )

    write_geojson(
        PREFIX_2_OUTPUT_PATH,
        prefix_2_features,
    )

    write_geojson(
        PREFIX_1_OUTPUT_PATH,
        prefix_1_features,
    )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    print()
    print(
        "Taiwan telephone-area-code GeoJSON generation complete."
    )
    print()

    print_dataset_summary(
        "Detailed area codes",
        DETAILED_OUTPUT_PATH,
        detailed_features,
    )

    print()

    print_dataset_summary(
        "2-digit prefixes",
        PREFIX_2_OUTPUT_PATH,
        prefix_2_features,
    )

    print()

    print_dataset_summary(
        "1-digit prefixes",
        PREFIX_1_OUTPUT_PATH,
        prefix_1_features,
    )


if __name__ == "__main__":
    main()