"""
Generic GeoJSON inspection utility.

Prints basic information about a GeoJSON FeatureCollection, including:

- feature count
- geometry types
- the properties of the first few features

Usage:

    python scripts/inspect/inspect_geojson.py path/to/file.geojson
"""

import json
import sys
from collections import Counter
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "scripts/inspect/inspect_geojson.py "
            "<geojson-file>"
        )
        return

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(
            f"ERROR: File not found: {file_path}"
        )
        return

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    features = data.get(
        "features",
        [],
    )

    print(
        "Top-level type:",
        data.get("type"),
    )

    print(
        "Feature count:",
        len(features),
    )

    geometry_types = Counter(
        (
            feature.get("geometry")
            or {}
        ).get(
            "type",
            "None",
        )
        for feature in features
    )

    print("\nGeometry types:")

    for geometry_type, count in (
        geometry_types.items()
    ):
        print(
            f"  {geometry_type}: {count}"
        )

    print("\nFirst 5 features:")

    for index, feature in enumerate(
        features[:5],
        start=1,
    ):
        print(
            f"\n--- Feature {index} ---"
        )

        print(
            "ID:",
            feature.get("id"),
        )

        geometry = (
            feature.get("geometry")
            or {}
        )

        print(
            "Geometry:",
            geometry.get("type"),
        )

        print("Properties:")

        properties = feature.get(
            "properties",
            {},
        )

        for key, value in (
            properties.items()
        ):
            print(
                f"  {key}: {value}"
            )


if __name__ == "__main__":
    main()