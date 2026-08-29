import json
import math
from pathlib import Path

# Generates country silhouette svg files for each country image in `public/data/countries.geojson`

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

INPUT_FILE = Path("public/data/countries.geojson")
OUTPUT_DIR = Path("public/data/country-images")

SVG_WIDTH = 600
SVG_HEIGHT = 400

PADDING = 25

FILL_COLOR = "currentColor"

# How far a secondary polygon can be from the main landmass
# and still be included.
#
# This is measured in degrees of latitude/longitude.
#
# ~5 degrees is roughly 500 km north/south.
INCLUDE_DISTANCE = 8


# ------------------------------------------------------------
# GeoJSON helpers
# ------------------------------------------------------------

def get_iso3(properties):
    for key in ("iso_a3", "ISO_A3", "ADM0_A3"):
        value = properties.get(key)

        if value and value != "-99":
            return str(value).upper()

    return None


def get_name(properties):
    for key in ("name", "NAME", "NAME_EN"):
        value = properties.get(key)

        if value:
            return str(value)

    return "Unknown"


def get_polygons(geometry):
    """
    Convert Polygon/MultiPolygon into a list of polygons.

    Each polygon is a list of rings.
    """

    geometry_type = geometry["type"]
    coordinates = geometry["coordinates"]

    if geometry_type == "Polygon":
        return [coordinates]

    if geometry_type == "MultiPolygon":
        return coordinates

    return []


def get_ring_points(polygon):
    """
    Return every point belonging to a polygon.
    """

    points = []

    for ring in polygon:
        points.extend(ring)

    return points


def get_polygon_bounds(polygon):
    points = get_ring_points(polygon)

    lons = [point[0] for point in points]
    lats = [point[1] for point in points]

    return (
        min(lons),
        min(lats),
        max(lons),
        max(lats),
    )


def polygon_area(polygon):
    """
    Approximate polygon area.

    This is sufficient for determining which polygon
    is the primary/main landmass.
    """

    ring = polygon[0]

    if len(ring) < 3:
        return 0

    center_lat = sum(
        point[1] for point in ring
    ) / len(ring)

    longitude_scale = math.cos(
        math.radians(center_lat)
    )

    area = 0

    for i in range(len(ring)):
        x1 = ring[i][0] * longitude_scale
        y1 = ring[i][1]

        x2 = ring[(i + 1) % len(ring)][0] * longitude_scale
        y2 = ring[(i + 1) % len(ring)][1]

        area += (x1 * y2) - (x2 * y1)

    return abs(area) / 2


# ------------------------------------------------------------
# Polygon selection
# ------------------------------------------------------------

def polygon_center(polygon):
    """
    Get the approximate center of a polygon.
    """

    points = get_ring_points(polygon)

    lons = [point[0] for point in points]
    lats = [point[1] for point in points]

    return (
        (min(lons) + max(lons)) / 2,
        (min(lats) + max(lats)) / 2,
    )


def distance_between_centers(a, b):
    """
    Approximate geographic distance between two polygon centers.
    """

    lon1, lat1 = polygon_center(a)
    lon2, lat2 = polygon_center(b)

    lat_distance = abs(lat1 - lat2)

    center_lat = (lat1 + lat2) / 2

    longitude_scale = math.cos(
        math.radians(center_lat)
    )

    lon_distance = (
        abs(lon1 - lon2)
        * longitude_scale
    )

    return math.sqrt(
        lat_distance ** 2
        + lon_distance ** 2
    )


def select_polygons(polygons):
    """
    Select the main landmass plus nearby islands.

    The largest polygon is always included.

    Other polygons are included when they are reasonably
    close to the main polygon.

    This removes distant overseas territories.
    """

    if len(polygons) <= 1:
        return polygons

    # Find the largest polygon.
    main_polygon = max(
        polygons,
        key=polygon_area,
    )

    selected = [main_polygon]

    for polygon in polygons:

        if polygon is main_polygon:
            continue

        distance = distance_between_centers(
            main_polygon,
            polygon,
        )

        if distance <= INCLUDE_DISTANCE:
            selected.append(polygon)

    return selected


# ------------------------------------------------------------
# Projection
# ------------------------------------------------------------

def get_all_points(polygons):
    points = []

    for polygon in polygons:
        points.extend(
            get_ring_points(polygon)
        )

    return points


def create_projection(points):

    center_lat = (
        min(point[1] for point in points)
        + max(point[1] for point in points)
    ) / 2

    longitude_scale = math.cos(
        math.radians(center_lat)
    )

    projected = []

    for lon, lat in points:

        x = lon * longitude_scale
        y = lat

        projected.append(
            (x, y)
        )

    min_x = min(
        point[0]
        for point in projected
    )

    max_x = max(
        point[0]
        for point in projected
    )

    min_y = min(
        point[1]
        for point in projected
    )

    max_y = max(
        point[1]
        for point in projected
    )

    return {
        "longitude_scale": longitude_scale,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
    }


def project_point(
    lon,
    lat,
    projection,
):

    x = (
        lon
        * projection["longitude_scale"]
    )

    y = lat

    return x, y


def transform_point(
    x,
    y,
    projection,
):

    min_x = projection["min_x"]
    max_x = projection["max_x"]

    min_y = projection["min_y"]
    max_y = projection["max_y"]

    width = max_x - min_x
    height = max_y - min_y

    if width == 0:
        width = 1

    if height == 0:
        height = 1

    usable_width = (
        SVG_WIDTH
        - (PADDING * 2)
    )

    usable_height = (
        SVG_HEIGHT
        - (PADDING * 2)
    )

    scale = min(
        usable_width / width,
        usable_height / height,
    )

    scaled_width = width * scale
    scaled_height = height * scale

    offset_x = (
        SVG_WIDTH
        - scaled_width
    ) / 2

    offset_y = (
        SVG_HEIGHT
        - scaled_height
    ) / 2

    svg_x = (
        offset_x
        + ((x - min_x) * scale)
    )

    svg_y = (
        offset_y
        + ((max_y - y) * scale)
    )

    return svg_x, svg_y


# ------------------------------------------------------------
# SVG creation
# ------------------------------------------------------------

def create_path(
    polygons,
    projection,
):

    path_commands = []

    for polygon in polygons:

        for ring in polygon:

            if not ring:
                continue

            commands = []

            for index, point in enumerate(ring):

                lon, lat = point

                x, y = project_point(
                    lon,
                    lat,
                    projection,
                )

                svg_x, svg_y = transform_point(
                    x,
                    y,
                    projection,
                )

                if index == 0:

                    commands.append(
                        f"M {svg_x:.2f} {svg_y:.2f}"
                    )

                else:

                    commands.append(
                        f"L {svg_x:.2f} {svg_y:.2f}"
                    )

            commands.append("Z")

            path_commands.append(
                " ".join(commands)
            )

    return " ".join(
        path_commands
    )


def create_svg(path_data):

    return f"""<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{SVG_WIDTH}"
    height="{SVG_HEIGHT}"
    viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}"
>
    <path
        d="{path_data}"
        fill="{FILL_COLOR}"
        fill-rule="evenodd"
    />
</svg>
"""


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    if not INPUT_FILE.exists():

        print(
            f"ERROR: Could not find "
            f"{INPUT_FILE}"
        )

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        geojson = json.load(file)

    features = geojson.get(
        "features",
        [],
    )

    generated = 0
    skipped = 0

    for feature in features:

        properties = feature.get(
            "properties",
            {},
        )

        geometry = feature.get(
            "geometry"
        )

        iso3 = get_iso3(
            properties
        )

        name = get_name(
            properties
        )

        if not iso3:

            print(
                f"Skipping {name}: "
                "no valid ISO-3 code"
            )

            skipped += 1

            continue

        if not geometry:

            print(
                f"Skipping {name}: "
                "no geometry"
            )

            skipped += 1

            continue

        if geometry["type"] not in (
            "Polygon",
            "MultiPolygon",
        ):

            print(
                f"Skipping {name}: "
                f"unsupported geometry "
                f"{geometry['type']}"
            )

            skipped += 1

            continue

        polygons = get_polygons(
            geometry
        )

        if not polygons:

            print(
                f"Skipping {name}: "
                "no polygons"
            )

            skipped += 1

            continue

        # ----------------------------------------------------
        # Select main landmass + nearby islands
        # ----------------------------------------------------

        selected_polygons = (
            select_polygons(polygons)
        )

        # ----------------------------------------------------
        # Calculate the bounding box only from the
        # selected polygons.
        # ----------------------------------------------------

        points = get_all_points(
            selected_polygons
        )

        if not points:

            print(
                f"Skipping {name}: "
                "no points"
            )

            skipped += 1

            continue

        projection = create_projection(
            points
        )

        path_data = create_path(
            selected_polygons,
            projection,
        )

        svg = create_svg(
            path_data
        )

        output_file = (
            OUTPUT_DIR
            / f"{iso3.lower()}.svg"
        )

        output_file.write_text(
            svg,
            encoding="utf-8",
        )

        generated += 1

        print(
            f"Generated: "
            f"{iso3.lower()}.svg "
            f"({name})"
        )

    print()
    print(
        f"Finished."
    )

    print(
        f"Generated: {generated}"
    )

    print(
        f"Skipped:   {skipped}"
    )

    print(
        f"Output:    {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()