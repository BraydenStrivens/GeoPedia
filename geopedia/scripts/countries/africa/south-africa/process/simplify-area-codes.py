"""
Simplify South Africa telephone area-code GeoJSON for GeoPedia runtime use.

The source polygons are dissolved from GeoPedia's ward-level telephone
area-code classification. This script simplifies both the full area-code
regions and the one-digit prefix regions while preserving topology as much as
possible for interactive MapLibre rendering.

Inputs:
    data/intermediate/countries/south-africa/area-codes/
    area-codes.geojson

    data/intermediate/countries/south-africa/area-codes/
    area-code-prefixes.geojson

Outputs:
    public/data/countries/south-africa/geojson/
    area-codes.geojson

    public/data/countries/south-africa/geojson/
    area-code-prefixes.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/process/simplify-area-codes.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape


AREA_CODES_INPUT = Path(
    "data/intermediate/countries/south-africa/area-codes/"
    "area-codes.geojson"
)

PREFIXES_INPUT = Path(
    "data/intermediate/countries/south-africa/area-codes/"
    "area-code-prefixes.geojson"
)

AREA_CODES_OUTPUT = Path(
    "public/data/countries/south-africa/geojson/"
    "area-codes.geojson"
)

PREFIXES_OUTPUT = Path(
    "public/data/countries/south-africa/geojson/"
    "area-code-prefixes.geojson"
)


# Area-code boundaries are derived from municipal wards and contain far more
# detail than GeoPedia needs at national quiz zoom levels.
AREA_CODE_TOLERANCE = 0.0025

# The five prefix regions are substantially larger and can tolerate slightly
# stronger simplification.
PREFIX_TOLERANCE = 0.005


def load_feature_collection(
    path: Path,
) -> list[dict[str, Any]]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
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

    return features


def simplify_features(
    features: list[dict[str, Any]],
    tolerance: float,
) -> list[dict[str, Any]]:
    """
    Simplify feature geometries while preserving polygon topology.
    """
    output: list[dict[str, Any]] = []

    for feature in features:
        geometry_data = feature.get(
            "geometry"
        )

        if not geometry_data:
            raise ValueError(
                "Feature is missing geometry."
            )

        geometry = shape(
            geometry_data
        )

        simplified = geometry.simplify(
            tolerance,
            preserve_topology=True,
        )

        if simplified.is_empty:
            raise ValueError(
                "Simplification produced an empty geometry."
            )

        if not simplified.is_valid:
            raise ValueError(
                "Simplification produced invalid geometry."
            )

        output.append(
            {
                "type": "Feature",
                "geometry": mapping(
                    simplified
                ),
                "properties": dict(
                    feature.get(
                        "properties",
                        {},
                    )
                ),
            }
        )

    return output


def write_feature_collection(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    """Write a compact GeoJSON FeatureCollection."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": features,
            },
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def size_mb(
    path: Path,
) -> float:
    """Return a file's size in MiB."""
    return (
        path.stat().st_size
        / (1024 * 1024)
    )


def process_dataset(
    label: str,
    input_path: Path,
    output_path: Path,
    tolerance: float,
) -> None:
    """Load, simplify, validate, and write one runtime dataset."""
    print()
    print(label)
    print("-" * 72)

    features = load_feature_collection(
        input_path
    )

    print(
        f"Features:        {len(features):,}"
    )
    print(
        f"Tolerance:       {tolerance}"
    )
    print(
        f"Input size:      {size_mb(input_path):.2f} MB"
    )

    simplified = simplify_features(
        features,
        tolerance,
    )

    write_feature_collection(
        output_path,
        simplified,
    )

    print(
        f"Output size:     {size_mb(output_path):.2f} MB"
    )
    print(
        f"Output:          {output_path}"
    )


def main() -> None:
    print("=" * 72)
    print("SOUTH AFRICA AREA-CODE SIMPLIFICATION")
    print("=" * 72)

    process_dataset(
        "Full area codes",
        AREA_CODES_INPUT,
        AREA_CODES_OUTPUT,
        AREA_CODE_TOLERANCE,
    )

    process_dataset(
        "One-digit prefixes",
        PREFIXES_INPUT,
        PREFIXES_OUTPUT,
        PREFIX_TOLERANCE,
    )

    print()
    print("Simplification complete.")


if __name__ == "__main__":
    main()