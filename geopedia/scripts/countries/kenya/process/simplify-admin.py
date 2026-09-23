"""
Simplify Kenya's canonical administrative GeoJSON for GeoPedia's runtime maps.

The canonical intermediate files remain unchanged. Simplified copies are
written to the public runtime data directory with all canonical hierarchy
properties preserved.

Inputs:
    data/intermediate/countries/kenya/admin/counties.geojson
    data/intermediate/countries/kenya/admin/sub-counties.geojson
    data/intermediate/countries/kenya/admin/wards.geojson

Outputs:
    public/data/countries/kenya/geojson/counties.geojson
    public/data/countries/kenya/geojson/sub-counties.geojson
    public/data/countries/kenya/geojson/wards.geojson
"""

import json
from pathlib import Path

from shapely.geometry import mapping, shape


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "kenya"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "kenya"
    / "geojson"
)

DATASETS = [
    {
        "name": "Counties",
        "filename": "counties.geojson",
        "tolerance": 0.002,
        "expected_count": 47,
    },
    {
        "name": "Sub-counties",
        "filename": "sub-counties.geojson",
        "tolerance": 0.001,
        "expected_count": 290,
    },
    {
        "name": "Wards",
        "filename": "wards.geojson",
        "tolerance": 0.00075,
        "expected_count": 1452,
    },
]


def load_geojson(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    return data


def simplify_feature(
    feature: dict,
    tolerance: float,
) -> dict:
    """Simplify one feature while preserving topology and properties."""
    geometry = shape(feature["geometry"])

    if geometry.is_empty:
        raise ValueError(
            "Cannot simplify an empty geometry."
        )

    simplified = geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified.is_empty:
        raise ValueError(
            "Simplification produced an empty geometry."
        )

    return {
        "type": "Feature",
        "properties": feature["properties"],
        "geometry": mapping(simplified),
    }


def write_geojson(
    path: Path,
    features: list[dict],
) -> None:
    """Write a compact runtime GeoJSON FeatureCollection."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def format_size(size: int) -> str:
    """Format a byte count as megabytes."""
    return f"{size / (1024 * 1024):.2f} MB"


def process_dataset(dataset: dict) -> None:
    """Simplify and write one administrative dataset."""
    input_path = INPUT_DIR / dataset["filename"]
    output_path = OUTPUT_DIR / dataset["filename"]

    data = load_geojson(input_path)
    features = data["features"]

    if len(features) != dataset["expected_count"]:
        raise ValueError(
            f"{dataset['name']} has {len(features)} features; "
            f"expected {dataset['expected_count']}."
        )

    simplified_features = [
        simplify_feature(
            feature,
            dataset["tolerance"],
        )
        for feature in features
    ]

    write_geojson(
        output_path,
        simplified_features,
    )

    input_size = input_path.stat().st_size
    output_size = output_path.stat().st_size

    reduction = (
        (1 - output_size / input_size) * 100
        if input_size
        else 0
    )

    print(dataset["name"])
    print(
        f"  Features:  {len(simplified_features)}"
    )
    print(
        f"  Tolerance: {dataset['tolerance']}"
    )
    print(
        f"  Input:     {format_size(input_size)}"
    )
    print(
        f"  Output:    {format_size(output_size)}"
    )
    print(
        f"  Reduction: {reduction:.1f}%"
    )
    print()


def main() -> None:
    """Create Kenya's simplified runtime administrative GeoJSON files."""
    print("Simplifying Kenya administrative boundaries...")
    print()

    for dataset in DATASETS:
        process_dataset(dataset)

    print("Kenya administrative simplification complete.")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()