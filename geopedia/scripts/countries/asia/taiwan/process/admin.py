"""
Normalize Taiwan administrative boundary data for GeoPedia.

Inputs
------
data/raw/countries/taiwan/gadm41_TWN_1.json
    GADM ADM1 boundaries: 7 province-level divisions.

data/raw/countries/taiwan/gadm41_TWN_2.json
    GADM ADM2 boundaries: 22 county-level divisions.

data/raw/countries/taiwan/townships-districts/TOWN_MOI_1120317.shp
    Taiwan Ministry of the Interior township/district boundaries:
    368 township-level divisions.

Outputs
-------
data/intermediate/countries/taiwan/provinces.geojson
data/intermediate/countries/taiwan/counties.geojson
data/intermediate/countries/taiwan/townships.geojson

Hierarchy
---------
province
    -> county
        -> township

The words "province", "county", and "township" are GeoPedia's normalized
level names. Individual source features can have other administrative
types, such as special municipalities, provincial cities, cities,
districts, towns, and townships.

Important implementation details
--------------------------------
- GADM supplies the province -> county hierarchy.
- MOI COUNTYCODE values are bridged explicitly to GADM ADM2 IDs.
- No spatial join is required.
- MOI text is explicitly read as UTF-8.
- MOI native county names are preferred over GADM native county names
  where available.
- Original source IDs are preserved as stable GeoPedia IDs.
- Geometry is converted to WGS84 / EPSG:4326 for output.
- Town_Majia_Sanhe.shp is intentionally not merged into the township
  dataset. It is a supplemental polygon showing Sanhe Village, an
  exclave of Majia Township in Pingtung County, supplied separately by
  the source because of unresolved overlapping administrative
  boundaries. It does not represent an additional township.
  
Run from the GeoPedia project root:

    python scripts/countries/taiwan/process/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.validation import make_valid


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = ROOT / "data" / "raw" / "countries" / "taiwan"
INTERMEDIATE_DIR = ROOT / "data" / "intermediate" / "countries" / "taiwan"

GADM_ADM1_PATH = RAW_DIR / "gadm41_TWN_1.json"
GADM_ADM2_PATH = RAW_DIR / "gadm41_TWN_2.json"

MOI_TOWNSHIPS_PATH = (
    RAW_DIR
    / "townships-districts"
    / "TOWN_MOI_1120317.shp"
)

PROVINCES_OUTPUT = INTERMEDIATE_DIR / "provinces.geojson"
COUNTIES_OUTPUT = INTERMEDIATE_DIR / "counties.geojson"
TOWNSHIPS_OUTPUT = INTERMEDIATE_DIR / "townships.geojson"


# ---------------------------------------------------------------------------
# Expected source counts
# ---------------------------------------------------------------------------

EXPECTED_PROVINCES = 7
EXPECTED_COUNTIES = 22
EXPECTED_TOWNSHIPS = 368


# ---------------------------------------------------------------------------
# MOI county -> GADM ADM2 bridge
# ---------------------------------------------------------------------------

MOI_COUNTY_CODE_TO_GADM_ID = {
    "09020": "TWN.1.1_1",   # Kinmen
    "09007": "TWN.1.2_1",   # Lienkiang

    "64000": "TWN.2.1_1",   # Kaohsiung
    "65000": "TWN.3.1_1",   # New Taipei
    "66000": "TWN.4.1_1",   # Taichung
    "67000": "TWN.5.1_1",   # Tainan
    "63000": "TWN.6.1_1",   # Taipei

    "10007": "TWN.7.1_1",   # Changhua
    "10020": "TWN.7.2_1",   # Chiayi City
    "10010": "TWN.7.3_1",   # Chiayi County
    "10018": "TWN.7.4_1",   # Hsinchu City
    "10004": "TWN.7.5_1",   # Hsinchu County
    "10015": "TWN.7.6_1",   # Hualien
    "10017": "TWN.7.7_1",   # Keelung
    "10005": "TWN.7.8_1",   # Miaoli
    "10008": "TWN.7.9_1",   # Nantou
    "10016": "TWN.7.10_1",  # Penghu
    "10013": "TWN.7.11_1",  # Pingtung
    "10014": "TWN.7.12_1",  # Taitung
    "68000": "TWN.7.13_1",  # Taoyuan
    "10002": "TWN.7.14_1",  # Yilan
    "10009": "TWN.7.15_1",  # Yunlin
}


# ---------------------------------------------------------------------------
# Display-name normalization
# ---------------------------------------------------------------------------

PROVINCE_NAMES = {
    "TWN.1_1": ("Fujian", "福建"),
    "TWN.2_1": ("Kaohsiung", "高雄"),
    "TWN.3_1": ("New Taipei", "新北"),
    "TWN.4_1": ("Taichung", "臺中"),
    "TWN.5_1": ("Tainan", "臺南"),
    "TWN.6_1": ("Taipei", "臺北"),
    "TWN.7_1": ("Taiwan", "臺灣"),
}

# GADM concatenates several English names.
COUNTY_NAMES = {
    "TWN.1.1_1": "Kinmen",
    "TWN.1.2_1": "Lienkiang",
    "TWN.2.1_1": "Kaohsiung",
    "TWN.3.1_1": "New Taipei",
    "TWN.4.1_1": "Taichung",
    "TWN.5.1_1": "Tainan",
    "TWN.6.1_1": "Taipei",
    "TWN.7.1_1": "Changhua",
    "TWN.7.2_1": "Chiayi City",
    "TWN.7.3_1": "Chiayi County",
    "TWN.7.4_1": "Hsinchu City",
    "TWN.7.5_1": "Hsinchu County",
    "TWN.7.6_1": "Hualien",
    "TWN.7.7_1": "Keelung",
    "TWN.7.8_1": "Miaoli",
    "TWN.7.9_1": "Nantou",
    "TWN.7.10_1": "Penghu",
    "TWN.7.11_1": "Pingtung",
    "TWN.7.12_1": "Taitung",
    "TWN.7.13_1": "Taoyuan",
    "TWN.7.14_1": "Yilan",
    "TWN.7.15_1": "Yunlin",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def clean_geometry(geometry: dict) -> dict:
    geom = shape(geometry)

    if geom.is_empty:
        raise ValueError("Encountered empty geometry.")

    if not geom.is_valid:
        geom = make_valid(geom)

    if geom.is_empty:
        raise ValueError("Geometry became empty after repair.")

    return mapping(geom)


def write_feature_collection(path: Path, features: list[dict]) -> None:
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


def require_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {label} values found.")


# ---------------------------------------------------------------------------
# Load sources
# ---------------------------------------------------------------------------

print("Loading Taiwan administrative sources...")

adm1 = load_geojson(GADM_ADM1_PATH)
adm2 = load_geojson(GADM_ADM2_PATH)

townships = gpd.read_file(
    MOI_TOWNSHIPS_PATH,
    encoding="utf-8",
)

if townships.crs is None:
    raise ValueError("MOI township dataset has no CRS.")

townships = townships.to_crs("EPSG:4326")


# ---------------------------------------------------------------------------
# Validate source counts
# ---------------------------------------------------------------------------

if len(adm1["features"]) != EXPECTED_PROVINCES:
    raise ValueError(
        f"Expected {EXPECTED_PROVINCES} ADM1 features, "
        f"found {len(adm1['features'])}."
    )

if len(adm2["features"]) != EXPECTED_COUNTIES:
    raise ValueError(
        f"Expected {EXPECTED_COUNTIES} ADM2 features, "
        f"found {len(adm2['features'])}."
    )

if len(townships) != EXPECTED_TOWNSHIPS:
    raise ValueError(
        f"Expected {EXPECTED_TOWNSHIPS} township features, "
        f"found {len(townships)}."
    )


# ---------------------------------------------------------------------------
# Build province lookup
# ---------------------------------------------------------------------------

province_lookup: dict[str, dict] = {}

for feature in adm1["features"]:
    props = feature["properties"]

    province_id = props["GID_1"]

    if province_id not in PROVINCE_NAMES:
        raise ValueError(
            f"No normalized names exist for province {province_id}."
        )

    province_name, native_province = PROVINCE_NAMES[province_id]

    province_lookup[province_id] = {
        "province_id": province_id,
        "province": province_name,
        "native_province": native_province,
    }

require_unique(
    list(province_lookup.keys()),
    "province IDs",
)


# ---------------------------------------------------------------------------
# Build MOI county-name lookup
# ---------------------------------------------------------------------------

moi_county_lookup: dict[str, dict] = {}

for _, row in townships.iterrows():
    county_code = str(row["COUNTYCODE"])

    value = {
        "native_county": row["COUNTYNAME"],
        "county_id_short": row["COUNTYID"],
    }

    existing = moi_county_lookup.get(county_code)

    if existing is not None and existing != value:
        raise ValueError(
            f"Inconsistent MOI county metadata for {county_code}: "
            f"{existing} vs {value}"
        )

    moi_county_lookup[county_code] = value

if len(moi_county_lookup) != EXPECTED_COUNTIES:
    raise ValueError(
        f"Expected {EXPECTED_COUNTIES} unique MOI counties, "
        f"found {len(moi_county_lookup)}."
    )

if set(moi_county_lookup) != set(MOI_COUNTY_CODE_TO_GADM_ID):
    missing_bridge = set(moi_county_lookup) - set(MOI_COUNTY_CODE_TO_GADM_ID)
    unused_bridge = set(MOI_COUNTY_CODE_TO_GADM_ID) - set(moi_county_lookup)

    raise ValueError(
        "MOI/GADM county bridge does not match source data.\n"
        f"Missing bridge entries: {sorted(missing_bridge)}\n"
        f"Unused bridge entries: {sorted(unused_bridge)}"
    )


# Reverse bridge for county processing.
GADM_ID_TO_MOI_COUNTY_CODE = {
    gadm_id: county_code
    for county_code, gadm_id in MOI_COUNTY_CODE_TO_GADM_ID.items()
}


# ---------------------------------------------------------------------------
# Process provinces
# ---------------------------------------------------------------------------

province_features: list[dict] = []

for feature in adm1["features"]:
    props = feature["properties"]

    province_id = props["GID_1"]
    normalized = province_lookup[province_id]

    province_features.append(
        {
            "type": "Feature",
            "properties": normalized,
            "geometry": clean_geometry(feature["geometry"]),
        }
    )


# ---------------------------------------------------------------------------
# Process counties
# ---------------------------------------------------------------------------

county_features: list[dict] = []
county_lookup: dict[str, dict] = {}

for feature in adm2["features"]:
    props = feature["properties"]

    county_id = props["GID_2"]
    province_id = props["GID_1"]

    if province_id not in province_lookup:
        raise ValueError(
            f"County {county_id} references unknown province {province_id}."
        )

    if county_id not in GADM_ID_TO_MOI_COUNTY_CODE:
        raise ValueError(
            f"No MOI county-code mapping exists for GADM county {county_id}."
        )

    if county_id not in COUNTY_NAMES:
        raise ValueError(
            f"No normalized English name exists for county {county_id}."
        )

    county_code = GADM_ID_TO_MOI_COUNTY_CODE[county_id]
    moi = moi_county_lookup[county_code]
    province = province_lookup[province_id]

    normalized = {
        "county_id": county_id,
        "county": COUNTY_NAMES[county_id],
        "native_county": moi["native_county"],
        "province_id": province["province_id"],
        "province": province["province"],
        "native_province": province["native_province"],
    }

    county_lookup[county_id] = normalized

    county_features.append(
        {
            "type": "Feature",
            "properties": normalized,
            "geometry": clean_geometry(feature["geometry"]),
        }
    )

require_unique(
    list(county_lookup.keys()),
    "county IDs",
)


# ---------------------------------------------------------------------------
# Process townships / districts
# ---------------------------------------------------------------------------

township_features: list[dict] = []

township_ids = [
    str(value)
    for value in townships["TOWNCODE"].tolist()
]

require_unique(township_ids, "township IDs")

for _, row in townships.iterrows():
    township_id = str(row["TOWNCODE"])
    county_code = str(row["COUNTYCODE"])

    county_id = MOI_COUNTY_CODE_TO_GADM_ID.get(county_code)

    if county_id is None:
        raise ValueError(
            f"Township {township_id} references unmapped "
            f"MOI county code {county_code}."
        )

    county = county_lookup[county_id]

    township_name = str(row["TOWNENG"]).strip()
    native_township = str(row["TOWNNAME"]).strip()

    if not township_name:
        raise ValueError(
            f"Township {township_id} has no English name."
        )

    if not native_township:
        raise ValueError(
            f"Township {township_id} has no native name."
        )

    normalized = {
        "township_id": township_id,
        "township": township_name,
        "native_township": native_township,

        "county_id": county["county_id"],
        "county": county["county"],
        "native_county": county["native_county"],

        "province_id": county["province_id"],
        "province": county["province"],
        "native_province": county["native_province"],
    }

    geom = row.geometry

    if geom is None or geom.is_empty:
        raise ValueError(
            f"Township {township_id} has empty geometry."
        )

    if not geom.is_valid:
        geom = make_valid(geom)

    if geom.is_empty:
        raise ValueError(
            f"Township {township_id} geometry became empty after repair."
        )

    township_features.append(
        {
            "type": "Feature",
            "properties": normalized,
            "geometry": mapping(geom),
        }
    )


# ---------------------------------------------------------------------------
# Final hierarchy validation
# ---------------------------------------------------------------------------

if len(county_lookup) != EXPECTED_COUNTIES:
    raise ValueError(
        f"Expected {EXPECTED_COUNTIES} normalized counties, "
        f"found {len(county_lookup)}."
    )

township_parent_ids = {
    feature["properties"]["county_id"]
    for feature in township_features
}

missing_county_parents = set(county_lookup) - township_parent_ids

if missing_county_parents:
    raise ValueError(
        "Counties with no township children: "
        f"{sorted(missing_county_parents)}"
    )

county_parent_ids = {
    feature["properties"]["province_id"]
    for feature in county_features
}

missing_province_parents = set(province_lookup) - county_parent_ids

if missing_province_parents:
    raise ValueError(
        "Provinces with no county children: "
        f"{sorted(missing_province_parents)}"
    )


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------

write_feature_collection(
    PROVINCES_OUTPUT,
    province_features,
)

write_feature_collection(
    COUNTIES_OUTPUT,
    county_features,
)

write_feature_collection(
    TOWNSHIPS_OUTPUT,
    township_features,
)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
print("Taiwan administrative processing complete.")
print()
print(f"Provinces: {len(province_features)}")
print(f"Counties:  {len(county_features)}")
print(f"Townships: {len(township_features)}")
print()
print("Outputs:")
print(f"  {PROVINCES_OUTPUT.relative_to(ROOT)}")
print(f"  {COUNTIES_OUTPUT.relative_to(ROOT)}")
print(f"  {TOWNSHIPS_OUTPUT.relative_to(ROOT)}")