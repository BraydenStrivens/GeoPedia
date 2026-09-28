"""
Processes South Korea's administrative boundary data for GeoPedia.

The source data contains:
- 17 provinces / province-level administrative divisions
- 250 municipalities
- 3,504 submunicipalities

The source hierarchy is encoded in each feature's administrative code:
- Province codes contain 2 digits.
- Municipality codes contain 5 digits and begin with their province code.
- Submunicipality codes contain 7 digits and begin with their municipality code.

This script:
1. Loads the three 2018 South Korea administrative GeoJSON datasets.
2. Validates required source properties and administrative codes.
3. Validates that all administrative codes are unique at their level.
4. Validates the complete province -> municipality -> submunicipality hierarchy.
5. Preserves the source romanized Korean names exactly apart from whitespace.
6. Preserves the source Korean names exactly apart from whitespace.
7. Adds parent hierarchy data to municipalities and submunicipalities.
8. Repairs invalid polygon geometries when necessary.
9. Writes normalized intermediate GeoJSON for later map processing.

The romanized source names intentionally retain Korean administrative suffixes
such as -do, -si, -gun, -gu, -eup, -myeon, and -dong. GeoPedia does not
translate these suffixes because the romanized forms are useful for recognizing
Korean place names on maps and signs.

Input:
    data/raw/countries/south-korea/
        skorea-provinces-2018-geo.json
        skorea-municipalities-2018-geo.json
        skorea-submunicipalities-2018-geo.json

Outputs:
    data/intermediate/countries/south-korea/geojson/
        provinces.geojson
        municipalities.geojson
        submunicipalities.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-korea/process/admin.py

The intermediate files are intentionally not simplified here. GeoPedia's
later map-data processing stage can clean and simplify them with Mapshaper.
Testing of this source found that:

    -clean -simplify weighted 10% keep-shapes

preserves the administrative features while substantially reducing geometry
size.
"""

from pathlib import Path
import re

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon


RAW_DIR = Path(
    "data/raw/countries/south-korea"
)

OUTPUT_DIR = Path(
    "data/intermediate/countries/south-korea/geojson"
)

PROVINCES_SOURCE_PATH = (
    RAW_DIR / "skorea-provinces-2018-geo.json"
)

MUNICIPALITIES_SOURCE_PATH = (
    RAW_DIR / "skorea-municipalities-2018-geo.json"
)

SUBMUNICIPALITIES_SOURCE_PATH = (
    RAW_DIR / "skorea-submunicipalities-2018-geo.json"
)

PROVINCES_PATH = OUTPUT_DIR / "provinces.geojson"

MUNICIPALITIES_PATH = (
    OUTPUT_DIR / "municipalities.geojson"
)

SUBMUNICIPALITIES_PATH = (
    OUTPUT_DIR / "submunicipalities.geojson"
)


EXPECTED_PROVINCES = 17
EXPECTED_MUNICIPALITIES = 250
EXPECTED_SUBMUNICIPALITIES = 3504

SOURCE_YEAR = "2018"


def clean_text(value: object) -> str:
    """
    Normalizes surrounding and repeated whitespace in source text.

    Korean and romanized names are otherwise preserved exactly as supplied by
    the source.
    """

    if value is None:
        return ""

    text = str(value).replace("\xa0", " ")

    return re.sub(r"\s+", " ", text).strip()


def validate_required_columns(
    frame: gpd.GeoDataFrame,
    label: str,
) -> None:
    """
    Ensures that a source layer contains the properties required by GeoPedia.
    """

    required_columns = {
        "name",
        "name_eng",
        "code",
        "base_year",
        "geometry",
    }

    missing = sorted(
        required_columns - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"{label} is missing required columns: "
            + ", ".join(missing)
        )


def validate_source_year(
    frame: gpd.GeoDataFrame,
    label: str,
) -> None:
    """
    Ensures every source feature belongs to the expected 2018 dataset.
    """

    years = {
        clean_text(value)
        for value in frame["base_year"]
    }

    if years != {SOURCE_YEAR}:
        raise ValueError(
            f"{label} contains unexpected base_year values: "
            f"{sorted(years)}"
        )


def validate_source_codes(
    frame: gpd.GeoDataFrame,
    label: str,
    expected_length: int,
) -> None:
    """
    Validates administrative codes for one source level.

    Codes must:
    - be present,
    - contain only decimal digits,
    - have the expected length,
    - be unique within the administrative level.
    """

    codes = frame["code"].apply(clean_text)

    missing = codes[codes == ""]

    if not missing.empty:
        raise ValueError(
            f"{label} contains {len(missing)} missing codes."
        )

    invalid_format = codes[
        ~codes.str.fullmatch(
            rf"\d{{{expected_length}}}"
        )
    ]

    if not invalid_format.empty:
        examples = sorted(
            invalid_format.unique()
        )[:20]

        raise ValueError(
            f"{label} contains codes that are not "
            f"{expected_length}-digit values: "
            + ", ".join(examples)
        )

    duplicate_codes = sorted(
        codes[
            codes.duplicated(keep=False)
        ].unique()
    )

    if duplicate_codes:
        raise ValueError(
            f"{label} contains duplicate codes: "
            + ", ".join(duplicate_codes)
        )


def validate_source_names(
    frame: gpd.GeoDataFrame,
    label: str,
) -> None:
    """
    Ensures every source feature has both a romanized and Korean name.
    """

    romanized_names = frame["name_eng"].apply(
        clean_text
    )

    native_names = frame["name"].apply(
        clean_text
    )

    missing_romanized = int(
        (romanized_names == "").sum()
    )

    missing_native = int(
        (native_names == "").sum()
    )

    if missing_romanized:
        raise ValueError(
            f"{label} contains {missing_romanized} "
            "missing romanized names."
        )

    if missing_native:
        raise ValueError(
            f"{label} contains {missing_native} "
            "missing Korean names."
        )


def extract_polygonal_geometry(geometry):
    """
    Returns only the polygonal components of a repaired geometry.

    Shapely's make_valid operation can convert an invalid Polygon or
    MultiPolygon into a GeometryCollection containing polygonal geometry
    together with lower-dimensional line or point artifacts.

    Polygon and MultiPolygon geometries are preserved. GeometryCollections
    are recursively searched for polygonal components, while Point,
    MultiPoint, LineString, and MultiLineString components are discarded.
    """

    if geometry is None or geometry.is_empty:
        return None

    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygons = []

        for part in geometry.geoms:
            polygonal_part = extract_polygonal_geometry(
                part
            )

            if polygonal_part is None:
                continue

            if isinstance(polygonal_part, Polygon):
                polygons.append(
                    polygonal_part
                )

            elif isinstance(
                polygonal_part,
                MultiPolygon,
            ):
                polygons.extend(
                    polygonal_part.geoms
                )

        if not polygons:
            return None

        if len(polygons) == 1:
            return polygons[0]

        return MultiPolygon(polygons)

    # Lower-dimensional artifacts created by make_valid(), such as
    # LineString, MultiLineString, Point, and MultiPoint, are not part
    # of GeoPedia's polygonal administrative boundaries.
    return None


def repair_geometries(
    frame: gpd.GeoDataFrame,
    label: str,
) -> gpd.GeoDataFrame:
    """
    Repairs invalid source geometries with Shapely's make_valid operation.
    """

    result = frame.copy()

    if result.geometry.isna().any():
        raise ValueError(
            f"{label} contains missing source geometries."
        )

    if result.geometry.is_empty.any():
        raise ValueError(
            f"{label} contains empty source geometries."
        )

    invalid_before = int(
        (~result.geometry.is_valid).sum()
    )

    print(
        f"{label} invalid geometries before repair: "
        f"{invalid_before}"
    )

    if invalid_before:
        result.geometry = (
            result.geometry.make_valid()
        )

    result.geometry = result.geometry.apply(
        extract_polygonal_geometry
    )

    missing_polygonal = int(
        result.geometry.isna().sum()
    )

    if missing_polygonal:
        raise ValueError(
            f"{label} contains {missing_polygonal} "
            "geometries with no polygonal components "
            "after repair."
        )

    non_polygonal = result.loc[
        ~result.geometry.geom_type.isin(
            ["Polygon", "MultiPolygon"]
        )
    ]

    if not non_polygonal.empty:
        raise ValueError(
            f"{label} contains {len(non_polygonal)} "
            "non-polygonal geometries after repair."
        )

    invalid_after = int(
        (~result.geometry.is_valid).sum()
    )

    print(
        f"{label} invalid geometries after repair: "
        f"{invalid_after}"
    )

    if invalid_after:
        raise ValueError(
            f"{label} still contains {invalid_after} "
            "invalid geometries after repair."
        )

    return result


def build_province_lookup(
    provinces: gpd.GeoDataFrame,
) -> dict[str, dict[str, str]]:
    """
    Builds a province-code lookup used to attach province hierarchy data to
    lower administrative levels.
    """

    lookup: dict[str, dict[str, str]] = {}

    for _, row in provinces.iterrows():
        province_id = clean_text(
            row["code"]
        )

        lookup[province_id] = {
            "province": clean_text(
                row["name_eng"]
            ),
            "native_province": clean_text(
                row["name"]
            ),
        }

    return lookup


def build_municipality_lookup(
    municipalities: gpd.GeoDataFrame,
) -> dict[str, dict[str, str]]:
    """
    Builds a municipality-code lookup used to attach municipality hierarchy
    data to submunicipalities.
    """

    lookup: dict[str, dict[str, str]] = {}

    for _, row in municipalities.iterrows():
        municipality_id = clean_text(
            row["code"]
        )

        lookup[municipality_id] = {
            "municipality": clean_text(
                row["name_eng"]
            ),
            "native_municipality": clean_text(
                row["name"]
            ),
        }

    return lookup


def validate_hierarchy(
    provinces: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
    submunicipalities: gpd.GeoDataFrame,
) -> None:
    """
    Validates South Korea's code-based administrative hierarchy.

    Municipality:
        first 2 digits -> province

    Submunicipality:
        first 5 digits -> municipality
        first 2 digits -> province

    Validation is performed in both directions so every child has a valid
    parent and every parent is represented by at least one child.
    """

    province_ids = {
        clean_text(value)
        for value in provinces["code"]
    }

    municipality_ids = {
        clean_text(value)
        for value in municipalities["code"]
    }

    submunicipality_ids = {
        clean_text(value)
        for value in submunicipalities["code"]
    }

    municipality_province_ids = {
        municipality_id[:2]
        for municipality_id in municipality_ids
    }

    submunicipality_province_ids = {
        submunicipality_id[:2]
        for submunicipality_id
        in submunicipality_ids
    }

    submunicipality_municipality_ids = {
        submunicipality_id[:5]
        for submunicipality_id
        in submunicipality_ids
    }

    unknown_municipality_provinces = sorted(
        municipality_province_ids - province_ids
    )

    if unknown_municipality_provinces:
        raise ValueError(
            "Municipalities reference unknown province "
            "codes: "
            + ", ".join(
                unknown_municipality_provinces
            )
        )

    unknown_submunicipality_provinces = sorted(
        submunicipality_province_ids
        - province_ids
    )

    if unknown_submunicipality_provinces:
        raise ValueError(
            "Submunicipalities reference unknown "
            "province codes: "
            + ", ".join(
                unknown_submunicipality_provinces
            )
        )

    unknown_submunicipality_municipalities = sorted(
        submunicipality_municipality_ids
        - municipality_ids
    )

    if unknown_submunicipality_municipalities:
        raise ValueError(
            "Submunicipalities reference unknown "
            "municipality codes: "
            + ", ".join(
                unknown_submunicipality_municipalities
            )
        )

    provinces_without_municipalities = sorted(
        province_ids - municipality_province_ids
    )

    if provinces_without_municipalities:
        raise ValueError(
            "Provinces with no municipalities: "
            + ", ".join(
                provinces_without_municipalities
            )
        )

    municipalities_without_submunicipalities = sorted(
        municipality_ids
        - submunicipality_municipality_ids
    )

    if municipalities_without_submunicipalities:
        raise ValueError(
            "Municipalities with no submunicipalities: "
            + ", ".join(
                municipalities_without_submunicipalities
            )
        )


def process_provinces(
    source: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Converts province-level source features into GeoPedia provinces.
    """

    records = []

    for _, row in source.iterrows():
        records.append(
            {
                "province_id": clean_text(
                    row["code"]
                ),
                "province": clean_text(
                    row["name_eng"]
                ),
                "native_province": clean_text(
                    row["name"]
                ),
                "geometry": row.geometry,
            }
        )

    return gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=source.crs,
    )


def process_municipalities(
    source: gpd.GeoDataFrame,
    province_lookup: dict[str, dict[str, str]],
) -> gpd.GeoDataFrame:
    """
    Converts municipality source features into GeoPedia municipalities and
    attaches their province hierarchy.
    """

    records = []

    for _, row in source.iterrows():
        municipality_id = clean_text(
            row["code"]
        )

        province_id = municipality_id[:2]

        province = province_lookup[
            province_id
        ]

        records.append(
            {
                "municipality_id": municipality_id,
                "municipality": clean_text(
                    row["name_eng"]
                ),
                "native_municipality": clean_text(
                    row["name"]
                ),
                "province_id": province_id,
                "province": province["province"],
                "native_province": province[
                    "native_province"
                ],
                "geometry": row.geometry,
            }
        )

    return gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=source.crs,
    )


def process_submunicipalities(
    source: gpd.GeoDataFrame,
    province_lookup: dict[str, dict[str, str]],
    municipality_lookup: dict[str, dict[str, str]],
) -> gpd.GeoDataFrame:
    """
    Converts submunicipality source features into GeoPedia submunicipalities
    and attaches their municipality and province hierarchy.
    """

    records = []

    for _, row in source.iterrows():
        submunicipality_id = clean_text(
            row["code"]
        )

        municipality_id = (
            submunicipality_id[:5]
        )

        province_id = (
            submunicipality_id[:2]
        )

        municipality = municipality_lookup[
            municipality_id
        ]

        province = province_lookup[
            province_id
        ]

        records.append(
            {
                "submunicipality_id": submunicipality_id,
                "submunicipality": clean_text(
                    row["name_eng"]
                ),
                "native_submunicipality": clean_text(
                    row["name"]
                ),
                "municipality_id": municipality_id,
                "municipality": municipality[
                    "municipality"
                ],
                "native_municipality": municipality[
                    "native_municipality"
                ],
                "province_id": province_id,
                "province": province["province"],
                "native_province": province[
                    "native_province"
                ],
                "geometry": row.geometry,
            }
        )

    return gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=source.crs,
    )


def validate_output(
    provinces: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
    submunicipalities: gpd.GeoDataFrame,
) -> None:
    """
    Performs structural and geometry validation before writing output.
    """

    expected_counts = [
        (
            "provinces",
            provinces,
            EXPECTED_PROVINCES,
            "province_id",
        ),
        (
            "municipalities",
            municipalities,
            EXPECTED_MUNICIPALITIES,
            "municipality_id",
        ),
        (
            "submunicipalities",
            submunicipalities,
            EXPECTED_SUBMUNICIPALITIES,
            "submunicipality_id",
        ),
    ]

    for (
        label,
        frame,
        expected_count,
        id_property,
    ) in expected_counts:
        if len(frame) != expected_count:
            raise ValueError(
                f"Expected {expected_count} {label}, "
                f"found {len(frame)}."
            )

        if frame[id_property].duplicated().any():
            duplicates = sorted(
                frame.loc[
                    frame[id_property].duplicated(
                        keep=False
                    ),
                    id_property,
                ].unique()
            )

            raise ValueError(
                f"Duplicate {id_property} values: "
                + ", ".join(duplicates)
            )

        if frame.geometry.isna().any():
            raise ValueError(
                f"{label} contains missing geometries."
            )

        if frame.geometry.is_empty.any():
            raise ValueError(
                f"{label} contains empty geometries."
            )

        invalid_count = int(
            (~frame.geometry.is_valid).sum()
        )

        if invalid_count:
            raise ValueError(
                f"{label} contains {invalid_count} "
                "invalid geometries."
            )

        non_polygonal = frame.loc[
            ~frame.geometry.geom_type.isin(
                ["Polygon", "MultiPolygon"]
            )
        ]

        if not non_polygonal.empty:
            raise ValueError(
                f"{label} contains "
                f"{len(non_polygonal)} "
                "non-polygonal geometries."
            )


def print_duplicate_summary(
    municipalities: gpd.GeoDataFrame,
    submunicipalities: gpd.GeoDataFrame,
) -> None:
    """
    Reports duplicate romanized and Korean administrative names.

    Duplicate names are expected in South Korea. This report is informational;
    stable administrative codes and hierarchy data allow later quiz generation
    to disambiguate them.
    """

    levels = [
        (
            "Municipality",
            municipalities,
            "municipality",
            "native_municipality",
        ),
        (
            "Submunicipality",
            submunicipalities,
            "submunicipality",
            "native_submunicipality",
        ),
    ]

    print()

    for (
        label,
        frame,
        romanized_property,
        native_property,
    ) in levels:
        romanized_counts = (
            frame[romanized_property]
            .value_counts()
        )

        native_counts = (
            frame[native_property]
            .value_counts()
        )

        duplicate_romanized = romanized_counts[
            romanized_counts > 1
        ]

        duplicate_native = native_counts[
            native_counts > 1
        ]

        print(
            f"{label} unique romanized names: "
            f"{frame[romanized_property].nunique()}"
        )

        print(
            f"{label} duplicate romanized names: "
            f"{len(duplicate_romanized)}"
        )

        print(
            f"{label} unique Korean names: "
            f"{frame[native_property].nunique()}"
        )

        print(
            f"{label} duplicate Korean names: "
            f"{len(duplicate_native)}"
        )

        print()


def write_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """
    Writes a GeoDataFrame as GeoJSON.
    """

    frame.to_file(
        path,
        driver="GeoJSON",
        index=False,
    )


def main() -> None:
    """
    Processes and exports South Korea's three administrative levels.
    """

    print("Reading South Korea provinces...")
    provinces_source = gpd.read_file(
        PROVINCES_SOURCE_PATH
    )

    print("Reading South Korea municipalities...")
    municipalities_source = gpd.read_file(
        MUNICIPALITIES_SOURCE_PATH
    )

    print(
        "Reading South Korea submunicipalities..."
    )
    submunicipalities_source = gpd.read_file(
        SUBMUNICIPALITIES_SOURCE_PATH
    )

    sources = [
        (
            "Provinces",
            provinces_source,
            EXPECTED_PROVINCES,
            2,
        ),
        (
            "Municipalities",
            municipalities_source,
            EXPECTED_MUNICIPALITIES,
            5,
        ),
        (
            "Submunicipalities",
            submunicipalities_source,
            EXPECTED_SUBMUNICIPALITIES,
            7,
        ),
    ]

    print()

    for (
        label,
        frame,
        expected_count,
        code_length,
    ) in sources:
        print(
            f"{label} source features: "
            f"{len(frame)}"
        )

        if len(frame) != expected_count:
            raise ValueError(
                f"Expected {expected_count} source "
                f"{label.lower()}, found {len(frame)}."
            )

        if frame.crs is None:
            raise ValueError(
                f"{label} source has no CRS."
            )

        validate_required_columns(
            frame,
            label,
        )

        validate_source_year(
            frame,
            label,
        )

        validate_source_codes(
            frame,
            label,
            code_length,
        )

        validate_source_names(
            frame,
            label,
        )

    if (
        provinces_source.crs
        != municipalities_source.crs
        or provinces_source.crs
        != submunicipalities_source.crs
    ):
        raise ValueError(
            "South Korea source layers do not "
            "use the same CRS."
        )

    print()
    print("Validating administrative hierarchy...")

    validate_hierarchy(
        provinces_source,
        municipalities_source,
        submunicipalities_source,
    )

    print("Administrative hierarchy is valid.")

    print()
    print("Repairing source geometries...")

    provinces_source = repair_geometries(
        provinces_source,
        "Provinces",
    )

    municipalities_source = repair_geometries(
        municipalities_source,
        "Municipalities",
    )

    submunicipalities_source = repair_geometries(
        submunicipalities_source,
        "Submunicipalities",
    )

    province_lookup = build_province_lookup(
        provinces_source
    )

    municipality_lookup = (
        build_municipality_lookup(
            municipalities_source
        )
    )

    print()
    print("Processing provinces...")

    provinces = process_provinces(
        provinces_source
    )

    print("Processing municipalities...")

    municipalities = process_municipalities(
        municipalities_source,
        province_lookup,
    )

    print("Processing submunicipalities...")

    submunicipalities = (
        process_submunicipalities(
            submunicipalities_source,
            province_lookup,
            municipality_lookup,
        )
    )

    print("Validating output...")

    validate_output(
        provinces,
        municipalities,
        submunicipalities,
    )

    print_duplicate_summary(
        municipalities,
        submunicipalities,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Writing provinces...")

    write_geojson(
        provinces,
        PROVINCES_PATH,
    )

    print("Writing municipalities...")

    write_geojson(
        municipalities,
        MUNICIPALITIES_PATH,
    )

    print("Writing submunicipalities...")

    write_geojson(
        submunicipalities,
        SUBMUNICIPALITIES_PATH,
    )

    print()
    print(
        "South Korea administrative processing complete."
    )

    print(
        f"Provinces: {len(provinces)}"
    )

    print(
        f"Municipalities: {len(municipalities)}"
    )

    print(
        "Submunicipalities: "
        f"{len(submunicipalities)}"
    )

    print()
    print("Municipalities by province:")

    municipality_counts = (
        municipalities
        .groupby("province")
        .size()
        .sort_index()
    )

    for province, count in (
        municipality_counts.items()
    ):
        print(
            f"  {province}: {count}"
        )

    print()
    print("Submunicipalities by province:")

    submunicipality_counts = (
        submunicipalities
        .groupby("province")
        .size()
        .sort_index()
    )

    for province, count in (
        submunicipality_counts.items()
    ):
        print(
            f"  {province}: {count}"
        )

    print()
    print("Output files:")
    print(f"  {PROVINCES_PATH}")
    print(f"  {MUNICIPALITIES_PATH}")
    print(f"  {SUBMUNICIPALITIES_PATH}")


if __name__ == "__main__":
    main()