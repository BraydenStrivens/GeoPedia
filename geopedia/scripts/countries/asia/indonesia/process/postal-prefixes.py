"""
Generate Indonesia 1-digit and 2-digit postal-prefix GeoJSON.

Purpose
-------
This script generates GeoPedia's Indonesia postal-prefix boundary files from
the already processed and simplified regency/city GeoJSON.

The raw postcode dataset contains 514 kabupaten/kota. Each is matched
one-to-one with the 514 administrative polygons in GeoPedia's regencies
GeoJSON using:

    - province
    - normalized kabupaten/kota name
    - administrative type (Kabupaten or Kota)
    - explicit aliases for known cross-dataset naming differences

For each kabupaten/kota, the dominant 2-digit postal prefix is determined from
the village records in desakel.csv.

The public regency geometry is already simplified, so this script does not
perform any additional simplification.

Eight non-administrative features in regencies.geojson represent lakes,
reservoirs, or forest rather than kabupaten/kota. They have no postcode
records. Each is assigned a prefix from neighboring administrative polygons.
The script requires an unambiguous neighboring prefix and fails rather than
silently choosing between conflicting candidates.

After every regency polygon has a prefix:

    1. polygons are dissolved by 2-digit prefix
    2. the first digit is derived from each 2-digit prefix
    3. polygons are dissolved again by 1-digit prefix

Inputs
------
Raw postcode hierarchy:

    data/raw/countries/indonesia/post-code-data/prov.csv
    data/raw/countries/indonesia/post-code-data/kabkota.csv
    data/raw/countries/indonesia/post-code-data/desakel.csv

Already simplified GeoPedia geometry:

    public/data/countries/indonesia/geojson/regencies.geojson

Outputs
-------
    public/data/countries/indonesia/geojson/postal-prefixes-2.geojson
    public/data/countries/indonesia/geojson/postal-prefixes-1.geojson

Output properties
-----------------
2-digit:

    {
        "prefix_2": "23"
    }

1-digit:

    {
        "prefix_1": "2"
    }

Feature IDs are the corresponding prefix values.

Requirements
------------
    pip install geopandas shapely

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/process/postal-prefixes.py
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd
import pandas as pd


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

POSTCODE_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "indonesia"
    / "post-code-data"
)

PUBLIC_GEOJSON_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "indonesia"
    / "geojson"
)

PROVINCES_CSV = (
    POSTCODE_DATA_DIR
    / "prov.csv"
)

KABKOTA_CSV = (
    POSTCODE_DATA_DIR
    / "kabkota.csv"
)

VILLAGES_CSV = (
    POSTCODE_DATA_DIR
    / "desakel.csv"
)

REGENCIES_GEOJSON = (
    PUBLIC_GEOJSON_DIR
    / "regencies.geojson"
)

PREFIX_2_GEOJSON = (
    PUBLIC_GEOJSON_DIR
    / "postal-prefixes-2.geojson"
)

PREFIX_1_GEOJSON = (
    PUBLIC_GEOJSON_DIR
    / "postal-prefixes-1.geojson"
)


# ---------------------------------------------------------------------------
# Expected counts
# ---------------------------------------------------------------------------

EXPECTED_PROVINCE_COUNT = 34
EXPECTED_KABKOTA_COUNT = 514
EXPECTED_VILLAGE_COUNT = 83_436
EXPECTED_REGENCY_FEATURE_COUNT = 522
EXPECTED_ADMINISTRATIVE_COUNT = 514
EXPECTED_SPECIAL_FEATURE_COUNT = 8

EXPECTED_PREFIX_2_COUNT = 83


# ---------------------------------------------------------------------------
# Special GeoJSON features
# ---------------------------------------------------------------------------

SPECIAL_GEOJSON_FEATURE_IDS = {
    "ID1288",  # Danau Toba
    "ID1388",  # Danau
    "ID1688",  # Danau
    "ID1888",  # Danau
    "ID3288",  # Waduk Cirata
    "ID3388",  # Wadung Kedungombo
    "ID3399",  # Hutan
    "ID7188",  # Danau
}


# ---------------------------------------------------------------------------
# Explicit cross-dataset aliases
# ---------------------------------------------------------------------------

REGENCY_POSTCODE_ALIASES = {
    "ID1607": "16.07",  # Banyu Asin -> Banyuasin
    "ID5107": "51.07",  # Karang Asem -> Karangasem
    "ID6372": "63.72",  # Kota Banjar Baru -> Banjarbaru
    "ID6302": "63.02",  # Kota Baru -> Kotabaru
    "ID7472": "74.72",  # Kota Baubau -> Bau-Bau
    "ID1674": "16.73",  # Kota Lubuklinggau -> Lubuk Linggau
    "ID1277": "12.77",  # Kota Padangsidimpuan -> Padang Sidempuan
    "ID1572": "15.72",  # Kota Sungai Penuh -> Sungaipenuh
    "ID1207": "12.10",  # Labuhan Batu -> Labuhanbatu
    "ID1222": "12.22",  # Labuhan Batu Selatan -> Labuhanbatu Selatan
    "ID1223": "12.23",  # Labuhan Batu Utara -> Labuhanbatu Utara
    "ID6411": "64.11",  # Mahakam Hulu -> Mahakam Ulu
    "ID1706": "17.06",  # Mukomuko -> Muko Muko
    "ID7309": "73.10",  # Pangkajene Dan Kepulauan -> Pangkajene Kepulauan
    "ID7108": "71.09",  # Siau Tagulandang Biaro -> Kepulauan ... (Sitaro)
    "ID1808": "18.05",  # Tulangbawang -> Tulang Bawang
}


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

NON_ALPHANUMERIC_PATTERN = re.compile(
    r"[^a-z0-9]+"
)

PARENTHETICAL_PATTERN = re.compile(
    r"\([^)]*\)"
)

ADMINISTRATIVE_PREFIX_PATTERN = re.compile(
    r"^(kabupaten|kota)\s+",
    re.IGNORECASE,
)


def normalize_kabkota_id(
    admin_id: str,
) -> str:
    """
    Normalize kabkota.csv IDs to the form used by descendant records.

    Some IDs have lost a trailing zero.

    Examples:
        11.01 -> 11.01
        11.1  -> 11.10
        12.2  -> 12.20
    """

    province, child = admin_id.split(
        "."
    )

    return (
        f"{province}."
        f"{child.ljust(2, '0')}"
    )


def normalize_text(
    value: str,
) -> str:
    """Normalize Unicode, punctuation, capitalization, and whitespace."""

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )

    value = value.lower()

    value = NON_ALPHANUMERIC_PATTERN.sub(
        " ",
        value,
    )

    return " ".join(
        value.split()
    )


def normalize_province_name(
    value: str,
) -> str:
    """Normalize province names across datasets."""

    value = PARENTHETICAL_PATTERN.sub(
        "",
        value,
    )

    normalized = normalize_text(
        value
    )

    aliases = {
        "dki jakarta": "jakarta",
        "di yogyakarta": "yogyakarta",
    }

    return aliases.get(
        normalized,
        normalized,
    )


def normalize_regency_name(
    value: str,
) -> str:
    """Normalize a kabupaten/kota name without its administrative prefix."""

    value = PARENTHETICAL_PATTERN.sub(
        "",
        value,
    )

    value = ADMINISTRATIVE_PREFIX_PATTERN.sub(
        "",
        value.strip(),
    )

    return normalize_text(
        value
    )


def normalize_admin_type(
    value: str,
) -> str:
    """Normalize Kabupaten/Kota type text."""

    return normalize_text(
        value
    )


def get_geojson_admin_type(
    regency_name: str,
) -> str:
    """Infer Kabupaten/Kota from GeoPedia's canonical name."""

    if regency_name.lower().startswith(
        "kota "
    ):
        return "kota"

    return "kabupaten"


# ---------------------------------------------------------------------------
# Postcode data
# ---------------------------------------------------------------------------

def load_postcode_provinces() -> dict[str, str]:
    """Load postcode province IDs and names."""

    provinces: dict[str, str] = {}

    with PROVINCES_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        for row in reader:
            province_id = row[
                "id"
            ].strip()

            name = row[
                "nm"
            ].strip()

            if province_id in provinces:
                raise ValueError(
                    f"Duplicate postcode province ID: {province_id}"
                )

            provinces[
                province_id
            ] = name

    if len(provinces) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            "Unexpected postcode province count: "
            f"{len(provinces):,}"
        )

    return provinces


def load_kabkota() -> dict[
    str,
    tuple[str, str, str],
]:
    """
    Load postcode Admin 2 units.

    Returns:
        admin_id -> (province_id, name, admin_type)
    """

    records: dict[
        str,
        tuple[str, str, str],
    ] = {}

    with KABKOTA_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        for row in reader:
            admin_id = normalize_kabkota_id(
                row[
                    "id"
                ].strip()
            )

            province_id = admin_id.split(
                ".",
                maxsplit=1,
            )[0]

            name = row[
                "nm"
            ].strip()

            admin_type = row[
                "type"
            ].strip()

            if admin_id in records:
                raise ValueError(
                    f"Duplicate postcode Admin 2 ID: {admin_id}"
                )

            records[
                admin_id
            ] = (
                province_id,
                name,
                admin_type,
            )

    if len(records) != EXPECTED_KABKOTA_COUNT:
        raise ValueError(
            "Unexpected postcode Admin 2 count: "
            f"{len(records):,}"
        )

    return records


def get_admin_2_id(
    village_id: str,
) -> str:
    """Extract the Admin 2 parent from a postcode village ID."""

    parts = village_id.split(
        "."
    )

    if len(parts) != 4:
        raise ValueError(
            f"Unexpected village ID: {village_id!r}"
        )

    return ".".join(
        parts[:2]
    )


def load_dominant_prefixes(
    kabkota: dict[
        str,
        tuple[str, str, str],
    ],
) -> dict[str, str]:
    """Determine the dominant 2-digit prefix for every postcode Admin 2."""

    counts: dict[
        str,
        Counter[str],
    ] = defaultdict(
        Counter
    )

    row_count = 0

    with VILLAGES_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        for row in reader:
            row_count += 1

            village_id = row[
                "id"
            ].strip()

            postcode = row[
                "zip"
            ].strip()

            if (
                len(postcode) != 5
                or not postcode.isdigit()
            ):
                raise ValueError(
                    f"Invalid postcode {postcode!r} "
                    f"for village {village_id!r}."
                )

            admin_id = get_admin_2_id(
                village_id
            )

            if admin_id not in kabkota:
                raise ValueError(
                    f"Unknown postcode Admin 2 ID: {admin_id}"
                )

            counts[
                admin_id
            ][
                postcode[:2]
            ] += 1

    if row_count != EXPECTED_VILLAGE_COUNT:
        raise ValueError(
            "Unexpected village count: "
            f"expected {EXPECTED_VILLAGE_COUNT:,}, "
            f"got {row_count:,}."
        )

    missing = (
        set(kabkota)
        - set(counts)
    )

    if missing:
        raise ValueError(
            "Postcode Admin 2 units without village records: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    return {
        admin_id: prefix_counts.most_common(
            1
        )[0][0]
        for admin_id, prefix_counts in counts.items()
    }


# ---------------------------------------------------------------------------
# Province crosswalk
# ---------------------------------------------------------------------------

def build_province_crosswalk(
    postcode_provinces: dict[str, str],
    regencies: gpd.GeoDataFrame,
) -> dict[str, str]:
    """Map GeoPedia province IDs to postcode province IDs."""

    postcode_by_name: dict[
        str,
        list[str],
    ] = defaultdict(
        list
    )

    for province_id, name in postcode_provinces.items():
        postcode_by_name[
            normalize_province_name(
                name
            )
        ].append(
            province_id
        )

    geojson_provinces = (
        regencies[
            [
                "province_id",
                "province",
            ]
        ]
        .drop_duplicates()
    )

    if len(geojson_provinces) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            "Unexpected province count in regencies.geojson: "
            f"{len(geojson_provinces):,}"
        )

    crosswalk: dict[str, str] = {}

    for row in geojson_provinces.itertuples(
        index=False
    ):
        normalized_name = normalize_province_name(
            str(
                row.province
            )
        )

        candidates = postcode_by_name.get(
            normalized_name,
            [],
        )

        if len(candidates) != 1:
            raise ValueError(
                "Could not uniquely match province: "
                f"{row.province_id} | {row.province} | "
                f"candidates={candidates}"
            )

        crosswalk[
            str(
                row.province_id
            )
        ] = candidates[
            0
        ]

    return crosswalk


# ---------------------------------------------------------------------------
# Regency crosswalk
# ---------------------------------------------------------------------------

def build_postcode_index(
    kabkota: dict[
        str,
        tuple[str, str, str],
    ],
) -> dict[
    tuple[str, str, str],
    list[str],
]:
    """Index postcode Admin 2 units by province, name, and type."""

    index: dict[
        tuple[str, str, str],
        list[str],
    ] = defaultdict(
        list
    )

    for admin_id, (
        province_id,
        name,
        admin_type,
    ) in kabkota.items():
        key = (
            province_id,
            normalize_regency_name(
                name
            ),
            normalize_admin_type(
                admin_type
            ),
        )

        index[
            key
        ].append(
            admin_id
        )

    return index


def build_regency_prefix_crosswalk(
    regencies: gpd.GeoDataFrame,
    province_crosswalk: dict[str, str],
    kabkota: dict[
        str,
        tuple[str, str, str],
    ],
    dominant_prefixes: dict[str, str],
) -> dict[str, str]:
    """
    Map each administrative GeoJSON regency ID to its dominant prefix.

    Every one of the 514 postcode Admin 2 units must be consumed exactly once.
    """

    postcode_index = build_postcode_index(
        kabkota
    )

    regency_prefixes: dict[str, str] = {}
    used_postcode_ids: set[str] = set()

    for row in regencies.itertuples():
        regency_id = str(
            row.regency_id
        )

        if regency_id in SPECIAL_GEOJSON_FEATURE_IDS:
            continue

        if regency_id in REGENCY_POSTCODE_ALIASES:
            postcode_id = REGENCY_POSTCODE_ALIASES[
                regency_id
            ]

            if postcode_id not in kabkota:
                raise ValueError(
                    f"Alias {regency_id} points to unknown "
                    f"postcode ID {postcode_id}."
                )

        else:
            province_id = str(
                row.province_id
            )

            postcode_province_id = province_crosswalk[
                province_id
            ]

            key = (
                postcode_province_id,
                normalize_regency_name(
                    str(
                        row.regency
                    )
                ),
                get_geojson_admin_type(
                    str(
                        row.regency
                    )
                ),
            )

            candidates = postcode_index.get(
                key,
                [],
            )

            if len(candidates) != 1:
                raise ValueError(
                    "Could not uniquely match GeoJSON Admin 2: "
                    f"{regency_id} | "
                    f"{row.province} | "
                    f"{row.regency} | "
                    f"candidates={candidates}"
                )

            postcode_id = candidates[
                0
            ]

        if postcode_id in used_postcode_ids:
            raise ValueError(
                f"Postcode Admin 2 {postcode_id} "
                f"was matched more than once."
            )

        used_postcode_ids.add(
            postcode_id
        )

        regency_prefixes[
            regency_id
        ] = dominant_prefixes[
            postcode_id
        ]

    if len(regency_prefixes) != EXPECTED_ADMINISTRATIVE_COUNT:
        raise ValueError(
            "Unexpected administrative crosswalk count: "
            f"expected {EXPECTED_ADMINISTRATIVE_COUNT:,}, "
            f"got {len(regency_prefixes):,}."
        )

    unused_postcode_ids = (
        set(kabkota)
        - used_postcode_ids
    )

    if unused_postcode_ids:
        raise ValueError(
            "Unused postcode Admin 2 IDs: "
            + ", ".join(
                sorted(
                    unused_postcode_ids
                )
            )
        )

    return regency_prefixes


# ---------------------------------------------------------------------------
# Special feature assignment
# ---------------------------------------------------------------------------

def assign_special_features(
    regencies: gpd.GeoDataFrame,
    regency_prefixes: dict[str, str],
) -> dict[str, str]:
    """
    Inspect neighboring postal prefixes for non-administrative polygons.

    Each special feature is compared with the administrative polygons that
    share a non-zero boundary length with it.

    If exactly one prefix touches the feature, that prefix is returned.

    If multiple prefixes touch the feature, they are returned as a
    slash-separated diagnostic value such as "32/34". These diagnostic
    values are not valid final assignments; main() stops before generating
    output when any are present.

    Point-only contacts are ignored.
    """

    administrative = regencies[
        regencies[
            "regency_id"
        ].astype(
            str
        ).isin(
            regency_prefixes
        )
    ].copy()

    administrative[
        "prefix_2"
    ] = administrative[
        "regency_id"
    ].astype(
        str
    ).map(
        regency_prefixes
    )

    spatial_index = administrative.sindex

    assignments: dict[str, str] = {}

    specials = regencies[
        regencies[
            "regency_id"
        ].astype(
            str
        ).isin(
            SPECIAL_GEOJSON_FEATURE_IDS
        )
    ]

    if len(specials) != EXPECTED_SPECIAL_FEATURE_COUNT:
        raise ValueError(
            "Unexpected special-feature count: "
            f"expected {EXPECTED_SPECIAL_FEATURE_COUNT}, "
            f"got {len(specials)}."
        )

    for row in specials.itertuples():
        special_id = str(
            row.regency_id
        )

        geometry = row.geometry

        candidate_positions = list(
            spatial_index.query(
                geometry,
                predicate="intersects",
            )
        )

        touching_prefixes: set[str] = set()

        for position in candidate_positions:
            neighbor = administrative.iloc[
                position
            ]

            neighbor_geometry = neighbor.geometry

            boundary_intersection = (
                geometry.boundary.intersection(
                    neighbor_geometry.boundary
                )
            )

            if boundary_intersection.length <= 0:
                continue

            touching_prefixes.add(
                str(
                    neighbor[
                        "prefix_2"
                    ]
                )
            )

        if len(touching_prefixes) == 0:
            assignments[
                special_id
            ] = "NONE"

            continue

        assignments[
            special_id
        ] = "/".join(
            sorted(
                touching_prefixes
            )
        )

    return assignments

# ---------------------------------------------------------------------------
# Dissolving
# ---------------------------------------------------------------------------

def dissolve_prefixes(
    regencies: gpd.GeoDataFrame,
    all_prefixes: dict[str, str],
) -> tuple[
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
]:
    """Create dissolved 2-digit and 1-digit prefix GeoDataFrames."""

    working = regencies[
        [
            "regency_id",
            "geometry",
        ]
    ].copy()

    working[
        "regency_id"
    ] = working[
        "regency_id"
    ].astype(
        str
    )

    working[
        "prefix_2"
    ] = working[
        "regency_id"
    ].map(
        all_prefixes
    )

    working = working[
        working[
            "prefix_2"
        ].notna()
    ].copy()

    prefix_2 = (
        working[
            [
                "prefix_2",
                "geometry",
            ]
        ]
        .dissolve(
            by="prefix_2",
            as_index=False,
        )
    )

    prefix_2[
        "prefix_2"
    ] = prefix_2[
        "prefix_2"
    ].astype(
        str
    )
    
    prefix_2[
        "prefix_1"
    ] = prefix_2[
        "prefix_2"
    ].str[
        0
    ]

    prefix_2[
        "id"
    ] = prefix_2[
        "prefix_2"
    ]

    prefix_2 = prefix_2[
        [
            "id",
            "prefix_2",
            "prefix_1",
            "geometry",
        ]
    ].sort_values(
        "prefix_2"
    ).reset_index(
        drop=True
    )

    if len(prefix_2) != EXPECTED_PREFIX_2_COUNT:
        raise ValueError(
            "Unexpected 2-digit prefix count: "
            f"expected {EXPECTED_PREFIX_2_COUNT}, "
            f"got {len(prefix_2)}."
        )

    prefix_1_source = prefix_2[
        [
            "prefix_2",
            "geometry",
        ]
    ].copy()

    prefix_1_source[
        "prefix_1"
    ] = prefix_1_source[
        "prefix_2"
    ].str[
        0
    ]

    prefix_1 = (
        prefix_1_source[
            [
                "prefix_1",
                "geometry",
            ]
        ]
        .dissolve(
            by="prefix_1",
            as_index=False,
        )
    )

    prefix_1[
        "id"
    ] = prefix_1[
        "prefix_1"
    ]

    prefix_1 = prefix_1[
        [
            "id",
            "prefix_1",
            "geometry",
        ]
    ].sort_values(
        "prefix_1"
    ).reset_index(
        drop=True
    )

    return (
        prefix_2,
        prefix_1,
    )


# ---------------------------------------------------------------------------
# GeoJSON writing
# ---------------------------------------------------------------------------

def write_geojson(
    dataframe: gpd.GeoDataFrame,
    path: Path,
    id_property: str,
) -> None:
    """
    Write compact GeoJSON with the prefix also used as the feature ID.

    GeoPandas writes properties normally but does not automatically use an
    arbitrary property as the top-level GeoJSON feature ID, so the generated
    file is adjusted after serialization.
    """

    import json

    temporary_path = path.with_suffix(
        ".tmp.geojson"
    )

    dataframe.to_file(
        temporary_path,
        driver="GeoJSON",
    )

    with temporary_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    for feature in data[
        "features"
    ]:
        properties = feature[
            "properties"
        ]

        feature[
            "id"
        ] = properties[
            id_property
        ]

        properties.pop(
            "id",
            None,
        )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    temporary_path.unlink()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate Indonesia 1-digit and 2-digit postal-prefix GeoJSON."""

    print(
        "Generating Indonesia postal-prefix GeoJSON..."
    )
    print()

    postcode_provinces = load_postcode_provinces()

    kabkota = load_kabkota()

    dominant_prefixes = load_dominant_prefixes(
        kabkota
    )

    print(
        f"Postcode kabupaten/kota:        {len(kabkota):,}"
    )
    print(
        f"Unique dominant prefixes:       "
        f"{len(set(dominant_prefixes.values())):,}"
    )
    print()

    regencies = gpd.read_file(
        REGENCIES_GEOJSON
    )

    required_properties = {
        "regency_id",
        "regency",
        "province_id",
        "province",
    }

    missing_properties = (
        required_properties
        - set(
            regencies.columns
        )
    )

    if missing_properties:
        raise ValueError(
            "regencies.geojson is missing properties: "
            + ", ".join(
                sorted(
                    missing_properties
                )
            )
        )

    if len(regencies) != EXPECTED_REGENCY_FEATURE_COUNT:
        raise ValueError(
            "Unexpected regency feature count: "
            f"expected {EXPECTED_REGENCY_FEATURE_COUNT:,}, "
            f"got {len(regencies):,}."
        )

    province_crosswalk = build_province_crosswalk(
        postcode_provinces,
        regencies,
    )

    regency_prefixes = build_regency_prefix_crosswalk(
        regencies,
        province_crosswalk,
        kabkota,
        dominant_prefixes,
    )

    print(
        "Administrative crosswalk:      "
        f"{len(regency_prefixes):,} / "
        f"{EXPECTED_ADMINISTRATIVE_COUNT:,}"
    )
    print()

    special_assignments = assign_special_features(
        regencies,
        regency_prefixes,
    )

    print(
        "SPECIAL FEATURE ASSIGNMENTS"
    )
    print(
        "-" * 72
    )

    special_lookup = (
        regencies.set_index(
            "regency_id"
        )
    )

    for special_id in sorted(
        special_assignments
    ):
        name = special_lookup.loc[
            special_id,
            "regency",
        ]

        print(
            f"{special_id:<10} "
            f"{str(name):<28} -> "
            f"{special_assignments[special_id]}"
        )

    print()
    
    ambiguous_specials = {
        special_id: prefix
        for special_id, prefix in special_assignments.items()
        if "/" in prefix or prefix == "NONE"
    }

    resolved_specials = {
        special_id: prefix
        for special_id, prefix in special_assignments.items()
        if "/" not in prefix and prefix != "NONE"
    }

    if ambiguous_specials:
        print(
            "Ambiguous special features will be excluded "
            "from postal-prefix geometry:"
        )

        for special_id in sorted(
            ambiguous_specials
        ):
            print(
                f"  {special_id}: "
                f"{ambiguous_specials[special_id]}"
            )

        print()

    all_prefixes = {
        **regency_prefixes,
        **resolved_specials,
    }

    expected_assigned_count = (
        EXPECTED_ADMINISTRATIVE_COUNT
        + len(resolved_specials)
    )

    if len(all_prefixes) != expected_assigned_count:
        raise ValueError(
            "Unexpected assigned feature count: "
            f"expected {expected_assigned_count:,}, "
            f"got {len(all_prefixes):,}."
        )

    (
        prefix_2,
        prefix_1,
    ) = dissolve_prefixes(
        regencies,
        all_prefixes,
    )

    PUBLIC_GEOJSON_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_geojson(
        prefix_2,
        PREFIX_2_GEOJSON,
        "prefix_2",
    )

    write_geojson(
        prefix_1,
        PREFIX_1_GEOJSON,
        "prefix_1",
    )

    print(
        "OUTPUT"
    )
    print(
        "-" * 72
    )
    print(
        f"2-digit prefix features:        {len(prefix_2):,}"
    )
    print(
        f"1-digit prefix features:        {len(prefix_1):,}"
    )
    print()

    print(
        PREFIX_2_GEOJSON.relative_to(
            PROJECT_ROOT
        )
    )
    print(
        PREFIX_1_GEOJSON.relative_to(
            PROJECT_ROOT
        )
    )
    print()

    print(
        "Generation complete."
    )


if __name__ == "__main__":
    main()