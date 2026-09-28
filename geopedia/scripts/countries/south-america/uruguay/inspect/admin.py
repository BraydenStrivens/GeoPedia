from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "uruguay"
    / "ury_adm_2020_shp"
)

ADM1_PATH = RAW_DIR / "ury_admbnda_adm1_2020.shp"
ADM2_PATH = RAW_DIR / "ury_admbnda_adm2_2020.shp"


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def inspect_layer(label: str, path: Path) -> None:
    print_section(label)

    print(f"Path: {path}")

    if not path.exists():
        raise FileNotFoundError(f"Could not find shapefile: {path}")

    gdf = gpd.read_file(path)

    print(f"Features: {len(gdf)}")
    print(f"CRS: {gdf.crs}")

    print()
    print("Geometry types:")
    print(gdf.geometry.geom_type.value_counts(dropna=False).to_string())

    print()
    print("Columns:")
    for column in gdf.columns:
        if column == gdf.geometry.name:
            continue

        series = gdf[column]

        populated = int(series.notna().sum())
        unique = int(series.nunique(dropna=True))

        print(
            f"  {column}: "
            f"populated={populated}, "
            f"unique={unique}, "
            f"dtype={series.dtype}"
        )

    print()
    print("Sample records:")

    non_geometry_columns = [
        column
        for column in gdf.columns
        if column != gdf.geometry.name
    ]

    sample = gdf[non_geometry_columns].head(15)

    print(sample.to_string(index=False))
    
    if "ADM2_ES" in gdf.columns:
        print()
        print("ADM2 names:")
        for _, row in gdf.iterrows():
            print(
                f"  {row['ADM2_PCODE']}: "
                f"{row['ADM2_ES']} "
                f"({row['ADM1_ES']})"
            )

    print()
    print("Bounds:")
    print(f"  minx: {gdf.total_bounds[0]}")
    print(f"  miny: {gdf.total_bounds[1]}")
    print(f"  maxx: {gdf.total_bounds[2]}")
    print(f"  maxy: {gdf.total_bounds[3]}")

    invalid_count = int((~gdf.geometry.is_valid).sum())
    empty_count = int(gdf.geometry.is_empty.sum())
    missing_count = int(gdf.geometry.isna().sum())

    print()
    print("Geometry health:")
    print(f"  Invalid: {invalid_count}")
    print(f"  Empty: {empty_count}")
    print(f"  Missing: {missing_count}")


def main() -> None:
    print("Inspecting Uruguay administrative boundary data...")

    inspect_layer(
        "ADM1 — Departments",
        ADM1_PATH,
    )

    inspect_layer(
        "ADM2 — Municipalities",
        ADM2_PATH,
    )

    print_section("DONE")
    print("Uruguay administrative inspection complete.")


if __name__ == "__main__":
    main()