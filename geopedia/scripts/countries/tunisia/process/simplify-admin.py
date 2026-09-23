"""
Simplify Tunisia's processed administrative GeoJSON for runtime use.

Input
-----
data/intermediate/countries/tunisia/admin/

    governorates.geojson
    delegations.geojson
    municipalities.geojson

Output
------
public/data/countries/tunisia/geojson/

    governorates.geojson
    delegations.geojson
    municipalities.geojson

The intermediate files retain the full processed source geometry. This script
creates smaller runtime copies for GeoPedia's interactive maps.

Simplification is performed directly in the source geographic coordinate
system, so tolerance values are expressed in degrees rather than meters.
Topology is preserved during simplification.

The script validates feature counts, canonical IDs, and output geometry before
writing each runtime file.
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
    / "tunisia"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "tunisia"
    / "geojson"
)


LEVELS = {
    "governorates": {
        "tolerance": 0.0005,
        "expected_count": 24,
        "id_property": "governorate_id",
    },
    "delegations": {
        "tolerance": 0.001,
        "expected_count": 264,
        "id_property": "delegation_id",
    },
    "municipalities": {
        "tolerance": 0.00125,
        "expected_count": 2084,
        "id_property": "municipality_id",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def format_size(size_bytes: int) -> str:
    """Format a byte count as megabytes for console output."""
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def validate_frame(
    frame: gpd.GeoDataFrame,
    expected_count: int,
    id_property: str,
    label: str,
) -> None:
    """Validate feature count, canonical IDs, and source geometry."""
    if len(frame) != expected_count:
        raise ValueError(
            f"{label}: expected {expected_count} features, "
            f"found {len(frame)}."
        )

    if id_property not in frame.columns:
        raise ValueError(
            f"{label}: missing ID property {id_property}."
        )

    if frame[id_property].isna().any():
        raise ValueError(
            f"{label}: {id_property} contains null values."
        )

    if frame[id_property].duplicated().any():
        duplicates = (
            frame.loc[
                frame[id_property].duplicated(keep=False),
                id_property,
            ]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            f"{label}: duplicate {id_property} values: "
            f"{duplicates}"
        )

    if frame.geometry.isna().any():
        raise ValueError(
            f"{label}: contains null geometry."
        )

    if frame.geometry.is_empty.any():
        raise ValueError(
            f"{label}: contains empty geometry."
        )


def validate_simplified_geometry(
    frame: gpd.GeoDataFrame,
    label: str,
) -> None:
    """Verify that simplification did not create missing or empty geometry."""
    if frame.geometry.isna().any():
        raise ValueError(
            f"{label}: simplification produced null geometry."
        )

    if frame.geometry.is_empty.any():
        empty_ids = frame.index[
            frame.geometry.is_empty
        ].tolist()

        raise ValueError(
            f"{label}: simplification produced empty geometry "
            f"for rows {empty_ids}."
        )


def write_compact_geojson(
    frame: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    """Write a GeoDataFrame as compact UTF-8 GeoJSON."""
    geojson = json.loads(
        frame.to_json(
            ensure_ascii=False,
            drop_id=True,
        )
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            geojson,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Simplification
# ---------------------------------------------------------------------------


def simplify_level(
    level: str,
    tolerance: float,
    expected_count: int,
    id_property: str,
) -> None:
    """Simplify and write one Tunisia administrative level."""
    input_path = INPUT_DIR / f"{level}.geojson"
    output_path = OUTPUT_DIR / f"{level}.geojson"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    input_size = input_path.stat().st_size

    frame = gpd.read_file(
        input_path
    )

    validate_frame(
        frame,
        expected_count,
        id_property,
        level.capitalize(),
    )

    simplified = frame.copy()

    simplified.geometry = simplified.geometry.simplify(
        tolerance=tolerance,
        preserve_topology=True,
    )

    validate_simplified_geometry(
        simplified,
        level.capitalize(),
    )

    write_compact_geojson(
        simplified,
        output_path,
    )

    output_size = output_path.stat().st_size

    print()
    print(
        f"========== {level.upper()} =========="
    )

    print(
        f"Input:       {input_path}"
    )

    print(
        f"Input size:  {format_size(input_size)}"
    )

    print(
        f"Tolerance:   {tolerance}°"
    )

    print(
        f"Output size: {format_size(output_size)}"
    )

    print(
        f"Features:    {len(simplified)}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Create simplified runtime GeoJSON for Tunisia's quiz maps."""
    for level, config in LEVELS.items():
        simplify_level(
            level=level,
            tolerance=config["tolerance"],
            expected_count=config["expected_count"],
            id_property=config["id_property"],
        )

    print()
    print(
        "Tunisia administrative simplification complete."
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()