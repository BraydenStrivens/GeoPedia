"""
Simplifies Peru's processed administrative GeoJSON files for GeoPedia runtime
use while preserving the full-detail intermediate files.

Inputs:
    data/intermediate/countries/peru/admin/regions.geojson
    data/intermediate/countries/peru/admin/provinces.geojson
    data/intermediate/countries/peru/admin/districts.geojson

Outputs:
    public/data/countries/peru/geojson/regions.geojson
    public/data/countries/peru/geojson/provinces.geojson
    public/data/countries/peru/geojson/districts.geojson

Different simplification tolerances are used for each administrative level.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

INTERMEDIATE_DIRECTORY = Path(
    "data/intermediate/countries/peru/admin"
)

RUNTIME_DIRECTORY = Path(
    "public/data/countries/peru/geojson"
)

FILES = {
    "Regions": {
        "input": INTERMEDIATE_DIRECTORY / "regions.geojson",
        "output": RUNTIME_DIRECTORY / "regions.geojson",
        "expected_count": 25,
        "tolerance": 0.01,
    },
    "Provinces": {
        "input": INTERMEDIATE_DIRECTORY / "provinces.geojson",
        "output": RUNTIME_DIRECTORY / "provinces.geojson",
        "expected_count": 196,
        "tolerance": 0.005,
    },
    "Districts": {
        "input": INTERMEDIATE_DIRECTORY / "districts.geojson",
        "output": RUNTIME_DIRECTORY / "districts.geojson",
        "expected_count": 1873,
        "tolerance": 0.0025,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} does not contain a valid features array."
        )

    return data


def write_geojson(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def simplify_feature(
    feature: dict[str, Any],
    tolerance: float,
) -> dict[str, Any]:
    geometry_data = feature.get("geometry")

    if not isinstance(geometry_data, dict):
        raise ValueError(
            "Feature is missing a valid geometry."
        )

    original_geometry = shape(
        geometry_data
    )

    if original_geometry.is_empty:
        raise ValueError(
            "Encountered empty geometry."
        )

    simplified_geometry = original_geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified_geometry.is_empty:
        raise ValueError(
            "Simplification produced an empty geometry."
        )

    if not simplified_geometry.is_valid:
        repaired_geometry = simplified_geometry.buffer(0)

        if (
            repaired_geometry.is_empty
            or not repaired_geometry.is_valid
        ):
            raise ValueError(
                "Unable to repair invalid simplified geometry."
            )

        simplified_geometry = repaired_geometry

    return {
        "type": "Feature",
        "properties": feature.get(
            "properties",
            {},
        ),
        "geometry": mapping(
            simplified_geometry
        ),
    }


def simplify_file(
    label: str,
    input_path: Path,
    output_path: Path,
    expected_count: int,
    tolerance: float,
) -> None:
    print(
        f"Simplifying {label.lower()}..."
    )

    data = load_geojson(
        input_path
    )

    features = data["features"]

    if len(features) != expected_count:
        raise ValueError(
            f"{label}: expected {expected_count:,} features but found "
            f"{len(features):,}."
        )

    simplified_features = [
        simplify_feature(
            feature,
            tolerance,
        )
        for feature in features
    ]

    if len(simplified_features) != expected_count:
        raise ValueError(
            f"{label}: simplification changed feature count."
        )

    write_geojson(
        output_path,
        simplified_features,
    )

    input_size = input_path.stat().st_size
    output_size = output_path.stat().st_size

    reduction = (
        1 - (output_size / input_size)
    ) * 100

    print(
        f"  Tolerance: {tolerance}"
    )
    print(
        f"  Features:  {len(simplified_features):,}"
    )
    print(
        f"  Before:    {input_size:,} bytes "
        f"({input_size / 1_000_000:.3f} MB)"
    )
    print(
        f"  After:     {output_size:,} bytes "
        f"({output_size / 1_000_000:.3f} MB)"
    )
    print(
        f"  Reduction: {reduction:.2f}%"
    )
    print(
        f"  Output:    {output_path}"
    )
    print("")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Simplifying Peru administrative boundaries...\n"
    )

    for label, config in FILES.items():
        simplify_file(
            label=label,
            input_path=config["input"],
            output_path=config["output"],
            expected_count=config["expected_count"],
            tolerance=config["tolerance"],
        )

    print(
        "Peru runtime GeoJSON simplification complete."
    )


if __name__ == "__main__":
    main()