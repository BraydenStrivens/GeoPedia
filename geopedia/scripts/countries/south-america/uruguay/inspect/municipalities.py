from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

MUNICIPALITIES_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "uruguay"
    / "municipios_20250507"
    / "municipios_20250507.shp"
)


def main() -> None:
    print("Inspecting Uruguay municipality data...")
    print()

    if not MUNICIPALITIES_PATH.exists():
        raise FileNotFoundError(
            f"Could not find shapefile: {MUNICIPALITIES_PATH}"
        )

    gdf = gpd.read_file(MUNICIPALITIES_PATH)

    print("=" * 80)
    print("MUNICIPALITIES")
    print("=" * 80)

    print(f"Path: {MUNICIPALITIES_PATH}")
    print(f"Features: {len(gdf)}")
    print(f"CRS: {gdf.crs}")

    print()
    print("Geometry types:")
    print(
        gdf.geometry.geom_type
        .value_counts(dropna=False)
        .to_string()
    )

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

    print(
        gdf[non_geometry_columns]
        .head(25)
        .to_string(index=False)
    )

    print()
    print("Unique values by column:")

    for column in non_geometry_columns:
        unique_count = gdf[column].nunique(dropna=True)

        if unique_count <= 30:
            print()
            print(f"{column}:")
            values = (
                gdf[column]
                .dropna()
                .astype(str)
                .sort_values()
                .unique()
            )

            for value in values:
                print(f"  {value}")

    print()
    print("Bounds:")
    minx, miny, maxx, maxy = gdf.total_bounds

    print(f"  minx: {minx}")
    print(f"  miny: {miny}")
    print(f"  maxx: {maxx}")
    print(f"  maxy: {maxy}")

    invalid_count = int((~gdf.geometry.is_valid).sum())
    empty_count = int(gdf.geometry.is_empty.sum())
    missing_count = int(gdf.geometry.isna().sum())

    print()
    print("Geometry health:")
    print(f"  Invalid: {invalid_count}")
    print(f"  Empty: {empty_count}")
    print(f"  Missing: {missing_count}")

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print("Uruguay municipality inspection complete.")


if __name__ == "__main__":
    main()