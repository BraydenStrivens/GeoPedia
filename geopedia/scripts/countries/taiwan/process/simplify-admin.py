"""
Prepare Taiwan administrative GeoJSON for GeoPedia's public map data.

Inputs
------
data/intermediate/countries/taiwan/provinces.geojson
data/intermediate/countries/taiwan/counties.geojson
data/intermediate/countries/taiwan/townships.geojson

Outputs
-------
public/data/countries/taiwan/geojson/provinces.geojson
public/data/countries/taiwan/geojson/counties.geojson
public/data/countries/taiwan/geojson/townships.geojson

Processing
----------
Provinces:
    Copied unchanged. The normalized source is already very small.

Counties:
    Copied unchanged. The normalized source is already very small.

Townships:
    Simplified with Mapshaper using:

        -clean
        -simplify weighted 10% keep-shapes

The script validates that feature counts, IDs, required properties, and
geometries survive processing.

Run from the GeoPedia project root:

    python scripts/countries/taiwan/process/simplify-admin.py

Requires Mapshaper to be available through npx.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]

INTERMEDIATE_DIR = (
    ROOT / "data" / "intermediate" / "countries" / "taiwan"
)

PUBLIC_DIR = (
    ROOT / "public" / "data" / "countries" / "taiwan" / "geojson"
)


# ---------------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------------

DATASETS = {
    "provinces": {
        "input": INTERMEDIATE_DIR / "provinces.geojson",
        "output": PUBLIC_DIR / "provinces.geojson",
        "id_property": "province_id",
        "expected_count": 7,
        "required_properties": {
            "province_id",
            "province",
            "native_province",
        },
        "simplify": False,
    },
    "counties": {
        "input": INTERMEDIATE_DIR / "counties.geojson",
        "output": PUBLIC_DIR / "counties.geojson",
        "id_property": "county_id",
        "expected_count": 22,
        "required_properties": {
            "county_id",
            "county",
            "native_county",
            "province_id",
            "province",
            "native_province",
        },
        "simplify": False,
    },
    "townships": {
        "input": INTERMEDIATE_DIR / "townships.geojson",
        "output": PUBLIC_DIR / "townships.geojson",
        "id_property": "township_id",
        "expected_count": 368,
        "required_properties": {
            "township_id",
            "township",
            "native_township",
            "county_id",
            "county",
            "native_county",
            "province_id",
            "province",
            "native_province",
        },
        "simplify": True,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_ids(data: dict, id_property: str) -> list[str]:
    ids: list[str] = []

    for feature in data["features"]:
        props = feature.get("properties") or {}

        if id_property not in props:
            raise ValueError(
                f"Feature missing ID property {id_property!r}."
            )

        ids.append(str(props[id_property]))

    return ids


def validate_geojson(
    name: str,
    data: dict,
    config: dict,
) -> set[str]:
    features = data.get("features", [])

    if len(features) != config["expected_count"]:
        raise ValueError(
            f"{name}: expected {config['expected_count']} features, "
            f"found {len(features)}."
        )

    ids = get_ids(data, config["id_property"])

    if len(ids) != len(set(ids)):
        raise ValueError(
            f"{name}: duplicate IDs found."
        )

    for feature in features:
        props = feature.get("properties") or {}

        missing = config["required_properties"] - set(props)

        if missing:
            raise ValueError(
                f"{name}: feature "
                f"{props.get(config['id_property'])!r} "
                f"is missing properties {sorted(missing)}."
            )

        geometry = feature.get("geometry")

        if geometry is None:
            raise ValueError(
                f"{name}: feature "
                f"{props.get(config['id_property'])!r} "
                "has no geometry."
            )

        if geometry.get("type") not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError(
                f"{name}: unexpected geometry type "
                f"{geometry.get('type')!r}."
            )

    return set(ids)


def validate_ids_preserved(
    name: str,
    expected_ids: set[str],
    output_data: dict,
    config: dict,
) -> None:
    actual_ids = set(
        get_ids(
            output_data,
            config["id_property"],
        )
    )

    if actual_ids != expected_ids:
        missing = expected_ids - actual_ids
        unexpected = actual_ids - expected_ids

        raise ValueError(
            f"{name}: feature IDs changed during processing.\n"
            f"Missing: {sorted(missing)}\n"
            f"Unexpected: {sorted(unexpected)}"
        )


def copy_unchanged(
    name: str,
    input_path: Path,
    output_path: Path,
) -> None:
    print(f"Copying {name} unchanged...")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copyfile(
        input_path,
        output_path,
    )


def simplify(
    name: str,
    input_path: Path,
    output_path: Path,
) -> None:
    print(f"Simplifying {name}...")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "npx.cmd",
        "mapshaper",
        str(input_path),
        "-clean",
        "-simplify",
        "weighted",
        "10%",
        "keep-shapes",
        "-o",
        "format=geojson",
        "precision=0.000001",
        str(output_path),
    ]

    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    PUBLIC_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name, config in DATASETS.items():
        input_path = config["input"]
        output_path = config["output"]

        if not input_path.exists():
            raise FileNotFoundError(
                f"Missing intermediate file: {input_path}"
            )

        source = load_geojson(input_path)

        expected_ids = validate_geojson(
            name,
            source,
            config,
        )

        if config["simplify"]:
            simplify(
                name,
                input_path,
                output_path,
            )
        else:
            copy_unchanged(
                name,
                input_path,
                output_path,
            )

        output = load_geojson(output_path)

        validate_geojson(
            name,
            output,
            config,
        )

        validate_ids_preserved(
            name,
            expected_ids,
            output,
            config,
        )

        input_size = input_path.stat().st_size
        output_size = output_path.stat().st_size

        if config["simplify"]:
            reduction = (
                100 * (1 - output_size / input_size)
                if input_size
                else 0
            )

            print(
                f"  {config['expected_count']} features"
                f" | {input_size / 1024 / 1024:.2f} MB"
                f" -> {output_size / 1024 / 1024:.2f} MB"
                f" | {reduction:.1f}% smaller"
            )
        else:
            print(
                f"  {config['expected_count']} features"
                f" | {output_size / 1024 / 1024:.2f} MB"
                f" | unchanged"
            )

    print()
    print("Taiwan administrative public data complete.")
    print()
    print("Outputs:")

    for config in DATASETS.values():
        print(
            f"  {config['output'].relative_to(ROOT)}"
        )


if __name__ == "__main__":
    main()