"""
Inspect Indonesia 2-digit postal-code prefixes and validate the complete
GeoPedia-to-postcode kabupaten/kota crosswalk.

Purpose
-------
This script uses the raw Indonesia postcode hierarchy to determine the
dominant 2-digit postal-code prefix for every kabupaten/kota, then matches
those units to GeoPedia's canonical regency/city polygons.

The two datasets use different administrative snapshots, so their Admin 2 IDs
cannot be matched directly. Matching instead uses:

    - province
    - normalized kabupaten/kota name
    - administrative type (Kabupaten or Kota)

A small explicit alias table handles known spelling/name differences between
the datasets.

GeoPedia's boundary source also contains eight non-administrative Admin 2
features representing lakes, forest, and reservoirs. These are explicitly
excluded from the administrative crosswalk.

The expected final result is:

    GeoJSON Admin 2 features:          522
    Administrative units:             514
    Special non-administrative units:   8
    Postcode kabupaten/kota:           514
    Matched administrative units:      514

No output files are written. This script validates the crosswalk that will
later be used to generate GeoPedia's Indonesia postal-prefix GeoJSON.

Inputs
------
Raw postcode hierarchy:

    data/raw/countries/indonesia/post-code-data/prov.csv
    data/raw/countries/indonesia/post-code-data/kabkota.csv
    data/raw/countries/indonesia/post-code-data/desakel.csv

Canonical GeoPedia boundaries:

    data/intermediate/countries/indonesia/provinces.geojson
    data/intermediate/countries/indonesia/regencies.geojson

Requirements
------------
    pip install ijson

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/inspect/post-code-prefixes.py
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import ijson


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

INTERMEDIATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "indonesia"
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

PROVINCES_GEOJSON = (
    INTERMEDIATE_DIR
    / "provinces.geojson"
)

REGENCIES_GEOJSON = (
    INTERMEDIATE_DIR
    / "regencies.geojson"
)


# ---------------------------------------------------------------------------
# Expected counts
# ---------------------------------------------------------------------------

EXPECTED_CSV_PROVINCE_COUNT = 34
EXPECTED_KABKOTA_COUNT = 514
EXPECTED_VILLAGE_COUNT = 83_436

EXPECTED_GEOJSON_PROVINCE_COUNT = 34
EXPECTED_GEOJSON_REGENCY_COUNT = 522

EXPECTED_ADMINISTRATIVE_REGENCY_COUNT = 514
EXPECTED_SPECIAL_FEATURE_COUNT = 8


# ---------------------------------------------------------------------------
# Known cross-dataset differences
# ---------------------------------------------------------------------------

# These GeoJSON Admin 2 features are not kabupaten/kota. They exist in the
# boundary source but have no corresponding record in kabkota.csv.

SPECIAL_GEOJSON_FEATURE_IDS = {
    "ID1388",  # Danau
    "ID1688",  # Danau
    "ID1888",  # Danau
    "ID7188",  # Danau
    "ID1288",  # Danau Toba
    "ID3399",  # Hutan
    "ID3288",  # Waduk Cirata
    "ID3388",  # Wadung Kedungombo
}


# Explicit aliases for genuine administrative units whose names differ
# between GeoPedia's boundary source and the postcode dataset.
#
# Key:
#     GeoPedia regency_id
#
# Value:
#     normalized postcode kabkota ID

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
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PostcodeKab:
    """One kabupaten/kota from the postcode dataset."""

    admin_id: str
    name: str
    admin_type: str
    province_id: str
    province_name: str
    dominant_prefix: str
    dominant_count: int
    village_count: int
    prefix_counts: Counter[str]

    @property
    def dominant_percentage(
        self,
    ) -> float:
        """Return the dominant prefix's share of villages."""

        return (
            self.dominant_count
            / self.village_count
            * 100
        )


@dataclass(frozen=True)
class GeoJSONRegency:
    """One canonical GeoPedia Admin 2 feature."""

    regency_id: str
    regency: str
    province_id: str
    province: str


@dataclass(frozen=True)
class CrosswalkMatch:
    """One validated GeoJSON-to-postcode match."""

    geojson: GeoJSONRegency
    postcode: PostcodeKab
    method: str


# ---------------------------------------------------------------------------
# Text / ID normalization
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
    Normalize kabkota.csv IDs to the form used by descendant IDs.

    Some kabkota.csv IDs have lost a trailing zero.

    Examples:
        11.01 -> 11.01
        11.1  -> 11.10
        12.2  -> 12.20
        14.72 -> 14.72
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
    """Normalize province names across the two datasets."""

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
    """Normalize an Admin 2 name without its administrative prefix."""

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


def get_geojson_admin_type(
    regency_name: str,
) -> str:
    """
    Infer Kabupaten/Kota from GeoPedia's canonical name.

    The source explicitly prefixes cities with "Kota". Ordinary Admin 2
    names without that prefix are treated as Kabupaten.
    """

    if regency_name.lower().startswith(
        "kota "
    ):
        return "kota"

    return "kabupaten"


def normalize_admin_type(
    value: str,
) -> str:
    """Normalize the postcode dataset's administrative type."""

    return normalize_text(
        value
    )


# ---------------------------------------------------------------------------
# Postcode hierarchy loading
# ---------------------------------------------------------------------------

def load_csv_provinces() -> dict[str, str]:
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

    if len(provinces) != EXPECTED_CSV_PROVINCE_COUNT:
        raise ValueError(
            "Unexpected postcode province count: "
            f"expected {EXPECTED_CSV_PROVINCE_COUNT:,}, "
            f"got {len(provinces):,}."
        )

    return provinces


def load_kabkota() -> dict[str, tuple[str, str]]:
    """Load normalized postcode Admin 2 IDs, names, and types."""

    records: dict[str, tuple[str, str]] = {}

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

            name = row[
                "nm"
            ].strip()

            admin_type = row[
                "type"
            ].strip()

            if admin_id in records:
                raise ValueError(
                    f"Duplicate normalized kabupaten/kota ID: "
                    f"{admin_id}"
                )

            records[
                admin_id
            ] = (
                name,
                admin_type,
            )

    if len(records) != EXPECTED_KABKOTA_COUNT:
        raise ValueError(
            "Unexpected kabupaten/kota count: "
            f"expected {EXPECTED_KABKOTA_COUNT:,}, "
            f"got {len(records):,}."
        )

    return records


def get_admin_2_id(
    village_id: str,
) -> str:
    """Extract the Admin 2 parent from a village ID."""

    parts = village_id.split(
        "."
    )

    if len(parts) != 4:
        raise ValueError(
            f"Unexpected village ID format: {village_id!r}"
        )

    return ".".join(
        parts[
            :2
        ]
    )


def load_prefix_counts() -> tuple[
    dict[str, Counter[str]],
    int,
]:
    """Count 2-digit postal prefixes for every postcode Admin 2 unit."""

    prefix_counts: dict[str, Counter[str]] = defaultdict(
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

            admin_2_id = get_admin_2_id(
                village_id
            )

            prefix_counts[
                admin_2_id
            ][
                postcode[:2]
            ] += 1

    if row_count != EXPECTED_VILLAGE_COUNT:
        raise ValueError(
            "Unexpected village count: "
            f"expected {EXPECTED_VILLAGE_COUNT:,}, "
            f"got {row_count:,}."
        )

    return (
        prefix_counts,
        row_count,
    )


def build_postcode_kabs(
    provinces: dict[str, str],
    kabkota: dict[str, tuple[str, str]],
    prefix_counts: dict[str, Counter[str]],
) -> dict[str, PostcodeKab]:
    """Combine postcode Admin 2 records with their prefix distributions."""

    missing = (
        set(kabkota)
        - set(prefix_counts)
    )

    unknown = (
        set(prefix_counts)
        - set(kabkota)
    )

    if missing:
        raise ValueError(
            "kabkota.csv units have no village postcode data: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    if unknown:
        raise ValueError(
            "Village data contains unknown Admin 2 IDs: "
            + ", ".join(
                sorted(
                    unknown
                )
            )
        )

    records: dict[str, PostcodeKab] = {}

    for admin_id, (
        name,
        admin_type,
    ) in kabkota.items():
        province_id = admin_id.split(
            ".",
            maxsplit=1,
        )[0]

        if province_id not in provinces:
            raise ValueError(
                f"Unknown postcode province {province_id!r} "
                f"for {admin_id!r}."
            )

        counts = prefix_counts[
            admin_id
        ]

        village_count = sum(
            counts.values()
        )

        dominant_prefix, dominant_count = counts.most_common(
            1
        )[0]

        records[
            admin_id
        ] = PostcodeKab(
            admin_id=admin_id,
            name=name,
            admin_type=admin_type,
            province_id=province_id,
            province_name=provinces[
                province_id
            ],
            dominant_prefix=dominant_prefix,
            dominant_count=dominant_count,
            village_count=village_count,
            prefix_counts=counts,
        )

    return records


# ---------------------------------------------------------------------------
# GeoJSON loading
# ---------------------------------------------------------------------------

def load_geojson_provinces() -> dict[str, str]:
    """Load canonical GeoPedia provinces."""

    provinces: dict[str, str] = {}

    with PROVINCES_GEOJSON.open(
        "rb"
    ) as file:
        for feature in ijson.items(
            file,
            "features.item",
        ):
            properties = feature[
                "properties"
            ]

            province_id = str(
                properties[
                    "province_id"
                ]
            ).strip()

            province = str(
                properties[
                    "province"
                ]
            ).strip()

            if province_id in provinces:
                raise ValueError(
                    f"Duplicate GeoJSON province ID: {province_id}"
                )

            provinces[
                province_id
            ] = province

    if len(provinces) != EXPECTED_GEOJSON_PROVINCE_COUNT:
        raise ValueError(
            "Unexpected GeoJSON province count: "
            f"expected {EXPECTED_GEOJSON_PROVINCE_COUNT:,}, "
            f"got {len(provinces):,}."
        )

    return provinces


def load_geojson_regencies() -> dict[str, GeoJSONRegency]:
    """Load canonical GeoPedia Admin 2 features."""

    records: dict[str, GeoJSONRegency] = {}

    with REGENCIES_GEOJSON.open(
        "rb"
    ) as file:
        for feature in ijson.items(
            file,
            "features.item",
        ):
            properties = feature[
                "properties"
            ]

            regency_id = str(
                properties[
                    "regency_id"
                ]
            ).strip()

            regency = str(
                properties[
                    "regency"
                ]
            ).strip()

            province_id = str(
                properties[
                    "province_id"
                ]
            ).strip()

            province = str(
                properties[
                    "province"
                ]
            ).strip()

            if regency_id in records:
                raise ValueError(
                    f"Duplicate GeoJSON regency ID: {regency_id}"
                )

            records[
                regency_id
            ] = GeoJSONRegency(
                regency_id=regency_id,
                regency=regency,
                province_id=province_id,
                province=province,
            )

    if len(records) != EXPECTED_GEOJSON_REGENCY_COUNT:
        raise ValueError(
            "Unexpected GeoJSON regency count: "
            f"expected {EXPECTED_GEOJSON_REGENCY_COUNT:,}, "
            f"got {len(records):,}."
        )

    return records


# ---------------------------------------------------------------------------
# Province crosswalk
# ---------------------------------------------------------------------------

def build_province_crosswalk(
    csv_provinces: dict[str, str],
    geojson_provinces: dict[str, str],
) -> dict[str, str]:
    """Match GeoPedia provinces to postcode provinces by normalized name."""

    csv_by_name: dict[str, list[str]] = defaultdict(
        list
    )

    for csv_id, name in csv_provinces.items():
        csv_by_name[
            normalize_province_name(
                name
            )
        ].append(
            csv_id
        )

    crosswalk: dict[str, str] = {}

    for geojson_id, name in geojson_provinces.items():
        candidates = csv_by_name.get(
            normalize_province_name(
                name
            ),
            [],
        )

        if len(candidates) != 1:
            raise ValueError(
                f"Could not uniquely match GeoJSON province "
                f"{geojson_id} ({name!r}). "
                f"Candidates: {candidates}"
            )

        crosswalk[
            geojson_id
        ] = candidates[
            0
        ]

    if len(crosswalk) != EXPECTED_GEOJSON_PROVINCE_COUNT:
        raise ValueError(
            "Province crosswalk is incomplete."
        )

    return crosswalk


# ---------------------------------------------------------------------------
# Admin 2 crosswalk
# ---------------------------------------------------------------------------

def build_postcode_index(
    postcode_kabs: dict[str, PostcodeKab],
) -> dict[
    tuple[str, str, str],
    list[PostcodeKab],
]:
    """
    Index postcode Admin 2 units by:

        province + normalized name + administrative type
    """

    index: dict[
        tuple[str, str, str],
        list[PostcodeKab],
    ] = defaultdict(
        list
    )

    for record in postcode_kabs.values():
        key = (
            record.province_id,
            normalize_regency_name(
                record.name
            ),
            normalize_admin_type(
                record.admin_type
            ),
        )

        index[
            key
        ].append(
            record
        )

    return index


def build_regency_crosswalk(
    geojson_regencies: dict[str, GeoJSONRegency],
    postcode_kabs: dict[str, PostcodeKab],
    province_crosswalk: dict[str, str],
) -> tuple[
    list[CrosswalkMatch],
    list[GeoJSONRegency],
]:
    """Build and validate the complete administrative Admin 2 crosswalk."""

    postcode_index = build_postcode_index(
        postcode_kabs
    )

    matches: list[CrosswalkMatch] = []
    special_features: list[GeoJSONRegency] = []

    used_postcode_ids: set[str] = set()

    for geojson in geojson_regencies.values():
        if geojson.regency_id in SPECIAL_GEOJSON_FEATURE_IDS:
            special_features.append(
                geojson
            )
            continue

        alias_id = REGENCY_POSTCODE_ALIASES.get(
            geojson.regency_id
        )

        if alias_id is not None:
            postcode = postcode_kabs.get(
                alias_id
            )

            if postcode is None:
                raise ValueError(
                    f"Alias for {geojson.regency_id} points to "
                    f"unknown postcode Admin 2 ID {alias_id!r}."
                )

            match_method = "alias"

        else:
            csv_province_id = province_crosswalk[
                geojson.province_id
            ]

            key = (
                csv_province_id,
                normalize_regency_name(
                    geojson.regency
                ),
                get_geojson_admin_type(
                    geojson.regency
                ),
            )

            candidates = postcode_index.get(
                key,
                [],
            )

            if len(candidates) == 0:
                raise ValueError(
                    "No postcode match for GeoJSON Admin 2: "
                    f"{geojson.regency_id} | "
                    f"{geojson.province} | "
                    f"{geojson.regency}"
                )

            if len(candidates) > 1:
                raise ValueError(
                    "Ambiguous postcode match for GeoJSON Admin 2: "
                    f"{geojson.regency_id} | "
                    f"{geojson.province} | "
                    f"{geojson.regency}. "
                    f"Candidates: "
                    + ", ".join(
                        candidate.admin_id
                        for candidate in candidates
                    )
                )

            postcode = candidates[
                0
            ]

            match_method = "automatic"

        if postcode.admin_id in used_postcode_ids:
            raise ValueError(
                f"Postcode Admin 2 {postcode.admin_id} "
                f"was matched more than once."
            )

        used_postcode_ids.add(
            postcode.admin_id
        )

        matches.append(
            CrosswalkMatch(
                geojson=geojson,
                postcode=postcode,
                method=match_method,
            )
        )

    unused_postcode_ids = (
        set(postcode_kabs)
        - used_postcode_ids
    )

    if unused_postcode_ids:
        details = ", ".join(
            f"{admin_id} ({postcode_kabs[admin_id].name})"
            for admin_id in sorted(
                unused_postcode_ids
            )
        )

        raise ValueError(
            "Postcode kabupaten/kota remain unused: "
            + details
        )

    return (
        matches,
        special_features,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_crosswalk(
    matches: list[CrosswalkMatch],
    special_features: list[GeoJSONRegency],
    postcode_kabs: dict[str, PostcodeKab],
) -> None:
    """Validate expected one-to-one administrative coverage."""

    if len(matches) != EXPECTED_ADMINISTRATIVE_REGENCY_COUNT:
        raise ValueError(
            "Unexpected administrative match count: "
            f"expected {EXPECTED_ADMINISTRATIVE_REGENCY_COUNT:,}, "
            f"got {len(matches):,}."
        )

    if len(special_features) != EXPECTED_SPECIAL_FEATURE_COUNT:
        raise ValueError(
            "Unexpected special-feature count: "
            f"expected {EXPECTED_SPECIAL_FEATURE_COUNT:,}, "
            f"got {len(special_features):,}."
        )

    if len(postcode_kabs) != len(matches):
        raise ValueError(
            "Postcode/Admin 2 crosswalk is not one-to-one: "
            f"{len(postcode_kabs):,} postcode units vs "
            f"{len(matches):,} matched GeoJSON units."
        )

    matched_geojson_ids = {
        match.geojson.regency_id
        for match in matches
    }

    matched_postcode_ids = {
        match.postcode.admin_id
        for match in matches
    }

    if len(matched_geojson_ids) != len(matches):
        raise ValueError(
            "Duplicate GeoJSON IDs found in crosswalk."
        )

    if len(matched_postcode_ids) != len(matches):
        raise ValueError(
            "Duplicate postcode IDs found in crosswalk."
        )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_prefix_summary(
    postcode_kabs: dict[str, PostcodeKab],
    village_count: int,
) -> None:
    """Print postcode-prefix statistics."""

    single_prefix = sum(
        len(record.prefix_counts) == 1
        for record in postcode_kabs.values()
    )

    dominant_100 = sum(
        record.dominant_percentage == 100
        for record in postcode_kabs.values()
    )

    dominant_95 = sum(
        record.dominant_percentage >= 95
        for record in postcode_kabs.values()
    )

    dominant_90 = sum(
        record.dominant_percentage >= 90
        for record in postcode_kabs.values()
    )

    dominant_75 = sum(
        record.dominant_percentage >= 75
        for record in postcode_kabs.values()
    )

    all_prefixes = {
        prefix
        for record in postcode_kabs.values()
        for prefix in record.prefix_counts
    }

    print(
        "=" * 88
    )
    print(
        "POSTCODE PREFIX SUMMARY"
    )
    print(
        "=" * 88
    )

    print(
        f"Kabupaten/kota:                 {len(postcode_kabs):,}"
    )
    print(
        f"Village records:                {village_count:,}"
    )
    print(
        f"Unique 2-digit prefixes:        {len(all_prefixes):,}"
    )
    print(
        f"Single-prefix units:            {single_prefix:,}"
    )
    print(
        f"Mixed-prefix units:             "
        f"{len(postcode_kabs) - single_prefix:,}"
    )
    print()

    print(
        f"Dominant prefix = 100%:         "
        f"{dominant_100:,} / {len(postcode_kabs):,}"
    )
    print(
        f"Dominant prefix >= 95%:         "
        f"{dominant_95:,} / {len(postcode_kabs):,}"
    )
    print(
        f"Dominant prefix >= 90%:         "
        f"{dominant_90:,} / {len(postcode_kabs):,}"
    )
    print(
        f"Dominant prefix >= 75%:         "
        f"{dominant_75:,} / {len(postcode_kabs):,}"
    )
    print()


def print_mixed_prefix_units(
    postcode_kabs: dict[str, PostcodeKab],
) -> None:
    """Print the small number of Admin 2 units containing multiple prefixes."""

    mixed = [
        record
        for record in postcode_kabs.values()
        if len(record.prefix_counts) > 1
    ]

    mixed.sort(
        key=lambda record: (
            record.dominant_percentage,
            record.admin_id,
        )
    )

    print(
        "=" * 88
    )
    print(
        "MIXED-PREFIX KABUPATEN/KOTA"
    )
    print(
        "=" * 88
    )

    for record in mixed:
        distribution = " | ".join(
            f"{prefix}: {count} "
            f"({count / record.village_count * 100:.1f}%)"
            for prefix, count in record.prefix_counts.most_common()
        )

        print(
            f"{record.admin_id:<8} "
            f"{record.admin_type:<10} "
            f"{record.name:<32} "
            f"| {distribution}"
        )

    print()


def print_crosswalk_summary(
    matches: list[CrosswalkMatch],
    special_features: list[GeoJSONRegency],
) -> None:
    """Print final crosswalk validation results."""

    automatic_count = sum(
        match.method == "automatic"
        for match in matches
    )

    alias_count = sum(
        match.method == "alias"
        for match in matches
    )

    print(
        "=" * 88
    )
    print(
        "FINAL GEOJSON → POSTCODE CROSSWALK"
    )
    print(
        "=" * 88
    )

    print(
        f"GeoJSON Admin 2 features:       "
        f"{EXPECTED_GEOJSON_REGENCY_COUNT:,}"
    )
    print(
        f"Administrative units:           {len(matches):,}"
    )
    print(
        f"Special non-admin features:     {len(special_features):,}"
    )
    print()

    print(
        f"Automatic matches:              {automatic_count:,}"
    )
    print(
        f"Explicit name aliases:          {alias_count:,}"
    )
    print(
        f"Matched administrative units:   "
        f"{len(matches):,} / "
        f"{EXPECTED_ADMINISTRATIVE_REGENCY_COUNT:,}"
    )
    print()

    print(
        "SPECIAL NON-ADMINISTRATIVE FEATURES"
    )
    print(
        "-" * 88
    )

    for feature in sorted(
        special_features,
        key=lambda item: item.regency_id,
    ):
        print(
            f"{feature.regency_id:<10} "
            f"{feature.province:<28} "
            f"{feature.regency}"
        )

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Validate Indonesia postcode prefixes and the Admin 2 crosswalk."""

    print(
        "Inspecting Indonesia postcode prefixes and Admin 2 crosswalk..."
    )
    print()

    csv_provinces = load_csv_provinces()

    kabkota = load_kabkota()

    (
        prefix_counts,
        village_count,
    ) = load_prefix_counts()

    postcode_kabs = build_postcode_kabs(
        csv_provinces,
        kabkota,
        prefix_counts,
    )

    geojson_provinces = load_geojson_provinces()

    geojson_regencies = load_geojson_regencies()

    province_crosswalk = build_province_crosswalk(
        csv_provinces,
        geojson_provinces,
    )

    (
        matches,
        special_features,
    ) = build_regency_crosswalk(
        geojson_regencies,
        postcode_kabs,
        province_crosswalk,
    )

    validate_crosswalk(
        matches,
        special_features,
        postcode_kabs,
    )

    print_prefix_summary(
        postcode_kabs,
        village_count,
    )

    print_mixed_prefix_units(
        postcode_kabs
    )

    print_crosswalk_summary(
        matches,
        special_features,
    )

    print(
        "=" * 88
    )
    print(
        "VALIDATION SUCCESSFUL"
    )
    print(
        "=" * 88
    )
    print(
        "All 514 postcode kabupaten/kota were matched one-to-one "
        "with GeoPedia administrative polygons."
    )
    print(
        "The remaining 8 GeoJSON Admin 2 features are explicitly "
        "classified as non-administrative."
    )


if __name__ == "__main__":
    main()