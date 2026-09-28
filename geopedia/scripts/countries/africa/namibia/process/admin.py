"""
Processes Namibia's administrative-boundary GeoJSON into canonical GeoPedia
admin datasets.

The source already contains the complete ADM1 -> ADM2 hierarchy, so parent
relationships are preserved directly rather than derived spatially.

One known source constituency geometry, Naminus (Luderitz) (NA0405), contains
a self-intersection. Invalid source geometries are repaired with Shapely's
make_valid before canonical output is written.

Administrative levels:
- ADM1 -> Regions
- ADM2 -> Constituencies

Canonical output properties:
- Regions:
    region_id, region
- Constituencies:
    constituency_id, constituency, region_id, region

Input:
    data/raw/countries/namibia/nam_admin_boundaries.geojson/
        nam_admin1.geojson
        nam_admin2.geojson

Output:
    data/intermediate/countries/namibia/admin/
        regions.geojson
        constituencies.geojson

Run from the GeoPedia project root:
    python scripts/countries/namibia/process/admin.py
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
    / "namibia"
    / "nam_admin_boundaries.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "namibia"
    / "admin"
)

EXPECTED_COUNTS = {
    "regions": 14,
    "constituencies": 107,
}


def load_geojson(path: Path) -> dict[str, Any]:
    """Loads and validates a source GeoJSON FeatureCollection."""

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
    """Returns a required non-empty source string property."""

    value = properties.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{feature_description} has invalid {key}: {value!r}"
        )

    return value.strip()


def prepare_geometry(
    geometry_data: dict[str, Any],
    *,
    feature_description: str,
) -> dict[str, Any]:
    """
    Validates a source geometry and repairs it with make_valid when necessary.

    Repairs are logged so source-data problems remain visible during
    regeneration rather than being silently corrected.
    """

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"{feature_description} has empty geometry."
        )

    if not geometry.is_valid:
        print(
            f"Repairing invalid geometry: "
            f"{feature_description}"
        )

        geometry = make_valid(geometry)

        if geometry.is_empty:
            raise ValueError(
                f"{feature_description} became empty after make_valid."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"{feature_description} remains invalid after make_valid."
            )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{feature_description} has unsupported geometry type "
            f"{geometry.geom_type!r} after validation/repair."
        )

    return mapping(geometry)


def process_regions(
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """Builds canonical Namibia region features."""

    features: list[dict[str, Any]] = []

    for source_feature in source["features"]:
        properties = source_feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM1 feature is missing valid properties."
            )

        region_id = require_string(
            properties,
            "adm1_pcode",
            feature_description="ADM1 feature",
        )

        region = require_string(
            properties,
            "adm1_name",
            feature_description=f"ADM1 {region_id}",
        )

        geometry_data = source_feature.get("geometry")

        if not isinstance(geometry_data, dict):
            raise ValueError(
                f"ADM1 {region_id} ({region!r}) "
                "is missing valid geometry."
            )

        geometry = prepare_geometry(
            geometry_data,
            feature_description=(
                f"ADM1 {region_id} ({region})"
            ),
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "region_id": region_id,
                    "region": region,
                },
                "geometry": geometry,
            }
        )

    return features


def process_constituencies(
    source: dict[str, Any],
    regions_by_id: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Builds canonical constituency features while validating their embedded
    ADM1 hierarchy against the processed region dataset.
    """

    features: list[dict[str, Any]] = []

    for source_feature in source["features"]:
        properties = source_feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "ADM2 feature is missing valid properties."
            )

        constituency_id = require_string(
            properties,
            "adm2_pcode",
            feature_description="ADM2 feature",
        )

        constituency = require_string(
            properties,
            "adm2_name",
            feature_description=f"ADM2 {constituency_id}",
        )

        region_id = require_string(
            properties,
            "adm1_pcode",
            feature_description=(
                f"ADM2 {constituency_id} ({constituency})"
            ),
        )

        region = require_string(
            properties,
            "adm1_name",
            feature_description=(
                f"ADM2 {constituency_id} ({constituency})"
            ),
        )

        expected_region = regions_by_id.get(region_id)

        if expected_region is None:
            raise ValueError(
                f"ADM2 {constituency_id} ({constituency!r}) "
                f"references unknown region {region_id!r}."
            )

        if region != expected_region:
            raise ValueError(
                f"ADM2 {constituency_id} ({constituency!r}) "
                f"has region name {region!r}, but {region_id!r} "
                f"maps to {expected_region!r}."
            )

        geometry_data = source_feature.get("geometry")

        if not isinstance(geometry_data, dict):
            raise ValueError(
                f"ADM2 {constituency_id} ({constituency!r}) "
                "is missing valid geometry."
            )

        geometry = prepare_geometry(
            geometry_data,
            feature_description=(
                f"ADM2 {constituency_id} ({constituency})"
            ),
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "constituency_id": constituency_id,
                    "constituency": constituency,
                    "region_id": region_id,
                    "region": region,
                },
                "geometry": geometry,
            }
        )

    return features


def validate_dataset(
    features: list[dict[str, Any]],
    dataset_name: str,
    id_property: str,
) -> None:
    """Validates canonical feature count and stable-ID uniqueness."""

    expected_count = EXPECTED_COUNTS[dataset_name]
    actual_count = len(features)

    if actual_count != expected_count:
        raise ValueError(
            f"Unexpected {dataset_name} feature count: "
            f"{actual_count} (expected {expected_count})."
        )

    ids = [
        feature["properties"][id_property]
        for feature in features
    ]

    if len(ids) != len(set(ids)):
        raise ValueError(
            f"{dataset_name} contains duplicate "
            f"{id_property} values."
        )


def write_geojson(
    filename: str,
    features: list[dict[str, Any]],
) -> Path:
    """Writes a compact canonical GeoJSON FeatureCollection."""

    path = OUTPUT_DIR / filename

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

    return path


def main() -> None:
    """Processes Namibia's regions and constituencies."""

    print("Loading Namibia administrative source data...")

    adm1_source = load_geojson(
        RAW_DIR / "nam_admin1.geojson"
    )

    adm2_source = load_geojson(
        RAW_DIR / "nam_admin2.geojson"
    )

    print()
    print("Processing ADM1 regions...")

    region_features = process_regions(
        adm1_source
    )

    validate_dataset(
        region_features,
        "regions",
        "region_id",
    )

    regions_by_id = {
        feature["properties"]["region_id"]:
        feature["properties"]["region"]
        for feature in region_features
    }

    print("Processing ADM2 constituencies...")

    constituency_features = process_constituencies(
        adm2_source,
        regions_by_id,
    )

    validate_dataset(
        constituency_features,
        "constituencies",
        "constituency_id",
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    region_path = write_geojson(
        "regions.geojson",
        region_features,
    )

    constituency_path = write_geojson(
        "constituencies.geojson",
        constituency_features,
    )

    print()
    print("Namibia administrative processing complete.")
    print()

    print(
        f"{'Regions':<16} "
        f"{len(region_features):>4,} features | "
        f"{region_path.stat().st_size / 1_000_000:>6.2f} MB"
    )

    print(
        f"{'Constituencies':<16} "
        f"{len(constituency_features):>4,} features | "
        f"{constituency_path.stat().st_size / 1_000_000:>6.2f} MB"
    )

    print()
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()