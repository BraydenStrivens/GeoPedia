
"""
Process Bangladesh ADM1–ADM3 administrative boundaries for GeoPedia.

Geometry and administrative hierarchy:
  geoBoundaries-BGD-ADM1.geojson
  geoBoundaries-BGD-ADM2.geojson
  geoBoundaries-BGD-ADM3.geojson

Bengali names:
  ifahimreza_bangladesh_geojson/bd-divisions.json
  ifahimreza_bangladesh_geojson/bd-districts.json

Outputs:
  public/data/countries/bangladesh/geojson/
    bangladesh_adm1.geojson
    bangladesh_adm2.geojson
    bangladesh_adm3.geojson

ADM1: English + Bengali names
ADM2: English + Bengali names, parent division
ADM3: English names, parent district and division

Parent relationships are determined using the original,
unsimplified geometries and an equal-area projection.

Run:
  python scripts/countries/asia/bangladesh/process/admin.py

Dependencies:
  pip install ijson shapely pyproj
"""

import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import ijson
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[5]

RAW = ROOT / "data/raw/countries/bangladesh"
NAMES = RAW / "ifahimreza_bangladesh_geojson"

OUTPUT = ROOT / "public/data/countries/bangladesh/geojson"

EXPECTED_COUNTS = {
    1: 8,
    2: 64,
    3: 544,
}

TOLERANCES = {
    1: 0.001,
    2: 0.001,
    3: 0.0005,
}

ALIASES = {
    "barisal": "barishal",
    "chittagong": "chattogram",
    "bogra": "bogura",
    "jessore": "jashore",
    "comilla": "cumilla",
    "rajshani": "rajshahi",
    "brahamanbaria": "brahmanbaria",
    "netrakona": "netrokona",
    "chapainababganj": "chapainawabganj",
    "moulvibazar": "maulvibazar",
    "khagrachhari": "khagrachari",
    "sirajganj": "sirajgonj",
}

TRANSFORMER = Transformer.from_crs(
    "EPSG:4326",
    (
        "+proj=laea "
        "+lat_0=24 "
        "+lon_0=90 "
        "+datum=WGS84 "
        "+units=m "
        "+no_defs"
    ),
    always_xy=True,
)


def normalize(value):
    value = unicodedata.normalize(
        "NFKC",
        str(value or ""),
    )

    value = "".join(
        character
        for character in value.casefold()
        if character.isalnum()
    )

    return ALIASES.get(value, value)


def load_records(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value

    raise ValueError(
        f"Unexpected JSON structure: {path}"
    )


def load_features(level):
    path = RAW / f"geoBoundaries-BGD-ADM{level}.geojson"

    with path.open("rb") as file:
        features = list(
            ijson.items(file, "features.item")
        )

    expected = EXPECTED_COUNTS[level]

    if len(features) != expected:
        raise ValueError(
            f"ADM{level}: expected {expected} features, "
            f"found {len(features)}"
        )

    return features


def build_name_lookup(records):
    lookup = defaultdict(list)

    for record in records:
        lookup[normalize(record["name"])].append(record)

    return lookup


def match_name(name, lookup, level):
    candidates = lookup.get(normalize(name), [])

    if len(candidates) != 1:
        raise ValueError(
            f"ADM{level}: cannot uniquely match "
            f"{name!r}; candidates={len(candidates)}"
        )

    record = candidates[0]
    native_name = str(record.get("bn_name") or "").strip()

    if not native_name:
        raise ValueError(
            f"ADM{level}: missing Bengali name for {name}"
        )

    return native_name


def project_geometry(geometry):
    return transform(
        TRANSFORMER.transform,
        shape(geometry),
    )


def simplify_geometry(geometry, tolerance):
    original = shape(geometry)

    simplified = original.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified.is_empty or not simplified.is_valid:
        raise ValueError(
            "Simplification produced invalid geometry"
        )

    return mapping(simplified)


def assign_parents(children, parents, child_level, parent_level):
    """
    Assign every child to the parent with the largest overlap.

    All comparisons use original, unsimplified geometries
    projected to a Bangladesh-centered equal-area CRS.

    Returns parent indices aligned with the children list.
    """

    print(
        f"Assigning ADM{child_level} -> ADM{parent_level} "
        "using geometry..."
    )

    parent_geometries = [
        project_geometry(feature["geometry"])
        for feature in parents
    ]

    tree = STRtree(parent_geometries)

    assignments = []
    coverage_values = []

    for child in children:
        name = child["properties"]["shapeName"]

        child_geometry = project_geometry(
            child["geometry"]
        )

        if child_geometry.is_empty or child_geometry.area <= 0:
            raise ValueError(
                f"ADM{child_level} {name}: invalid area"
            )

        candidate_indices = tree.query(child_geometry)

        overlaps = []

        for index in candidate_indices:
            index = int(index)

            parent_geometry = parent_geometries[index]

            intersection_area = child_geometry.intersection(
                parent_geometry
            ).area

            if intersection_area > 0:
                overlaps.append(
                    (intersection_area, index)
                )

        if not overlaps:
            raise ValueError(
                f"ADM{child_level} {name}: "
                f"no ADM{parent_level} overlap"
            )

        overlaps.sort(reverse=True)

        best_area, best_index = overlaps[0]

        best_area, best_index = overlaps[0]

        coverage = best_area / child_geometry.area

        assignments.append(best_index)
        coverage_values.append(coverage)

    print(
        f"  Assigned: {len(assignments)}/{len(children)}"
    )
    print(
        f"  Minimum parent coverage: "
        f"{min(coverage_values):.2%}"
    )
    print(
        f"  Average parent coverage: "
        f"{sum(coverage_values) / len(coverage_values):.2%}"
    )

    return assignments


def process_adm1(source, division_lookup):
    features = []

    for feature in source:
        properties = feature["properties"]

        name = properties["shapeName"]
        native_name = match_name(
            name,
            division_lookup,
            1,
        )

        features.append({
            "type": "Feature",
            "id": properties["shapeID"],
            "properties": {
                "name": name,
                "nativeName": native_name,
            },
            "geometry": simplify_geometry(
                feature["geometry"],
                TOLERANCES[1],
            ),
        })

    return features


def process_adm2(
    source,
    adm1_source,
    adm1_processed,
    district_lookup,
):
    parent_indices = assign_parents(
        source,
        adm1_source,
        child_level=2,
        parent_level=1,
    )

    features = []

    for feature, parent_index in zip(
        source,
        parent_indices,
    ):
        properties = feature["properties"]

        name = properties["shapeName"]
        native_name = match_name(
            name,
            district_lookup,
            2,
        )

        division = adm1_processed[parent_index]

        features.append({
            "type": "Feature",
            "id": properties["shapeID"],
            "properties": {
                "name": name,
                "nativeName": native_name,
                "division": division["properties"]["name"],
                "divisionId": division["id"],
            },
            "geometry": simplify_geometry(
                feature["geometry"],
                TOLERANCES[2],
            ),
        })

    return features


def process_adm3(
    source,
    adm2_source,
    adm2_processed,
):
    parent_indices = assign_parents(
        source,
        adm2_source,
        child_level=3,
        parent_level=2,
    )

    features = []

    for feature, parent_index in zip(
        source,
        parent_indices,
    ):
        properties = feature["properties"]

        district = adm2_processed[parent_index]
        district_properties = district["properties"]

        features.append({
            "type": "Feature",
            "id": properties["shapeID"],
            "properties": {
                "name": properties["shapeName"],
                "district": district_properties["name"],
                "districtId": district["id"],
                "division": district_properties["division"],
                "divisionId": district_properties["divisionId"],
            },
            "geometry": simplify_geometry(
                feature["geometry"],
                TOLERANCES[3],
            ),
        })

    return features


def validate(level, features):
    expected = EXPECTED_COUNTS[level]

    if len(features) != expected:
        raise ValueError(
            f"ADM{level}: expected {expected} features, "
            f"found {len(features)}"
        )

    ids = [
        feature["id"]
        for feature in features
    ]

    duplicates = [
        value
        for value, count in Counter(ids).items()
        if count > 1
    ]

    if duplicates:
        raise ValueError(
            f"ADM{level}: duplicate IDs: {duplicates}"
        )

    for feature in features:
        properties = feature["properties"]

        if not properties.get("name"):
            raise ValueError(
                f"ADM{level}: missing English name"
            )

        if level <= 2 and not properties.get("nativeName"):
            raise ValueError(
                f"ADM{level}: missing Bengali name "
                f"for {properties['name']}"
            )

        if level >= 2:
            if not properties.get("division"):
                raise ValueError(
                    f"ADM{level}: missing division "
                    f"for {properties['name']}"
                )

            if not properties.get("divisionId"):
                raise ValueError(
                    f"ADM{level}: missing division ID "
                    f"for {properties['name']}"
                )

        if level == 3:
            if not properties.get("district"):
                raise ValueError(
                    f"ADM3: missing district "
                    f"for {properties['name']}"
                )

            if not properties.get("districtId"):
                raise ValueError(
                    f"ADM3: missing district ID "
                    f"for {properties['name']}"
                )

    print(
        f"ADM{level}: validated {len(features)} features"
    )


def write_geojson(level, features):
    path = OUTPUT / f"bangladesh_adm{level}.geojson"

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": features,
            },
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_mb = path.stat().st_size / (1024 * 1024)

    print(
        f"Wrote {path.relative_to(ROOT)} "
        f"({size_mb:.2f} MB)"
    )


def main():
    print("Loading Bangladesh administrative boundaries...")

    adm1_source = load_features(1)
    adm2_source = load_features(2)
    adm3_source = load_features(3)

    divisions = load_records(
        NAMES / "bd-divisions.json"
    )

    districts = load_records(
        NAMES / "bd-districts.json"
    )

    division_lookup = build_name_lookup(divisions)
    district_lookup = build_name_lookup(districts)

    print("\nProcessing Bangladesh ADM1...")
    adm1 = process_adm1(
        adm1_source,
        division_lookup,
    )

    print("\nProcessing Bangladesh ADM2...")
    adm2 = process_adm2(
        adm2_source,
        adm1_source,
        adm1,
        district_lookup,
    )

    print("\nProcessing Bangladesh ADM3...")
    adm3 = process_adm3(
        adm3_source,
        adm2_source,
        adm2,
    )

    print("\nValidating processed data...")

    for level, features in (
        (1, adm1),
        (2, adm2),
        (3, adm3),
    ):
        validate(level, features)

    print("\nWriting GeoJSON files...")

    for level, features in (
        (1, adm1),
        (2, adm2),
        (3, adm3),
    ):
        write_geojson(level, features)

    print("\nBangladesh processing complete.")


if __name__ == "__main__":
    main()
