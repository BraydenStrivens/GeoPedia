
"""
Generate Thailand's 1-digit and 2-digit landline area-code regions.

Inputs:
    public/data/countries/thailand/geojson/provinces.geojson
    public/data/countries/thailand/geojson/districts.geojson

Outputs:
    public/data/countries/thailand/geojson/area-code-prefixes-1.geojson
    public/data/countries/thailand/geojson/area-code-prefixes-2.geojson

Area-code assignments follow the researched province/district table.
Code 052 is omitted; 053 represents its geographic coverage.
Tak uses 055.

Run:
    python scripts/countries/asia/thailand/process/area-codes.py

Requires:
    pip install shapely
"""

import json
from collections import defaultdict
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


PROJECT_ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIR = (
    PROJECT_ROOT
    / "public/data/countries/thailand/geojson"
)

# Province IDs are Thailand's two-digit administrative codes.
# Each province appears exactly once.
AREA_CODES = {
    "02": ["10", "11", "12", "13"],
    "32": ["70", "76", "77"],
    "34": ["71", "73", "74", "75"],
    "35": ["14", "15", "72"],
    "36": ["16", "17", "19"],
    "37": ["25", "26", "27"],
    "38": ["20", "21", "24"],
    "39": ["22", "23"],
    "42": ["38", "42", "43", "47", "48", "49", "39", "41"],
    "43": ["40", "44", "45", "46"],
    "44": ["30", "31", "32", "36"],
    "45": ["33", "34", "35", "37"],
    "53": ["50", "51", "57", "58"],
    "54": ["52", "54", "55", "56"],
    "55": ["62", "63", "64", "65", "53"],
    "56": ["18", "60", "61", "66", "67"],
    "73": ["94", "95", "96"],
    "74": ["90", "91", "93"],
    "75": ["80", "81", "92"],
    "76": ["82", "83"],
    "77": ["84", "85", "86"],
}

# Province ID -> district English name -> override area code.
DISTRICT_EXCEPTIONS = {
    "73": {
        "Phutthamonthon": "02",
    },
    "67": {
        "Nam Nao": "43",
    },
    "66": {
        "Sam Ngam": "55",
        "Wachirabarami": "55",
    },
}


def load_features(filename):
    path = GEOJSON_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data["type"] != "FeatureCollection":
        raise ValueError(f"Invalid FeatureCollection: {path}")

    return data["features"]


def write_geojson(filename, features):
    path = GEOJSON_DIR / filename

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print(
        f"  {filename}: {len(features)} features, "
        f"{path.stat().st_size / 1_000_000:.2f} MB"
    )


def build_province_lookup():
    lookup = {}

    for area_code, province_ids in AREA_CODES.items():
        for province_id in province_ids:
            if province_id in lookup:
                raise ValueError(
                    f"Province {province_id} assigned more than once"
                )

            lookup[province_id] = area_code

    if len(lookup) != 77:
        raise ValueError(
            f"Expected 77 province assignments, got {len(lookup)}"
        )

    return lookup


def collect_geometries():
    provinces = load_features("provinces.geojson")
    districts = load_features("districts.geojson")

    province_codes = build_province_lookup()
    geometries = defaultdict(list)

    if len(provinces) != 77:
        raise ValueError(
            f"Expected 77 provinces, got {len(provinces)}"
        )

    if len(districts) != 928:
        raise ValueError(
            f"Expected 928 districts, got {len(districts)}"
        )

    province_ids = {
        feature["properties"]["province_id"]
        for feature in provinces
    }

    if province_ids != set(province_codes):
        raise ValueError(
            "Province IDs do not match the area-code assignments. "
            f"Missing: {sorted(province_ids - set(province_codes))}; "
            f"Extra: {sorted(set(province_codes) - province_ids)}"
        )

    # For ordinary provinces, use their existing province geometry.
    for feature in provinces:
        properties = feature["properties"]
        province_id = properties["province_id"]

        if province_id in DISTRICT_EXCEPTIONS:
            continue

        area_code = province_codes[province_id]
        geometries[area_code].append(shape(feature["geometry"]))

    # For exception provinces, use all their district geometries.
    # This avoids overlapping province/district polygons.
    matched_exceptions = defaultdict(set)
    district_counts = defaultdict(int)

    for feature in districts:
        properties = feature["properties"]
        province_id = properties["province_id"]

        if province_id not in DISTRICT_EXCEPTIONS:
            continue

        district_counts[province_id] += 1
        district_name = properties["district"]

        overrides = DISTRICT_EXCEPTIONS[province_id]
        area_code = overrides.get(
            district_name,
            province_codes[province_id],
        )

        if district_name in overrides:
            matched_exceptions[province_id].add(district_name)

        geometries[area_code].append(shape(feature["geometry"]))

    # Fail rather than silently assigning an exception incorrectly.
    for province_id, overrides in DISTRICT_EXCEPTIONS.items():
        expected = set(overrides)
        actual = matched_exceptions[province_id]

        if expected != actual:
            raise ValueError(
                f"District exception mismatch in province "
                f"{province_id}: expected {sorted(expected)}, "
                f"matched {sorted(actual)}"
            )

        if district_counts[province_id] == 0:
            raise ValueError(
                f"No districts found for province {province_id}"
            )

    return geometries


def dissolve_regions(geometries):
    features = []

    for code, parts in sorted(geometries.items()):
        geometry = unary_union(parts)

        if geometry.is_empty or not geometry.is_valid:
            raise ValueError(
                f"Invalid dissolved geometry for area code {code}"
            )

        features.append({
            "type": "Feature",
            "properties": {
                "area_code_prefix": code,
                "area_code_group": "2" if code == "02" else code[0],
            },
            "geometry": mapping(geometry),
        })

    return features


def main():
    print("Thailand landline area-code processing")

    print("\nLoading province and district geometries...")
    geometries = collect_geometries()

    print("\nGenerating 2-digit regions...")
    two_digit_features = dissolve_regions(geometries)

    if len(two_digit_features) != 21:
        raise ValueError(
            f"Expected 21 regions, got {len(two_digit_features)}"
        )

    write_geojson(
        "area-code-prefixes-2.geojson",
        two_digit_features,
    )

    print("\nGenerating 1-digit regions...")
    groups = defaultdict(list)

    for feature in two_digit_features:
        code = feature["properties"]["area_code_group"]
        groups[code].append(shape(feature["geometry"]))

    one_digit_features = []

    for code, parts in sorted(groups.items()):
        geometry = unary_union(parts)

        if geometry.is_empty or not geometry.is_valid:
            raise ValueError(
                f"Invalid dissolved geometry for prefix {code}"
            )

        one_digit_features.append({
            "type": "Feature",
            "properties": {
                "area_code_prefix": code,
            },
            "geometry": mapping(geometry),
        })

    if len(one_digit_features) != 5:
        raise ValueError(
            f"Expected 5 regions, got {len(one_digit_features)}"
        )

    write_geojson(
        "area-code-prefixes-1.geojson",
        one_digit_features,
    )

    print("\nProcessing complete.")


if __name__ == "__main__":
    main()
