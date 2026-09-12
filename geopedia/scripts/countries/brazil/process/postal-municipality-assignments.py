"""
Assign approximate Brazil CEP-2 regions to IBGE municipalities.

This script combines:

1. GeoPedia's processed 2025 IBGE municipality geometry.
2. brazil.db's 2012 street-level CEP data.
3. HelloQuiz's broad two-digit postal-region geometry.

Assignment priority:

1. Known multi-prefix municipalities from brazil.db are preserved exactly.
2. Known single-prefix municipalities from brazil.db are preserved exactly.
3. Municipalities covered by a single-prefix HelloQuiz region receive that
   prefix directly.
4. Municipalities inside grouped HelloQuiz regions are assigned by geographic
   propagation from known single-prefix brazil.db anchors.
5. If a grouped-region municipality belongs to a disconnected component with
   no anchor, the nearest known anchor in the same HelloQuiz region is used.
6. If no usable anchor exists, the municipality remains unresolved.

Grouped-region propagation uses a multi-source shortest-path search through
the municipality adjacency graph. Edge weights are distances between projected
municipality centroids. This produces deterministic, geographically coherent
zones without pretending that the inferred boundaries are official Correios
boundaries.

This script generates intermediate inspection data only. It does not generate
the final runtime quiz GeoJSON.
"""

from __future__ import annotations

import csv
import heapq
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import mapping
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

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "brazil"
    / "postal"
)

OUTPUT_GEOJSON_PATH = (
    OUTPUT_DIRECTORY
    / "municipalities-with-cep2.geojson"
)

OUTPUT_CSV_PATH = (
    OUTPUT_DIRECTORY
    / "municipality-cep2-assignments.csv"
)

OUTPUT_SUMMARY_PATH = (
    OUTPUT_DIRECTORY
    / "municipality-cep2-assignment-summary.json"
)


# Equal-area Brazil projection used for intersection and centroid-distance
# calculations. Runtime output remains EPSG:4326.
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

# Historical or alternate municipality names in brazil.db that differ from
# the current IBGE municipality names used by GeoPedia.
BRAZIL_DB_MUNICIPALITY_NAME_ALIASES = {
    ("GO", "planaltina de goias"): "planaltina",
    ("RS", "santana do livramento"): "sant ana do livramento",
}

BRAZIL_MANUAL_CEP2_OVERRIDES = {
    ("PE", "fernando de noronha"): ["53"],
}


def decode_mysql_string(value: str) -> str:
    """
    Decode the subset of MySQL escaping needed for source place names.
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

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(value.split())


def normalize_helloquiz_label(value: object) -> str:
    """
    Normalize punctuation and encoding artifacts in HelloQuiz labels.
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
    Convert a HelloQuiz region label into possible CEP-2 prefixes.

    Examples:

    "35"    -> {"35"}
    "30-34" -> {"30", "31", "32", "33", "34"}
    "27x"   -> {"27"}
    "279"   -> {"27"}
    "0x"    -> {"01", ..., "09"}
    """

    normalized = normalize_helloquiz_label(
        label
    ).casefold()

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
        return {
            three_digit_match.group(1)
        }

    two_digit_x_match = re.fullmatch(
        r"(\d{2})x",
        normalized,
    )

    if two_digit_x_match:
        return {
            two_digit_x_match.group(1)
        }

    one_digit_x_match = re.fullmatch(
        r"(\d)x",
        normalized,
    )

    if one_digit_x_match:
        first_digit = int(
            one_digit_x_match.group(1)
        )

        prefixes = {
            f"{value:02d}"
            for value in range(
                first_digit * 10,
                first_digit * 10 + 10,
            )
        }

        # Brazil has no CEP-2 region 00 in the source data.
        prefixes.discard("00")

        return prefixes

    raise ValueError(
        "Unsupported HelloQuiz postal label: "
        f"{label!r}"
    )


def find_helloquiz_path() -> Path:
    """
    Locate the raw HelloQuiz Brazil postal GeoJSON.
    """

    if not HELLOQUIZ_DIRECTORY.exists():
        raise FileNotFoundError(
            "HelloQuiz directory was not found:\n"
            f"{HELLOQUIZ_DIRECTORY}"
        )

    candidates = sorted(
        HELLOQUIZ_DIRECTORY.rglob("*.geojson")
    )

    if not candidates:
        raise FileNotFoundError(
            "No GeoJSON files were found under:\n"
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
        "Multiple possible HelloQuiz files were found:\n"
        f"{candidate_list}"
    )


def load_brazil_db() -> tuple[
    dict[int, dict[str, str]],
    dict[int, dict[str, Any]],
]:
    """
    Parse brazil.db states, cities, and CEP-2 membership.
    """

    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"CEP SQL dump was not found:\n{SQL_PATH}"
        )

    states: dict[int, dict[str, str]] = {}
    cities: dict[int, dict[str, Any]] = {}

    city_prefix_counts: dict[
        int,
        Counter[str],
    ] = defaultdict(Counter)

    with SQL_PATH.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:
        for line_number, raw_line in enumerate(
            file,
            start=1,
        ):
            line = raw_line.rstrip("\r\n")

            if line.startswith(
                "INSERT INTO `tend_estado`"
            ):
                match = STATE_INSERT_RE.match(line)

                if not match:
                    raise ValueError(
                        "Could not parse tend_estado INSERT "
                        f"on line {line_number}."
                    )

                state_id = int(match.group(1))

                states[state_id] = {
                    "name": decode_mysql_string(
                        match.group(2)
                    ),
                    "abbreviation": match.group(3),
                }

                continue

            if line.startswith(
                "INSERT INTO `tend_cidade`"
            ):
                match = CITY_INSERT_RE.match(line)

                if not match:
                    raise ValueError(
                        "Could not parse tend_cidade INSERT "
                        f"on line {line_number}."
                    )

                city_id = int(match.group(1))

                cities[city_id] = {
                    "name": decode_mysql_string(
                        match.group(3)
                    ),
                    "state_id": int(
                        match.group(2)
                    ),
                    "prefix_counts": Counter(),
                }

                continue

            if not line.startswith(
                "INSERT INTO `tend_endereco`"
            ):
                continue

            match = ADDRESS_INSERT_RE.match(line)

            if not match:
                raise ValueError(
                    "Could not parse tend_endereco INSERT "
                    f"on line {line_number}."
                )

            cep = match.group(1)
            city_id = int(match.group(2))

            if not VALID_CEP_RE.fullmatch(cep):
                continue

            city_prefix_counts[
                city_id
            ][cep[:2]] += 1

    for city_id, prefix_counts in (
        city_prefix_counts.items()
    ):
        city = cities.get(city_id)

        if city is None:
            raise ValueError(
                "CEP row references unknown city ID "
                f"{city_id}."
            )

        city["prefix_counts"] = prefix_counts

    return states, cities


def load_municipalities() -> gpd.GeoDataFrame:
    """
    Load GeoPedia's processed 2025 IBGE municipalities.
    """

    if not MUNICIPALITIES_PATH.exists():
        raise FileNotFoundError(
            "Municipality GeoJSON was not found:\n"
            f"{MUNICIPALITIES_PATH}"
        )

    municipalities = gpd.read_file(
        MUNICIPALITIES_PATH
    )

    required_columns = {
        "id",
        "name",
        "state_id",
        "geometry",
    }

    missing_columns = (
        required_columns
        - set(municipalities.columns)
    )

    if missing_columns:
        raise ValueError(
            "Municipality GeoJSON is missing "
            "required properties: "
            f"{sorted(missing_columns)}"
        )

    municipalities = municipalities[
        [
            "id",
            "name",
            "state_id",
            "geometry",
        ]
    ].copy()

    municipalities["id"] = municipalities[
        "id"
    ].astype(str)

    municipalities["name"] = municipalities[
        "name"
    ].astype(str)

    municipalities["state_id"] = municipalities[
        "state_id"
    ].astype(str)

    municipalities["state"] = municipalities[
        "state_id"
    ].map(
        STATE_ID_TO_ABBREVIATION
    )

    if municipalities["state"].isna().any():
        unknown = sorted(
            municipalities.loc[
                municipalities["state"].isna(),
                "state_id",
            ].unique()
        )

        raise ValueError(
            "Unknown municipality state IDs: "
            f"{unknown}"
        )

    municipalities[
        "normalized_name"
    ] = municipalities["name"].map(
        normalize_name
    )

    if municipalities.crs is None:
        municipalities = municipalities.set_crs(
            "EPSG:4326"
        )

    return municipalities


def load_helloquiz() -> tuple[
    Path,
    gpd.GeoDataFrame,
]:
    """
    Load the HelloQuiz two-digit postal geometry.
    """

    path = find_helloquiz_path()

    helloquiz = gpd.read_file(path)

    if "AreaCode" not in helloquiz.columns:
        raise ValueError(
            "HelloQuiz GeoJSON does not contain "
            "the expected AreaCode property."
        )

    if helloquiz.crs is None:
        helloquiz = helloquiz.set_crs(
            "EPSG:4326"
        )

    helloquiz = helloquiz[
        [
            "AreaCode",
            "geometry",
        ]
    ].copy()

    helloquiz[
        "helloquiz_label"
    ] = helloquiz["AreaCode"].map(
        normalize_helloquiz_label
    )

    helloquiz[
        "allowed_prefixes"
    ] = helloquiz["helloquiz_label"].map(
        lambda label: sorted(
            helloquiz_label_to_prefixes(
                label
            )
        )
    )

    return path, helloquiz


def match_known_cities(
    states: dict[int, dict[str, str]],
    cities: dict[int, dict[str, Any]],
    municipalities: gpd.GeoDataFrame,
) -> dict[int, dict[str, Any]]:
    """
    Match brazil.db cities with CEP evidence to current IBGE municipalities.
    """

    lookup: dict[
        tuple[str, str],
        list[int],
    ] = defaultdict(list)

    for (
        municipality_index,
        municipality,
    ) in municipalities.iterrows():
        
        state_abbreviation = municipality[
            "state"
        ]

        normalized_municipality_name = (
            normalize_name(
                municipality["name"]
            )
        )

        key = (
            state_abbreviation,
            normalized_municipality_name,
        )

        lookup[key].append(
            municipality_index
        )

    matched: dict[int, dict[str, Any]] = {}

    for city_id, city in cities.items():
        prefix_counts: Counter[str] = (
            city["prefix_counts"]
        )

        if not prefix_counts:
            continue

        state = states.get(
            city["state_id"]
        )

        if state is None:
            continue

        state_abbreviation = state[
            "abbreviation"
        ]

        normalized_city_name = normalize_name(
            city["name"]
        )

        normalized_city_name = (
            BRAZIL_DB_MUNICIPALITY_NAME_ALIASES.get(
                (
                    state_abbreviation,
                    normalized_city_name,
                ),
                normalized_city_name,
            )
        )

        key = (
            state_abbreviation,
            normalized_city_name,
        )

        candidates = lookup.get(
            key,
            [],
        )

        if len(candidates) != 1:
            continue

        municipality_index = candidates[0]

        if municipality_index in matched:
            raise ValueError(
                "Multiple brazil.db CEP cities matched "
                "the same municipality: "
                f"{municipalities.loc[municipality_index, 'name']}"
            )

        matched[municipality_index] = {
            "city_id": city_id,
            "prefixes": sorted(
                prefix_counts
            ),
            "prefix_counts": dict(
                sorted(
                    prefix_counts.items()
                )
            ),
        }

    return matched


def calculate_primary_helloquiz_regions(
    municipalities: gpd.GeoDataFrame,
    helloquiz: gpd.GeoDataFrame,
) -> dict[int, dict[str, Any]]:
    """
    Find the HelloQuiz region covering the largest area of each municipality.
    """

    municipalities_area = (
        municipalities.to_crs(
            AREA_CRS
        )
    )

    helloquiz_area = helloquiz.to_crs(
        AREA_CRS
    )

    spatial_index = (
        helloquiz_area.sindex
    )

    assignments: dict[
        int,
        dict[str, Any],
    ] = {}

    for (
        municipality_index,
        municipality,
    ) in municipalities_area.iterrows():
        geometry: BaseGeometry = (
            municipality.geometry
        )

        if (
            geometry is None
            or geometry.is_empty
        ):
            continue

        municipality_area = geometry.area

        if municipality_area <= 0:
            continue

        candidate_indexes = (
            spatial_index.query(
                geometry,
                predicate="intersects",
            )
        )

        best_index: int | None = None
        best_area = 0.0

        for candidate_index in (
            candidate_indexes
        ):
            candidate_index = int(
                candidate_index
            )

            candidate_geometry = (
                helloquiz_area.iloc[
                    candidate_index
                ].geometry
            )

            intersection_area = (
                geometry.intersection(
                    candidate_geometry
                ).area
            )

            if intersection_area > best_area:
                best_area = intersection_area
                best_index = candidate_index

        if best_index is None:
            continue

        region = helloquiz_area.iloc[
            best_index
        ]

        assignments[
            municipality_index
        ] = {
            "helloquiz_label": region[
                "helloquiz_label"
            ],
            "allowed_prefixes": set(
                region[
                    "allowed_prefixes"
                ]
            ),
            "overlap_fraction": (
                best_area
                / municipality_area
            ),
        }

    return assignments


def build_adjacency(
    municipalities: gpd.GeoDataFrame,
) -> dict[int, set[int]]:
    """
    Build a graph connecting municipalities that share polygon boundaries.
    """

    adjacency: dict[
        int,
        set[int],
    ] = defaultdict(set)

    spatial_index = municipalities.sindex

    for (
        municipality_index,
        municipality,
    ) in municipalities.iterrows():
        geometry: BaseGeometry = (
            municipality.geometry
        )

        if (
            geometry is None
            or geometry.is_empty
        ):
            continue

        candidates = spatial_index.query(
            geometry,
            predicate="intersects",
        )

        for candidate_index in candidates:
            candidate_index = int(
                candidate_index
            )

            if (
                candidate_index
                == municipality_index
            ):
                continue

            candidate_geometry = (
                municipalities.loc[
                    candidate_index,
                    "geometry",
                ]
            )

            if geometry.touches(
                candidate_geometry
            ):
                adjacency[
                    municipality_index
                ].add(candidate_index)

                adjacency[
                    candidate_index
                ].add(municipality_index)

    return adjacency


def calculate_centroids(
    municipalities: gpd.GeoDataFrame,
) -> dict[int, BaseGeometry]:
    """
    Calculate municipality centroids in the projected working CRS.
    """

    projected = municipalities.to_crs(
        AREA_CRS
    )

    return {
        index: geometry.centroid
        for index, geometry
        in projected.geometry.items()
    }


def edge_distance(
    first_index: int,
    second_index: int,
    centroids: dict[
        int,
        BaseGeometry,
    ],
) -> float:
    """
    Return projected centroid distance between adjacent municipalities.
    """

    return centroids[
        first_index
    ].distance(
        centroids[
            second_index
        ]
    )


def propagate_grouped_region(
    region_indexes: set[int],
    seed_prefixes: dict[int, str],
    adjacency: dict[int, set[int]],
    centroids: dict[int, BaseGeometry],
) -> dict[
    int,
    dict[str, Any],
]:
    """
    Propagate known CEP-2 seeds through one grouped HelloQuiz region.

    Multi-source Dijkstra propagation assigns each reachable municipality to
    the geographically closest seed through the municipality adjacency graph.

    Equal-distance ties are resolved deterministically by CEP prefix.
    """

    if not seed_prefixes:
        return {}

    best: dict[
        int,
        tuple[float, str, int],
    ] = {}

    queue: list[
        tuple[
            float,
            str,
            int,
            int,
        ]
    ] = []

    for (
        seed_index,
        prefix,
    ) in sorted(
        seed_prefixes.items(),
        key=lambda item: (
            item[1],
            item[0],
        ),
    ):
        best[seed_index] = (
            0.0,
            prefix,
            seed_index,
        )

        heapq.heappush(
            queue,
            (
                0.0,
                prefix,
                seed_index,
                seed_index,
            ),
        )

    while queue:
        (
            distance,
            prefix,
            seed_index,
            current_index,
        ) = heapq.heappop(queue)

        current_best = best.get(
            current_index
        )

        if current_best is None:
            continue

        if (
            distance,
            prefix,
            seed_index,
        ) != current_best:
            continue

        for neighbor_index in adjacency.get(
            current_index,
            set(),
        ):
            if (
                neighbor_index
                not in region_indexes
            ):
                continue

            new_distance = (
                distance
                + edge_distance(
                    current_index,
                    neighbor_index,
                    centroids,
                )
            )

            new_value = (
                new_distance,
                prefix,
                seed_index,
            )

            previous = best.get(
                neighbor_index
            )

            if (
                previous is None
                or new_value < previous
            ):
                best[
                    neighbor_index
                ] = new_value

                heapq.heappush(
                    queue,
                    (
                        new_distance,
                        prefix,
                        seed_index,
                        neighbor_index,
                    ),
                )

    return {
        municipality_index: {
            "prefix": prefix,
            "seed_index": seed_index,
            "path_distance_m": distance,
        }
        for (
            municipality_index,
            (
                distance,
                prefix,
                seed_index,
            ),
        ) in best.items()
    }


def nearest_seed_assignment(
    target_index: int,
    seed_prefixes: dict[int, str],
    centroids: dict[int, BaseGeometry],
) -> tuple[
    str,
    int,
    float,
] | None:
    """
    Find the nearest seed centroid when graph propagation cannot reach a target.
    """

    if not seed_prefixes:
        return None

    target_centroid = centroids[
        target_index
    ]

    candidates = []

    for (
        seed_index,
        prefix,
    ) in seed_prefixes.items():
        distance = (
            target_centroid.distance(
                centroids[
                    seed_index
                ]
            )
        )

        candidates.append(
            (
                distance,
                prefix,
                seed_index,
            )
        )

    distance, prefix, seed_index = min(
        candidates
    )

    return (
        prefix,
        seed_index,
        distance,
    )


def build_assignments(
    municipalities: gpd.GeoDataFrame,
    known_cities: dict[
        int,
        dict[str, Any],
    ],
    helloquiz_assignments: dict[
        int,
        dict[str, Any],
    ],
    adjacency: dict[int, set[int]],
    centroids: dict[
        int,
        BaseGeometry,
    ],
) -> dict[int, dict[str, Any]]:
    """
    Assign CEP-2 values to all possible municipalities.
    """

    results: dict[
        int,
        dict[str, Any],
    ] = {}

    # Known brazil.db evidence always takes priority.
    for (
        municipality_index,
        known,
    ) in known_cities.items():
        prefixes = known[
            "prefixes"
        ]

        results[
            municipality_index
        ] = {
            "postal_codes": prefixes,
            "assignment_method": (
                "known-single"
                if len(prefixes) == 1
                else "known-multiple"
            ),
            "source_seed_index": (
                municipality_index
                if len(prefixes) == 1
                else None
            ),
            "path_distance_m": 0.0,
        }


    # Manual overrides for municipalities not covered by the source datasets.
    for (
        municipality_index,
        municipality,
    ) in municipalities.iterrows():
        if municipality_index in results:
            continue
    
        override = BRAZIL_MANUAL_CEP2_OVERRIDES.get(
            (
                municipality["state"],
                normalize_name(
                    municipality["name"]
                ),
            )
        )

        if override is None:
            continue

        results[municipality_index] = {
            "postal_codes": override,
            "assignment_method": "manual-override",
            "source_seed_index": None,
            "path_distance_m": None,
        }


    # HelloQuiz regions containing only one normalized CEP-2 prefix can be
    # assigned directly unless brazil.db already provided stronger evidence.
    for (
        municipality_index,
        helloquiz,
    ) in helloquiz_assignments.items():
        if municipality_index in results:
            continue

        allowed_prefixes = (
            helloquiz[
                "allowed_prefixes"
            ]
        )

        if len(allowed_prefixes) != 1:
            continue

        results[
            municipality_index
        ] = {
            "postal_codes": sorted(
                allowed_prefixes
            ),
            "assignment_method": (
                "helloquiz-exact"
            ),
            "source_seed_index": None,
            "path_distance_m": None,
        }

    grouped_by_label: dict[
        str,
        set[int],
    ] = defaultdict(set)

    for (
        municipality_index,
        helloquiz,
    ) in helloquiz_assignments.items():
        if len(
            helloquiz[
                "allowed_prefixes"
            ]
        ) <= 1:
            continue

        grouped_by_label[
            helloquiz[
                "helloquiz_label"
            ]
        ].add(
            municipality_index
        )

    for (
        label,
        region_indexes,
    ) in sorted(
        grouped_by_label.items()
    ):
        allowed_prefixes = set()

        for index in region_indexes:
            allowed_prefixes.update(
                helloquiz_assignments[
                    index
                ][
                    "allowed_prefixes"
                ]
            )

        seed_prefixes: dict[
            int,
            str,
        ] = {}

        for index in region_indexes:
            known = known_cities.get(
                index
            )

            if known is None:
                continue

            prefixes = known[
                "prefixes"
            ]

            if len(prefixes) != 1:
                continue

            prefix = prefixes[0]

            if prefix not in allowed_prefixes:
                continue

            seed_prefixes[index] = prefix

        propagated = (
            propagate_grouped_region(
                region_indexes,
                seed_prefixes,
                adjacency,
                centroids,
            )
        )

        for index in region_indexes:
            # Preserve known single or multiple brazil.db evidence.
            if index in results:
                continue

            propagated_value = (
                propagated.get(index)
            )

            if propagated_value is not None:
                results[index] = {
                    "postal_codes": [
                        propagated_value[
                            "prefix"
                        ]
                    ],
                    "assignment_method": (
                        "propagated"
                    ),
                    "source_seed_index": (
                        propagated_value[
                            "seed_index"
                        ]
                    ),
                    "path_distance_m": (
                        propagated_value[
                            "path_distance_m"
                        ]
                    ),
                }

                continue

            fallback = (
                nearest_seed_assignment(
                    index,
                    seed_prefixes,
                    centroids,
                )
            )

            if fallback is not None:
                (
                    prefix,
                    seed_index,
                    distance,
                ) = fallback

                results[index] = {
                    "postal_codes": [
                        prefix
                    ],
                    "assignment_method": (
                        "nearest-seed-fallback"
                    ),
                    "source_seed_index": (
                        seed_index
                    ),
                    "path_distance_m": (
                        distance
                    ),
                }

                continue

            results[index] = {
                "postal_codes": [],
                "assignment_method": (
                    "unresolved"
                ),
                "source_seed_index": None,
                "path_distance_m": None,
            }

    # Any municipality with no usable HelloQuiz overlap and no known
    # brazil.db evidence remains explicitly unresolved.
    for index in municipalities.index:
        if index in results:
            continue

        results[index] = {
            "postal_codes": [],
            "assignment_method": (
                "unresolved"
            ),
            "source_seed_index": None,
            "path_distance_m": None,
        }

    return results


def validate_assignments(
    municipalities: gpd.GeoDataFrame,
    assignments: dict[
        int,
        dict[str, Any],
    ],
    helloquiz_assignments: dict[
        int,
        dict[str, Any],
    ],
) -> None:
    """
    Validate final intermediate assignment structure.
    """

    if len(assignments) != len(
        municipalities
    ):
        raise ValueError(
            "Assignment count does not match "
            "municipality count."
        )

    for index in municipalities.index:
        assignment = assignments[
            index
        ]

        postal_codes = assignment[
            "postal_codes"
        ]

        if len(
            postal_codes
        ) != len(set(postal_codes)):
            raise ValueError(
                "Duplicate postal code assignment for "
                f"{municipalities.loc[index, 'name']}."
            )

        for prefix in postal_codes:
            if not re.fullmatch(
                r"\d{2}",
                prefix,
            ):
                raise ValueError(
                    "Invalid CEP-2 assignment "
                    f"{prefix!r} for "
                    f"{municipalities.loc[index, 'name']}."
                )

        if (
            assignment[
                "assignment_method"
            ]
            == "propagated"
        ):
            helloquiz = (
                helloquiz_assignments.get(
                    index
                )
            )

            if helloquiz is None:
                raise ValueError(
                    "Propagated municipality has no "
                    "HelloQuiz region."
                )

            if not set(
                postal_codes
            ).issubset(
                helloquiz[
                    "allowed_prefixes"
                ]
            ):
                raise ValueError(
                    "Propagated CEP prefix falls outside "
                    "the municipality's HelloQuiz constraint."
                )


def write_geojson(
    municipalities: gpd.GeoDataFrame,
    assignments: dict[
        int,
        dict[str, Any],
    ],
    helloquiz_assignments: dict[
        int,
        dict[str, Any],
    ],
) -> None:
    """
    Write municipality assignments as GeoJSON with native postal-code arrays.
    """

    features = []

    for (
        municipality_index,
        municipality,
    ) in municipalities.iterrows():
        assignment = assignments[
            municipality_index
        ]

        helloquiz = (
            helloquiz_assignments.get(
                municipality_index
            )
        )

        seed_index = assignment[
            "source_seed_index"
        ]

        if seed_index is None:
            seed_id = None
            seed_name = None
        else:
            seed_id = municipalities.loc[
                seed_index,
                "id",
            ]

            seed_name = municipalities.loc[
                seed_index,
                "name",
            ]

        feature = {
            "type": "Feature",
            "properties": {
                "id": municipality[
                    "id"
                ],
                "name": municipality[
                    "name"
                ],
                "state_id": municipality[
                    "state_id"
                ],
                "state": municipality[
                    "state"
                ],
                "postal_codes": assignment[
                    "postal_codes"
                ],
                "assignment_method": assignment[
                    "assignment_method"
                ],
                "helloquiz_label": (
                    helloquiz[
                        "helloquiz_label"
                    ]
                    if helloquiz
                    else None
                ),
                "helloquiz_overlap": (
                    round(
                        helloquiz[
                            "overlap_fraction"
                        ],
                        6,
                    )
                    if helloquiz
                    else None
                ),
                "source_seed_id": seed_id,
                "source_seed_name": seed_name,
                "path_distance_km": (
                    round(
                        assignment[
                            "path_distance_m"
                        ]
                        / 1000,
                        3,
                    )
                    if assignment[
                        "path_distance_m"
                    ]
                    is not None
                    else None
                ),
            },
            "geometry": mapping(
                municipality.geometry
            ),
        }

        features.append(feature)

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    with OUTPUT_GEOJSON_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def write_csv(
    municipalities: gpd.GeoDataFrame,
    assignments: dict[
        int,
        dict[str, Any],
    ],
    helloquiz_assignments: dict[
        int,
        dict[str, Any],
    ],
) -> None:
    """
    Write a human-readable municipality assignment table.
    """

    with OUTPUT_CSV_PATH.open(
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
                "postal_codes",
                "assignment_method",
                "helloquiz_label",
                "helloquiz_overlap_percent",
                "source_seed_id",
                "source_seed_name",
                "path_distance_km",
            ]
        )

        for (
            municipality_index,
            municipality,
        ) in municipalities.iterrows():
            assignment = assignments[
                municipality_index
            ]

            helloquiz = (
                helloquiz_assignments.get(
                    municipality_index
                )
            )

            seed_index = assignment[
                "source_seed_index"
            ]

            writer.writerow(
                [
                    municipality["id"],
                    municipality["name"],
                    municipality["state"],
                    ", ".join(
                        assignment[
                            "postal_codes"
                        ]
                    ),
                    assignment[
                        "assignment_method"
                    ],
                    (
                        helloquiz[
                            "helloquiz_label"
                        ]
                        if helloquiz
                        else ""
                    ),
                    (
                        round(
                            helloquiz[
                                "overlap_fraction"
                            ] * 100,
                            4,
                        )
                        if helloquiz
                        else ""
                    ),
                    (
                        municipalities.loc[
                            seed_index,
                            "id",
                        ]
                        if seed_index
                        is not None
                        else ""
                    ),
                    (
                        municipalities.loc[
                            seed_index,
                            "name",
                        ]
                        if seed_index
                        is not None
                        else ""
                    ),
                    (
                        round(
                            assignment[
                                "path_distance_m"
                            ]
                            / 1000,
                            3,
                        )
                        if assignment[
                            "path_distance_m"
                        ]
                        is not None
                        else ""
                    ),
                ]
            )


def write_summary(
    municipalities: gpd.GeoDataFrame,
    assignments: dict[
        int,
        dict[str, Any],
    ],
    helloquiz_assignments: dict[
        int,
        dict[str, Any],
    ],
) -> dict[str, Any]:
    """
    Write assignment statistics and return the summary object.
    """

    method_counts = Counter(
        assignment[
            "assignment_method"
        ]
        for assignment
        in assignments.values()
    )

    prefix_municipality_counts: Counter[
        str
    ] = Counter()

    represented_prefixes: set[str] = set()

    for assignment in assignments.values():
        for prefix in assignment[
            "postal_codes"
        ]:
            represented_prefixes.add(
                prefix
            )

            prefix_municipality_counts[
                prefix
            ] += 1

    grouped_regions: dict[
        str,
        dict[str, Any],
    ] = {}

    grouped_labels = sorted(
        {
            value[
                "helloquiz_label"
            ]
            for value
            in helloquiz_assignments.values()
            if len(
                value[
                    "allowed_prefixes"
                ]
            ) > 1
        }
    )

    for label in grouped_labels:
        region_indexes = [
            index
            for index, value
            in helloquiz_assignments.items()
            if (
                value[
                    "helloquiz_label"
                ]
                == label
            )
        ]

        allowed_prefixes: set[
            str
        ] = set()

        assigned_prefixes: set[
            str
        ] = set()

        methods = Counter()

        for index in region_indexes:
            allowed_prefixes.update(
                helloquiz_assignments[
                    index
                ][
                    "allowed_prefixes"
                ]
            )

            assigned_prefixes.update(
                assignments[
                    index
                ][
                    "postal_codes"
                ]
            )

            methods[
                assignments[
                    index
                ][
                    "assignment_method"
                ]
            ] += 1

        grouped_regions[label] = {
            "municipalities": len(
                region_indexes
            ),
            "allowed_prefixes": sorted(
                allowed_prefixes
            ),
            "assigned_prefixes": sorted(
                assigned_prefixes
            ),
            "assignment_methods": dict(
                sorted(
                    methods.items()
                )
            ),
        }

    unresolved = [
        {
            "id": municipalities.loc[
                index,
                "id",
            ],
            "name": municipalities.loc[
                index,
                "name",
            ],
            "state": municipalities.loc[
                index,
                "state",
            ],
            "helloquiz_label": (
                helloquiz_assignments[
                    index
                ][
                    "helloquiz_label"
                ]
                if index
                in helloquiz_assignments
                else None
            ),
        }
        for index, assignment
        in assignments.items()
        if assignment[
            "assignment_method"
        ] == "unresolved"
    ]

    summary = {
        "municipalities": len(
            municipalities
        ),
        "assignment_methods": dict(
            sorted(
                method_counts.items()
            )
        ),
        "represented_prefix_count": len(
            represented_prefixes
        ),
        "represented_prefixes": sorted(
            represented_prefixes
        ),
        "municipalities_per_prefix": dict(
            sorted(
                prefix_municipality_counts.items()
            )
        ),
        "grouped_regions": grouped_regions,
        "unresolved_count": len(
            unresolved
        ),
        "unresolved": unresolved,
    }

    with OUTPUT_SUMMARY_PATH.open(
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

    return summary


def print_summary(
    summary: dict[str, Any],
) -> None:
    """
    Print the important reconstruction statistics.
    """

    print()
    print("Municipality CEP-2 assignment")
    print("-----------------------------")
    print(
        f"Municipalities:         "
        f"{summary['municipalities']:,}"
    )

    print()
    print("Assignment methods")
    print("------------------")

    for (
        method,
        count,
    ) in summary[
        "assignment_methods"
    ].items():
        print(
            f"{method:<24} "
            f"{count:>5,}"
        )

    print()
    print("CEP-2 coverage")
    print("--------------")
    print(
        f"Distinct prefixes:      "
        f"{summary['represented_prefix_count']}"
    )

    print(
        "Values:                 "
        + ", ".join(
            summary[
                "represented_prefixes"
            ]
        )
    )

    print()
    print("Grouped HelloQuiz regions")
    print("-------------------------")

    for (
        label,
        region,
    ) in summary[
        "grouped_regions"
    ].items():
        allowed = ",".join(
            region[
                "allowed_prefixes"
            ]
        )

        assigned = ",".join(
            region[
                "assigned_prefixes"
            ]
        )

        methods = ", ".join(
            f"{method}={count}"
            for method, count
            in region[
                "assignment_methods"
            ].items()
        )

        print(
            f"{label:<8} "
            f"municipalities="
            f"{region['municipalities']:<3} "
            f"allowed=[{allowed}] "
            f"assigned=[{assigned}] "
            f"{methods}"
        )

    print()
    print(
        f"Unresolved municipalities: "
        f"{summary['unresolved_count']}"
    )

    if summary[
        "unresolved"
    ]:
        print()
        print("Unresolved")
        print("----------")

        for municipality in summary[
            "unresolved"
        ]:
            print(
                f"{municipality['state']}  "
                f"{municipality['name']}  "
                f"HelloQuiz="
                f"{municipality['helloquiz_label']}"
            )

    print()
    print("Outputs")
    print("-------")
    print(
        "GeoJSON: "
        f"{OUTPUT_GEOJSON_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "CSV:     "
        f"{OUTPUT_CSV_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "JSON:    "
        f"{OUTPUT_SUMMARY_PATH.relative_to(PROJECT_ROOT)}"
    )


def main() -> None:
    """
    Build the first complete municipality-level CEP-2 reconstruction.
    """

    print(
        "Loading brazil.db CEP information..."
    )

    states, cities = load_brazil_db()

    print(
        "Loading processed IBGE municipalities..."
    )

    municipalities = (
        load_municipalities()
    )

    print(
        "Loading HelloQuiz postal geometry..."
    )

    (
        helloquiz_path,
        helloquiz,
    ) = load_helloquiz()

    print(
        "HelloQuiz source: "
        f"{helloquiz_path.relative_to(PROJECT_ROOT)}"
    )

    print(
        "Matching brazil.db CEP cities "
        "to IBGE municipalities..."
    )

    known_cities = match_known_cities(
        states,
        cities,
        municipalities,
    )

    known_single_count = sum(
        len(value["prefixes"]) == 1
        for value in known_cities.values()
    )

    known_multiple_count = sum(
        len(value["prefixes"]) > 1
        for value in known_cities.values()
    )

    print(
        f"Matched CEP municipalities: "
        f"{len(known_cities):,}"
    )

    print(
        f"  Single-prefix: "
        f"{known_single_count:,}"
    )

    print(
        f"  Multi-prefix:  "
        f"{known_multiple_count:,}"
    )

    print(
        "Assigning municipalities to "
        "HelloQuiz regions..."
    )

    helloquiz_assignments = (
        calculate_primary_helloquiz_regions(
            municipalities,
            helloquiz,
        )
    )

    print(
        "Building municipality adjacency graph..."
    )

    adjacency = build_adjacency(
        municipalities
    )

    print(
        "Calculating municipality centroids..."
    )

    centroids = calculate_centroids(
        municipalities
    )

    print(
        "Propagating grouped CEP regions..."
    )

    assignments = build_assignments(
        municipalities,
        known_cities,
        helloquiz_assignments,
        adjacency,
        centroids,
    )

    print(
        "Validating assignments..."
    )

    validate_assignments(
        municipalities,
        assignments,
        helloquiz_assignments,
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Writing intermediate GeoJSON..."
    )

    write_geojson(
        municipalities,
        assignments,
        helloquiz_assignments,
    )

    print(
        "Writing assignment table..."
    )

    write_csv(
        municipalities,
        assignments,
        helloquiz_assignments,
    )

    print(
        "Writing summary..."
    )

    summary = write_summary(
        municipalities,
        assignments,
        helloquiz_assignments,
    )

    print_summary(
        summary
    )


if __name__ == "__main__":
    main()