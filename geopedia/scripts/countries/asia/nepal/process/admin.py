
"""
Process Nepal's administrative boundaries into GeoPedia-ready GeoJSON files.

Administrative levels:
    ADM1: Provinces (7)
    ADM2: Districts (77)
    ADM3: Local levels (753)

Source files:
    data/raw/countries/nepal/surajmazar_repo/province.geojson
    data/raw/countries/nepal/surajmazar_repo/district.geojson
    data/raw/countries/nepal/surajmazar_repo/municipality.geojson

Output files:
    public/data/countries/nepal/geojson/nepal_adm1.geojson
    public/data/countries/nepal/geojson/nepal_adm2.geojson
    public/data/countries/nepal/geojson/nepal_adm3.geojson

Processing:
    - Standardize current province names.
    - Preserve English and Nepali administrative names.
    - Assign parent regions using existing administrative codes.
    - Exclude non-municipal features from ADM3.
    - Consolidate multipart municipalities by municipality code.
    - Simplify geometries while preserving topology.
    - Validate administrative counts and parent relationships.

Usage:
    python scripts/countries/asia/nepal/process/admin.py
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = ROOT / "data/raw/countries/nepal/surajmazar_repo"
OUTPUT_DIR = ROOT / "public/data/countries/nepal/geojson"

PROVINCE_INPUT = RAW_DIR / "province.geojson"
DISTRICT_INPUT = RAW_DIR / "district.geojson"
MUNICIPALITY_INPUT = RAW_DIR / "municipality.geojson"

ADM1_OUTPUT = OUTPUT_DIR / "nepal_adm1.geojson"
ADM2_OUTPUT = OUTPUT_DIR / "nepal_adm2.geojson"
ADM3_OUTPUT = OUTPUT_DIR / "nepal_adm3.geojson"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ADM1_TOLERANCE = 0.001
ADM2_TOLERANCE = 0.001
ADM3_TOLERANCE = 0.0005

EXPECTED_ADM1_COUNT = 7
EXPECTED_ADM2_COUNT = 77
EXPECTED_ADM3_COUNT = 753

PROVINCE_NAMES = {
    "1": ("Koshi", "कोशी"),
    "2": ("Madhesh", "मधेश"),
    "3": ("Bagmati", "बागमती"),
    "4": ("Gandaki", "गण्डकी"),
    "5": ("Lumbini", "लुम्बिनी"),
    "6": ("Karnali", "कर्णाली"),
    "7": ("Sudurpashchim", "सुदूरपश्चिम"),
}

DISTRICT_NATIVE_NAME_OVERRIDES = {
    "501": "रुकुम पूर्व",
}

MUNICIPALITY_PROVINCE_CODE_OVERRIDES = {
    "40305": "4",  # Thasang, Mustang District, Gandaki
}

MUNICIPALITY_TYPES = {
    "Gaunpalika": "Rural Municipality",
    "Nagarpalika": "Municipality",
    "Upamahanagarpalika": "Sub-metropolitan City",
    "Mahanagarpalika": "Metropolitan City",
}

EXPECTED_MUNICIPALITY_TYPES = {
    "Rural Municipality": 460,
    "Municipality": 276,
    "Sub-metropolitan City": 11,
    "Metropolitan City": 6,
}

NATIVE_MUNICIPALITY_SUFFIXES = (
    "उपमहानगरपालिका",
    "महानगरपालिका",
    "गाउँपालिका",
    "नगरपालिका",
)

DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_features(path):
    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    return data["features"]


def polygon_parts(geometry):
    """
    Recursively extract polygonal components from a geometry.

    Geometry repair may produce GeometryCollections containing
    non-polygonal components, which are not needed for this dataset.
    """
    if geometry.is_empty:
        return []

    if geometry.geom_type == "Polygon":
        return [geometry]

    if geometry.geom_type in ("MultiPolygon", "GeometryCollection"):
        parts = []

        for component in geometry.geoms:
            parts.extend(polygon_parts(component))

        return parts

    return []


def ensure_polygonal(geometry):
    """Repair a geometry and retain only its polygonal components."""
    if not geometry.is_valid:
        geometry = make_valid(geometry)

    parts = polygon_parts(geometry)

    if not parts:
        raise ValueError("Geometry contains no polygonal components.")

    result = parts[0] if len(parts) == 1 else unary_union(parts)

    if result.is_empty:
        raise ValueError("Geometry is empty.")

    if result.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError(
            f"Unexpected geometry type: {result.geom_type}"
        )

    if not result.is_valid:
        raise ValueError("Unable to produce valid polygonal geometry.")

    return result


def process_geometry(geometry, tolerance):
    geometry = ensure_polygonal(geometry)

    geometry = geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    return ensure_polygonal(geometry)


def get_native_municipality_name(name):
    """Remove the administrative type suffix from a Nepali name."""
    name = name.strip()

    for suffix in NATIVE_MUNICIPALITY_SUFFIXES:
        if name.endswith(suffix):
            return name[:-len(suffix)].strip()

    return name


def create_feature(admin_id, properties, geometry):
    return {
        "type": "Feature",
        "id": admin_id,
        "properties": {
            "admin_id": admin_id,
            **properties,
        },
        "geometry": mapping(geometry),
    }


def validate_features(features, expected_count, level):
    if len(features) != expected_count:
        raise ValueError(
            f"{level}: expected {expected_count} features, "
            f"found {len(features)}."
        )

    ids = [feature["id"] for feature in features]

    if len(ids) != len(set(ids)):
        raise ValueError(f"{level}: duplicate administrative IDs.")

    for feature in features:
        props = feature["properties"]

        if not props["name"].strip():
            raise ValueError(
                f"{level}: missing English name for {feature['id']}."
            )

        if not DEVANAGARI_PATTERN.search(props["nativeName"]):
            raise ValueError(
                f"{level}: missing Nepali name for {feature['id']}."
            )

        if props["admin_id"] != feature["id"]:
            raise ValueError(
                f"{level}: mismatched feature and administrative IDs."
            )


def write_geojson(path, features):
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
            allow_nan=False,
        )

    size_mb = path.stat().st_size / (1024 * 1024)

    print(f"Written: {path.name}")
    print(f"Features: {len(features)}")
    print(f"File size: {size_mb:.2f} MB")


# ---------------------------------------------------------------------------
# ADM1 — Provinces
# ---------------------------------------------------------------------------

def process_provinces():
    raw_features = load_features(PROVINCE_INPUT)

    features = []
    provinces_by_id = {}

    for raw_feature in raw_features:
        props = raw_feature["properties"]

        province_id = str(props["province_code"])

        if province_id in provinces_by_id:
            raise ValueError(f"Duplicate province ID: {province_id}")

        name, native_name = PROVINCE_NAMES[province_id]

        geometry = process_geometry(
            shape(raw_feature["geometry"]),
            ADM1_TOLERANCE,
        )

        feature = create_feature(
            province_id,
            {
                "name": name,
                "nativeName": native_name,
            },
            geometry,
        )

        features.append(feature)
        provinces_by_id[province_id] = feature["properties"]

    validate_features(features, EXPECTED_ADM1_COUNT, "ADM1")

    features.sort(key=lambda feature: int(feature["id"]))

    return features, provinces_by_id


# ---------------------------------------------------------------------------
# ADM2 — Districts
# ---------------------------------------------------------------------------

def process_districts(provinces_by_id):
    raw_features = load_features(DISTRICT_INPUT)

    features = []
    districts_by_id = {}

    for raw_feature in raw_features:
        props = raw_feature["properties"]

        district_id = str(props["district_code"])
        province_id = str(props["province_code"])

        if district_id in districts_by_id:
            raise ValueError(f"Duplicate district ID: {district_id}")

        if province_id not in provinces_by_id:
            raise ValueError(
                f"District {district_id} has unknown province "
                f"{province_id}."
            )

        province = provinces_by_id[province_id]

        geometry = process_geometry(
            shape(raw_feature["geometry"]),
            ADM2_TOLERANCE,
        )

        feature = create_feature(
            district_id,
            {
                "name": props["district_name_en"].strip(),
                "nativeName": DISTRICT_NATIVE_NAME_OVERRIDES.get(
                    district_id,
                    props["district_name_np"].strip(),
                ),
                "province": province["name"],
                "provinceId": province_id,
            },
            geometry,
        )

        features.append(feature)
        districts_by_id[district_id] = feature["properties"]

    validate_features(features, EXPECTED_ADM2_COUNT, "ADM2")

    features.sort(key=lambda feature: int(feature["id"]))

    return features, districts_by_id


# ---------------------------------------------------------------------------
# ADM3 — Local levels
# ---------------------------------------------------------------------------

def process_municipalities(provinces_by_id, districts_by_id):
    raw_features = load_features(MUNICIPALITY_INPUT)

    grouped_features = defaultdict(list)
    excluded_count = 0
    merged_count = 0

    # Group all polygon parts belonging to the same municipality.
    for raw_feature in raw_features:
        props = raw_feature["properties"]
        municipality_code = props.get("municipality_code")

        # Exclude national parks, reserves, and other non-municipal areas.
        if not municipality_code:
            excluded_count += 1
            continue

        municipality_id = str(municipality_code)

        grouped_features[municipality_id].append(raw_feature)

    features = []

    for municipality_id, parts in grouped_features.items():
        props = parts[0]["properties"]

        province_id = MUNICIPALITY_PROVINCE_CODE_OVERRIDES.get(
            municipality_id,
            str(props["province_code"]),
        )
        district_id = str(props["district_code"])

        if province_id not in provinces_by_id:
            raise ValueError(
                f"Municipality {municipality_id} has unknown province "
                f"{province_id}."
            )

        if district_id not in districts_by_id:
            raise ValueError(
                f"Municipality {municipality_id} has unknown district "
                f"{district_id}."
            )

        province = provinces_by_id[province_id]
        district = districts_by_id[district_id]

        if district["provinceId"] != province_id:
            raise ValueError(
                f"Municipality {municipality_id} has inconsistent "
                f"province and district assignments."
            )

        # Verify that all parts have identical administrative properties.
        comparison_fields = (
            "province_code",
            "district_code",
            "municipality_code",
            "gapa_napa",
            "gapa_napa_np",
            "type",
            "key",
        )

        for part in parts[1:]:
            part_props = part["properties"]

            for field in comparison_fields:
                if props.get(field) != part_props.get(field):
                    raise ValueError(
                        f"Conflicting property '{field}' for "
                        f"municipality {municipality_id}."
                    )

        municipality_type = MUNICIPALITY_TYPES[props["type"]]

        # Repair individual polygon parts before merging.
        geometries = [
            ensure_polygonal(shape(part["geometry"]))
            for part in parts
        ]

        if len(geometries) > 1:
            geometry = unary_union(geometries)
            merged_count += len(geometries) - 1

            print(
                f"Consolidated {props['key']} ({municipality_id}): "
                f"{len(geometries)} parts -> {geometry.geom_type}"
            )
        else:
            geometry = geometries[0]

        # Simplify only after all municipality parts have been combined.
        geometry = process_geometry(
            geometry,
            ADM3_TOLERANCE,
        )

        feature = create_feature(
            municipality_id,
            {
                "name": props["key"].strip(),
                "nativeName": get_native_municipality_name(
                    props["gapa_napa_np"]
                ),
                "province": province["name"],
                "provinceId": province_id,
                "district": district["name"],
                "districtId": district_id,
                "type": municipality_type,
            },
            geometry,
        )

        features.append(feature)

    validate_features(features, EXPECTED_ADM3_COUNT, "ADM3")

    type_counts = Counter(
        feature["properties"]["type"]
        for feature in features
    )

    if dict(type_counts) != EXPECTED_MUNICIPALITY_TYPES:
        raise ValueError(
            f"Unexpected municipality type distribution: "
            f"{dict(type_counts)}"
        )

    features.sort(key=lambda feature: int(feature["id"]))

    print(f"\nRaw ADM3 features: {len(raw_features)}")
    print(f"Excluded non-municipal features: {excluded_count}")
    print(f"Consolidated additional polygon parts: {merged_count}")
    print(f"Final municipality count: {len(features)}")

    print("\nMunicipality types:")

    for municipality_type, count in type_counts.most_common():
        print(f"  {municipality_type}: {count}")

    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NEPAL ADMINISTRATIVE BOUNDARY PROCESSING")
    print("=" * 60)

    print("\nProcessing ADM1 — Provinces...")
    adm1, provinces_by_id = process_provinces()

    print("\nProcessing ADM2 — Districts...")
    adm2, districts_by_id = process_districts(provinces_by_id)

    print("\nProcessing ADM3 — Local levels...")
    adm3 = process_municipalities(
        provinces_by_id,
        districts_by_id,
    )

    print("\n" + "=" * 60)
    print("WRITING PROCESSED GEOJSON FILES")
    print("=" * 60)

    print("\nADM1:")
    write_geojson(ADM1_OUTPUT, adm1)

    print("\nADM2:")
    write_geojson(ADM2_OUTPUT, adm2)

    print("\nADM3:")
    write_geojson(ADM3_OUTPUT, adm3)

    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)

    for level, features in (
        ("ADM1", adm1),
        ("ADM2", adm2),
        ("ADM3", adm3),
    ):
        native_count = sum(
            bool(
                DEVANAGARI_PATTERN.search(
                    feature["properties"]["nativeName"]
                )
            )
            for feature in features
        )

        print(
            f"{level}: {len(features)} features, "
            f"{native_count}/{len(features)} native names"
        )

    print(f"\nTotal administrative regions: {len(adm1) + len(adm2) + len(adm3)}")
    print("\nProcessing completed successfully.")


if __name__ == "__main__":
    main()
