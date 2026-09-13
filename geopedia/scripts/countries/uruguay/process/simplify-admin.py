from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "uruguay"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "uruguay"
    / "geojson"
)

DEPARTMENTS_INPUT = INPUT_DIR / "departments.geojson"
MUNICIPALITIES_INPUT = INPUT_DIR / "municipalities.geojson"

DEPARTMENTS_OUTPUT = OUTPUT_DIR / "departments.geojson"
MUNICIPALITIES_OUTPUT = OUTPUT_DIR / "municipalities.geojson"


DEPARTMENT_TOLERANCE = 0.01
MUNICIPALITY_TOLERANCE = 0.0025


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / 1_000_000


def simplify_layer(
    label: str,
    input_path: Path,
    output_path: Path,
    tolerance: float,
    expected_count: int,
) -> None:
    print(f"Simplifying {label}...")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Could not find input file: {input_path}"
        )

    gdf = gpd.read_file(input_path)

    if len(gdf) != expected_count:
        raise ValueError(
            f"{label}: expected {expected_count} features, "
            f"found {len(gdf)}."
        )

    if gdf.crs is None:
        raise ValueError(
            f"{label}: input has no CRS."
        )

    gdf = gdf.to_crs("EPSG:4326")

    input_size = file_size_mb(input_path)

    simplified = gdf.copy()

    simplified["geometry"] = simplified.geometry.simplify(
        tolerance=tolerance,
        preserve_topology=True,
    )

    invalid_count = int(
        (~simplified.geometry.is_valid).sum()
    )
    empty_count = int(
        simplified.geometry.is_empty.sum()
    )
    missing_count = int(
        simplified.geometry.isna().sum()
    )

    if invalid_count:
        raise ValueError(
            f"{label}: simplification produced "
            f"{invalid_count} invalid geometries."
        )

    if empty_count:
        raise ValueError(
            f"{label}: simplification produced "
            f"{empty_count} empty geometries."
        )

    if missing_count:
        raise ValueError(
            f"{label}: simplification produced "
            f"{missing_count} missing geometries."
        )

    if len(simplified) != expected_count:
        raise ValueError(
            f"{label}: feature count changed during simplification."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    simplified.to_file(
        output_path,
        driver="GeoJSON",
    )

    output_size = file_size_mb(output_path)

    reduction = (
        (1 - output_size / input_size) * 100
        if input_size > 0
        else 0
    )

    print(
        f"  Features: {len(simplified)}"
    )
    print(
        f"  Tolerance: {tolerance}"
    )
    print(
        f"  Input size: {input_size:.3f} MB"
    )
    print(
        f"  Runtime size: {output_size:.3f} MB"
    )
    print(
        f"  Reduction: {reduction:.1f}%"
    )
    print()


def main() -> None:
    print(
        "Simplifying Uruguay administrative boundaries..."
    )
    print()

    simplify_layer(
        label="Departments",
        input_path=DEPARTMENTS_INPUT,
        output_path=DEPARTMENTS_OUTPUT,
        tolerance=DEPARTMENT_TOLERANCE,
        expected_count=19,
    )

    simplify_layer(
        label="Municipalities",
        input_path=MUNICIPALITIES_INPUT,
        output_path=MUNICIPALITIES_OUTPUT,
        tolerance=MUNICIPALITY_TOLERANCE,
        expected_count=136,
    )

    print("Complete.")
    print(
        f"Output directory: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()