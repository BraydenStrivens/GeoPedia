"""
Inspect Panama's administrative boundary GeoJSON files.

This script reports the structure, attributes, geometry quality, and hierarchy
of Panama's province/comarca, district, and corregimiento boundary datasets.

In addition to inspecting each file independently, it validates relationships
between the three administrative levels. This is especially useful for finding:

- province codes that do not agree between datasets;
- districts missing from the corregimiento dataset;
- districts present only in the corregimiento dataset;
- inconsistent district names between administrative levels;
- malformed hierarchical corregimiento IDs;
- duplicate corregimiento IDs and the records that share them.

The script is intended as a permanent diagnostic tool for evaluating raw Panama
boundary datasets before they are converted into GeoPedia runtime GeoJSON.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import geopandas as gpd
import pandas as pd
from shapely.geometry.base import BaseGeometry


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "panama"
)

ADMIN_FILES = {
    "ADM1": SOURCE_DIRECTORY
    / "Panama_Province_Boundaries_2024_355929332618465870.geojson",
    "ADM2": SOURCE_DIRECTORY
    / "Panama_Distritos_Boundaries_2024_4679260270347429694.geojson",
    "ADM3": SOURCE_DIRECTORY
    / "Panama_Corregimientos_Boundaries_2024_-2164041707231143700.geojson",
}

SAMPLE_COUNT = 10
LOW_CARDINALITY_LIMIT = 30


def print_heading(title: str, character: str = "=") -> None:
    """Print a section heading."""

    print()
    print(character * 80)
    print(title)
    print(character * 80)


def print_subheading(title: str) -> None:
    """Print a subsection heading."""

    print()
    print(title)
    print("-" * len(title))


def format_value(value: Any) -> str:
    """Return a readable representation of a dataframe value."""

    if pd.isna(value):
        return "None"

    return repr(value)


def normalized_string(value: Any) -> str | None:
    """Convert a dataframe value to a stripped string or None."""

    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def count_geometry_coordinates(geometry: BaseGeometry | None) -> int:
    """
    Count coordinate pairs in a Shapely geometry.

    The function recursively handles multipart and collection geometries.
    """

    if geometry is None or geometry.is_empty:
        return 0

    geometry_type = geometry.geom_type

    if geometry_type == "Point":
        return 1

    if geometry_type in {"LineString", "LinearRing"}:
        return len(geometry.coords)

    if geometry_type == "Polygon":
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if hasattr(geometry, "geoms"):
        return sum(
            count_geometry_coordinates(part)
            for part in geometry.geoms
        )

    return 0


def compact_geometry_size(gdf: gpd.GeoDataFrame) -> int:
    """
    Approximate the compact GeoJSON size when only geometry is retained.

    This helps estimate how much of a raw file's size comes from geometry
    rather than attributes.
    """

    features = []

    for geometry in gdf.geometry:
        features.append(
            {
                "type": "Feature",
                "properties": {},
                "geometry": (
                    None
                    if geometry is None
                    else geometry.__geo_interface__
                ),
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    encoded = json.dumps(
        geojson,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return len(encoded)


def print_columns(gdf: gpd.GeoDataFrame) -> None:
    """Print every dataframe column and its dtype."""

    print_subheading("Columns")

    for column in gdf.columns:
        if column == gdf.geometry.name:
            print(f"{column} (geometry)")
        else:
            print(f"{column}: {gdf[column].dtype}")


def print_name_fields(gdf: gpd.GeoDataFrame) -> None:
    """
    Inspect columns whose names contain the word 'name'.

    Some Panama datasets use Spanish field names such as NOMBRE, PROVINCIA,
    DISTRITO, and Corregimiento, so these fields are also covered elsewhere
    through the low-cardinality output.
    """

    print_subheading("Name fields")

    name_columns = [
        column
        for column in gdf.columns
        if "name" in column.lower()
        and column != gdf.geometry.name
    ]

    if not name_columns:
        print("No columns containing 'name' were found.")
        return

    for column in name_columns:
        values = [
            normalized_string(value)
            for value in gdf[column]
        ]

        non_blank_values = [
            value
            for value in values
            if value is not None
        ]

        counts = Counter(non_blank_values)

        null_count = int(gdf[column].isna().sum())

        blank_count = sum(
            1
            for value in gdf[column]
            if not pd.isna(value)
            and not str(value).strip()
        )

        print(
            f"{column}: "
            f"{len(counts)} unique non-blank values, "
            f"{null_count} null, "
            f"{blank_count} blank"
        )

        duplicates = {
            value: count
            for value, count in counts.items()
            if count > 1
        }

        if duplicates:
            print(f"  Duplicate values: {len(duplicates)}")

            for value, count in sorted(
                duplicates.items(),
                key=lambda item: item[0],
            ):
                print(f"    {value!r}: {count}")


def print_code_fields(gdf: gpd.GeoDataFrame) -> None:
    """Inspect likely code or identifier columns."""

    print_subheading("Code / ID fields")

    code_columns = []

    for column in gdf.columns:
        if column == gdf.geometry.name:
            continue

        lowered = column.lower()

        if (
            "code" in lowered
            or "pcode" in lowered
            or lowered == "id"
            or lowered.startswith("id_")
            or lowered.endswith("_id")
            or lowered == "objectid"
            or lowered == "globalid"
        ):
            code_columns.append(column)

    if not code_columns:
        print("No likely code / ID columns were found.")
        return

    for column in code_columns:
        non_null_values = gdf[column].dropna()
        value_counts = non_null_values.astype(str).value_counts()

        print(
            f"{column}: "
            f"{len(value_counts)} unique, "
            f"{int(gdf[column].isna().sum())} null"
        )

        if len(value_counts) <= LOW_CARDINALITY_LIMIT:
            for value, count in sorted(
                value_counts.items(),
                key=lambda item: item[0],
            ):
                print(f"  {value!r}: {count}")


def print_other_low_cardinality_fields(
    gdf: gpd.GeoDataFrame,
) -> None:
    """Print low-cardinality non-geometry fields not already treated as IDs."""

    print_subheading("Other low-cardinality fields")

    found_any = False

    for column in gdf.columns:
        if column == gdf.geometry.name:
            continue

        lowered = column.lower()

        if (
            "code" in lowered
            or "pcode" in lowered
            or lowered == "id"
            or lowered.startswith("id_")
            or lowered.endswith("_id")
            or lowered == "objectid"
            or lowered == "globalid"
        ):
            continue

        non_null_values = gdf[column].dropna()

        if non_null_values.empty:
            continue

        value_counts = (
            non_null_values
            .astype(str)
            .value_counts()
        )

        if len(value_counts) > LOW_CARDINALITY_LIMIT:
            continue

        found_any = True

        print(
            f"{column}: "
            f"{len(value_counts)} unique, "
            f"{int(gdf[column].isna().sum())} null"
        )

        for value, count in sorted(
            value_counts.items(),
            key=lambda item: item[0],
        ):
            print(f"  {value!r}: {count}")

    if not found_any:
        print("No additional low-cardinality fields were found.")


def print_sample_records(
    gdf: gpd.GeoDataFrame,
    sample_count: int = SAMPLE_COUNT,
) -> None:
    """Print a small sample of non-geometry records."""

    print_subheading(f"First {min(sample_count, len(gdf))} records")

    attribute_columns = [
        column
        for column in gdf.columns
        if column != gdf.geometry.name
    ]

    for index, (_, row) in enumerate(
        gdf.head(sample_count).iterrows()
    ):
        print(f"[{index}]")

        for column in attribute_columns:
            print(
                f"  {column}: "
                f"{format_value(row[column])}"
            )


def print_geometry_summary(gdf: gpd.GeoDataFrame) -> None:
    """Print geometry type, validity, coordinate, bounds, and size information."""

    print_subheading("Geometry")

    geometry_type_counts = gdf.geometry.geom_type.value_counts()

    print("Geometry types:")

    for geometry_type, count in geometry_type_counts.items():
        print(f"  {geometry_type}: {count}")

    empty_count = int(gdf.geometry.is_empty.sum())
    invalid_count = int((~gdf.geometry.is_valid).sum())

    coordinate_count = sum(
        count_geometry_coordinates(geometry)
        for geometry in gdf.geometry
    )

    min_x, min_y, max_x, max_y = gdf.total_bounds

    size_bytes = compact_geometry_size(gdf)
    size_mb = size_bytes / (1024 * 1024)

    print(f"Empty geometries: {empty_count}")
    print(f"Invalid geometries: {invalid_count}")
    print(f"Coordinate count: {coordinate_count:,}")
    print(
        "Bounds: "
        f"({min_x:.6f}, {min_y:.6f}) -> "
        f"({max_x:.6f}, {max_y:.6f})"
    )
    print(
        "Approximate compact geometry-only size: "
        f"{size_mb:.2f} MB ({size_bytes:,} bytes)"
    )


def inspect_file(
    level: str,
    path: Path,
) -> gpd.GeoDataFrame:
    """Load and report the structure of one administrative boundary file."""

    print_heading(f"{level}: {path.name}")

    print(f"Path: {path}")

    if not path.exists():
        raise FileNotFoundError(
            f"Missing source file: {path}"
        )

    gdf = gpd.read_file(path)

    print(f"Features: {len(gdf)}")
    print(f"CRS: {gdf.crs}")

    print_columns(gdf)
    print_name_fields(gdf)
    print_code_fields(gdf)
    print_other_low_cardinality_fields(gdf)
    print_sample_records(gdf)
    print_geometry_summary(gdf)

    return gdf


def build_adm2_district_id(row: pd.Series) -> str:
    """Return the globally unique district ID supplied by the ADM2 source."""

    return str(row["ID_Distrito"]).strip()


def build_adm3_district_id(row: pd.Series) -> str:
    """Derive the parent district ID from a corregimiento's hierarchical ID."""

    return str(row["ID_CORR"]).strip()[:4]


def print_set_difference(
    label: str,
    values: Iterable[str],
) -> None:
    """Print a sorted set of values or indicate that none were found."""

    values = sorted(set(values))

    print(f"{label}: {len(values)}")

    if not values:
        print("  None")
        return

    for value in values:
        print(f"  {value}")

def validate_province_hierarchy(
    adm1: gpd.GeoDataFrame,
    adm2: gpd.GeoDataFrame,
    adm3: gpd.GeoDataFrame,
) -> None:
    """Compare province/comarca IDs and names across the 2024 datasets."""

    print_subheading("Province hierarchy")

    adm1_provinces = {
        str(row["ID_PROV"]).strip(): str(row["Provincia"]).strip()
        for _, row in adm1.iterrows()
    }

    adm2_province_names = set(
        adm2["Provincia"].astype(str).str.strip()
    )

    adm3_province_names = set(
        adm3["Provincia"].astype(str).str.strip()
    )

    adm1_names = set(adm1_provinces.values())

    print(f"ADM1 provinces/comarcas: {len(adm1_provinces)}")
    print(f"ADM2 province/comarca names: {len(adm2_province_names)}")
    print(f"ADM3 province/comarca names: {len(adm3_province_names)}")

    print_set_difference(
        "ADM1 names missing from ADM2",
        adm1_names - adm2_province_names,
    )

    print_set_difference(
        "ADM2 names not present in ADM1",
        adm2_province_names - adm1_names,
    )

    print_set_difference(
        "ADM1 names missing from ADM3",
        adm1_names - adm3_province_names,
    )

    print_set_difference(
        "ADM3 names not present in ADM1",
        adm3_province_names - adm1_names,
    )

def validate_district_hierarchy(
    adm2: gpd.GeoDataFrame,
    adm3: gpd.GeoDataFrame,
) -> None:
    """Compare ADM2 districts with parent district IDs represented by ADM3."""

    print_subheading("District hierarchy")

    adm2_records: dict[str, tuple[str, str]] = {}

    for _, row in adm2.iterrows():
        district_id = build_adm2_district_id(row)

        adm2_records[district_id] = (
            str(row["Provincia"]).strip(),
            str(row["Distrito"]).strip(),
        )

    adm3_district_records: dict[
        str,
        set[tuple[str, str]],
    ] = defaultdict(set)

    adm3_feature_counts: Counter[str] = Counter()

    for _, row in adm3.iterrows():
        district_id = build_adm3_district_id(row)

        adm3_district_records[district_id].add(
            (
                str(row["Provincia"]).strip(),
                str(row["Distrito"]).strip(),
            )
        )

        adm3_feature_counts[district_id] += 1

    adm2_ids = set(adm2_records)
    adm3_ids = set(adm3_district_records)

    print(f"ADM2 district IDs: {len(adm2_ids)}")
    print(f"District IDs referenced by ADM3: {len(adm3_ids)}")

    missing_from_adm3 = adm2_ids - adm3_ids
    extra_in_adm3 = adm3_ids - adm2_ids

    print()
    print(
        "ADM2 districts with no corregimientos in ADM3: "
        f"{len(missing_from_adm3)}"
    )

    if not missing_from_adm3:
        print("  None")
    else:
        for district_id in sorted(missing_from_adm3):
            province, district = adm2_records[district_id]
            print(f"  {district_id}: {district} ({province})")

    print()
    print(
        "District IDs referenced by ADM3 but absent from ADM2: "
        f"{len(extra_in_adm3)}"
    )

    if not extra_in_adm3:
        print("  None")
    else:
        for district_id in sorted(extra_in_adm3):
            print(
                f"  {district_id}: "
                f"{sorted(adm3_district_records[district_id])}"
            )

    print()
    print("District name consistency:")

    mismatch_count = 0

    for district_id in sorted(adm2_ids & adm3_ids):
        adm2_record = adm2_records[district_id]
        adm3_records = adm3_district_records[district_id]

        if adm3_records == {adm2_record}:
            continue

        mismatch_count += 1

        print(f"  {district_id}:")
        print(f"    ADM2: {adm2_record}")
        print(f"    ADM3: {sorted(adm3_records)}")

    if mismatch_count == 0:
        print("  All shared district names agree.")

    print(
        "District IDs with inconsistent names: "
        f"{mismatch_count}"
    )

    print()
    print("Corregimiento counts by district:")

    for district_id in sorted(adm3_ids):
        records = sorted(adm3_district_records[district_id])
        province, district = records[0]

        print(
            f"  {district_id}: "
            f"{adm3_feature_counts[district_id]} "
            f"- {district} ({province})"
        )

def validate_corregimiento_ids(
    adm3: gpd.GeoDataFrame,
) -> None:
    """Validate uniqueness and structure of 2024 corregimiento IDs."""

    print_subheading("Corregimiento ID validation")

    actual_ids = adm3["ID_CORR"].astype(str).str.strip()

    invalid_length_mask = actual_ids.str.len() != 6
    non_numeric_mask = ~actual_ids.str.fullmatch(r"\d{6}")

    print(f"Features: {len(adm3)}")
    print(f"Unique ID_CORR values: {actual_ids.nunique()}")
    print(
        "IDs not exactly 6 characters long: "
        f"{int(invalid_length_mask.sum())}"
    )
    print(
        "IDs not composed of exactly 6 digits: "
        f"{int(non_numeric_mask.sum())}"
    )

    counts = actual_ids.value_counts()

    duplicate_ids = counts[
        counts > 1
    ].sort_index()

    print()
    print(f"Duplicated ID_CORR values: {len(duplicate_ids)}")
    print(
        "Extra features caused by duplicate IDs: "
        f"{sum(int(count) - 1 for count in duplicate_ids)}"
    )

    if duplicate_ids.empty:
        print("  None")
        return

    for corregimiento_id, count in duplicate_ids.items():
        rows = adm3[
            actual_ids == corregimiento_id
        ]

        print()
        print(
            f"ID_CORR {corregimiento_id}: "
            f"{count} features"
        )

        geometry_wkbs: list[bytes | None] = []

        for index, row in rows.iterrows():
            geometry = row.geometry

            geometry_wkbs.append(
                None if geometry is None else geometry.wkb
            )

            print(f"  Row {index}")
            print(f"    Provincia: {row['Provincia']!r}")
            print(f"    Distrito: {row['Distrito']!r}")
            print(
                f"    Corregimiento: "
                f"{row['Corregimiento']!r}"
            )
            print(f"    Cabecera: {row['Cabecera']!r}")
            print(f"    Area_HA: {row['Area_HA']!r}")
            print(
                "    Geometry type: "
                f"{geometry.geom_type if geometry is not None else None}"
            )
            print(
                "    Geometry valid: "
                f"{geometry.is_valid if geometry is not None else None}"
            )

        non_null_wkbs = [
            geometry_wkb
            for geometry_wkb in geometry_wkbs
            if geometry_wkb is not None
        ]

        exact_geometry_duplicates = (
            len(non_null_wkbs) > 1
            and len(set(non_null_wkbs)) == 1
        )

        print(
            "  All duplicate records have exactly "
            f"identical geometry: {exact_geometry_duplicates}"
        )
        
        zero_suffix_rows = adm3[
            actual_ids.str.endswith("00")
        ]

        print()
        print(
            "Corregimiento IDs ending in 00: "
            f"{len(zero_suffix_rows)}"
        )

        for index, row in zero_suffix_rows.iterrows():
            print(f"  Row {index}")
            print(f"    ID_CORR: {row['ID_CORR']!r}")
            print(f"    Provincia: {row['Provincia']!r}")
            print(f"    Distrito: {row['Distrito']!r}")
            print(
                f"    Corregimiento: "
                f"{row['Corregimiento']!r}"
            )
            print(f"    Cabecera: {row['Cabecera']!r}")
            print(f"    Area_HA: {row['Area_HA']!r}")
            
            santa_fe_ids = {"050300", "050316"}

    santa_fe_rows = adm3[
        actual_ids.isin(santa_fe_ids)
    ]

    print()
    print("Santa Fe, Darién geometry comparison:")

    for index, row in santa_fe_rows.iterrows():
        geometry = row.geometry

        print(f"  {row['ID_CORR']}:")
        print(f"    Row: {index}")
        print(f"    Area_HA: {row['Area_HA']!r}")
        print(f"    Cabecera: {row['Cabecera']!r}")
        print(f"    Geometry type: {geometry.geom_type}")
        print(f"    Geometry valid: {geometry.is_valid}")
        print(f"    Bounds: {geometry.bounds}")

    if len(santa_fe_rows) == 2:
        first = santa_fe_rows.iloc[0]
        second = santa_fe_rows.iloc[1]

        first_geometry = first.geometry
        second_geometry = second.geometry

        print()
        print(
            "  Geometries exactly equal: "
            f"{first_geometry.equals(second_geometry)}"
        )
        print(
            "  Geometries intersect: "
            f"{first_geometry.intersects(second_geometry)}"
        )
        print(
            "  First contains second: "
            f"{first_geometry.contains(second_geometry)}"
        )
        print(
            "  Second contains first: "
            f"{second_geometry.contains(first_geometry)}"
        )

        intersection = first_geometry.intersection(
            second_geometry
        )

        print(
            "  Intersection empty: "
            f"{intersection.is_empty}"
        )
        print(
            "  Intersection area (source CRS): "
            f"{intersection.area}"
        )
        
def validate_corregimiento_name_disambiguation(
    adm3: gpd.GeoDataFrame,
) -> None:
    """
    Determine whether duplicate corregimiento names can be disambiguated by
    their district names.
    """

    print_subheading("Corregimiento name disambiguation")

    name_groups: dict[
        str,
        list[tuple[str, str, str]],
    ] = defaultdict(list)

    for _, row in adm3.iterrows():
        name = str(row["Corregimiento"]).strip()
        district = str(row["Distrito"]).strip()
        province = str(row["Provincia"]).strip()
        corregimiento_id = str(row["ID_CORR"]).strip()

        name_groups[name].append(
            (
                district,
                province,
                corregimiento_id,
            )
        )

    duplicate_names = {
        name: records
        for name, records in name_groups.items()
        if len(records) > 1
    }

    print(
        "Corregimiento names appearing more than once: "
        f"{len(duplicate_names)}"
    )

    district_insufficient = []

    for name, records in sorted(duplicate_names.items()):
        district_names = [
            district
            for district, _, _ in records
        ]

        if len(district_names) != len(set(district_names)):
            district_insufficient.append(
                (
                    name,
                    records,
                )
            )

    print(
        "Duplicate names where district alone is "
        "not enough to disambiguate: "
        f"{len(district_insufficient)}"
    )

    if not district_insufficient:
        print(
            "  Every duplicate corregimiento name can be "
            "disambiguated using its district."
        )
        return

    for name, records in district_insufficient:
        print(f"  {name!r}")

        for district, province, corregimiento_id in records:
            print(
                f"    {corregimiento_id}: "
                f"{district} ({province})"
            )


def validate_cross_level_hierarchy(
    adm1: gpd.GeoDataFrame,
    adm2: gpd.GeoDataFrame,
    adm3: gpd.GeoDataFrame,
) -> None:
    """Run all validations involving multiple administrative levels."""

    print_heading("Cross-level hierarchy validation")

    validate_province_hierarchy(
        adm1,
        adm2,
        adm3,
    )

    validate_district_hierarchy(
        adm2,
        adm3,
    )

    validate_corregimiento_ids(
        adm3,
    )

    validate_corregimiento_name_disambiguation(
        adm3,
    )


def main() -> None:
    """Inspect Panama's administrative files and validate their hierarchy."""

    print("Panama administrative boundary inspection")
    print(f"Source directory: {SOURCE_DIRECTORY}")

    datasets = {
        level: inspect_file(
            level,
            path,
        )
        for level, path in ADMIN_FILES.items()
    }

    validate_cross_level_hierarchy(
        datasets["ADM1"],
        datasets["ADM2"],
        datasets["ADM3"],
    )

    print_heading("Inspection complete")


if __name__ == "__main__":
    main()