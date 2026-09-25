"""
Extract useful populated places from South Africa OpenStreetMap data and
associate each place with GeoPedia's South African administrative hierarchy.

This is a research/intermediate-data script used while constructing datasets
such as South Africa's geographic telephone area-code regions. It extracts
OSM nodes tagged as city, town, or village and spatially joins them to
GeoPedia's processed municipality and ward polygons.

Input:
    data/raw/countries/south-africa/south-africa-260923.osm.pbf

Administrative references:
    public/data/countries/south-africa/geojson/municipalities.geojson
    public/data/countries/south-africa/geojson/wards.geojson

Output:
    data/intermediate/countries/south-africa/osm/places.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/process/extract-osm-places.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import osmium
from shapely.geometry import Point, shape
from shapely.strtree import STRtree


PBF_PATH = Path(
    "data/raw/countries/south-africa/south-africa-260923.osm.pbf"
)

MUNICIPALITIES_PATH = Path(
    "public/data/countries/south-africa/geojson/municipalities.geojson"
)

WARDS_PATH = Path(
    "public/data/countries/south-africa/geojson/wards.geojson"
)

OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/osm/places.geojson"
)

PLACE_TYPES = {
    "city",
    "town",
    "village",
}


def optional_tag(tags: Any, key: str) -> str | None:
    """
    Return a stripped OSM tag value, or None when the tag is absent/empty.
    """
    value = tags.get(key)

    if value is None:
        return None

    value = value.strip()

    return value or None


class PlaceHandler(osmium.SimpleHandler):
    """
    Collect named OSM nodes representing cities, towns, and villages.

    Only point features are needed for the area-code research workflow.
    Administrative membership is assigned later from GeoPedia's municipality
    polygons rather than relying on OSM administrative tags.
    """

    def __init__(self) -> None:
        super().__init__()
        self.places: list[dict[str, Any]] = []

    def node(self, node: osmium.osm.Node) -> None:
        place_type = node.tags.get("place")

        if place_type not in PLACE_TYPES:
            return

        name = optional_tag(node.tags, "name")

        if name is None:
            return

        if not node.location.valid():
            return

        properties: dict[str, Any] = {
            "osm_id": node.id,
            "name": name,
            "place": place_type,
        }

        # Keep useful alternate naming information where OSM provides it.
        for tag, property_name in (
            ("name:en", "name_en"),
            ("official_name", "official_name"),
            ("alt_name", "alt_name"),
            ("old_name", "old_name"),
        ):
            value = optional_tag(node.tags, tag)

            if value is not None:
                properties[property_name] = value

        self.places.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        node.location.lon,
                        node.location.lat,
                    ],
                },
                "properties": properties,
            }
        )


def load_polygon_features(
    path: Path,
    label: str,
) -> tuple[
    list[dict[str, Any]],
    list[Any],
    STRtree,
]:
    """
    Load polygon features and build a spatial index for point lookups.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{label} GeoJSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{label} input must be a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list) or not features:
        raise ValueError(
            f"{label} GeoJSON contains no features."
        )

    geometries = []

    for feature in features:
        geometry_data = feature.get("geometry")

        if geometry_data is None:
            raise ValueError(
                f"{label} feature contains no geometry."
            )

        geometry = shape(geometry_data)

        if geometry.is_empty:
            raise ValueError(
                f"{label} feature contains empty geometry."
            )

        geometries.append(geometry)

    return features, geometries, STRtree(geometries)

def attach_admin_hierarchy(
    places: list[dict[str, Any]],
    municipality_features: list[dict[str, Any]],
    municipality_geometries: list[Any],
    tree: STRtree,
) -> int:
    """
    Spatially join each OSM place to its containing municipality.

    STRtree is used so thousands of OSM places do not need to be tested
    against all 213 municipality polygons individually.

    Returns the number of places for which no containing municipality could
    be identified.
    """
    unmatched = 0

    for feature in places:
        longitude, latitude = feature["geometry"]["coordinates"]
        point = Point(longitude, latitude)

        candidate_indices = tree.query(point)

        municipality_index: int | None = None

        for candidate_index in candidate_indices:
            index = int(candidate_index)

            # covers() includes points lying exactly on a polygon boundary.
            if municipality_geometries[index].covers(point):
                municipality_index = index
                break

        if municipality_index is None:
            unmatched += 1
            continue

        municipality_properties = municipality_features[
            municipality_index
        ]["properties"]

        place_properties = feature["properties"]

        for property_name in (
            "municipality_id",
            "municipality",
            "district_id",
            "district",
            "province_id",
            "province",
        ):
            value = municipality_properties.get(property_name)

            if value is None:
                raise ValueError(
                    f"Municipality is missing {property_name!r}: "
                    f"{municipality_properties}"
                )

            place_properties[property_name] = value

    return unmatched


def attach_ward(
    places: list[dict[str, Any]],
    ward_features: list[dict[str, Any]],
    ward_geometries: list[Any],
    tree: STRtree,
) -> int:
    """
    Spatially join each OSM place to its containing South African ward.

    Ward membership gives the area-code research workflow a substantially
    finer geographic unit than municipalities, which is important where
    telephone area-code boundaries split a municipality.

    Returns the number of places for which no containing ward could be
    identified.
    """
    unmatched = 0

    for feature in places:
        longitude, latitude = feature["geometry"]["coordinates"]
        point = Point(longitude, latitude)

        candidate_indices = tree.query(point)

        ward_index: int | None = None

        for candidate_index in candidate_indices:
            index = int(candidate_index)

            if ward_geometries[index].covers(point):
                ward_index = index
                break

        if ward_index is None:
            unmatched += 1
            continue

        ward_properties = ward_features[ward_index]["properties"]
        place_properties = feature["properties"]

        for property_name in (
            "ward_id",
            "ward",
            "ward_number",
        ):
            value = ward_properties.get(property_name)

            if value is None:
                raise ValueError(
                    f"Ward is missing {property_name!r}: "
                    f"{ward_properties}"
                )

            place_properties[property_name] = value

    return unmatched
  

def sort_places(
    places: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Sort output deterministically for easier inspection and comparison.
    """
    place_order = {
        "city": 0,
        "town": 1,
        "village": 2,
    }

    return sorted(
        places,
        key=lambda feature: (
            place_order[feature["properties"]["place"]],
            feature["properties"]["name"].casefold(),
            feature["properties"]["osm_id"],
        ),
    )


def main() -> None:
    if not PBF_PATH.exists():
        raise FileNotFoundError(
            f"OSM PBF not found: {PBF_PATH}"
        )

    print(f"Reading OSM places from:")
    print(f"  {PBF_PATH}")
    print()

    handler = PlaceHandler()
    handler.apply_file(str(PBF_PATH), locations=True)

    print(f"Extracted named places: {len(handler.places):,}")

    counts = {
        place_type: sum(
            feature["properties"]["place"] == place_type
            for feature in handler.places
        )
        for place_type in sorted(PLACE_TYPES)
    }

    for place_type, count in counts.items():
        print(f"  {place_type:<8} {count:,}")

    print()
    print("Loading municipality polygons...")

    (
        municipality_features,
        municipality_geometries,
        municipality_tree,
    ) = load_polygon_features(
        MUNICIPALITIES_PATH,
        "Municipality",
    )

    print(
        f"Loaded municipalities: "
        f"{len(municipality_features):,}"
    )

    print("Assigning administrative hierarchy...")

    municipality_unmatched = attach_admin_hierarchy(
        handler.places,
        municipality_features,
        municipality_geometries,
        municipality_tree,
    )

    municipality_matched = (
        len(handler.places) - municipality_unmatched
    )

    print(f"Matched places:   {municipality_matched:,}")
    print(f"Unmatched places: {municipality_unmatched:,}")

    print()
    print("Loading ward polygons...")

    (
        ward_features,
        ward_geometries,
        ward_tree,
    ) = load_polygon_features(
        WARDS_PATH,
        "Ward",
    )

    print(f"Loaded wards: {len(ward_features):,}")

    print("Assigning wards...")

    ward_unmatched = attach_ward(
        handler.places,
        ward_features,
        ward_geometries,
        ward_tree,
    )

    ward_matched = len(handler.places) - ward_unmatched

    print(f"Matched wards:   {ward_matched:,}")
    print(f"Unmatched wards: {ward_unmatched:,}")

    output_features = sort_places(handler.places)

    output = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)

    print()
    print("Wrote:")
    print(f"  {OUTPUT_PATH}")
    print(f"  {size_mb:.2f} MB")


if __name__ == "__main__":
    main()