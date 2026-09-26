"""
Processes Japan's administrative boundary data for GeoPedia.

The source data contains:
- ADM1: 47 prefectures
- ADM2: 1,892 municipalities and wards

This script:
1. Repairs invalid source geometries.
2. Cleans and normalizes the prefecture data.
3. Assigns every prefecture to one of GeoPedia's nine Japanese regions.
4. Creates region boundaries by dissolving prefecture geometries.
5. Processes all ADM2 features as municipalities.
6. Normalizes English municipality type suffixes.
7. Adds prefecture and region hierarchy data to every municipality.

Japanese prefecture names are converted to their common short forms by
removing a trailing 都, 府, or 県. 北海道 is preserved unchanged.

English ADM2 administrative suffixes are normalized as follows:
- City -> City
- -ku -> Ward
- -cho -> Town
- -machi -> Town
- -mura -> Village
- -son -> Village
- Town -> Town

Japanese ADM2 names are otherwise preserved exactly as supplied by the
source apart from surrounding whitespace.

Input:
    data/raw/countries/japan/jpn_adm_2019_shp/
        jpn_admbnda_adm1_2019.shp
        jpn_admbnda_adm2_2019.shp

Outputs:
    data/intermediate/countries/japan/geojson/regions.geojson
    data/intermediate/countries/japan/geojson/prefectures.geojson
    data/intermediate/countries/japan/geojson/municipalities.geojson

Run from the GeoPedia project root:

    python scripts/countries/japan/process/admin.py
"""

from pathlib import Path
import re

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon


RAW_DIR = Path(
    "data/raw/countries/japan/jpn_adm_2019_shp"
)

OUTPUT_DIR = Path(
    "data/intermediate/countries/japan/geojson"
)

ADM1_PATH = RAW_DIR / "jpn_admbnda_adm1_2019.shp"
ADM2_PATH = RAW_DIR / "jpn_admbnda_adm2_2019.shp"

REGIONS_PATH = OUTPUT_DIR / "regions.geojson"
PREFECTURES_PATH = OUTPUT_DIR / "prefectures.geojson"
MUNICIPALITIES_PATH = OUTPUT_DIR / "municipalities.geojson"


# GeoPedia uses a nine-region model for Japan, with Okinawa treated as
# its own region rather than being included in Kyushu.
#
# Prefecture IDs come directly from the source ADM1_PCODE values.
REGION_DEFINITIONS = {
    "hokkaido": {
        "region": "Hokkaido",
        "native_region": "北海道",
        "prefecture_ids": {
            "JP01",
        },
    },
    "tohoku": {
        "region": "Tohoku",
        "native_region": "東北",
        "prefecture_ids": {
            "JP02",  # Aomori
            "JP03",  # Iwate
            "JP04",  # Miyagi
            "JP05",  # Akita
            "JP06",  # Yamagata
            "JP07",  # Fukushima
        },
    },
    "kanto": {
        "region": "Kanto",
        "native_region": "関東",
        "prefecture_ids": {
            "JP08",  # Ibaraki
            "JP09",  # Tochigi
            "JP10",  # Gunma
            "JP11",  # Saitama
            "JP12",  # Chiba
            "JP13",  # Tokyo
            "JP14",  # Kanagawa
        },
    },
    "chubu": {
        "region": "Chubu",
        "native_region": "中部",
        "prefecture_ids": {
            "JP15",  # Niigata
            "JP16",  # Toyama
            "JP17",  # Ishikawa
            "JP18",  # Fukui
            "JP19",  # Yamanashi
            "JP20",  # Nagano
            "JP21",  # Gifu
            "JP22",  # Shizuoka
            "JP23",  # Aichi
        },
    },
    "kansai": {
        "region": "Kansai",
        "native_region": "関西",
        "prefecture_ids": {
            "JP24",  # Mie
            "JP25",  # Shiga
            "JP26",  # Kyoto
            "JP27",  # Osaka
            "JP28",  # Hyogo
            "JP29",  # Nara
            "JP30",  # Wakayama
        },
    },
    "chugoku": {
        "region": "Chugoku",
        "native_region": "中国",
        "prefecture_ids": {
            "JP31",  # Tottori
            "JP32",  # Shimane
            "JP33",  # Okayama
            "JP34",  # Hiroshima
            "JP35",  # Yamaguchi
        },
    },
    "shikoku": {
        "region": "Shikoku",
        "native_region": "四国",
        "prefecture_ids": {
            "JP36",  # Tokushima
            "JP37",  # Kagawa
            "JP38",  # Ehime
            "JP39",  # Kochi
        },
    },
    "kyushu": {
        "region": "Kyushu",
        "native_region": "九州",
        "prefecture_ids": {
            "JP40",  # Fukuoka
            "JP41",  # Saga
            "JP42",  # Nagasaki
            "JP43",  # Kumamoto
            "JP44",  # Oita
            "JP45",  # Miyazaki
            "JP46",  # Kagoshima
        },
    },
    "okinawa": {
        "region": "Okinawa",
        "native_region": "沖縄",
        "prefecture_ids": {
            "JP47",
        },
    },
}


def clean_text(value: object) -> str:
    """
    Normalizes surrounding and repeated whitespace in source text.

    The source contains non-breaking spaces in some English names.
    """

    if value is None:
        return ""

    text = str(value).replace("\xa0", " ")

    return re.sub(r"\s+", " ", text).strip()


def clean_native_prefecture(value: object) -> str:
    """
    Converts Japanese prefecture names to their common short forms.

    Examples:
        愛知県 -> 愛知
        大阪府 -> 大阪
        京都府 -> 京都
        東京都 -> 東京

    北海道 is intentionally preserved as 北海道.
    """

    name = clean_text(value)

    if name == "北海道":
        return name

    if name.endswith(("都", "府", "県")):
        return name[:-1]

    return name


def remove_source_parenthetical(name: str) -> str:
    """
    Removes source-provided parenthetical qualifiers from ADM2 English names.

    Some source records contain inaccurate or inconsistent qualifiers such as:
        Hino-machi (Tokyo)
        Hirokawa-cho (Nagoya City)

    GeoPedia performs its own duplicate-name disambiguation using the actual
    prefecture hierarchy, so these source qualifiers should not be retained.
    """

    return re.sub(
        r"\s*\([^)]*\)\s*$",
        "",
        name,
    ).strip()


def normalize_municipality_name(
    value: object,
    native_value: object,
) -> str:
    """
    Normalizes an ADM2 English name and its administrative type.

    Administrative type suffixes are translated consistently:
        -ku -> Ward
        -cho / -machi -> Town
        -mura / -son -> Village

    Generic directional ward names are translated only when the Japanese
    name confirms that the entire base name is the corresponding direction.
    Compound proper names such as Higashiura and Minamiaso are preserved.

    Examples:
        Kita-ku / 北区 -> North Ward
        Minami-ku / 南区 -> South Ward
        Higashi-ku / 東区 -> East Ward
        Nishi-ku / 西区 -> West Ward
        Chuo-ku / 中央区 -> Central Ward
        Higashiura-cho / 東浦町 -> Higashiura Town
        Minamiaso-mura / 南阿蘇村 -> Minamiaso Village
    """

    name = remove_source_parenthetical(
        clean_text(value)
    )

    native_name = clean_text(native_value)

    directional_wards = {
        ("Kita-ku", "北区"): "North Ward",
        ("Minami-ku", "南区"): "South Ward",
        ("Higashi-ku", "東区"): "East Ward",
        ("Nishi-ku", "西区"): "West Ward",
        ("Chuo-ku", "中央区"): "Central Ward",
    }

    translated_ward = directional_wards.get(
        (name, native_name)
    )

    if translated_ward is not None:
        return translated_ward

    replacements = (
        ("-machi", " Town"),
        ("-mura", " Village"),
        ("-cho", " Town"),
        ("-son", " Village"),
        ("-ku", " Ward"),
    )

    lower_name = name.casefold()

    for suffix, replacement in replacements:
        if lower_name.endswith(suffix):
            return name[: -len(suffix)] + replacement

    return name
  

def build_region_lookup() -> dict[str, dict[str, str]]:
    """
    Builds a prefecture-ID lookup for region metadata.
    """

    lookup: dict[str, dict[str, str]] = {}

    for region_id, definition in REGION_DEFINITIONS.items():
        for prefecture_id in definition["prefecture_ids"]:
            if prefecture_id in lookup:
                raise ValueError(
                    f"Prefecture ID {prefecture_id!r} appears in "
                    "multiple region definitions."
                )

            lookup[prefecture_id] = {
                "region_id": region_id,
                "region": definition["region"],
                "native_region": definition["native_region"],
            }

    return lookup


def validate_region_definitions(
    prefecture_ids: set[str],
    region_lookup: dict[str, dict[str, str]],
) -> None:
    """
    Ensures every source prefecture belongs to exactly one region and
    that the region table contains no unknown prefecture IDs.
    """

    mapped_ids = set(region_lookup)

    missing = sorted(prefecture_ids - mapped_ids)
    extra = sorted(mapped_ids - prefecture_ids)

    if missing:
        raise ValueError(
            "Prefectures missing from REGION_DEFINITIONS: "
            + ", ".join(missing)
        )

    if extra:
        raise ValueError(
            "REGION_DEFINITIONS contains unknown prefectures: "
            + ", ".join(extra)
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

    The source Japan boundary data contains invalid polygon geometries.
    Repairing them before dissolving prevents those source defects from
    propagating into the derived region geometries.
    """

    result = frame.copy()

    invalid_before = int(
        (~result.geometry.is_valid).sum()
    )

    print(
        f"{label} invalid geometries before repair: "
        f"{invalid_before}"
    )

    if invalid_before:
        result.geometry = result.geometry.make_valid()

    result.geometry = result.geometry.apply(
        extract_polygonal_geometry
    )
    
    missing_polygonal = int(
        result.geometry.isna().sum()
    )

    if missing_polygonal:
        raise ValueError(
            f"{label} contains {missing_polygonal} geometries "
            "with no polygonal components after repair."
        )

    invalid_after = int(
        (~result.geometry.is_valid).sum()
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


def process_prefectures(
    source: gpd.GeoDataFrame,
    region_lookup: dict[str, dict[str, str]],
) -> gpd.GeoDataFrame:
    """
    Converts ADM1 source features into GeoPedia prefectures.
    """

    records = []

    for _, row in source.iterrows():
        prefecture_id = clean_text(
            row["ADM1_PCODE"]
        )

        region = region_lookup[prefecture_id]

        records.append(
            {
                "prefecture_id": prefecture_id,
                "prefecture": clean_text(
                    row["ADM1_EN"]
                ),
                "native_prefecture": clean_native_prefecture(
                    row["ADM1_JA"]
                ),
                "region_id": region["region_id"],
                "region": region["region"],
                "native_region": region["native_region"],
                "geometry": row.geometry,
            }
        )

    result = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=source.crs,
    )

    if result["prefecture_id"].duplicated().any():
        duplicates = sorted(
            result.loc[
                result["prefecture_id"].duplicated(
                    keep=False
                ),
                "prefecture_id",
            ].unique()
        )

        raise ValueError(
            "Duplicate prefecture IDs: "
            + ", ".join(duplicates)
        )

    return result


def process_municipalities(
    source: gpd.GeoDataFrame,
    region_lookup: dict[str, dict[str, str]],
) -> gpd.GeoDataFrame:
    """
    Converts ADM2 source features into GeoPedia municipalities.

    All 1,892 source ADM2 polygons are retained, including wards.

    English municipality names receive consistent English administrative
    type suffixes while Japanese names are retained from the source.
    """

    records = []

    for _, row in source.iterrows():
        prefecture_id = clean_text(
            row["ADM1_PCODE"]
        )

        region = region_lookup[prefecture_id]

        records.append(
            {
                "municipality_id": clean_text(
                    row["ADM2_PCODE"]
                ),
                "municipality": normalize_municipality_name(
                    row["ADM2_EN"],
                    row["ADM2_JA"]
                ),
                "native_municipality": clean_text(
                    row["ADM2_JA"]
                ),
                "prefecture_id": prefecture_id,
                "prefecture": clean_text(
                    row["ADM1_EN"]
                ),
                "native_prefecture": clean_native_prefecture(
                    row["ADM1_JA"]
                ),
                "region_id": region["region_id"],
                "region": region["region"],
                "native_region": region["native_region"],
                "geometry": row.geometry,
            }
        )

    result = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=source.crs,
    )

    if result["municipality_id"].duplicated().any():
        duplicates = sorted(
            result.loc[
                result["municipality_id"].duplicated(
                    keep=False
                ),
                "municipality_id",
            ].unique()
        )

        raise ValueError(
            "Duplicate municipality IDs: "
            + ", ".join(duplicates)
        )

    return result


def build_regions(
    prefectures: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Creates Japan's nine GeoPedia regions by dissolving prefectures.
    """

    regions = prefectures.dissolve(
        by=[
            "region_id",
            "region",
            "native_region",
        ],
        as_index=False,
    )

    return regions[
        [
            "region_id",
            "region",
            "native_region",
            "geometry",
        ]
    ].copy()


def validate_output(
    regions: gpd.GeoDataFrame,
    prefectures: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame,
) -> None:
    """
    Performs structural and geometry validation before writing output.
    """

    expected_regions = 9
    expected_prefectures = 47
    expected_municipalities = 1892

    if len(regions) != expected_regions:
        raise ValueError(
            f"Expected {expected_regions} regions, "
            f"found {len(regions)}."
        )

    if len(prefectures) != expected_prefectures:
        raise ValueError(
            f"Expected {expected_prefectures} prefectures, "
            f"found {len(prefectures)}."
        )

    if len(municipalities) != expected_municipalities:
        raise ValueError(
            f"Expected {expected_municipalities} municipalities, "
            f"found {len(municipalities)}."
        )

    for name, frame in [
        ("regions", regions),
        ("prefectures", prefectures),
        ("municipalities", municipalities),
    ]:
        if frame.geometry.isna().any():
            raise ValueError(
                f"{name} contains missing geometries."
            )

        if frame.geometry.is_empty.any():
            raise ValueError(
                f"{name} contains empty geometries."
            )

        invalid_count = int(
            (~frame.geometry.is_valid).sum()
        )

        if invalid_count:
            raise ValueError(
                f"{name} contains {invalid_count} "
                "invalid geometries."
            )


def print_duplicate_summary(
    municipalities: gpd.GeoDataFrame,
) -> None:
    """
    Reports duplicate English and Japanese municipality names.

    Duplicate names are expected in Japan. This report is informational;
    the quiz-data generator will later disambiguate them using hierarchy.
    """

    english_counts = (
        municipalities["municipality"]
        .value_counts()
    )

    native_counts = (
        municipalities["native_municipality"]
        .value_counts()
    )

    duplicate_english = english_counts[
        english_counts > 1
    ]

    duplicate_native = native_counts[
        native_counts > 1
    ]

    print()
    print(
        "Unique English municipality names: "
        f"{municipalities['municipality'].nunique()}"
    )
    print(
        "Duplicate English municipality names: "
        f"{len(duplicate_english)}"
    )

    print(
        "Unique Japanese municipality names: "
        f"{municipalities['native_municipality'].nunique()}"
    )
    print(
        "Duplicate Japanese municipality names: "
        f"{len(duplicate_native)}"
    )


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
    Processes and exports Japan's region, prefecture, and municipality data.
    """

    print("Reading Japan ADM1...")
    adm1 = gpd.read_file(ADM1_PATH)

    print("Reading Japan ADM2...")
    adm2 = gpd.read_file(ADM2_PATH)

    if adm1.crs is None:
        raise ValueError(
            "ADM1 source has no CRS."
        )

    if adm2.crs is None:
        raise ValueError(
            "ADM2 source has no CRS."
        )

    if adm1.crs != adm2.crs:
        raise ValueError(
            f"ADM1 CRS {adm1.crs} does not match "
            f"ADM2 CRS {adm2.crs}."
        )

    print(
        f"ADM1 source features: {len(adm1)}"
    )
    print(
        f"ADM2 source features: {len(adm2)}"
    )

    print()
    print("Repairing source geometries...")

    adm1 = repair_geometries(
        adm1,
        "ADM1",
    )

    adm2 = repair_geometries(
        adm2,
        "ADM2",
    )

    region_lookup = build_region_lookup()

    source_prefecture_ids = {
        clean_text(value)
        for value in adm1["ADM1_PCODE"]
    }

    validate_region_definitions(
        source_prefecture_ids,
        region_lookup,
    )

    print()
    print("Processing prefectures...")

    prefectures = process_prefectures(
        adm1,
        region_lookup,
    )

    print("Processing municipalities...")

    municipalities = process_municipalities(
        adm2,
        region_lookup,
    )

    print("Building regions from prefectures...")

    regions = build_regions(
        prefectures
    )

    print("Validating output...")

    validate_output(
        regions,
        prefectures,
        municipalities,
    )

    print_duplicate_summary(
        municipalities
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("Writing regions...")

    write_geojson(
        regions,
        REGIONS_PATH,
    )

    print("Writing prefectures...")

    write_geojson(
        prefectures,
        PREFECTURES_PATH,
    )

    print("Writing municipalities...")

    write_geojson(
        municipalities,
        MUNICIPALITIES_PATH,
    )

    print()
    print(
        "Japan administrative processing complete."
    )
    print(
        f"Regions: {len(regions)}"
    )
    print(
        f"Prefectures: {len(prefectures)}"
    )
    print(
        f"Municipalities: {len(municipalities)}"
    )

    print()
    print("Municipalities by region:")

    region_counts = (
        municipalities
        .groupby("region")
        .size()
        .sort_index()
    )

    for region, count in region_counts.items():
        print(
            f"  {region}: {count}"
        )

    print()
    print("Output files:")
    print(f"  {REGIONS_PATH}")
    print(f"  {PREFECTURES_PATH}")
    print(f"  {MUNICIPALITIES_PATH}")


if __name__ == "__main__":
    main()