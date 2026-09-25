"""
Extract geographic South African telephone area-code observations from
OpenStreetMap phone-number tags.

South Africa's OSM populated-place features generally do not contain a
dedicated telephone area-code property. However, many geolocated OSM objects
contain complete landline phone numbers. The geographic area code can be
derived from those numbers and used as input for constructing GeoPedia's
telephone area-code regions.

Nodes use their coordinates directly. Ways and relations are converted to
geometry and represented by a point guaranteed to lie on that geometry when
possible.

Only known geographic South African area codes are retained. Mobile,
non-geographic, malformed, foreign, and otherwise unsupported phone numbers
are rejected.

Input:
    data/raw/countries/south-africa/south-africa-260923.osm.pbf

Output:
    data/intermediate/countries/south-africa/osm/area-code-points.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/process/extract-osm-area-codes.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import osmium
from shapely import wkb
from shapely.geometry import Point, mapping


PBF_PATH = Path(
    "data/raw/countries/south-africa/south-africa-260923.osm.pbf"
)

OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "area-code-points.geojson"
)


# Geographic South African landline area codes represented by the telephone
# area-code map being constructed for GeoPedia.
GEOGRAPHIC_AREA_CODES = {
    "010",
    "011",
    "012",
    "013",
    "014",
    "015",
    "016",
    "017",
    "018",
    "021",
    "022",
    "023",
    "027",
    "028",
    "031",
    "032",
    "033",
    "034",
    "035",
    "036",
    "039",
    "040",
    "041",
    "042",
    "043",
    "044",
    "045",
    "046",
    "047",
    "048",
    "049",
    "051",
    "053",
    "054",
    "056",
    "057",
    "058",
}


# Phone-related tags observed in the South Africa OSM extract. Some are rare,
# but retaining them costs little and prevents useful landline observations
# from being discarded.
PHONE_TAG_KEYS = (
    "phone",
    "contact:phone",
    "telephone",
    "phone:1",
    "phone:2",
    "contact:phone2",
    "alt_phone",
    "emergency:phone",
)


PHONE_SPLIT_RE = re.compile(r"[;/|]")


def normalize_phone_number(value: str) -> str | None:
    """
    Normalize one South African phone-number string to domestic digits.

    Accepted examples:
        +27 21 531 4760 -> 0215314760
        +27215316561    -> 0215316561
        021 685 0394    -> 0216850394
        (021) 685 0394  -> 0216850394

    Returns None when the value cannot reasonably be interpreted as a South
    African telephone number.
    """
    value = value.strip()

    if not value:
        return None

    # Remove common extension suffixes before stripping punctuation.
    value = re.split(
        r"\b(?:ext|extension|x)\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    digits = re.sub(r"\D", "", value)

    if not digits:
        return None

    # International South African form.
    if digits.startswith("0027"):
        digits = "0" + digits[4:]
    elif digits.startswith("27"):
        digits = "0" + digits[2:]

    # Normal South African national numbers should begin with zero.
    if not digits.startswith("0"):
        return None

    return digits


def extract_area_code(phone: str) -> str | None:
    """
    Return a supported three-digit geographic area code from a phone number.
    """
    normalized = normalize_phone_number(phone)

    if normalized is None or len(normalized) < 3:
        return None

    area_code = normalized[:3]

    if area_code not in GEOGRAPHIC_AREA_CODES:
        return None

    return area_code


def split_phone_values(value: str) -> list[str]:
    """
    Split an OSM phone tag containing multiple phone numbers.

    OSM commonly separates multiple values with semicolons. A few other
    separators are accepted because they occur in real-world phone tags.
    """
    return [
        part.strip()
        for part in PHONE_SPLIT_RE.split(value)
        if part.strip()
    ]


def get_phone_observations(
    tags: osmium.osm.TagList,
) -> list[tuple[str, str, str]]:
    """
    Extract unique geographic phone observations from an OSM object's tags.

    Returns tuples of:
        (area_code, original_phone_value, source_tag)
    """
    observations: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    for key in PHONE_TAG_KEYS:
        value = tags.get(key)

        if not value:
            continue

        for phone in split_phone_values(value):
            area_code = extract_area_code(phone)

            if area_code is None:
                continue

            identity = (area_code, phone)

            if identity in seen:
                continue

            seen.add(identity)
            observations.append(
                (
                    area_code,
                    phone,
                    key,
                )
            )

    return observations


def representative_point(geometry: Any) -> Point | None:
    """
    Return a useful point representing a Shapely geometry.

    For polygonal geometry, representative_point() guarantees a point inside
    the geometry. For linear geometry, centroid is sufficient for locating the
    OSM object at the scale of South Africa's telephone area-code regions.
    """
    if geometry is None or geometry.is_empty:
        return None

    if geometry.geom_type in (
        "Polygon",
        "MultiPolygon",
    ):
        point = geometry.representative_point()
    else:
        point = geometry.centroid

    if point.is_empty:
        return None

    return point


class AreaCodeHandler(osmium.SimpleHandler):
    """
    Extract geolocated OSM objects containing geographic landline numbers.
    """

    def __init__(self) -> None:
        super().__init__()

        self.features: list[dict[str, Any]] = []

        self.area_code_counts: Counter[str] = Counter()
        self.object_type_counts: Counter[str] = Counter()

        self.objects_with_phone_tags = 0
        self.objects_with_geographic_phone = 0
        self.rejected_phone_values = 0
        self.accepted_phone_values = 0
        self.geometry_failures = 0

        self.wkb_factory = osmium.geom.WKBFactory()

    def has_phone_tag(
        self,
        tags: osmium.osm.TagList,
    ) -> bool:
        return any(tags.get(key) for key in PHONE_TAG_KEYS)

    def add_feature(
        self,
        *,
        osm_type: str,
        osm_id: int,
        tags: osmium.osm.TagList,
        point: Point,
    ) -> None:
        """
        Add one GeoJSON point for each distinct geographic area code attached
        to an OSM object.

        If an object contains multiple phone numbers with the same area code,
        the object contributes only one spatial observation for that code.
        """
        observations = get_phone_observations(tags)

        if not observations:
            return

        self.objects_with_geographic_phone += 1

        observations_by_code: dict[
            str,
            list[tuple[str, str]],
        ] = {}

        for area_code, phone, source_tag in observations:
            observations_by_code.setdefault(
                area_code,
                [],
            ).append(
                (
                    phone,
                    source_tag,
                )
            )

        for area_code, code_observations in observations_by_code.items():
            phones = [
                phone
                for phone, _ in code_observations
            ]

            source_tags = sorted(
                {
                    source_tag
                    for _, source_tag in code_observations
                }
            )

            properties: dict[str, Any] = {
                "osm_type": osm_type,
                "osm_id": osm_id,
                "area_code": area_code,
                "phone": phones[0],
                "phone_tag": source_tags[0],
            }

            name = tags.get("name")

            if name:
                properties["name"] = name

            if len(phones) > 1:
                properties["phones"] = phones

            if len(source_tags) > 1:
                properties["phone_tags"] = source_tags

            self.features.append(
                {
                    "type": "Feature",
                    "geometry": mapping(point),
                    "properties": properties,
                }
            )

            self.area_code_counts[area_code] += 1
            self.object_type_counts[osm_type] += 1

    def inspect_phone_values(
        self,
        tags: osmium.osm.TagList,
    ) -> None:
        """
        Count accepted and rejected individual phone values for diagnostics.
        """
        if not self.has_phone_tag(tags):
            return

        self.objects_with_phone_tags += 1

        for key in PHONE_TAG_KEYS:
            value = tags.get(key)

            if not value:
                continue

            for phone in split_phone_values(value):
                if extract_area_code(phone) is None:
                    self.rejected_phone_values += 1
                else:
                    self.accepted_phone_values += 1

    def node(self, node: osmium.osm.Node) -> None:
        self.inspect_phone_values(node.tags)

        if not get_phone_observations(node.tags):
            return

        if not node.location.valid():
            self.geometry_failures += 1
            return

        point = Point(
            node.location.lon,
            node.location.lat,
        )

        self.add_feature(
            osm_type="node",
            osm_id=node.id,
            tags=node.tags,
            point=point,
        )

    def way(self, way: osmium.osm.Way) -> None:
        self.inspect_phone_values(way.tags)

        if not get_phone_observations(way.tags):
            return

        try:
            wkb_hex = self.wkb_factory.create_linestring(
                way,
            )
            geometry = wkb.loads(
                wkb_hex,
                hex=True,
            )
        except Exception:
            self.geometry_failures += 1
            return

        point = representative_point(geometry)

        if point is None:
            self.geometry_failures += 1
            return

        self.add_feature(
            osm_type="way",
            osm_id=way.id,
            tags=way.tags,
            point=point,
        )

    def relation(
        self,
        relation: osmium.osm.Relation,
    ) -> None:
        self.inspect_phone_values(relation.tags)

        if not get_phone_observations(relation.tags):
            return

        # Constructing arbitrary relation geometry reliably requires member
        # geometry assembly. Most useful phone observations in this extract
        # occur on nodes and ways, so relations are counted diagnostically
        # but are not emitted unless a later processing step explicitly
        # resolves their geometry.
        self.geometry_failures += 1


def validate_features(
    features: list[dict[str, Any]],
) -> None:
    """
    Validate the extracted GeoJSON observations before writing them.
    """
    if not features:
        raise ValueError(
            "No geographic area-code observations were extracted."
        )

    for feature in features:
        properties = feature["properties"]
        area_code = properties["area_code"]

        if area_code not in GEOGRAPHIC_AREA_CODES:
            raise ValueError(
                f"Unexpected area code in output: {area_code}"
            )

        geometry = feature["geometry"]

        if geometry.get("type") != "Point":
            raise ValueError(
                "Area-code observations must be Point geometries."
            )


def write_geojson(
    features: list[dict[str, Any]],
) -> None:
    """
    Write extracted observations as a GeoJSON FeatureCollection.
    """
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    if not PBF_PATH.exists():
        raise FileNotFoundError(
            f"OSM PBF not found: {PBF_PATH}"
        )

    print("Reading OSM data from:")
    print(f"  {PBF_PATH}")
    print()

    handler = AreaCodeHandler()

    # locations=True makes node coordinates available while ways are read.
    handler.apply_file(
        str(PBF_PATH),
        locations=True,
    )

    validate_features(handler.features)
    write_geojson(handler.features)

    print("Extraction complete.")
    print()
    print(
        f"Objects with phone tags:       "
        f"{handler.objects_with_phone_tags:,}"
    )
    print(
        f"Objects with geographic code: "
        f"{handler.objects_with_geographic_phone:,}"
    )
    print(
        f"Accepted phone values:         "
        f"{handler.accepted_phone_values:,}"
    )
    print(
        f"Rejected phone values:         "
        f"{handler.rejected_phone_values:,}"
    )
    print(
        f"Geometry failures/skips:       "
        f"{handler.geometry_failures:,}"
    )
    print(
        f"Output point features:         "
        f"{len(handler.features):,}"
    )

    print()
    print("Features by OSM object type:")

    for object_type in (
        "node",
        "way",
        "relation",
    ):
        print(
            f"  {object_type:<8} "
            f"{handler.object_type_counts[object_type]:>7,}"
        )

    print()
    print("Observations by area code:")

    for area_code in sorted(
        GEOGRAPHIC_AREA_CODES
    ):
        print(
            f"  {area_code}: "
            f"{handler.area_code_counts[area_code]:,}"
        )

    missing_codes = [
        area_code
        for area_code in sorted(
            GEOGRAPHIC_AREA_CODES
        )
        if handler.area_code_counts[area_code] == 0
    ]

    if missing_codes:
        print()
        print(
            "WARNING: No observations found for: "
            + ", ".join(missing_codes)
        )

    size_mb = OUTPUT_PATH.stat().st_size / (
        1024 * 1024
    )

    print()
    print("Wrote:")
    print(f"  {OUTPUT_PATH}")
    print(f"  {size_mb:.2f} MB")


if __name__ == "__main__":
    main()