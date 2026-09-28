"""
Compare Brazil CEP city data, IBGE municipalities, and HelloQuiz postal regions.

This inspection script combines three sources:

1. brazil.db's 2012 CEP database, which provides known two-digit CEP prefixes
   for cities with street-level postal records.
2. GeoPedia's processed 2025 IBGE municipality GeoJSON, which provides current
   municipality geometry and official municipality IDs.
3. HelloQuiz's postal-code GeoJSON, which provides broad postal-region
   geometry that can constrain later inference.

The script does not generate final runtime postal-code geometry. Its purpose is
to determine whether the available free sources agree closely enough to make a
useful approximate two-digit CEP map.

Generated reports are written to:
data/intermediate/countries/brazil/postal/
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry.base import BaseGeometry


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SQL_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "brazil"
    / "brazil.db-master"
    / "cep2012"
    / "cep2012.sql"
)

MUNICIPALITIES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
    / "municipalities.geojson"
)

HELLOQUIZ_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "brazil"
    / "helloquiz"
)

REPORT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "brazil"
    / "postal"
)

SUMMARY_PATH = REPORT_DIRECTORY / "postal-source-comparison.json"
CITY_MATCHES_PATH = REPORT_DIRECTORY / "city-matches.csv"
HELLOQUIZ_ANCHORS_PATH = REPORT_DIRECTORY / "helloquiz-anchor-summary.csv"
MUNICIPALITY_COVERAGE_PATH = (
    REPORT_DIRECTORY / "municipality-helloquiz-coverage.csv"
)


# Equal-area projection used only for measuring polygon intersections.
AREA_CRS = "EPSG:5880"


STATE_ID_TO_ABBREVIATION = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


STATE_INSERT_RE = re.compile(
    r"^INSERT INTO `tend_estado` .* VALUES "
    r"\((\d+),'((?:\\'|[^'])*)','([A-Z]{2})'\);$"
)

CITY_INSERT_RE = re.compile(
    r"^INSERT INTO `tend_cidade` .* VALUES "
    r"\((\d+),(\d+),'((?:\\'|[^'])*)'\);$"
)

ADDRESS_INSERT_RE = re.compile(
    r"^INSERT INTO `tend_endereco` .* VALUES "
    r"\('([^']+)',(\d+),"
)

VALID_CEP_RE = re.compile(r"^\d{5}-\d{3}$")


def decode_mysql_string(value: str) -> str:
    """
    Decode the small subset of MySQL escaping used in names from the SQL dump.
    """

    return (
        value.replace(r"\'", "'")
        .replace(r"\\", "\\")
    )


def normalize_name(value: str) -> str:
    """
    Normalize a place name for deterministic old-to-current municipality matching.

    Accents, punctuation, apostrophes, and capitalization are ignored. Matching
    still occurs within a state so identical municipality names in different
    states cannot collide.
    """

    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    value = value.casefold()

    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


def find_helloquiz_path() -> Path:
    """
    Locate the HelloQuiz two-digit postal GeoJSON in its raw-data directory.
    """

    if not HELLOQUIZ_DIRECTORY.exists():
        raise FileNotFoundError(
            "HelloQuiz directory was not found:\n"
            f"{HELLOQUIZ_DIRECTORY}"
        )

    candidates = sorted(
        path
        for path in HELLOQUIZ_DIRECTORY.rglob("*.geojson")
        if "2-digit" in path.name.casefold()
        or "2_digit" in path.name.casefold()
        or "postal" in path.name.casefold()
    )

    if not candidates:
        candidates = sorted(
            HELLOQUIZ_DIRECTORY.rglob("*.geojson")
        )

    if not candidates:
        raise FileNotFoundError(
            "No GeoJSON files were found in the HelloQuiz directory:\n"
            f"{HELLOQUIZ_DIRECTORY}"
        )

    if len(candidates) > 1:
        candidate_list = "\n".join(
            f"  - {path.relative_to(PROJECT_ROOT)}"
            for path in candidates
        )

        raise ValueError(
            "Multiple possible HelloQuiz GeoJSON files were found. "
            "Keep only the intended Brazil postal file in the directory "
            "or make the filename clearly identify it:\n"
            f"{candidate_list}"
        )

    return candidates[0]


def normalize_helloquiz_label(value: object) -> str:
    """
    Normalize formatting differences in a HelloQuiz postal-region label.
    """

    label = str(value).strip()

    label = (
        label.replace("â€‘", "-")
        .replace("-", "-")
        .replace("–", "-")
        .replace("—", "-")
    )

    return label


def helloquiz_label_to_prefixes(label: str) -> set[str]:
    """
    Convert a HelloQuiz area label into the CEP-2 prefixes it can represent.

    Examples:
    "69"    -> {"69"}
    "30-34" -> {"30", "31", "32", "33", "34"}
    "27x"   -> {"27"}
    "279"   -> {"27"}
    "0x"    -> {"01", ..., "09"}

    These values are used only as broad constraints. They are not treated as
    final quiz answers or final postal geometry.
    """

    normalized = normalize_helloquiz_label(label).casefold()

    range_match = re.fullmatch(
        r"(\d{2})\s*-\s*(\d{2})",
        normalized,
    )

    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))

        if end < start:
            raise ValueError(
                f"Invalid HelloQuiz postal range: {label!r}"
            )

        return {
            f"{value:02d}"
            for value in range(start, end + 1)
        }

    exact_two_digit_match = re.fullmatch(
        r"\d{2}",
        normalized,
    )

    if exact_two_digit_match:
        return {normalized}

    three_digit_match = re.fullmatch(
        r"(\d{2})\d",
        normalized,
    )

    if three_digit_match:
        return {three_digit_match.group(1)}

    two_digit_x_match = re.fullmatch(
        r"(\d{2})x",
        normalized,
    )

    if two_digit_x_match:
        return {two_digit_x_match.group(1)}

    one_digit_x_match = re.fullmatch(
        r"(\d)x",
        normalized,
    )

    if one_digit_x_match:
        first_digit = int(one_digit_x_match.group(1))

        start = first_digit * 10
        end = start + 9

        prefixes = {
            f"{value:02d}"
            for value in range(start, end + 1)
        }

        # Brazil's source data contains no 00 CEP-2 region.
        prefixes.discard("00")

        return prefixes

    raise ValueError(
        "Unsupported HelloQuiz postal label format: "
        f"{label!r}"
    )


def load_brazil_db() -> tuple[
    dict[int, dict[str, str]],
    dict[int, dict[str, Any]],
]:
    """
    Parse states, cities, and known two-digit CEP prefixes from brazil.db.
    """

    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"CEP SQL dump was not found:\n{SQL_PATH}"
        )

    states: dict[int, dict[str, str]] = {}
    cities: dict[int, dict[str, Any]] = {}

    city_prefix_counts: dict[int, Counter[str]] = defaultdict(Counter)

    with SQL_PATH.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.rstrip("\r\n")

            if line.startswith("INSERT INTO `tend_estado`"):
                match = STATE_INSERT_RE.match(line)

                if not match:
                    raise ValueError(
                        "Could not parse tend_estado INSERT on "
                        f"line {line_number}."
                    )

                state_id = int(match.group(1))

                states[state_id] = {
                    "name": decode_mysql_string(match.group(2)),
                    "abbreviation": match.group(3),
                }

                continue

            if line.startswith("INSERT INTO `tend_cidade`"):
                match = CITY_INSERT_RE.match(line)

                if not match:
                    raise ValueError(
                        "Could not parse tend_cidade INSERT on "
                        f"line {line_number}."
                    )

                city_id = int(match.group(1))

                cities[city_id] = {
                    "name": decode_mysql_string(match.group(3)),
                    "state_id": int(match.group(2)),
                    "prefix_counts": Counter(),
                }

                continue

            if not line.startswith("INSERT INTO `tend_endereco`"):
                continue

            match = ADDRESS_INSERT_RE.match(line)

            if not match:
                raise ValueError(
                    "Could not parse tend_endereco INSERT on "
                    f"line {line_number}."
                )

            cep = match.group(1)
            city_id = int(match.group(2))

            if not VALID_CEP_RE.fullmatch(cep):
                continue

            city_prefix_counts[city_id][cep[:2]] += 1

    for city_id, prefix_counts in city_prefix_counts.items():
        city = cities.get(city_id)

        if city is None:
            raise ValueError(
                "CEP record references an unknown city ID: "
                f"{city_id}"
            )

        city["prefix_counts"] = prefix_counts

    return states, cities


def load_municipalities() -> gpd.GeoDataFrame:
    """
    Load GeoPedia's processed 2025 IBGE municipality geometry.
    """

    if not MUNICIPALITIES_PATH.exists():
        raise FileNotFoundError(
            "Processed Brazil municipality GeoJSON was not found:\n"
            f"{MUNICIPALITIES_PATH}"
        )

    municipalities = gpd.read_file(MUNICIPALITIES_PATH)

    required_columns = {
        "id",
        "name",
        "state_id",
        "geometry",
    }

    missing_columns = required_columns - set(municipalities.columns)

    if missing_columns:
        raise ValueError(
            "Municipality GeoJSON is missing required properties: "
            f"{sorted(missing_columns)}"
        )

    municipalities = municipalities[
        ["id", "name", "state_id", "geometry"]
    ].copy()

    municipalities["id"] = municipalities["id"].astype(str)
    municipalities["state_id"] = municipalities["state_id"].astype(str)
    municipalities["name"] = municipalities["name"].astype(str)

    municipalities["state"] = municipalities["state_id"].map(
        STATE_ID_TO_ABBREVIATION
    )

    if municipalities["state"].isna().any():
        unknown_state_ids = sorted(
            municipalities.loc[
                municipalities["state"].isna(),
                "state_id",
            ].unique()
        )

        raise ValueError(
            "Unknown IBGE state IDs in municipality GeoJSON: "
            f"{unknown_state_ids}"
        )

    municipalities["normalized_name"] = municipalities["name"].map(
        normalize_name
    )

    if municipalities.crs is None:
        municipalities = municipalities.set_crs(
            "EPSG:4326"
        )

    return municipalities


def load_helloquiz() -> tuple[Path, gpd.GeoDataFrame]:
    """
    Load and normalize the HelloQuiz postal-region GeoJSON.
    """

    path = find_helloquiz_path()

    helloquiz = gpd.read_file(path)

    if "AreaCode" not in helloquiz.columns:
        raise ValueError(
            "HelloQuiz GeoJSON does not contain the expected "
            "'AreaCode' property."
        )

    if helloquiz.crs is None:
        helloquiz = helloquiz.set_crs("EPSG:4326")

    helloquiz = helloquiz[
        ["AreaCode", "geometry"]
    ].copy()

    helloquiz["helloquiz_label"] = helloquiz["AreaCode"].map(
        normalize_helloquiz_label
    )

    helloquiz["allowed_prefixes"] = helloquiz[
        "helloquiz_label"
    ].map(
        lambda label: sorted(
            helloquiz_label_to_prefixes(label)
        )
    )

    return path, helloquiz


def build_ibge_lookup(
    municipalities: gpd.GeoDataFrame,
) -> dict[tuple[str, str], list[int]]:
    """
    Build a state-and-normalized-name lookup for IBGE municipalities.
    """

    lookup: dict[
        tuple[str, str],
        list[int],
    ] = defaultdict(list)

    for index, municipality in municipalities.iterrows():
        key = (
            municipality["state"],
            municipality["normalized_name"],
        )

        lookup[key].append(index)

    return lookup


def match_old_cities(
    states: dict[int, dict[str, str]],
    cities: dict[int, dict[str, Any]],
    municipalities: gpd.GeoDataFrame,
) -> tuple[
    list[dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    """
    Match brazil.db cities to 2025 IBGE municipalities by state and name.
    """

    lookup = build_ibge_lookup(municipalities)

    match_rows: list[dict[str, Any]] = []
    known_municipalities: dict[int, dict[str, Any]] = {}

    for city_id, city in sorted(cities.items()):
        state = states.get(city["state_id"])

        if state is None:
            raise ValueError(
                f"City {city_id} references unknown state "
                f"{city['state_id']}."
            )

        state_abbreviation = state["abbreviation"]
        normalized_city_name = normalize_name(city["name"])

        candidate_indexes = lookup.get(
            (
                state_abbreviation,
                normalized_city_name,
            ),
            [],
        )

        prefix_counts: Counter[str] = city["prefix_counts"]
        prefixes = sorted(prefix_counts)

        if len(candidate_indexes) == 1:
            match_status = "matched"

            municipality_index = candidate_indexes[0]
            municipality = municipalities.loc[
                municipality_index
            ]

            municipality_id = municipality["id"]
            municipality_name = municipality["name"]

            if prefixes:
                existing = known_municipalities.get(
                    municipality_index
                )

                if existing is not None:
                    raise ValueError(
                        "Multiple brazil.db city rows with CEP data "
                        "matched the same IBGE municipality:\n"
                        f"{state_abbreviation} "
                        f"{municipality_name}"
                    )

                known_municipalities[municipality_index] = {
                    "city_id": city_id,
                    "old_city_name": city["name"],
                    "municipality_id": municipality_id,
                    "municipality_name": municipality_name,
                    "state": state_abbreviation,
                    "prefixes": prefixes,
                    "prefix_counts": dict(
                        sorted(prefix_counts.items())
                    ),
                }

        elif len(candidate_indexes) == 0:
            match_status = "unmatched"
            municipality_id = ""
            municipality_name = ""

        else:
            match_status = "ambiguous"
            municipality_id = ""
            municipality_name = " | ".join(
                municipalities.loc[
                    candidate_indexes,
                    "name",
                ].tolist()
            )

        match_rows.append(
            {
                "city_id": city_id,
                "old_city_name": city["name"],
                "state": state_abbreviation,
                "has_cep_data": bool(prefixes),
                "prefixes": prefixes,
                "prefix_count": len(prefixes),
                "match_status": match_status,
                "ibge_municipality_id": municipality_id,
                "ibge_municipality_name": municipality_name,
            }
        )

    return match_rows, known_municipalities


def calculate_helloquiz_coverage(
    municipalities: gpd.GeoDataFrame,
    helloquiz: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:
    """
    Find the HelloQuiz region covering the largest area of each municipality.

    Area calculations are performed in an equal-area projected CRS.
    """

    municipalities_area = municipalities.to_crs(
        AREA_CRS
    ).copy()

    helloquiz_area = helloquiz.to_crs(
        AREA_CRS
    ).copy()

    spatial_index = helloquiz_area.sindex

    coverage_rows: list[dict[str, Any]] = []

    for municipality_index, municipality in municipalities_area.iterrows():
        geometry: BaseGeometry = municipality.geometry

        if geometry is None or geometry.is_empty:
            raise ValueError(
                "Municipality has empty geometry: "
                f"{municipality['id']} "
                f"{municipality['name']}"
            )

        municipality_area = geometry.area

        if municipality_area <= 0:
            raise ValueError(
                "Municipality has zero-area geometry: "
                f"{municipality['id']} "
                f"{municipality['name']}"
            )

        candidate_indexes = list(
            spatial_index.query(
                geometry,
                predicate="intersects",
            )
        )

        overlaps: list[
            tuple[int, float, float]
        ] = []

        for helloquiz_index in candidate_indexes:
            helloquiz_geometry = helloquiz_area.iloc[
                helloquiz_index
            ].geometry

            intersection = geometry.intersection(
                helloquiz_geometry
            )

            intersection_area = intersection.area

            if intersection_area <= 0:
                continue

            overlap_fraction = (
                intersection_area / municipality_area
            )

            overlaps.append(
                (
                    helloquiz_index,
                    intersection_area,
                    overlap_fraction,
                )
            )

        overlaps.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        original = municipalities.loc[
            municipality_index
        ]

        if not overlaps:
            coverage_rows.append(
                {
                    "municipality_index": municipality_index,
                    "municipality_id": original["id"],
                    "municipality_name": original["name"],
                    "state": original["state"],
                    "helloquiz_label": "",
                    "allowed_prefixes": [],
                    "primary_overlap_fraction": 0.0,
                    "total_overlap_fraction": 0.0,
                    "intersecting_region_count": 0,
                    "intersecting_labels": [],
                }
            )

            continue

        primary_index = overlaps[0][0]
        primary_region = helloquiz_area.iloc[
            primary_index
        ]

        total_overlap_fraction = sum(
            overlap[2]
            for overlap in overlaps
        )

        coverage_rows.append(
            {
                "municipality_index": municipality_index,
                "municipality_id": original["id"],
                "municipality_name": original["name"],
                "state": original["state"],
                "helloquiz_label": primary_region[
                    "helloquiz_label"
                ],
                "allowed_prefixes": list(
                    primary_region["allowed_prefixes"]
                ),
                "primary_overlap_fraction": overlaps[0][2],
                "total_overlap_fraction": total_overlap_fraction,
                "intersecting_region_count": len(overlaps),
                "intersecting_labels": [
                    helloquiz_area.iloc[index][
                        "helloquiz_label"
                    ]
                    for index, _, _ in overlaps
                ],
            }
        )

    return coverage_rows


def analyze_anchors(
    coverage_rows: list[dict[str, Any]],
    known_municipalities: dict[int, dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Compare known CEP-2 municipality anchors against HelloQuiz constraints.
    """

    coverage_by_index = {
        row["municipality_index"]: row
        for row in coverage_rows
    }

    anchor_rows: list[dict[str, Any]] = []

    region_stats: dict[
        str,
        dict[str, Any],
    ] = defaultdict(
        lambda: {
            "municipalities": 0,
            "known_anchors": 0,
            "single_prefix_anchors": 0,
            "multi_prefix_anchors": 0,
            "compatible_anchors": 0,
            "incompatible_anchors": 0,
            "observed_prefix_counts": Counter(),
            "allowed_prefixes": set(),
        }
    )

    for coverage in coverage_rows:
        label = coverage["helloquiz_label"]

        if not label:
            continue

        stats = region_stats[label]
        stats["municipalities"] += 1

        stats["allowed_prefixes"].update(
            coverage["allowed_prefixes"]
        )

    for municipality_index, known in sorted(
        known_municipalities.items()
    ):
        coverage = coverage_by_index.get(
            municipality_index
        )

        if coverage is None:
            raise ValueError(
                "Known CEP municipality is missing HelloQuiz "
                "coverage information."
            )

        known_prefixes = set(known["prefixes"])
        allowed_prefixes = set(
            coverage["allowed_prefixes"]
        )

        compatible = (
            bool(allowed_prefixes)
            and known_prefixes.issubset(
                allowed_prefixes
            )
        )

        anchor_rows.append(
            {
                **known,
                "helloquiz_label": coverage[
                    "helloquiz_label"
                ],
                "helloquiz_allowed_prefixes": sorted(
                    allowed_prefixes
                ),
                "primary_overlap_fraction": coverage[
                    "primary_overlap_fraction"
                ],
                "compatible": compatible,
            }
        )

        label = coverage["helloquiz_label"]

        if not label:
            continue

        stats = region_stats[label]
        stats["known_anchors"] += 1

        if len(known_prefixes) == 1:
            stats["single_prefix_anchors"] += 1
        else:
            stats["multi_prefix_anchors"] += 1

        if compatible:
            stats["compatible_anchors"] += 1
        else:
            stats["incompatible_anchors"] += 1

        for prefix in known_prefixes:
            stats["observed_prefix_counts"][prefix] += 1

    region_rows: list[dict[str, Any]] = []

    for label, stats in sorted(
        region_stats.items()
    ):
        region_rows.append(
            {
                "helloquiz_label": label,
                "allowed_prefixes": sorted(
                    stats["allowed_prefixes"]
                ),
                "municipalities": stats["municipalities"],
                "known_anchors": stats["known_anchors"],
                "single_prefix_anchors": stats[
                    "single_prefix_anchors"
                ],
                "multi_prefix_anchors": stats[
                    "multi_prefix_anchors"
                ],
                "compatible_anchors": stats[
                    "compatible_anchors"
                ],
                "incompatible_anchors": stats[
                    "incompatible_anchors"
                ],
                "observed_prefix_counts": dict(
                    sorted(
                        stats[
                            "observed_prefix_counts"
                        ].items()
                    )
                ),
            }
        )

    return anchor_rows, region_rows


def write_reports(
    helloquiz_path: Path,
    match_rows: list[dict[str, Any]],
    known_municipalities: dict[int, dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    anchor_rows: list[dict[str, Any]],
    region_rows: list[dict[str, Any]],
) -> None:
    """
    Write CSV and JSON inspection reports.
    """

    REPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CITY_MATCHES_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "city_id",
                "old_city_name",
                "state",
                "has_cep_data",
                "prefix_count",
                "prefixes",
                "match_status",
                "ibge_municipality_id",
                "ibge_municipality_name",
            ]
        )

        for row in match_rows:
            writer.writerow(
                [
                    row["city_id"],
                    row["old_city_name"],
                    row["state"],
                    row["has_cep_data"],
                    row["prefix_count"],
                    ", ".join(row["prefixes"]),
                    row["match_status"],
                    row["ibge_municipality_id"],
                    row["ibge_municipality_name"],
                ]
            )

    with MUNICIPALITY_COVERAGE_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "municipality_id",
                "municipality_name",
                "state",
                "helloquiz_label",
                "allowed_prefixes",
                "primary_overlap_percent",
                "total_overlap_percent",
                "intersecting_region_count",
                "intersecting_labels",
            ]
        )

        for row in coverage_rows:
            writer.writerow(
                [
                    row["municipality_id"],
                    row["municipality_name"],
                    row["state"],
                    row["helloquiz_label"],
                    ", ".join(
                        row["allowed_prefixes"]
                    ),
                    round(
                        row[
                            "primary_overlap_fraction"
                        ] * 100,
                        4,
                    ),
                    round(
                        row[
                            "total_overlap_fraction"
                        ] * 100,
                        4,
                    ),
                    row["intersecting_region_count"],
                    " | ".join(
                        row["intersecting_labels"]
                    ),
                ]
            )

    with HELLOQUIZ_ANCHORS_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "helloquiz_label",
                "allowed_prefixes",
                "municipalities",
                "known_anchors",
                "single_prefix_anchors",
                "multi_prefix_anchors",
                "compatible_anchors",
                "incompatible_anchors",
                "observed_prefix_counts",
            ]
        )

        for row in region_rows:
            writer.writerow(
                [
                    row["helloquiz_label"],
                    ", ".join(
                        row["allowed_prefixes"]
                    ),
                    row["municipalities"],
                    row["known_anchors"],
                    row["single_prefix_anchors"],
                    row["multi_prefix_anchors"],
                    row["compatible_anchors"],
                    row["incompatible_anchors"],
                    ", ".join(
                        f"{prefix}:{count}"
                        for prefix, count
                        in row[
                            "observed_prefix_counts"
                        ].items()
                    ),
                ]
            )

    matched_rows = [
        row
        for row in match_rows
        if row["match_status"] == "matched"
    ]

    unmatched_rows = [
        row
        for row in match_rows
        if row["match_status"] == "unmatched"
    ]

    ambiguous_rows = [
        row
        for row in match_rows
        if row["match_status"] == "ambiguous"
    ]

    cep_rows = [
        row
        for row in match_rows
        if row["has_cep_data"]
    ]

    matched_cep_rows = [
        row
        for row in cep_rows
        if row["match_status"] == "matched"
    ]

    compatible_anchor_count = sum(
        1
        for row in anchor_rows
        if row["compatible"]
    )

    incompatible_anchor_count = (
        len(anchor_rows)
        - compatible_anchor_count
    )

    strong_coverage_count = sum(
        1
        for row in coverage_rows
        if row["primary_overlap_fraction"] >= 0.95
    )

    weak_coverage_count = sum(
        1
        for row in coverage_rows
        if 0
        < row["primary_overlap_fraction"]
        < 0.95
    )

    uncovered_count = sum(
        1
        for row in coverage_rows
        if row["primary_overlap_fraction"] == 0
    )

    summary = {
        "sources": {
            "brazil_db": str(
                SQL_PATH.relative_to(
                    PROJECT_ROOT
                )
            ),
            "municipalities": str(
                MUNICIPALITIES_PATH.relative_to(
                    PROJECT_ROOT
                )
            ),
            "helloquiz": str(
                helloquiz_path.relative_to(
                    PROJECT_ROOT
                )
            ),
        },
        "city_matching": {
            "total_old_cities": len(match_rows),
            "matched": len(matched_rows),
            "unmatched": len(unmatched_rows),
            "ambiguous": len(ambiguous_rows),
            "cep_known_cities": len(cep_rows),
            "cep_known_matched": len(
                matched_cep_rows
            ),
            "cep_known_unmatched_or_ambiguous": (
                len(cep_rows)
                - len(matched_cep_rows)
            ),
        },
        "known_municipality_anchors": len(
            known_municipalities
        ),
        "helloquiz_coverage": {
            "municipalities_total": len(
                coverage_rows
            ),
            "primary_overlap_at_least_95_percent": (
                strong_coverage_count
            ),
            "primary_overlap_below_95_percent": (
                weak_coverage_count
            ),
            "no_positive_area_overlap": (
                uncovered_count
            ),
        },
        "anchor_compatibility": {
            "anchors_compared": len(
                anchor_rows
            ),
            "compatible": compatible_anchor_count,
            "incompatible": incompatible_anchor_count,
            "compatibility_percent": (
                round(
                    compatible_anchor_count
                    / len(anchor_rows)
                    * 100,
                    2,
                )
                if anchor_rows
                else 0.0
            ),
        },
        "helloquiz_regions": region_rows,
        "incompatible_anchors": [
            row
            for row in anchor_rows
            if not row["compatible"]
        ],
        "unmatched_cep_cities": [
            row
            for row in cep_rows
            if row["match_status"] != "matched"
        ],
    }

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write("\n")


def print_summary(
    match_rows: list[dict[str, Any]],
    anchor_rows: list[dict[str, Any]],
    region_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
) -> None:
    """
    Print the most important comparison results.
    """

    matched = sum(
        row["match_status"] == "matched"
        for row in match_rows
    )

    unmatched = sum(
        row["match_status"] == "unmatched"
        for row in match_rows
    )

    ambiguous = sum(
        row["match_status"] == "ambiguous"
        for row in match_rows
    )

    cep_known = [
        row
        for row in match_rows
        if row["has_cep_data"]
    ]

    cep_known_matched = sum(
        row["match_status"] == "matched"
        for row in cep_known
    )

    compatible = sum(
        row["compatible"]
        for row in anchor_rows
    )

    incompatible = len(anchor_rows) - compatible

    print()
    print("City matching")
    print("-------------")
    print(
        f"Old brazil.db cities:       "
        f"{len(match_rows):,}"
    )
    print(
        f"Matched to 2025 IBGE:       "
        f"{matched:,}"
    )
    print(
        f"Unmatched:                   "
        f"{unmatched:,}"
    )
    print(
        f"Ambiguous:                   "
        f"{ambiguous:,}"
    )
    print()
    print(
        f"Cities with CEP evidence:    "
        f"{len(cep_known):,}"
    )
    print(
        f"CEP cities matched to IBGE:  "
        f"{cep_known_matched:,}"
    )

    print()
    print("HelloQuiz municipality coverage")
    print("-------------------------------")

    strong = sum(
        row["primary_overlap_fraction"] >= 0.95
        for row in coverage_rows
    )

    weak = sum(
        0
        < row["primary_overlap_fraction"]
        < 0.95
        for row in coverage_rows
    )

    uncovered = sum(
        row["primary_overlap_fraction"] == 0
        for row in coverage_rows
    )

    print(
        f"Primary region >= 95%:       "
        f"{strong:,}"
    )
    print(
        f"Primary region < 95%:        "
        f"{weak:,}"
    )
    print(
        f"No positive-area overlap:    "
        f"{uncovered:,}"
    )

    print()
    print("Known CEP anchor compatibility")
    print("------------------------------")
    print(
        f"Anchors compared:            "
        f"{len(anchor_rows):,}"
    )
    print(
        f"Compatible with HelloQuiz:   "
        f"{compatible:,}"
    )
    print(
        f"Incompatible:                "
        f"{incompatible:,}"
    )

    if anchor_rows:
        print(
            f"Compatibility:               "
            f"{compatible / len(anchor_rows) * 100:.2f}%"
        )

    print()
    print("HelloQuiz region anchors")
    print("------------------------")

    for row in region_rows:
        observed = ", ".join(
            f"{prefix}:{count}"
            for prefix, count
            in row[
                "observed_prefix_counts"
            ].items()
        )

        allowed = ", ".join(
            row["allowed_prefixes"]
        )

        print(
            f"{row['helloquiz_label']:<8} "
            f"allowed=[{allowed}]  "
            f"municipalities={row['municipalities']:<4} "
            f"anchors={row['known_anchors']:<3} "
            f"bad={row['incompatible_anchors']:<2} "
            f"observed=[{observed}]"
        )

    incompatible_rows = [
        row
        for row in anchor_rows
        if not row["compatible"]
    ]

    if incompatible_rows:
        print()
        print("Incompatible known anchors")
        print("--------------------------")

        for row in incompatible_rows:
            print(
                f"{row['state']}  "
                f"{row['municipality_name']}  "
                f"known={','.join(row['prefixes'])}  "
                f"HelloQuiz={row['helloquiz_label']}  "
                f"allows={','.join(row['helloquiz_allowed_prefixes'])}  "
                f"overlap={row['primary_overlap_fraction'] * 100:.2f}%"
            )

    print()
    print("Reports")
    print("-------")
    print(
        "JSON: "
        f"{SUMMARY_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "CSV:  "
        f"{CITY_MATCHES_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "CSV:  "
        f"{HELLOQUIZ_ANCHORS_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "CSV:  "
        f"{MUNICIPALITY_COVERAGE_PATH.relative_to(PROJECT_ROOT)}"
    )


def main() -> None:
    """
    Run the postal-source comparison.
    """

    print("Loading brazil.db CEP information...")
    states, cities = load_brazil_db()

    print("Loading processed IBGE municipalities...")
    municipalities = load_municipalities()

    print("Locating and loading HelloQuiz postal geometry...")
    helloquiz_path, helloquiz = load_helloquiz()

    print(
        "HelloQuiz source: "
        f"{helloquiz_path.relative_to(PROJECT_ROOT)}"
    )

    print("Matching brazil.db cities to IBGE municipalities...")
    match_rows, known_municipalities = match_old_cities(
        states,
        cities,
        municipalities,
    )

    print(
        "Calculating HelloQuiz coverage for "
        f"{len(municipalities):,} municipalities..."
    )

    coverage_rows = calculate_helloquiz_coverage(
        municipalities,
        helloquiz,
    )

    print("Comparing known CEP anchors to HelloQuiz...")

    anchor_rows, region_rows = analyze_anchors(
        coverage_rows,
        known_municipalities,
    )

    print("Writing reports...")

    write_reports(
        helloquiz_path,
        match_rows,
        known_municipalities,
        coverage_rows,
        anchor_rows,
        region_rows,
    )

    print_summary(
        match_rows,
        anchor_rows,
        region_rows,
        coverage_rows,
    )


if __name__ == "__main__":
    main()