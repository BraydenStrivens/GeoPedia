"""
Evaluate geographic inference for Brazil's grouped two-digit CEP regions.

This script performs leave-one-out validation on known single-prefix
municipality anchors from brazil.db.

For each known anchor inside a grouped HelloQuiz region:

1. Temporarily hide the municipality's known CEP-2 prefix.
2. Infer the prefix from the remaining known anchors in the same broad
   HelloQuiz region.
3. Prefer prefixes found on adjacent municipalities.
4. Fall back to the nearest known municipality centroid.
5. Compare the inferred prefix against the hidden known prefix.

The script does not generate final runtime postal geometry.
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

SUMMARY_PATH = REPORT_DIRECTORY / "postal-inference-validation.json"
DETAILS_PATH = REPORT_DIRECTORY / "postal-inference-validation.csv"


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
    Decode the small subset of MySQL escaping used by the source dump.
    """

    return (
        value.replace(r"\'", "'")
        .replace(r"\\", "\\")
    )


def normalize_name(value: str) -> str:
    """
    Normalize municipality names for deterministic state-scoped matching.
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
    Locate the raw HelloQuiz Brazil postal GeoJSON.
    """

    if not HELLOQUIZ_DIRECTORY.exists():
        raise FileNotFoundError(
            f"HelloQuiz directory was not found:\n{HELLOQUIZ_DIRECTORY}"
        )

    candidates = sorted(
        HELLOQUIZ_DIRECTORY.rglob("*.geojson")
    )

    if not candidates:
        raise FileNotFoundError(
            "No GeoJSON file was found under:\n"
            f"{HELLOQUIZ_DIRECTORY}"
        )

    preferred = [
        path
        for path in candidates
        if "2-digit" in path.name.casefold()
        or "2_digit" in path.name.casefold()
        or "postal" in path.name.casefold()
    ]

    if len(preferred) == 1:
        return preferred[0]

    if len(candidates) == 1:
        return candidates[0]

    candidate_list = "\n".join(
        f"  - {path.relative_to(PROJECT_ROOT)}"
        for path in candidates
    )

    raise ValueError(
        "Multiple HelloQuiz GeoJSON files were found and the intended "
        f"postal source is ambiguous:\n{candidate_list}"
    )


def normalize_helloquiz_label(value: object) -> str:
    """
    Normalize HelloQuiz label punctuation.
    """

    return (
        str(value)
        .strip()
        .replace("â€‘", "-")
        .replace("–", "-")
        .replace("—", "-")
    )


def helloquiz_label_to_prefixes(label: str) -> set[str]:
    """
    Convert a HelloQuiz area label to the CEP-2 prefixes it may contain.
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
                f"Invalid HelloQuiz range: {label!r}"
            )

        return {
            f"{value:02d}"
            for value in range(start, end + 1)
        }

    if re.fullmatch(r"\d{2}", normalized):
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

        prefixes = {
            f"{value:02d}"
            for value in range(
                first_digit * 10,
                first_digit * 10 + 10,
            )
        }

        prefixes.discard("00")

        return prefixes

    raise ValueError(
        f"Unsupported HelloQuiz label: {label!r}"
    )


def load_brazil_db() -> tuple[
    dict[int, dict[str, str]],
    dict[int, dict[str, Any]],
]:
    """
    Parse brazil.db cities and CEP-2 prefix membership.
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
                f"CEP record references unknown city ID {city_id}."
            )

        city["prefix_counts"] = prefix_counts

    return states, cities


def load_municipalities() -> gpd.GeoDataFrame:
    """
    Load GeoPedia's processed IBGE municipality GeoJSON.
    """

    if not MUNICIPALITIES_PATH.exists():
        raise FileNotFoundError(
            f"Municipality GeoJSON was not found:\n{MUNICIPALITIES_PATH}"
        )

    municipalities = gpd.read_file(MUNICIPALITIES_PATH)

    required_columns = {
        "id",
        "name",
        "state_id",
        "geometry",
    }

    missing = required_columns - set(municipalities.columns)

    if missing:
        raise ValueError(
            "Municipality GeoJSON is missing required columns: "
            f"{sorted(missing)}"
        )

    municipalities = municipalities[
        ["id", "name", "state_id", "geometry"]
    ].copy()

    municipalities["id"] = municipalities["id"].astype(str)
    municipalities["name"] = municipalities["name"].astype(str)
    municipalities["state_id"] = municipalities["state_id"].astype(str)

    municipalities["state"] = municipalities["state_id"].map(
        STATE_ID_TO_ABBREVIATION
    )

    if municipalities["state"].isna().any():
        raise ValueError(
            "At least one municipality contains an unknown state_id."
        )

    municipalities["normalized_name"] = municipalities["name"].map(
        normalize_name
    )

    if municipalities.crs is None:
        municipalities = municipalities.set_crs("EPSG:4326")

    return municipalities


def load_helloquiz() -> tuple[Path, gpd.GeoDataFrame]:
    """
    Load the raw HelloQuiz postal-region GeoJSON.
    """

    path = find_helloquiz_path()

    helloquiz = gpd.read_file(path)

    if "AreaCode" not in helloquiz.columns:
        raise ValueError(
            "HelloQuiz GeoJSON does not contain an AreaCode property."
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
        lambda value: sorted(
            helloquiz_label_to_prefixes(value)
        )
    )

    return path, helloquiz


def match_known_anchors(
    states: dict[int, dict[str, str]],
    cities: dict[int, dict[str, Any]],
    municipalities: gpd.GeoDataFrame,
) -> dict[int, dict[str, Any]]:
    """
    Match single-prefix brazil.db cities to current IBGE municipalities.

    Only single-prefix municipalities are used for holdout validation because
    they provide an unambiguous ground-truth CEP-2 answer.
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

    anchors: dict[int, dict[str, Any]] = {}

    for city_id, city in cities.items():
        prefix_counts: Counter[str] = city["prefix_counts"]

        if len(prefix_counts) != 1:
            continue

        state = states.get(city["state_id"])

        if state is None:
            continue

        key = (
            state["abbreviation"],
            normalize_name(city["name"]),
        )

        candidate_indexes = lookup.get(key, [])

        if len(candidate_indexes) != 1:
            continue

        municipality_index = candidate_indexes[0]

        prefix = next(iter(prefix_counts))

        anchors[municipality_index] = {
            "city_id": city_id,
            "state": state["abbreviation"],
            "old_city_name": city["name"],
            "municipality_id": municipalities.loc[
                municipality_index,
                "id",
            ],
            "municipality_name": municipalities.loc[
                municipality_index,
                "name",
            ],
            "prefix": prefix,
            "cep_records": prefix_counts[prefix],
        }

    return anchors


def calculate_primary_helloquiz_regions(
    municipalities: gpd.GeoDataFrame,
    helloquiz: gpd.GeoDataFrame,
) -> dict[int, dict[str, Any]]:
    """
    Assign each municipality to its largest-area HelloQuiz region.
    """

    municipalities_area = municipalities.to_crs(AREA_CRS)
    helloquiz_area = helloquiz.to_crs(AREA_CRS)

    spatial_index = helloquiz_area.sindex

    assignments: dict[int, dict[str, Any]] = {}

    for municipality_index, municipality in municipalities_area.iterrows():
        geometry: BaseGeometry = municipality.geometry

        if geometry is None or geometry.is_empty:
            continue

        municipality_area = geometry.area

        if municipality_area <= 0:
            continue

        candidate_indexes = spatial_index.query(
            geometry,
            predicate="intersects",
        )

        best_index: int | None = None
        best_area = 0.0

        for candidate_index in candidate_indexes:
            candidate_geometry = helloquiz_area.iloc[
                candidate_index
            ].geometry

            intersection_area = geometry.intersection(
                candidate_geometry
            ).area

            if intersection_area > best_area:
                best_area = intersection_area
                best_index = int(candidate_index)

        if best_index is None:
            continue

        region = helloquiz_area.iloc[best_index]

        assignments[municipality_index] = {
            "helloquiz_label": region["helloquiz_label"],
            "allowed_prefixes": set(
                region["allowed_prefixes"]
            ),
            "overlap_fraction": best_area / municipality_area,
        }

    return assignments


def build_adjacency(
    municipalities: gpd.GeoDataFrame,
) -> dict[int, set[int]]:
    """
    Build municipality adjacency from shared polygon boundaries.

    Two municipalities are considered adjacent when their polygons touch.
    """

    adjacency: dict[int, set[int]] = defaultdict(set)

    spatial_index = municipalities.sindex

    for index, municipality in municipalities.iterrows():
        geometry: BaseGeometry = municipality.geometry

        if geometry is None or geometry.is_empty:
            continue

        candidate_indexes = spatial_index.query(
            geometry,
            predicate="intersects",
        )

        for candidate_index in candidate_indexes:
            candidate_index = int(candidate_index)

            if candidate_index == index:
                continue

            candidate_geometry = municipalities.loc[
                candidate_index,
                "geometry",
            ]

            if geometry.touches(candidate_geometry):
                adjacency[index].add(candidate_index)

    return adjacency


def infer_prefix(
    target_index: int,
    candidate_anchor_indexes: set[int],
    anchors: dict[int, dict[str, Any]],
    assignments: dict[int, dict[str, Any]],
    adjacency: dict[int, set[int]],
    centroids: dict[int, BaseGeometry],
) -> tuple[str | None, str, list[str]]:
    """
    Infer one municipality's CEP-2 prefix from remaining anchors.

    Adjacent known anchors are preferred. If adjacent evidence does not produce
    a unique result, the nearest known anchor centroid is used.
    """

    assignment = assignments.get(target_index)

    if assignment is None:
        return None, "no-region", []

    allowed_prefixes: set[str] = assignment["allowed_prefixes"]

    eligible_anchors = {
        index
        for index in candidate_anchor_indexes
        if index in assignments
        and anchors[index]["prefix"] in allowed_prefixes
        and assignments[index]["helloquiz_label"]
        == assignment["helloquiz_label"]
    }

    if not eligible_anchors:
        return None, "no-anchor", []

    adjacent_anchor_indexes = sorted(
        adjacency.get(target_index, set())
        & eligible_anchors
    )

    if adjacent_anchor_indexes:
        adjacent_prefixes = [
            anchors[index]["prefix"]
            for index in adjacent_anchor_indexes
        ]

        counts = Counter(adjacent_prefixes)

        highest_count = max(counts.values())

        winners = sorted(
            prefix
            for prefix, count in counts.items()
            if count == highest_count
        )

        if len(winners) == 1:
            return (
                winners[0],
                "adjacent-majority",
                adjacent_prefixes,
            )

    target_centroid = centroids[target_index]

    nearest_index = min(
        eligible_anchors,
        key=lambda index: target_centroid.distance(
            centroids[index]
        ),
    )

    return (
        anchors[nearest_index]["prefix"],
        "nearest-anchor",
        [
            anchors[index]["prefix"]
            for index in adjacent_anchor_indexes
        ],
    )


def run_validation(
    municipalities: gpd.GeoDataFrame,
    anchors: dict[int, dict[str, Any]],
    assignments: dict[int, dict[str, Any]],
    adjacency: dict[int, set[int]],
) -> list[dict[str, Any]]:
    """
    Perform leave-one-out validation for anchors in grouped HelloQuiz regions.
    """

    projected = municipalities.to_crs(AREA_CRS)

    centroids = {
        index: geometry.centroid
        for index, geometry
        in projected.geometry.items()
    }

    grouped_anchor_indexes = {
        index
        for index, anchor in anchors.items()
        if index in assignments
        and len(
            assignments[index]["allowed_prefixes"]
        ) > 1
        and anchor["prefix"]
        in assignments[index]["allowed_prefixes"]
    }

    rows: list[dict[str, Any]] = []

    for target_index in sorted(grouped_anchor_indexes):
        target = anchors[target_index]
        assignment = assignments[target_index]

        candidate_anchor_indexes = (
            grouped_anchor_indexes - {target_index}
        )

        prediction, method, adjacent_prefixes = infer_prefix(
            target_index,
            candidate_anchor_indexes,
            anchors,
            assignments,
            adjacency,
            centroids,
        )

        rows.append(
            {
                "municipality_index": target_index,
                "municipality_id": target["municipality_id"],
                "municipality_name": target["municipality_name"],
                "state": target["state"],
                "helloquiz_label": assignment["helloquiz_label"],
                "allowed_prefixes": sorted(
                    assignment["allowed_prefixes"]
                ),
                "actual_prefix": target["prefix"],
                "predicted_prefix": prediction,
                "correct": prediction == target["prefix"],
                "method": method,
                "adjacent_anchor_prefixes": adjacent_prefixes,
                "helloquiz_overlap_percent": (
                    assignment["overlap_fraction"] * 100
                ),
            }
        )

    return rows


def write_reports(
    rows: list[dict[str, Any]],
) -> None:
    """
    Write detailed CSV and summary JSON reports.
    """

    REPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with DETAILS_PATH.open(
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
                "actual_prefix",
                "predicted_prefix",
                "correct",
                "method",
                "adjacent_anchor_prefixes",
                "helloquiz_overlap_percent",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    row["municipality_id"],
                    row["municipality_name"],
                    row["state"],
                    row["helloquiz_label"],
                    ", ".join(row["allowed_prefixes"]),
                    row["actual_prefix"],
                    row["predicted_prefix"] or "",
                    row["correct"],
                    row["method"],
                    ", ".join(
                        row["adjacent_anchor_prefixes"]
                    ),
                    round(
                        row["helloquiz_overlap_percent"],
                        4,
                    ),
                ]
            )

    by_region: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "tests": 0,
            "correct": 0,
        }
    )

    by_method: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "tests": 0,
            "correct": 0,
        }
    )

    for row in rows:
        region_stats = by_region[
            row["helloquiz_label"]
        ]

        region_stats["tests"] += 1

        if row["correct"]:
            region_stats["correct"] += 1

        method_stats = by_method[row["method"]]

        method_stats["tests"] += 1

        if row["correct"]:
            method_stats["correct"] += 1

    total_tests = len(rows)
    total_correct = sum(
        row["correct"]
        for row in rows
    )

    summary = {
        "tests": total_tests,
        "correct": total_correct,
        "accuracy_percent": (
            round(
                total_correct / total_tests * 100,
                2,
            )
            if total_tests
            else 0.0
        ),
        "by_region": {
            label: {
                **stats,
                "accuracy_percent": (
                    round(
                        stats["correct"]
                        / stats["tests"]
                        * 100,
                        2,
                    )
                    if stats["tests"]
                    else 0.0
                ),
            }
            for label, stats in sorted(
                by_region.items()
            )
        },
        "by_method": {
            method: {
                **stats,
                "accuracy_percent": (
                    round(
                        stats["correct"]
                        / stats["tests"]
                        * 100,
                        2,
                    )
                    if stats["tests"]
                    else 0.0
                ),
            }
            for method, stats in sorted(
                by_method.items()
            )
        },
        "failures": [
            row
            for row in rows
            if not row["correct"]
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
    rows: list[dict[str, Any]],
) -> None:
    """
    Print validation accuracy and failures.
    """

    total = len(rows)
    correct = sum(
        row["correct"]
        for row in rows
    )

    print()
    print("Grouped-region holdout validation")
    print("---------------------------------")
    print(f"Tests:              {total:,}")
    print(f"Correct:            {correct:,}")

    if total:
        print(
            f"Accuracy:           "
            f"{correct / total * 100:.2f}%"
        )

    by_region: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        by_region[row["helloquiz_label"]].append(
            row
        )

    print()
    print("Accuracy by HelloQuiz region")
    print("----------------------------")

    for label, region_rows in sorted(
        by_region.items()
    ):
        region_correct = sum(
            row["correct"]
            for row in region_rows
        )

        print(
            f"{label:<8} "
            f"{region_correct:>2}/{len(region_rows):<2} "
            f"{region_correct / len(region_rows) * 100:6.2f}%"
        )

    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        by_method[row["method"]].append(row)

    print()
    print("Accuracy by inference method")
    print("----------------------------")

    for method, method_rows in sorted(
        by_method.items()
    ):
        method_correct = sum(
            row["correct"]
            for row in method_rows
        )

        print(
            f"{method:<20} "
            f"{method_correct:>2}/{len(method_rows):<2} "
            f"{method_correct / len(method_rows) * 100:6.2f}%"
        )

    failures = [
        row
        for row in rows
        if not row["correct"]
    ]

    if failures:
        print()
        print("Failed predictions")
        print("------------------")

        for row in failures:
            print(
                f"{row['state']}  "
                f"{row['municipality_name']}  "
                f"region={row['helloquiz_label']}  "
                f"actual={row['actual_prefix']}  "
                f"predicted={row['predicted_prefix']}  "
                f"method={row['method']}  "
                f"neighbors="
                f"{','.join(row['adjacent_anchor_prefixes']) or '-'}"
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
        f"{DETAILS_PATH.relative_to(PROJECT_ROOT)}"
    )


def main() -> None:
    """
    Run grouped-region holdout validation.
    """

    print("Loading brazil.db CEP information...")
    states, cities = load_brazil_db()

    print("Loading IBGE municipalities...")
    municipalities = load_municipalities()

    print("Loading HelloQuiz postal geometry...")
    helloquiz_path, helloquiz = load_helloquiz()

    print(
        "HelloQuiz source: "
        f"{helloquiz_path.relative_to(PROJECT_ROOT)}"
    )

    print("Matching known single-prefix CEP anchors...")
    anchors = match_known_anchors(
        states,
        cities,
        municipalities,
    )

    print(
        f"Known single-prefix anchors: "
        f"{len(anchors):,}"
    )

    print("Assigning municipalities to HelloQuiz regions...")
    assignments = calculate_primary_helloquiz_regions(
        municipalities,
        helloquiz,
    )

    print("Building municipality adjacency graph...")
    adjacency = build_adjacency(
        municipalities
    )

    print("Running leave-one-out validation...")
    rows = run_validation(
        municipalities,
        anchors,
        assignments,
        adjacency,
    )

    write_reports(rows)
    print_summary(rows)


if __name__ == "__main__":
    main()