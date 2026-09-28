from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "argentina"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "argentina"
    / "geojson"
)

PROVINCES_INPUT = (
    INPUT_DIR / "provinces.geojson"
)

DEPARTMENTS_INPUT = (
    INPUT_DIR / "departments.geojson"
)

PROVINCES_OUTPUT = (
    OUTPUT_DIR / "provinces.geojson"
)

DEPARTMENTS_OUTPUT = (
    OUTPUT_DIR / "departments.geojson"
)


PROVINCE_TOLERANCE = 0.01
DEPARTMENT_TOLERANCE = 0.0025


def simplify_layer(
    input_path: Path,
    output_path: Path,
    tolerance: float,
    expected_count: int,
    label: str,
) -> None:
    print(f"Simplifying {label}...")

    gdf = gpd.read_file(
        input_path
    )

    if len(gdf) != expected_count:
        raise ValueError(
            f"Expected {expected_count} {label} features, "
            f"found {len(gdf)}."
        )

    if gdf.crs is None:
        raise ValueError(
            f"{label} layer has no CRS."
        )

    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(
            epsg=4326
        )

    original_invalid = int(
        (~gdf.geometry.is_valid).sum()
    )

    if original_invalid:
        raise ValueError(
            f"{label} source contains "
            f"{original_invalid} invalid geometries."
        )

    gdf["geometry"] = (
        gdf.geometry.simplify(
            tolerance=tolerance,
            preserve_topology=True,
        )
    )

    empty_count = int(
        gdf.geometry.is_empty.sum()
    )

    missing_count = int(
        gdf.geometry.isna().sum()
    )

    invalid_count = int(
        (~gdf.geometry.is_valid).sum()
    )

    if empty_count:
        raise ValueError(
            f"{label} simplification created "
            f"{empty_count} empty geometries."
        )

    if missing_count:
        raise ValueError(
            f"{label} simplification created "
            f"{missing_count} missing geometries."
        )

    if invalid_count:
        raise ValueError(
            f"{label} simplification created "
            f"{invalid_count} invalid geometries."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    gdf.to_file(
        output_path,
        driver="GeoJSON",
    )

    print(
        f"  Features: {len(gdf):,}"
    )

    print(
        f"  Tolerance: {tolerance}"
    )

    print(
        f"  Saved: {output_path}"
    )

    print()


def main() -> None:
    simplify_layer(
        input_path=PROVINCES_INPUT,
        output_path=PROVINCES_OUTPUT,
        tolerance=PROVINCE_TOLERANCE,
        expected_count=24,
        label="provinces",
    )

    simplify_layer(
        input_path=DEPARTMENTS_INPUT,
        output_path=DEPARTMENTS_OUTPUT,
        tolerance=DEPARTMENT_TOLERANCE,
        expected_count=526,
        label="departments",
    )

    print(
        "Argentina admin simplification complete."
    )


if __name__ == "__main__":
    main()