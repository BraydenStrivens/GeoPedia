"""
Process Vietnam's pre-reform administrative boundaries.

Source
------
GADM v2.8 (2015):
    data/raw/countries/vietnam/pre-reform-admin/
        dk039bc2779/VNM_adm3.shp

The source contains Vietnam's complete 2015 ADM3 hierarchy. GeoPedia uses
this single source for all pre-reform administrative levels so that the
province, district, and commune-level boundaries remain internally
consistent.

Outputs
-------
data/intermediate/countries/vietnam/pre-reform-admin/
    provinces.geojson
    districts.geojson
    communes.geojson

Expected feature counts
-----------------------
Provinces:  63
Districts:  678
Communes:   10,805

The province and district layers are dissolved from the ADM3 geometry.
The commune layer preserves the original ADM3 features.

This script performs normalization and hierarchy construction only.
Geometry simplification is handled by a separate script.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd


RAW_PATH = Path(
    "data/raw/countries/vietnam/pre-reform-admin/"
    "dk039bc2779/VNM_adm3.shp"
)

OUTPUT_DIR = Path(
    "data/intermediate/countries/vietnam/pre-reform-admin"
)

PROVINCES_PATH = OUTPUT_DIR / "provinces.geojson"
DISTRICTS_PATH = OUTPUT_DIR / "districts.geojson"
COMMUNES_PATH = OUTPUT_DIR / "communes.geojson"

EXPECTED_PROVINCES = 63
EXPECTED_DISTRICTS = 678
EXPECTED_COMMUNES = 10_805


def clean_text(value: object) -> str:
    """Return a stripped string, or an empty string for a missing value."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def validate_source(gdf: gpd.GeoDataFrame) -> None:
    """Validate the fields and basic geometry required by the processor."""
    required_columns = {
        "ID_1",
        "NAME_1",
        "ID_2",
        "NAME_2",
        "ID_3",
        "NAME_3",
        "ENGTYPE_3",
        "geometry",
    }

    missing_columns = required_columns - set(gdf.columns)

    if missing_columns:
        raise ValueError(
            "GADM source is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if gdf.crs is None:
        raise ValueError("GADM source has no CRS.")

    if gdf.geometry.isna().any():
        raise ValueError("GADM source contains missing geometries.")

    if gdf.geometry.is_empty.any():
        raise ValueError("GADM source contains empty geometries.")

    invalid_count = int((~gdf.geometry.is_valid).sum())

    if invalid_count:
        raise ValueError(
            f"GADM source contains {invalid_count:,} invalid geometries."
        )


def prepare_communes(source: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Normalize the original ADM3 features into GeoPedia properties."""
    communes = source[
        [
            "ID_1",
            "NAME_1",
            "ID_2",
            "NAME_2",
            "ID_3",
            "NAME_3",
            "ENGTYPE_3",
            "geometry",
        ]
    ].copy()

    communes["province_id"] = communes["ID_1"].astype(int).astype(str)
    communes["province"] = communes["NAME_1"].map(clean_text)

    communes["district_id"] = communes["ID_2"].astype(int).astype(str)
    communes["district"] = communes["NAME_2"].map(clean_text)

    communes["commune_id"] = communes["ID_3"].astype(int).astype(str)
    communes["commune"] = communes["NAME_3"].map(clean_text)
    communes["commune_type"] = communes["ENGTYPE_3"].map(clean_text)

    communes = communes[
        [
            "province_id",
            "province",
            "district_id",
            "district",
            "commune_id",
            "commune",
            "commune_type",
            "geometry",
        ]
    ]

    return communes


def prepare_districts(
    communes: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve commune geometry into the 2015 district hierarchy."""
    district_properties = (
        communes[
            [
                "district_id",
                "district",
                "province_id",
                "province",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    duplicate_ids = district_properties["district_id"].duplicated(
        keep=False
    )

    if duplicate_ids.any():
        duplicates = sorted(
            district_properties.loc[duplicate_ids, "district_id"].unique()
        )

        raise ValueError(
            "District IDs do not map to exactly one hierarchy: "
            + ", ".join(duplicates[:20])
        )

    geometry = (
        communes[["district_id", "geometry"]]
        .dissolve(by="district_id")
        .reset_index()
    )

    districts = district_properties.merge(
        geometry,
        on="district_id",
        how="left",
        validate="one_to_one",
    )

    return gpd.GeoDataFrame(
        districts,
        geometry="geometry",
        crs=communes.crs,
    )


def prepare_provinces(
    communes: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Dissolve commune geometry into the 2015 provincial hierarchy."""
    province_properties = (
        communes[
            [
                "province_id",
                "province",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    duplicate_ids = province_properties["province_id"].duplicated(
        keep=False
    )

    if duplicate_ids.any():
        duplicates = sorted(
            province_properties.loc[duplicate_ids, "province_id"].unique()
        )

        raise ValueError(
            "Province IDs do not map to exactly one hierarchy: "
            + ", ".join(duplicates[:20])
        )

    geometry = (
        communes[["province_id", "geometry"]]
        .dissolve(by="province_id")
        .reset_index()
    )

    provinces = province_properties.merge(
        geometry,
        on="province_id",
        how="left",
        validate="one_to_one",
    )

    return gpd.GeoDataFrame(
        provinces,
        geometry="geometry",
        crs=communes.crs,
    )


def validate_output(
    gdf: gpd.GeoDataFrame,
    *,
    name: str,
    id_column: str,
    expected_count: int,
) -> None:
    """Validate a processed administrative layer before writing it."""
    if len(gdf) != expected_count:
        raise ValueError(
            f"{name} count mismatch: "
            f"expected {expected_count:,}, got {len(gdf):,}."
        )

    unique_ids = gdf[id_column].nunique()

    if unique_ids != expected_count:
        raise ValueError(
            f"{name} ID count mismatch: "
            f"expected {expected_count:,}, got {unique_ids:,}."
        )

    if gdf.geometry.isna().any():
        raise ValueError(f"{name} contains missing geometry.")

    if gdf.geometry.is_empty.any():
        raise ValueError(f"{name} contains empty geometry.")

    invalid_count = int((~gdf.geometry.is_valid).sum())

    if invalid_count:
        raise ValueError(
            f"{name} contains {invalid_count:,} invalid geometries."
        )


def main() -> None:
    print("Processing Vietnam pre-reform administrative data...")
    print(f"Source: {RAW_PATH}")

    source = gpd.read_file(RAW_PATH)

    validate_source(source)

    # GeoPedia public GeoJSON is standardized on WGS84.
    source = source.to_crs("EPSG:4326")

    communes = prepare_communes(source)
    districts = prepare_districts(communes)
    provinces = prepare_provinces(communes)

    validate_output(
        provinces,
        name="Provinces",
        id_column="province_id",
        expected_count=EXPECTED_PROVINCES,
    )

    validate_output(
        districts,
        name="Districts",
        id_column="district_id",
        expected_count=EXPECTED_DISTRICTS,
    )

    validate_output(
        communes,
        name="Communes",
        id_column="commune_id",
        expected_count=EXPECTED_COMMUNES,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    provinces.to_file(PROVINCES_PATH, driver="GeoJSON")
    districts.to_file(DISTRICTS_PATH, driver="GeoJSON")
    communes.to_file(COMMUNES_PATH, driver="GeoJSON")

    print()
    print("Vietnam pre-reform administrative processing complete.")
    print(f"Provinces: {len(provinces):,}")
    print(f"Districts: {len(districts):,}")
    print(f"Communes:  {len(communes):,}")
    print()
    print(f"Wrote: {PROVINCES_PATH}")
    print(f"Wrote: {DISTRICTS_PATH}")
    print(f"Wrote: {COMMUNES_PATH}")


if __name__ == "__main__":
    main()