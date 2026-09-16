"""
Process Chile administrative boundaries into GeoPedia's canonical GeoJSON format.

Source
------
data/raw/countries/chile/chl_admin_boundaries.geojson/

    chl_admin1.geojson -> 16 regions
    chl_admin2.geojson -> 56 provinces
    chl_admin3.geojson -> 345 communes

Output
------
data/processed/countries/chile/admin/

    regions.geojson
    provinces.geojson
    communes.geojson

Canonical properties
--------------------
regions.geojson:
    region_id
    region

provinces.geojson:
    province_id
    province
    region_id
    region

communes.geojson:
    commune_id
    commune
    province_id
    province
    region_id
    region

The source PCODE values are preserved as GeoPedia's stable administrative IDs.

A small number of known source naming errors or missing accents are corrected
during processing. Parent names in lower administrative levels are resolved
from the processed parent dictionaries rather than copied directly from the
lower-level source features. This ensures that name corrections remain
consistent throughout the hierarchy.

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
    / "chile"
    / "chl_admin_boundaries.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "admin"
)

ADM1_PATH = RAW_DIR / "chl_admin1.geojson"
ADM2_PATH = RAW_DIR / "chl_admin2.geojson"
ADM3_PATH = RAW_DIR / "chl_admin3.geojson"

REGIONS_OUTPUT_PATH = OUTPUT_DIR / "regions.geojson"
PROVINCES_OUTPUT_PATH = OUTPUT_DIR / "provinces.geojson"
COMMUNES_OUTPUT_PATH = OUTPUT_DIR / "communes.geojson"


# ---------------------------------------------------------------------------
# Known source corrections
# ---------------------------------------------------------------------------

REGION_NAME_CORRECTIONS = {
    # Correct the missing accent in Ibáñez.
    "CL11": "Región de Aysén del Gral. Ibáñez del Campo",
}

PROVINCE_NAME_CORRECTIONS = {
    # Correct missing accents in the source names.
    "CL102": "Chiloé",
    "CL124": "Última Esperanza",
}

COMMUNE_NAME_CORRECTIONS = {
    # The source incorrectly labels CL01401 as Tocopilla.
    # CL01401 is Pozo Almonte, in Tamarugal Province.
    "CL01401": "Pozo Almonte",

    # Correct missing accents in the source names.
    "CL08206": "Los Álamos",
    "CL08301": "Los Ángeles",
}


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


def feature_collection(features: list[dict[str, Any]]) -> dict[str, Any]:
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

        source_name = require_string(
            properties,
            "adm1_name",
            f"Region {region_id}",
        )

        region = REGION_NAME_CORRECTIONS.get(region_id, source_name)

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


def process_provinces(
    source: dict[str, Any],
    region_names: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """
    Process ADM2 features into canonical province features.

    Region names are resolved through the processed region lookup so that
    corrections made at ADM1 propagate consistently into ADM2.

    Returns both the processed features and a province ID -> province name
    lookup used when processing communes.
    """
    features: list[dict[str, Any]] = []
    province_names: dict[str, str] = {}

    for source_feature in source["features"]:
        properties = source_feature["properties"]

        province_id = require_string(
            properties,
            "adm2_pcode",
            "ADM2 feature",
        )

        source_name = require_string(
            properties,
            "adm2_name",
            f"Province {province_id}",
        )

        region_id = require_string(
            properties,
            "adm1_pcode",
            f"Province {province_id}",
        )

        if region_id not in region_names:
            raise ValueError(
                f"Province {province_id} references unknown "
                f"region ID {region_id}"
            )

        province = PROVINCE_NAME_CORRECTIONS.get(
            province_id,
            source_name,
        )

        if province_id in province_names:
            raise ValueError(f"Duplicate province ID: {province_id}")

        province_names[province_id] = province

        features.append(
            make_feature(
                geometry=source_feature["geometry"],
                properties={
                    "province_id": province_id,
                    "province": province,
                    "region_id": region_id,
                    "region": region_names[region_id],
                },
            )
        )

    validate_unique_ids(features, "province_id", "province")

    return features, province_names


def process_communes(
    source: dict[str, Any],
    region_names: dict[str, str],
    province_names: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Process ADM3 features into canonical commune features.

    Province and region names are resolved through their processed parent
    dictionaries so corrections at higher levels propagate consistently.
    """
    features: list[dict[str, Any]] = []

    for source_feature in source["features"]:
        properties = source_feature["properties"]

        commune_id = require_string(
            properties,
            "adm3_pcode",
            "ADM3 feature",
        )

        source_name = require_string(
            properties,
            "adm3_name",
            f"Commune {commune_id}",
        )

        province_id = require_string(
            properties,
            "adm2_pcode",
            f"Commune {commune_id}",
        )

        region_id = require_string(
            properties,
            "adm1_pcode",
            f"Commune {commune_id}",
        )

        if province_id not in province_names:
            raise ValueError(
                f"Commune {commune_id} references unknown "
                f"province ID {province_id}"
            )

        if region_id not in region_names:
            raise ValueError(
                f"Commune {commune_id} references unknown "
                f"region ID {region_id}"
            )

        commune = COMMUNE_NAME_CORRECTIONS.get(
            commune_id,
            source_name,
        )

        features.append(
            make_feature(
                geometry=source_feature["geometry"],
                properties={
                    "commune_id": commune_id,
                    "commune": commune,
                    "province_id": province_id,
                    "province": province_names[province_id],
                    "region_id": region_id,
                    "region": region_names[region_id],
                },
            )
        )

    validate_unique_ids(features, "commune_id", "commune")

    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Process all three Chile administrative levels."""
    print("Loading Chile administrative source data...")

    adm1 = load_geojson(ADM1_PATH)
    adm2 = load_geojson(ADM2_PATH)
    adm3 = load_geojson(ADM3_PATH)

    print("Processing regions...")
    regions, region_names = process_regions(adm1)

    print("Processing provinces...")
    provinces, province_names = process_provinces(
        adm2,
        region_names,
    )

    print("Processing communes...")
    communes = process_communes(
        adm3,
        region_names,
        province_names,
    )

    # These counts are expected from the inspected source dataset.
    expected_counts = {
        "regions": 16,
        "provinces": 56,
        "communes": 345,
    }

    actual_counts = {
        "regions": len(regions),
        "provinces": len(provinces),
        "communes": len(communes),
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
        PROVINCES_OUTPUT_PATH,
        feature_collection(provinces),
    )

    write_geojson(
        COMMUNES_OUTPUT_PATH,
        feature_collection(communes),
    )

    print()
    print("Chile administrative processing complete.")
    print(f"  Regions:   {len(regions)}")
    print(f"  Provinces: {len(provinces)}")
    print(f"  Communes:  {len(communes)}")
    print()
    print("Output:")
    print(f"  {REGIONS_OUTPUT_PATH}")
    print(f"  {PROVINCES_OUTPUT_PATH}")
    print(f"  {COMMUNES_OUTPUT_PATH}")


if __name__ == "__main__":
    main()