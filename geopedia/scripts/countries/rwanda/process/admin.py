"""
Processes Rwanda's administrative-boundary GeoJSON into canonical GeoPedia
admin datasets with complete parent hierarchy information.

The geoBoundaries source files contain stable IDs and subdivision names but do
not contain parent administrative relationships. Immediate parents are
therefore assigned spatially, and higher-level ancestry is inherited from the
matched parent.

Administrative levels:
- ADM1 -> Intara (Provinces)
- ADM2 -> Uturere (Districts)
- ADM3 -> Imirenge (Sectors)
- ADM4 -> Utugali (Cells)
- ADM5 -> Imidugudu (Villages)

Canonical output properties:
- Provinces:
    province_id, province
- Districts:
    district_id, district, province_id, province
- Sectors:
    sector_id, sector, district_id, district,
    province_id, province
- Cells:
    cell_id, cell, sector_id, sector,
    district_id, district, province_id, province
- Villages:
    village_id, village, cell_id, cell,
    sector_id, sector, district_id, district,
    province_id, province

Input:
    data/raw/countries/rwanda/
        geoBoundaries-RWA-ADM1.geojson
        geoBoundaries-RWA-ADM2.geojson
        geoBoundaries-RWA-ADM3.geojson
        geoBoundaries-RWA-ADM4.geojson
        geoBoundaries-RWA-ADM5.geojson

Output:
    data/intermediate/countries/rwanda/admin/
        provinces.geojson
        districts.geojson
        sectors.geojson
        cells.geojson
        villages.geojson

Run from the GeoPedia project root:
    python scripts/countries/rwanda/process/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import shape
from shapely.strtree import STRtree


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "rwanda"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "rwanda"
    / "admin"
)

EXPECTED_COUNTS = {
    "provinces": 5,
    "districts": 30,
    "sectors": 416,
    "cells": 2148,
    "villages": 14815,
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


def validate_source_feature(
    feature: dict[str, Any],
    expected_level: str,
) -> tuple[str, str, Any]:
    """
    Validates a geoBoundaries feature and returns its stable ID, name, and
    Shapely geometry.
    """

    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            f"{expected_level} feature is missing valid properties."
        )

    shape_id = require_string(
        properties,
        "shapeID",
        feature_description=f"{expected_level} feature",
    )

    shape_name = require_string(
        properties,
        "shapeName",
        feature_description=f"{expected_level} {shape_id}",
    )

    shape_type = require_string(
        properties,
        "shapeType",
        feature_description=f"{expected_level} {shape_id}",
    )

    if shape_type != expected_level:
        raise ValueError(
            f"{expected_level} {shape_id} has shapeType "
            f"{shape_type!r}."
        )

    geometry_data = feature.get("geometry")

    if not isinstance(geometry_data, dict):
        raise ValueError(
            f"{expected_level} {shape_id} is missing valid geometry."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"{expected_level} {shape_id} has empty geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{expected_level} {shape_id} has invalid geometry."
        )

    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(
            f"{expected_level} {shape_id} has unexpected geometry type "
            f"{geometry.geom_type!r}."
        )

    return shape_id, shape_name, geometry


def build_source_records(
    source: dict[str, Any],
    expected_level: str,
) -> list[dict[str, Any]]:
    """Converts source features into validated working records."""

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for feature in source["features"]:
        shape_id, shape_name, geometry = validate_source_feature(
            feature,
            expected_level,
        )

        if shape_id in seen_ids:
            raise ValueError(
                f"Duplicate shapeID in {expected_level}: {shape_id!r}"
            )

        seen_ids.add(shape_id)

        records.append(
            {
                "id": shape_id,
                "name": shape_name,
                "geometry": geometry,
                "geometry_json": feature["geometry"],
            }
        )

    return records


def find_parent(
    child_geometry: Any,
    parent_records: list[dict[str, Any]],
    parent_tree: STRtree,
) -> dict[str, Any]:
    """
    Finds the best immediate parent for one child geometry.

    A representative point is used first because administrative child
    polygons should normally have an interior point inside their parent.
    If that does not produce exactly one parent, candidate parents are ranked
    by polygon intersection area.
    """

    point = child_geometry.representative_point()

    point_indices = parent_tree.query(
        point,
        predicate="intersects",
    )

    if len(point_indices) == 1:
        return parent_records[int(point_indices[0])]

    candidate_indices = parent_tree.query(
        child_geometry,
        predicate="intersects",
    )

    if len(candidate_indices) == 0:
        raise ValueError(
            "Could not find any intersecting parent geometry."
        )

    best_parent: dict[str, Any] | None = None
    best_overlap = -1.0

    for index in candidate_indices:
        parent = parent_records[int(index)]

        overlap = child_geometry.intersection(
            parent["geometry"]
        ).area

        if overlap > best_overlap:
            best_overlap = overlap
            best_parent = parent

    if best_parent is None or best_overlap <= 0:
        raise ValueError(
            "Could not determine a parent with positive overlap."
        )

    return best_parent


def assign_parents(
    children: list[dict[str, Any]],
    parents: list[dict[str, Any]],
    child_label: str,
    parent_label: str,
) -> None:
    """Assigns an immediate spatial parent to every child record."""

    parent_tree = STRtree(
        [parent["geometry"] for parent in parents]
    )

    for index, child in enumerate(children, start=1):
        try:
            child["parent"] = find_parent(
                child["geometry"],
                parents,
                parent_tree,
            )
        except Exception as error:
            raise ValueError(
                f"Could not assign {parent_label} parent for "
                f"{child_label} {child['id']} ({child['name']!r})."
            ) from error

        if index % 1000 == 0:
            print(
                f"  Assigned {index:,} / {len(children):,} "
                f"{child_label.lower()} features..."
            )


def make_feature(
    record: dict[str, Any],
    properties: dict[str, str],
) -> dict[str, Any]:
    """Creates a canonical GeoPedia feature from a working source record."""

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": record["geometry_json"],
    }


def build_provinces(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Builds canonical province features."""

    return [
        make_feature(
            record,
            {
                "province_id": record["id"],
                "province": record["name"],
            },
        )
        for record in records
    ]


def build_districts(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Builds canonical district features with province hierarchy."""

    features = []

    for record in records:
        province = record["parent"]

        features.append(
            make_feature(
                record,
                {
                    "district_id": record["id"],
                    "district": record["name"],
                    "province_id": province["id"],
                    "province": province["name"],
                },
            )
        )

    return features


def build_sectors(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Builds canonical sector features with district/province hierarchy."""

    features = []

    for record in records:
        district = record["parent"]
        province = district["parent"]

        features.append(
            make_feature(
                record,
                {
                    "sector_id": record["id"],
                    "sector": record["name"],
                    "district_id": district["id"],
                    "district": district["name"],
                    "province_id": province["id"],
                    "province": province["name"],
                },
            )
        )

    return features


def build_cells(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Builds canonical cell features with complete parent hierarchy."""

    features = []

    for record in records:
        sector = record["parent"]
        district = sector["parent"]
        province = district["parent"]

        features.append(
            make_feature(
                record,
                {
                    "cell_id": record["id"],
                    "cell": record["name"],
                    "sector_id": sector["id"],
                    "sector": sector["name"],
                    "district_id": district["id"],
                    "district": district["name"],
                    "province_id": province["id"],
                    "province": province["name"],
                },
            )
        )

    return features


def build_villages(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Builds canonical village features with complete parent hierarchy."""

    features = []

    for record in records:
        cell = record["parent"]
        sector = cell["parent"]
        district = sector["parent"]
        province = district["parent"]

        features.append(
            make_feature(
                record,
                {
                    "village_id": record["id"],
                    "village": record["name"],
                    "cell_id": cell["id"],
                    "cell": cell["name"],
                    "sector_id": sector["id"],
                    "sector": sector["name"],
                    "district_id": district["id"],
                    "district": district["name"],
                    "province_id": province["id"],
                    "province": province["name"],
                },
            )
        )

    return features


def validate_count(
    features: list[dict[str, Any]],
    dataset_name: str,
) -> None:
    """Checks a canonical dataset against its expected feature count."""

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
    """Processes all five Rwanda administrative levels."""

    print("Loading Rwanda administrative source data...")

    adm1 = build_source_records(
        load_geojson(RAW_DIR / "geoBoundaries-RWA-ADM1.geojson"),
        "ADM1",
    )
    adm2 = build_source_records(
        load_geojson(RAW_DIR / "geoBoundaries-RWA-ADM2.geojson"),
        "ADM2",
    )
    adm3 = build_source_records(
        load_geojson(RAW_DIR / "geoBoundaries-RWA-ADM3.geojson"),
        "ADM3",
    )
    adm4 = build_source_records(
        load_geojson(RAW_DIR / "geoBoundaries-RWA-ADM4.geojson"),
        "ADM4",
    )
    adm5 = build_source_records(
        load_geojson(RAW_DIR / "geoBoundaries-RWA-ADM5.geojson"),
        "ADM5",
    )

    print()
    print("Assigning spatial hierarchy...")

    print("ADM2 districts -> ADM1 provinces")
    assign_parents(
        adm2,
        adm1,
        "District",
        "province",
    )

    print("ADM3 sectors -> ADM2 districts")
    assign_parents(
        adm3,
        adm2,
        "Sector",
        "district",
    )

    print("ADM4 cells -> ADM3 sectors")
    assign_parents(
        adm4,
        adm3,
        "Cell",
        "sector",
    )

    print("ADM5 villages -> ADM4 cells")
    assign_parents(
        adm5,
        adm4,
        "Village",
        "cell",
    )

    print()
    print("Building canonical datasets...")

    provinces = build_provinces(adm1)
    districts = build_districts(adm2)
    sectors = build_sectors(adm3)
    cells = build_cells(adm4)
    villages = build_villages(adm5)

    validate_count(provinces, "provinces")
    validate_count(districts, "districts")
    validate_count(sectors, "sectors")
    validate_count(cells, "cells")
    validate_count(villages, "villages")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = [
        (
            "Provinces",
            write_geojson("provinces.geojson", provinces),
            provinces,
        ),
        (
            "Districts",
            write_geojson("districts.geojson", districts),
            districts,
        ),
        (
            "Sectors",
            write_geojson("sectors.geojson", sectors),
            sectors,
        ),
        (
            "Cells",
            write_geojson("cells.geojson", cells),
            cells,
        ),
        (
            "Villages",
            write_geojson("villages.geojson", villages),
            villages,
        ),
    ]

    print()
    print("Rwanda administrative processing complete.")
    print()

    for label, path, features in outputs:
        print(
            f"{label:<12} "
            f"{len(features):>6,} features | "
            f"{path.stat().st_size / 1_000_000:>7.2f} MB"
        )

    print()
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()