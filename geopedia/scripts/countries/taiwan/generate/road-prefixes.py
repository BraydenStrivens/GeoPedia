"""
Generate Taiwan's county-road prefix quiz GeoJSON.

Source
------
public/data/countries/taiwan/geojson/counties.geojson

Output
------
public/data/countries/taiwan/geojson/road-prefixes.geojson

Taiwan county roads use a Chinese character before the route number to
identify the county or municipality associated with the road.

The Plonk It Taiwan road-prefix reference map provides 16 unique
county-specific characters. Three cities instead use the generic 市
("city") prefix:

    Keelung City
    Hsinchu City
    Chiayi City

Those three geographically separate features are merged into one
MultiPolygon quiz feature so 市 can be treated as a single answer.

Taipei City is excluded because the reference map shows no road prefix.

Kinmen County and Lienchiang County are also excluded because the
reference map does not provide unique road-prefix characters for them.

The resulting GeoJSON therefore contains:

    16 unique county-prefix features
     1 combined 市 feature
    --------------------------------
    17 total quiz features

Run from the GeoPedia project root:

    python scripts/countries/taiwan/generate/road-prefixes.py
"""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    ROOT
    / "public"
    / "data"
    / "countries"
    / "taiwan"
    / "geojson"
    / "counties.geojson"
)

OUTPUT_PATH = (
    ROOT
    / "public"
    / "data"
    / "countries"
    / "taiwan"
    / "geojson"
    / "road-prefixes.geojson"
)


# ---------------------------------------------------------------------------
# Prefix assignments
# ---------------------------------------------------------------------------

PREFIX_BY_COUNTY_ID = {
    "TWN.7.13_1": "桃",  # Taoyuan
    "TWN.3.1_1": "北",   # New Taipei
    "TWN.7.5_1": "竹",   # Hsinchu County
    "TWN.7.8_1": "苗",   # Miaoli
    "TWN.4.1_1": "中",   # Taichung
    "TWN.7.1_1": "彰",   # Changhua
    "TWN.7.15_1": "雲",  # Yunlin
    "TWN.7.3_1": "嘉",   # Chiayi County
    "TWN.5.1_1": "南",   # Tainan
    "TWN.2.1_1": "高",   # Kaohsiung
    "TWN.7.11_1": "屏",  # Pingtung
    "TWN.7.14_1": "宜",  # Yilan
    "TWN.7.9_1": "投",   # Nantou
    "TWN.7.6_1": "花",   # Hualien
    "TWN.7.12_1": "東",  # Taitung
    "TWN.7.10_1": "澎",  # Penghu
}

CITY_PREFIX_COUNTY_IDS = {
    "TWN.7.7_1",  # Keelung City
    "TWN.7.4_1",  # Hsinchu City
    "TWN.7.2_1",  # Chiayi City
}

EXPECTED_SOURCE_COUNT = 22
EXPECTED_OUTPUT_COUNT = 17


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading Taiwan counties...")

    source = load_geojson(SOURCE_PATH)
    source_features = source["features"]

    if len(source_features) != EXPECTED_SOURCE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SOURCE_COUNT} counties, "
            f"found {len(source_features)}."
        )

    features_by_id = {
        feature["properties"]["county_id"]: feature
        for feature in source_features
    }

    if len(features_by_id) != EXPECTED_SOURCE_COUNT:
        raise ValueError(
            "Duplicate county_id values found in counties.geojson."
        )

    required_ids = (
        set(PREFIX_BY_COUNTY_ID)
        | CITY_PREFIX_COUNTY_IDS
    )

    missing_ids = required_ids - set(features_by_id)

    if missing_ids:
        raise ValueError(
            "Missing required county IDs: "
            f"{sorted(missing_ids)}"
        )

    output_features: list[dict] = []

    # -----------------------------------------------------------------------
    # Unique county-specific prefixes
    # -----------------------------------------------------------------------

    for county_id, prefix in PREFIX_BY_COUNTY_ID.items():
        source_feature = features_by_id[county_id]
        source_props = source_feature["properties"]

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "road_prefix_id": county_id,
                    "road_prefix": prefix,
                    "county_id": county_id,
                    "county": source_props["county"],
                    "native_county": source_props["native_county"],
                },
                "geometry": source_feature["geometry"],
            }
        )

    # -----------------------------------------------------------------------
    # Generic 市 prefix
    # -----------------------------------------------------------------------

    city_geometries = [
        shape(
            features_by_id[county_id]["geometry"]
        )
        for county_id in CITY_PREFIX_COUNTY_IDS
    ]

    city_geometry = unary_union(
        city_geometries
    )

    if city_geometry.is_empty:
        raise ValueError(
            "Combined 市 geometry is empty."
        )

    if not city_geometry.is_valid:
        raise ValueError(
            "Combined 市 geometry is invalid."
        )

    output_features.append(
        {
            "type": "Feature",
            "properties": {
                "road_prefix_id": "city",
                "road_prefix": "市",
                "county_id": None,
                "county": (
                    "Keelung City / Hsinchu City / Chiayi City"
                ),
                "native_county": (
                    "基隆市 / 新竹市 / 嘉義市"
                ),
            },
            "geometry": mapping(city_geometry),
        }
    )

    # -----------------------------------------------------------------------
    # Validate
    # -----------------------------------------------------------------------

    if len(output_features) != EXPECTED_OUTPUT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_OUTPUT_COUNT} output features, "
            f"found {len(output_features)}."
        )

    road_prefix_ids = [
        feature["properties"]["road_prefix_id"]
        for feature in output_features
    ]

    if len(road_prefix_ids) != len(set(road_prefix_ids)):
        raise ValueError(
            "Duplicate road_prefix_id values found."
        )

    prefixes = [
        feature["properties"]["road_prefix"]
        for feature in output_features
    ]

    if len(prefixes) != len(set(prefixes)):
        raise ValueError(
            "Duplicate road_prefix values found."
        )

    # -----------------------------------------------------------------------
    # Write
    # -----------------------------------------------------------------------

    output = {
        "type": "FeatureCollection",
        "features": output_features,
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
            separators=(",", ":"),
        )

    print()
    print("Taiwan road-prefix GeoJSON generated.")
    print()
    print(f"Features: {len(output_features)}")
    print(
        f"Output: {OUTPUT_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()