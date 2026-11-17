
"""
Process Bhutan geoBoundaries ADM1 and ADM2 for GeoPedia.

Inputs:
  data/raw/countries/bhutan/
    geoBoundaries-BTN-ADM1.geojson
    geoBoundaries-BTN-ADM2.geojson
    subdivisions_with_native_names.js

Outputs:
  public/data/countries/bhutan/geojson/
    bhutan_adm1.geojson
    bhutan_adm2.geojson

Processing:
- Match ADM1 English names to Dzongkha names.
- Assign each ADM2 gewog to its ADM1 dzongkhag using the
  largest area of intersection between original geometries.
- Simplify output geometry while preserving topology.
- Preserve shapeID as the GeoJSON feature ID.
- Validate counts, IDs, native names, and parent assignments.

Run from the GeoPedia project root:
  python scripts/countries/asia/bhutan/process/admin.py

Dependencies:
  pip install shapely
"""

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from shapely.geometry import mapping, shape


ROOT = Path(__file__).resolve().parents[5]

RAW = ROOT / "data/raw/countries/bhutan"

OUTPUT = (
    ROOT
    / "public/data/countries/bhutan/geojson"
)

ADM1_PATH = RAW / "geoBoundaries-BTN-ADM1.geojson"
ADM2_PATH = RAW / "geoBoundaries-BTN-ADM2.geojson"

NATIVE_NAMES_PATH = RAW / "subdivisions_with_native_names.js"

ADM1_TOLERANCE = 0.001
ADM2_TOLERANCE = 0.0005

EXPECTED_ADM1 = 20
EXPECTED_ADM2 = 205

NAME_ALIASES = {
    "lhuntse": "lhuentse",
    "thimpu": "thimphu",
    "chukha": "chhukha",
}


def normalize_name(value):
    value = unicodedata.normalize("NFKC", value)
    value = value.casefold()

    return "".join(
        char for char in value
        if char.isalnum()
    )


def load_geojson(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"Not a FeatureCollection: {path}")

    return data["features"]


def load_native_names():
    """
    Extract the 20 dzongkhag names and their Dzongkha
    translations from the JavaScript reference file.
    """

    text = NATIVE_NAMES_PATH.read_text(encoding="utf-8")

    matches = re.findall(
        r'dzongkhag:\s*"([^"]+)"\s*,\s*'
        r'dzongkhagDzongkha:\s*"([^"]+)"',
        text,
    )

    names = {}

    for english, dzongkha in matches:
        key = normalize_name(english)

        if key in names:
            raise ValueError(
                f"Duplicate native-name reference: {english}"
            )

        names[key] = dzongkha

    if len(names) != EXPECTED_ADM1:
        raise ValueError(
            f"Expected {EXPECTED_ADM1} native district names, "
            f"found {len(names)}"
        )

    return names


def validate_source(features, expected_count, level):
    if len(features) != expected_count:
        raise ValueError(
            f"ADM{level}: expected {expected_count} features, "
            f"found {len(features)}"
        )

    ids = [
        feature["properties"]["shapeID"]
        for feature in features
    ]

    if len(ids) != len(set(ids)):
        raise ValueError(f"ADM{level}: duplicate shapeIDs")

    for feature in features:
        properties = feature["properties"]

        if not properties.get("shapeID"):
            raise ValueError(f"ADM{level}: missing shapeID")

        if not properties.get("shapeName"):
            raise ValueError(f"ADM{level}: missing shapeName")

        geometry = shape(feature["geometry"])

        if geometry.is_empty or not geometry.is_valid:
            raise ValueError(
                f"ADM{level}: invalid geometry for "
                f"{properties['shapeName']}"
            )


def simplify_geometry(geometry, tolerance):
    simplified = geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified.is_empty or not simplified.is_valid:
        raise ValueError("Simplification produced invalid geometry")

    return mapping(simplified)


def process_adm1(features, native_names):
    processed = []
    districts = []

    for feature in features:
        properties = feature["properties"]

        name = properties["shapeName"]
        district_id = properties["shapeID"]

        normalized = normalize_name(name)
        lookup_key = NAME_ALIASES.get(normalized, normalized)

        native_name = native_names.get(lookup_key)

        if not native_name:
            raise ValueError(
                f"Missing Dzongkha name for district: {name}"
            )

        original_geometry = shape(feature["geometry"])

        districts.append({
            "id": district_id,
            "name": name,
            "geometry": original_geometry,
        })

        processed.append({
            "type": "Feature",
            "id": district_id,
            "properties": {
                "admin_id": district_id,
                "name": name,
                "nativeName": native_name,
                "shapeISO": properties.get("shapeISO") or None,
            },
            "geometry": simplify_geometry(
                original_geometry,
                ADM1_TOLERANCE,
            ),
        })

    print(
        f"ADM1 native names matched: "
        f"{len(processed)}/{EXPECTED_ADM1}"
    )

    return processed, districts


def find_parent(geometry, districts):
    """
    Find the dzongkhag with the largest intersection area.

    Uses original, unsimplified geometries.

    No minimum coverage threshold is required.
    """

    best_district = None
    best_area = 0.0

    for district in districts:
        district_geometry = district["geometry"]

        if not geometry.intersects(district_geometry):
            continue

        area = geometry.intersection(
            district_geometry
        ).area

        if area > best_area:
            best_area = area
            best_district = district

    if best_district is None:
        return None, 0.0

    coverage = (
        best_area / geometry.area * 100
        if geometry.area > 0
        else 0.0
    )

    return best_district, coverage


def process_adm2(features, districts):
    processed = []
    coverages = []
    parent_counts = Counter()

    for feature in features:
        properties = feature["properties"]

        name = properties["shapeName"]
        gewog_id = properties["shapeID"]

        original_geometry = shape(feature["geometry"])

        parent, coverage = find_parent(
            original_geometry,
            districts,
        )

        if parent is None:
            raise ValueError(
                f"No dzongkhag intersection found for: {name}"
            )

        coverages.append(coverage)
        parent_counts[parent["name"]] += 1

        processed.append({
            "type": "Feature",
            "id": gewog_id,
            "properties": {
                "admin_id": gewog_id,
                "name": name,
                "dzongkhag": parent["name"],
                "dzongkhagId": parent["id"],
            },
            "geometry": simplify_geometry(
                original_geometry,
                ADM2_TOLERANCE,
            ),
        })

    print(
        f"ADM2 parent assignments: "
        f"{len(processed)}/{EXPECTED_ADM2}"
    )

    print(f"Minimum parent coverage: {min(coverages):.2f}%")
    print(
        f"Average parent coverage: "
        f"{sum(coverages) / len(coverages):.2f}%"
    )

    print("\nGewogs per dzongkhag:")

    for district in sorted(districts, key=lambda d: d["name"]):
        print(
            f"  {district['name']}: "
            f"{parent_counts[district['name']]}"
        )

    return processed


def write_geojson(path, features):
    path.parent.mkdir(parents=True, exist_ok=True)

    collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_mb = path.stat().st_size / 1024 / 1024

    print(f"Wrote {path.relative_to(ROOT)} ({size_mb:.2f} MB)")


def main():
    adm1 = load_geojson(ADM1_PATH)
    adm2 = load_geojson(ADM2_PATH)

    validate_source(adm1, EXPECTED_ADM1, 1)
    validate_source(adm2, EXPECTED_ADM2, 2)

    native_names = load_native_names()

    processed_adm1, districts = process_adm1(
        adm1,
        native_names,
    )

    processed_adm2 = process_adm2(
        adm2,
        districts,
    )

    print("\nVALIDATION:")
    print(f"ADM1: {len(processed_adm1)} features")
    print(f"ADM2: {len(processed_adm2)} features")

    print("\nOUTPUT:")

    write_geojson(
        OUTPUT / "bhutan_adm1.geojson",
        processed_adm1,
    )

    write_geojson(
        OUTPUT / "bhutan_adm2.geojson",
        processed_adm2,
    )

    print("\nBhutan processing complete.")


if __name__ == "__main__":
    main()
