
"""
Inspect Bhutan geoBoundaries ADM1 and ADM2 datasets.

Checks:
- Feature counts and geometry types
- Property coverage and example values
- Dzongkha-script name availability
- Duplicate administrative names
- Geometry validity
- Simplification size estimates

Inputs:
  data/raw/countries/bhutan/
    geoBoundaries-BTN-ADM1.geojson
    geoBoundaries-BTN-ADM2.geojson

Run:
  python scripts/countries/asia/bhutan/inspect/admin.py

Dependencies:
  pip install shapely
"""

import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from shapely.geometry import mapping, shape


ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / "data/raw/countries/bhutan"

LEVELS = (1, 2)

TOLERANCES = (0.0001, 0.0005, 0.001)


def contains_tibetan_script(value):
    """Detect Tibetan-script characters used to write Dzongkha."""
    return any(
        "\u0f00" <= char <= "\u0fff"
        for char in str(value or "")
    )


def inspect_properties(features):
    keys = sorted({
        key
        for feature in features
        for key in feature.get("properties", {})
    })

    print("\nPROPERTY COVERAGE:")

    for key in keys:
        values = [
            feature.get("properties", {}).get(key)
            for feature in features
        ]

        populated = [
            value
            for value in values
            if value is not None and str(value).strip()
        ]

        native = sum(
            contains_tibetan_script(value)
            for value in populated
        )

        examples = list(dict.fromkeys(
            str(value)[:100]
            for value in populated
        ))[:3]

        print(f"\n  {key}")
        print(f"    Populated: {len(populated)}/{len(features)}")
        print(f"    Dzongkha script: {native}/{len(features)}")
        print(f"    Examples: {' | '.join(examples) or '(none)'}")


def inspect_duplicates(features):
    names = [
        str(feature.get("properties", {}).get("shapeName") or "").strip()
        for feature in features
    ]

    counts = Counter(names)
    duplicates = {
        name: count
        for name, count in counts.items()
        if count > 1
    }

    print("\nNAMES:")
    print(f"  Unique names: {len(counts)}")
    print(f"  Duplicate-name groups: {len(duplicates)}")

    for name, count in sorted(duplicates.items()):
        print(f"    {name}: {count}")


def inspect_geometry(features):
    geometries = [
        shape(feature["geometry"])
        for feature in features
    ]

    types = Counter(
        geometry.geom_type
        for geometry in geometries
    )

    invalid = [
        (index, geometry)
        for index, geometry in enumerate(geometries)
        if not geometry.is_valid or geometry.is_empty
    ]

    print("\nGEOMETRY TYPES:")
    for geometry_type, count in sorted(types.items()):
        print(f"  {geometry_type}: {count}")

    print(f"\nINVALID OR EMPTY GEOMETRIES: {len(invalid)}")

    for index, geometry in invalid[:10]:
        print(
            f"  Feature {index + 1}: "
            f"{geometry.geom_type}, valid={geometry.is_valid}"
        )

    original_size = sum(
        len(json.dumps(
            mapping(geometry),
            separators=(",", ":"),
        ))
        for geometry in geometries
    )

    print("\nSIMPLIFICATION ESTIMATES:")

    for tolerance in TOLERANCES:
        simplified_size = sum(
            len(json.dumps(
                mapping(geometry.simplify(
                    tolerance,
                    preserve_topology=True,
                )),
                separators=(",", ":"),
            ))
            for geometry in geometries
        )

        percentage = (
            100 * simplified_size / original_size
            if original_size else 0
        )

        print(
            f"  Tolerance {tolerance}: "
            f"{percentage:.2f}% of original geometry size"
        )


def inspect_level(level):
    path = RAW / f"geoBoundaries-BTN-ADM{level}.geojson"

    print("\n" + "=" * 65)
    print(f"ADM{level}: {path.name}")
    print(f"FILE SIZE: {path.stat().st_size / 1024 / 1024:.2f} MB")
    print("=" * 65)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    features = data["features"]

    print(f"\nFEATURE COUNT: {len(features)}")

    inspect_properties(features)
    inspect_duplicates(features)
    inspect_geometry(features)

    print("\nFIRST 3 FEATURES:")

    for index, feature in enumerate(features[:3], 1):
        print(f"\n  Feature {index}:")
        print(json.dumps(
            feature.get("properties", {}),
            ensure_ascii=False,
            indent=4,
        ))


def main():
    for level in LEVELS:
        inspect_level(level)


if __name__ == "__main__":
    main()
