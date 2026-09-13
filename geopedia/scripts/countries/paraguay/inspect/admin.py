"""
Inspects Paraguay's ADM1 and ADM2 administrative boundary shapefiles.

Expected hierarchy:
    ADM1 -> 18 department-level units
            (17 departments + Asunción)
    ADM2 -> 259 districts

Input directory:
    data/raw/countries/paraguay/pry_adm_dgeec_2020_shp
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


RAW_DIRECTORY = Path(
    "data/raw/countries/paraguay/pry_adm_dgeec_2020_shp"
)

ADM1_PATH = (
    RAW_DIRECTORY
    / "pry_admbnda_adm1_DGEEC_2020.shp"
)

ADM2_PATH = (
    RAW_DIRECTORY
    / "pry_admbnda_adm2_DGEEC_2020.shp"
)


def print_separator() -> None:
    print()
    print("=" * 80)
    print()


def inspect_layer(
    label: str,
    path: Path,
) -> None:
    print_separator()

    print(label)
    print(path)

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {path}"
        )

    gdf = gpd.read_file(
        path
    )

    print()
    print(f"Features: {len(gdf):,}")
    print(f"CRS:      {gdf.crs}")

    print()
    print("Geometry types:")

    geometry_counts = (
        gdf.geometry
        .geom_type
        .value_counts(
            dropna=False
        )
    )

    for geometry_type, count in geometry_counts.items():
        print(
            f"  {geometry_type}: {count:,}"
        )

    print()
    print("Columns:")

    for column in gdf.columns:
        if column == gdf.geometry.name:
            continue

        series = gdf[
            column
        ]

        populated = (
            series.notna().sum()
        )

        unique = (
            series.nunique(
                dropna=True
            )
        )

        print(
            f"  {column}"
        )

        print(
            f"    dtype:     {series.dtype}"
        )

        print(
            f"    populated: {populated:,}/{len(gdf):,}"
        )

        print(
            f"    unique:    {unique:,}"
        )

        sample_values = (
            series
            .dropna()
            .astype(str)
            .drop_duplicates()
            .head(10)
            .tolist()
        )

        if sample_values:
            print(
                "    samples:"
            )

            for value in sample_values:
                print(
                    f"      {value!r}"
                )

    print()
    print("First 10 records:")

    display_columns = [
        column
        for column in gdf.columns
        if column != gdf.geometry.name
    ]

    with pd.option_context(
        "display.max_columns",
        None,
        "display.width",
        250,
        "display.max_colwidth",
        80,
    ):
        print(
            gdf[
                display_columns
            ]
            .head(10)
            .to_string(
                index=False
            )
        )

    print()
    print("Potential identifier/name fields:")

    keywords = (
        "adm",
        "name",
        "pcode",
        "code",
        "id",
        "dept",
        "dist",
    )

    candidates = [
        column
        for column in display_columns
        if any(
            keyword in column.lower()
            for keyword in keywords
        )
    ]

    if candidates:
        for column in candidates:
            print(
                f"  {column}"
            )
    else:
        print(
            "  None detected automatically."
        )


def main() -> None:
    print(
        "Inspecting Paraguay administrative boundaries..."
    )

    inspect_layer(
        "ADM1",
        ADM1_PATH,
    )

    inspect_layer(
        "ADM2",
        ADM2_PATH,
    )

    print_separator()

    print(
        "Inspection complete."
    )


if __name__ == "__main__":
    main()