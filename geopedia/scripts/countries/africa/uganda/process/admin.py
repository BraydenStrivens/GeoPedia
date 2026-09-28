"""
Processes Uganda's administrative-boundary GeoJSON into canonical GeoPedia
admin datasets.

The source already contains stable administrative pcodes and complete parent
hierarchy information, so no spatial parent matching is required.

Administrative levels:
- ADM1 -> Regions
- ADM2 -> Districts
- ADM3 -> Counties
- ADM4 -> Sub-counties

Canonical output properties:
- Regions:
    region_id, region
- Districts:
    district_id, district, region_id, region
- Counties:
    county_id, county, district_id, district, region_id, region
- Sub-counties:
    sub_county_id, sub_county, county_id, county,
    district_id, district, region_id, region

Input:
    data/raw/countries/uganda/uga_admin_boundaries.geojson/
        uga_admin1.geojson
        uga_admin2.geojson
        uga_admin3.geojson
        uga_admin4.geojson

Output:
    data/intermediate/countries/uganda/admin/
        regions.geojson
        districts.geojson
        counties.geojson
        sub-counties.geojson

Run from the GeoPedia project root:
    python scripts/countries/uganda/process/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.validation import make_valid


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "uganda"
    / "uga_admin_boundaries.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "uganda"
    / "admin"
)

EXPECTED_COUNTS = {
    "regions": 4,
    "districts": 135,
    "counties": 203,
    "sub-counties": 1520,
}


def load_geojson(path: Path) -> dict[str, Any]:
    """Loads and validates a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} is missing a valid features array."
        )

    return data


def require_string(
    properties: dict[str, Any],
    key: str,
    *,
    feature_description: str,
) -> str:
    """Returns a required non-empty string property."""

    value = properties.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{feature_description} has invalid {key}: {value!r}"
        )

    return value.strip()


def validate_geometry(
    feature: dict[str, Any],
    *,
    feature_description: str,
) -> dict[str, Any]:
    """
    Validates and, when necessary, repairs a feature's polygon geometry.

    Source geometries are expected to be Polygon or MultiPolygon. Invalid
    geometries are repaired with Shapely's make_valid before being written to
    the canonical intermediate dataset.
    """

    geometry_data = feature.get("geometry")

    if not isinstance(geometry_data, dict):
        raise ValueError(
            f"{feature_description} is missing valid geometry."
        )

    geometry_type = geometry_data.get("type")

    if geometry_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(
            f"{feature_description} has unexpected geometry type "
            f"{geometry_type!r}."
        )

    coordinates = geometry_data.get("coordinates")

    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError(
            f"{feature_description} has empty geometry coordinates."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"{feature_description} has empty geometry."
        )

    if not geometry.is_valid:
        geometry = make_valid(geometry)

        if geometry.is_empty:
            raise ValueError(
                f"{feature_description} became empty during geometry repair."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"{feature_description} remains invalid after geometry repair."
            )

        if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(
                f"{feature_description} became unexpected geometry type "
                f"{geometry.geom_type!r} during geometry repair."
            )

        print(
            f"Repaired invalid geometry: {feature_description}"
        )

    return mapping(geometry)
  

def make_feature(
    geometry: dict[str, Any],
    properties: dict[str, str],
) -> dict[str, Any]:
    """Creates a canonical GeoPedia GeoJSON feature."""

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry,
    }


def process_regions(
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """Converts Uganda ADM1 features into canonical region features."""

    output: list[dict[str, Any]] = []

    for feature in source["features"]:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM1 feature is missing a valid properties object."
            )

        region_id = require_string(
            properties,
            "adm1_pcode",
            feature_description="ADM1 feature",
        )
        region = require_string(
            properties,
            "adm1_name",
            feature_description=f"Region {region_id}",
        )

        geometry = validate_geometry(
            feature,
            feature_description=f"Region {region_id}",
        )

        output.append(
            make_feature(
                geometry,
                {
                    "region_id": region_id,
                    "region": region,
                },
            )
        )

    return output


def process_districts(
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """Converts Uganda ADM2 features into canonical district features."""

    output: list[dict[str, Any]] = []

    for feature in source["features"]:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM2 feature is missing a valid properties object."
            )

        district_id = require_string(
            properties,
            "adm2_pcode",
            feature_description="ADM2 feature",
        )
        district = require_string(
            properties,
            "adm2_name",
            feature_description=f"District {district_id}",
        )
        region_id = require_string(
            properties,
            "adm1_pcode",
            feature_description=f"District {district_id}",
        )
        region = require_string(
            properties,
            "adm1_name",
            feature_description=f"District {district_id}",
        )

        geometry = validate_geometry(
            feature,
            feature_description=f"District {district_id}",
        )

        output.append(
            make_feature(
                geometry,
                {
                    "district_id": district_id,
                    "district": district,
                    "region_id": region_id,
                    "region": region,
                },
            )
        )

    return output


def process_counties(
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """Converts Uganda ADM3 features into canonical county features."""

    output: list[dict[str, Any]] = []

    for feature in source["features"]:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM3 feature is missing a valid properties object."
            )

        county_id = require_string(
            properties,
            "adm3_pcode",
            feature_description="ADM3 feature",
        )
        county = require_string(
            properties,
            "adm3_name",
            feature_description=f"County {county_id}",
        )
        district_id = require_string(
            properties,
            "adm2_pcode",
            feature_description=f"County {county_id}",
        )
        district = require_string(
            properties,
            "adm2_name",
            feature_description=f"County {county_id}",
        )
        region_id = require_string(
            properties,
            "adm1_pcode",
            feature_description=f"County {county_id}",
        )
        region = require_string(
            properties,
            "adm1_name",
            feature_description=f"County {county_id}",
        )

        geometry = validate_geometry(
            feature,
            feature_description=f"County {county_id}",
        )

        output.append(
            make_feature(
                geometry,
                {
                    "county_id": county_id,
                    "county": county,
                    "district_id": district_id,
                    "district": district,
                    "region_id": region_id,
                    "region": region,
                },
            )
        )

    return output


def process_sub_counties(
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """Converts Uganda ADM4 features into canonical sub-county features."""

    output: list[dict[str, Any]] = []

    for feature in source["features"]:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM4 feature is missing a valid properties object."
            )

        sub_county_id = require_string(
            properties,
            "adm4_pcode",
            feature_description="ADM4 feature",
        )
        sub_county = require_string(
            properties,
            "adm4_name",
            feature_description=f"Sub-county {sub_county_id}",
        )
        county_id = require_string(
            properties,
            "adm3_pcode",
            feature_description=f"Sub-county {sub_county_id}",
        )
        county = require_string(
            properties,
            "adm3_name",
            feature_description=f"Sub-county {sub_county_id}",
        )
        district_id = require_string(
            properties,
            "adm2_pcode",
            feature_description=f"Sub-county {sub_county_id}",
        )
        district = require_string(
            properties,
            "adm2_name",
            feature_description=f"Sub-county {sub_county_id}",
        )
        region_id = require_string(
            properties,
            "adm1_pcode",
            feature_description=f"Sub-county {sub_county_id}",
        )
        region = require_string(
            properties,
            "adm1_name",
            feature_description=f"Sub-county {sub_county_id}",
        )

        geometry = validate_geometry(
            feature,
            feature_description=f"Sub-county {sub_county_id}",
        )

        output.append(
            make_feature(
                geometry,
                {
                    "sub_county_id": sub_county_id,
                    "sub_county": sub_county,
                    "county_id": county_id,
                    "county": county,
                    "district_id": district_id,
                    "district": district,
                    "region_id": region_id,
                    "region": region,
                },
            )
        )

    return output


def validate_unique_ids(
    features: list[dict[str, Any]],
    id_property: str,
    dataset_name: str,
) -> None:
    """Ensures every canonical feature has a unique stable ID."""

    seen: set[str] = set()

    for feature in features:
        value = feature["properties"][id_property]

        if value in seen:
            raise ValueError(
                f"Duplicate {id_property} in {dataset_name}: {value!r}"
            )

        seen.add(value)


def validate_parent_reference(
    features: list[dict[str, Any]],
    parent_id_property: str,
    parent_name_property: str,
    valid_parents: dict[str, str],
    dataset_name: str,
) -> None:
    """
    Ensures every stored parent ID exists and its accompanying name agrees
    with the canonical parent dataset.
    """

    for feature in features:
        properties = feature["properties"]

        parent_id = properties[parent_id_property]
        parent_name = properties[parent_name_property]

        expected_name = valid_parents.get(parent_id)

        if expected_name is None:
            raise ValueError(
                f"{dataset_name} references unknown "
                f"{parent_id_property} {parent_id!r}."
            )

        if parent_name != expected_name:
            raise ValueError(
                f"{dataset_name} has inconsistent parent data for "
                f"{parent_id!r}: {parent_name!r} != {expected_name!r}."
            )


def build_name_lookup(
    features: list[dict[str, Any]],
    id_property: str,
    name_property: str,
) -> dict[str, str]:
    """Builds an ID-to-name lookup from a canonical feature collection."""

    return {
        feature["properties"][id_property]:
            feature["properties"][name_property]
        for feature in features
    }


def validate_count(
    features: list[dict[str, Any]],
    dataset_name: str,
) -> None:
    """Checks a processed dataset against its expected feature count."""

    expected = EXPECTED_COUNTS[dataset_name]
    actual = len(features)

    if actual != expected:
        raise ValueError(
            f"Unexpected {dataset_name} feature count: "
            f"{actual} (expected {expected})."
        )


def write_geojson(
    filename: str,
    features: list[dict[str, Any]],
) -> Path:
    """Writes a canonical GeoJSON FeatureCollection."""

    path = OUTPUT_DIR / filename

    output = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    return path


def main() -> None:
    """Processes and validates all four Uganda administrative quiz levels."""

    adm1 = load_geojson(RAW_DIR / "uga_admin1.geojson")
    adm2 = load_geojson(RAW_DIR / "uga_admin2.geojson")
    adm3 = load_geojson(RAW_DIR / "uga_admin3.geojson")
    adm4 = load_geojson(RAW_DIR / "uga_admin4.geojson")

    regions = process_regions(adm1)
    districts = process_districts(adm2)
    counties = process_counties(adm3)
    sub_counties = process_sub_counties(adm4)

    validate_count(regions, "regions")
    validate_count(districts, "districts")
    validate_count(counties, "counties")
    validate_count(sub_counties, "sub-counties")

    validate_unique_ids(
        regions,
        "region_id",
        "regions",
    )
    validate_unique_ids(
        districts,
        "district_id",
        "districts",
    )
    validate_unique_ids(
        counties,
        "county_id",
        "counties",
    )
    validate_unique_ids(
        sub_counties,
        "sub_county_id",
        "sub-counties",
    )

    region_lookup = build_name_lookup(
        regions,
        "region_id",
        "region",
    )
    district_lookup = build_name_lookup(
        districts,
        "district_id",
        "district",
    )
    county_lookup = build_name_lookup(
        counties,
        "county_id",
        "county",
    )

    validate_parent_reference(
        districts,
        "region_id",
        "region",
        region_lookup,
        "Districts",
    )

    validate_parent_reference(
        counties,
        "district_id",
        "district",
        district_lookup,
        "Counties",
    )
    validate_parent_reference(
        counties,
        "region_id",
        "region",
        region_lookup,
        "Counties",
    )

    validate_parent_reference(
        sub_counties,
        "county_id",
        "county",
        county_lookup,
        "Sub-counties",
    )
    validate_parent_reference(
        sub_counties,
        "district_id",
        "district",
        district_lookup,
        "Sub-counties",
    )
    validate_parent_reference(
        sub_counties,
        "region_id",
        "region",
        region_lookup,
        "Sub-counties",
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = [
        (
            "Regions",
            write_geojson("regions.geojson", regions),
            regions,
        ),
        (
            "Districts",
            write_geojson("districts.geojson", districts),
            districts,
        ),
        (
            "Counties",
            write_geojson("counties.geojson", counties),
            counties,
        ),
        (
            "Sub-counties",
            write_geojson("sub-counties.geojson", sub_counties),
            sub_counties,
        ),
    ]

    print("Uganda administrative processing complete.")
    print()

    for label, path, features in outputs:
        print(
            f"{label:<14} "
            f"{len(features):>4} features | "
            f"{path.stat().st_size / 1_000_000:.2f} MB"
        )

    print()
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()