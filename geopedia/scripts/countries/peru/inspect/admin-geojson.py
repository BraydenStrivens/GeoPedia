"""
Inspects Peru's raw administrative GeoJSON files.

The goal is to determine:

- feature counts
- available property names
- geometry types
- likely stable administrative IDs
- likely administrative names
- hierarchy fields between admin1, admin2, and admin3

Input directory:
    data/raw/countries/peru/per_admin_boundaries.geojson/
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


RAW_DIRECTORY = Path(
    "data/raw/countries/peru/per_admin_boundaries.geojson"
)

FILES = {
    "admin1": RAW_DIRECTORY / "per_admin1.geojson",
    "admin2": RAW_DIRECTORY / "per_admin2.geojson",
    "admin3": RAW_DIRECTORY / "per_admin3.geojson",
}


def load_geojson(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    return data


def inspect_file(label: str, path: Path) -> None:
    print("=" * 80)
    print(label.upper())
    print("=" * 80)

    data = load_geojson(path)

    features = data.get("features", [])

    print(f"File: {path}")
    print(f"Features: {len(features):,}")

    geometry_types = Counter(
        feature.get("geometry", {}).get("type")
        if feature.get("geometry")
        else None
        for feature in features
    )

    print("\nGeometry types:")

    for geometry_type, count in sorted(
        geometry_types.items(),
        key=lambda item: str(item[0]),
    ):
        print(
            f"  {geometry_type}: {count:,}"
        )

    all_property_keys = set()

    for feature in features:
        properties = feature.get("properties", {})

        all_property_keys.update(
            properties.keys()
        )

    print("\nProperty keys:")

    for key in sorted(all_property_keys):
        print(f"  {key}")

    print("\nFirst 5 feature property objects:")

    for index, feature in enumerate(
        features[:5],
        start=1,
    ):
        properties = feature.get(
            "properties",
            {},
        )

        print(f"\nFeature {index}:")

        for key in sorted(properties):
            print(
                f"  {key}: {properties[key]!r}"
            )

    print("\n")


def main() -> None:
    print(
        "Inspecting Peru administrative GeoJSON files...\n"
    )

    for label, path in FILES.items():
        inspect_file(label, path)


if __name__ == "__main__":
    main()