"""
Inspect candidate Indonesia area-code-prefix assignments from a raster map.

Purpose
-------
This script compares GeoPedia's kabupaten/kota boundaries with a raster
reference map showing Indonesia's telephone area-code-prefix regions.

The geographic calibration was established manually using diagnostic overlay
PNGs. Those calibration values are now treated as fixed inspection metadata.

This stage:

    1. loads the area-code reference raster
    2. loads GeoPedia's simplified regencies.geojson
    3. applies the calibrated geographic-to-raster transformations
    4. identifies reference colors around known printed prefix labels
    5. classifies raster pixels using both:
           - similarity to a reference fill color
           - geographic proximity to matching prefix-label anchors
    6. measures each kabupaten/kota's overlap with candidate prefix regions
    7. writes a diagnostic CSV
    8. generates candidate-assignment overlay PNGs for manual review

This script does NOT generate final GeoJSON.

After the candidate assignments have been manually reviewed, the accepted
regency_id -> prefix_2 mapping should be frozen into an explicit deterministic
crosswalk. The final processing script should use that crosswalk rather than
perform raster analysis.

Telephone-prefix convention
---------------------------
The source map displays values such as:

    021
    022
    031
    040
    061

GeoPedia stores the significant two-digit prefix without the Indonesian trunk
zero:

    021 -> "21"
    031 -> "31"
    040 -> "40"

These values are called area-code PREFIXES because some Indonesian landline
area codes contain an additional digit.

Inputs
------
Reference raster:

    data/raw/countries/indonesia/area-codes/area-code-map.webp

GeoPedia boundaries:

    public/data/countries/indonesia/geojson/regencies.geojson

Outputs
-------
    data/intermediate/countries/indonesia/area-codes/
        candidates.csv
        candidates-national.png
        candidates-sumatra.png
        candidates-java.png
        candidates-kalimantan.png
        candidates-sulawesi.png
        candidates-eastern-indonesia.png

The existing calibration overlays are not overwritten by this stage.

Requirements
------------
    pip install geopandas pillow numpy shapely

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/inspect/area-code-prefixes.py
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import geopandas as gpd
import numpy as np
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPolygon,
    Polygon,
)


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

AREA_CODE_IMAGE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "indonesia"
    / "area-codes"
    / "area-code-map.webp"
)

REGENCIES_GEOJSON = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "indonesia"
    / "geojson"
    / "regencies.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "indonesia"
    / "area-codes"
)

CANDIDATES_CSV = (
    OUTPUT_DIR
    / "candidates.csv"
)


# ---------------------------------------------------------------------------
# Expected source structure
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 522
EXPECTED_ADMINISTRATIVE_COUNT = 514
EXPECTED_SPECIAL_COUNT = 8


SPECIAL_FEATURE_IDS = {
    "ID1288",  # Danau Toba
    "ID1388",  # Danau
    "ID1688",  # Danau
    "ID1888",  # Danau
    "ID3288",  # Waduk Cirata
    "ID3388",  # Wadung Kedungombo
    "ID3399",  # Hutan
    "ID7188",  # Danau
}


# ---------------------------------------------------------------------------
# Reference-raster calibration
# ---------------------------------------------------------------------------

REFERENCE_WIDTH = 2048
REFERENCE_HEIGHT = 753

REFERENCE_MAP_LEFT = 11
REFERENCE_MAP_RIGHT = 2037
REFERENCE_MAP_TOP = 40
REFERENCE_MAP_BOTTOM = 742


# ---------------------------------------------------------------------------
# Frozen global calibration
# ---------------------------------------------------------------------------

GLOBAL_X_OFFSET = 0.0
GLOBAL_Y_OFFSET = -18.0

GLOBAL_X_SCALE = 1.025
GLOBAL_Y_SCALE = 1.035


# ---------------------------------------------------------------------------
# Frozen regional calibration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegionalCalibration:
    """Local correction applied after the global projection."""

    x_offset: float = 0.0
    y_offset: float = 0.0

    x_scale: float = 1.0
    y_scale: float = 1.0


REGIONAL_CALIBRATIONS = {
    "sumatra": RegionalCalibration(
        x_offset=8.0,
        y_offset=-10.0,
        x_scale=1.018,
        y_scale=1.018,
    ),
    "java": RegionalCalibration(
        x_offset=8.0,
        y_offset=6.0,
        x_scale=1.000,
        y_scale=1.010,
    ),
    "kalimantan": RegionalCalibration(
        x_offset=7.0,
        y_offset=-7.0,
        x_scale=1.005,
        y_scale=1.008,
    ),
    "sulawesi": RegionalCalibration(
        x_offset=1.0,
        y_offset=0.0,
        x_scale=1.008,
        y_scale=1.010,
    ),
    "eastern-indonesia": RegionalCalibration(
        x_offset=-7.0,
        y_offset=-3.0,
        x_scale=1.005,
        y_scale=1.010,
    ),
}


# ---------------------------------------------------------------------------
# GeoPedia region -> calibration group
# ---------------------------------------------------------------------------

# Nusa Tenggara is left on the global calibration because it lies between the
# Java and eastern diagnostic regions and already aligned sufficiently well
# in the nationwide inspection.
#
# Maluku and Papua use the eastern-Indonesia correction.

REGION_CALIBRATION_GROUPS = {
    "sumatra": "sumatra",
    "java": "java",
    "nusa-tenggara": None,
    "kalimantan": "kalimantan",
    "sulawesi": "sulawesi",
    "maluku": "eastern-indonesia",
    "papua": "eastern-indonesia",
}


# ---------------------------------------------------------------------------
# Printed prefix-label anchors
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LabelAnchor:
    """
    Printed prefix-label position and optional fill-sampling position.

    label_x / label_y describe where the prefix is printed on the reference
    map and are used for spatial classification.

    sample_x / sample_y optionally point to a known interior pixel belonging
    to that prefix region. This is necessary when the printed label itself is
    over water or whitespace, such as 038 and 091.
    """

    full_label: str

    label_x: int
    label_y: int

    sample_x: int | None = None
    sample_y: int | None = None

    @property
    def prefix_2(self) -> str:
        return self.full_label[1:]

    @property
    def effective_sample_x(self) -> int:
        return (
            self.sample_x
            if self.sample_x is not None
            else self.label_x
        )

    @property
    def effective_sample_y(self) -> int:
        return (
            self.sample_y
            if self.sample_y is not None
            else self.label_y
        )


LABEL_ANCHORS = [
    # Sumatra
    LabelAnchor("065", 31, 58),
    LabelAnchor("064", 106, 57),
    LabelAnchor("061", 161, 100),
    LabelAnchor("062", 185, 129),
    LabelAnchor("063", 187, 199),
    LabelAnchor("076", 302, 253),
    LabelAnchor("077", 431, 238),
    LabelAnchor("075", 231, 300),
    LabelAnchor("074", 343, 335),
    LabelAnchor("073", 347, 420),
    LabelAnchor("071", 436, 395),
    LabelAnchor("072", 449, 477),

    # Java / Bali / Nusa Tenggara
    LabelAnchor("021", 523, 527),
    LabelAnchor("025", 505, 554),
    LabelAnchor("022", 558, 576),
    LabelAnchor("026", 584, 592),
    LabelAnchor("023", 594, 527),
    LabelAnchor("028", 637, 574),
    LabelAnchor("024", 685, 582),
    LabelAnchor("027", 693, 610),
    LabelAnchor("029", 716, 543),
    LabelAnchor("035", 741, 573),
    LabelAnchor("031", 789, 586),
    LabelAnchor("032", 824, 575),
    LabelAnchor("034", 781, 627),
    LabelAnchor("033", 836, 624),
    LabelAnchor("036", 900, 635),
    LabelAnchor("037", 997, 645),
    LabelAnchor(
        "038",
        1207,
        687,
        sample_x=1295,
        sample_y=687,
    ),

    # Kalimantan
    LabelAnchor("056", 723, 256),
    LabelAnchor("053", 750, 348),
    LabelAnchor("052", 899, 349),
    LabelAnchor("051", 901, 406),
    LabelAnchor("055", 953, 131),
    LabelAnchor("054", 952, 259),

    # Sulawesi
    LabelAnchor("044", 1184, 228),
    LabelAnchor("043", 1292, 216),
    LabelAnchor("045", 1112, 321),
    LabelAnchor("046", 1207, 319),
    LabelAnchor("047", 1138, 379),
    LabelAnchor("042", 1083, 421),
    LabelAnchor("040", 1216, 426),
    LabelAnchor("048", 1159, 466),
    LabelAnchor("041", 1106, 524),

    # Maluku / Papua
    LabelAnchor("092", 1457, 292),
    LabelAnchor("093", 1514, 418),
    LabelAnchor("095", 1678, 337),
    LabelAnchor(
        "091",
        1515,
        507,
        sample_x=1600,
        sample_y=595,
    ),
    LabelAnchor("098", 1817, 391),
    LabelAnchor("096", 1964, 409),
    LabelAnchor("090", 1887, 487),
    LabelAnchor("097", 2001, 531),
]

REGION_ALLOWED_PREFIXES = {
    "sumatra": {
        "61", "62", "63", "64", "65",
        "71", "72", "73", "74", "75", "76", "77",
    },

    "java": {
        "21", "22", "23", "24", "25", "26",
        "27", "28", "29",
        "31", "32", "33", "34", "35", "36",
    },

    "nusa-tenggara": {
        "36", "37", "38",
    },

    "kalimantan": {
        "51", "52", "53", "54", "55", "56",
    },

    "sulawesi": {
        "40", "41", "42", "43", "44",
        "45", "46", "47", "48",
    },

    "maluku": {
        "91", "92", "93",
    },

    "papua": {
        "90", "95", "96", "97", "98",
    },
}


# ---------------------------------------------------------------------------
# Color-analysis settings
# ---------------------------------------------------------------------------

BACKGROUND_THRESHOLD = 245
DARK_THRESHOLD = 75

ANCHOR_SEARCH_RADIUS = 22

COLOR_QUANTIZATION_STEP = 8

# A source pixel is considered compatible with an anchor's fill color when
# its RGB distance is at most this value.
COLOR_DISTANCE_TOLERANCE = 30.0

# Color is the primary criterion. Distance to the printed label is only used
# to distinguish spatially separate prefixes that reuse the same fill color.
#
# This value controls how strongly physical distance influences the score.
SPATIAL_DISTANCE_WEIGHT = 0.015


# ---------------------------------------------------------------------------
# Candidate confidence
# ---------------------------------------------------------------------------

HIGH_CONFIDENCE = 0.80
REVIEW_CONFIDENCE = 0.60

# Tiny kota may rasterize to very few pixels. Even a high percentage should
# still be reviewed when the evidence consists of fewer pixels than this.
MIN_CLASSIFIED_PIXELS_FOR_HIGH_CONFIDENCE = 20


# ---------------------------------------------------------------------------
# Candidate-overlay appearance
# ---------------------------------------------------------------------------

CANDIDATE_BORDER_COLOR = (
    0,
    255,
    255,
    255,
)

CANDIDATE_LABEL_COLOR = (
    0,
    0,
    0,
    255,
)

REVIEW_LABEL_COLOR = (
    255,
    0,
    0,
    255,
)

CANDIDATE_BORDER_WIDTH = 1

LABEL_MIN_POLYGON_PIXELS = 12


# ---------------------------------------------------------------------------
# Diagnostic regions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DiagnosticRegion:
    id: str
    filename: str

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    padding: int = 35


DIAGNOSTIC_REGIONS = [
    DiagnosticRegion(
        id="sumatra",
        filename="candidates-sumatra.png",
        min_lon=94.5,
        min_lat=-6.5,
        max_lon=107.0,
        max_lat=6.5,
    ),
    DiagnosticRegion(
        id="java",
        filename="candidates-java.png",
        min_lon=104.5,
        min_lat=-9.5,
        max_lon=116.0,
        max_lat=-5.0,
        padding=40,
    ),
    DiagnosticRegion(
        id="kalimantan",
        filename="candidates-kalimantan.png",
        min_lon=108.0,
        min_lat=-5.0,
        max_lon=119.5,
        max_lat=5.0,
    ),
    DiagnosticRegion(
        id="sulawesi",
        filename="candidates-sulawesi.png",
        min_lon=118.0,
        min_lat=-7.0,
        max_lon=126.5,
        max_lat=3.0,
    ),
    DiagnosticRegion(
        id="eastern-indonesia",
        filename="candidates-eastern-indonesia.png",
        min_lon=124.0,
        min_lat=-11.5,
        max_lon=142.0,
        max_lat=3.5,
    ),
]


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GlobalProjection:
    image_width: int
    image_height: int

    map_left: float
    map_right: float
    map_top: float
    map_bottom: float

    geo_min_lon: float
    geo_min_lat: float
    geo_max_lon: float
    geo_max_lat: float


def build_global_projection(
    image: Image.Image,
    regencies: gpd.GeoDataFrame,
) -> GlobalProjection:
    """Build the frozen nationwide baseline transformation."""

    min_lon, min_lat, max_lon, max_lat = (
        float(value)
        for value in regencies.total_bounds
    )

    raster_x_scale = image.width / REFERENCE_WIDTH
    raster_y_scale = image.height / REFERENCE_HEIGHT

    base_left = REFERENCE_MAP_LEFT * raster_x_scale
    base_right = REFERENCE_MAP_RIGHT * raster_x_scale

    base_top = REFERENCE_MAP_TOP * raster_y_scale
    base_bottom = REFERENCE_MAP_BOTTOM * raster_y_scale

    base_center_x = (
        base_left
        + base_right
    ) / 2.0

    base_center_y = (
        base_top
        + base_bottom
    ) / 2.0

    width = (
        base_right
        - base_left
    ) * GLOBAL_X_SCALE

    height = (
        base_bottom
        - base_top
    ) * GLOBAL_Y_SCALE

    center_x = (
        base_center_x
        + GLOBAL_X_OFFSET
    )

    center_y = (
        base_center_y
        + GLOBAL_Y_OFFSET
    )

    return GlobalProjection(
        image_width=image.width,
        image_height=image.height,

        map_left=center_x - width / 2.0,
        map_right=center_x + width / 2.0,
        map_top=center_y - height / 2.0,
        map_bottom=center_y + height / 2.0,

        geo_min_lon=min_lon,
        geo_min_lat=min_lat,
        geo_max_lon=max_lon,
        geo_max_lat=max_lat,
    )


def global_coordinate_to_pixel(
    longitude: float,
    latitude: float,
    projection: GlobalProjection,
) -> tuple[float, float]:
    """Project geographic coordinates with the global transform."""

    x_fraction = (
        longitude
        - projection.geo_min_lon
    ) / (
        projection.geo_max_lon
        - projection.geo_min_lon
    )

    y_fraction = (
        projection.geo_max_lat
        - latitude
    ) / (
        projection.geo_max_lat
        - projection.geo_min_lat
    )

    x = (
        projection.map_left
        + x_fraction
        * (
            projection.map_right
            - projection.map_left
        )
    )

    y = (
        projection.map_top
        + y_fraction
        * (
            projection.map_bottom
            - projection.map_top
        )
    )

    return (
        x,
        y,
    )


def get_calibration_center(
    calibration_group: str,
    projection: GlobalProjection,
) -> tuple[float, float]:
    """Return the approximate geographic center of a calibration group."""

    centers = {
        "sumatra": (100.75, 0.0),
        "java": (110.25, -7.25),
        "kalimantan": (113.75, 0.0),
        "sulawesi": (122.25, -2.0),
        "eastern-indonesia": (133.0, -4.0),
    }

    longitude, latitude = centers[
        calibration_group
    ]

    return global_coordinate_to_pixel(
        longitude,
        latitude,
        projection,
    )


def coordinate_to_pixel(
    longitude: float,
    latitude: float,
    region_id: str,
    projection: GlobalProjection,
) -> tuple[float, float]:
    """
    Project one coordinate using the appropriate frozen regional calibration.
    """

    x, y = global_coordinate_to_pixel(
        longitude,
        latitude,
        projection,
    )

    calibration_group = REGION_CALIBRATION_GROUPS.get(
        region_id
    )

    if calibration_group is None:
        return (
            x,
            y,
        )

    calibration = REGIONAL_CALIBRATIONS[
        calibration_group
    ]

    center_x, center_y = get_calibration_center(
        calibration_group,
        projection,
    )

    x = (
        center_x
        + (
            x
            - center_x
        )
        * calibration.x_scale
        + calibration.x_offset
    )

    y = (
        center_y
        + (
            y
            - center_y
        )
        * calibration.y_scale
        + calibration.y_offset
    )

    return (
        x,
        y,
    )


# ---------------------------------------------------------------------------
# Reference-anchor scaling
# ---------------------------------------------------------------------------

def scale_reference_point(
    x: int,
    y: int,
    image: Image.Image,
) -> tuple[float, float]:
    """Scale a reference-map coordinate to the loaded raster."""

    return (
        x
        * image.width
        / REFERENCE_WIDTH,
        y
        * image.height
        / REFERENCE_HEIGHT,
    )


def scale_anchor_label(
    anchor: LabelAnchor,
    image: Image.Image,
) -> tuple[float, float]:
    """Scale an anchor's printed-label position."""

    return scale_reference_point(
        anchor.label_x,
        anchor.label_y,
        image,
    )


def scale_anchor_sample(
    anchor: LabelAnchor,
    image: Image.Image,
) -> tuple[float, float]:
    """Scale an anchor's fill-sampling position."""

    return scale_reference_point(
        anchor.effective_sample_x,
        anchor.effective_sample_y,
        image,
    )
    

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

RGB = tuple[int, int, int]


def is_background(
    color: RGB,
) -> bool:
    return all(
        channel >= BACKGROUND_THRESHOLD
        for channel in color
    )


def is_dark(
    color: RGB,
) -> bool:
    return all(
        channel <= DARK_THRESHOLD
        for channel in color
    )


def quantize_color(
    color: RGB,
) -> RGB:
    return tuple(
        max(
            0,
            min(
                255,
                int(
                    round(
                        channel
                        / COLOR_QUANTIZATION_STEP
                    )
                    * COLOR_QUANTIZATION_STEP
                ),
            ),
        )
        for channel in color
    )


def color_distance(
    first: RGB,
    second: RGB,
) -> float:
    return math.sqrt(
        sum(
            (
                first_channel
                - second_channel
            ) ** 2
            for first_channel, second_channel in zip(
                first,
                second,
            )
        )
    )


# ---------------------------------------------------------------------------
# Reference-prefix information
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PrefixReference:
    prefix_2: str

    anchor_x: float
    anchor_y: float

    color: RGB


def extract_anchor_color(
    image: Image.Image,
    anchor: LabelAnchor,
) -> RGB:
    """
    Estimate the dominant non-background fill color around a printed label.
    """

    anchor_x, anchor_y = scale_anchor_sample(
        anchor,
        image,
    )

    radius_x = max(
        1,
        round(
            ANCHOR_SEARCH_RADIUS
            * image.width
            / REFERENCE_WIDTH
        ),
    )

    radius_y = max(
        1,
        round(
            ANCHOR_SEARCH_RADIUS
            * image.height
            / REFERENCE_HEIGHT
        ),
    )

    pixels = image.load()

    colors: Counter[RGB] = Counter()

    for y in range(
        max(
            0,
            round(
                anchor_y
                - radius_y
            ),
        ),
        min(
            image.height,
            round(
                anchor_y
                + radius_y
                + 1
            ),
        ),
    ):
        for x in range(
            max(
                0,
                round(
                    anchor_x
                    - radius_x
                ),
            ),
            min(
                image.width,
                round(
                    anchor_x
                    + radius_x
                    + 1
                ),
            ),
        ):
            raw = pixels[
                x,
                y,
            ]

            color = (
                int(
                    raw[0]
                ),
                int(
                    raw[1]
                ),
                int(
                    raw[2]
                ),
            )

            if is_background(
                color
            ):
                continue

            if is_dark(
                color
            ):
                continue

            colors[
                quantize_color(
                    color
                )
            ] += 1

    if not colors:
        raise ValueError(
            "Could not determine reference fill color for "
            f"{anchor.full_label}."
        )

    return colors.most_common(
        1
    )[0][0]


def build_prefix_references(
    image: Image.Image,
) -> list[PrefixReference]:
    """Build the spatial/color reference for every printed prefix."""

    references = []

    for anchor in LABEL_ANCHORS:
        x, y = scale_anchor_label(
            anchor,
            image,
        )

        color = extract_anchor_color(
            image,
            anchor,
        )

        references.append(
            PrefixReference(
                prefix_2=anchor.prefix_2,
                anchor_x=x,
                anchor_y=y,
                color=color,
            )
        )

    return references


# ---------------------------------------------------------------------------
# Pixel classification
# ---------------------------------------------------------------------------

def classify_pixel(
    color: RGB,
    x: int,
    y: int,
    references: list[PrefixReference],
    allowed_prefixes: set[str],
) -> str | None:
    """
    Classify one raster pixel.

    First reject references whose fill color is too different. Among the
    remaining color-compatible prefixes, choose the spatially closest label.

    This allows distinct prefixes that reuse the same map color to remain
    separate.
    """

    if is_background(
        color
    ):
        return None

    if is_dark(
        color
    ):
        return None

    candidates = []

    for reference in references:
        if reference.prefix_2 not in allowed_prefixes:
            continue

        difference = color_distance(
            color,
            reference.color,
        )

        if difference > COLOR_DISTANCE_TOLERANCE:
            continue

        spatial_distance = math.hypot(
            x
            - reference.anchor_x,
            y
            - reference.anchor_y,
        )

        score = (
            difference
            + spatial_distance
            * SPATIAL_DISTANCE_WEIGHT
        )

        candidates.append(
            (
                score,
                reference.prefix_2,
            )
        )

    if not candidates:
        return None

    candidates.sort()

    return candidates[
        0
    ][1]


# ---------------------------------------------------------------------------
# Geometry rasterization
# ---------------------------------------------------------------------------

def ring_to_pixels(
    ring,
    region_id: str,
    projection: GlobalProjection,
) -> list[tuple[float, float]]:
    """Project a polygon ring into raster pixels."""

    return [
        coordinate_to_pixel(
            float(
                coordinate[0]
            ),
            float(
                coordinate[1]
            ),
            region_id,
            projection,
        )
        for coordinate in ring.coords
    ]


def draw_polygon_mask(
    draw: ImageDraw.ImageDraw,
    polygon: Polygon,
    region_id: str,
    projection: GlobalProjection,
) -> None:
    """Rasterize one Polygon."""

    exterior = ring_to_pixels(
        polygon.exterior,
        region_id,
        projection,
    )

    draw.polygon(
        exterior,
        fill=255,
    )

    for interior in polygon.interiors:
        hole = ring_to_pixels(
            interior,
            region_id,
            projection,
        )

        draw.polygon(
            hole,
            fill=0,
        )


def geometry_mask(
    geometry,
    region_id: str,
    projection: GlobalProjection,
) -> np.ndarray:
    """Rasterize one Polygon or MultiPolygon."""

    mask = Image.new(
        "L",
        (
            projection.image_width,
            projection.image_height,
        ),
        0,
    )

    draw = ImageDraw.Draw(
        mask
    )

    if isinstance(
        geometry,
        Polygon,
    ):
        draw_polygon_mask(
            draw,
            geometry,
            region_id,
            projection,
        )

    elif isinstance(
        geometry,
        MultiPolygon,
    ):
        for polygon in geometry.geoms:
            draw_polygon_mask(
                draw,
                polygon,
                region_id,
                projection,
            )

    else:
        raise ValueError(
            "Unsupported feature geometry: "
            f"{geometry.geom_type}"
        )

    return (
        np.asarray(
            mask
        )
        > 0
    )


# ---------------------------------------------------------------------------
# Candidate assignments
# ---------------------------------------------------------------------------

@dataclass
class CandidateAssignment:
    regency_id: str
    regency: str

    province_id: str
    province: str

    region_id: str
    region: str

    prefix_2: str | None

    confidence: float

    second_prefix: str | None
    second_share: float

    classified_pixels: int
    polygon_pixels: int

    classified_share: float

    status: str


def inspect_feature(
    row,
    image_array: np.ndarray,
    references: list[PrefixReference],
    projection: GlobalProjection,
) -> CandidateAssignment:
    """Calculate the raster-derived prefix candidate for one regency."""

    region_id = str(
        row.region_id
    )

    mask = geometry_mask(
        row.geometry,
        region_id,
        projection,
    )

    polygon_pixels = int(
        mask.sum()
    )

    if polygon_pixels == 0:
        return CandidateAssignment(
            regency_id=str(
                row.regency_id
            ),
            regency=str(
                row.regency
            ),
            province_id=str(
                row.province_id
            ),
            province=str(
                row.province
            ),
            region_id=region_id,
            region=str(
                row.region
            ),
            prefix_2=None,
            confidence=0.0,
            second_prefix=None,
            second_share=0.0,
            classified_pixels=0,
            polygon_pixels=0,
            classified_share=0.0,
            status="NO_PIXELS",
        )

    ys, xs = np.where(
        mask
    )

    counts: Counter[str] = Counter()

    for y, x in zip(
        ys,
        xs,
    ):
        pixel = image_array[
            y,
            x,
            :3,
        ]

        color = (
            int(
                pixel[0]
            ),
            int(
                pixel[1]
            ),
            int(
                pixel[2]
            ),
        )

        prefix = classify_pixel(
            color,
            int(
                x
            ),
            int(
                y
            ),
            references,
            REGION_ALLOWED_PREFIXES[
                region_id
            ],
        )

        if prefix is not None:
            counts[
                prefix
            ] += 1

    classified_pixels = sum(
        counts.values()
    )

    classified_share = (
        classified_pixels
        / polygon_pixels
        if polygon_pixels
        else 0.0
    )

    if classified_pixels == 0:
        return CandidateAssignment(
            regency_id=str(
                row.regency_id
            ),
            regency=str(
                row.regency
            ),
            province_id=str(
                row.province_id
            ),
            province=str(
                row.province
            ),
            region_id=region_id,
            region=str(
                row.region
            ),
            prefix_2=None,
            confidence=0.0,
            second_prefix=None,
            second_share=0.0,
            classified_pixels=0,
            polygon_pixels=polygon_pixels,
            classified_share=0.0,
            status="UNCLASSIFIED",
        )

    ranked = counts.most_common()

    prefix_2, best_count = ranked[
        0
    ]

    confidence = (
        best_count
        / classified_pixels
    )

    second_prefix = None
    second_share = 0.0

    if len(
        ranked
    ) > 1:
        second_prefix = ranked[
            1
        ][0]

        second_share = (
            ranked[
                1
            ][1]
            / classified_pixels
        )

    if (
        confidence >= HIGH_CONFIDENCE
        and classified_pixels
        >= MIN_CLASSIFIED_PIXELS_FOR_HIGH_CONFIDENCE
    ):
        status = "HIGH"

    elif confidence >= REVIEW_CONFIDENCE:
        status = "REVIEW"

    else:
        status = "UNCERTAIN"

    if (
        classified_pixels
        < MIN_CLASSIFIED_PIXELS_FOR_HIGH_CONFIDENCE
        and status == "HIGH"
    ):
        status = "REVIEW"

    return CandidateAssignment(
        regency_id=str(
            row.regency_id
        ),
        regency=str(
            row.regency
        ),
        province_id=str(
            row.province_id
        ),
        province=str(
            row.province
        ),
        region_id=region_id,
        region=str(
            row.region
        ),
        prefix_2=prefix_2,
        confidence=confidence,
        second_prefix=second_prefix,
        second_share=second_share,
        classified_pixels=classified_pixels,
        polygon_pixels=polygon_pixels,
        classified_share=classified_share,
        status=status,
    )


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def write_candidates_csv(
    assignments: list[CandidateAssignment],
) -> None:
    """Write the complete diagnostic candidate table."""

    with CANDIDATES_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(
            file
        )

        writer.writerow(
            [
                "regency_id",
                "regency",
                "province_id",
                "province",
                "region_id",
                "region",
                "prefix_2",
                "display",
                "confidence",
                "second_prefix",
                "second_display",
                "second_share",
                "classified_pixels",
                "polygon_pixels",
                "classified_share",
                "status",
            ]
        )

        for assignment in assignments:
            writer.writerow(
                [
                    assignment.regency_id,
                    assignment.regency,
                    assignment.province_id,
                    assignment.province,
                    assignment.region_id,
                    assignment.region,

                    assignment.prefix_2
                    or "",

                    (
                        f"0{assignment.prefix_2}-"
                        if assignment.prefix_2
                        else ""
                    ),

                    f"{assignment.confidence:.6f}",

                    assignment.second_prefix
                    or "",

                    (
                        f"0{assignment.second_prefix}-"
                        if assignment.second_prefix
                        else ""
                    ),

                    f"{assignment.second_share:.6f}",

                    assignment.classified_pixels,
                    assignment.polygon_pixels,

                    f"{assignment.classified_share:.6f}",

                    assignment.status,
                ]
            )


# ---------------------------------------------------------------------------
# Candidate-overlay drawing
# ---------------------------------------------------------------------------

def draw_line_geometry(
    draw: ImageDraw.ImageDraw,
    geometry,
    projector: Callable,
    color,
    width: int,
) -> None:
    """Draw arbitrary polygon-boundary geometry."""

    if geometry is None:
        return

    if geometry.is_empty:
        return

    if isinstance(
        geometry,
        LineString,
    ):
        points = [
            projector(
                coordinate
            )
            for coordinate in geometry.coords
        ]

        if len(
            points
        ) >= 2:
            draw.line(
                points,
                fill=color,
                width=width,
            )

        return

    if isinstance(
        geometry,
        MultiLineString,
    ):
        for line in geometry.geoms:
            draw_line_geometry(
                draw,
                line,
                projector,
                color,
                width,
            )

        return

    if isinstance(
        geometry,
        Polygon,
    ):
        draw_line_geometry(
            draw,
            geometry.boundary,
            projector,
            color,
            width,
        )

        return

    if isinstance(
        geometry,
        MultiPolygon,
    ):
        for polygon in geometry.geoms:
            draw_line_geometry(
                draw,
                polygon.boundary,
                projector,
                color,
                width,
            )

        return

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        for child in geometry.geoms:
            draw_line_geometry(
                draw,
                child,
                projector,
                color,
                width,
            )

        return


def feature_label_pixel(
    row,
    projection: GlobalProjection,
) -> tuple[float, float]:
    """Project a representative point for candidate text."""

    point = row.geometry.representative_point()

    return coordinate_to_pixel(
        float(
            point.x
        ),
        float(
            point.y
        ),
        str(
            row.region_id
        ),
        projection,
    )


def render_candidate_overlay(
    image: Image.Image,
    administrative: gpd.GeoDataFrame,
    assignments_by_id: dict[str, CandidateAssignment],
    projection: GlobalProjection,
) -> Image.Image:
    """Render candidate prefix labels over the original reference raster."""

    base = image.convert(
        "RGBA"
    )

    drawing = Image.new(
        "RGBA",
        base.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        drawing
    )

    font = ImageFont.load_default()

    for row in administrative.itertuples():
        region_id = str(
            row.region_id
        )

        def projector(
            coordinate,
        ):
            return coordinate_to_pixel(
                float(
                    coordinate[0]
                ),
                float(
                    coordinate[1]
                ),
                region_id,
                projection,
            )

        draw_line_geometry(
            draw,
            row.geometry.boundary,
            projector,
            CANDIDATE_BORDER_COLOR,
            CANDIDATE_BORDER_WIDTH,
        )

        assignment = assignments_by_id[
            str(
                row.regency_id
            )
        ]

        if assignment.polygon_pixels < LABEL_MIN_POLYGON_PIXELS:
            continue

        if assignment.prefix_2 is None:
            label = "?"
        else:
            label = assignment.prefix_2

        x, y = feature_label_pixel(
            row,
            projection,
        )

        label_color = (
            CANDIDATE_LABEL_COLOR
            if assignment.status == "HIGH"
            else REVIEW_LABEL_COLOR
        )

        draw.text(
            (
                round(
                    x
                ),
                round(
                    y
                ),
            ),
            label,
            fill=label_color,
            font=font,
            anchor="mm",
            stroke_width=1,
            stroke_fill=(
                255,
                255,
                255,
                255,
            ),
        )

    return Image.alpha_composite(
        base,
        drawing,
    )


# ---------------------------------------------------------------------------
# Diagnostic crops
# ---------------------------------------------------------------------------

def diagnostic_crop_box(
    region: DiagnosticRegion,
    projection: GlobalProjection,
) -> tuple[int, int, int, int]:
    """Convert a diagnostic geographic extent to a raster crop."""

    corners = [
        (
            region.min_lon,
            region.min_lat,
        ),
        (
            region.min_lon,
            region.max_lat,
        ),
        (
            region.max_lon,
            region.min_lat,
        ),
        (
            region.max_lon,
            region.max_lat,
        ),
    ]

    points = [
        global_coordinate_to_pixel(
            longitude,
            latitude,
            projection,
        )
        for longitude, latitude in corners
    ]

    xs = [
        point[0]
        for point in points
    ]

    ys = [
        point[1]
        for point in points
    ]

    left = max(
        0,
        int(
            min(
                xs
            )
        )
        - region.padding,
    )

    right = min(
        projection.image_width,
        int(
            max(
                xs
            )
        )
        + region.padding,
    )

    top = max(
        0,
        int(
            min(
                ys
            )
        )
        - region.padding,
    )

    bottom = min(
        projection.image_height,
        int(
            max(
                ys
            )
        )
        + region.padding,
    )

    return (
        left,
        top,
        right,
        bottom,
    )


def write_candidate_images(
    overlay: Image.Image,
    projection: GlobalProjection,
) -> None:
    """Write nationwide and regional candidate overlays."""

    national_path = (
        OUTPUT_DIR
        / "candidates-national.png"
    )

    overlay.convert(
        "RGB"
    ).save(
        national_path,
        format="PNG",
    )

    for region in DIAGNOSTIC_REGIONS:
        crop = overlay.crop(
            diagnostic_crop_box(
                region,
                projection,
            )
        )

        crop.convert(
            "RGB"
        ).save(
            OUTPUT_DIR
            / region.filename,
            format="PNG",
        )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_reference_summary(
    references: list[PrefixReference],
) -> None:
    """Print the prefix/color reference extracted from the source."""

    print(
        "=" * 100
    )
    print(
        "REFERENCE PREFIXES"
    )
    print(
        "=" * 100
    )

    for reference in references:
        print(
            f"0{reference.prefix_2}-  "
            f"anchor=({reference.anchor_x:7.1f}, "
            f"{reference.anchor_y:7.1f})  "
            f"RGB{reference.color}"
        )

    print()


def print_assignment_summary(
    assignments: list[CandidateAssignment],
) -> None:
    """Print assignment statistics and every feature needing review."""

    statuses = Counter(
        assignment.status
        for assignment in assignments
    )

    represented = {
        assignment.prefix_2
        for assignment in assignments
        if assignment.prefix_2
    }

    print(
        "=" * 100
    )
    print(
        "ASSIGNMENT SUMMARY"
    )
    print(
        "=" * 100
    )

    print(
        f"Administrative features:       "
        f"{len(assignments):,}"
    )

    print(
        f"Reference prefixes:             "
        f"{len(LABEL_ANCHORS):,}"
    )

    print(
        f"Prefixes represented:           "
        f"{len(represented):,}"
    )

    print(
        f"High confidence:                "
        f"{statuses['HIGH']:,}"
    )

    print(
        f"Review:                         "
        f"{statuses['REVIEW']:,}"
    )

    print(
        f"Uncertain:                      "
        f"{statuses['UNCERTAIN']:,}"
    )

    print(
        f"Unclassified:                   "
        f"{statuses['UNCLASSIFIED']:,}"
    )

    print(
        f"No pixels:                      "
        f"{statuses['NO_PIXELS']:,}"
    )

    print()

    print(
        "=" * 100
    )
    print(
        "REVIEW / UNCERTAIN"
    )
    print(
        "=" * 100
    )

    review = [
        assignment
        for assignment in assignments
        if assignment.status != "HIGH"
    ]

    review.sort(
        key=lambda assignment: (
            assignment.region_id,
            assignment.province,
            assignment.regency,
        )
    )

    if not review:
        print(
            "None."
        )

    for assignment in review:
        best = (
            f"0{assignment.prefix_2}-"
            if assignment.prefix_2
            else "-"
        )

        second = (
            f"0{assignment.second_prefix}-"
            if assignment.second_prefix
            else "-"
        )

        print(
            f"{assignment.regency_id:<10} "
            f"{assignment.province:<24} "
            f"{assignment.regency:<30} "
            f"best={best:<6} "
            f"{assignment.confidence:>6.1%}  "
            f"second={second:<6} "
            f"{assignment.second_share:>6.1%}  "
            f"classified={assignment.classified_share:>6.1%}  "
            f"pixels={assignment.classified_pixels:>5}  "
            f"{assignment.status}"
        )

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate raster-derived Indonesia area-code-prefix candidates."""

    print(
        "Generating Indonesia area-code-prefix candidates..."
    )
    print()

    if not AREA_CODE_IMAGE.exists():
        raise FileNotFoundError(
            "Area-code reference image not found:\n"
            f"  {AREA_CODE_IMAGE}"
        )

    if not REGENCIES_GEOJSON.exists():
        raise FileNotFoundError(
            "Regencies GeoJSON not found:\n"
            f"  {REGENCIES_GEOJSON}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    image = Image.open(
        AREA_CODE_IMAGE
    ).convert(
        "RGB"
    )

    image_array = np.asarray(
        image
    )

    regencies = gpd.read_file(
        REGENCIES_GEOJSON
    )

    if len(
        regencies
    ) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected regencies.geojson feature count: "
            f"expected {EXPECTED_FEATURE_COUNT:,}, "
            f"got {len(regencies):,}."
        )

    special_mask = (
        regencies[
            "regency_id"
        ]
        .astype(
            str
        )
        .isin(
            SPECIAL_FEATURE_IDS
        )
    )

    special_count = int(
        special_mask.sum()
    )

    if special_count != EXPECTED_SPECIAL_COUNT:
        raise ValueError(
            "Unexpected special-feature count: "
            f"expected {EXPECTED_SPECIAL_COUNT:,}, "
            f"got {special_count:,}."
        )

    administrative = regencies[
        ~special_mask
    ].copy()

    if len(
        administrative
    ) != EXPECTED_ADMINISTRATIVE_COUNT:
        raise ValueError(
            "Unexpected administrative count: "
            f"expected {EXPECTED_ADMINISTRATIVE_COUNT:,}, "
            f"got {len(administrative):,}."
        )

    projection = build_global_projection(
        image,
        regencies,
    )

    references = build_prefix_references(
        image
    )

    print(
        f"Reference image:               "
        f"{image.width} x {image.height}"
    )

    print(
        f"GeoJSON features:              "
        f"{len(regencies):,}"
    )

    print(
        f"Administrative features:       "
        f"{len(administrative):,}"
    )

    print(
        f"Excluded special features:     "
        f"{special_count:,}"
    )

    print(
        f"Reference prefixes:            "
        f"{len(references):,}"
    )

    print()

    print_reference_summary(
        references
    )

    assignments = []

    total = len(
        administrative
    )

    for index, row in enumerate(
        administrative.itertuples(),
        start=1,
    ):
        assignment = inspect_feature(
            row,
            image_array,
            references,
            projection,
        )

        assignments.append(
            assignment
        )

        if (
            index % 50 == 0
            or index == total
        ):
            print(
                f"Classified "
                f"{index:,} / {total:,} features..."
            )

    print()

    write_candidates_csv(
        assignments
    )

    assignments_by_id = {
        assignment.regency_id: assignment
        for assignment in assignments
    }

    print(
        "Rendering candidate diagnostic overlays..."
    )

    candidate_overlay = render_candidate_overlay(
        image,
        administrative,
        assignments_by_id,
        projection,
    )

    write_candidate_images(
        candidate_overlay,
        projection,
    )

    print()

    print_assignment_summary(
        assignments
    )

    print(
        "=" * 100
    )
    print(
        "OUTPUT"
    )
    print(
        "=" * 100
    )

    outputs = [
        CANDIDATES_CSV,
        OUTPUT_DIR
        / "candidates-national.png",
        *[
            OUTPUT_DIR
            / region.filename
            for region in DIAGNOSTIC_REGIONS
        ],
    ]

    for path in outputs:
        print(
            path.relative_to(
                PROJECT_ROOT
            )
        )

    print()
    print(
        "Candidate inspection complete."
    )
    print(
        "These assignments are diagnostic only and must be reviewed "
        "before becoming the final crosswalk."
    )


if __name__ == "__main__":
    main()