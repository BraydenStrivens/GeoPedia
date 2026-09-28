"""
Group Taiwan townships by the fill colors used in the Plonk It telephone
area-code reference map.

Inputs
------
data/raw/countries/taiwan/area-codes/plonkit-area-codes.webp

data/intermediate/countries/taiwan/townships.geojson

data/intermediate/countries/taiwan/area-codes/
    township-prefix-classification.json

Outputs
-------
data/intermediate/countries/taiwan/area-codes/
    township-area-code-color-regions.json

data/intermediate/countries/taiwan/area-codes/
    area-code-color-regions.png

Purpose
-------
This script deliberately DOES NOT attempt to determine telephone area-code
numbers such as 032, 035, 049, or 089.

Instead, it answers a simpler geometric question:

    Which Taiwan townships belong to the same colored region
    on the Plonk It reference map?

Each distinct detected Plonk It fill color receives a temporary GeoPedia
region ID:

    R01
    R02
    R03
    ...

These IDs have no telephone meaning.

After the township grouping has been manually verified, the temporary
region IDs can later be mapped to the actual accepted telephone answers.

For example, a future mapping might look like:

    R03 -> ["032", "033"]
    R04 -> ["032", "034"]

but this script intentionally does not make those decisions.

Classification rule
-------------------
For each Taiwan-proper township:

1. Sample Plonk It pixels falling inside the township.
2. Ignore background, text, borders, and low-information pixels.
3. Determine which detected Plonk It fill-color cluster each usable pixel
   belongs to.
4. Count support for each color region.
5. If one region receives at least 70% of the recognized samples, assign
   the township to that region.
6. Otherwise leave the township UNCLASSIFIED.

There is NO neighbor recovery.

A township on a color boundary is therefore not guessed from neighboring
townships. If no color covers at least 70% of its recognized samples, it
remains white for manual assignment.

Diagnostic
----------
GRAY
    Township has been assigned to a temporary Rxx color region.

WHITE
    Township remains unclassified.

Thin gray line
    Ordinary township boundary.

Thick black line
    Boundary between two different assigned Rxx regions.

Rxx label
    Temporary color-region ID.

The actual Plonk It colors are not reproduced in the diagnostic because the
purpose of the image is to verify grouping geometry, not reproduce the
reference map.

Color detection
---------------
The script does not use manually chosen telephone-code seed points.

Instead it derives candidate source colors from the raster itself.

For every township, it first determines its locally dominant Plonk It fill
color. These dominant colors are then clustered globally so small WebP color
variations do not create artificial regions.

This means the algorithm knows only:

    "these pixels have the same source fill"

and NOT:

    "this color means 035"

That mapping is intentionally deferred until the geometry is verified.

Offshore regions
----------------
Penghu, Kinmen, and Lienchiang are shown as separately scaled Plonk It
insets and cannot use the Taiwan-proper georeferencing transform.

The existing broad-prefix file identifies those 16 townships because their
one_digit_prefix is null.

They are excluded from this mainland classifier and will be handled
separately later.

Run from the GeoPedia project root:

    python scripts/countries/taiwan/process/classify-area-codes.py

Requires:
    pillow
    shapely
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict, deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
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

PREFIX_CLASSIFICATION_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "township-prefix-classification.json"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "township-area-code-color-regions.json"
)

DIAGNOSTIC_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "area-code-color-regions.png"
)


# ---------------------------------------------------------------------------
# Locked Taiwan-proper georeferencing
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
# Sampling / classification settings
# ---------------------------------------------------------------------------

# Sample every Nth raster pixel.
SAMPLE_STEP = 2

# Avoid township-border pixels, where the township geometry and raster
# alignment are most sensitive.
BOUNDARY_INSET_PIXELS = 1.5

# A township must have at least this many usable source-color samples.
MIN_RECOGNIZED_SAMPLES = 10

# User-selected rule:
#
# If at least 70% of recognized samples belong to one color region,
# classify the township. Otherwise leave it unresolved.
ASSIGNMENT_THRESHOLD = 0.70

# ---------------------------------------------------------------------------
# Conservative neighbor recovery
# ---------------------------------------------------------------------------
#
# Neighbor recovery is performed only AFTER the >=70% source-color
# classification.
#
# It never changes an already-classified township.
#
# An unclassified township can be recovered when:
#
# 1. every classified adjacent township belongs to the same Rxx region, or
#
# 2. at least 3 classified neighbors exist, at least 75% belong to the same
#    Rxx region, AND the unresolved township's own raster samples provide
#    some support for that same region.
#
# Recovery repeats because filling one obvious hole may make another
# previously isolated township recoverable.
# ---------------------------------------------------------------------------

MIN_MAJORITY_NEIGHBORS = 3

NEIGHBOR_MAJORITY_THRESHOLD = 0.75

MIN_RASTER_SUPPORT_FOR_MAJORITY = 0.20

# ---------------------------------------------------------------------------
# Manually verified color-region overrides
# ---------------------------------------------------------------------------
#
# These townships could not be assigned confidently from raster sampling
# and/or conservative neighbor recovery.
#
# The assignments below were manually verified against the Plonk It
# reference using the numbered township diagnostic.
#
# Keys are stable MOI township IDs, NOT temporary diagnostic numbers.
# ---------------------------------------------------------------------------

MANUAL_REGION_OVERRIDES = {
    "10002040": "R05",  # Toucheng Township — diagnostic #328

    "10010010": "R18",  # Taibao City — diagnostic #41

    "67000130": "R20",  # Xuejia District — diagnostic #275
    "67000140": "R20",  # Xigang District — diagnostic #271

    "67000310": "R22",  # Yongkang District — diagnostic #277
    "67000280": "R22",  # Guiren District — diagnostic #253

    "64000150": "R23",  # Dashu District — diagnostic #79
    "64000140": "R23",  # Daliao District — diagnostic #77
    "64000130": "R23",  # Linyuan District — diagnostic #86

    "10013180": "R26",  # Kanding Township — diagnostic #192
    "10013220": "R26",  # Liuqiu Township — diagnostic #197

    "10014110": "R24",  # Ludao Township — diagnostic #303
}

# ---------------------------------------------------------------------------
# Explicit offshore region assignments
# ---------------------------------------------------------------------------
#
# Plonk It displays Penghu, Kinmen, and Lienkiang/Matsu in separately
# scaled inset maps, so these townships cannot be classified with the
# Taiwan-proper raster transform.
#
# They are therefore assigned explicitly using their stable MOI township
# IDs.
#
# R27 = Penghu
# R28 = Kinmen
#
# R29-R32 are the four Lienkiang/Matsu telephone regions.
#
# R32 / 08368 is intentionally retained even though the current Plonk It
# reference marks that region as having no GeoGuessr coverage. GeoPedia's
# geographic quiz data should still represent the complete region.
# ---------------------------------------------------------------------------

OFFSHORE_REGION_ASSIGNMENTS = {
    # Penghu — 069
    "10016010": "R27",  # Magong City
    "10016020": "R27",  # Huxi Township
    "10016030": "R27",  # Baisha Township
    "10016040": "R27",  # Xiyu Township
    "10016050": "R27",  # Wang'an Township
    "10016060": "R27",  # Qimei Township

    # Kinmen — 082
    "09020010": "R28",  # Jincheng Township
    "09020020": "R28",  # Jinsha Township
    "09020030": "R28",  # Jinhu Township
    "09020040": "R28",  # Jinning Township
    "09020050": "R28",  # Lieyu Township
    "09020060": "R28",  # Wuqiu Township

    # Lienkiang / Matsu
    "09007010": "R29",  # Nangan Township  — 08362
    "09007030": "R30",  # Juguang Township — 08365
    "09007040": "R31",  # Dongyin Township — 08367
    "09007020": "R32",  # Beigan Township  — 08368
}


# ---------------------------------------------------------------------------
# Telephone answers by verified geographic region
# ---------------------------------------------------------------------------
#
# R01-R26 are the 26 verified Taiwan-proper color regions.
# R27-R32 are the explicitly assigned offshore regions.
#
# A region may have multiple accepted telephone answers when the Plonk It
# reference does not distinguish those codes geographically.
#
# These answer sets should remain attached to the REGION, not duplicated
# independently across township geometry.
# ---------------------------------------------------------------------------

AREA_CODES_BY_REGION = {
    # Taiwan proper
    "R01": ["02"],
    "R02": ["033"],
    "R03": ["032", "034"],
    "R04": ["035", "036"],
    "R05": ["039"],
    "R06": ["037"],

    "R07": ["043", "0426"],
    "R08": ["0425"],
    "R09": ["043", "0422", "0423", "0424", "0427"],
    "R10": ["047"],
    "R11": ["048"],
    "R12": ["049"],

    "R13": ["056"],
    "R14": ["055"],
    "R15": ["038"],
    "R16": ["057"],
    "R17": ["052"],
    "R18": ["053"],

    "R19": ["066"],
    "R20": ["067"],
    "R21": ["065"],
    "R22": ["062", "063"],

    "R23": ["07"],

    "R24": ["089"],
    "R25": ["087"],
    "R26": ["088"],

    # Offshore
    "R27": ["069"],
    "R28": ["082"],
    "R29": ["08362"],
    "R30": ["08365"],
    "R31": ["08367"],
    "R32": ["08368"],
}

# ---------------------------------------------------------------------------
# Color filtering
# ---------------------------------------------------------------------------

# Very bright near-white pixels are background.
WHITE_THRESHOLD = 245

# Very dark pixels are primarily text / outlines.
BLACK_THRESHOLD = 45

# A true colored Plonk It fill should have a reasonable difference between
# at least two RGB channels.
MIN_COLOR_RANGE = 25

# WebP compression can create several almost-identical RGB values around a
# single source fill. Colors within this Euclidean RGB distance are treated
# as the same fill-color family.
COLOR_CLUSTER_DISTANCE = 18.0

# A locally dominant exact RGB value must appear at least this many times
# across township sampling before it can seed a global color cluster.
#
# This helps prevent text anti-aliasing colors from becoming Rxx regions.
MIN_GLOBAL_COLOR_SAMPLES = 20


# ---------------------------------------------------------------------------
# Diagnostic styling
# ---------------------------------------------------------------------------

CLASSIFIED_FILL = (
    190,
    190,
    190,
    255,
)

UNCLASSIFIED_FILL = (
    255,
    255,
    255,
    255,
)

TOWNSHIP_BOUNDARY_COLOR = (
    110,
    110,
    110,
    255,
)

REGION_BOUNDARY_COLOR = (
    0,
    0,
    0,
    255,
)

LABEL_COLOR = (
    0,
    0,
    0,
    255,
)

THIN_BOUNDARY_WIDTH = 1

THICK_BOUNDARY_WIDTH = 4


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
        return json.load(
            file
        )


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


def color_distance(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
) -> float:
    return math.sqrt(
        (first[0] - second[0]) ** 2
        + (first[1] - second[1]) ** 2
        + (first[2] - second[2]) ** 2
    )


def is_possible_fill_color(
    color: tuple[int, int, int],
) -> bool:
    red, green, blue = color

    # Background / white text halo.
    if (
        red >= WHITE_THRESHOLD
        and green >= WHITE_THRESHOLD
        and blue >= WHITE_THRESHOLD
    ):
        return False

    # Black labels / outlines.
    if (
        red <= BLACK_THRESHOLD
        and green <= BLACK_THRESHOLD
        and blue <= BLACK_THRESHOLD
    ):
        return False

    # Neutral gray pixels are not Plonk It region fills.
    color_range = (
        max(
            red,
            green,
            blue,
        )
        - min(
            red,
            green,
            blue,
        )
    )

    if color_range < MIN_COLOR_RANGE:
        return False

    return True


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

    x = (
        left
        + x_fraction
        * (right - left)
    )

    y = (
        top
        + y_fraction
        * (bottom - top)
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

    longitude = (
        min_lon
        + x_fraction
        * (max_lon - min_lon)
    )

    latitude = (
        max_lat
        - y_fraction
        * (max_lat - min_lat)
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

    polygons = []

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
# Sample raw colors inside a township
# ---------------------------------------------------------------------------

def sample_township_colors(
    image: Image.Image,
    feature: dict,
) -> Counter[tuple[int, int, int]]:
    geometry_data = feature[
        "geometry"
    ]

    geographic_geometry = shape(
        geometry_data
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

    colors: Counter[
        tuple[int, int, int]
    ] = Counter()

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

            if (
                geographic_geometry.boundary.distance(
                    point
                )
                < boundary_inset_degrees
            ):
                continue

            color = image.getpixel(
                (x, y)
            )

            if not is_possible_fill_color(
                color
            ):
                continue

            colors[
                color
            ] += 1

    return colors


# ---------------------------------------------------------------------------
# Build source-color clusters
# ---------------------------------------------------------------------------

def build_color_clusters(
    township_raw_colors: dict[
        str,
        Counter[tuple[int, int, int]],
    ],
) -> list[dict]:
    """
    Discover the actual Plonk It fill-color families without assigning any
    telephone meaning to them.

    Exact RGB values are first counted globally.

    Frequent colors are then merged when their RGB values are sufficiently
    close, which absorbs WebP compression variations around a single fill.

    Cluster IDs are assigned later based on geographic position so R01,
    R02, etc. are stable and easy to inspect.
    """

    global_counts: Counter[
        tuple[int, int, int]
    ] = Counter()

    for colors in township_raw_colors.values():
        global_counts.update(
            colors
        )

    candidate_colors = [
        (
            color,
            count,
        )
        for color, count
        in global_counts.most_common()
        if count >= MIN_GLOBAL_COLOR_SAMPLES
    ]

    clusters: list[dict] = []

    for color, count in candidate_colors:
        best_cluster = None
        best_distance = float(
            "inf"
        )

        for cluster in clusters:
            distance = color_distance(
                color,
                cluster[
                    "representative_color"
                ],
            )

            if distance < best_distance:
                best_distance = distance
                best_cluster = cluster

        if (
            best_cluster is not None
            and best_distance
            <= COLOR_CLUSTER_DISTANCE
        ):
            best_cluster[
                "colors"
            ].add(
                color
            )

            best_cluster[
                "sample_count"
            ] += count

        else:
            clusters.append(
                {
                    "representative_color": color,
                    "colors": {
                        color
                    },
                    "sample_count": count,
                }
            )

    return clusters


def nearest_cluster_index(
    color: tuple[int, int, int],
    clusters: list[dict],
) -> int | None:
    best_index = None
    best_distance = float(
        "inf"
    )

    for index, cluster in enumerate(
        clusters
    ):
        distance = color_distance(
            color,
            cluster[
                "representative_color"
            ],
        )

        if distance < best_distance:
            best_distance = distance
            best_index = index

    if (
        best_index is None
        or best_distance
        > COLOR_CLUSTER_DISTANCE
    ):
        return None

    return best_index


# ---------------------------------------------------------------------------
# Township region classification
# ---------------------------------------------------------------------------

def classify_township_from_color(
    raw_colors: Counter[
        tuple[int, int, int]
    ],
    clusters: list[dict],
) -> tuple[
    int | None,
    float,
    int,
    dict[int, int],
]:
    cluster_votes: Counter[
        int
    ] = Counter()

    for color, count in raw_colors.items():
        cluster_index = nearest_cluster_index(
            color,
            clusters,
        )

        if cluster_index is None:
            continue

        cluster_votes[
            cluster_index
        ] += count

    recognized_samples = sum(
        cluster_votes.values()
    )

    if (
        recognized_samples
        < MIN_RECOGNIZED_SAMPLES
    ):
        return (
            None,
            0.0,
            recognized_samples,
            dict(
                cluster_votes
            ),
        )

    winning_cluster, winning_count = (
        cluster_votes.most_common(
            1
        )[0]
    )

    confidence = (
        winning_count
        / recognized_samples
    )

    if confidence < ASSIGNMENT_THRESHOLD:
        return (
            None,
            confidence,
            recognized_samples,
            dict(
                cluster_votes
            ),
        )

    return (
        winning_cluster,
        confidence,
        recognized_samples,
        dict(
            cluster_votes
        ),
    )


# ---------------------------------------------------------------------------
# Township adjacency
# ---------------------------------------------------------------------------

def build_adjacency(
    mainland_features: list[dict],
) -> tuple[
    dict[str, set[str]],
    dict[str, object],
]:
    township_ids = []

    geometries = []

    geometry_by_id = {}

    for feature in mainland_features:
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties[
            "township_id"
        ]

        geometry = shape(
            feature[
                "geometry"
            ]
        )

        township_ids.append(
            township_id
        )

        geometries.append(
            geometry
        )

        geometry_by_id[
            township_id
        ] = geometry

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

        for candidate_index in tree.query(
            geometry
        ):
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
                and shared_boundary.length > 1e-8
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

    return (
        adjacency,
        geometry_by_id,
    )


# ---------------------------------------------------------------------------
# Give detected clusters stable Rxx IDs
# ---------------------------------------------------------------------------

def assign_region_ids(
    preliminary_results: dict[str, dict],
    geometry_by_id: dict[str, object],
    cluster_count: int,
) -> dict[int, str]:
    """
    Assign R01, R02, ... to source-color clusters.

    IDs are ordered geographically from north to south, then west to east,
    using the average representative point of townships assigned to each
    cluster.

    This gives the temporary IDs deterministic meaning without tying them
    to telephone numbers.
    """

    positions: dict[
        int,
        list[tuple[float, float]]
    ] = defaultdict(
        list
    )

    for township_id, result in preliminary_results.items():
        cluster_index = result.get(
            "cluster_index"
        )

        if cluster_index is None:
            continue

        point = geometry_by_id[
            township_id
        ].representative_point()

        positions[
            cluster_index
        ].append(
            (
                point.x,
                point.y,
            )
        )

    sortable = []

    for cluster_index in range(
        cluster_count
    ):
        cluster_positions = positions.get(
            cluster_index,
            [],
        )

        if cluster_positions:
            average_lon = sum(
                position[0]
                for position in cluster_positions
            ) / len(
                cluster_positions
            )

            average_lat = sum(
                position[1]
                for position in cluster_positions
            ) / len(
                cluster_positions
            )

        else:
            average_lon = 999.0
            average_lat = -999.0

        sortable.append(
            (
                cluster_index,
                average_lon,
                average_lat,
            )
        )

    # North -> south.
    # For regions at roughly the same latitude, west -> east.
    sortable.sort(
        key=lambda item: (
            -item[2],
            item[1],
        )
    )

    return {
        cluster_index: (
            f"R{position:02d}"
        )
        for position, (
            cluster_index,
            _,
            _,
        )
        in enumerate(
            sortable,
            start=1,
        )
    }
    
# ---------------------------------------------------------------------------
# Conservative neighbor recovery
# ---------------------------------------------------------------------------

def recover_unclassified_from_neighbors(
    results_by_id: dict[str, dict],
    adjacency: dict[str, set[str]],
) -> int:
    """
    Recover obvious holes after source-color classification.

    This function NEVER changes a township that already has an Rxx region.

    Recovery rules
    --------------
    Unanimous:
        If every currently classified adjacent township belongs to the same
        Rxx region, assign that region.

    Majority:
        If at least MIN_MAJORITY_NEIGHBORS classified neighbors exist and
        at least NEIGHBOR_MAJORITY_THRESHOLD of them belong to one region,
        the township can be assigned to that region only when its own raster
        votes also contain at least MIN_RASTER_SUPPORT_FOR_MAJORITY support
        for that same Rxx region.

    Recovery is iterative, but all assignments within one iteration are
    calculated before any are applied. This prevents iteration order from
    affecting the result.
    """

    total_recovered = 0

    iteration = 0

    while True:
        iteration += 1

        proposed: dict[
            str,
            dict,
        ] = {}

        for township_id, result in results_by_id.items():
            if result.get(
                "region_id"
            ) is not None:
                continue

            if result.get(
                "status"
            ) != "unclassified":
                continue

            classified_neighbors = []

            for neighbor_id in adjacency.get(
                township_id,
                set(),
            ):
                neighbor = results_by_id.get(
                    neighbor_id
                )

                if neighbor is None:
                    continue

                neighbor_region = neighbor.get(
                    "region_id"
                )

                if neighbor_region is None:
                    continue

                classified_neighbors.append(
                    neighbor_region
                )

            if not classified_neighbors:
                continue

            neighbor_votes = Counter(
                classified_neighbors
            )

            winning_region, winning_count = (
                neighbor_votes.most_common(
                    1
                )[0]
            )

            classified_neighbor_count = len(
                classified_neighbors
            )

            neighbor_confidence = (
                winning_count
                / classified_neighbor_count
            )

            # -----------------------------------------------------------
            # Rule 1: unanimous classified neighbors
            # -----------------------------------------------------------

            if len(
                neighbor_votes
            ) == 1:
                proposed[
                    township_id
                ] = {
                    "region_id": winning_region,
                    "method": "neighbor-unanimous",
                    "neighbor_confidence": (
                        neighbor_confidence
                    ),
                    "classified_neighbor_count": (
                        classified_neighbor_count
                    ),
                }

                continue

            # -----------------------------------------------------------
            # Rule 2: strong neighbor majority + raster support
            # -----------------------------------------------------------

            if (
                classified_neighbor_count
                < MIN_MAJORITY_NEIGHBORS
            ):
                continue

            if (
                neighbor_confidence
                < NEIGHBOR_MAJORITY_THRESHOLD
            ):
                continue

            region_votes = result.get(
                "region_votes",
                {},
            )

            total_raster_votes = sum(
                region_votes.values()
            )

            if total_raster_votes == 0:
                continue

            winning_region_raster_votes = (
                region_votes.get(
                    winning_region,
                    0,
                )
            )

            raster_support = (
                winning_region_raster_votes
                / total_raster_votes
            )

            if (
                raster_support
                < MIN_RASTER_SUPPORT_FOR_MAJORITY
            ):
                continue

            proposed[
                township_id
            ] = {
                "region_id": winning_region,
                "method": "neighbor-majority",
                "neighbor_confidence": (
                    neighbor_confidence
                ),
                "classified_neighbor_count": (
                    classified_neighbor_count
                ),
                "raster_support": raster_support,
            }

        if not proposed:
            break

        for township_id, recovery in proposed.items():
            result = results_by_id[
                township_id
            ]

            result[
                "region_id"
            ] = recovery[
                "region_id"
            ]

            result[
                "status"
            ] = "recovered"

            result[
                "recovery_method"
            ] = recovery[
                "method"
            ]

            result[
                "recovery_iteration"
            ] = iteration

            result[
                "neighbor_confidence"
            ] = round(
                recovery[
                    "neighbor_confidence"
                ],
                4,
            )

            result[
                "classified_neighbor_count"
            ] = recovery[
                "classified_neighbor_count"
            ]

            raster_support = recovery.get(
                "raster_support"
            )

            result[
                "recovery_raster_support"
            ] = (
                round(
                    raster_support,
                    4,
                )
                if raster_support is not None
                else None
            )

        print(
            f"  Recovery iteration {iteration}: "
            f"{len(proposed)} townships"
        )

        total_recovered += len(
            proposed
        )

    return total_recovered

def apply_manual_region_overrides(
    results_by_id: dict[str, dict],
) -> int:
    """
    Apply manually verified Rxx assignments.

    Manual assignments are authoritative and are applied after automatic
    color classification and neighbor recovery.
    """

    applied = 0

    for township_id, region_id in MANUAL_REGION_OVERRIDES.items():
        result = results_by_id.get(
            township_id
        )

        if result is None:
            raise ValueError(
                f"Manual region override references unknown "
                f"township_id {township_id!r}."
            )

        result[
            "region_id"
        ] = region_id

        result[
            "status"
        ] = "manual"

        result[
            "manual_region_override"
        ] = True

        applied += 1

    return applied

# ---------------------------------------------------------------------------
# Connected groups
# ---------------------------------------------------------------------------

def build_connected_region_groups(
    results_by_id: dict[str, dict],
    adjacency: dict[str, set[str]],
) -> list[dict]:
    visited = set()

    groups = []

    for township_id, result in results_by_id.items():
        region_id = result.get(
            "region_id"
        )

        if region_id is None:
            continue

        if township_id in visited:
            continue

        queue = deque(
            [
                township_id
            ]
        )

        visited.add(
            township_id
        )

        member_ids = []

        while queue:
            current_id = queue.popleft()

            member_ids.append(
                current_id
            )

            for neighbor_id in adjacency.get(
                current_id,
                set(),
            ):
                if neighbor_id in visited:
                    continue

                neighbor = results_by_id[
                    neighbor_id
                ]

                if (
                    neighbor.get(
                        "region_id"
                    )
                    != region_id
                ):
                    continue

                visited.add(
                    neighbor_id
                )

                queue.append(
                    neighbor_id
                )

        groups.append(
            {
                "region_id": region_id,
                "township_ids": member_ids,
            }
        )

    return groups


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_geometry_lines(
    draw: ImageDraw.ImageDraw,
    geometry,
    fill,
    width: int,
) -> None:
    if geometry.is_empty:
        return

    if geometry.geom_type == "LineString":
        coordinates = [
            lon_lat_to_pixel(
                longitude,
                latitude,
            )
            for longitude, latitude
            in geometry.coords
        ]

        if len(
            coordinates
        ) >= 2:
            draw.line(
                coordinates,
                fill=fill,
                width=width,
                joint="curve",
            )

        return

    if geometry.geom_type in {
        "MultiLineString",
        "GeometryCollection",
    }:
        for part in geometry.geoms:
            draw_geometry_lines(
                draw=draw,
                geometry=part,
                fill=fill,
                width=width,
            )


def draw_township(
    draw: ImageDraw.ImageDraw,
    feature: dict,
    classified: bool,
) -> None:
    fill = (
        CLASSIFIED_FILL
        if classified
        else UNCLASSIFIED_FILL
    )

    for polygon in transform_geometry_to_pixel_polygons(
        feature[
            "geometry"
        ]
    ):
        if len(
            polygon
        ) < 3:
            continue

        draw.polygon(
            polygon,
            fill=fill,
            outline=TOWNSHIP_BOUNDARY_COLOR,
            width=THIN_BOUNDARY_WIDTH,
        )


def draw_region_boundaries(
    draw: ImageDraw.ImageDraw,
    results_by_id: dict[str, dict],
    adjacency: dict[str, set[str]],
    geometry_by_id: dict[str, object],
) -> None:
    drawn_pairs = set()

    for township_id, neighbors in adjacency.items():
        first_region = results_by_id[
            township_id
        ].get(
            "region_id"
        )

        if first_region is None:
            continue

        for neighbor_id in neighbors:
            pair = tuple(
                sorted(
                    (
                        township_id,
                        neighbor_id,
                    )
                )
            )

            if pair in drawn_pairs:
                continue

            drawn_pairs.add(
                pair
            )

            second_region = results_by_id[
                neighbor_id
            ].get(
                "region_id"
            )

            # White/unclassified townships are intentionally not used to
            # invent a color-region boundary.
            if second_region is None:
                continue

            if first_region == second_region:
                continue

            shared_boundary = (
                geometry_by_id[
                    township_id
                ]
                .boundary
                .intersection(
                    geometry_by_id[
                        neighbor_id
                    ].boundary
                )
            )

            draw_geometry_lines(
                draw=draw,
                geometry=shared_boundary,
                fill=REGION_BOUNDARY_COLOR,
                width=THICK_BOUNDARY_WIDTH,
            )


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def get_font(
    size: int,
) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "arialbd.ttf",
        "arial.ttf",
    ]

    for candidate in candidates:
        try:
            return ImageFont.truetype(
                candidate,
                size=size,
            )

        except OSError:
            continue

    return ImageFont.load_default()


def draw_group_labels(
    image: Image.Image,
    groups: list[dict],
    geometry_by_id: dict[str, object],
) -> None:
    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    font = get_font(
        16
    )

    for group in groups:
        member_ids = group[
            "township_ids"
        ]

        if not member_ids:
            continue

        geometries = [
            geometry_by_id[
                township_id
            ]
            for township_id in member_ids
        ]

        # Use the largest member township as a safe location for the label.
        largest_geometry = max(
            geometries,
            key=lambda geometry: geometry.area,
        )

        point = (
            largest_geometry
            .representative_point()
        )

        x, y = lon_lat_to_pixel(
            point.x,
            point.y,
        )

        text = group[
            "region_id"
        ]

        bbox = draw.textbbox(
            (
                0,
                0,
            ),
            text,
            font=font,
            stroke_width=2,
        )

        text_width = (
            bbox[2]
            - bbox[0]
        )

        text_height = (
            bbox[3]
            - bbox[1]
        )

        draw.text(
            (
                x - text_width / 2,
                y - text_height / 2,
            ),
            text,
            font=font,
            fill=LABEL_COLOR,
            stroke_width=2,
            stroke_fill=(
                255,
                255,
                255,
                255,
            ),
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

    print(
        "Loading verified broad-prefix metadata..."
    )

    prefix_data = load_json(
        PREFIX_CLASSIFICATION_PATH
    )

    prefix_results = prefix_data.get(
        "results"
    )

    if not isinstance(
        prefix_results,
        list,
    ):
        raise ValueError(
            "Broad-prefix classification is missing its results array."
        )

    prefix_by_id = {
        result[
            "township_id"
        ]: result.get(
            "one_digit_prefix"
        )
        for result in prefix_results
    }

    # -----------------------------------------------------------------------
    # Separate mainland from offshore
    # -----------------------------------------------------------------------

    mainland_features = []

    offshore_features = []

    for feature in township_features:
        township_id = feature.get(
            "properties",
            {}
        ).get(
            "township_id"
        )

        if prefix_by_id.get(
            township_id
        ) is None:
            offshore_features.append(
                feature
            )

        else:
            mainland_features.append(
                feature
            )

    print()
    print(
        f"Taiwan-proper townships: {len(mainland_features)}"
    )

    print(
        f"Offshore townships:      {len(offshore_features)}"
    )

    # -----------------------------------------------------------------------
    # Adjacency
    # -----------------------------------------------------------------------

    print()
    print(
        "Building township adjacency..."
    )

    (
        adjacency,
        geometry_by_id,
    ) = build_adjacency(
        mainland_features
    )

    # -----------------------------------------------------------------------
    # Sample raw source colors
    # -----------------------------------------------------------------------

    print(
        "Sampling Plonk It fill colors inside each township..."
    )

    township_raw_colors = {}

    features_by_id = {}

    for feature in mainland_features:
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties[
            "township_id"
        ]

        features_by_id[
            township_id
        ] = feature

        township_raw_colors[
            township_id
        ] = sample_township_colors(
            image=image,
            feature=feature,
        )

    # -----------------------------------------------------------------------
    # Discover source-color regions
    # -----------------------------------------------------------------------

    print(
        "Discovering Plonk It color regions..."
    )

    clusters = build_color_clusters(
        township_raw_colors
    )

    print(
        f"  Detected source-color clusters: {len(clusters)}"
    )

    # -----------------------------------------------------------------------
    # Initial classification
    # -----------------------------------------------------------------------

    preliminary_results = {}

    classified_count = 0

    unclassified_count = 0

    for feature in mainland_features:
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties[
            "township_id"
        ]

        (
            cluster_index,
            confidence,
            recognized_samples,
            cluster_votes,
        ) = classify_township_from_color(
            raw_colors=township_raw_colors[
                township_id
            ],
            clusters=clusters,
        )

        if cluster_index is None:
            unclassified_count += 1

        else:
            classified_count += 1

        preliminary_results[
            township_id
        ] = {
            "township_id": township_id,
            "township": properties.get(
                "township"
            ),
            "township_native": properties.get(
                "township_native"
            ),
            "county_id": properties.get(
                "county_id"
            ),
            "county": properties.get(
                "county"
            ),
            "one_digit_prefix": prefix_by_id.get(
                township_id
            ),
            "cluster_index": cluster_index,
            "region_id": None,
            "confidence": round(
                confidence,
                4,
            ),
            "recognized_samples": recognized_samples,
            "cluster_votes": cluster_votes,
            "status": (
                "classified"
                if cluster_index is not None
                else "unclassified"
            ),
        }

    # -----------------------------------------------------------------------
    # Stable temporary region IDs
    # -----------------------------------------------------------------------

    cluster_to_region_id = assign_region_ids(
        preliminary_results=preliminary_results,
        geometry_by_id=geometry_by_id,
        cluster_count=len(
            clusters
        ),
    )

    for result in preliminary_results.values():
        cluster_index = result[
            "cluster_index"
        ]

        if cluster_index is None:
            continue

        result[
            "region_id"
        ] = cluster_to_region_id[
            cluster_index
        ]

    # Convert numeric cluster-vote keys into Rxx IDs for useful debugging.
    for result in preliminary_results.values():
        converted_votes = {}

        for cluster_index, count in result[
            "cluster_votes"
        ].items():
            region_id = cluster_to_region_id.get(
                int(
                    cluster_index
                )
            )

            if region_id is not None:
                converted_votes[
                    region_id
                ] = count

        result[
            "region_votes"
        ] = converted_votes

        del result[
            "cluster_votes"
        ]

        del result[
            "cluster_index"
        ]

    # -----------------------------------------------------------------------
    # Conservative neighbor recovery
    # -----------------------------------------------------------------------

    print()
    print(
        "Recovering obvious unclassified holes from neighbors..."
    )

    recovered_count = recover_unclassified_from_neighbors(
        results_by_id=preliminary_results,
        adjacency=adjacency,
    )
    
    # -----------------------------------------------------------------------
    # Manual verification overrides
    # -----------------------------------------------------------------------

    print()
    print(
        "Applying manually verified color-region overrides..."
    )

    manual_override_count = apply_manual_region_overrides(
        results_by_id=preliminary_results,
    )
    
    # -----------------------------------------------------------------------
    # Attach telephone answers to all verified mainland regions
    # -----------------------------------------------------------------------

    for result in preliminary_results.values():
        region_id = result.get(
            "region_id"
        )

        if region_id is None:
            continue

        area_codes = AREA_CODES_BY_REGION.get(
            region_id
        )

        if area_codes is None:
            raise ValueError(
                f"Region {region_id!r} does not have an "
                "area-code answer mapping."
            )

        result[
            "area_codes"
        ] = list(
            area_codes
        )

    print(
        f"  Manual overrides: {manual_override_count}"
    )

    # -----------------------------------------------------------------------
    # Recalculate final counts after recovery
    # -----------------------------------------------------------------------

    classified_count = sum(
        1
        for result in preliminary_results.values()
        if result.get(
            "region_id"
        ) is not None
    )

    unclassified_count = sum(
        1
        for result in preliminary_results.values()
        if result.get(
            "region_id"
        ) is None
    )

    # -----------------------------------------------------------------------
    # Connected groups
    # -----------------------------------------------------------------------

    groups = build_connected_region_groups(
        results_by_id=preliminary_results,
        adjacency=adjacency,
    )

    # -----------------------------------------------------------------------
    # Diagnostic
    # -----------------------------------------------------------------------

    print(
        "Rendering color-region diagnostic..."
    )

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

    for township_id, feature in features_by_id.items():
        result = preliminary_results[
            township_id
        ]

        draw_township(
            draw=draw,
            feature=feature,
            classified=(
                result[
                    "region_id"
                ]
                is not None
            ),
        )

    draw_region_boundaries(
        draw=draw,
        results_by_id=preliminary_results,
        adjacency=adjacency,
        geometry_by_id=geometry_by_id,
    )

    draw_group_labels(
        image=diagnostic,
        groups=groups,
        geometry_by_id=geometry_by_id,
    )

    DIAGNOSTIC_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    diagnostic.convert(
        "RGB"
    ).save(
        DIAGNOSTIC_PATH,
        quality=95,
    )

    # -----------------------------------------------------------------------
    # Region metadata
    # -----------------------------------------------------------------------

    region_metadata = []

    for cluster_index, region_id in sorted(
        cluster_to_region_id.items(),
        key=lambda item: item[1],
    ):
        cluster = clusters[
            cluster_index
        ]

        township_ids = [
            township_id
            for township_id, result
            in preliminary_results.items()
            if result.get(
                "region_id"
            ) == region_id
        ]

        region_metadata.append(
            {
                "region_id": region_id,
                "source_representative_rgb": list(
                    cluster[
                        "representative_color"
                    ]
                ),
                "source_sample_count": cluster[
                    "sample_count"
                ],
                "township_count": len(
                    township_ids
                ),
                "township_ids": sorted(
                    township_ids
                ),
            }
        )

    # -----------------------------------------------------------------------
    # Add explicit offshore region assignments
    # -----------------------------------------------------------------------

    all_results = list(
        preliminary_results.values()
    )

    offshore_assigned_count = 0

    for feature in offshore_features:
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties.get(
            "township_id"
        )

        region_id = OFFSHORE_REGION_ASSIGNMENTS.get(
            township_id
        )

        if region_id is None:
            raise ValueError(
                "Missing explicit offshore region assignment for "
                f"{properties.get('county')} — "
                f"{properties.get('township')} "
                f"({township_id})."
            )

        area_codes = AREA_CODES_BY_REGION.get(
            region_id
        )

        if area_codes is None:
            raise ValueError(
                f"Offshore region {region_id!r} does not have a "
                "telephone-area-code mapping."
            )

        all_results.append(
            {
                "township_id": township_id,
                "township": properties.get(
                    "township"
                ),
                "township_native": properties.get(
                    "township_native"
                ),
                "county_id": properties.get(
                    "county_id"
                ),
                "county": properties.get(
                    "county"
                ),
                "one_digit_prefix": None,
                "region_id": region_id,
                "area_codes": list(
                    area_codes
                ),
                "confidence": None,
                "recognized_samples": 0,
                "region_votes": {},
                "status": "offshore-explicit",
            }
        )

        offshore_assigned_count += 1

    if offshore_assigned_count != 16:
        raise ValueError(
            "Expected exactly 16 explicitly assigned offshore townships, "
            f"found {offshore_assigned_count}."
        )
        
    # -----------------------------------------------------------------------
    # Final completeness validation
    # -----------------------------------------------------------------------

    expected_regions = {
        f"R{number:02d}"
        for number in range(
            1,
            33,
        )
    }

    actual_regions = {
        result.get(
            "region_id"
        )
        for result in all_results
        if result.get(
            "region_id"
        ) is not None
    }

    if actual_regions != expected_regions:
        missing = sorted(
            expected_regions
            - actual_regions
        )

        unexpected = sorted(
            actual_regions
            - expected_regions
        )

        raise ValueError(
            "Final region validation failed. "
            f"Missing={missing}, unexpected={unexpected}"
        )

    for result in all_results:
        if result.get(
            "region_id"
        ) is None:
            raise ValueError(
                "Final output contains an unassigned township: "
                f"{result.get('county')} — "
                f"{result.get('township')} "
                f"({result.get('township_id')})"
            )

        if not result.get(
            "area_codes"
        ):
            raise ValueError(
                "Final output contains a township without telephone "
                f"answers: {result.get('township_id')}"
            )

    if len(
        all_results
    ) != 368:
        raise ValueError(
            f"Expected 368 final township assignments, "
            f"found {len(all_results)}."
        )

    all_results.sort(
        key=lambda item: (
            item.get(
                "county"
            ) or "",
            item.get(
                "township"
            ) or "",
            item.get(
                "township_id"
            ) or "",
        )
    )

    # -----------------------------------------------------------------------
    # Save JSON
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # Complete R01-R32 region metadata
    # -----------------------------------------------------------------------

    all_region_metadata = []

    for region in region_metadata:
        region_id = region[
            "region_id"
        ]

        all_region_metadata.append(
            {
                **region,
                "area_codes": list(
                    AREA_CODES_BY_REGION[
                        region_id
                    ]
                ),
                "assignment_method": "plonkit-color-region",
            }
        )

    for region_id in (
        "R27",
        "R28",
        "R29",
        "R30",
        "R31",
        "R32",
    ):
        township_ids = sorted(
            result[
                "township_id"
            ]
            for result in all_results
            if result.get(
                "region_id"
            ) == region_id
        )

        all_region_metadata.append(
            {
                "region_id": region_id,
                "source_representative_rgb": None,
                "source_sample_count": None,
                "township_count": len(
                    township_ids
                ),
                "township_ids": township_ids,
                "area_codes": AREA_CODES_BY_REGION[
                    region_id
                ],
                "assignment_method": "explicit-offshore",
            }
        )


    output = {
        "description": (
            "Taiwan telephone-area-code region assignments for all 368 "
            "townships. R01-R26 are Taiwan-proper Plonk It source-color "
            "regions. R27-R32 are explicitly assigned offshore regions for "
            "Penghu, Kinmen, and Lienkiang/Matsu. Mainland Rxx telephone-code "
            "answers are assigned separately."
        ),
        "assignment_threshold": ASSIGNMENT_THRESHOLD,
        "neighbor_recovery": True,
        "regions": all_region_metadata,
        "results": all_results,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
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

    # -----------------------------------------------------------------------
    # Console summary
    # -----------------------------------------------------------------------

    print()
    print(
        "Color-region classification complete."
    )

    print()
    print(
        f"Detected color regions: {len(clusters)}"
    )

    print(
        f"Neighbor recovered:     {recovered_count}"
    )

    print(
        f"Classified mainland:    {classified_count}"
    )

    print(
        f"Unclassified mainland:  {unclassified_count}"
    )

    print(
        f"Offshore assigned:      {offshore_assigned_count}"
    )

    print(
        f"Total townships:        {len(all_results)}"
    )

    print(
        f"Total regions:          {len(all_region_metadata)}"
    )

    print(
        f"Connected groups:       {len(groups)}"
    )

    print()
    print(
        "Temporary region counts:"
    )

    region_counts = Counter(
        result[
            "region_id"
        ]
        for result
        in preliminary_results.values()
        if result[
            "region_id"
        ] is not None
    )

    for region_id in sorted(
        region_counts
    ):
        metadata = next(
            region
            for region in region_metadata
            if region[
                "region_id"
            ] == region_id
        )

        rgb = metadata[
            "source_representative_rgb"
        ]

        print(
            f"  {region_id}: "
            f"{region_counts[region_id]:3} townships "
            f"source RGB={tuple(rgb)}"
        )

    if unclassified_count:
        print()
        print(
            "Unclassified mainland townships:"
        )

        for result in sorted(
            preliminary_results.values(),
            key=lambda item: (
                item.get(
                    "county"
                ) or "",
                item.get(
                    "township"
                ) or "",
            ),
        ):
            if result[
                "status"
            ] != "unclassified":
                continue

            print(
                "  "
                f"{result['county']} — "
                f"{result['township']} "
                f"({result['township_id']}) "
                f"prefix={result['one_digit_prefix']} "
                f"confidence={result['confidence']:.3f} "
                f"votes={result['region_votes']}"
            )

    print()
    print(
        f"Data: {OUTPUT_PATH.relative_to(ROOT)}"
    )

    print(
        f"Diagnostic: {DIAGNOSTIC_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()