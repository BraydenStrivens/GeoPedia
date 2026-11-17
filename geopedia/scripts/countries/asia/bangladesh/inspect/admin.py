
"""
Inspect Bangladesh's ADM1–ADM4 geoBoundaries datasets.

Inputs:
    data/raw/countries/bangladesh/geoBoundaries-BGD-ADM1.geojson
    data/raw/countries/bangladesh/geoBoundaries-BGD-ADM2.geojson
    data/raw/countries/bangladesh/geoBoundaries-BGD-ADM3.geojson
    data/raw/countries/bangladesh/geoBoundaries-BGD-ADM4.geojson

Reports:
    - Feature counts and geometry types
    - Property names, completeness, and sample values
    - Candidate IDs, names, and parent relationships
    - Duplicate values for identifier/name fields
    - Invalid/empty geometries, polygon parts, and coordinates
    - Geometry simplification benchmarks

Does not modify the source files.

Run:
    python scripts/countries/asia/bangladesh/inspect/admin.py

Dependencies:
    pip install ijson shapely
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import ijson
from shapely.geometry import shape


PROJECT_ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = PROJECT_ROOT / "data/raw/countries/bangladesh"

DATASETS = {
    level: RAW_DIR / f"geoBoundaries-BGD-ADM{level}.geojson"
    for level in range(1, 5)
}

SIMPLIFICATION_TOLERANCES = (
    0.0001,
    0.0005,
    0.001,
    0.002,
    0.005,
)

# Inspect all geometries, but benchmark simplification on a sample.
SIMPLIFICATION_SAMPLE_INTERVAL = {
    1: 1,
    2: 1,
    3: 5,
    4: 25,
}

MAX_EXAMPLES = 8
MAX_DUPLICATES = 10


def stream_features(path):
    with path.open("rb") as file:
        yield from ijson.items(
            file,
            "features.item",
            use_float=True,
        )


def format_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)[:120]

    return str(value)[:120]


def inspect_properties(path):
    feature_count = 0
    property_counts = Counter()
    property_samples = defaultdict(list)
    property_values = defaultdict(Counter)
    geometry_types = Counter()

    first_features = []

    for feature in stream_features(path):
        feature_count += 1

        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}

        geometry_types[geometry.get("type", "null")] += 1

        if len(first_features) < 3:
            first_features.append(properties)

        for key, value in properties.items():
            if value is None or value == "":
                continue

            property_counts[key] += 1

            formatted = format_value(value)

            if formatted not in property_samples[key]:
                if len(property_samples[key]) < MAX_EXAMPLES:
                    property_samples[key].append(formatted)

            # Only retain distributions for likely names/IDs/parents.
            key_lower = key.lower()

            if any(
                term in key_lower
                for term in (
                    "name",
                    "shapeid",
                    "pcode",
                    "code",
                    "parent",
                    "admin",
                )
            ):
                if isinstance(value, (str, int, float, bool)):
                    property_values[key][str(value)] += 1

    print(f"  Features: {feature_count:,}")
    print(f"  Geometry types: {dict(geometry_types)}")

    print("\n  Properties:")

    for key in sorted(property_counts):
        present = property_counts[key]
        missing = feature_count - present

        print(f"\n    {key}")
        print(f"      Present: {present:,}/{feature_count:,}")
        print(f"      Missing: {missing:,}")
        print(f"      Examples: {property_samples[key]}")

    print("\n  Duplicate candidate values:")

    if not property_values:
        print("    No candidate name/ID properties detected.")

    for key, counts in sorted(property_values.items()):
        duplicate_values = [
            (value, count)
            for value, count in counts.items()
            if count > 1
        ]

        duplicate_values.sort(
            key=lambda item: (-item[1], item[0])
        )

        print(
            f"    {key}: "
            f"{len(counts):,} unique values, "
            f"{len(duplicate_values):,} duplicate groups"
        )

        for value, count in duplicate_values[:MAX_DUPLICATES]:
            print(f"      {value!r}: {count}")

    print("\n  First feature properties:")

    for index, properties in enumerate(first_features, 1):
        print(
            f"    Feature {index}: "
            f"{json.dumps(properties, ensure_ascii=False)}"
        )

    return feature_count


def count_coordinates(geometry):
    if geometry.is_empty:
        return 0

    if geometry.geom_type == "Polygon":
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if geometry.geom_type == "MultiPolygon":
        return sum(
            count_coordinates(polygon)
            for polygon in geometry.geoms
        )

    if hasattr(geometry, "geoms"):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    if hasattr(geometry, "coords"):
        return len(geometry.coords)

    return 0


def count_polygon_parts(geometry):
    if geometry.geom_type == "Polygon":
        return 1

    if geometry.geom_type == "MultiPolygon":
        return len(geometry.geoms)

    if hasattr(geometry, "geoms"):
        return sum(
            count_polygon_parts(part)
            for part in geometry.geoms
        )

    return 0


def inspect_geometry(path, level):
    feature_count = 0
    invalid_count = 0
    empty_count = 0
    total_parts = 0
    total_coordinates = 0

    coordinate_counts = []
    polygon_part_counts = []

    simplification = {
        tolerance: {
            "original_coordinates": 0,
            "simplified_coordinates": 0,
            "original_bytes": 0,
            "simplified_bytes": 0,
            "invalid": 0,
            "empty": 0,
            "sample_count": 0,
        }
        for tolerance in SIMPLIFICATION_TOLERANCES
    }

    interval = SIMPLIFICATION_SAMPLE_INTERVAL[level]

    for feature in stream_features(path):
        feature_count += 1

        geometry_data = feature.get("geometry")

        if geometry_data is None:
            empty_count += 1
            continue

        geometry = shape(geometry_data)

        if geometry.is_empty:
            empty_count += 1

        if not geometry.is_valid:
            invalid_count += 1

        coordinates = count_coordinates(geometry)
        parts = count_polygon_parts(geometry)

        total_coordinates += coordinates
        total_parts += parts

        coordinate_counts.append(coordinates)
        polygon_part_counts.append(parts)

        if (feature_count - 1) % interval != 0:
            continue

        original_bytes = len(
            json.dumps(
                geometry_data,
                separators=(",", ":"),
            ).encode("utf-8")
        )

        for tolerance, stats in simplification.items():
            simplified = geometry.simplify(
                tolerance,
                preserve_topology=True,
            )

            simplified_data = simplified.__geo_interface__

            simplified_bytes = len(
                json.dumps(
                    simplified_data,
                    separators=(",", ":"),
                ).encode("utf-8")
            )

            stats["original_coordinates"] += coordinates
            stats["simplified_coordinates"] += (
                count_coordinates(simplified)
            )

            stats["original_bytes"] += original_bytes
            stats["simplified_bytes"] += simplified_bytes

            stats["invalid"] += not simplified.is_valid
            stats["empty"] += simplified.is_empty
            stats["sample_count"] += 1

        if feature_count % 1000 == 0:
            print(f"  Inspected {feature_count:,} geometries...")

    coordinate_counts.sort()
    polygon_part_counts.sort()

    def median(values):
        if not values:
            return 0
        return values[len(values) // 2]

    print(f"\n  Geometry features: {feature_count:,}")
    print(f"  Invalid geometries: {invalid_count:,}")
    print(f"  Empty geometries: {empty_count:,}")
    print(f"  Total polygon parts: {total_parts:,}")
    print(f"  Total coordinates: {total_coordinates:,}")
    print(f"  Median coordinates: {median(coordinate_counts):,}")
    print(
        f"  Maximum coordinates: "
        f"{max(coordinate_counts, default=0):,}"
    )
    print(
        f"  Median polygon parts: "
        f"{median(polygon_part_counts):,}"
    )
    print(
        f"  Maximum polygon parts: "
        f"{max(polygon_part_counts, default=0):,}"
    )

    print("\n  Simplification benchmarks:")
    print(f"  Sampling every {interval} feature(s)")

    for tolerance, stats in simplification.items():
        original_coords = stats["original_coordinates"]
        simplified_coords = stats["simplified_coordinates"]

        original_bytes = stats["original_bytes"]
        simplified_bytes = stats["simplified_bytes"]

        coordinate_reduction = (
            100 * (1 - simplified_coords / original_coords)
            if original_coords
            else 0
        )

        size_reduction = (
            100 * (1 - simplified_bytes / original_bytes)
            if original_bytes
            else 0
        )

        print(
            f"    {tolerance:<8g} "
            f"coordinates: -{coordinate_reduction:5.1f}%  "
            f"bytes: -{size_reduction:5.1f}%  "
            f"invalid: {stats['invalid']}  "
            f"empty: {stats['empty']}  "
            f"samples: {stats['sample_count']:,}"
        )


def main():
    print("Bangladesh administrative dataset inspection")

    for level, path in DATASETS.items():
        print("\n" + "=" * 72)
        print(f"ADM{level}: {path.name}")
        print("=" * 72)

        if not path.exists():
            print(f"  Missing file: {path}")
            continue

        print(
            f"  File size: "
            f"{path.stat().st_size / 1_000_000:.2f} MB"
        )

        print("\nPROPERTY INSPECTION")
        feature_count = inspect_properties(path)

        print("\nGEOMETRY INSPECTION")
        inspect_geometry(path, level)

        print(f"\nCompleted ADM{level}: {feature_count:,} features")

    print("\nInspection complete.")


if __name__ == "__main__":
    main()
