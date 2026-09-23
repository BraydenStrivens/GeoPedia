"""
Simplify Ghana's canonical administrative boundaries for runtime use.

Inputs
------
data/intermediate/countries/ghana/admin/regions.geojson
data/intermediate/countries/ghana/admin/districts.geojson

Outputs
-------
public/data/countries/ghana/geojson/regions.geojson
public/data/countries/ghana/geojson/districts.geojson

The canonical intermediate files remain unchanged. Runtime copies are
simplified with topology preservation to reduce download and rendering costs.

The source data uses EPSG:4326, so simplification tolerances are expressed
in degrees.
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ghana"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "ghana"
    / "geojson"
)


DATASETS = {
    "regions": {
        "filename": "regions.geojson",
        "id_property": "region_id",
        "expected_count": 16,
        "tolerance": 0.002,
    },
    "districts": {
        "filename": "districts.geojson",
        "id_property": "district_id",
        "expected_count": 260,
        "tolerance": 0.001,
    },
}


def load_dataset(
    path: Path,
    expected_count: int,
    id_property: str,
) -> gpd.GeoDataFrame:
    """Load and validate one canonical administrative dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input GeoJSON not found: {path}"
        )

    frame = gpd.read_file(
        path
    )

    if len(frame) != expected_count:
        raise ValueError(
            f"Unexpected feature count for {path.name}: "
            f"expected {expected_count}, found {len(frame)}."
        )

    if id_property not in frame.columns:
        raise ValueError(
            f"{path.name} is missing ID property {id_property!r}."
        )

    if frame[id_property].isna().any():
        raise ValueError(
            f"{path.name} contains null {id_property} values."
        )

    if frame[id_property].duplicated().any():
        raise ValueError(
            f"{path.name} contains duplicate {id_property} values."
        )

    if frame.crs is None:
        raise ValueError(
            f"{path.name} has no CRS."
        )

    if frame.crs.to_epsg() != 4326:
        raise ValueError(
            f"{path.name} has unexpected CRS: {frame.crs}"
        )

    if frame.geometry.isna().any():
        raise ValueError(
            f"{path.name} contains null geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            f"{path.name} contains empty geometry."
        )

    return frame


def simplify_dataset(
    frame: gpd.GeoDataFrame,
    tolerance: float,
) -> gpd.GeoDataFrame:
    """Simplify geometry while preserving each feature's topology."""
    output = frame.copy()

    output.geometry = (
        output.geometry.simplify(
            tolerance=tolerance,
            preserve_topology=True,
        )
    )

    if output.geometry.isna().any():
        raise ValueError(
            "Simplification produced null geometry."
        )

    if output.geometry.is_empty.any():
        raise ValueError(
            "Simplification produced empty geometry."
        )

    return output


def write_compact_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """Write a runtime dataset as compact UTF-8 GeoJSON."""
    geojson = json.loads(
        frame.to_json(
            ensure_ascii=False,
            drop_id=True,
        )
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def main() -> None:
    """Create Ghana's simplified runtime administrative GeoJSON."""
    print(
        "Simplifying Ghana administrative boundaries..."
    )
    print()

    for name, config in DATASETS.items():
        input_path = (
            INPUT_DIR
            / config["filename"]
        )

        output_path = (
            OUTPUT_DIR
            / config["filename"]
        )

        frame = load_dataset(
            input_path,
            config["expected_count"],
            config["id_property"],
        )

        simplified = simplify_dataset(
            frame,
            config["tolerance"],
        )

        write_compact_geojson(
            simplified,
            output_path,
        )

        input_size = (
            input_path.stat().st_size
            / (1024 * 1024)
        )

        output_size = (
            output_path.stat().st_size
            / (1024 * 1024)
        )

        print(
            f"{name.capitalize()}:"
        )
        print(
            f"  Features:  {len(simplified)}"
        )
        print(
            f"  Tolerance: {config['tolerance']}"
        )
        print(
            f"  Input:     {input_size:.2f} MB"
        )
        print(
            f"  Output:    {output_size:.2f} MB"
        )
        print()

    print(
        "Ghana administrative simplification complete."
    )
    print(
        f"Output directory: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()