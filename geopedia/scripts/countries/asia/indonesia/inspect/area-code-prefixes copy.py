"""
Generate calibration overlays for Indonesia's area-code reference map.

Purpose
-------
This inspection script aligns GeoPedia's kabupaten/kota boundaries with the
raster reference map of Indonesia's telephone area-code prefixes.

It deliberately does NOT classify regencies or generate area-code data.

Two calibration stages are supported:

1. Global calibration
   Applied to the nationwide diagnostic overlay and used as the common
   baseline for every regional calibration.

2. Regional calibration
   Applied independently around each region's geographic center. This allows
   local differences in the reference raster to be corrected without making
   another region worse.

The nationwide image always uses only the global calibration. It is intended
as the first sanity check after every run.

Regional images use the global calibration plus their own local correction.

Outputs
-------
    data/intermediate/countries/indonesia/area-codes/
        overlay-national.png
        overlay-sumatra.png
        overlay-java.png
        overlay-kalimantan.png
        overlay-sulawesi.png
        overlay-eastern-indonesia.png

Appearance
----------
    Magenta = GeoPedia kabupaten/kota boundaries
    Cyan    = GeoPedia province boundaries

Inputs
------
Reference raster:

    data/raw/countries/indonesia/area-codes/area-code-map.webp

GeoPedia boundaries:

    public/data/countries/indonesia/geojson/regencies.geojson

Requirements
------------
    pip install geopandas pillow shapely

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/inspect/area-code-prefixes.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
from PIL import Image, ImageDraw
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPolygon,
    Polygon,
)
from shapely.ops import unary_union


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


# ---------------------------------------------------------------------------
# Expected source structure
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 522


# ---------------------------------------------------------------------------
# Reference-raster calibration
# ---------------------------------------------------------------------------

# The original calibration was measured against a 2048x753 working copy.
# These values are automatically scaled to the actual raster dimensions.

REFERENCE_WIDTH = 2048
REFERENCE_HEIGHT = 753

REFERENCE_MAP_LEFT = 11
REFERENCE_MAP_RIGHT = 2037
REFERENCE_MAP_TOP = 40
REFERENCE_MAP_BOTTOM = 742


# ---------------------------------------------------------------------------
# Global calibration
# ---------------------------------------------------------------------------

# These values are applied to the complete GeoJSON extent.
#
# The current values come from the second nationwide calibration pass.
#
# Do not use these to correct small regional differences anymore. Once the
# nationwide alignment is reasonably close, use REGIONAL_CALIBRATIONS below.

GLOBAL_X_OFFSET = 0.0
GLOBAL_Y_OFFSET = -18.0

GLOBAL_X_SCALE = 1.025
GLOBAL_Y_SCALE = 1.035


# ---------------------------------------------------------------------------
# Regional calibration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegionalCalibration:
    """
    Additional local transform applied after the global transform.

    x_offset / y_offset:
        Pixel translation after the global projection.

    x_scale / y_scale:
        Local scaling around this region's own projected center.

    Values of 1.0 and 0.0 mean no regional correction.
    """

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
# Overlay appearance
# ---------------------------------------------------------------------------

REGENCY_COLOR = (
    255,
    0,
    255,
    230,
)

PROVINCE_COLOR = (
    0,
    255,
    255,
    255,
)

REGENCY_LINE_WIDTH = 1
PROVINCE_LINE_WIDTH = 3


# ---------------------------------------------------------------------------
# Regional definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Region:
    """Regional diagnostic area and local calibration definition."""

    id: str
    filename: str

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    padding: int = 35


REGIONS = [
    Region(
        id="sumatra",
        filename="overlay-sumatra.png",
        min_lon=94.5,
        min_lat=-6.5,
        max_lon=107.0,
        max_lat=6.5,
        padding=35,
    ),
    Region(
        id="java",
        filename="overlay-java.png",
        min_lon=104.5,
        min_lat=-9.5,
        max_lon=116.0,
        max_lat=-5.0,
        padding=40,
    ),
    Region(
        id="kalimantan",
        filename="overlay-kalimantan.png",
        min_lon=108.0,
        min_lat=-5.0,
        max_lon=119.5,
        max_lat=5.0,
        padding=35,
    ),
    Region(
        id="sulawesi",
        filename="overlay-sulawesi.png",
        min_lon=118.0,
        min_lat=-7.0,
        max_lon=126.5,
        max_lat=3.0,
        padding=35,
    ),
    Region(
        id="eastern-indonesia",
        filename="overlay-eastern-indonesia.png",
        min_lon=124.0,
        min_lat=-11.5,
        max_lon=142.0,
        max_lat=3.5,
        padding=35,
    ),
]


# ---------------------------------------------------------------------------
# Global projection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GlobalProjection:
    """Global geographic-to-raster transformation."""

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
    """Build the nationwide baseline transformation."""

    min_lon, min_lat, max_lon, max_lat = (
        float(value)
        for value in regencies.total_bounds
    )

    raster_x_scale = (
        image.width
        / REFERENCE_WIDTH
    )

    raster_y_scale = (
        image.height
        / REFERENCE_HEIGHT
    )

    base_left = (
        REFERENCE_MAP_LEFT
        * raster_x_scale
    )

    base_right = (
        REFERENCE_MAP_RIGHT
        * raster_x_scale
    )

    base_top = (
        REFERENCE_MAP_TOP
        * raster_y_scale
    )

    base_bottom = (
        REFERENCE_MAP_BOTTOM
        * raster_y_scale
    )

    base_center_x = (
        base_left
        + base_right
    ) / 2.0

    base_center_y = (
        base_top
        + base_bottom
    ) / 2.0

    calibrated_width = (
        base_right
        - base_left
    ) * GLOBAL_X_SCALE

    calibrated_height = (
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

        map_left=(
            center_x
            - calibrated_width / 2.0
        ),
        map_right=(
            center_x
            + calibrated_width / 2.0
        ),
        map_top=(
            center_y
            - calibrated_height / 2.0
        ),
        map_bottom=(
            center_y
            + calibrated_height / 2.0
        ),

        geo_min_lon=min_lon,
        geo_min_lat=min_lat,
        geo_max_lon=max_lon,
        geo_max_lat=max_lat,
    )


# ---------------------------------------------------------------------------
# Coordinate projection
# ---------------------------------------------------------------------------

def global_longitude_to_x(
    longitude: float,
    projection: GlobalProjection,
) -> float:
    """Project longitude using only the global calibration."""

    fraction = (
        longitude
        - projection.geo_min_lon
    ) / (
        projection.geo_max_lon
        - projection.geo_min_lon
    )

    return (
        projection.map_left
        + fraction
        * (
            projection.map_right
            - projection.map_left
        )
    )


def global_latitude_to_y(
    latitude: float,
    projection: GlobalProjection,
) -> float:
    """Project latitude using only the global calibration."""

    fraction = (
        projection.geo_max_lat
        - latitude
    ) / (
        projection.geo_max_lat
        - projection.geo_min_lat
    )

    return (
        projection.map_top
        + fraction
        * (
            projection.map_bottom
            - projection.map_top
        )
    )


def global_coordinate_to_pixel(
    coordinate,
    projection: GlobalProjection,
) -> tuple[float, float]:
    """Project one coordinate using only the nationwide transform."""

    longitude = float(
        coordinate[0]
    )

    latitude = float(
        coordinate[1]
    )

    return (
        global_longitude_to_x(
            longitude,
            projection,
        ),
        global_latitude_to_y(
            latitude,
            projection,
        ),
    )


# ---------------------------------------------------------------------------
# Regional projection
# ---------------------------------------------------------------------------

def get_region_center_pixel(
    region: Region,
    projection: GlobalProjection,
) -> tuple[float, float]:
    """Return a region's center after the global projection."""

    center_lon = (
        region.min_lon
        + region.max_lon
    ) / 2.0

    center_lat = (
        region.min_lat
        + region.max_lat
    ) / 2.0

    return (
        global_longitude_to_x(
            center_lon,
            projection,
        ),
        global_latitude_to_y(
            center_lat,
            projection,
        ),
    )


def regional_coordinate_to_pixel(
    coordinate,
    projection: GlobalProjection,
    region: Region,
) -> tuple[float, float]:
    """
    Apply global projection followed by this region's local transform.

    Scaling occurs around the region's own projected center, preventing a
    correction in one part of Indonesia from shifting another region.
    """

    x, y = global_coordinate_to_pixel(
        coordinate,
        projection,
    )

    center_x, center_y = get_region_center_pixel(
        region,
        projection,
    )

    correction = REGIONAL_CALIBRATIONS[
        region.id
    ]

    x = (
        center_x
        + (
            x
            - center_x
        )
        * correction.x_scale
        + correction.x_offset
    )

    y = (
        center_y
        + (
            y
            - center_y
        )
        * correction.y_scale
        + correction.y_offset
    )

    return (
        x,
        y,
    )


# ---------------------------------------------------------------------------
# Geometry drawing
# ---------------------------------------------------------------------------

def draw_line_string(
    draw: ImageDraw.ImageDraw,
    geometry: LineString,
    coordinate_projector,
    color,
    width: int,
) -> None:
    """Draw one projected LineString."""

    points = [
        coordinate_projector(
            coordinate
        )
        for coordinate in geometry.coords
    ]

    if len(points) < 2:
        return

    draw.line(
        points,
        fill=color,
        width=width,
        joint="curve",
    )


def draw_boundary_geometry(
    draw: ImageDraw.ImageDraw,
    geometry,
    coordinate_projector,
    color,
    width: int,
) -> None:
    """Draw arbitrary boundary geometry."""

    if geometry is None:
        return

    if geometry.is_empty:
        return

    if isinstance(
        geometry,
        LineString,
    ):
        draw_line_string(
            draw,
            geometry,
            coordinate_projector,
            color,
            width,
        )

        return

    if isinstance(
        geometry,
        MultiLineString,
    ):
        for line in geometry.geoms:
            draw_line_string(
                draw,
                line,
                coordinate_projector,
                color,
                width,
            )

        return

    if isinstance(
        geometry,
        Polygon,
    ):
        draw_boundary_geometry(
            draw,
            geometry.boundary,
            coordinate_projector,
            color,
            width,
        )

        return

    if isinstance(
        geometry,
        MultiPolygon,
    ):
        for polygon in geometry.geoms:
            draw_boundary_geometry(
                draw,
                polygon.boundary,
                coordinate_projector,
                color,
                width,
            )

        return

    if isinstance(
        geometry,
        GeometryCollection,
    ):
        for child in geometry.geoms:
            draw_boundary_geometry(
                draw,
                child,
                coordinate_projector,
                color,
                width,
            )

        return

    raise ValueError(
        "Unsupported boundary geometry type: "
        f"{geometry.geom_type}"
    )


# ---------------------------------------------------------------------------
# Province boundaries
# ---------------------------------------------------------------------------

def build_province_boundaries(
    regencies: gpd.GeoDataFrame,
) -> list:
    """Merge regencies by province and return their outer boundaries."""

    boundaries = []

    for _, province_rows in regencies.groupby(
        "province_id"
    ):
        geometry = unary_union(
            list(
                province_rows.geometry
            )
        )

        boundaries.append(
            geometry.boundary
        )

    return boundaries


# ---------------------------------------------------------------------------
# Generic overlay renderer
# ---------------------------------------------------------------------------

def render_overlay(
    image: Image.Image,
    regencies: gpd.GeoDataFrame,
    province_boundaries: list,
    coordinate_projector,
) -> Image.Image:
    """Draw administrative boundaries over a copy of the reference image."""

    base = image.convert(
        "RGBA"
    )

    drawing_layer = Image.new(
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
        drawing_layer
    )

    for geometry in regencies.geometry:
        draw_boundary_geometry(
            draw,
            geometry.boundary,
            coordinate_projector,
            REGENCY_COLOR,
            REGENCY_LINE_WIDTH,
        )

    for boundary in province_boundaries:
        draw_boundary_geometry(
            draw,
            boundary,
            coordinate_projector,
            PROVINCE_COLOR,
            PROVINCE_LINE_WIDTH,
        )

    return Image.alpha_composite(
        base,
        drawing_layer,
    )


# ---------------------------------------------------------------------------
# National overlay
# ---------------------------------------------------------------------------

def render_national_overlay(
    image: Image.Image,
    regencies: gpd.GeoDataFrame,
    province_boundaries: list,
    projection: GlobalProjection,
) -> Image.Image:
    """Render the nationwide overlay using global calibration only."""

    def projector(
        coordinate,
    ):
        return global_coordinate_to_pixel(
            coordinate,
            projection,
        )

    return render_overlay(
        image,
        regencies,
        province_boundaries,
        projector,
    )


# ---------------------------------------------------------------------------
# Regional overlays
# ---------------------------------------------------------------------------

def get_regional_rows(
    regencies: gpd.GeoDataFrame,
    region: Region,
) -> gpd.GeoDataFrame:
    """
    Select features intersecting a regional geographic diagnostic window.

    A bounding-box selection is sufficient because this is only used for
    diagnostic rendering.
    """

    bounds = regencies.geometry.bounds

    mask = (
        (
            bounds["maxx"]
            >= region.min_lon
        )
        & (
            bounds["minx"]
            <= region.max_lon
        )
        & (
            bounds["maxy"]
            >= region.min_lat
        )
        & (
            bounds["miny"]
            <= region.max_lat
        )
    )

    return regencies[
        mask
    ].copy()


def get_regional_crop_box(
    region: Region,
    projection: GlobalProjection,
) -> tuple[
    int,
    int,
    int,
    int,
]:
    """
    Calculate a crop large enough to contain both the reference geography
    and the regionally transformed GeoJSON.
    """

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

    global_pixels = [
        global_coordinate_to_pixel(
            coordinate,
            projection,
        )
        for coordinate in corners
    ]

    regional_pixels = [
        regional_coordinate_to_pixel(
            coordinate,
            projection,
            region,
        )
        for coordinate in corners
    ]

    all_pixels = (
        global_pixels
        + regional_pixels
    )

    xs = [
        point[0]
        for point in all_pixels
    ]

    ys = [
        point[1]
        for point in all_pixels
    ]

    left = int(
        min(
            xs
        )
    ) - region.padding

    right = int(
        max(
            xs
        )
    ) + region.padding

    top = int(
        min(
            ys
        )
    ) - region.padding

    bottom = int(
        max(
            ys
        )
    ) + region.padding

    left = max(
        0,
        left,
    )

    top = max(
        0,
        top,
    )

    right = min(
        projection.image_width,
        right,
    )

    bottom = min(
        projection.image_height,
        bottom,
    )

    return (
        left,
        top,
        right,
        bottom,
    )


def render_regional_overlay(
    image: Image.Image,
    regencies: gpd.GeoDataFrame,
    projection: GlobalProjection,
    region: Region,
) -> Image.Image:
    """Render and crop one independently calibrated regional overlay."""

    regional_rows = get_regional_rows(
        regencies,
        region,
    )

    regional_province_boundaries = build_province_boundaries(
        regional_rows
    )

    def projector(
        coordinate,
    ):
        return regional_coordinate_to_pixel(
            coordinate,
            projection,
            region,
        )

    full_overlay = render_overlay(
        image,
        regional_rows,
        regional_province_boundaries,
        projector,
    )

    crop_box = get_regional_crop_box(
        region,
        projection,
    )

    return full_overlay.crop(
        crop_box
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_configuration(
    image: Image.Image,
    regencies: gpd.GeoDataFrame,
    projection: GlobalProjection,
) -> None:
    """Print source and calibration information."""

    min_lon, min_lat, max_lon, max_lat = (
        float(value)
        for value in regencies.total_bounds
    )

    print(
        "=" * 80
    )
    print(
        "SOURCE"
    )
    print(
        "=" * 80
    )

    print(
        f"Reference image:      "
        f"{image.width} x {image.height}"
    )

    print(
        f"GeoJSON features:     "
        f"{len(regencies):,}"
    )

    print(
        f"Longitude bounds:     "
        f"{min_lon:.6f} -> {max_lon:.6f}"
    )

    print(
        f"Latitude bounds:      "
        f"{min_lat:.6f} -> {max_lat:.6f}"
    )

    print()

    print(
        "=" * 80
    )
    print(
        "GLOBAL CALIBRATION"
    )
    print(
        "=" * 80
    )

    print(
        f"X offset:             "
        f"{GLOBAL_X_OFFSET:.3f}"
    )

    print(
        f"Y offset:             "
        f"{GLOBAL_Y_OFFSET:.3f}"
    )

    print(
        f"X scale:              "
        f"{GLOBAL_X_SCALE:.6f}"
    )

    print(
        f"Y scale:              "
        f"{GLOBAL_Y_SCALE:.6f}"
    )

    print()

    print(
        "Projected raster bounds:"
    )

    print(
        f"  left:               "
        f"{projection.map_left:.2f}"
    )

    print(
        f"  right:              "
        f"{projection.map_right:.2f}"
    )

    print(
        f"  top:                "
        f"{projection.map_top:.2f}"
    )

    print(
        f"  bottom:             "
        f"{projection.map_bottom:.2f}"
    )

    print()

    print(
        "=" * 80
    )
    print(
        "REGIONAL CALIBRATION"
    )
    print(
        "=" * 80
    )

    for region in REGIONS:
        calibration = REGIONAL_CALIBRATIONS[
            region.id
        ]

        print(
            f"{region.id}:"
        )

        print(
            f"  x_offset = "
            f"{calibration.x_offset:.3f}"
        )

        print(
            f"  y_offset = "
            f"{calibration.y_offset:.3f}"
        )

        print(
            f"  x_scale  = "
            f"{calibration.x_scale:.6f}"
        )

        print(
            f"  y_scale  = "
            f"{calibration.y_scale:.6f}"
        )

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate national and independently calibrated regional overlays."""

    print(
        "Generating Indonesia area-code calibration overlays..."
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

    image = Image.open(
        AREA_CODE_IMAGE
    ).convert(
        "RGB"
    )

    regencies = gpd.read_file(
        REGENCIES_GEOJSON
    )

    if len(regencies) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected regencies.geojson feature count: "
            f"expected {EXPECTED_FEATURE_COUNT:,}, "
            f"got {len(regencies):,}."
        )

    required_properties = {
        "regency_id",
        "regency",
        "province_id",
        "province",
        "region_id",
        "region",
    }

    missing_properties = (
        required_properties
        - set(
            regencies.columns
        )
    )

    if missing_properties:
        raise ValueError(
            "regencies.geojson is missing properties: "
            + ", ".join(
                sorted(
                    missing_properties
                )
            )
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    projection = build_global_projection(
        image,
        regencies,
    )

    province_boundaries = build_province_boundaries(
        regencies
    )

    print_configuration(
        image,
        regencies,
        projection,
    )

    # ------------------------------------------------------------------
    # Nationwide sanity check
    # ------------------------------------------------------------------

    print(
        "Rendering national overlay..."
    )

    national_overlay = render_national_overlay(
        image,
        regencies,
        province_boundaries,
        projection,
    )

    national_path = (
        OUTPUT_DIR
        / "overlay-national.png"
    )

    national_overlay.convert(
        "RGB"
    ).save(
        national_path,
        format="PNG",
    )

    # ------------------------------------------------------------------
    # Independent regional calibration overlays
    # ------------------------------------------------------------------

    for region in REGIONS:
        print(
            f"Rendering {region.id} overlay..."
        )

        regional_overlay = render_regional_overlay(
            image,
            regencies,
            projection,
            region,
        )

        output_path = (
            OUTPUT_DIR
            / region.filename
        )

        regional_overlay.convert(
            "RGB"
        ).save(
            output_path,
            format="PNG",
        )

    print()
    print(
        "=" * 80
    )
    print(
        "OUTPUT"
    )
    print(
        "=" * 80
    )

    print(
        national_path.relative_to(
            PROJECT_ROOT
        )
    )

    for region in REGIONS:
        print(
            (
                OUTPUT_DIR
                / region.filename
            ).relative_to(
                PROJECT_ROOT
            )
        )

    print()
    print(
        "Overlay generation complete."
    )


if __name__ == "__main__":
    main()