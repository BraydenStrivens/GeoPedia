"""
Generate Philippines telephone area-code boundary datasets for GeoPedia.

This script derives two geography datasets from GeoPedia's processed
Philippines administrative boundaries:

    area-codes.geojson
    area-code-prefixes.geojson

Inputs
------
    data/intermediate/countries/philippines/provinces.geojson

    data/intermediate/countries/philippines/
        municipalities-cities.geojson

Outputs
-------
Intermediate:

    data/intermediate/countries/philippines/
        area-codes.geojson
        area-code-prefixes.geojson

Public:

    public/data/countries/philippines/geojson/
        area-codes.geojson
        area-code-prefixes.geojson

Area-code geometry
------------------
Most Philippines landline area-code boundaries can be constructed by assigning
whole GeoPedia province-level features to an area code and dissolving features
that share the same code.

Two exceptions require Admin 3 geometry:

Cavite:
    PH0402103  Bacoor City        -> 02
    remainder of PH04021 Cavite   -> 046

Laguna:
    PH0403425  City of San Pedro  -> 02
    remainder of PH04034 Laguna   -> 049

The 02 feature is therefore the union of:

    Metropolitan Manila
    Rizal
    Bacoor City
    City of San Pedro

Province assignments are keyed exclusively by stable province IDs. Province
names are included only as comments for readability and are never used to join
datasets.

Domestic dialing format
-----------------------
Area codes are stored in their domestic dialing form, including the leading 0:

    2  -> 02
    32 -> 032
    49 -> 049

Each area-code feature also receives its one-digit dialing prefix:

    02  -> 02
    032 -> 03
    049 -> 04
    088 -> 08

The 02 area is special: 02 is itself the complete area code. There are no
021, 022, etc. area-code groups represented by this dataset.

Regions
-------
Each dissolved area-code feature stores every canonical GeoPedia region
intersected by its source administrative features:

    "region": ["Central Visayas"]

or, when an area code spans regions:

    "region": ["Bicol Region", "Calabarzon", "Mimaropa Region"]

This allows the full area-code quiz to group questions by region.

Prefix geometry
---------------
The area-code features are dissolved again by prefix_1 to produce seven
prefix features:

    02
    03
    04
    05
    06
    07
    08

The prefix dataset does not require region properties because the prefix quiz
does not support grouping.

This script does not modify provinces.geojson or
municipalities-cities.geojson.

Requirements
------------
    pip install shapely

Run from the GeoPedia project root:

    python scripts/countries/philippines/process/area-codes.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

PUBLIC_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "philippines"
    / "geojson"
)

PROVINCES_PATH = (
    PUBLIC_DIRECTORY
    / "provinces.geojson"
)

MUNICIPALITIES_CITIES_PATH = (
    PUBLIC_DIRECTORY
    / "municipalities-cities.geojson"
)

AREA_CODES_PATH = (
    PUBLIC_DIRECTORY
    / "area-codes.geojson"
)

PREFIXES_PATH = (
    PUBLIC_DIRECTORY
    / "area-code-prefixes.geojson"
)


# ---------------------------------------------------------------------------
# Special Admin 3 carve-outs
# ---------------------------------------------------------------------------

BACOOR_CITY_ID = "PH0402103"
SAN_PEDRO_CITY_ID = "PH0403425"

CAVITE_ID = "PH04021"
LAGUNA_ID = "PH04034"


# ---------------------------------------------------------------------------
# Province -> area-code assignments
# ---------------------------------------------------------------------------
#
# All assignments use canonical GeoPedia province IDs.
#
# Cavite and Laguna are intentionally omitted because their geometries are
# split using Bacoor City and City of San Pedro.
#
# Province-level units not present in the supplied telephone-area-code list
# are intentionally omitted from this mapping.
# ---------------------------------------------------------------------------

AREA_CODE_BY_PROVINCE_ID: dict[str, str] = {
    # 02
    "PH13039": "02",   # Metropolitan Manila
    "PH04058": "02",   # Rizal

    # 032
    "PH07022": "032",  # Cebu

    # 033
    "PH06079": "033",  # Guimaras
    "PH06030": "033",  # Iloilo

    # 034
    "PH06045": "034",  # Negros Occidental

    # 035
    "PH07046": "035",  # Negros Oriental
    "PH07061": "035",  # Siquijor

    # 036
    "PH06004": "036",  # Aklan
    "PH06006": "036",  # Antique
    "PH06019": "036",  # Capiz

    # 038
    "PH07012": "038",  # Bohol

    # 042
    "PH03077": "042",  # Aurora
    "PH17040": "042",  # Marinduque
    "PH04056": "042",  # Quezon
    "PH17059": "042",  # Romblon

    # 043
    "PH04010": "043",  # Batangas
    "PH17051": "043",  # Occidental Mindoro
    "PH17052": "043",  # Oriental Mindoro

    # 044
    "PH03014": "044",  # Bulacan
    "PH03049": "044",  # Nueva Ecija

    # 045
    "PH03054": "045",  # Pampanga
    "PH03069": "045",  # Tarlac

    # 047
    "PH03008": "047",  # Bataan
    "PH03071": "047",  # Zambales

    # 048
    "PH17053": "048",  # Palawan

    # 052
    "PH05005": "052",  # Albay
    "PH05020": "052",  # Catanduanes

    # 053
    "PH08078": "053",  # Biliran
    "PH08037": "053",  # Leyte
    "PH08064": "053",  # Southern Leyte

    # 054
    "PH05016": "054",  # Camarines Norte
    "PH05017": "054",  # Camarines Sur

    # 055
    "PH08026": "055",  # Eastern Samar
    "PH08048": "055",  # Northern Samar
    "PH08060": "055",  # Samar (Western Samar)

    # 056
    "PH05041": "056",  # Masbate
    "PH05062": "056",  # Sorsogon

    # 062
    "PH19007": "062",  # Basilan
    "PH09073": "062",  # Zamboanga del Sur
    "PH09083": "062",  # Zamboanga Sibugay

    # 063
    "PH10035": "063",  # Lanao del Norte
    "PH19036": "063",  # Lanao del Sur

    # 064
    "PH12047": "064",  # Cotabato
    "PH19087": "064",  # Maguindanao del Norte
    "PH19088": "064",  # Maguindanao del Sur
    "PH12065": "064",  # Sultan Kudarat

    # 065
    "PH09072": "065",  # Zamboanga del Norte

    # 068
    "PH19066": "068",  # Sulu
    "PH19070": "068",  # Tawi-Tawi

    # 072
    "PH01033": "072",  # La Union

    # 074
    "PH14001": "074",  # Abra
    "PH14081": "074",  # Apayao
    "PH14011": "074",  # Benguet
    "PH14027": "074",  # Ifugao
    "PH14032": "074",  # Kalinga
    "PH14044": "074",  # Mountain Province

    # 075
    "PH01055": "075",  # Pangasinan

    # 077
    "PH01028": "077",  # Ilocos Norte
    "PH01029": "077",  # Ilocos Sur

    # 078
    "PH02009": "078",  # Batanes
    "PH02015": "078",  # Cagayan
    "PH02031": "078",  # Isabela
    "PH02050": "078",  # Nueva Vizcaya
    "PH02057": "078",  # Quirino

    # 082
    "PH11024": "082",  # Davao del Sur
    "PH11086": "082",  # Davao Occidental

    # 083
    "PH12080": "083",  # Sarangani
    "PH12063": "083",  # South Cotabato

    # 084
    "PH11023": "084",  # Davao del Norte

    # 085
    "PH16002": "085",  # Agusan del Norte
    "PH16003": "085",  # Agusan del Sur

    # 086
    "PH16085": "086",  # Dinagat Islands
    "PH16067": "086",  # Surigao del Norte
    "PH16068": "086",  # Surigao del Sur

    # 087
    "PH11082": "087",  # Davao de Oro
    "PH11025": "087",  # Davao Oriental

    # 088
    "PH10013": "088",  # Bukidnon
    "PH10018": "088",  # Camiguin
    "PH10042": "088",  # Misamis Occidental
    "PH10043": "088",  # Misamis Oriental
}


# ---------------------------------------------------------------------------
# Expected output values
# ---------------------------------------------------------------------------

EXPECTED_AREA_CODES = {
    "02",
    "032",
    "033",
    "034",
    "035",
    "036",
    "038",
    "042",
    "043",
    "044",
    "045",
    "046",
    "047",
    "048",
    "049",
    "052",
    "053",
    "054",
    "055",
    "056",
    "062",
    "063",
    "064",
    "065",
    "068",
    "072",
    "074",
    "075",
    "077",
    "078",
    "082",
    "083",
    "084",
    "085",
    "086",
    "087",
    "088",
}

EXPECTED_PREFIXES = {
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
}


# ---------------------------------------------------------------------------
# GeoJSON helpers
# ---------------------------------------------------------------------------


def load_feature_collection(
    path: Path,
) -> list[dict[str, Any]]:
    """Load and minimally validate a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required GeoJSON not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if data.get(
        "type"
    ) != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path.name} has a malformed features array."
        )

    return features


def write_feature_collection(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    """Write a compact GeoJSON FeatureCollection."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )


def parse_geometry(
    feature: dict[str, Any],
    *,
    label: str,
) -> BaseGeometry:
    """Parse and validate a polygonal GeoJSON feature geometry."""

    geometry_data = feature.get(
        "geometry"
    )

    if not isinstance(
        geometry_data,
        dict,
    ):
        raise ValueError(
            f"{label} has missing or malformed geometry."
        )

    geometry = shape(
        geometry_data
    )

    if geometry.is_empty:
        raise ValueError(
            f"{label} has empty geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{label} has unexpected geometry type "
            f"{geometry.geom_type!r}."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{label} has invalid geometry."
        )

    return geometry


def make_feature(
    *,
    properties: dict[str, Any],
    geometry: BaseGeometry,
) -> dict[str, Any]:
    """Create a GeoJSON Feature."""

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": mapping(
            geometry
        ),
    }


def file_size_mb(
    path: Path,
) -> float:
    """Return a file's size in MiB."""

    return (
        path.stat().st_size
        / (1024 * 1024)
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def dissolve(
    geometries: list[BaseGeometry],
    *,
    label: str,
) -> BaseGeometry:
    """Union a non-empty collection of polygonal geometries."""

    if not geometries:
        raise ValueError(
            f"No geometries were collected for {label}."
        )

    geometry = unary_union(
        geometries
    )

    if geometry.is_empty:
        raise ValueError(
            f"Dissolved geometry for {label} is empty."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"Dissolved geometry for {label} has unexpected type "
            f"{geometry.geom_type!r}."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Dissolved geometry for {label} is invalid."
        )

    return geometry


def subtract(
    source: BaseGeometry,
    carve_out: BaseGeometry,
    *,
    label: str,
) -> BaseGeometry:
    """Subtract an Admin 3 carve-out from its parent province."""

    result = source.difference(
        carve_out
    )

    if result.is_empty:
        raise ValueError(
            f"Geometry subtraction for {label} produced an empty result."
        )

    if result.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"Geometry subtraction for {label} produced unexpected type "
            f"{result.geom_type!r}."
        )

    if not result.is_valid:
        raise ValueError(
            f"Geometry subtraction for {label} produced invalid geometry."
        )

    return result


# ---------------------------------------------------------------------------
# Property helpers
# ---------------------------------------------------------------------------


def require_properties(
    feature: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    """Return a feature's properties object."""

    properties = feature.get(
        "properties"
    )

    if not isinstance(
        properties,
        dict,
    ):
        raise ValueError(
            f"{label} has malformed properties."
        )

    return properties


def require_string(
    properties: dict[str, Any],
    property_name: str,
    *,
    label: str,
) -> str:
    """Read a required non-empty string property."""

    value = properties.get(
        property_name
    )

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{label} has non-string property {property_name!r}."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{label} has blank property {property_name!r}."
        )

    return value


def prefix_for_area_code(
    area_code: str,
) -> str:
    """Return the domestic one-digit prefix group for an area code."""

    if area_code == "02":
        return "02"

    if len(
        area_code
    ) != 3:
        raise ValueError(
            f"Unexpected area-code format: {area_code!r}"
        )

    if not area_code.startswith(
        "0"
    ):
        raise ValueError(
            f"Area code does not begin with 0: {area_code!r}"
        )

    return area_code[:2]


# ---------------------------------------------------------------------------
# Source indexing
# ---------------------------------------------------------------------------


def index_provinces(
    features: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Index province features by canonical province_id."""

    indexed: dict[
        str,
        dict[str, Any],
    ] = {}

    for feature in features:
        properties = require_properties(
            feature,
            label="Province feature",
        )

        province_id = require_string(
            properties,
            "province_id",
            label="Province feature",
        )

        if province_id in indexed:
            raise ValueError(
                f"Duplicate province_id {province_id!r}."
            )

        indexed[
            province_id
        ] = feature

    return indexed


def index_municipalities_cities(
    features: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Index Admin 3 features by municipality_city_id."""

    indexed: dict[
        str,
        dict[str, Any],
    ] = {}

    for feature in features:
        properties = require_properties(
            feature,
            label="Municipality/city feature",
        )

        feature_id = require_string(
            properties,
            "municipality_city_id",
            label="Municipality/city feature",
        )

        if feature_id in indexed:
            raise ValueError(
                f"Duplicate municipality_city_id {feature_id!r}."
            )

        indexed[
            feature_id
        ] = feature

    return indexed


# ---------------------------------------------------------------------------
# Area-code construction
# ---------------------------------------------------------------------------


def build_area_code_features(
    provinces: dict[str, dict[str, Any]],
    municipalities_cities: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Construct and dissolve the full Philippines area-code dataset."""

    geometries_by_code: dict[
        str,
        list[BaseGeometry],
    ] = {}

    regions_by_code: dict[
        str,
        set[str],
    ] = {}

    def add_piece(
        *,
        area_code: str,
        geometry: BaseGeometry,
        region: str,
    ) -> None:
        geometries_by_code.setdefault(
            area_code,
            [],
        ).append(
            geometry
        )

        regions_by_code.setdefault(
            area_code,
            set(),
        ).add(
            region
        )

    # ------------------------------------------------------------------
    # Whole-province assignments
    # ------------------------------------------------------------------

    for (
        province_id,
        area_code,
    ) in AREA_CODE_BY_PROVINCE_ID.items():
        feature = provinces.get(
            province_id
        )

        if feature is None:
            raise ValueError(
                f"Province {province_id!r} required for area code "
                f"{area_code} was not found."
            )

        properties = require_properties(
            feature,
            label=f"Province {province_id}",
        )

        region = require_string(
            properties,
            "region",
            label=f"Province {province_id}",
        )

        geometry = parse_geometry(
            feature,
            label=f"Province {province_id}",
        )

        add_piece(
            area_code=area_code,
            geometry=geometry,
            region=region,
        )

    # ------------------------------------------------------------------
    # Cavite / Bacoor split
    # ------------------------------------------------------------------

    cavite_feature = provinces.get(
        CAVITE_ID
    )

    if cavite_feature is None:
        raise ValueError(
            f"Cavite province {CAVITE_ID!r} was not found."
        )

    bacoor_feature = municipalities_cities.get(
        BACOOR_CITY_ID
    )

    if bacoor_feature is None:
        raise ValueError(
            f"Bacoor City {BACOOR_CITY_ID!r} was not found."
        )

    cavite_properties = require_properties(
        cavite_feature,
        label="Cavite",
    )

    cavite_region = require_string(
        cavite_properties,
        "region",
        label="Cavite",
    )

    cavite_geometry = parse_geometry(
        cavite_feature,
        label="Cavite",
    )

    bacoor_geometry = parse_geometry(
        bacoor_feature,
        label="Bacoor City",
    )

    cavite_remainder = subtract(
        cavite_geometry,
        bacoor_geometry,
        label="Cavite minus Bacoor City",
    )

    add_piece(
        area_code="02",
        geometry=bacoor_geometry,
        region=cavite_region,
    )

    add_piece(
        area_code="046",
        geometry=cavite_remainder,
        region=cavite_region,
    )

    # ------------------------------------------------------------------
    # Laguna / San Pedro split
    # ------------------------------------------------------------------

    laguna_feature = provinces.get(
        LAGUNA_ID
    )

    if laguna_feature is None:
        raise ValueError(
            f"Laguna province {LAGUNA_ID!r} was not found."
        )

    san_pedro_feature = municipalities_cities.get(
        SAN_PEDRO_CITY_ID
    )

    if san_pedro_feature is None:
        raise ValueError(
            f"City of San Pedro {SAN_PEDRO_CITY_ID!r} was not found."
        )

    laguna_properties = require_properties(
        laguna_feature,
        label="Laguna",
    )

    laguna_region = require_string(
        laguna_properties,
        "region",
        label="Laguna",
    )

    laguna_geometry = parse_geometry(
        laguna_feature,
        label="Laguna",
    )

    san_pedro_geometry = parse_geometry(
        san_pedro_feature,
        label="City of San Pedro",
    )

    laguna_remainder = subtract(
        laguna_geometry,
        san_pedro_geometry,
        label="Laguna minus City of San Pedro",
    )

    add_piece(
        area_code="02",
        geometry=san_pedro_geometry,
        region=laguna_region,
    )

    add_piece(
        area_code="049",
        geometry=laguna_remainder,
        region=laguna_region,
    )

    # ------------------------------------------------------------------
    # Validate codes before dissolving
    # ------------------------------------------------------------------

    actual_codes = set(
        geometries_by_code
    )

    if actual_codes != EXPECTED_AREA_CODES:
        missing = sorted(
            EXPECTED_AREA_CODES
            - actual_codes
        )

        unexpected = sorted(
            actual_codes
            - EXPECTED_AREA_CODES
        )

        raise ValueError(
            "Area-code set mismatch.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    # ------------------------------------------------------------------
    # Dissolve
    # ------------------------------------------------------------------

    output_features: list[
        dict[str, Any]
    ] = []

    for area_code in sorted(
        geometries_by_code
    ):
        geometry = dissolve(
            geometries_by_code[
                area_code
            ],
            label=f"area code {area_code}",
        )

        regions = sorted(
            regions_by_code[
                area_code
            ]
        )

        output_features.append(
            make_feature(
                properties={
                    "area_code": area_code,
                    "prefix_1": prefix_for_area_code(
                        area_code
                    ),
                    "region": regions,
                },
                geometry=geometry,
            )
        )

    return output_features


# ---------------------------------------------------------------------------
# Prefix construction
# ---------------------------------------------------------------------------


def build_prefix_features(
    area_code_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Dissolve area-code features into one-digit prefix groups."""

    geometries_by_prefix: dict[
        str,
        list[BaseGeometry],
    ] = {}

    for feature in area_code_features:
        properties = require_properties(
            feature,
            label="Area-code feature",
        )

        prefix = require_string(
            properties,
            "prefix_1",
            label="Area-code feature",
        )

        geometry = parse_geometry(
            feature,
            label=f"Area-code prefix {prefix}",
        )

        geometries_by_prefix.setdefault(
            prefix,
            [],
        ).append(
            geometry
        )

    actual_prefixes = set(
        geometries_by_prefix
    )

    if actual_prefixes != EXPECTED_PREFIXES:
        missing = sorted(
            EXPECTED_PREFIXES
            - actual_prefixes
        )

        unexpected = sorted(
            actual_prefixes
            - EXPECTED_PREFIXES
        )

        raise ValueError(
            "Prefix set mismatch.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    output_features: list[
        dict[str, Any]
    ] = []

    for prefix in sorted(
        geometries_by_prefix
    ):
        geometry = dissolve(
            geometries_by_prefix[
                prefix
            ],
            label=f"prefix {prefix}",
        )

        output_features.append(
            make_feature(
                properties={
                    "prefix_1": prefix,
                },
                geometry=geometry,
            )
        )

    return output_features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Generating Philippines telephone area-code boundaries..."
    )
    print()

    province_features = load_feature_collection(
        PROVINCES_PATH
    )

    municipality_city_features = load_feature_collection(
        MUNICIPALITIES_CITIES_PATH
    )

    print(
        f"Loaded {len(province_features):,} province-level features."
    )
    print(
        f"Loaded {len(municipality_city_features):,} "
        "municipality/city features."
    )
    print()

    provinces = index_provinces(
        province_features
    )

    municipalities_cities = index_municipalities_cities(
        municipality_city_features
    )

    print(
        "Building area-code geometries..."
    )

    area_code_features = build_area_code_features(
        provinces,
        municipalities_cities,
    )

    if len(
        area_code_features
    ) != len(
        EXPECTED_AREA_CODES
    ):
        raise ValueError(
            f"Expected {len(EXPECTED_AREA_CODES):,} area-code features but "
            f"generated {len(area_code_features):,}."
        )

    write_feature_collection(
        AREA_CODES_PATH,
        area_code_features,
    )

    print(
        f"  Area codes: {len(area_code_features):,}"
    )
    print(
        f"  Size:       "
        f"{file_size_mb(AREA_CODES_PATH):.2f} MB"
    )
    print()

    print(
        "Building one-digit prefix geometries..."
    )

    prefix_features = build_prefix_features(
        area_code_features
    )

    if len(
        prefix_features
    ) != len(
        EXPECTED_PREFIXES
    ):
        raise ValueError(
            f"Expected {len(EXPECTED_PREFIXES):,} prefix features but "
            f"generated {len(prefix_features):,}."
        )

    write_feature_collection(
        PREFIXES_PATH,
        prefix_features,
    )

    print(
        f"  Prefixes: {len(prefix_features):,}"
    )
    print(
        f"  Size:     "
        f"{file_size_mb(PREFIXES_PATH):.2f} MB"
    )
    print()

    print(
        "=" * 78
    )
    print(
        "Philippines telephone area-code processing complete."
    )
    print(
        "=" * 78
    )
    print()
    print(
        f"Area-code features: {len(area_code_features):,}"
    )
    print(
        f"Prefix features:    {len(prefix_features):,}"
    )
    print()
    print(
        "Special geometry handling:"
    )
    print(
        "  02  = Metropolitan Manila + Rizal + Bacoor City + "
        "City of San Pedro"
    )
    print(
        "  046 = Cavite minus Bacoor City"
    )
    print(
        "  049 = Laguna minus City of San Pedro"
    )


if __name__ == "__main__":
    main()