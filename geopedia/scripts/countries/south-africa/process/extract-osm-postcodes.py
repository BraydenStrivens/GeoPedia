"""
Extract South African postcode observations from OpenStreetMap.

The extractor reads the South Africa OSM PBF and converts objects carrying
usable postcode tags into point observations for later spatial analysis
against GeoPedia's administrative ward geometry.

Accepted postcode tags:

    addr:postcode
    postal_code
    post:postcode

Only normalized four-digit South African postcodes are retained. Prefixes are
also stored so the same extracted dataset can later be evaluated at four-,
three-, two-, and one-digit resolution without rereading the OSM PBF.

Nodes use their geographic coordinates directly. Ways use a representative
point derived from their geometry. Relations are counted for diagnostic
purposes but are not emitted because this extractor does not construct
relation geometries.

Input:

    data/raw/countries/south-africa/
    south-africa-260923.osm.pbf

Output:

    data/intermediate/countries/south-africa/osm/
    postcode-points.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-africa/process/extract-osm-postcodes.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import osmium
from shapely import wkb


INPUT_PATH = Path(
    "data/raw/countries/south-africa/"
    "south-africa-260923.osm.pbf"
)

OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points.geojson"
)

POSTCODE_TAGS = (
    "addr:postcode",
    "postal_code",
    "post:postcode",
)

FOUR_DIGIT_POSTCODE = re.compile(
    r"^\d{4}$"
)


def normalize_postcode(
    value: str,
) -> str | None:
    """
    Normalize an OSM postcode value.

    Only an unambiguous four-digit numeric postcode is accepted. Leading and
    trailing whitespace is ignored.

    Values containing multiple postcodes or additional non-whitespace text
    are deliberately rejected so questionable OSM data does not silently
    enter the geographic classification pipeline.
    """
    normalized = value.strip()

    if not FOUR_DIGIT_POSTCODE.fullmatch(
        normalized
    ):
        return None

    return normalized


def make_properties(
    *,
    postcode: str,
    source_tag: str,
    osm_type: str,
    osm_id: int,
) -> dict[str, Any]:
    """Create the properties stored on one postcode observation."""
    return {
        "postcode": postcode,
        "prefix_3": postcode[:3],
        "prefix_2": postcode[:2],
        "prefix_1": postcode[:1],
        "source_tag": source_tag,
        "osm_type": osm_type,
        "osm_id": osm_id,
    }


def make_feature(
    *,
    longitude: float,
    latitude: float,
    properties: dict[str, Any],
) -> dict[str, Any]:
    """Create one GeoJSON Point feature."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                longitude,
                latitude,
            ],
        },
        "properties": properties,
    }


class PostcodeHandler(
    osmium.SimpleHandler
):
    """
    Extract postcode-tagged OSM objects.

    Nodes are emitted directly.

    Ways are converted to representative points using geometry supplied by
    osmium's node-location support.

    Relations are inspected for postcode tags and included in diagnostics,
    but are not emitted because relation geometry is not assembled here.
    """

    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.features: list[
            dict[str, Any]
        ] = []

        self.tag_counts: Counter[str] = Counter()
        self.object_counts: Counter[str] = Counter()
        self.accepted_counts: Counter[str] = Counter()
        self.rejected_counts: Counter[str] = Counter()

        self.rejected_values: Counter[str] = Counter()

        self.geometry_failures: Counter[str] = Counter()

        self.wkb_factory = (
            osmium.geom.WKBFactory()
        )

    def extract_values(
        self,
        tags: Any,
        *,
        osm_type: str,
    ) -> list[
        tuple[str, str]
    ]:
        """
        Extract unique valid postcode/tag pairs from one OSM object.

        If the same postcode appears in more than one accepted tag on the
        same object, only one observation is retained for that postcode. The
        first tag in POSTCODE_TAGS determines the stored source tag.
        """
        results: list[
            tuple[str, str]
        ] = []

        seen_postcodes: set[str] = set()

        has_postcode_tag = False

        for tag_name in POSTCODE_TAGS:
            raw_value = tags.get(
                tag_name
            )

            if raw_value is None:
                continue

            has_postcode_tag = True

            self.tag_counts[
                tag_name
            ] += 1

            postcode = normalize_postcode(
                raw_value
            )

            if postcode is None:
                self.rejected_counts[
                    tag_name
                ] += 1

                self.rejected_values[
                    raw_value
                ] += 1

                continue

            self.accepted_counts[
                tag_name
            ] += 1

            if postcode in seen_postcodes:
                continue

            seen_postcodes.add(
                postcode
            )

            results.append(
                (
                    postcode,
                    tag_name,
                )
            )

        if has_postcode_tag:
            self.object_counts[
                osm_type
            ] += 1

        return results

    def node(
        self,
        node: osmium.osm.Node,
    ) -> None:
        """Extract postcode observations from a node."""
        values = self.extract_values(
            node.tags,
            osm_type="node",
        )

        if not values:
            return

        if not node.location.valid():
            self.geometry_failures[
                "node"
            ] += 1
            return

        longitude = node.location.lon
        latitude = node.location.lat

        for postcode, source_tag in values:
            self.features.append(
                make_feature(
                    longitude=longitude,
                    latitude=latitude,
                    properties=make_properties(
                        postcode=postcode,
                        source_tag=source_tag,
                        osm_type="node",
                        osm_id=node.id,
                    ),
                )
            )

    def way(
        self,
        way: osmium.osm.Way,
    ) -> None:
        """Extract postcode observations from a way."""
        values = self.extract_values(
            way.tags,
            osm_type="way",
        )

        if not values:
            return

        try:
            geometry_wkb = (
                self.wkb_factory.create_linestring(
                    way
                )
            )

            geometry = wkb.loads(
                geometry_wkb,
                hex=True,
            )

            if geometry.is_empty:
                raise ValueError(
                    "Empty way geometry."
                )

            point = (
                geometry.representative_point()
            )

        except Exception:
            self.geometry_failures[
                "way"
            ] += 1
            return

        for postcode, source_tag in values:
            self.features.append(
                make_feature(
                    longitude=point.x,
                    latitude=point.y,
                    properties=make_properties(
                        postcode=postcode,
                        source_tag=source_tag,
                        osm_type="way",
                        osm_id=way.id,
                    ),
                )
            )

    def relation(
        self,
        relation: osmium.osm.Relation,
    ) -> None:
        """
        Count postcode-tagged relations for diagnostics.

        Relation geometry is intentionally not constructed by this extractor.
        """
        values = self.extract_values(
            relation.tags,
            osm_type="relation",
        )

        if values:
            self.geometry_failures[
                "relation_not_emitted"
            ] += len(values)


def print_counter(
    title: str,
    counter: Counter[str],
) -> None:
    """Print a small diagnostic Counter in sorted key order."""
    print(title)

    if not counter:
        print("  None")
        return

    for key in sorted(counter):
        print(
            f"  {key}: {counter[key]:,}"
        )


def main() -> None:
    """Extract and write normalized OSM postcode observations."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input PBF not found: {INPUT_PATH}"
        )

    print(
        f"Reading {INPUT_PATH}..."
    )

    handler = PostcodeHandler()

    handler.apply_file(
        str(INPUT_PATH),
        locations=True,
    )

    features = handler.features

    postcode_counts = Counter(
        feature["properties"]["postcode"]
        for feature in features
    )

    prefix_3_counts = Counter(
        feature["properties"]["prefix_3"]
        for feature in features
    )

    prefix_2_counts = Counter(
        feature["properties"]["prefix_2"]
        for feature in features
    )

    prefix_1_counts = Counter(
        feature["properties"]["prefix_1"]
        for feature in features
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            feature_collection,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        ),
        encoding="utf-8",
    )

    print()
    print_counter(
        "Objects with postcode tags:",
        handler.object_counts,
    )

    print()
    print_counter(
        "Tag occurrences:",
        handler.tag_counts,
    )

    print()
    print_counter(
        "Accepted tag values:",
        handler.accepted_counts,
    )

    print()
    print_counter(
        "Rejected tag values:",
        handler.rejected_counts,
    )

    print()
    print_counter(
        "Geometry failures / omissions:",
        handler.geometry_failures,
    )

    print()
    print(
        f"Output observations: "
        f"{len(features):,}"
    )
    print(
        f"Distinct 4-digit postcodes: "
        f"{len(postcode_counts):,}"
    )
    print(
        f"Distinct 3-digit prefixes: "
        f"{len(prefix_3_counts):,}"
    )
    print(
        f"Distinct 2-digit prefixes: "
        f"{len(prefix_2_counts):,}"
    )
    print(
        f"Distinct 1-digit prefixes: "
        f"{len(prefix_1_counts):,}"
    )

    if handler.rejected_values:
        print()
        print(
            "Most common rejected values:"
        )

        for value, count in (
            handler.rejected_values.most_common(
                20
            )
        ):
            print(
                f"  {value!r}: {count:,}"
            )

    print()
    print(
        f"Wrote {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()