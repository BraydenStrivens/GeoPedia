"""
Process HelloQuiz Mexican phone-code boundaries into GeoPedia runtime GeoJSON.

Sources
-------
    data/raw/countries/mexico/helloquiz/phone-codes.geojson

    public/data/countries/mexico/geojson/states.geojson

The HelloQuiz source contains 399 geographic phone-code regions. Most regions
have one LADA code, while some use two-digit codes and the Mexico City region
contains multiple answers such as `55/56`.

The processed Mexico state GeoJSON is used to determine which states each
phone-code region meaningfully overlaps.

Outputs
-------
    public/data/countries/mexico/geojson/phone-codes.geojson

    public/data/countries/mexico/geojson/phone-code-prefixes.geojson

Full phone-code features contain:

    {
        "area_codes": ["55", "56"],
        "first_digit": "5",
        "state_ids": ["09"]
    }

`area_codes` is an array because GeoPedia supports multiple valid answers for
a single geographic feature. This allows codes such as 55 and 56 to remain
separate quiz questions while resolving to the same map feature.

`first_digit` supports grouping the full quiz by the first digit of the phone
code.

`state_ids` supports grouping the full quiz by Mexican state. A phone-code
region may belong to more than one state.

The 1-digit GeoJSON is derived from the full phone-code geometry by dissolving
all regions whose phone codes begin with the same digit.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from pyproj import CRS, Transformer
from shapely import make_valid, set_precision
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union
from shapely.validation import explain_validity


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "mexico"
    / "helloquiz"
    / "phone-codes.geojson"
)

STATES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "mexico"
    / "geojson"
    / "states.geojson"
)

PHONE_CODES_OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "mexico"
    / "geojson"
    / "phone-codes.geojson"
)

PHONE_PREFIXES_OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "mexico"
    / "geojson"
    / "phone-code-prefixes.geojson"
)


# ---------------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 399
EXPECTED_STATE_COUNT = 32

EXPECTED_STATE_IDS = {
    f"{state_id:02d}"
    for state_id in range(1, 33)
}

EXPECTED_PREFIXES = {
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
}

EXPECTED_MULTI_ANSWER_VALUES = {
    "55/56",
}


# ---------------------------------------------------------------------------
# Processing settings
# ---------------------------------------------------------------------------

COORDINATE_DECIMAL_PLACES = 6

WGS84 = CRS.from_epsg(4326)
MEXICO_METRIC_CRS = CRS.from_epsg(6372)

TO_METRIC = Transformer.from_crs(
    WGS84,
    MEXICO_METRIC_CRS,
    always_xy=True,
).transform


# ---------------------------------------------------------------------------
# State-overlap settings
# ---------------------------------------------------------------------------

# Ignore tiny absolute overlaps caused by boundary differences.
MIN_STATE_OVERLAP_KM2 = 1.0

# A state must contain at least 1% of the phone-code region.
MIN_STATE_OVERLAP_RATIO = 0.01

# A state's overlap must also be at least 15% as large as the region's
# largest state overlap. This removes tiny neighboring-state slivers while
# retaining genuinely multi-state phone-code regions.
MIN_RELATIVE_TO_LARGEST_OVERLAP = 0.15


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def keep_polygonal_geometry(
    geometry: BaseGeometry,
) -> Polygon | MultiPolygon:
    """
    Extract polygonal content from a geometry.

    Geometry repair and unions can produce GeometryCollections containing
    lines or points. GeoPedia only requires polygonal area, so non-polygonal
    components are discarded.
    """

    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            if isinstance(part, Polygon):
                polygons.append(part)

            elif isinstance(part, MultiPolygon):
                polygons.extend(part.geoms)

        if not polygons:
            raise ValueError(
                "GeometryCollection contains no polygonal geometry."
            )

        if len(polygons) == 1:
            return polygons[0]

        return MultiPolygon(polygons)

    raise ValueError(
        f"Expected polygonal geometry, found {geometry.geom_type}."
    )


def repair_geometry(
    geometry: BaseGeometry,
) -> Polygon | MultiPolygon:
    """
    Repair invalid geometry when necessary and return polygonal content.
    """

    if geometry.is_empty:
        raise ValueError("Encountered empty geometry.")

    if not geometry.is_valid:
        geometry = make_valid(geometry)

    polygonal = keep_polygonal_geometry(
        geometry
    )

    if polygonal.is_empty:
        raise ValueError(
            "Geometry became empty after repair."
        )

    if not polygonal.is_valid:
        raise ValueError(
            "Geometry remains invalid after repair: "
            f"{explain_validity(polygonal)}"
        )

    return polygonal


def normalize_multipolygon(
    geometry: Polygon | MultiPolygon,
) -> MultiPolygon:
    """
    Normalize polygonal geometry to MultiPolygon.
    """

    if isinstance(geometry, MultiPolygon):
        return geometry

    return MultiPolygon([geometry])

def geometry_to_geojson(
    geometry: Polygon | MultiPolygon,
) -> dict[str, Any]:
    """
    Convert polygonal geometry to GeoJSON using topology-safe precision.

    Shapely's set_precision() snaps coordinates to the requested grid while
    preserving valid polygon topology. This avoids invalid rings that can be
    created by independently rounding every coordinate with Python's round().
    """

    geometry = normalize_multipolygon(
        geometry
    )

    precision_grid_size = (
        10 ** -COORDINATE_DECIMAL_PLACES
    )

    geometry = set_precision(
        geometry,
        grid_size=precision_grid_size,
        mode="valid_output",
    )

    geometry = repair_geometry(
        geometry
    )

    geometry = normalize_multipolygon(
        geometry
    )

    mapped = mapping(
        geometry
    )

    return {
        "type": mapped["type"],
        "coordinates": mapped["coordinates"],
    }


def to_metric(
    geometry: BaseGeometry,
) -> Polygon | MultiPolygon:
    """
    Project WGS84 polygonal geometry into Mexico ITRF2008 / LCC.

    The projected result is repaired before use because reprojection can expose
    small topology defects that were not invalid in the original WGS84
    geometry. Returning validated polygonal geometry prevents GEOS topology
    errors during state-intersection calculations.
    """

    projected = transform(
        TO_METRIC,
        geometry,
    )

    return repair_geometry(
        projected
    )


# ---------------------------------------------------------------------------
# Phone-code helpers
# ---------------------------------------------------------------------------


def parse_area_codes(
    raw_value: Any,
) -> list[str]:
    """
    Convert a HelloQuiz AreaCode value into one or more distinct answers.

    Examples
    --------
        "248"   -> ["248"]
        "55/56" -> ["55", "56"]
    """

    if not isinstance(raw_value, str):
        raw_value = str(
            raw_value
        )

    raw_value = raw_value.strip()

    if not raw_value:
        raise ValueError(
            "Found empty AreaCode value."
        )

    codes = [
        part.strip()
        for part in raw_value.split("/")
    ]

    if any(
        not code
        for code in codes
    ):
        raise ValueError(
            f"Malformed AreaCode value {raw_value!r}."
        )

    if any(
        not code.isdigit()
        for code in codes
    ):
        raise ValueError(
            "AreaCode contains a non-numeric answer: "
            f"{raw_value!r}."
        )

    if len(set(codes)) != len(codes):
        raise ValueError(
            "AreaCode contains duplicate answers: "
            f"{raw_value!r}."
        )

    return codes


def create_feature_id(
    area_codes: list[str],
) -> str:
    """
    Create a stable feature ID from one or more phone-code answers.
    """

    return "/".join(
        area_codes
    )


def get_first_digit(
    area_codes: list[str],
) -> str:
    """
    Return the shared first digit for all answers belonging to one feature.
    """

    prefixes = {
        area_code[0]
        for area_code in area_codes
    }

    if len(prefixes) != 1:
        raise ValueError(
            "A multi-answer phone-code feature contains "
            f"different first digits: {area_codes}"
        )

    prefix = next(
        iter(prefixes)
    )

    if prefix not in EXPECTED_PREFIXES:
        raise ValueError(
            f"Unexpected phone-code prefix {prefix!r}."
        )

    return prefix


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------


def load_phone_code_features() -> list[dict[str, Any]]:
    """
    Load and structurally validate the HelloQuiz phone-code source.
    """

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            "Missing HelloQuiz Mexico phone-code GeoJSON:\n"
            f"  {SOURCE_PATH}"
        )

    with SOURCE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Phone-code source is not a FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(features, list):
        raise ValueError(
            "Phone-code source has no feature list."
        )

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected HelloQuiz feature count: "
            f"expected {EXPECTED_FEATURE_COUNT}, "
            f"found {len(features)}."
        )

    return features


def load_states() -> dict[str, Polygon | MultiPolygon]:
    """
    Load processed INEGI state geometry keyed by two-digit state ID.
    """

    if not STATES_PATH.exists():
        raise FileNotFoundError(
            "Missing processed Mexico state GeoJSON:\n"
            f"  {STATES_PATH}"
        )

    with STATES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Mexico states GeoJSON is not a FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(features, list):
        raise ValueError(
            "Mexico states GeoJSON has no feature list."
        )

    if len(features) != EXPECTED_STATE_COUNT:
        raise ValueError(
            "Unexpected Mexico state count: "
            f"expected {EXPECTED_STATE_COUNT}, "
            f"found {len(features)}."
        )

    states: dict[
        str,
        Polygon | MultiPolygon,
    ] = {}

    for feature in features:
        properties = feature.get(
            "properties"
        )

        if not isinstance(properties, dict):
            raise ValueError(
                "Mexico state feature has invalid properties."
            )

        state_id = properties.get(
            "state_id"
        )

        if not isinstance(state_id, str):
            raise ValueError(
                "Mexico state feature has invalid state_id."
            )

        if state_id in states:
            raise ValueError(
                f"Duplicate Mexico state ID {state_id!r}."
            )

        geometry_data = feature.get(
            "geometry"
        )

        if geometry_data is None:
            raise ValueError(
                f"Mexico state {state_id} has no geometry."
            )

        geometry = repair_geometry(
            shape(
                geometry_data
            )
        )

        states[state_id] = geometry

    if set(states) != EXPECTED_STATE_IDS:
        raise ValueError(
            "Unexpected Mexico state IDs.\n"
            f"Expected: {sorted(EXPECTED_STATE_IDS)}\n"
            f"Found: {sorted(states)}"
        )

    return states


# ---------------------------------------------------------------------------
# State assignment
# ---------------------------------------------------------------------------


def prepare_metric_states(
    states: dict[
        str,
        Polygon | MultiPolygon,
    ],
) -> dict[str, BaseGeometry]:
    """
    Project all state polygons once so repeated overlap checks are efficient.
    """

    return {
        state_id: to_metric(
            geometry
        )
        for state_id, geometry in states.items()
    }


def find_state_ids(
    phone_geometry: Polygon | MultiPolygon,
    metric_states: dict[
        str,
        BaseGeometry,
    ],
) -> tuple[
    list[str],
    list[tuple[str, float, float]],
]:
    """
    Determine which Mexican states meaningfully overlap a phone-code feature.

    A state is retained when either:

    - the overlap is at least MIN_STATE_OVERLAP_KM2, or
    - the overlap represents at least MIN_STATE_OVERLAP_RATIO of the
      phone-code feature's total area.

    The second condition protects legitimate cross-state portions of small
    phone-code regions, while the first prevents tiny boundary artifacts from
    assigning large regions to neighboring states.

    At least the state with the largest intersection is always retained.
    """

    metric_phone = to_metric(
        phone_geometry
    )

    phone_area_m2 = (
        metric_phone.area
    )

    if phone_area_m2 <= 0:
        raise ValueError(
            "Phone-code geometry has no measurable area."
        )

    overlaps: list[
        tuple[str, float, float]
    ] = []

    for (
        state_id,
        metric_state,
    ) in metric_states.items():
        if not metric_phone.intersects(
            metric_state
        ):
            continue

        intersection = (
            metric_phone.intersection(
                metric_state
            )
        )

        intersection_area_m2 = (
            intersection.area
        )

        if intersection_area_m2 <= 0:
            continue

        overlap_km2 = (
            intersection_area_m2
            / 1_000_000
        )

        overlap_ratio = (
            intersection_area_m2
            / phone_area_m2
        )

        overlaps.append(
            (
                state_id,
                overlap_km2,
                overlap_ratio,
            )
        )

    if not overlaps:
        raise ValueError(
            "Phone-code region does not overlap "
            "any Mexico state."
        )

    overlaps.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    largest_overlap_km2 = overlaps[0][1]

    selected = [
        state_id
        for (
            state_id,
            overlap_km2,
            overlap_ratio,
        ) in overlaps
        if (
            overlap_km2 >= MIN_STATE_OVERLAP_KM2
            and overlap_ratio >= MIN_STATE_OVERLAP_RATIO
            and overlap_km2
            >= largest_overlap_km2
            * MIN_RELATIVE_TO_LARGEST_OVERLAP
        )
    ]

    # Guarantee every phone-code feature belongs to at least one state.
    if not selected:
        selected = [
            overlaps[0][0]
        ]

    selected.sort(
        key=int
    )

    return (
        selected,
        overlaps,
    )


# ---------------------------------------------------------------------------
# Full phone-code processing
# ---------------------------------------------------------------------------


def process_phone_codes(
    source_features: list[dict[str, Any]],
    metric_states: dict[
        str,
        BaseGeometry,
    ],
) -> tuple[
    dict[str, Any],
    dict[str, list[Polygon | MultiPolygon]],
]:
    """
    Normalize phone-code features and derive grouping metadata.
    """

    output_features: list[
        dict[str, Any]
    ] = []

    geometries_by_prefix: dict[
        str,
        list[Polygon | MultiPolygon],
    ] = defaultdict(
        list
    )

    feature_ids: set[str] = set()
    individual_codes: set[str] = set()

    invalid_source_count = 0

    source_component_count = 0
    output_component_count = 0

    multi_answer_values: set[str] = set()

    state_feature_counts: dict[
        str,
        int,
    ] = defaultdict(
        int
    )

    multi_state_features: list[
        tuple[str, list[str]]
    ] = []

    for index, source_feature in enumerate(
        source_features,
        start=1,
    ):
        properties = source_feature.get(
            "properties"
        )

        if not isinstance(properties, dict):
            raise ValueError(
                "Source phone-code feature has invalid properties."
            )

        raw_area_code = properties.get(
            "AreaCode"
        )

        area_codes = parse_area_codes(
            raw_area_code
        )

        feature_id = create_feature_id(
            area_codes
        )

        if feature_id in feature_ids:
            raise ValueError(
                f"Duplicate feature ID {feature_id!r}."
            )

        feature_ids.add(
            feature_id
        )

        for area_code in area_codes:
            if area_code in individual_codes:
                raise ValueError(
                    "Phone code appears in multiple "
                    f"source features: {area_code}"
                )

            individual_codes.add(
                area_code
            )

        if len(area_codes) > 1:
            multi_answer_values.add(
                feature_id
            )

        first_digit = get_first_digit(
            area_codes
        )

        geometry_data = source_feature.get(
            "geometry"
        )

        if geometry_data is None:
            raise ValueError(
                f"Feature {feature_id} has no geometry."
            )

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            raise ValueError(
                f"Feature {feature_id} has empty geometry."
            )

        if isinstance(
            geometry,
            MultiPolygon,
        ):
            source_component_count += len(
                geometry.geoms
            )

        elif isinstance(
            geometry,
            Polygon,
        ):
            source_component_count += 1

        else:
            raise ValueError(
                f"Feature {feature_id} has unsupported "
                f"geometry type {geometry.geom_type}."
            )

        if not geometry.is_valid:
            invalid_source_count += 1

            print(
                f"  Repairing {feature_id}: "
                f"{explain_validity(geometry)}"
            )

        processed_geometry = repair_geometry(
            geometry
        )

        processed_geometry = (
            normalize_multipolygon(
                processed_geometry
            )
        )

        output_component_count += len(
            processed_geometry.geoms
        )

        (
            state_ids,
            state_overlaps,
        ) = find_state_ids(
            processed_geometry,
            metric_states,
        )

        for state_id in state_ids:
            state_feature_counts[
                state_id
            ] += 1

        if len(state_ids) > 1:
            multi_state_features.append(
                (
                    feature_id,
                    state_ids,
                )
            )

        geometries_by_prefix[
            first_digit
        ].append(
            processed_geometry
        )

        output_features.append(
            {
                "type": "Feature",
                "id": feature_id,
                "properties": {
                    "phone_code_id": feature_id,
                    "area_codes": area_codes,
                    "first_digit": first_digit,
                    "state_ids": state_ids,
                },
                "geometry": geometry_to_geojson(
                    processed_geometry
                ),
            }
        )

        if index % 50 == 0:
            print(
                f"  Processed {index:,} / "
                f"{len(source_features):,} regions..."
            )

    if (
        multi_answer_values
        != EXPECTED_MULTI_ANSWER_VALUES
    ):
        raise ValueError(
            "Unexpected multi-answer feature set.\n"
            f"Expected: "
            f"{sorted(EXPECTED_MULTI_ANSWER_VALUES)}\n"
            f"Found: "
            f"{sorted(multi_answer_values)}"
        )

    if (
        set(geometries_by_prefix)
        != EXPECTED_PREFIXES
    ):
        raise ValueError(
            "Unexpected 1-digit prefix set.\n"
            f"Expected: {sorted(EXPECTED_PREFIXES)}\n"
            f"Found: "
            f"{sorted(geometries_by_prefix)}"
        )

    missing_states = (
        EXPECTED_STATE_IDS
        - set(state_feature_counts)
    )

    if missing_states:
        raise ValueError(
            "Some Mexico states received no phone-code regions:\n"
            f"  {sorted(missing_states)}"
        )

    output_features.sort(
        key=lambda feature: tuple(
            int(code)
            for code in feature[
                "properties"
            ]["area_codes"]
        )
    )

    print()
    print(
        f"✓ Processed "
        f"{len(output_features):,} "
        "phone-code regions."
    )

    print(
        f"✓ Found "
        f"{len(individual_codes):,} "
        "distinct quiz answers."
    )

    print(
        f"✓ Repaired "
        f"{invalid_source_count:,} "
        "invalid source geometries."
    )

    print(
        "✓ Polygon components: "
        f"{source_component_count:,} → "
        f"{output_component_count:,}."
    )

    print(
        "✓ Multi-answer features: "
        + ", ".join(
            sorted(
                multi_answer_values
            )
        )
    )

    print(
        f"✓ {len(multi_state_features):,} "
        "phone-code regions span multiple states."
    )

    if multi_state_features:
        print()
        print(
            "Multi-state phone-code regions:"
        )

        for (
            feature_id,
            state_ids,
        ) in multi_state_features:
            print(
                f"  {feature_id}: "
                f"{', '.join(state_ids)}"
            )

    print()
    print(
        "Phone-code regions by state:"
    )

    for state_id in sorted(
        state_feature_counts,
        key=int,
    ):
        print(
            f"  {state_id}: "
            f"{state_feature_counts[state_id]:,}"
        )

    return (
        {
            "type": "FeatureCollection",
            "features": output_features,
        },
        geometries_by_prefix,
    )


# ---------------------------------------------------------------------------
# 1-digit prefix processing
# ---------------------------------------------------------------------------


def process_phone_code_prefixes(
    geometries_by_prefix: dict[
        str,
        list[Polygon | MultiPolygon],
    ],
) -> dict[str, Any]:
    """
    Dissolve full phone-code regions into eight 1-digit prefix features.
    """

    features: list[
        dict[str, Any]
    ] = []

    for prefix in sorted(
        EXPECTED_PREFIXES,
        key=int,
    ):
        geometries = (
            geometries_by_prefix[
                prefix
            ]
        )

        dissolved = unary_union(
            geometries
        )

        dissolved = repair_geometry(
            dissolved
        )

        dissolved = normalize_multipolygon(
            dissolved
        )

        features.append(
            {
                "type": "Feature",
                "id": prefix,
                "properties": {
                    "prefix": prefix,
                },
                "geometry": geometry_to_geojson(
                    dissolved
                ),
            }
        )

        print(
            f"  Prefix {prefix}: "
            f"{len(geometries):,} "
            "phone-code regions → "
            f"{len(dissolved.geoms):,} "
            "polygon components"
        )

    if len(features) != len(
        EXPECTED_PREFIXES
    ):
        raise ValueError(
            "Unexpected generated prefix feature count."
        )

    print()
    print(
        f"✓ Generated "
        f"{len(features)} "
        "1-digit phone-code regions."
    )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------


def validate_phone_codes(
    feature_collection: dict[
        str,
        Any,
    ],
) -> None:
    """
    Validate the final full phone-code runtime GeoJSON.
    """

    features = feature_collection.get(
        "features"
    )

    if not isinstance(features, list):
        raise ValueError(
            "Generated phone-code GeoJSON "
            "has no feature list."
        )

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected generated phone-code "
            f"feature count: {len(features)}."
        )

    feature_ids: set[str] = set()
    answers: set[str] = set()

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
                "Generated phone-code feature "
                "has invalid ID."
            )

        if feature_id in feature_ids:
            raise ValueError(
                "Duplicate generated feature ID "
                f"{feature_id!r}."
            )

        feature_ids.add(
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
                f"Feature {feature_id} "
                "has invalid properties."
            )
            
        phone_code_id = properties.get(
            "phone_code_id"
        )

        if phone_code_id != feature_id:
            raise ValueError(
                f"Feature {feature_id} has mismatched "
                f"phone_code_id {phone_code_id!r}."
            )

        expected_properties = {
            "phone_code_id",
            "area_codes",
            "first_digit",
            "state_ids",
        }

        if (
            set(properties)
            != expected_properties
        ):
            raise ValueError(
                f"Feature {feature_id} "
                "contains unexpected properties: "
                f"{sorted(properties)}"
            )

        area_codes = properties[
            "area_codes"
        ]

        if (
            not isinstance(
                area_codes,
                list,
            )
            or not area_codes
        ):
            raise ValueError(
                f"Feature {feature_id} "
                "has invalid area_codes."
            )

        for area_code in area_codes:
            if area_code in answers:
                raise ValueError(
                    "Phone-code answer appears "
                    "in multiple generated features: "
                    f"{area_code}"
                )

            answers.add(
                area_code
            )

        first_digit = properties[
            "first_digit"
        ]

        if first_digit not in EXPECTED_PREFIXES:
            raise ValueError(
                f"Feature {feature_id} has "
                "invalid first_digit."
            )

        if any(
            code[0] != first_digit
            for code in area_codes
        ):
            raise ValueError(
                f"Feature {feature_id} has "
                "inconsistent first_digit."
            )

        state_ids = properties[
            "state_ids"
        ]

        if (
            not isinstance(
                state_ids,
                list,
            )
            or not state_ids
        ):
            raise ValueError(
                f"Feature {feature_id} "
                "has no state assignments."
            )

        if (
            len(state_ids)
            != len(set(state_ids))
        ):
            raise ValueError(
                f"Feature {feature_id} "
                "has duplicate state IDs."
            )

        invalid_state_ids = (
            set(state_ids)
            - EXPECTED_STATE_IDS
        )

        if invalid_state_ids:
            raise ValueError(
                f"Feature {feature_id} "
                "has invalid state IDs: "
                f"{sorted(invalid_state_ids)}"
            )

        geometry = shape(
            feature["geometry"]
        )

        if geometry.is_empty:
            raise ValueError(
                f"Feature {feature_id} "
                "has empty geometry."
            )

        if not isinstance(
            geometry,
            (Polygon, MultiPolygon),
        ):
            raise ValueError(
                f"Feature {feature_id} "
                "has invalid geometry type "
                f"{geometry.geom_type}."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Feature {feature_id} "
                "has invalid final geometry: "
                f"{explain_validity(geometry)}"
            )

    print(
        f"✓ Validated "
        f"{len(features):,} full-code features "
        f"and {len(answers):,} distinct answers."
    )


def validate_prefixes(
    feature_collection: dict[
        str,
        Any,
    ],
) -> None:
    """
    Validate the final 1-digit phone-code runtime GeoJSON.
    """

    features = feature_collection.get(
        "features"
    )

    if not isinstance(features, list):
        raise ValueError(
            "Generated prefix GeoJSON "
            "has no feature list."
        )

    if len(features) != len(
        EXPECTED_PREFIXES
    ):
        raise ValueError(
            "Unexpected generated prefix "
            f"feature count: {len(features)}."
        )

    prefixes: set[str] = set()

    for feature in features:
        feature_id = feature.get(
            "id"
        )

        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"Prefix feature {feature_id} "
                "has invalid properties."
            )

        if set(properties) != {
            "prefix"
        }:
            raise ValueError(
                f"Prefix feature {feature_id} "
                "contains unexpected properties."
            )

        prefix = properties[
            "prefix"
        ]

        if prefix != feature_id:
            raise ValueError(
                f"Prefix feature {feature_id} "
                "has mismatched prefix property."
            )

        prefixes.add(
            prefix
        )

        geometry = shape(
            feature["geometry"]
        )

        if geometry.is_empty:
            raise ValueError(
                f"Prefix {prefix} "
                "has empty geometry."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Prefix {prefix} "
                "has invalid final geometry: "
                f"{explain_validity(geometry)}"
            )

    if prefixes != EXPECTED_PREFIXES:
        raise ValueError(
            "Generated prefix set does not "
            "match expected prefixes."
        )

    print(
        "✓ Validated all eight "
        "1-digit prefix features."
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_geojson(
    path: Path,
    feature_collection: dict[
        str,
        Any,
    ],
) -> None:
    """
    Write compact UTF-8 GeoJSON and report the resulting file size.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            feature_collection,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    size_bytes = (
        path.stat().st_size
    )

    size_kb = (
        size_bytes
        / 1024
    )

    size_mb = (
        size_kb
        / 1024
    )

    print("✓ Saved:")
    print(
        f"  {path}"
    )
    print(
        f"  {size_kb:,.0f} KB "
        f"({size_mb:.2f} MB)"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Generate Mexico full-code and 1-digit phone-code runtime GeoJSON.
    """

    print(
        "Mexico phone-code processor"
    )
    print(
        "---------------------------"
    )

    print(
        f"Phone-code source: "
        f"{SOURCE_PATH}"
    )

    print(
        f"State source: "
        f"{STATES_PATH}"
    )

    print()

    source_features = (
        load_phone_code_features()
    )

    print(
        f"✓ Loaded exactly "
        f"{len(source_features):,} "
        "HelloQuiz phone-code regions."
    )

    states = load_states()

    print(
        f"✓ Loaded exactly "
        f"{len(states):,} "
        "INEGI state regions."
    )

    print()
    print(
        "Projecting state geometry..."
    )

    metric_states = (
        prepare_metric_states(
            states
        )
    )

    print(
        "✓ State geometry ready."
    )

    print()
    print(
        "Processing full phone-code regions..."
    )

    (
        phone_codes,
        geometries_by_prefix,
    ) = process_phone_codes(
        source_features,
        metric_states,
    )

    print()
    print(
        "Generating 1-digit regions..."
    )

    phone_prefixes = (
        process_phone_code_prefixes(
            geometries_by_prefix
        )
    )

    print()
    print(
        "Validating generated GeoJSON..."
    )

    validate_phone_codes(
        phone_codes
    )

    validate_prefixes(
        phone_prefixes
    )

    print()
    print(
        "Writing runtime files..."
    )

    write_geojson(
        PHONE_CODES_OUTPUT_PATH,
        phone_codes,
    )

    write_geojson(
        PHONE_PREFIXES_OUTPUT_PATH,
        phone_prefixes,
    )

    print()
    print(
        "✓ Mexico phone-code processing complete."
    )


if __name__ == "__main__":
    main()