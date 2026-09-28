"""
Simplify South Africa's reconstructed postcode GeoJSON datasets.

Each postcode level is simplified independently from its unsimplified
intermediate GeoJSON using Mapshaper. This preserves shared topology within
each dataset while substantially reducing the runtime file size.

The four-digit reconstruction remains the canonical high-resolution postcode
geography. The three-, two-, and one-digit intermediate datasets were derived
from it by dissolving postcode prefixes before simplification.

Inputs:

    data/intermediate/countries/south-africa/postcodes/
    postcodes-4.geojson
    postcodes-3.geojson
    postcodes-2.geojson
    postcodes-1.geojson

Outputs:

    public/data/countries/south-africa/geojson/
    postcodes-4.geojson
    postcodes-3.geojson
    postcodes-2.geojson
    postcodes-1.geojson

Simplification tolerances:

    4-digit: 0.0010 degrees
    3-digit: 0.0015 degrees
    2-digit: 0.0025 degrees
    1-digit: 0.0050 degrees

Mapshaper is invoked through npx so the script uses the project's available
Mapshaper installation/tooling.

Run from the GeoPedia project root:

    python scripts/countries/south-africa/process/simplify-postcodes.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


INPUT_DIRECTORY = Path(
    "data/intermediate/countries/south-africa/postcodes"
)

OUTPUT_DIRECTORY = Path(
    "public/data/countries/south-africa/geojson"
)

TOLERANCES = {
    4: 0.0010,
    3: 0.0015,
    2: 0.0025,
    1: 0.0050,
}


def load_feature_collection(
    path: Path,
) -> dict[str, Any]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file not found: {path}"
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


def file_size_mb(
    path: Path,
) -> float:
    """Return a file's size in megabytes."""
    return (
        path.stat().st_size
        / 1024
        / 1024
    )


def geometry_summary(
    data: dict[str, Any],
) -> tuple[
    int,
    int,
    int,
    int,
]:
    """
    Return feature, Polygon, MultiPolygon, and other geometry counts.
    """
    features = data[
        "features"
    ]

    polygon_count = 0
    multipolygon_count = 0
    other_count = 0

    for feature in features:
        geometry = feature.get(
            "geometry"
        )

        if not isinstance(
            geometry,
            dict,
        ):
            other_count += 1
            continue

        geometry_type = geometry.get(
            "type"
        )

        if geometry_type == "Polygon":
            polygon_count += 1

        elif geometry_type == "MultiPolygon":
            multipolygon_count += 1

        else:
            other_count += 1

    return (
        len(features),
        polygon_count,
        multipolygon_count,
        other_count,
    )


def expected_property(
    digits: int,
) -> str:
    """Return the identifying property for a postcode level."""
    if digits == 4:
        return "postcode"

    return f"prefix_{digits}"


def feature_ids(
    data: dict[str, Any],
    property_name: str,
) -> set[str]:
    """Return and validate all feature identifiers for one dataset."""
    identifiers: set[str] = set()

    for feature in data[
        "features"
    ]:
        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                "Feature has no valid properties object."
            )

        value = properties.get(
            property_name
        )

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"Feature is missing string property "
                f"{property_name!r}."
            )

        if value in identifiers:
            raise ValueError(
                f"Duplicate {property_name}: {value}"
            )

        identifiers.add(
            value
        )

    return identifiers


def validate_output(
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    digits: int,
) -> None:
    """
    Verify simplification preserved features and their identifiers.
    """
    property_name = expected_property(
        digits
    )

    input_ids = feature_ids(
        input_data,
        property_name,
    )

    output_ids = feature_ids(
        output_data,
        property_name,
    )

    if input_ids != output_ids:
        missing = sorted(
            input_ids
            - output_ids
        )

        unexpected = sorted(
            output_ids
            - input_ids
        )

        raise RuntimeError(
            f"{digits}-digit simplification changed "
            f"the feature identifiers.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    (
        _,
        _,
        _,
        other_count,
    ) = geometry_summary(
        output_data
    )

    if other_count:
        raise RuntimeError(
            f"{digits}-digit output contains "
            f"{other_count:,} non-polygon geometries."
        )


def simplify_level(
    digits: int,
    tolerance: float,
) -> None:
    """Simplify one postcode level with Mapshaper."""
    input_path = (
        INPUT_DIRECTORY
        / f"postcodes-{digits}.geojson"
    )

    output_path = (
        OUTPUT_DIRECTORY
        / f"postcodes-{digits}.geojson"
    )

    print()
    print(
        "=" * 72
    )
    print(
        f"{digits}-DIGIT POSTCODES"
    )
    print(
        "=" * 72
    )

    input_data = load_feature_collection(
        input_path
    )

    (
        input_features,
        input_polygons,
        input_multipolygons,
        input_other,
    ) = geometry_summary(
        input_data
    )

    if input_other:
        raise ValueError(
            f"{input_path} contains "
            f"{input_other:,} non-polygon geometries."
        )

    input_size = file_size_mb(
        input_path
    )

    print(
        f"Input:             {input_path}"
    )
    print(
        f"Tolerance:         {tolerance:g} degrees"
    )
    print(
        f"Features:          {input_features:,}"
    )
    print(
        f"Polygons:          {input_polygons:,}"
    )
    print(
        f"MultiPolygons:     {input_multipolygons:,}"
    )
    print(
        f"Input size:        {input_size:.2f} MB"
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "npx",
        "mapshaper",
        str(input_path),
        "-simplify",
        f"dp",
        f"interval={tolerance}",
        "keep-shapes",
        "-o",
        str(output_path),
        "format=geojson",
        "precision=0.000001",
        "force",
    ]

    print()
    print(
        "Running Mapshaper..."
    )

    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            shell=True,
        )

    except OSError as error:
        raise RuntimeError(
            "Unable to start Mapshaper through npx."
        ) from error

    if result.stdout.strip():
        print(
            result.stdout.strip()
        )

    if result.returncode != 0:
        if result.stderr.strip():
            print(
                result.stderr.strip()
            )

        raise RuntimeError(
            f"Mapshaper failed while simplifying "
            f"{digits}-digit postcodes "
            f"(exit code {result.returncode})."
        )

    if result.stderr.strip():
        print(
            result.stderr.strip()
        )

    if not output_path.exists():
        raise RuntimeError(
            f"Mapshaper completed without creating "
            f"{output_path}."
        )

    output_data = load_feature_collection(
        output_path
    )

    validate_output(
        input_data,
        output_data,
        digits,
    )

    (
        output_features,
        output_polygons,
        output_multipolygons,
        output_other,
    ) = geometry_summary(
        output_data
    )

    output_size = file_size_mb(
        output_path
    )

    reduction = (
        (
            1.0
            - output_size
            / input_size
        )
        * 100.0
        if input_size > 0
        else 0.0
    )

    print()
    print("Result")
    print("------")
    print(
        f"Features:          {output_features:,}"
    )
    print(
        f"Polygons:          {output_polygons:,}"
    )
    print(
        f"MultiPolygons:     {output_multipolygons:,}"
    )
    print(
        f"Other geometries:  {output_other:,}"
    )
    print(
        f"Output size:       {output_size:.2f} MB"
    )
    print(
        f"Size reduction:    {reduction:.1f}%"
    )
    print(
        f"Wrote:             {output_path}"
    )


def main() -> None:
    """Simplify all South African postcode datasets."""
    print(
        "Simplifying South African postcode geography..."
    )

    for digits in (
        4,
        3,
        2,
        1,
    ):
        simplify_level(
            digits,
            TOLERANCES[
                digits
            ],
        )

    print()
    print(
        "=" * 72
    )
    print(
        "All postcode datasets simplified successfully."
    )
    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()