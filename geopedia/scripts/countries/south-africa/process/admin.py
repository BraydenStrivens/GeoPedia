"""
Process South Africa's administrative boundaries for GeoPedia.

The source contains four administrative levels with their parent hierarchy
embedded directly in the feature properties:

    ADM1 -> Provinces
    ADM2 -> Districts
    ADM3 -> Municipalities
    ADM4 -> Wards

Source:
    data/raw/countries/south-africa/zaf_admin_boundaries.geojson/
        zaf_admin1.geojson
        zaf_admin2.geojson
        zaf_admin3.geojson
        zaf_admin4.geojson

Outputs:
    data/intermediate/countries/south-africa/admin/provinces.geojson
    data/intermediate/countries/south-africa/admin/districts.geojson
    data/intermediate/countries/south-africa/admin/municipalities.geojson
    data/intermediate/countries/south-africa/admin/wards.geojson

Runtime properties:
    Provinces:
        province_id
        province

    Districts:
        district_id
        district
        province_id
        province

    Municipalities:
        municipality_id
        municipality
        district_id
        district
        province_id
        province

    Wards:
        ward_id
        ward
        ward_number
        municipality_id
        municipality
        district_id
        district
        province_id
        province

Ward names are formatted as:
    Ward XXX, Municipality

For example:
    Ward 001, Makhado

The original geometries are preserved here. A separate simplification step
prepares the smaller runtime GeoJSON files used by the application.

Run:
    python scripts/countries/south-africa/process/admin.py
"""

import json
from pathlib import Path

from shapely.geometry import shape


SOURCE_ROOT = Path(
    "data/raw/countries/south-africa/zaf_admin_boundaries.geojson"
)

OUTPUT_ROOT = Path(
    "data/intermediate/countries/south-africa/admin"
)

PROVINCES_SOURCE = SOURCE_ROOT / "zaf_admin1.geojson"
DISTRICTS_SOURCE = SOURCE_ROOT / "zaf_admin2.geojson"
MUNICIPALITIES_SOURCE = SOURCE_ROOT / "zaf_admin3.geojson"
WARDS_SOURCE = SOURCE_ROOT / "zaf_admin4.geojson"

EXPECTED_PROVINCE_COUNT = 9
EXPECTED_DISTRICT_COUNT = 52
EXPECTED_MUNICIPALITY_COUNT = 213
EXPECTED_WARD_COUNT = 4392


def load_feature_collection(path: Path) -> dict:
    """Load and validate a source GeoJSON FeatureCollection."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def require_string(
    properties: dict,
    property_name: str,
    context: str,
) -> str:
    """Return a required non-empty string property."""

    value = properties.get(property_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{context}: invalid {property_name}: {value!r}"
        )

    return value.strip()


def validate_geometry(
    feature: dict,
    context: str,
) -> None:
    """Validate that a feature has a usable polygonal geometry."""

    geometry_data = feature.get("geometry")

    if geometry_data is None:
        raise ValueError(
            f"{context}: missing geometry."
        )

    geometry_type = geometry_data.get("type")

    if geometry_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{context}: unsupported geometry type "
            f"{geometry_type!r}."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"{context}: geometry is empty."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{context}: geometry is invalid."
        )


def validate_unique_ids(
    features: list[dict],
    id_property: str,
    label: str,
) -> None:
    """Validate that a canonical ID is unique across a feature set."""

    seen = set()

    for feature in features:
        properties = feature["properties"]
        feature_id = properties[id_property]

        if feature_id in seen:
            raise ValueError(
                f"Duplicate {label} ID: {feature_id}"
            )

        seen.add(feature_id)


def build_provinces(
    source_features: list[dict],
) -> list[dict]:
    """Build canonical province features."""

    if len(source_features) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            "Unexpected province count: "
            f"expected {EXPECTED_PROVINCE_COUNT}, "
            f"found {len(source_features)}."
        )

    output = []

    for index, feature in enumerate(source_features):
        context = f"Province source feature {index}"

        validate_geometry(feature, context)

        properties = feature.get("properties") or {}

        province_id = require_string(
            properties,
            "adm1_pcode",
            context,
        )
        province = require_string(
            properties,
            "adm1_name",
            context,
        )

        output.append(
            {
                "type": "Feature",
                "properties": {
                    "province_id": province_id,
                    "province": province,
                },
                "geometry": feature["geometry"],
            }
        )

    validate_unique_ids(
        output,
        "province_id",
        "province",
    )

    output.sort(
        key=lambda feature: feature["properties"]["province"]
    )

    return output


def build_districts(
    source_features: list[dict],
) -> list[dict]:
    """Build canonical district features with province hierarchy."""

    if len(source_features) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected district count: "
            f"expected {EXPECTED_DISTRICT_COUNT}, "
            f"found {len(source_features)}."
        )

    output = []

    for index, feature in enumerate(source_features):
        context = f"District source feature {index}"

        validate_geometry(feature, context)

        properties = feature.get("properties") or {}

        district_id = require_string(
            properties,
            "adm2_pcode",
            context,
        )
        district = require_string(
            properties,
            "adm2_name",
            context,
        )
        province_id = require_string(
            properties,
            "adm1_pcode",
            context,
        )
        province = require_string(
            properties,
            "adm1_name",
            context,
        )

        output.append(
            {
                "type": "Feature",
                "properties": {
                    "district_id": district_id,
                    "district": district,
                    "province_id": province_id,
                    "province": province,
                },
                "geometry": feature["geometry"],
            }
        )

    validate_unique_ids(
        output,
        "district_id",
        "district",
    )

    output.sort(
        key=lambda feature: (
            feature["properties"]["province"],
            feature["properties"]["district"],
        )
    )

    return output


def build_municipalities(
    source_features: list[dict],
) -> list[dict]:
    """Build canonical municipality features with parent hierarchy."""

    if len(source_features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            "Unexpected municipality count: "
            f"expected {EXPECTED_MUNICIPALITY_COUNT}, "
            f"found {len(source_features)}."
        )

    output = []

    for index, feature in enumerate(source_features):
        context = f"Municipality source feature {index}"

        validate_geometry(feature, context)

        properties = feature.get("properties") or {}

        municipality_id = require_string(
            properties,
            "adm3_pcode",
            context,
        )
        municipality = require_string(
            properties,
            "adm3_name",
            context,
        )
        district_id = require_string(
            properties,
            "adm2_pcode",
            context,
        )
        district = require_string(
            properties,
            "adm2_name",
            context,
        )
        province_id = require_string(
            properties,
            "adm1_pcode",
            context,
        )
        province = require_string(
            properties,
            "adm1_name",
            context,
        )

        output.append(
            {
                "type": "Feature",
                "properties": {
                    "municipality_id": municipality_id,
                    "municipality": municipality,
                    "district_id": district_id,
                    "district": district,
                    "province_id": province_id,
                    "province": province,
                },
                "geometry": feature["geometry"],
            }
        )

    validate_unique_ids(
        output,
        "municipality_id",
        "municipality",
    )

    output.sort(
        key=lambda feature: (
            feature["properties"]["province"],
            feature["properties"]["district"],
            feature["properties"]["municipality"],
        )
    )

    return output


def build_wards(
    source_features: list[dict],
) -> list[dict]:
    """Build canonical ward features with their full parent hierarchy."""

    if len(source_features) != EXPECTED_WARD_COUNT:
        raise ValueError(
            "Unexpected ward count: "
            f"expected {EXPECTED_WARD_COUNT}, "
            f"found {len(source_features)}."
        )

    output = []

    for index, feature in enumerate(source_features):
        context = f"Ward source feature {index}"

        validate_geometry(feature, context)

        properties = feature.get("properties") or {}

        ward_id = require_string(
            properties,
            "adm4_pcode",
            context,
        )
        ward_number = require_string(
            properties,
            "adm4_name",
            context,
        )
        municipality_id = require_string(
            properties,
            "adm3_pcode",
            context,
        )
        municipality = require_string(
            properties,
            "adm3_name",
            context,
        )
        district_id = require_string(
            properties,
            "adm2_pcode",
            context,
        )
        district = require_string(
            properties,
            "adm2_name",
            context,
        )
        province_id = require_string(
            properties,
            "adm1_pcode",
            context,
        )
        province = require_string(
            properties,
            "adm1_name",
            context,
        )

        ward = (
            f"Ward {ward_number}, {municipality}"
        )

        output.append(
            {
                "type": "Feature",
                "properties": {
                    "ward_id": ward_id,
                    "ward": ward,
                    "ward_number": ward_number,
                    "municipality_id": municipality_id,
                    "municipality": municipality,
                    "district_id": district_id,
                    "district": district,
                    "province_id": province_id,
                    "province": province,
                },
                "geometry": feature["geometry"],
            }
        )

    validate_unique_ids(
        output,
        "ward_id",
        "ward",
    )

    output.sort(
        key=lambda feature: (
            feature["properties"]["province"],
            feature["properties"]["district"],
            feature["properties"]["municipality"],
            feature["properties"]["ward_number"],
        )
    )

    return output


def build_lookup(
    features: list[dict],
    id_property: str,
    name_property: str,
) -> dict[str, str]:
    """Build an ID-to-name lookup from canonical features."""

    return {
        feature["properties"][id_property]:
            feature["properties"][name_property]
        for feature in features
    }


def validate_parent(
    child_features: list[dict],
    parent_lookup: dict[str, str],
    parent_id_property: str,
    parent_name_property: str,
    child_label: str,
    parent_label: str,
) -> None:
    """Validate embedded child hierarchy against a canonical parent level."""

    for feature in child_features:
        properties = feature["properties"]

        parent_id = properties[parent_id_property]
        parent_name = properties[parent_name_property]

        expected_name = parent_lookup.get(parent_id)

        if expected_name is None:
            raise ValueError(
                f"{child_label} references unknown "
                f"{parent_label} ID {parent_id!r}."
            )

        if parent_name != expected_name:
            raise ValueError(
                f"{child_label} hierarchy mismatch for "
                f"{parent_label} {parent_id!r}: "
                f"{parent_name!r} != {expected_name!r}."
            )


def write_geojson(
    path: Path,
    features: list[dict],
) -> None:
    """Write a canonical intermediate GeoJSON FeatureCollection."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def print_output(
    label: str,
    path: Path,
    feature_count: int,
) -> None:
    """Print a compact output summary."""

    size_mb = path.stat().st_size / 1_000_000

    print(
        f"{label:<16} "
        f"{feature_count:>5} features | "
        f"{size_mb:>7.2f} MB"
    )


def main() -> None:
    """Process and validate South Africa's administrative hierarchy."""

    print("Processing South Africa administrative boundaries...")
    print()

    province_source = load_feature_collection(
        PROVINCES_SOURCE
    )
    district_source = load_feature_collection(
        DISTRICTS_SOURCE
    )
    municipality_source = load_feature_collection(
        MUNICIPALITIES_SOURCE
    )
    ward_source = load_feature_collection(
        WARDS_SOURCE
    )

    provinces = build_provinces(
        province_source["features"]
    )
    districts = build_districts(
        district_source["features"]
    )
    municipalities = build_municipalities(
        municipality_source["features"]
    )
    wards = build_wards(
        ward_source["features"]
    )

    province_lookup = build_lookup(
        provinces,
        "province_id",
        "province",
    )
    district_lookup = build_lookup(
        districts,
        "district_id",
        "district",
    )
    municipality_lookup = build_lookup(
        municipalities,
        "municipality_id",
        "municipality",
    )

    validate_parent(
        districts,
        province_lookup,
        "province_id",
        "province",
        "District",
        "province",
    )

    validate_parent(
        municipalities,
        province_lookup,
        "province_id",
        "province",
        "Municipality",
        "province",
    )

    validate_parent(
        municipalities,
        district_lookup,
        "district_id",
        "district",
        "Municipality",
        "district",
    )

    validate_parent(
        wards,
        province_lookup,
        "province_id",
        "province",
        "Ward",
        "province",
    )

    validate_parent(
        wards,
        district_lookup,
        "district_id",
        "district",
        "Ward",
        "district",
    )

    validate_parent(
        wards,
        municipality_lookup,
        "municipality_id",
        "municipality",
        "Ward",
        "municipality",
    )

    province_path = OUTPUT_ROOT / "provinces.geojson"
    district_path = OUTPUT_ROOT / "districts.geojson"
    municipality_path = OUTPUT_ROOT / "municipalities.geojson"
    ward_path = OUTPUT_ROOT / "wards.geojson"

    write_geojson(
        province_path,
        provinces,
    )
    write_geojson(
        district_path,
        districts,
    )
    write_geojson(
        municipality_path,
        municipalities,
    )
    write_geojson(
        ward_path,
        wards,
    )

    print_output(
        "Provinces",
        province_path,
        len(provinces),
    )
    print_output(
        "Districts",
        district_path,
        len(districts),
    )
    print_output(
        "Municipalities",
        municipality_path,
        len(municipalities),
    )
    print_output(
        "Wards",
        ward_path,
        len(wards),
    )

    print()
    print("Hierarchy validation passed.")
    print()
    print(f"Output: {OUTPUT_ROOT}")
    print()
    print("South Africa administrative processing complete.")


if __name__ == "__main__":
    main()