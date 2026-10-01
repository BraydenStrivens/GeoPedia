"""
Simplify Vietnam's post-reform administrative GeoJSON files.

This script reads the processed post-reform administrative layers created by:

    scripts/countries/asia/vietnam/process/post-reform-admin.py

Inputs:
    data/intermediate/countries/vietnam/post-reform-admin/
        provinces.geojson
        communes.geojson

Outputs:
    public/data/countries/vietnam/geojson/
        post-reform-provinces.geojson
        post-reform-communes.geojson

The post-reform data represents Vietnam's two-tier administrative structure.
There is no district layer in this dataset.

Simplification uses Mapshaper's percentage-based simplification with
keep-shapes enabled. A 10% retention rate is used as the initial target.
The resulting files are validated for expected feature counts, unique IDs,
non-empty geometry, and valid Polygon/MultiPolygon geometry.

Requirements:
    - Python 3
    - GeoPandas
    - Shapely
    - Mapshaper available through npx

Run from the GeoPedia project root:

    python scripts/countries/asia/vietnam/process/simplify-post-reform-admin.py
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

import geopandas as gpd


INPUT_DIR = Path(
    "data/intermediate/countries/vietnam/post-reform-admin"
)

OUTPUT_DIR = Path(
    "public/data/countries/vietnam/geojson"
)

SIMPLIFY_PERCENT = 10

LAYERS = (
    {
        "name": "Provinces",
        "input": INPUT_DIR / "provinces.geojson",
        "output": OUTPUT_DIR / "post-reform-provinces.geojson",
        "id_property": "province_id",
        "expected_count": 34,
    },
    {
        "name": "Commune-level units",
        "input": INPUT_DIR / "communes.geojson",
        "output": OUTPUT_DIR / "post-reform-communes.geojson",
        "id_property": "commune_id",
        "expected_count": 3_321,
    },
)


def count_coordinates(value: object) -> int:
    """Recursively count coordinate positions in GeoJSON coordinates."""
    if not isinstance(value, list):
        return 0

    if (
        len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    ):
        return 1

    return sum(count_coordinates(item) for item in value)


def inspect_geojson(path: Path) -> tuple[int, int]:
    """Return file size in bytes and total coordinate count."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    coordinate_count = sum(
        count_coordinates(feature["geometry"]["coordinates"])
        for feature in data["features"]
    )

    return path.stat().st_size, coordinate_count


def repair_polygonal_geometry(geometry):
    """
    Repair invalid geometry while retaining polygonal area only.

    Mapshaper simplification can leave small self-intersections in otherwise
    valid administrative polygons. make_valid() may represent collapsed
    boundaries as zero-area LineString components inside a GeometryCollection.
    GeoPedia only needs polygonal area, so those remnants are discarded.
    """
    if geometry.is_valid:
        return geometry

    repaired = make_valid(geometry)

    if isinstance(repaired, (Polygon, MultiPolygon)):
        return repaired

    if isinstance(repaired, GeometryCollection):
        polygon_parts = []

        for part in repaired.geoms:
            if isinstance(part, Polygon):
                polygon_parts.append(part)

            elif isinstance(part, MultiPolygon):
                polygon_parts.extend(part.geoms)

        if not polygon_parts:
            raise ValueError(
                "Geometry repair produced no polygonal components."
            )

        repaired = unary_union(polygon_parts)

        if isinstance(repaired, (Polygon, MultiPolygon)):
            return repaired

    raise ValueError(
        "Geometry repair did not produce Polygon/MultiPolygon: "
        f"{repaired.geom_type}"
    )
    

def validate_layer(
    path: Path,
    *,
    name: str,
    id_property: str,
    expected_count: int,
) -> None:
    """Validate a simplified administrative layer."""
    gdf = gpd.read_file(path)

    if len(gdf) != expected_count:
        raise ValueError(
            f"{name}: expected {expected_count:,} features, "
            f"found {len(gdf):,}."
        )

    if id_property not in gdf.columns:
        raise ValueError(
            f"{name}: missing ID property {id_property!r}."
        )

    if gdf[id_property].isna().any():
        raise ValueError(
            f"{name}: contains missing {id_property} values."
        )

    if gdf[id_property].astype(str).duplicated().any():
        raise ValueError(
            f"{name}: contains duplicate {id_property} values."
        )

    if gdf.geometry.isna().any():
        raise ValueError(
            f"{name}: contains missing geometries."
        )

    if gdf.geometry.is_empty.any():
        raise ValueError(
            f"{name}: contains empty geometries."
        )

    invalid_count = int((~gdf.geometry.is_valid).sum())

    if invalid_count:
        raise ValueError(
            f"{name}: contains {invalid_count:,} invalid geometries."
        )

    bad_types = sorted(
        set(gdf.geometry.geom_type)
        - {"Polygon", "MultiPolygon"}
    )

    if bad_types:
        raise ValueError(
            f"{name}: unexpected geometry types: {bad_types}"
        )


def simplify_layer(
    *,
    name: str,
    input_path: Path,
    output_path: Path,
    id_property: str,
    expected_count: int,
) -> None:
    """Simplify one GeoJSON layer with Mapshaper."""
    print()
    print(f"Simplifying {name}...")

    before_size, before_coordinates = inspect_geojson(input_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_output = Path(temp_dir) / output_path.name

        command = [
            "npx.cmd",
            "mapshaper",
            str(input_path),
            "-simplify",
            f"{SIMPLIFY_PERCENT}%",
            "keep-shapes",
            "-o",
            "format=geojson",
            "precision=0.000001",
            str(temp_output),
        ]

        result = subprocess.run(
            command,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Mapshaper failed while simplifying {name}."
            )
            
        # Mapshaper can leave a small number of self-intersections after
        # simplification. Repair those defects and discard any zero-area
        # line/point remnants produced by make_valid().
        simplified = gpd.read_file(temp_output)

        invalid_before_repair = int(
            (~simplified.geometry.is_valid).sum()
        )

        if invalid_before_repair:
            simplified["geometry"] = simplified.geometry.map(
                repair_polygonal_geometry
            )

            simplified.to_file(
                temp_output,
                driver="GeoJSON",
            )

            print(
                f"  Repaired {invalid_before_repair:,} "
                "post-simplification geometries"
            )

        validate_layer(
            temp_output,
            name=name,
            id_property=id_property,
            expected_count=expected_count,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_output.replace(output_path)

    after_size, after_coordinates = inspect_geojson(output_path)

    size_retained = (
        after_size / before_size * 100
        if before_size
        else 0
    )

    coordinates_retained = (
        after_coordinates / before_coordinates * 100
        if before_coordinates
        else 0
    )

    print(f"  Features: {expected_count:,}")
    print(
        f"  Size: "
        f"{before_size / 1024 / 1024:,.2f} MB -> "
        f"{after_size / 1024 / 1024:,.2f} MB "
        f"({size_retained:.1f}% retained)"
    )
    print(
        f"  Coordinates: "
        f"{before_coordinates:,} -> "
        f"{after_coordinates:,} "
        f"({coordinates_retained:.1f}% retained)"
    )
    print(f"  Wrote: {output_path}")


def main() -> None:
    """Simplify all post-reform administrative layers."""
    print(
        "Simplifying Vietnam post-reform administrative data..."
    )
    print(f"Mapshaper retention: {SIMPLIFY_PERCENT}%")

    for layer in LAYERS:
        if not layer["input"].exists():
            raise FileNotFoundError(
                f"Missing input: {layer['input']}"
            )

        simplify_layer(
            name=layer["name"],
            input_path=layer["input"],
            output_path=layer["output"],
            id_property=layer["id_property"],
            expected_count=layer["expected_count"],
        )

    print()
    print(
        "Vietnam post-reform administrative simplification complete."
    )


if __name__ == "__main__":
    main()