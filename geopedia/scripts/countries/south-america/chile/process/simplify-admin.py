"""
Simplify Chile administrative GeoJSON for GeoPedia runtime use.

Input
-----
data/intermediate/countries/chile/admin/

    regions.geojson
    provinces.geojson
    communes.geojson

Output
------
public/data/countries/chile/admin/

    regions.geojson
    provinces.geojson
    communes.geojson

The intermediate files contain GeoPedia's canonical administrative properties
and full source geometry. This script simplifies those geometries for efficient
browser rendering while preserving the canonical properties.

Simplification is performed with GeoPandas/Shapely using a metric CRS so the
tolerances are specified in meters.

Different administrative levels use different tolerances because smaller
features require more geometric detail than larger features.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "chile"
    / "geojson"
)


# ---------------------------------------------------------------------------
# Simplification configuration
# ---------------------------------------------------------------------------

LEVELS = {
    "regions": {
        "tolerance": 0.02,
        "expected_count": 16,
        "id_property": "region_id",
    },
    "provinces": {
        "tolerance": 0.015,
        "expected_count": 56,
        "id_property": "province_id",
    },
    "communes": {
        "tolerance": 0.01,
        "expected_count": 345,
        "id_property": "commune_id",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def file_size_mb(path: Path) -> float:
    """Return a file's size in megabytes."""
    return path.stat().st_size / (1024 * 1024)


def validate_ids(
    frame: gpd.GeoDataFrame,
    id_property: str,
    expected_count: int,
    level: str,
) -> None:
    """Validate feature count, non-null IDs, and ID uniqueness."""
    if len(frame) != expected_count:
        raise ValueError(
            f"{level}: expected {expected_count} features, "
            f"got {len(frame)}"
        )

    if frame[id_property].isna().any():
        raise ValueError(
            f"{level}: found null values in {id_property}"
        )

    duplicate_ids = frame.loc[
        frame[id_property].duplicated(),
        id_property,
    ].tolist()

    if duplicate_ids:
        raise ValueError(
            f"{level}: duplicate IDs found: {duplicate_ids}"
        )


def validate_geometry(
    frame: gpd.GeoDataFrame,
    level: str,
) -> None:
    """Validate that all output geometries exist and are non-empty."""
    null_count = int(frame.geometry.isna().sum())
    empty_count = int(frame.geometry.is_empty.sum())

    if null_count:
        raise ValueError(
            f"{level}: {null_count} null geometries after simplification"
        )

    if empty_count:
        raise ValueError(
            f"{level}: {empty_count} empty geometries after simplification"
        )


def write_compact_geojson(
    frame: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    """Write a GeoDataFrame as compact UTF-8 GeoJSON."""
    geojson = json.loads(frame.to_json(drop_id=True))

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


# ---------------------------------------------------------------------------
# Simplification
# ---------------------------------------------------------------------------

def simplify_level(
    level: str,
    tolerance: float,
    expected_count: int,
    id_property: str,
) -> None:
    """Simplify one administrative level and write its runtime GeoJSON."""
    input_path = INPUT_DIR / f"{level}.geojson"
    output_path = OUTPUT_DIR / f"{level}.geojson"

    print()
    print(f"========== {level.upper()} ==========")
    print(f"Input:     {input_path}")
    print(f"Input size: {file_size_mb(input_path):.2f} MB")
    print(f"Tolerance: {tolerance:g}°")\
  
    frame = gpd.read_file(input_path)

    validate_ids(
        frame,
        id_property,
        expected_count,
        level,
    )

    if frame.crs is None:
        raise ValueError(
            f"{level}: input GeoJSON has no CRS"
        )

    output_frame = frame.copy()

    output_frame.geometry = output_frame.geometry.simplify(
        tolerance=tolerance,
        preserve_topology=True,
    )

    validate_ids(
        output_frame,
        id_property,
        expected_count,
        level,
    )

    validate_geometry(output_frame, level)

    write_compact_geojson(
        output_frame,
        output_path,
    )

    print(f"Output size: {file_size_mb(output_path):.2f} MB")
    print(f"Features:    {len(output_frame)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Simplify all Chile administrative levels."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Simplifying Chile administrative GeoJSON...")

    for level, config in LEVELS.items():
        simplify_level(
            level=level,
            tolerance=config["tolerance"],
            expected_count=config["expected_count"],
            id_property=config["id_property"],
        )

    print()
    print("Chile administrative simplification complete.")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()