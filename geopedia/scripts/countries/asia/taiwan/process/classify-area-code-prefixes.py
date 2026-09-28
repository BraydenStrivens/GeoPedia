"""
Classify Taiwan townships by broad telephone area-code prefix.

Sources
-------
data/raw/countries/taiwan/area-codes/plonkit-area-codes.webp

data/intermediate/countries/taiwan/townships.geojson

Outputs
-------
data/intermediate/countries/taiwan/area-codes/
    township-prefix-classification.json

data/intermediate/countries/taiwan/area-codes/
    broad-prefix-classification.png

Purpose
-------
The Plonk It Taiwan telephone map uses different fill colors for its
detailed telephone regions such as:

    032, 033, 034, ...
    0425, 047, 049, ...
    052, 053, ...
    062, 063, ...
    07
    087, 088, 089

For the first stage of GeoPedia's telephone-area-code processing, those
detailed regions are collapsed into seven broad prefixes:

    02
    03
    04
    05
    06
    07
    08

The Plonk It source colors are used ONLY as classification evidence.

They have no relationship to the colors used in the generated diagnostic
image.

Pipeline
--------
    Plonk It raster pixel
        ->
    exact/nearest Plonk It fill color
        ->
    broad telephone prefix
        ->
    majority vote for each MOI township
        ->
    adjacency recovery
        ->
    manually verified overrides
        ->
    opaque diagnostic image

The diagnostic image uses one fixed GeoPedia color for each broad prefix:

    02 = red
    03 = yellow
    04 = blue
    05 = purple
    06 = orange
    07 = pink
    08 = green

White means that a township remains unresolved.

The diagnostic is intentionally rendered on a clean white background.
The original Plonk It raster is NOT used as the background, preventing
its detailed-region colors from bleeding through the GeoPedia colors.

Offshore Kinmen, Penghu, and Lienchiang townships are excluded from this
main-island classifier because the Plonk It source displays them as
separately scaled insets. They will be assigned explicitly when the
detailed area-code geometry is generated.

Run from the GeoPedia project root:

    python scripts/countries/taiwan/process/classify-area-code-prefixes.py

Requires:
    pillow
    shapely
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw
from shapely.geometry import Point, shape
from shapely.prepared import prep
from shapely.strtree import STRtree


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]

PLONKIT_PATH = (
    ROOT
    / "data"
    / "raw"
    / "countries"
    / "taiwan"
    / "plonkit-area-codes.webp"
)

TOWNSHIPS_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "townships.geojson"
)

CLASSIFICATION_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "township-prefix-classification.json"
)

DIAGNOSTIC_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "broad-prefix-classification.png"
)


# ---------------------------------------------------------------------------
# Locked Taiwan-proper calibration
# ---------------------------------------------------------------------------
#
# These are the same geographic/pixel bounds used by the georeferenced
# Plonk It township overlay.
# ---------------------------------------------------------------------------

MAINLAND_GEO_BOUNDS = (
    120.00,
    21.85,
    122.05,
    25.35,
)

MAINLAND_PIXEL_BOUNDS = (
    257,
    25,
    968,
    1391,
)


# ---------------------------------------------------------------------------
# Taiwan-proper counties
# ---------------------------------------------------------------------------

MAINLAND_COUNTY_IDS = {
    "TWN.2.1_1",   # Kaohsiung
    "TWN.3.1_1",   # New Taipei
    "TWN.4.1_1",   # Taichung
    "TWN.5.1_1",   # Tainan
    "TWN.6.1_1",   # Taipei
    "TWN.7.1_1",   # Changhua
    "TWN.7.2_1",   # Chiayi City
    "TWN.7.3_1",   # Chiayi County
    "TWN.7.4_1",   # Hsinchu City
    "TWN.7.5_1",   # Hsinchu County
    "TWN.7.6_1",   # Hualien
    "TWN.7.7_1",   # Keelung
    "TWN.7.8_1",   # Miaoli
    "TWN.7.9_1",   # Nantou
    "TWN.7.11_1",  # Pingtung
    "TWN.7.12_1",  # Taitung
    "TWN.7.13_1",  # Taoyuan
    "TWN.7.14_1",  # Yilan
    "TWN.7.15_1",  # Yunlin
}


# ---------------------------------------------------------------------------
# Plonk It source palette
# ---------------------------------------------------------------------------
#
# These RGB values were measured directly from the actual
# plonkit-area-codes.webp source image.
#
# IMPORTANT:
#
# These are SOURCE colors only.
#
# They are used to determine which broad telephone prefix a raster pixel
# belongs to. They are NOT used to render the diagnostic image.
#
# Several different colors intentionally collapse into the same broad prefix
# because Plonk It distinguishes detailed telephone regions while this stage
# of GeoPedia only needs 02-08.
# ---------------------------------------------------------------------------

PLONKIT_COLOR_TO_PREFIX = {
    # -----------------------------------------------------------------------
    # 02
    # -----------------------------------------------------------------------

    (255, 127, 127): "02",

    # -----------------------------------------------------------------------
    # 03
    #
    # Includes the detailed 032-039 family.
    # -----------------------------------------------------------------------

    (255, 179, 127): "03",
    (229, 159, 114): "03",

    (218, 255, 126): "03",
    (165, 254, 126): "03",
    (254, 233, 126): "03",

    # -----------------------------------------------------------------------
    # 04
    #
    # Includes 042x, 043, 047, 048, 049.
    # -----------------------------------------------------------------------

    (114, 229, 126): "04",
    (127, 186, 230): "04",
    (127, 255, 255): "04",

    # -----------------------------------------------------------------------
    # 05
    #
    # Includes 052, 053, 055, 056, 057.
    # -----------------------------------------------------------------------

    (146, 163, 255): "05",
    (187, 174, 228): "05",
    (199, 180, 255): "05",

    # -----------------------------------------------------------------------
    # 06
    #
    # Includes 062, 063, 065, 066, 067.
    # -----------------------------------------------------------------------

    (205, 162, 229): "06",
    (229, 181, 254): "06",

    # -----------------------------------------------------------------------
    # 07
    # -----------------------------------------------------------------------

    (255, 205, 249): "07",

    # -----------------------------------------------------------------------
    # 08
    #
    # Includes 087, 088, 089.
    # -----------------------------------------------------------------------

    (254, 186, 216): "08",
    (255, 158, 200): "08",
    (255, 178, 179): "08",

    # 038 uses this source color, so it belongs to 03 rather than 08.
    (128, 255, 199): "03",
}


# ---------------------------------------------------------------------------
# Plonk It source-color aliases
# ---------------------------------------------------------------------------
#
# WebP compression produces small RGB variations around otherwise uniform
# fills. These aliases are particularly common variants visible in the
# source image.
#
# The nearest-color classifier below handles most compression variation
# automatically, but keeping major aliases here improves transparency and
# makes the measured palette easier to audit.
# ---------------------------------------------------------------------------

PLONKIT_COLOR_ALIASES = {
    (255, 128, 128): "02",
}


# ---------------------------------------------------------------------------
# Classification settings
# ---------------------------------------------------------------------------

# Maximum Euclidean RGB distance from a known Plonk It fill color.
#
# This should remain fairly strict. Text, borders, white background, and
# anti-aliased labels should be ignored rather than forced into a prefix.
COLOR_DISTANCE_LIMIT = 18.0

# Sample every N raster pixels inside each township.
SAMPLE_STEP = 3

# Ignore pixels very close to township boundaries. This reduces contamination
# from Plonk It boundary lines and slight georeferencing mismatch.
BOUNDARY_INSET_PIXELS = 2.0

# Minimum number of recognized source pixels required for direct
# classification.
MIN_VALID_SAMPLES = 8

# Minimum winning-prefix fraction for direct raster classification.
MIN_CONFIDENCE = 0.60


# ---------------------------------------------------------------------------
# Neighbor recovery settings
# ---------------------------------------------------------------------------

MIN_MAJORITY_NEIGHBORS = 3

NEIGHBOR_MAJORITY_THRESHOLD = 0.75

PIXEL_SUPPORT_THRESHOLD = 0.30

MIN_SHARED_BOUNDARY_LENGTH = 1e-8


# ---------------------------------------------------------------------------
# Manually verified broad-prefix overrides
# ---------------------------------------------------------------------------
#
# These use stable MOI township IDs, never temporary diagnostic numbers.
#
# The first group contains the manually checked difficult townships from the
# earlier georeferenced-overlay inspection.
#
# Dajia District was subsequently identified as diagnostic township 218 and
# manually verified as belonging to 04 rather than 03.
# ---------------------------------------------------------------------------

MANUAL_PREFIX_OVERRIDES = {
    # Taichung
    "66000220": "04",  # Da'an District
    "66000210": "04",  # Waipu District
    "66000110": "04",  # Dajia District — diagnostic #218

    # Yunlin
    "10009080": "05",  # Dabi Township
    "10009020": "05",  # Dounan Township
    "10009170": "05",  # Yuanchang Township

    # Kaohsiung
    "64000250": "07",  # Hunei District
    "64000260": "07",  # Qieding District

    # Pingtung
    "10013180": "08",  # Kanding Township
    "10013220": "08",  # Liuqiu Township

    # Taitung
    "10014110": "08",  # Ludao Township

    # Taoyuan
    "68000080": "03",  # Bade District
    "68000030": "03",  # Daxi District
    "68000130": "03",  # Fuxing District
    "68000050": "03",  # Luzhu District
    "68000010": "03",  # Taoyuan District
    
    # New Taipei
    "65000080": "03",  # Yingge District — diagnostic #178

    # Tainan
    "67000170": "06",  # Beimen District — diagnostic #247
    "67000270": "06",  # Rende District — diagnostic #265
    "67000330": "06",  # South District — diagnostic #268

    # Yunlin
    "10009150": "05",  # Baozhong Township — diagnostic #333
    "10009140": "05",  # Dongshi Township — diagnostic #337
    "10009120": "05",  # Lunbei Township — diagnostic #345
    "10009160": "05",  # Taixi Township — diagnostic #349
}


# ---------------------------------------------------------------------------
# Diagnostic palette
# ---------------------------------------------------------------------------
#
# These are GeoPedia DEVELOPMENT colors.
#
# They are intentionally unrelated to the Plonk It source colors.
#
# All colors are fully opaque.
# ---------------------------------------------------------------------------

DIAGNOSTIC_COLORS = {
    "02": (230, 50, 50, 255),       # red
    "03": (245, 210, 35, 255),      # yellow
    "04": (35, 135, 245, 255),      # blue
    "05": (130, 45, 230, 255),      # purple
    "06": (245, 135, 30, 255),      # orange
    "07": (245, 45, 175, 255),      # pink
    "08": (35, 190, 85, 255),       # green
}

UNRESOLVED_COLOR = (
    255,
    255,
    255,
    255,
)

OUTLINE_COLOR = (
    0,
    0,
    0,
    255,
)


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing source file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_geojson(path: Path) -> dict:
    data = load_json(
        path
    )

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
            f"{path} does not contain a valid features array."
        )

    return data


# ---------------------------------------------------------------------------
# Coordinate transforms
# ---------------------------------------------------------------------------

def lon_lat_to_pixel(
    longitude: float,
    latitude: float,
) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = MAINLAND_GEO_BOUNDS
    left, top, right, bottom = MAINLAND_PIXEL_BOUNDS

    x_fraction = (
        (longitude - min_lon)
        / (max_lon - min_lon)
    )

    y_fraction = (
        (max_lat - latitude)
        / (max_lat - min_lat)
    )

    x = left + x_fraction * (
        right - left
    )

    y = top + y_fraction * (
        bottom - top
    )

    return x, y


def pixel_to_lon_lat(
    x: float,
    y: float,
) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = MAINLAND_GEO_BOUNDS
    left, top, right, bottom = MAINLAND_PIXEL_BOUNDS

    x_fraction = (
        (x - left)
        / (right - left)
    )

    y_fraction = (
        (y - top)
        / (bottom - top)
    )

    longitude = min_lon + x_fraction * (
        max_lon - min_lon
    )

    latitude = max_lat - y_fraction * (
        max_lat - min_lat
    )

    return longitude, latitude


def transform_geometry_to_pixel_polygons(
    geometry: dict,
) -> list[list[tuple[float, float]]]:
    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates"
    )

    if geometry_type == "Polygon":
        source_polygons = [
            coordinates
        ]

    elif geometry_type == "MultiPolygon":
        source_polygons = coordinates

    else:
        raise ValueError(
            f"Unexpected geometry type: {geometry_type!r}"
        )

    polygons: list[
        list[tuple[float, float]]
    ] = []

    for polygon in source_polygons:
        exterior = polygon[0]

        polygons.append(
            [
                lon_lat_to_pixel(
                    coordinate[0],
                    coordinate[1],
                )
                for coordinate in exterior
            ]
        )

    return polygons


# ---------------------------------------------------------------------------
# Source-color classification
# ---------------------------------------------------------------------------

SOURCE_PALETTE = {
    **PLONKIT_COLOR_TO_PREFIX,
    **PLONKIT_COLOR_ALIASES,
}


def color_distance(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
) -> float:
    return math.sqrt(
        (
            first[0] - second[0]
        ) ** 2
        + (
            first[1] - second[1]
        ) ** 2
        + (
            first[2] - second[2]
        ) ** 2
    )


def classify_source_color(
    color: tuple[int, int, int],
) -> str | None:
    """
    Convert one Plonk It raster color into a broad telephone prefix.

    Exact measured colors are checked first.

    If no exact match exists, the closest measured source color is accepted
    only when it falls within COLOR_DISTANCE_LIMIT.

    This accommodates minor WebP compression differences without allowing
    text, borders, or the white background to become telephone regions.
    """

    exact = SOURCE_PALETTE.get(
        color
    )

    if exact is not None:
        return exact

    best_prefix: str | None = None
    best_distance = float(
        "inf"
    )

    for reference_color, prefix in SOURCE_PALETTE.items():
        distance = color_distance(
            color,
            reference_color,
        )

        if distance < best_distance:
            best_distance = distance
            best_prefix = prefix

    if best_distance > COLOR_DISTANCE_LIMIT:
        return None

    return best_prefix


# ---------------------------------------------------------------------------
# Township raster classification
# ---------------------------------------------------------------------------

def classify_township(
    image: Image.Image,
    feature: dict,
) -> tuple[
    str | None,
    float,
    int,
    dict[str, int],
]:
    """
    Determine a township's broad prefix from Plonk It raster samples.

    Returns:
        winning prefix or None
        winning-prefix confidence
        number of recognized samples
        vote counts by prefix
    """

    geometry_data = feature.get(
        "geometry"
    )

    if geometry_data is None:
        raise ValueError(
            "Township has no geometry."
        )

    geographic_geometry = shape(
        geometry_data
    )

    if geographic_geometry.is_empty:
        raise ValueError(
            "Township has empty geometry."
        )

    prepared_geometry = prep(
        geographic_geometry
    )

    pixel_polygons = transform_geometry_to_pixel_polygons(
        geometry_data
    )

    all_x = [
        x
        for polygon in pixel_polygons
        for x, _ in polygon
    ]

    all_y = [
        y
        for polygon in pixel_polygons
        for _, y in polygon
    ]

    min_x = max(
        0,
        int(
            math.floor(
                min(all_x)
            )
        ),
    )

    max_x = min(
        image.width - 1,
        int(
            math.ceil(
                max(all_x)
            )
        ),
    )

    min_y = max(
        0,
        int(
            math.floor(
                min(all_y)
            )
        ),
    )

    max_y = min(
        image.height - 1,
        int(
            math.ceil(
                max(all_y)
            )
        ),
    )

    lon_per_pixel = (
        MAINLAND_GEO_BOUNDS[2]
        - MAINLAND_GEO_BOUNDS[0]
    ) / (
        MAINLAND_PIXEL_BOUNDS[2]
        - MAINLAND_PIXEL_BOUNDS[0]
    )

    lat_per_pixel = (
        MAINLAND_GEO_BOUNDS[3]
        - MAINLAND_GEO_BOUNDS[1]
    ) / (
        MAINLAND_PIXEL_BOUNDS[3]
        - MAINLAND_PIXEL_BOUNDS[1]
    )

    boundary_inset_degrees = (
        max(
            lon_per_pixel,
            lat_per_pixel,
        )
        * BOUNDARY_INSET_PIXELS
    )

    votes: Counter[str] = Counter()

    for y in range(
        min_y,
        max_y + 1,
        SAMPLE_STEP,
    ):
        for x in range(
            min_x,
            max_x + 1,
            SAMPLE_STEP,
        ):
            longitude, latitude = pixel_to_lon_lat(
                x + 0.5,
                y + 0.5,
            )

            point = Point(
                longitude,
                latitude,
            )

            if not prepared_geometry.contains(
                point
            ):
                continue

            if geographic_geometry.boundary.distance(
                point
            ) < boundary_inset_degrees:
                continue

            source_color = image.getpixel(
                (x, y)
            )

            prefix = classify_source_color(
                source_color
            )

            if prefix is None:
                continue

            votes[
                prefix
            ] += 1

    valid_samples = sum(
        votes.values()
    )

    if valid_samples < MIN_VALID_SAMPLES:
        return (
            None,
            0.0,
            valid_samples,
            dict(votes),
        )

    winning_prefix, winning_votes = (
        votes.most_common(
            1
        )[0]
    )

    confidence = (
        winning_votes
        / valid_samples
    )

    if confidence < MIN_CONFIDENCE:
        return (
            None,
            confidence,
            valid_samples,
            dict(votes),
        )

    return (
        winning_prefix,
        confidence,
        valid_samples,
        dict(votes),
    )


# ---------------------------------------------------------------------------
# Township adjacency
# ---------------------------------------------------------------------------

def build_adjacency(
    mainland_features: list[dict],
) -> dict[str, set[str]]:
    township_ids: list[str] = []
    geometries = []

    for feature in mainland_features:
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties.get(
            "township_id"
        )

        if not township_id:
            raise ValueError(
                "Township feature is missing township_id."
            )

        township_ids.append(
            township_id
        )

        geometries.append(
            shape(
                feature[
                    "geometry"
                ]
            )
        )

    tree = STRtree(
        geometries
    )

    adjacency = {
        township_id: set()
        for township_id in township_ids
    }

    for index, geometry in enumerate(
        geometries
    ):
        township_id = township_ids[
            index
        ]

        candidate_indices = tree.query(
            geometry
        )

        for candidate_index in candidate_indices:
            candidate_index = int(
                candidate_index
            )

            if candidate_index == index:
                continue

            other_id = township_ids[
                candidate_index
            ]

            if other_id in adjacency[
                township_id
            ]:
                continue

            other_geometry = geometries[
                candidate_index
            ]

            shared_boundary = (
                geometry.boundary.intersection(
                    other_geometry.boundary
                )
            )

            if (
                not shared_boundary.is_empty
                and shared_boundary.length
                > MIN_SHARED_BOUNDARY_LENGTH
            ):
                adjacency[
                    township_id
                ].add(
                    other_id
                )

                adjacency[
                    other_id
                ].add(
                    township_id
                )

    return adjacency


# ---------------------------------------------------------------------------
# Neighbor recovery
# ---------------------------------------------------------------------------

def pixel_support_for_prefix(
    result: dict,
    prefix: str,
) -> float:
    votes = result.get(
        "votes",
        {}
    )

    total = sum(
        votes.values()
    )

    if total == 0:
        return 0.0

    return (
        votes.get(
            prefix,
            0,
        )
        / total
    )


def recover_from_neighbors(
    results_by_id: dict[str, dict],
    adjacency: dict[str, set[str]],
) -> int:
    total_recovered = 0
    iteration = 0

    while True:
        iteration += 1

        proposed: dict[
            str,
            tuple[str, str, float],
        ] = {}

        for township_id, result in results_by_id.items():
            if result.get(
                "status"
            ) != "review":
                continue

            neighbor_ids = adjacency.get(
                township_id,
                set(),
            )

            classified_prefixes = [
                results_by_id[
                    neighbor_id
                ].get(
                    "one_digit_prefix"
                )
                for neighbor_id in neighbor_ids
                if results_by_id[
                    neighbor_id
                ].get(
                    "one_digit_prefix"
                )
                is not None
            ]

            if not classified_prefixes:
                continue

            neighbor_votes = Counter(
                classified_prefixes
            )

            winning_prefix, winning_count = (
                neighbor_votes.most_common(
                    1
                )[0]
            )

            neighbor_count = len(
                classified_prefixes
            )

            neighbor_confidence = (
                winning_count
                / neighbor_count
            )

            # If every classified neighbor agrees, use that prefix.
            if len(
                neighbor_votes
            ) == 1:
                proposed[
                    township_id
                ] = (
                    winning_prefix,
                    "neighbor-unanimous",
                    neighbor_confidence,
                )

                continue

            # Otherwise require a strong neighbor majority plus some
            # supporting raster evidence from the unresolved township.
            if (
                neighbor_count
                >= MIN_MAJORITY_NEIGHBORS
                and neighbor_confidence
                >= NEIGHBOR_MAJORITY_THRESHOLD
            ):
                raster_support = pixel_support_for_prefix(
                    result,
                    winning_prefix,
                )

                if (
                    raster_support
                    >= PIXEL_SUPPORT_THRESHOLD
                ):
                    proposed[
                        township_id
                    ] = (
                        winning_prefix,
                        "neighbor-majority",
                        neighbor_confidence,
                    )

        if not proposed:
            break

        for township_id, (
            prefix,
            method,
            neighbor_confidence,
        ) in proposed.items():
            result = results_by_id[
                township_id
            ]

            result[
                "one_digit_prefix"
            ] = prefix

            result[
                "status"
            ] = "recovered"

            result[
                "recovery_method"
            ] = method

            result[
                "neighbor_confidence"
            ] = round(
                neighbor_confidence,
                4,
            )

            result[
                "recovery_iteration"
            ] = iteration

        total_recovered += len(
            proposed
        )

        print(
            f"  Recovery iteration {iteration}: "
            f"{len(proposed)} townships"
        )

    return total_recovered


# ---------------------------------------------------------------------------
# Diagnostic rendering
# ---------------------------------------------------------------------------

def draw_diagnostic_feature(
    draw: ImageDraw.ImageDraw,
    feature: dict,
    prefix: str | None,
) -> None:
    """
    Draw one township using ONLY its final broad-prefix assignment.

    The original Plonk It raster is not involved in rendering.
    """

    fill = DIAGNOSTIC_COLORS.get(
        prefix,
        UNRESOLVED_COLOR,
    )

    geometry = feature.get(
        "geometry"
    )

    for polygon in transform_geometry_to_pixel_polygons(
        geometry
    ):
        if len(
            polygon
        ) < 3:
            continue

        draw.polygon(
            polygon,
            fill=fill,
            outline=OUTLINE_COLOR,
            width=1,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Loading Plonk It Taiwan area-code reference..."
    )

    if not PLONKIT_PATH.exists():
        raise FileNotFoundError(
            f"Missing Plonk It image: {PLONKIT_PATH}"
        )

    image = Image.open(
        PLONKIT_PATH
    ).convert(
        "RGB"
    )

    if image.size != (
        960,
        1370,
    ):
        raise ValueError(
            "Unexpected Plonk It image dimensions. "
            f"Expected 960 x 1370, found {image.size}."
        )

    print(
        "Loading Taiwan townships..."
    )

    township_data = load_geojson(
        TOWNSHIPS_PATH
    )

    township_features = township_data[
        "features"
    ]

    if len(
        township_features
    ) != 368:
        raise ValueError(
            f"Expected 368 townships, found "
            f"{len(township_features)}."
        )

    # -----------------------------------------------------------------------
    # Raster classification
    # -----------------------------------------------------------------------

    print()
    print(
        "Classifying Taiwan-proper townships..."
    )

    results: list[dict] = []
    mainland_features: list[dict] = []

    raster_classified_count = 0
    raster_review_count = 0
    offshore_count = 0

    for feature in township_features:
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties.get(
            "township_id"
        )

        county_id = properties.get(
            "county_id"
        )

        result = {
            "township_id": township_id,
            "township": properties.get(
                "township"
            ),
            "township_native": properties.get(
                "township_native"
            ),
            "county_id": county_id,
            "county": properties.get(
                "county"
            ),
            "one_digit_prefix": None,
            "confidence": None,
            "valid_samples": 0,
            "votes": {},
            "status": None,
            "recovery_method": None,
            "neighbor_confidence": None,
            "recovery_iteration": None,
        }

        if county_id not in MAINLAND_COUNTY_IDS:
            result[
                "status"
            ] = "offshore"

            offshore_count += 1

            results.append(
                result
            )

            continue

        mainland_features.append(
            feature
        )

        (
            prefix,
            confidence,
            valid_samples,
            votes,
        ) = classify_township(
            image=image,
            feature=feature,
        )

        result[
            "one_digit_prefix"
        ] = prefix

        result[
            "confidence"
        ] = round(
            confidence,
            4,
        )

        result[
            "valid_samples"
        ] = valid_samples

        result[
            "votes"
        ] = votes

        if prefix is None:
            result[
                "status"
            ] = "review"

            raster_review_count += 1

        else:
            result[
                "status"
            ] = "classified"

            raster_classified_count += 1

        results.append(
            result
        )

    print(
        f"  Raster classified: {raster_classified_count}"
    )

    print(
        f"  Raster review:     {raster_review_count}"
    )

    # -----------------------------------------------------------------------
    # Adjacency recovery
    # -----------------------------------------------------------------------

    print()
    print(
        "Building township adjacency..."
    )

    adjacency = build_adjacency(
        mainland_features
    )

    results_by_id = {
        result[
            "township_id"
        ]: result
        for result in results
    }

    print(
        "Recovering unresolved townships from neighbors..."
    )

    recovered_count = recover_from_neighbors(
        results_by_id=results_by_id,
        adjacency=adjacency,
    )

    # -----------------------------------------------------------------------
    # Manual overrides
    # -----------------------------------------------------------------------

    print()
    print(
        "Applying manually verified prefix overrides..."
    )

    manual_override_count = 0

    for township_id, prefix in MANUAL_PREFIX_OVERRIDES.items():
        result = results_by_id.get(
            township_id
        )

        if result is None:
            raise ValueError(
                "Manual override references unknown "
                f"township_id {township_id!r}."
            )

        if result.get(
            "status"
        ) == "offshore":
            raise ValueError(
                "Manual override unexpectedly references "
                f"offshore township {township_id!r}."
            )

        result[
            "one_digit_prefix"
        ] = prefix

        result[
            "status"
        ] = "manual"

        result[
            "recovery_method"
        ] = "manual-overlay-verification"

        result[
            "neighbor_confidence"
        ] = None

        result[
            "recovery_iteration"
        ] = None

        manual_override_count += 1

    print(
        f"  Manual overrides: {manual_override_count}"
    )

    # -----------------------------------------------------------------------
    # Clean diagnostic
    # -----------------------------------------------------------------------
    #
    # Start with a completely white image.
    #
    # DO NOT use the Plonk It raster as the diagnostic background.
    # -----------------------------------------------------------------------

    diagnostic = Image.new(
        "RGBA",
        image.size,
        (
            255,
            255,
            255,
            255,
        ),
    )

    draw = ImageDraw.Draw(
        diagnostic,
        "RGBA",
    )

    features_by_id = {
        feature.get(
            "properties",
            {},
        ).get(
            "township_id"
        ): feature
        for feature in mainland_features
    }

    for township_id, feature in features_by_id.items():
        result = results_by_id[
            township_id
        ]

        draw_diagnostic_feature(
            draw=draw,
            feature=feature,
            prefix=result.get(
                "one_digit_prefix"
            ),
        )

    # -----------------------------------------------------------------------
    # Write classification data
    # -----------------------------------------------------------------------

    results.sort(
        key=lambda item: (
            item[
                "county"
            ] or "",
            item[
                "township"
            ] or "",
            item[
                "township_id"
            ] or "",
        )
    )

    output = {
        "description": (
            "Intermediate classification of Taiwan townships "
            "by broad telephone area-code prefix."
        ),
        "prefixes": [
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
        ],
        "results": results,
    }

    CLASSIFICATION_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CLASSIFICATION_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write(
            "\n"
        )

    diagnostic.convert(
        "RGB"
    ).save(
        DIAGNOSTIC_PATH,
        quality=95,
    )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    remaining_review_count = sum(
        1
        for result in results
        if result.get(
            "status"
        ) == "review"
    )

    final_classified_count = sum(
        1
        for result in results
        if result.get(
            "status"
        ) in {
            "classified",
            "recovered",
            "manual",
        }
    )

    prefix_counts = Counter(
        result[
            "one_digit_prefix"
        ]
        for result in results
        if result.get(
            "one_digit_prefix"
        )
        is not None
    )

    print()
    print(
        "Broad-prefix classification complete."
    )

    print()
    print(
        f"Raster classified:   {raster_classified_count}"
    )
    print(
        f"Neighbor recovered:  {recovered_count}"
    )
    print(
        f"Manual overrides:    {manual_override_count}"
    )
    print(
        f"Total classified:    {final_classified_count}"
    )
    print(
        f"Needs review:        {remaining_review_count}"
    )
    print(
        f"Offshore:            {offshore_count}"
    )

    print()
    print(
        "Final mainland prefix counts:"
    )

    for prefix in [
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
    ]:
        print(
            f"  {prefix}: {prefix_counts.get(prefix, 0)}"
        )

    print()

    if remaining_review_count:
        print(
            "Unresolved townships:"
        )

        for result in results:
            if result.get(
                "status"
            ) != "review":
                continue

            print(
                "  "
                f"{result['county']} — "
                f"{result['township']} "
                f"({result['township_id']}) "
                f"votes={result['votes']}"
            )

        print()

    print(
        f"Data: "
        f"{CLASSIFICATION_PATH.relative_to(ROOT)}"
    )

    print(
        f"Diagnostic: "
        f"{DIAGNOSTIC_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()