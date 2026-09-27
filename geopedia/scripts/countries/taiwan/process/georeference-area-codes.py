"""
Create a georeferenced reference overlay for Taiwan telephone area codes.

Sources
-------
data/raw/countries/taiwan/area-codes/plonkit-area-codes.webp
data/intermediate/countries/taiwan/townships.geojson

Output
------
data/intermediate/countries/taiwan/area-codes/
    plonkit-township-overlay.png

Purpose
-------
GeoPedia's only detailed source for Taiwan's telephone area-code geography
is a Plonk It reference map. The map contains:

1. Taiwan proper.
2. A separate Kinmen inset.
3. A separate Penghu inset.
4. A separate Lienchiang / Matsu inset.

The inset islands have been repositioned and rescaled in the source image, so
the entire image cannot be represented by one geographic transformation.

This script draws GeoPedia's authoritative MOI township/district boundaries
over the corresponding parts of the Plonk It reference image. Each map
section uses its own geographic-to-pixel transformation.

The resulting image is a DEVELOPMENT REFERENCE ONLY. It is not used by the
GeoPedia website and should not be copied to public/.

It will be used to construct:

    data/intermediate/countries/taiwan/area-codes/
        township-area-codes.json

That assignment file will become the canonical intermediate source for
generating the full, two-significant-digit-prefix, and
one-significant-digit-prefix area-code maps.

Important
---------
The Plonk It map includes blue minor area codes. These are real quiz answers
and must not be discarded. A geographic region may therefore eventually
have multiple valid answers, for example:

    {
        "area_codes": ["035", "036"]
    }

Run from the GeoPedia project root:

    python scripts/countries/taiwan/process/georeference-area-codes.py

Requires:
    pillow
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape


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

OUTPUT_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "plonkit-township-overlay.png"
)

LABELED_OUTPUT_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "plonkit-township-labeled-overlay.png"
)

TOWNSHIP_LABEL_LOOKUP_PATH = (
    ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "taiwan"
    / "area-codes"
    / "township-label-lookup.json"
)


# ---------------------------------------------------------------------------
# Plonk It map sections
# ---------------------------------------------------------------------------
#
# The source image is 960 x 1370 pixels.
#
# Taiwan proper and each offshore-island inset use independent geographic
# transformations because the islands have been moved and rescaled in the
# Plonk It graphic.
#
# Each section is described by:
#
#     geographic bounds:
#         min longitude
#         min latitude
#         max longitude
#         max latitude
#
#     image bounds:
#         left pixel
#         top pixel
#         right pixel
#         bottom pixel
#
# These values are calibration values for the supplied Plonk It image.
# They are intentionally kept here rather than embedded in drawing logic so
# they can be refined independently if visual inspection reveals an offset.
# ---------------------------------------------------------------------------


MAP_SECTIONS = {
    "mainland": {
        "counties": {
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
        },

        # Geographic bounds of the Taiwan-proper reference map.
        #
        # These intentionally encompass the visible Taiwan coastline rather
        # than every offshore point belonging to the included counties.
        "geo_bounds": (
            120.00,
            21.85,
            122.05,
            25.35,
        ),

        # Approximate Plonk It pixel rectangle occupied by Taiwan proper.
        "pixel_bounds": (
            257,
            25,
            968,
            1391,
        ),
    },

    "kinmen": {
        "counties": {
            "TWN.1.1_1",
        },
        "geo_bounds": (
            118.05,
            24.35,
            118.50,
            24.55,
        ),
        "pixel_bounds": (
            65,
            326,
            234,
            507,
        ),
    },

    "penghu": {
        "counties": {
            "TWN.7.10_1",
        },
        "geo_bounds": (
            119.25,
            23.15,
            119.75,
            23.85,
        ),
        "pixel_bounds": (
            49,
            622,
            159,
            874,
        ),
    },

    "lienchiang": {
        "counties": {
            "TWN.1.2_1",
        },
        "geo_bounds": (
            119.85,
            25.90,
            120.55,
            26.40,
        ),
        "pixel_bounds": (
            197,
            75,
            449,
            283,
        ),
    },
}


# ---------------------------------------------------------------------------
# Drawing configuration
# ---------------------------------------------------------------------------

# Bright magenta is intentionally used because it remains visible against
# every fill color used by the Plonk It reference map.
TOWNSHIP_LINE_COLOR = (
    255,
    0,
    255,
    255,
)

TOWNSHIP_LINE_WIDTH = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Missing source file: {path}"
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
            f"{path} does not contain a valid features array."
        )

    return data


def lon_lat_to_pixel(
    longitude: float,
    latitude: float,
    geo_bounds: tuple[float, float, float, float],
    pixel_bounds: tuple[int, int, int, int],
) -> tuple[float, float]:
    """
    Convert longitude/latitude into Plonk It image pixel coordinates.

    This uses an affine transformation independently for each map section.
    """

    min_lon, min_lat, max_lon, max_lat = geo_bounds
    left, top, right, bottom = pixel_bounds

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


def transform_ring(
    ring: Iterable[list[float]],
    geo_bounds: tuple[float, float, float, float],
    pixel_bounds: tuple[int, int, int, int],
) -> list[tuple[float, float]]:
    """Transform a GeoJSON coordinate ring into image pixels."""

    return [
        lon_lat_to_pixel(
            longitude=coordinate[0],
            latitude=coordinate[1],
            geo_bounds=geo_bounds,
            pixel_bounds=pixel_bounds,
        )
        for coordinate in ring
    ]


def iter_polygon_rings(
    geometry: dict,
) -> Iterable[list[list[float]]]:
    """
    Yield every ring from Polygon or MultiPolygon geometry.

    Exterior and interior rings are both drawn because internal island/lake
    boundaries can be useful while comparing the MOI geometry to Plonk It.
    """

    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates"
    )

    if geometry_type == "Polygon":
        for ring in coordinates:
            yield ring

    elif geometry_type == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                yield ring

    else:
        raise ValueError(
            f"Unexpected township geometry type "
            f"{geometry_type!r}."
        )


def draw_section(
    draw: ImageDraw.ImageDraw,
    features: list[dict],
    section_name: str,
    section: dict,
) -> int:
    """Draw one georeferenced map section."""

    county_ids = section[
        "counties"
    ]

    geo_bounds = section[
        "geo_bounds"
    ]

    pixel_bounds = section[
        "pixel_bounds"
    ]

    matching_features = [
        feature
        for feature in features
        if feature.get(
            "properties",
            {},
        ).get("county_id") in county_ids
    ]

    if not matching_features:
        raise ValueError(
            f"No townships found for map section "
            f"{section_name!r}."
        )

    for feature in matching_features:
        geometry = feature.get(
            "geometry"
        )

        if geometry is None:
            raise ValueError(
                "Township feature has no geometry."
            )

        for ring in iter_polygon_rings(
            geometry
        ):
            pixels = transform_ring(
                ring=ring,
                geo_bounds=geo_bounds,
                pixel_bounds=pixel_bounds,
            )

            if len(pixels) >= 2:
                draw.line(
                    pixels,
                    fill=TOWNSHIP_LINE_COLOR,
                    width=TOWNSHIP_LINE_WIDTH,
                    joint="curve",
                )

    return len(
        matching_features
    )
    
    
def geometry_label_point(
    geometry_data: dict,
) -> tuple[float, float]:
    """
    Return a point guaranteed to lie inside a township.

    representative_point() is preferable to a centroid here because many
    Taiwan townships are irregular or multipart and their centroid can fall
    outside the visible polygon.
    """

    geometry = shape(
        geometry_data
    )

    if geometry.is_empty:
        raise ValueError(
            "Cannot label an empty township geometry."
        )

    point = geometry.representative_point()

    return (
        point.x,
        point.y,
    )


def draw_mainland_township_labels(
    image: Image.Image,
    features: list[dict],
) -> dict[str, dict]:
    """
    Draw short sequential township numbers over Taiwan proper.

    Full township IDs and names are too long to display legibly on the
    Plonk It raster. Each mainland township therefore receives a short
    development-only number.

    The returned lookup maps those numbers back to the authoritative MOI
    township metadata.
    """

    draw = ImageDraw.Draw(
        image
    )

    font = ImageFont.load_default()

    section = MAP_SECTIONS[
        "mainland"
    ]

    county_ids = section[
        "counties"
    ]

    geo_bounds = section[
        "geo_bounds"
    ]

    pixel_bounds = section[
        "pixel_bounds"
    ]

    mainland_features = [
        feature
        for feature in features
        if feature.get(
            "properties",
            {},
        ).get("county_id") in county_ids
    ]

    # Stable ordering makes the diagnostic numbers reproducible.
    mainland_features.sort(
        key=lambda feature: (
            feature.get(
                "properties",
                {},
            ).get("county") or "",
            feature.get(
                "properties",
                {},
            ).get("township") or "",
            feature.get(
                "properties",
                {},
            ).get("township_id") or "",
        )
    )

    lookup: dict[str, dict] = {}

    for number, feature in enumerate(
        mainland_features,
        start=1,
    ):
        properties = feature.get(
            "properties",
            {}
        )

        township_id = properties.get(
            "township_id"
        )

        if not township_id:
            raise ValueError(
                "Township is missing township_id."
            )

        longitude, latitude = geometry_label_point(
            feature[
                "geometry"
            ]
        )

        x, y = lon_lat_to_pixel(
            longitude=longitude,
            latitude=latitude,
            geo_bounds=geo_bounds,
            pixel_bounds=pixel_bounds,
        )

        label = str(
            number
        )

        # White outline keeps the compact number visible over every
        # Plonk It fill color without covering much of the source map.
        draw.text(
            (x, y),
            label,
            font=font,
            fill=(0, 0, 0),
            stroke_width=2,
            stroke_fill=(255, 255, 255),
            anchor="mm",
        )

        lookup[
            label
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
        }

    return lookup
  

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
    ).convert("RGBA")

    print(
        f"Reference image: {image.width} x {image.height}"
    )

    if image.size != (
        960,
        1370,
    ):
        raise ValueError(
            "Unexpected Plonk It image dimensions. "
            "The calibration in this script expects "
            "a 960 x 1370 image."
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

    if len(township_features) != 368:
        raise ValueError(
            f"Expected 368 Taiwan townships, found "
            f"{len(township_features)}."
        )

    draw = ImageDraw.Draw(
        image
    )

    print()
    print(
        "Drawing georeferenced township boundaries..."
    )

    drawn_township_ids: set[str] = set()

    for section_name, section in MAP_SECTIONS.items():
        count = draw_section(
            draw=draw,
            features=township_features,
            section_name=section_name,
            section=section,
        )

        section_counties = section[
            "counties"
        ]

        for feature in township_features:
            properties = feature.get(
                "properties",
                {}
            )

            if properties.get(
                "county_id"
            ) in section_counties:
                township_id = properties.get(
                    "township_id"
                )

                if township_id:
                    drawn_township_ids.add(
                        township_id
                    )

        print(
            f"  {section_name}: {count} townships"
        )

    # -----------------------------------------------------------------------
    # Validate complete township coverage
    # -----------------------------------------------------------------------

    all_township_ids = {
        feature.get(
            "properties",
            {},
        ).get("township_id")
        for feature in township_features
    }

    all_township_ids.discard(
        None
    )

    missing_townships = (
        all_township_ids
        - drawn_township_ids
    )

    if missing_townships:
        raise ValueError(
            "Some townships were not assigned to a Plonk It "
            "map section:\n"
            f"{sorted(missing_townships)}"
        )
        
    # -----------------------------------------------------------------------
    # Create labeled assignment reference
    # -----------------------------------------------------------------------

    labeled_image = image.copy()

    township_label_lookup = draw_mainland_township_labels(
        image=labeled_image,
        features=township_features,
    )

    # -----------------------------------------------------------------------
    # Write reference image
    # -----------------------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.convert(
        "RGB"
    ).save(
        OUTPUT_PATH,
        quality=95,
    )
    
    labeled_image.convert(
        "RGB"
    ).save(
        LABELED_OUTPUT_PATH,
        quality=95,
    )
    
    with TOWNSHIP_LABEL_LOOKUP_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            township_label_lookup,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write(
            "\n"
        )

    print()
    print(
        "Taiwan area-code reference overlay generated."
    )
    print()
    print(
        f"Townships: {len(township_features)}"
    )
    print(
        f"Townships drawn: {len(drawn_township_ids)}"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH.relative_to(ROOT)}"
    )
    print(
        f"Labeled: {LABELED_OUTPUT_PATH.relative_to(ROOT)}"
    )
    print(
        f"Lookup: {TOWNSHIP_LABEL_LOOKUP_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()