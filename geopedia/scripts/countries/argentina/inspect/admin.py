from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "argentina"
    / "arg_adm_unhcr2017_shp"
)

LAYERS = {
    "ADM1 / Provinces": (
        RAW_DIR / "arg_admbnda_adm1_unhcr2017.shp"
    ),
    "ADM2 / Departments": (
        RAW_DIR / "arg_admbnda_adm2_unhcr2017.shp"
    ),
}


def print_column_values(
    gdf: gpd.GeoDataFrame,
) -> None:
    non_geometry_columns = [
        column
        for column in gdf.columns
        if column != gdf.geometry.name
    ]

    for column in non_geometry_columns:
        unique_count = int(
            gdf[column].nunique(
                dropna=True,
            )
        )

        if unique_count > 100:
            continue

        print()
        print(
            f"{column} "
            f"({unique_count:,} unique):"
        )

        values = (
            gdf[column]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .sort_values()
        )

        for value in values:
            print(f"  {value}")


def inspect_layer(
    label: str,
    path: Path,
) -> None:
    print("=" * 80)
    print(label)
    print("=" * 80)
    print(f"Source: {path}")
    print()

    gdf = gpd.read_file(path)

    print(f"Features: {len(gdf):,}")
    print(f"CRS: {gdf.crs}")
    print()

    print("Geometry types:")
    print(
        gdf.geometry.geom_type
        .value_counts()
        .to_string()
    )

    print()
    print("Columns:")

    for column in gdf.columns:
        if column == gdf.geometry.name:
            continue

        populated = int(
            gdf[column].notna().sum()
        )

        unique = int(
            gdf[column].nunique(
                dropna=True,
            )
        )

        print(
            f"  {column}: "
            f"{populated:,} populated, "
            f"{unique:,} unique"
        )

    bounds = gdf.total_bounds

    print()
    print(
        "Bounds: "
        f"[{bounds[0]}, {bounds[1]}, "
        f"{bounds[2]}, {bounds[3]}]"
    )

    invalid_count = int(
        (~gdf.geometry.is_valid).sum()
    )

    empty_count = int(
        gdf.geometry.is_empty.sum()
    )

    missing_count = int(
        gdf.geometry.isna().sum()
    )

    print()
    print(
        f"Invalid geometries: "
        f"{invalid_count:,}"
    )
    print(
        f"Empty geometries: "
        f"{empty_count:,}"
    )
    print(
        f"Missing geometries: "
        f"{missing_count:,}"
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
        .head(10)
        .to_string(index=False)
    )

    print_column_values(gdf)
    
    if "ADM2_PCODE" in gdf.columns:
        print()
        print("ADM2 feature counts by province:")

        counts = (
            gdf.groupby(
                ["ADM1_PCODE", "ADM1_ES"]
            )
            .size()
            .reset_index(name="count")
            .sort_values("ADM1_PCODE")
        )

        print(
            counts.to_string(
                index=False
            )
        )

        print()
        print(
            "Ciudad de Buenos Aires ADM2 features:"
        )

        caba = gdf[
            gdf["ADM1_PCODE"] == "AR002"
        ][
            [
                "ADM2_PCODE",
                "ADM2_ES",
                "ADM2_REF",
            ]
        ].sort_values("ADM2_PCODE")

        print(
            caba.to_string(
                index=False
            )
        )

    print()
    print()


def main() -> None:
    for label, path in LAYERS.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Missing shapefile: {path}"
            )

        inspect_layer(
            label,
            path,
        )


if __name__ == "__main__":
    main()