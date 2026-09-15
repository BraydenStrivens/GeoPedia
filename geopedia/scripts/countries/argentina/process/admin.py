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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "countries"
    / "argentina"
)

PROVINCES_SOURCE = (
    RAW_DIR / "arg_admbnda_adm1_unhcr2017.shp"
)

DEPARTMENTS_SOURCE = (
    RAW_DIR / "arg_admbnda_adm2_unhcr2017.shp"
)

PROVINCES_OUTPUT = (
    OUTPUT_DIR / "provinces.geojson"
)

DEPARTMENTS_OUTPUT = (
    OUTPUT_DIR / "departments.geojson"
)


PROVINCE_NAME_FIXES = {
    "Río negro": "Río Negro",
}


def normalize_province_name(
    value: str,
) -> str:
    return PROVINCE_NAME_FIXES.get(
        value,
        value,
    )


def process_provinces() -> gpd.GeoDataFrame:
    print("Processing Argentina provinces...")

    gdf = gpd.read_file(
        PROVINCES_SOURCE
    )

    if len(gdf) != 24:
        raise ValueError(
            "Expected 24 Argentina ADM1 features, "
            f"found {len(gdf)}."
        )

    required_columns = {
        "ADM1_ES",
        "ADM1_PCODE",
    }

    missing_columns = (
        required_columns
        - set(gdf.columns)
    )

    if missing_columns:
        raise ValueError(
            "Province source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    gdf = gdf.to_crs(
        epsg=4326
    )

    gdf = gdf[
        [
            "ADM1_PCODE",
            "ADM1_ES",
            "geometry",
        ]
    ].copy()

    gdf = gdf.rename(
        columns={
            "ADM1_PCODE": "province_id",
            "ADM1_ES": "province",
        }
    )

    gdf["province"] = (
        gdf["province"]
        .astype(str)
        .map(normalize_province_name)
    )

    if gdf["province_id"].isna().any():
        raise ValueError(
            "Province data contains missing province_id values."
        )

    if gdf["province"].isna().any():
        raise ValueError(
            "Province data contains missing province names."
        )

    if not gdf["province_id"].is_unique:
        raise ValueError(
            "Province IDs are not unique."
        )

    if not gdf["province"].is_unique:
        raise ValueError(
            "Province names are not unique."
        )

    invalid_count = int(
        (~gdf.geometry.is_valid).sum()
    )

    if invalid_count:
        raise ValueError(
            f"Province data contains {invalid_count} "
            "invalid geometries."
        )

    gdf = gdf.sort_values(
        "province_id"
    ).reset_index(
        drop=True
    )

    return gdf


def process_departments() -> gpd.GeoDataFrame:
    print("Processing Argentina departments...")

    gdf = gpd.read_file(
        DEPARTMENTS_SOURCE
    )

    if len(gdf) != 526:
        raise ValueError(
            "Expected 526 Argentina ADM2 features, "
            f"found {len(gdf)}."
        )

    required_columns = {
        "ADM1_ES",
        "ADM1_PCODE",
        "ADM2_ES",
        "ADM2_PCODE",
    }

    missing_columns = (
        required_columns
        - set(gdf.columns)
    )

    if missing_columns:
        raise ValueError(
            "Department source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    gdf = gdf.to_crs(
        epsg=4326
    )

    gdf = gdf[
        [
            "ADM2_PCODE",
            "ADM2_ES",
            "ADM1_PCODE",
            "ADM1_ES",
            "geometry",
        ]
    ].copy()

    gdf = gdf.rename(
        columns={
            "ADM2_PCODE": "department_id",
            "ADM2_ES": "department",
            "ADM1_PCODE": "province_id",
            "ADM1_ES": "province",
        }
    )

    gdf["province"] = (
        gdf["province"]
        .astype(str)
        .map(normalize_province_name)
    )

    required_output_columns = [
        "department_id",
        "department",
        "province_id",
        "province",
    ]

    for column in required_output_columns:
        if gdf[column].isna().any():
            raise ValueError(
                f"Department data contains missing {column} values."
            )

    if not gdf["department_id"].is_unique:
        raise ValueError(
            "Department IDs are not unique."
        )

    invalid_count = int(
        (~gdf.geometry.is_valid).sum()
    )

    if invalid_count:
        raise ValueError(
            f"Department data contains {invalid_count} "
            "invalid geometries."
        )

    gdf = gdf.sort_values(
        [
            "province_id",
            "department_id",
        ]
    ).reset_index(
        drop=True
    )

    return gdf


def validate_relationships(
    provinces: gpd.GeoDataFrame,
    departments: gpd.GeoDataFrame,
) -> None:
    province_ids = set(
        provinces["province_id"]
    )

    department_parent_ids = set(
        departments["province_id"]
    )

    unknown_parent_ids = (
        department_parent_ids
        - province_ids
    )

    if unknown_parent_ids:
        raise ValueError(
            "Departments reference unknown province IDs: "
            f"{sorted(unknown_parent_ids)}"
        )

    if len(department_parent_ids) != 24:
        raise ValueError(
            "Expected departments to reference all 24 "
            f"provinces, found {len(department_parent_ids)}."
        )

    province_names_by_id = dict(
        zip(
            provinces["province_id"],
            provinces["province"],
        )
    )

    mismatches = []

    for row in departments.itertuples():
        expected_name = (
            province_names_by_id[
                row.province_id
            ]
        )

        if row.province != expected_name:
            mismatches.append(
                (
                    row.department_id,
                    row.province_id,
                    row.province,
                    expected_name,
                )
            )

    if mismatches:
        preview = mismatches[:10]

        raise ValueError(
            "Department province names do not match "
            "the ADM1 layer. Example mismatches: "
            f"{preview}"
        )


def write_geojson(
    gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    gdf.to_file(
        output_path,
        driver="GeoJSON",
    )

    print(
        f"Saved: {output_path}"
    )


def print_summary(
    provinces: gpd.GeoDataFrame,
    departments: gpd.GeoDataFrame,
) -> None:
    print()
    print("=" * 80)
    print("Argentina admin processing complete")
    print("=" * 80)

    print(
        f"Provinces: {len(provinces)}"
    )

    print(
        f"Departments / partidos / comunas: "
        f"{len(departments)}"
    )

    print()
    print(
        "Department feature counts by province:"
    )

    counts = (
        departments.groupby(
            [
                "province_id",
                "province",
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            "province_id"
        )
    )

    print(
        counts.to_string(
            index=False
        )
    )

    print()
    print(
        f"Provinces output: {PROVINCES_OUTPUT}"
    )

    print(
        f"Departments output: {DEPARTMENTS_OUTPUT}"
    )


def main() -> None:
    provinces = (
        process_provinces()
    )

    departments = (
        process_departments()
    )

    validate_relationships(
        provinces,
        departments,
    )

    write_geojson(
        provinces,
        PROVINCES_OUTPUT,
    )

    write_geojson(
        departments,
        DEPARTMENTS_OUTPUT,
    )

    print_summary(
        provinces,
        departments,
    )


if __name__ == "__main__":
    main()