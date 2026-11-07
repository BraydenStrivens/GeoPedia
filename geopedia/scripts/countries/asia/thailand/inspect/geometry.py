"""
Inspect Thailand's administrative boundary geometry and simplification options.

Streams ADM1–ADM3 GeoJSON features to measure coordinate counts, polygon
complexity, geometry validity, small polygon parts, and potential size
reductions from topology-preserving simplification.

Inputs:
    data/raw/countries/thailand/tha_admin_boundaries.geojson/
        tha_admin1.geojson
        tha_admin2.geojson
        tha_admin3.geojson

Output:
    Console report only. No files are modified.

Usage:
    python scripts/countries/asia/thailand/inspect/geometry.py

Dependencies:
    pip install shapely ijson
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import median

import ijson
from shapely.geometry import mapping, shape


PROJECT_ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = (
    PROJECT_ROOT
    / "data/raw/countries/thailand/tha_admin_boundaries.geojson"
)

FILES = {
    "ADM1": RAW_DIR / "tha_admin1.geojson",
    "ADM2": RAW_DIR / "tha_admin2.geojson",
    "ADM3": RAW_DIR / "tha_admin3.geojson",
}

# Tolerances are measured in geographic degrees, not percentages.
# Approximately 0.0001 degrees of latitude equals 11 meters.
TOLERANCES = [
    0.0001,
    0.0005,
    0.001,
    0.002,
    0.005,
]

# Small polygon-part thresholds in approximate square kilometers.
SMALL_PART_THRESHOLDS = [
    0.01,
    0.1,
    1.0,
]

# Simplification benchmarks use a deterministic sample of features.
# Every feature is still inspected for its original geometry statistics.
SAMPLE_INTERVALS = {
    "ADM1": 1,
    "ADM2": 5,
    "ADM3": 25,
}


def stream_features(path: Path):
    """Yield GeoJSON features without loading the entire file."""

    with path.open("rb") as file:
        yield from ijson.items(
            file,
            "features.item",
            use_float=True,
        )


def polygon_parts(geometry):
    """Return the Polygon components of a geometry."""

    if geometry.geom_type == "Polygon":
        return [geometry]

    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)

    return []


def coordinate_count(geometry) -> int:
    """Count polygon ring coordinates, including closing vertices."""

    count = 0

    for polygon in polygon_parts(geometry):
        count += len(polygon.exterior.coords)

        for interior in polygon.interiors:
            count += len(interior.coords)

    return count


def serialized_size(geometry) -> int:
    """Measure compact GeoJSON geometry size in bytes."""

    return len(
        json.dumps(
            mapping(geometry),
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )


def inspect_level(level: str, path: Path) -> None:
    print()
    print("=" * 80)
    print(f"{level}: {path.name}")
    print("=" * 80)

    file_size = path.stat().st_size

    feature_count = 0
    invalid_count = 0
    empty_count = 0

    geometry_types = Counter()
    coordinate_counts = []

    total_coordinates = 0
    total_parts = 0

    small_parts = {
        threshold: 0
        for threshold in SMALL_PART_THRESHOLDS
    }

    sampled_features = 0
    sampled_original_bytes = 0

    sampled_simplified_bytes = {
        tolerance: 0
        for tolerance in TOLERANCES
    }

    sampled_simplified_coordinates = {
        tolerance: 0
        for tolerance in TOLERANCES
    }

    sampled_invalid = {
        tolerance: 0
        for tolerance in TOLERANCES
    }

    sample_interval = SAMPLE_INTERVALS[level]

    for index, feature in enumerate(stream_features(path)):
        feature_count += 1

        geometry_data = feature.get("geometry")

        if geometry_data is None:
            empty_count += 1
            continue

        geometry = shape(geometry_data)

        geometry_types[geometry.geom_type] += 1

        if geometry.is_empty:
            empty_count += 1
            continue

        if not geometry.is_valid:
            invalid_count += 1

        coordinates = coordinate_count(geometry)

        coordinate_counts.append(coordinates)
        total_coordinates += coordinates

        parts = polygon_parts(geometry)
        total_parts += len(parts)

        for polygon in parts:
            # This is an approximate conversion suitable for inspection.
            # It is not an equal-area projection.
            latitude = polygon.centroid.y

            square_km_per_degree = (
                111.32 * 111.32
                * abs(__import__("math").cos(
                    __import__("math").radians(latitude)
                ))
            )

            area_km2 = polygon.area * square_km_per_degree

            for threshold in SMALL_PART_THRESHOLDS:
                if area_km2 < threshold:
                    small_parts[threshold] += 1

        if index % sample_interval != 0:
            continue

        sampled_features += 1

        sampled_original_bytes += serialized_size(
            geometry
        )

        for tolerance in TOLERANCES:
            simplified = geometry.simplify(
                tolerance,
                preserve_topology=True,
            )

            sampled_simplified_bytes[tolerance] += (
                serialized_size(simplified)
            )

            sampled_simplified_coordinates[tolerance] += (
                coordinate_count(simplified)
            )

            if not simplified.is_valid:
                sampled_invalid[tolerance] += 1

        if feature_count % 500 == 0:
            print(
                f"  Inspected {feature_count:,} features...",
                flush=True,
            )

    print()
    print("Original geometry")
    print("-" * 80)

    print(f"Features:            {feature_count:,}")
    print(f"File size:           {file_size / 1_000_000:,.2f} MB")
    print(f"Invalid geometries:  {invalid_count:,}")
    print(f"Empty geometries:    {empty_count:,}")
    print(f"Polygon parts:       {total_parts:,}")
    print(f"Total coordinates:   {total_coordinates:,}")

    if coordinate_counts:
        print(
            f"Median coordinates:  {median(coordinate_counts):,.0f}"
        )
        print(
            f"Maximum coordinates: {max(coordinate_counts):,}"
        )

    print()
    print("Geometry types:")

    for geometry_type, count in sorted(geometry_types.items()):
        print(f"  {geometry_type}: {count:,}")

    print()
    print("Small polygon parts (approximate):")

    for threshold, count in small_parts.items():
        print(
            f"  Under {threshold:g} km²: {count:,}"
        )

    print()
    print(
        f"Simplification benchmarks "
        f"({sampled_features:,} sampled features)"
    )
    print("-" * 80)

    print(
        f"{'Tolerance':<12}"
        f"{'Coord reduction':>18}"
        f"{'Size reduction':>18}"
        f"{'Invalid':>12}"
    )

    sampled_original_coordinates = sum(
        coordinate_counts[::sample_interval]
    )

    for tolerance in TOLERANCES:
        simplified_coordinates = (
            sampled_simplified_coordinates[tolerance]
        )

        simplified_bytes = (
            sampled_simplified_bytes[tolerance]
        )

        coordinate_reduction = (
            100 * (
                1
                - simplified_coordinates
                / sampled_original_coordinates
            )
            if sampled_original_coordinates
            else 0
        )

        size_reduction = (
            100 * (
                1
                - simplified_bytes
                / sampled_original_bytes
            )
            if sampled_original_bytes
            else 0
        )

        print(
            f"{tolerance:<12g}"
            f"{coordinate_reduction:>17.1f}%"
            f"{size_reduction:>17.1f}%"
            f"{sampled_invalid[tolerance]:>12,}"
        )

    print()
    print(
        "Note: Simplification is applied independently to each feature. "
        "Shared boundaries may develop gaps or overlaps."
    )


def main() -> None:
    print("Thailand administrative geometry inspection")
    print(f"Source: {RAW_DIR.relative_to(PROJECT_ROOT)}")

    for level, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(path)

        inspect_level(level, path)

    print()
    print("Inspection complete.")


if __name__ == "__main__":
    main()