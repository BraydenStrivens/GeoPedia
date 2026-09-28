"""Inspect the Dominican Republic administrative-boundary source data.

Validates the ADM1–ADM3 hierarchy downloaded from HDX/OCHA and originally
sourced from the Dominican Republic Oficina Nacional de Estadística (ONE).

The script checks:
- Feature and geometry counts.
- Required properties.
- Unique administrative pcodes.
- Blank names and pcodes.
- Expected administrative name prefixes.
- Parent-child relationships between ADM1, ADM2, and ADM3.
- Consistency of ADM1 ancestry stored on ADM3 features.
- Dataset metadata values such as valid_on, version, and language.
- Duplicate display names after administrative prefixes are removed.

This script only inspects the raw source data. It does not modify or generate
any files.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "dominican-republic"
    / "dom_admin_boundaries.geojson"
)

ADM_PATHS = {
    1: SOURCE_DIR / "dom_admin1.geojson",
    2: SOURCE_DIR / "dom_admin2.geojson",
    3: SOURCE_DIR / "dom_admin3.geojson",
}

EXPECTED_COUNTS = {
    1: 10,
    2: 32,
    3: 155,
}

EXPECTED_PREFIXES = {
    1: "Región ",
    2: "Provincia ",
    3: "Municipio ",
}

REQUIRED_PROPERTIES = {
    1: {
        "adm1_name",
        "adm1_pcode",
        "adm0_name",
        "adm0_pcode",
        "valid_on",
        "valid_to",
        "version",
        "lang",
    },
    2: {
        "adm2_name",
        "adm2_pcode",
        "adm1_name",
        "adm1_pcode",
        "adm0_name",
        "adm0_pcode",
        "valid_on",
        "valid_to",
        "version",
        "lang",
    },
    3: {
        "adm3_name",
        "adm3_pcode",
        "adm2_name",
        "adm2_pcode",
        "adm1_name",
        "adm1_pcode",
        "adm0_name",
        "adm0_pcode",
        "valid_on",
        "valid_to",
        "version",
        "lang",
    },
}


def load_features(path: Path) -> list[dict[str, Any]]:
    """Load and return the features from a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(f"Source file does not exist: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"Expected FeatureCollection in {path}")

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(f"Missing or invalid features array in {path}")

    return features


def get_properties(feature: dict[str, Any]) -> dict[str, Any]:
    """Return a feature's properties dictionary."""
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError("Feature has missing or invalid properties.")

    return properties


def clean_display_name(name: str, prefix: str) -> str:
    """Remove an expected administrative prefix from a source name."""
    if name.startswith(prefix):
        return name[len(prefix) :].strip()

    return name.strip()


def print_heading(title: str) -> None:
    """Print a clearly separated report heading."""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def inspect_level(
    level: int,
    features: list[dict[str, Any]],
) -> None:
    """Print structural and attribute diagnostics for one ADM level."""
    name_property = f"adm{level}_name"
    pcode_property = f"adm{level}_pcode"
    expected_prefix = EXPECTED_PREFIXES[level]

    properties = [get_properties(feature) for feature in features]

    print_heading(f"ADM{level}")

    print(f"Features: {len(features)}")
    print(f"Expected features: {EXPECTED_COUNTS[level]}")
    print(
        "Feature count valid:",
        len(features) == EXPECTED_COUNTS[level],
    )

    geometry_types = Counter(
        feature.get("geometry", {}).get("type")
        if isinstance(feature.get("geometry"), dict)
        else None
        for feature in features
    )

    print(f"Geometry types: {dict(geometry_types)}")

    available_properties = set(properties[0]) if properties else set()
    missing_required = REQUIRED_PROPERTIES[level] - available_properties

    print(f"Required properties present: {not missing_required}")

    if missing_required:
        print(f"Missing required properties: {sorted(missing_required)}")

    names = [props.get(name_property) for props in properties]
    pcodes = [props.get(pcode_property) for props in properties]

    blank_names = [
        index
        for index, name in enumerate(names)
        if not isinstance(name, str) or not name.strip()
    ]

    blank_pcodes = [
        index
        for index, pcode in enumerate(pcodes)
        if not isinstance(pcode, str) or not pcode.strip()
    ]

    print(f"Blank names: {len(blank_names)}")
    print(f"Blank pcodes: {len(blank_pcodes)}")

    pcode_counts = Counter(pcodes)
    duplicate_pcodes = {
        pcode: count
        for pcode, count in pcode_counts.items()
        if pcode is not None and count > 1
    }

    print(f"Unique pcodes: {len(pcode_counts)}")
    print(f"Duplicate pcodes: {len(duplicate_pcodes)}")

    if duplicate_pcodes:
        for pcode, count in sorted(duplicate_pcodes.items()):
            print(f"  {pcode}: {count}")

    unexpected_prefix_names = [
        name
        for name in names
        if isinstance(name, str) and not name.startswith(expected_prefix)
    ]

    print(
        f'Names missing expected "{expected_prefix.strip()}" prefix: '
        f"{len(unexpected_prefix_names)}"
    )

    for name in unexpected_prefix_names:
        print(f"  {name!r}")

    display_names = [
        clean_display_name(name, expected_prefix)
        for name in names
        if isinstance(name, str)
    ]

    display_name_counts = Counter(display_names)
    duplicate_display_names = {
        name: count
        for name, count in display_name_counts.items()
        if count > 1
    }

    print(f"Duplicate display names: {len(duplicate_display_names)}")

    for name, count in sorted(duplicate_display_names.items()):
        print(f"  {name}: {count}")

    print()
    print("Metadata values:")

    for property_name in ("valid_on", "valid_to", "version", "lang"):
        values = Counter(props.get(property_name) for props in properties)
        print(f"  {property_name}: {dict(values)}")

    print()
    print("Names and pcodes:")

    entries = sorted(
        (
            str(props.get(pcode_property, "")),
            str(props.get(name_property, "")),
        )
        for props in properties
    )

    for pcode, name in entries:
        print(f"  {pcode}: {name}")


def inspect_adm2_hierarchy(
    adm1_features: list[dict[str, Any]],
    adm2_features: list[dict[str, Any]],
) -> None:
    """Validate ADM2 parent references against ADM1."""
    print_heading("ADM2 -> ADM1 HIERARCHY")

    adm1_by_pcode = {
        get_properties(feature)["adm1_pcode"]: get_properties(feature)
        for feature in adm1_features
    }

    missing_parents: list[str] = []
    name_mismatches: list[str] = []

    children_by_parent: defaultdict[str, list[str]] = defaultdict(list)

    for feature in adm2_features:
        props = get_properties(feature)

        adm2_pcode = props["adm2_pcode"]
        adm2_name = props["adm2_name"]
        parent_pcode = props["adm1_pcode"]
        parent_name = props["adm1_name"]

        children_by_parent[parent_pcode].append(adm2_pcode)

        parent = adm1_by_pcode.get(parent_pcode)

        if parent is None:
            missing_parents.append(
                f"{adm2_pcode} ({adm2_name}) -> {parent_pcode}"
            )
            continue

        if parent["adm1_name"] != parent_name:
            name_mismatches.append(
                f"{adm2_pcode}: "
                f"{parent_name!r} != {parent['adm1_name']!r}"
            )

    print(f"Missing ADM1 parents: {len(missing_parents)}")

    for message in missing_parents:
        print(f"  {message}")

    print(f"ADM1 parent-name mismatches: {len(name_mismatches)}")

    for message in name_mismatches:
        print(f"  {message}")

    unused_parents = sorted(set(adm1_by_pcode) - set(children_by_parent))

    print(f"ADM1 regions with no ADM2 children: {len(unused_parents)}")

    for pcode in unused_parents:
        print(f"  {pcode}: {adm1_by_pcode[pcode]['adm1_name']}")

    print()
    print("Province counts by region:")

    for pcode in sorted(adm1_by_pcode):
        name = adm1_by_pcode[pcode]["adm1_name"]
        count = len(children_by_parent[pcode])
        print(f"  {pcode} {name}: {count}")


def inspect_adm3_hierarchy(
    adm1_features: list[dict[str, Any]],
    adm2_features: list[dict[str, Any]],
    adm3_features: list[dict[str, Any]],
) -> None:
    """Validate ADM3 parent and ancestor references."""
    print_heading("ADM3 -> ADM2 -> ADM1 HIERARCHY")

    adm1_by_pcode = {
        get_properties(feature)["adm1_pcode"]: get_properties(feature)
        for feature in adm1_features
    }

    adm2_by_pcode = {
        get_properties(feature)["adm2_pcode"]: get_properties(feature)
        for feature in adm2_features
    }

    missing_adm2_parents: list[str] = []
    adm2_name_mismatches: list[str] = []
    adm1_pcode_mismatches: list[str] = []
    adm1_name_mismatches: list[str] = []

    children_by_province: defaultdict[str, list[str]] = defaultdict(list)

    for feature in adm3_features:
        props = get_properties(feature)

        adm3_pcode = props["adm3_pcode"]
        adm3_name = props["adm3_name"]
        adm2_pcode = props["adm2_pcode"]

        children_by_province[adm2_pcode].append(adm3_pcode)

        parent = adm2_by_pcode.get(adm2_pcode)

        if parent is None:
            missing_adm2_parents.append(
                f"{adm3_pcode} ({adm3_name}) -> {adm2_pcode}"
            )
            continue

        if props["adm2_name"] != parent["adm2_name"]:
            adm2_name_mismatches.append(
                f"{adm3_pcode}: "
                f"{props['adm2_name']!r} != {parent['adm2_name']!r}"
            )

        if props["adm1_pcode"] != parent["adm1_pcode"]:
            adm1_pcode_mismatches.append(
                f"{adm3_pcode}: "
                f"{props['adm1_pcode']} != {parent['adm1_pcode']}"
            )

        if props["adm1_name"] != parent["adm1_name"]:
            adm1_name_mismatches.append(
                f"{adm3_pcode}: "
                f"{props['adm1_name']!r} != {parent['adm1_name']!r}"
            )

        adm1 = adm1_by_pcode.get(props["adm1_pcode"])

        if adm1 is None:
            adm1_pcode_mismatches.append(
                f"{adm3_pcode}: unknown ADM1 {props['adm1_pcode']}"
            )
        elif props["adm1_name"] != adm1["adm1_name"]:
            adm1_name_mismatches.append(
                f"{adm3_pcode}: "
                f"{props['adm1_name']!r} != {adm1['adm1_name']!r}"
            )

    print(f"Missing ADM2 parents: {len(missing_adm2_parents)}")

    for message in missing_adm2_parents:
        print(f"  {message}")

    print(f"ADM2 parent-name mismatches: {len(adm2_name_mismatches)}")

    for message in adm2_name_mismatches:
        print(f"  {message}")

    print(f"ADM1 pcode mismatches: {len(adm1_pcode_mismatches)}")

    for message in adm1_pcode_mismatches:
        print(f"  {message}")

    print(f"ADM1 name mismatches: {len(adm1_name_mismatches)}")

    for message in adm1_name_mismatches:
        print(f"  {message}")

    unused_provinces = sorted(set(adm2_by_pcode) - set(children_by_province))

    print(f"Provinces with no municipalities: {len(unused_provinces)}")

    for pcode in unused_provinces:
        print(f"  {pcode}: {adm2_by_pcode[pcode]['adm2_name']}")

    print()
    print("Municipality counts by province:")

    for pcode in sorted(adm2_by_pcode):
        name = adm2_by_pcode[pcode]["adm2_name"]
        count = len(children_by_province[pcode])
        print(f"  {pcode} {name}: {count}")


def main() -> None:
    """Run all Dominican Republic administrative-boundary inspections."""
    print("Dominican Republic administrative-boundary inspection")
    print(f"Source directory: {SOURCE_DIR}")

    datasets = {
        level: load_features(path)
        for level, path in ADM_PATHS.items()
    }

    for level in (1, 2, 3):
        inspect_level(level, datasets[level])

    inspect_adm2_hierarchy(
        datasets[1],
        datasets[2],
    )

    inspect_adm3_hierarchy(
        datasets[1],
        datasets[2],
        datasets[3],
    )

    print_heading("SUMMARY")

    print("Inspection complete.")
    print(
        "Review all counts, duplicate names, metadata values, and hierarchy "
        "errors above before processing the source data."
    )


if __name__ == "__main__":
    main()