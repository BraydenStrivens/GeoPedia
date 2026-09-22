"""
Process Senegal administrative boundaries into GeoPedia's canonical GeoJSON format.

Source
------
data/raw/countries/senegal/sen_admin_boundaries.geojson/

    sen_admin1.geojson -> 14 regions
    sen_admin2.geojson -> 46 departments
    sen_admin3.geojson -> 125 arrondissements

Output
------
data/intermediate/countries/senegal/admin/

    regions.geojson
    departments.geojson
    arrondissements.geojson

Canonical properties
--------------------
regions.geojson:
    region_id
    region

departments.geojson:
    department_id
    department
    region_id
    region

arrondissements.geojson:
    arrondissement_id
    arrondissement
    department_id
    department
    region_id
    region

The source PCODE values are preserved as GeoPedia's stable administrative IDs.

Parent names in lower administrative levels are resolved from the processed
parent dictionaries rather than copied directly from the lower-level source
features. This keeps the administrative hierarchy internally consistent.

This script does not simplify geometry. Geometry simplification is handled
separately by process/simplify-admin.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "senegal"
    / "sen_admin_boundaries.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "senegal"
    / "admin"
)

ADM1_PATH = RAW_DIR / "sen_admin1.geojson"
ADM2_PATH = RAW_DIR / "sen_admin2.geojson"
ADM3_PATH = RAW_DIR / "sen_admin3.geojson"

REGIONS_OUTPUT_PATH = OUTPUT_DIR / "regions.geojson"
DEPARTMENTS_OUTPUT_PATH = OUTPUT_DIR / "departments.geojson"
ARRONDISSEMENTS_OUTPUT_PATH = OUTPUT_DIR / "arrondissements.geojson"


# ---------------------------------------------------------------------------
# GeoJSON helpers
# ---------------------------------------------------------------------------


def load_geojson(path: Path) -> dict[str, Any]:
    """Load a GeoJSON file from disk."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_geojson(path: Path, data: dict[str, Any]) -> None:
    """Write compact UTF-8 GeoJSON while preserving non-ASCII characters."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def feature_collection(
    features: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def make_feature(
    geometry: dict[str, Any],
    properties: dict[str, str],
) -> dict[str, Any]:
    """Create a canonical GeoJSON feature."""
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry,
    }


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def require_string(
    properties: dict[str, Any],
    key: str,
    context: str,
) -> str:
    """Return a required non-empty string property or raise an error."""
    value = properties.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{context}: expected non-empty string property {key!r}, "
            f"got {value!r}"
        )

    return value.strip()


def validate_unique_ids(
    features: list[dict[str, Any]],
    id_property: str,
    label: str,
) -> None:
    """Verify that every processed feature has a unique ID."""
    seen: set[str] = set()

    for feature in features:
        feature_id = feature["properties"][id_property]

        if feature_id in seen:
            raise ValueError(
                f"Duplicate {label} ID in processed data: {feature_id}"
            )

        seen.add(feature_id)


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def process_regions(
    source: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """
    Process ADM1 features into canonical region features.

    Returns both the processed features and a region ID -> region name lookup
    used when processing lower administrative levels.
    """
    features: list[dict[str, Any]] = []
    region_names: dict[str, str] = {}

    for source_feature in source["features"]:
        properties = source_feature["properties"]

        region_id = require_string(
            properties,
            "adm1_pcode",
            "ADM1 feature",
        )

        region = require_string(
            properties,
            "adm1_name",
            f"Region {region_id}",
        )

        if region_id in region_names:
            raise ValueError(f"Duplicate region ID: {region_id}")

        region_names[region_id] = region

        features.append(
            make_feature(
                geometry=source_feature["geometry"],
                properties={
                    "region_id": region_id,
                    "region": region,
                },
            )
        )

    validate_unique_ids(features, "region_id", "region")

    return features, region_names


def process_departments(
    source: dict[str, Any],
    region_names: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """
    Process ADM2 features into canonical department features.

    Region names are resolved through the processed region lookup so every
    department uses the canonical name belonging to its parent region.

    Returns both the processed features and a department ID -> department name
    lookup used when processing arrondissements.
    """
    features: list[dict[str, Any]] = []
    department_names: dict[str, str] = {}

    for source_feature in source["features"]:
        properties = source_feature["properties"]

        department_id = require_string(
            properties,
            "adm2_pcode",
            "ADM2 feature",
        )

        department = require_string(
            properties,
            "adm2_name",
            f"Department {department_id}",
        )

        region_id = require_string(
            properties,
            "adm1_pcode",
            f"Department {department_id}",
        )

        if region_id not in region_names:
            raise ValueError(
                f"Department {department_id} references unknown "
                f"region ID {region_id}"
            )

        if department_id in department_names:
            raise ValueError(
                f"Duplicate department ID: {department_id}"
            )

        department_names[department_id] = department

        features.append(
            make_feature(
                geometry=source_feature["geometry"],
                properties={
                    "department_id": department_id,
                    "department": department,
                    "region_id": region_id,
                    "region": region_names[region_id],
                },
            )
        )

    validate_unique_ids(
        features,
        "department_id",
        "department",
    )

    return features, department_names


def process_arrondissements(
    source: dict[str, Any],
    region_names: dict[str, str],
    department_names: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Process ADM3 features into canonical arrondissement features.

    Department and region names are resolved through their processed parent
    dictionaries so lower-level features use the canonical hierarchy.
    """
    features: list[dict[str, Any]] = []

    for source_feature in source["features"]:
        properties = source_feature["properties"]

        arrondissement_id = require_string(
            properties,
            "adm3_pcode",
            "ADM3 feature",
        )

        arrondissement = require_string(
            properties,
            "adm3_name",
            f"Arrondissement {arrondissement_id}",
        )

        department_id = require_string(
            properties,
            "adm2_pcode",
            f"Arrondissement {arrondissement_id}",
        )

        region_id = require_string(
            properties,
            "adm1_pcode",
            f"Arrondissement {arrondissement_id}",
        )

        if department_id not in department_names:
            raise ValueError(
                f"Arrondissement {arrondissement_id} references unknown "
                f"department ID {department_id}"
            )

        if region_id not in region_names:
            raise ValueError(
                f"Arrondissement {arrondissement_id} references unknown "
                f"region ID {region_id}"
            )

        features.append(
            make_feature(
                geometry=source_feature["geometry"],
                properties={
                    "arrondissement_id": arrondissement_id,
                    "arrondissement": arrondissement,
                    "department_id": department_id,
                    "department": department_names[department_id],
                    "region_id": region_id,
                    "region": region_names[region_id],
                },
            )
        )

    validate_unique_ids(
        features,
        "arrondissement_id",
        "arrondissement",
    )

    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Process all three Senegal administrative levels."""
    print("Loading Senegal administrative source data...")

    adm1 = load_geojson(ADM1_PATH)
    adm2 = load_geojson(ADM2_PATH)
    adm3 = load_geojson(ADM3_PATH)

    print("Processing regions...")
    regions, region_names = process_regions(adm1)

    print("Processing departments...")
    departments, department_names = process_departments(
        adm2,
        region_names,
    )

    print("Processing arrondissements...")
    arrondissements = process_arrondissements(
        adm3,
        region_names,
        department_names,
    )

    # These counts are expected from the inspected source dataset.
    expected_counts = {
        "regions": 14,
        "departments": 46,
        "arrondissements": 125,
    }

    actual_counts = {
        "regions": len(regions),
        "departments": len(departments),
        "arrondissements": len(arrondissements),
    }

    for level, expected in expected_counts.items():
        actual = actual_counts[level]

        if actual != expected:
            raise ValueError(
                f"Unexpected {level} count: expected {expected}, "
                f"got {actual}"
            )

    print("Writing processed GeoJSON...")

    write_geojson(
        REGIONS_OUTPUT_PATH,
        feature_collection(regions),
    )

    write_geojson(
        DEPARTMENTS_OUTPUT_PATH,
        feature_collection(departments),
    )

    write_geojson(
        ARRONDISSEMENTS_OUTPUT_PATH,
        feature_collection(arrondissements),
    )

    print()
    print("Senegal administrative processing complete.")
    print(f"  Regions:          {len(regions)}")
    print(f"  Departments:      {len(departments)}")
    print(f"  Arrondissements:  {len(arrondissements)}")
    print()
    print("Output:")
    print(f"  {REGIONS_OUTPUT_PATH}")
    print(f"  {DEPARTMENTS_OUTPUT_PATH}")
    print(f"  {ARRONDISSEMENTS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()