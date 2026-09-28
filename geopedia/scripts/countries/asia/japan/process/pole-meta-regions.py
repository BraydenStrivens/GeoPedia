"""
Builds Japan's specialized pole-meta regions for GeoPedia.

These regions are used by quizzes that teach regional Japanese utility-pole
metas, such as pole plates and pole tops. They are intentionally separate
from GeoPedia's standard Japan regions because pole metas distinguish
Hokuriku from the remainder of Chubu.

The source is Japan's ADM1 prefecture boundary dataset. Every prefecture is
assigned to exactly one pole-meta region, then prefecture geometries are
dissolved to create the final regional boundaries.

GeoPedia's pole-meta model contains 10 regions:

    Hokkaido
    Tohoku
    Kanto
    Chubu
    Hokuriku
    Kansai
    Chugoku
    Shikoku
    Kyushu
    Okinawa

Hokuriku consists of Toyama, Ishikawa, and Fukui. The remaining prefectures
from GeoPedia's standard Chubu region remain assigned to Chubu.

Input:
    data/raw/countries/japan/jpn_adm_2019_shp/
        jpn_admbnda_adm1_2019.shp

Output:
    public/data/countries/japan/geojson/
        pole-meta-regions.geojson

The generated public file intentionally preserves the full processed geometry
without simplification because the resulting dataset is already small enough
for direct use by GeoPedia.

Run from the GeoPedia project root:

    python scripts/countries/japan/process/pole-meta-regions.py
"""

from pathlib import Path
import re

import geopandas as gpd
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_DIR = Path(
    "data/raw/countries/japan/jpn_adm_2019_shp"
)

OUTPUT_DIR = Path(
    "public/data/countries/japan/geojson"
)

ADM1_PATH = RAW_DIR / "jpn_admbnda_adm1_2019.shp"

OUTPUT_PATH = OUTPUT_DIR / "pole-meta-regions.geojson"


# ---------------------------------------------------------------------------
# Pole-meta region definitions
# ---------------------------------------------------------------------------

EXPECTED_PREFECTURE_COUNT = 47
EXPECTED_REGION_COUNT = 10


POLE_META_REGION_DEFINITIONS = {
    "hokkaido": {
        "pole_meta_region": "Hokkaido",
        "native_pole_meta_region": "北海道",
        "prefecture_ids": {
            "JP01",
        },
    },
    "tohoku": {
        "pole_meta_region": "Tohoku",
        "native_pole_meta_region": "東北",
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
        "pole_meta_region": "Kanto",
        "native_pole_meta_region": "関東",
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
        "pole_meta_region": "Chubu",
        "native_pole_meta_region": "中部",
        "prefecture_ids": {
            "JP15",  # Niigata
            "JP19",  # Yamanashi
            "JP20",  # Nagano
            "JP21",  # Gifu
            "JP22",  # Shizuoka
            "JP23",  # Aichi
        },
    },
    "hokuriku": {
        "pole_meta_region": "Hokuriku",
        "native_pole_meta_region": "北陸",
        "prefecture_ids": {
            "JP16",  # Toyama
            "JP17",  # Ishikawa
            "JP18",  # Fukui
        },
    },
    "kansai": {
        "pole_meta_region": "Kansai",
        "native_pole_meta_region": "関西",
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
        "pole_meta_region": "Chugoku",
        "native_pole_meta_region": "中国",
        "prefecture_ids": {
            "JP31",  # Tottori
            "JP32",  # Shimane
            "JP33",  # Okayama
            "JP34",  # Hiroshima
            "JP35",  # Yamaguchi
        },
    },
    "shikoku": {
        "pole_meta_region": "Shikoku",
        "native_pole_meta_region": "四国",
        "prefecture_ids": {
            "JP36",  # Tokushima
            "JP37",  # Kagawa
            "JP38",  # Ehime
            "JP39",  # Kochi
        },
    },
    "kyushu": {
        "pole_meta_region": "Kyushu",
        "native_pole_meta_region": "九州",
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
        "pole_meta_region": "Okinawa",
        "native_pole_meta_region": "沖縄",
        "prefecture_ids": {
            "JP47",
        },
    },
}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def clean_text(value: object) -> str:
    """
    Normalizes surrounding and repeated whitespace in source text.

    The source contains non-breaking spaces in some English names.
    """

    if value is None:
        return ""

    text = str(value).replace("\xa0", " ")

    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def extract_polygonal_geometry(geometry):
    """
    Returns only the polygonal components of a repaired geometry.

    Shapely's make_valid operation can produce GeometryCollections containing
    polygonal geometry together with lower-dimensional line or point
    artifacts. Only polygonal components belong in the region boundaries.
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

    return None


def repair_geometries(
    frame: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Repairs invalid ADM1 geometries before regional dissolving.

    The same ADM1 source used by GeoPedia's administrative processor contains
    invalid polygon geometries, so those defects are repaired before the
    pole-meta regions are constructed.
    """

    result = frame.copy()

    invalid_before = int(
        (~result.geometry.is_valid).sum()
    )

    print(
        "ADM1 invalid geometries before repair: "
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
            f"ADM1 contains {missing_polygonal} geometries "
            "with no polygonal components after repair."
        )

    non_polygonal = result.loc[
        ~result.geometry.geom_type.isin(
            ["Polygon", "MultiPolygon"]
        )
    ]

    if not non_polygonal.empty:
        raise ValueError(
            f"ADM1 contains {len(non_polygonal)} "
            "non-polygonal geometries after repair."
        )

    invalid_after = int(
        (~result.geometry.is_valid).sum()
    )

    print(
        "ADM1 invalid geometries after repair: "
        f"{invalid_after}"
    )

    if invalid_after:
        raise ValueError(
            f"ADM1 still contains {invalid_after} "
            "invalid geometries after repair."
        )

    return result


# ---------------------------------------------------------------------------
# Region lookup and validation
# ---------------------------------------------------------------------------


def build_region_lookup() -> dict[str, dict[str, str]]:
    """
    Builds a prefecture-ID lookup for pole-meta region metadata.

    Duplicate prefecture assignments are rejected immediately so a prefecture
    cannot silently belong to multiple pole-meta regions.
    """

    lookup: dict[str, dict[str, str]] = {}

    for (
        region_id,
        definition,
    ) in POLE_META_REGION_DEFINITIONS.items():
        for prefecture_id in definition["prefecture_ids"]:
            if prefecture_id in lookup:
                raise ValueError(
                    f"Prefecture ID {prefecture_id!r} appears "
                    "in multiple pole-meta region definitions."
                )

            lookup[prefecture_id] = {
                "pole_meta_region_id": region_id,
                "pole_meta_region": definition[
                    "pole_meta_region"
                ],
                "native_pole_meta_region": definition[
                    "native_pole_meta_region"
                ],
            }

    return lookup


def validate_region_definitions(
    source_prefecture_ids: set[str],
    region_lookup: dict[str, dict[str, str]],
) -> None:
    """
    Ensures all 47 source prefectures belong to exactly one pole-meta region.
    """

    if len(source_prefecture_ids) != EXPECTED_PREFECTURE_COUNT:
        raise ValueError(
            "Unexpected ADM1 prefecture count: "
            f"expected {EXPECTED_PREFECTURE_COUNT}, "
            f"found {len(source_prefecture_ids)}."
        )

    mapped_ids = set(region_lookup)

    missing = sorted(
        source_prefecture_ids - mapped_ids
    )

    extra = sorted(
        mapped_ids - source_prefecture_ids
    )

    if missing:
        raise ValueError(
            "Prefectures missing from "
            "POLE_META_REGION_DEFINITIONS: "
            + ", ".join(missing)
        )

    if extra:
        raise ValueError(
            "POLE_META_REGION_DEFINITIONS contains "
            "unknown prefectures: "
            + ", ".join(extra)
        )


# ---------------------------------------------------------------------------
# Region construction
# ---------------------------------------------------------------------------


def build_pole_meta_regions(
    source: gpd.GeoDataFrame,
    region_lookup: dict[str, dict[str, str]],
) -> gpd.GeoDataFrame:
    """
    Assigns ADM1 prefectures to pole-meta regions and dissolves their geometry.
    """

    records = []

    for _, row in source.iterrows():
        prefecture_id = clean_text(
            row["ADM1_PCODE"]
        )

        region = region_lookup[prefecture_id]

        records.append(
            {
                "pole_meta_region_id": region[
                    "pole_meta_region_id"
                ],
                "pole_meta_region": region[
                    "pole_meta_region"
                ],
                "native_pole_meta_region": region[
                    "native_pole_meta_region"
                ],
                "geometry": row.geometry,
            }
        )

    prefectures = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs=source.crs,
    )

    regions = prefectures.dissolve(
        by=[
            "pole_meta_region_id",
            "pole_meta_region",
            "native_pole_meta_region",
        ],
        as_index=False,
    )
    
    regions["pole_meta_region_ids"] = regions[
        "pole_meta_region_id"
    ].apply(
        lambda region_id: [
            f"{region_id}_1",
            f"{region_id}_2",
            f"{region_id}_3",
        ]
    )

    return regions[
        [
            "pole_meta_region_id",
            "pole_meta_region_ids",
            "pole_meta_region",
            "native_pole_meta_region",
            "geometry",
        ]
    ].copy()


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------


def validate_output(
    regions: gpd.GeoDataFrame,
) -> None:
    """
    Validates the final 10-feature pole-meta region dataset.
    """

    if len(regions) != EXPECTED_REGION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} pole-meta regions, "
            f"found {len(regions)}."
        )

    if regions["pole_meta_region_id"].duplicated().any():
        duplicates = sorted(
            regions.loc[
                regions[
                    "pole_meta_region_id"
                ].duplicated(keep=False),
                "pole_meta_region_id",
            ].unique()
        )

        raise ValueError(
            "Duplicate pole-meta region IDs: "
            + ", ".join(duplicates)
        )

    expected_ids = set(
        POLE_META_REGION_DEFINITIONS
    )

    actual_ids = set(
        regions["pole_meta_region_id"]
    )

    if actual_ids != expected_ids:
        missing = sorted(
            expected_ids - actual_ids
        )

        extra = sorted(
            actual_ids - expected_ids
        )

        raise ValueError(
            "Pole-meta region ID mismatch. "
            f"Missing: {missing}; extra: {extra}."
        )

    if regions.geometry.isna().any():
        raise ValueError(
            "Pole-meta regions contain missing geometries."
        )

    if regions.geometry.is_empty.any():
        raise ValueError(
            "Pole-meta regions contain empty geometries."
        )

    non_polygonal = regions.loc[
        ~regions.geometry.geom_type.isin(
            ["Polygon", "MultiPolygon"]
        )
    ]

    if not non_polygonal.empty:
        raise ValueError(
            f"Pole-meta regions contain {len(non_polygonal)} "
            "non-polygonal geometries."
        )

    invalid_count = int(
        (~regions.geometry.is_valid).sum()
    )

    if invalid_count:
        raise ValueError(
            f"Pole-meta regions contain {invalid_count} "
            "invalid geometries."
        )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_geojson(
    frame: gpd.GeoDataFrame,
    path: Path,
) -> None:
    """
    Writes the pole-meta regions as GeoJSON.
    """

    frame.to_file(
        path,
        driver="GeoJSON",
        index=False,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Builds and exports Japan's specialized pole-meta region geography.
    """

    print("Reading Japan ADM1...")

    adm1 = gpd.read_file(
        ADM1_PATH
    )

    if adm1.crs is None:
        raise ValueError(
            "ADM1 source has no CRS."
        )

    print(
        f"ADM1 source features: {len(adm1)}"
    )

    print()
    print("Repairing ADM1 geometries...")

    adm1 = repair_geometries(
        adm1
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
    print(
        "Building pole-meta regions from prefectures..."
    )

    regions = build_pole_meta_regions(
        adm1,
        region_lookup,
    )

    print("Validating output...")

    validate_output(
        regions
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Writing pole-meta regions...")

    write_geojson(
        regions,
        OUTPUT_PATH,
    )

    print()
    print(
        "Japan pole-meta region processing complete."
    )
    print(
        f"Pole-meta regions: {len(regions)}"
    )

    print()
    print("Prefectures by pole-meta region:")

    for (
        region_id,
        definition,
    ) in POLE_META_REGION_DEFINITIONS.items():
        print(
            f"  {definition['pole_meta_region']}: "
            f"{len(definition['prefecture_ids'])}"
        )

    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()