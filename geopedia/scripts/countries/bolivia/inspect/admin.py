"""
Inspects Bolivia's administrative boundary GeoJSON files.

Expected hierarchy:
    ADM1 -> Departments
    ADM2 -> Provinces
    ADM3 -> Municipalities

This script reports:
    - Feature counts
    - Geometry types
    - Available property names
    - Sample feature properties
    - Likely hierarchy fields
    - Duplicate IDs
    - Missing IDs / names

Inputs:
    data/raw/countries/bolivia/bol_admin_boundaries.geojson/bol_admin1.geojson
    data/raw/countries/bolivia/bol_admin_boundaries.geojson/bol_admin2.geojson
    data/raw/countries/bolivia/bol_admin_boundaries.geojson/bol_admin3.geojson
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_DIRECTORY = Path(
    "data/raw/countries/bolivia/bol_admin_boundaries.geojson"
)

ADM1_PATH = RAW_DIRECTORY / "bol_admin1.geojson"
ADM2_PATH = RAW_DIRECTORY / "bol_admin2.geojson"
ADM3_PATH = RAW_DIRECTORY / "bol_admin3.geojson"


# ---------------------------------------------------------------------------
# Reference expectations
# ---------------------------------------------------------------------------

EXPECTED_COUNTS = {
    "ADM1": 9,
    "ADM2": 112,
    "ADM3": 339,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} has no valid features array."
        )

    return data


def get_geometry_type(
    feature: dict[str, Any],
) -> str:
    geometry = feature.get("geometry")

    if not isinstance(geometry, dict):
        return "<missing>"

    geometry_type = geometry.get("type")

    if not isinstance(geometry_type, str):
        return "<missing>"

    return geometry_type


def get_properties(
    feature: dict[str, Any],
) -> dict[str, Any]:
    properties = feature.get("properties")

    if isinstance(properties, dict):
        return properties

    return {}


def collect_property_names(
    features: list[dict[str, Any]],
) -> list[str]:
    names: set[str] = set()

    for feature in features:
        names.update(
            get_properties(feature).keys()
        )

    return sorted(
        names
    )


def print_sample_properties(
    features: list[dict[str, Any]],
    sample_count: int = 5,
) -> None:
    print(
        "\nSample properties:"
    )

    for index, feature in enumerate(
        features[:sample_count],
        start=1,
    ):
        print(
            f"\n  Feature {index}:"
        )

        properties = get_properties(
            feature
        )

        for key in sorted(properties):
            print(
                f"    {key}: {properties[key]!r}"
            )


def inspect_candidate_field(
    features: list[dict[str, Any]],
    field_name: str,
) -> None:
    values: list[Any] = []

    missing_count = 0

    for feature in features:
        properties = get_properties(
            feature
        )

        value = properties.get(
            field_name
        )

        if value in (
            None,
            "",
        ):
            missing_count += 1
            continue

        values.append(
            value
        )

    if not values:
        return

    duplicate_values = [
        value
        for value, count in Counter(values).items()
        if count > 1
    ]

    print(
        f"\n  Field: {field_name}"
    )

    print(
        f"    Populated: {len(values)}"
    )

    print(
        f"    Missing:   {missing_count}"
    )

    print(
        f"    Unique:    {len(set(values))}"
    )

    if duplicate_values:
        print(
            f"    Duplicates: {len(duplicate_values)} distinct duplicated values"
        )

        for value in duplicate_values[:10]:
            print(
                f"      {value!r}"
            )

        if len(duplicate_values) > 10:
            print(
                "      ..."
            )
    else:
        print(
            "    Duplicates: none"
        )


def inspect_likely_hierarchy_fields(
    features: list[dict[str, Any]],
) -> None:
    property_names = collect_property_names(
        features
    )

    likely_fields = [
        name
        for name in property_names
        if any(
            token in name.lower()
            for token in (
                "adm",
                "pcode",
                "code",
                "name",
            )
        )
    ]

    if not likely_fields:
        return

    print(
        "\nLikely hierarchy / identity fields:"
    )

    for field_name in likely_fields:
        inspect_candidate_field(
            features,
            field_name,
        )


def inspect_layer(
    label: str,
    path: Path,
) -> None:
    data = load_geojson(
        path
    )

    features = data[
        "features"
    ]

    expected_count = EXPECTED_COUNTS[
        label
    ]

    geometry_counts = Counter(
        get_geometry_type(feature)
        for feature in features
    )

    property_names = collect_property_names(
        features
    )

    print(
        "=" * 80
    )

    print(
        label
    )

    print(
        "=" * 80
    )

    print(
        f"File: {path}"
    )

    print(
        f"Features: {len(features)}"
    )

    print(
        f"Reference expectation: {expected_count}"
    )

    difference = (
        len(features)
        - expected_count
    )

    if difference == 0:
        print(
            "Count comparison: matches expectation"
        )
    else:
        sign = (
            "+"
            if difference > 0
            else ""
        )

        print(
            f"Count comparison: {sign}{difference} from expectation"
        )

    print(
        "\nGeometry types:"
    )

    for geometry_type, count in sorted(
        geometry_counts.items()
    ):
        print(
            f"  {geometry_type}: {count}"
        )

    print(
        "\nProperty names:"
    )

    for property_name in property_names:
        print(
            f"  {property_name}"
        )

    inspect_likely_hierarchy_fields(
        features
    )

    print_sample_properties(
        features
    )

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Inspecting Bolivia administrative boundaries...\n"
    )

    inspect_layer(
        "ADM1",
        ADM1_PATH,
    )

    inspect_layer(
        "ADM2",
        ADM2_PATH,
    )

    inspect_layer(
        "ADM3",
        ADM3_PATH,
    )

    print(
        "Inspection complete."
    )


if __name__ == "__main__":
    main()