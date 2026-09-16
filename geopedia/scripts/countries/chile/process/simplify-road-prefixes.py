"""
Simplify Chile road-prefix GeoJSON for GeoPedia runtime use.

Input
-----
data/intermediate/countries/chile/road-prefixes.geojson

Output
------
public/data/countries/chile/geojson/road-prefixes.geojson

Run with:

    python scripts/countries/chile/process/simplify-road-prefixes.py
"""

import json
from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "road-prefixes.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "chile"
    / "geojson"
    / "road-prefixes.geojson"
)


TOLERANCE = 0.02
EXPECTED_FEATURES = 23


def size_mb(
    path: Path,
) -> float:
    return (
        path.stat().st_size
        / 1024
        / 1024
    )


def validate_geometry(
    frame: gpd.GeoDataFrame,
) -> None:
    if len(frame) != EXPECTED_FEATURES:
        raise ValueError(
            f"Expected {EXPECTED_FEATURES} features, "
            f"found {len(frame)}."
        )

    if frame.geometry.isna().any():
        raise ValueError(
            "Simplified GeoJSON contains null geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            "Simplified GeoJSON contains empty geometry."
        )

    invalid = ~frame.geometry.is_valid

    if invalid.any():
        invalid_ids = frame.loc[
            invalid,
            "road_prefix_id",
        ].tolist()

        raise ValueError(
            "Simplified GeoJSON contains invalid "
            f"geometry: {invalid_ids}"
        )

    geometry_types = set(
        frame.geometry.geom_type
    )

    allowed_types = {
        "Polygon",
        "MultiPolygon",
    }

    unexpected = (
        geometry_types - allowed_types
    )

    if unexpected:
        raise ValueError(
            "Unexpected geometry types after "
            f"simplification: {sorted(unexpected)}"
        )


def write_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    output_frame = frame.copy()

    output_frame["road_prefixes"] = (
        output_frame["road_prefixes"].apply(
            lambda value: (
                value.tolist()
                if hasattr(value, "tolist")
                else value
            )
        )
    )

    geojson = json.loads(
        output_frame.to_json(
            drop_id=True
        )
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        
        
def main() -> None:
    print(
        "Simplifying Chile road-prefix GeoJSON..."
    )

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}"
        )

    frame = gpd.read_file(
        INPUT_PATH
    )

    if frame.crs is None:
        raise ValueError(
            "Road-prefix GeoJSON has no CRS."
        )

    if len(frame) != EXPECTED_FEATURES:
        raise ValueError(
            f"Expected {EXPECTED_FEATURES} input "
            f"features, found {len(frame)}."
        )

    print()
    print(
        f"Input:      {INPUT_PATH}"
    )
    print(
        f"Input size: {size_mb(INPUT_PATH):.2f} MB"
    )
    print(
        f"Tolerance:  {TOLERANCE}°"
    )

    output_frame = frame.copy()

    output_frame.geometry = (
        output_frame.geometry.simplify(
            tolerance=TOLERANCE,
            preserve_topology=True,
        )
    )

    validate_geometry(
        output_frame
    )

    write_geojson(
        output_frame,
        OUTPUT_PATH,
    )

    print(
        f"Output size: {size_mb(OUTPUT_PATH):.2f} MB"
    )
    print(
        f"Features:    {len(output_frame)}"
    )

    print()
    print(
        "Chile road-prefix simplification complete."
    )
    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()