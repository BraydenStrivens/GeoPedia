"""
Simplifies Bolivia's processed administrative boundaries for runtime use.

Inputs:
    data/intermediate/countries/bolivia/admin/departments.geojson
    data/intermediate/countries/bolivia/admin/provinces.geojson
    data/intermediate/countries/bolivia/admin/municipalities.geojson

Outputs:
    public/data/countries/bolivia/geojson/departments.geojson
    public/data/countries/bolivia/geojson/provinces.geojson
    public/data/countries/bolivia/geojson/municipalities.geojson
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape


INTERMEDIATE_DIRECTORY = Path(
    "data/intermediate/countries/bolivia/admin"
)

RUNTIME_DIRECTORY = Path(
    "public/data/countries/bolivia/geojson"
)

LAYERS = [
    {
        "name": "Departments",
        "input": INTERMEDIATE_DIRECTORY / "departments.geojson",
        "output": RUNTIME_DIRECTORY / "departments.geojson",
        "tolerance": 0.01,
        "expected_count": 9,
    },
    {
        "name": "Provinces",
        "input": INTERMEDIATE_DIRECTORY / "provinces.geojson",
        "output": RUNTIME_DIRECTORY / "provinces.geojson",
        "tolerance": 0.005,
        "expected_count": 112,
    },
    {
        "name": "Municipalities",
        "input": INTERMEDIATE_DIRECTORY / "municipalities.geojson",
        "output": RUNTIME_DIRECTORY / "municipalities.geojson",
        "tolerance": 0.0025,
        "expected_count": 339,
    },
]


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
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
            f"{path} does not contain a valid features array."
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
    geometry_data = feature.get(
        "geometry"
    )

    if not isinstance(
        geometry_data,
        dict,
    ):
        raise ValueError(
            "Feature has invalid geometry."
        )

    geometry = shape(
        geometry_data
    )

    if geometry.is_empty:
        raise ValueError(
            "Feature has empty geometry."
        )

    simplified = geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified.is_empty:
        raise ValueError(
            "Simplification produced empty geometry."
        )

    if not simplified.is_valid:
        simplified = simplified.buffer(
            0
        )

    if (
        simplified.is_empty
        or not simplified.is_valid
    ):
        raise ValueError(
            "Unable to produce valid simplified geometry."
        )

    return {
        "type": "Feature",
        "properties": feature.get(
            "properties",
            {},
        ),
        "geometry": mapping(
            simplified
        ),
    }


def process_layer(
    name: str,
    input_path: Path,
    output_path: Path,
    tolerance: float,
    expected_count: int,
) -> None:
    data = load_geojson(
        input_path
    )

    features = data[
        "features"
    ]

    if len(features) != expected_count:
        raise ValueError(
            f"{name}: expected {expected_count} features "
            f"but found {len(features)}."
        )

    simplified_features = [
        simplify_feature(
            feature,
            tolerance,
        )
        for feature in features
    ]

    write_geojson(
        output_path,
        simplified_features,
    )

    input_size = (
        input_path.stat().st_size
    )

    output_size = (
        output_path.stat().st_size
    )

    reduction = (
        1 - output_size / input_size
    ) * 100

    print(
        f"{name}:"
    )

    print(
        f"  Features:   {len(simplified_features)}"
    )

    print(
        f"  Tolerance:  {tolerance}"
    )

    print(
        f"  Input:      {input_size / 1_000_000:.3f} MB"
    )

    print(
        f"  Runtime:    {output_size / 1_000_000:.3f} MB"
    )

    print(
        f"  Reduction:  {reduction:.1f}%"
    )

    print(
        f"  Output:     {output_path}"
    )

    print()


def main() -> None:
    print(
        "Simplifying Bolivia administrative boundaries...\n"
    )

    for layer in LAYERS:
        process_layer(
            name=layer["name"],
            input_path=layer["input"],
            output_path=layer["output"],
            tolerance=layer["tolerance"],
            expected_count=layer["expected_count"],
        )

    print(
        "Bolivia administrative simplification complete."
    )


if __name__ == "__main__":
    main()