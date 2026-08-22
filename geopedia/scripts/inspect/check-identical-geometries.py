"""
Finds GeoJSON features that share exactly identical geometry.

This is useful for detecting overlay regions or duplicate geographic
features in datasets where multiple records occupy the same polygon.

Usage:

    python scripts/inspect/check_identical_geometries.py \
        path/to/file.geojson
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def geometry_key(geometry):
    """
    Converts a geometry into a consistent string representation so
    geometrically identical GeoJSON objects produce the same key.
    """
    return json.dumps(
        geometry,
        sort_keys=True,
        separators=(",", ":"),
    )


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python "
            "scripts/inspect/check_identical_geometries.py "
            "<geojson-file> [property]"
        )
        return

    file_path = Path(sys.argv[1])

    # Optional property used when displaying matching features.
    display_property = (
        sys.argv[2]
        if len(sys.argv) >= 3
        else None
    )

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

    geometry_groups = defaultdict(list)

    for feature in features:
        geometry = feature.get(
            "geometry"
        )

        if not geometry:
            continue

        key = geometry_key(
            geometry
        )

        if display_property:
            value = (
                feature.get(
                    "properties",
                    {},
                ).get(
                    display_property
                )
            )
        else:
            value = (
                feature.get("id")
            )

        geometry_groups[key].append(
            value
        )

    shared_groups = [
        values
        for values in geometry_groups.values()
        if len(values) > 1
    ]

    print(
        "Total features:",
        len(features),
    )

    print(
        "Unique geometries:",
        len(geometry_groups),
    )

    print(
        "Shared geometries:",
        len(shared_groups),
    )

    if not shared_groups:
        return

    print(
        "\nFeatures sharing identical geometry:"
    )

    for values in shared_groups:
        display_values = [
            str(value)
            for value in values
        ]

        print(
            "  "
            + " / ".join(
                display_values
            )
        )


if __name__ == "__main__":
    main()