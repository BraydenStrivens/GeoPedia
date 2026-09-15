from __future__ import annotations

import html
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "argentina"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "countries"
    / "argentina"
)

AREA_CODE_PATH = RAW_DIR / "areaCodeData2.js"

LOCALITIES_PATH = (
    RAW_DIR
    / "c1fc1f5b-dfe3-5231-9f3b-f7c703b906c7.json"
)

OUTPUT_GEOJSON_PATH = (
    PROCESSED_DIR
    / "phone-code-localities.geojson"
)

UNRESOLVED_PATH = (
    PROCESSED_DIR
    / "phone-code-localities-unresolved.json"
)

FUZZY_REVIEW_PATH = (
    PROCESSED_DIR
    / "phone-code-localities-fuzzy-auto.json"
)

GEOGRAPHIC_REVIEW_PATH = (
    PROCESSED_DIR
    / "phone-code-localities-geographic-auto.json"
)


TYPE_PRIORITY = {
    "LOCALIDAD": 3,
    "ENTIDAD": 2,
    "SITIO EDIFICADO": 1,
}


MANUAL_OVERRIDES = {
    (
        "BUENOS AIRES",
        "GENERAL MADARIAGA",
    ): 814,

    (
        "BUENOS AIRES",
        "HUANGUELEN SUR",
    ): 455,
}

FORCED_UNRESOLVED = {
    # -------------------------------------------------
    # Previously reviewed duplicate-coordinate matches
    # -------------------------------------------------

    (
        "BUENOS AIRES",
        "BARRIO SAN EDUARDO",
        "223",
    ),

    (
        "BUENOS AIRES",
        "SAN EDUARDO DEL MAR",
        "2291",
    ),

    (
        "BUENOS AIRES",
        "LAS PIEDRITAS",
        "2266",
    ),

    # -------------------------------------------------
    # Catamarca
    # -------------------------------------------------

    # Source says Dto Capital, but the matched official
    # locality is EL LINDERO in ANDALGALA. The 3835
    # source row explicitly identifies Andalgala.
    (
        "CATAMARCA",
        "EL LINDERO",
        "383",
    ),

    # -------------------------------------------------
    # Cordoba
    # -------------------------------------------------

    # Weaker containment match onto exact EL CRISPIN.
    (
        "CORDOBA",
        "AGUA DEL CRISPIN",
        "3542",
    ),

    # Generic EL BAÑADO was attached to BAÑADO DE SOTO.
    (
        "CORDOBA",
        "EL BANADO",
        "358",
    ),

    # North and south are distinct source areas but were
    # collapsed onto the same generic official point.
    # Neither should arbitrarily own that point.
    (
        "CORDOBA",
        "CANADA DEL MACHADO NORTE",
        "3574",
    ),

    (
        "CORDOBA",
        "CANADA DEL MACHADO SUR",
        "3573",
    ),

    # Both source rows were collapsed onto the same
    # official locality with conflicting codes.
    (
        "CORDOBA",
        "COLONIA CUATRO ESQUINAS",
        "3576",
    ),

    (
        "CORDOBA",
        "LAS CUATRO ESQUINAS",
        "353",
    ),

    # VILLA DOLORES has an exact 3544 source row.
    (
        "CORDOBA",
        "DOLORES",
        "3548",
    ),

    # LA CALERA has an exact 3543 source row. This
    # qualified source name was only containment-matched.
    (
        "CORDOBA",
        "LA CALERA CALAMUCHITA",
        "358",
    ),

    # East and west were both collapsed onto one generic
    # LAS PALMITAS point, so neither should own it.
    (
        "CORDOBA",
        "LAS PALMITAS ESTE",
        "3575",
    ),

    (
        "CORDOBA",
        "LAS PALMITAS OESTE",
        "3521",
    ),

    # Official data combines these as
    # LOS CEDROS - LAS QUINTAS, so a single point cannot
    # safely represent either conflicting source code.
    (
        "CORDOBA",
        "LAS QUINTAS",
        "358",
    ),

    (
        "CORDOBA",
        "LOS CEDROS",
        "3547",
    ),

    # Source says Rio Seco, but matched official point
    # is in SAN JAVIER. The 3544 row explicitly identifies
    # San Javier.
    (
        "CORDOBA",
        "LOS CERRILLOS",
        "3522",
    ),

    # VILLA YACANTO has an exact 3546 source row.
    (
        "CORDOBA",
        "YACANTO",
        "3544",
    ),

    # -------------------------------------------------
    # Corrientes
    # -------------------------------------------------

    # SAN ANTONIO has the stronger exact 3775 source row.
    (
        "CORRIENTES",
        "COLONIA SAN ANTONIO",
        "3786",
    ),

    # -------------------------------------------------
    # Jujuy
    # -------------------------------------------------

    # Source says El Carmen, while the matched official
    # point is in COCHINOCA. The 3888 row explicitly
    # identifies Cochinoca.
    (
        "JUJUY",
        "AGUA CALIENTE",
        "388",
    ),

    # -------------------------------------------------
    # Mendoza
    # -------------------------------------------------

    # Source says Lavalle, but matched official point is
    # SAN JOSE in TUPUNGATO. The 263 source row explicitly
    # identifies Tupungato.
    (
        "MENDOZA",
        "SAN JOSE",
        "261",
    ),

    # -------------------------------------------------
    # San Juan
    # -------------------------------------------------

    # Different official records happen to share the
    # exact same coordinate. ASTICA is an exact INDEC
    # match; Huerta De Huachi was only containment-matched.
    (
        "SAN JUAN",
        "HUERTA DE HUACHI",
        "2647",
    ),

    # -------------------------------------------------
    # Santa Cruz
    # -------------------------------------------------

    # PERITO MORENO has an exact 2963 source row.
    (
        "SANTA CRUZ",
        "VENTISQUERO PERITO MORENO",
        "2902",
    ),

    # -------------------------------------------------
    # Santa Fe
    # -------------------------------------------------

    # VILLA SAN JOSE has the stronger exact 3492 row.
    (
        "SANTA FE",
        "COLONIA SAN JOSE",
        "342",
    ),

    # -------------------------------------------------
    # Tucuman
    # -------------------------------------------------

    # LA TRINIDAD has the stronger exact 3865 row.
    (
        "TUCUMAN",
        "INGENIO LA TRINIDAD",
        "381",
    ),
}

AREA_CODE_11_DEPARTMENTS = {
    "ALMIRANTE BROWN",
    "AVELLANEDA",
    "BERAZATEGUI",
    "ESTEBAN ECHEVERRIA",
    "EZEIZA",
    "FLORENCIO VARELA",
    "GENERAL SAN MARTIN",
    "HURLINGHAM",
    "ITUZAINGO",
    "JOSE C PAZ",
    "LA MATANZA",
    "LANUS",
    "LOMAS DE ZAMORA",
    "MALVINAS ARGENTINAS",
    "MERLO",
    "MORENO",
    "MORON",
    "QUILMES",
    "SAN FERNANDO",
    "SAN ISIDRO",
    "SAN MIGUEL",
    "TIGRE",
    "TRES DE FEBRERO",
    "VICENTE LOPEZ",
}


PROVINCE_ALIASES = {
    "CAPITAL FEDERAL":
        "CIUDAD DE BUENOS AIRES",

    "CABA":
        "CIUDAD DE BUENOS AIRES",

    "CIUDAD AUTONOMA DE BUENOS AIRES":
        "CIUDAD DE BUENOS AIRES",

    "TIERRA DEL FUEGO ANTARTIDA E ISLAS DEL ATLANTICO SUR":
        "TIERRA DEL FUEGO",
}


TOKEN_ALIASES = {
    "GRAL": "GENERAL",
    "CNEL": "CORONEL",
    "DR": "DOCTOR",
    "ING": "INGENIERO",
    "PTE": "PRESIDENTE",
    "TTE": "TENIENTE",
    "CMTE": "COMANDANTE",
    "STA": "SANTA",
    "STO": "SANTO",

    # Regional spelling variant.
    "SUD": "SUR",
}


NUMBER_ALIASES = {
    "UNO": "1",
    "UNA": "1",
    "DOS": "2",
    "TRES": "3",
    "CUATRO": "4",
    "CINCO": "5",
    "SEIS": "6",
    "SIETE": "7",
    "OCHO": "8",
    "NUEVE": "9",
    "DIEZ": "10",
    "ONCE": "11",
    "DOCE": "12",

    # Roman numerals that occur in locality names.
    "I": "1",
    "II": "2",
    "III": "3",
    "IV": "4",
    "V": "5",
    "VI": "6",
    "VII": "7",
    "VIII": "8",
    "IX": "9",
    "X": "10",
    "XI": "11",
    "XII": "12",
    "XX": "20",
}


DEPARTMENT_MARKERS = {
    "DTO",
    "DPTO",
    "DEPTO",
    "DEPARTAMENTO",
}


SKELETON_STOPWORDS = {
    "DE",
    "DEL",
    "LA",
    "LAS",
    "LOS",
    "EL",
}


GENERIC_PLACE_TOKENS = {
    "BARRIO",
    "COLONIA",
    "ESTACION",
    "LOTE",
    "LOTEO",
    "MINA",
    "PARAJE",
    "PUEBLO",
    "PUERTO",
    "VILLA",
    "AERODROMO",
    "INGENIO",
}


def strip_accents(
    value: str,
) -> str:
    value = unicodedata.normalize(
        "NFD",
        value,
    )

    return "".join(
        char
        for char in value
        if unicodedata.category(char) != "Mn"
    )


def normalize_text(
    value: str,
) -> str:
    value = html.unescape(value)

    value = value.upper().strip()

    value = value.replace(
        "’",
        "'",
    )

    value = value.replace(
        "`",
        "'",
    )

    value = strip_accents(value)

    value = re.sub(
        r"\([^)]*\)",
        " ",
        value,
    )

    value = re.sub(
        r"[^A-Z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_province(
    value: str,
) -> str:
    normalized = normalize_text(
        value
    )

    return PROVINCE_ALIASES.get(
        normalized,
        normalized,
    )


def normalize_department(
    value: str,
) -> str:
    return normalize_text(
        value
    )


def expand_token(
    token: str,
) -> str:
    token = TOKEN_ALIASES.get(
        token,
        token,
    )

    token = NUMBER_ALIASES.get(
        token,
        token,
    )

    return token


def expand_tokens(
    tokens: list[str],
) -> list[str]:
    return [
        expand_token(
            token
        )
        for token in tokens
    ]


def normalize_name_loose(
    value: str,
) -> str:
    normalized = normalize_text(
        value
    )

    tokens = expand_tokens(
        normalized.split()
    )

    return " ".join(
        tokens
    )


def normalize_name_core(
    value: str,
) -> str:
    """
    Remove isolated single-letter initials while retaining
    numeric tokens.

    Examples:

        EMILIO V BUNGE
        -> EMILIO BUNGE

        COMANDANTE N OTAMENDI
        -> COMANDANTE OTAMENDI
    """

    tokens = (
        normalize_name_loose(
            value
        ).split()
    )

    tokens = [
        token
        for token in tokens
        if (
            len(token) > 1
            or token.isdigit()
        )
    ]

    return " ".join(
        tokens
    )


def normalize_name_compact(
    value: str,
) -> str:
    return (
        normalize_name_core(
            value
        )
        .replace(
            " ",
            "",
        )
    )


def normalize_name_skeleton(
    value: str,
) -> str:
    """
    Ignore common articles and prepositions.
    """

    tokens = [
        token
        for token in (
            normalize_name_core(
                value
            ).split()
        )
        if token
        not in SKELETON_STOPWORDS
    ]

    return " ".join(
        tokens
    )


def significant_tokens(
    value: str,
) -> tuple[str, ...]:
    """
    Remove only generic settlement words in addition to
    articles/prepositions.

    This gives forms such as:

        BARRIO PARQUE SICARDI
        -> PARQUE SICARDI

        VILLA PARQUE SICARDI
        -> PARQUE SICARDI

        COLONIA SAN MIGUEL ARCANGEL
        -> SAN MIGUEL ARCANGEL
    """

    tokens = []

    for token in (
        normalize_name_core(
            value
        ).split()
    ):
        if token in SKELETON_STOPWORDS:
            continue

        if token in GENERIC_PLACE_TOKENS:
            continue

        tokens.append(
            token
        )

    return tuple(
        tokens
    )


def normalize_name_significant(
    value: str,
) -> str:
    return " ".join(
        significant_tokens(
            value
        )
    )


def numeric_signature(
    value: str,
) -> tuple[str, ...]:
    tokens = expand_tokens(
        normalize_text(
            value
        ).split()
    )

    numbers = sorted(
        {
            token
            for token in tokens
            if token.isdigit()
        },
        key=lambda number: int(number),
    )

    return tuple(
        numbers
    )


def numeric_conflict(
    first: str,
    second: str,
) -> bool:
    first_numbers = (
        numeric_signature(
            first
        )
    )

    second_numbers = (
        numeric_signature(
            second
        )
    )

    if (
        not first_numbers
        and not second_numbers
    ):
        return False

    return (
        first_numbers
        != second_numbers
    )
    
def edit_distance(
    first: str,
    second: str,
) -> int:
    """
    Standard Levenshtein edit distance.

    Insertions, deletions, and substitutions each cost 1.
    """

    if first == second:
        return 0

    if not first:
        return len(second)

    if not second:
        return len(first)

    # Keep the working row small.
    if len(first) > len(second):
        first, second = (
            second,
            first,
        )

    previous = list(
        range(
            len(first) + 1
        )
    )

    for (
        second_index,
        second_char,
    ) in enumerate(
        second,
        start=1,
    ):
        current = [
            second_index
        ]

        for (
            first_index,
            first_char,
        ) in enumerate(
            first,
            start=1,
        ):
            insertion = (
                current[
                    first_index - 1
                ]
                + 1
            )

            deletion = (
                previous[
                    first_index
                ]
                + 1
            )

            substitution = (
                previous[
                    first_index - 1
                ]
                + (
                    0
                    if (
                        first_char
                        == second_char
                    )
                    else 1
                )
            )

            current.append(
                min(
                    insertion,
                    deletion,
                    substitution,
                )
            )

        previous = current

    return previous[-1]


def typo_comparison_form(
    value: str,
) -> str:
    """
    Compact normalized form used only for typo detection.

    Spaces, punctuation, accents, and common abbreviations
    have already been normalized before edit distance is
    calculated.
    """

    return normalize_name_compact(
        value
    )


def name_forms(
    value: str,
) -> dict[str, str]:
    return {
        "exact":
            normalize_text(
                value
            ),

        "loose":
            normalize_name_loose(
                value
            ),

        "core":
            normalize_name_core(
                value
            ),

        "compact":
            normalize_name_compact(
                value
            ),

        "skeleton":
            normalize_name_skeleton(
                value
            ),

        "significant":
            normalize_name_significant(
                value
            ),
    }


def extract_department_hint(
    locality_name: str,
) -> tuple[
    str,
    str | None,
]:
    """
    Extract only explicit department markers.

    Example:

        SAN PEDRO DTO CAPAYAN

        locality:
            SAN PEDRO

        department:
            CAPAYAN
    """

    normalized = normalize_text(
        locality_name
    )

    tokens = normalized.split()

    for (
        index,
        token,
    ) in enumerate(tokens):
        if (
            token
            not in DEPARTMENT_MARKERS
        ):
            continue

        if (
            index == 0
            or index
            == len(tokens) - 1
        ):
            continue

        locality_tokens = (
            tokens[:index]
        )

        department_tokens = (
            tokens[index + 1:]
        )

        locality = " ".join(
            locality_tokens
        ).strip()

        department = " ".join(
            department_tokens
        ).strip()

        if (
            locality
            and department
        ):
            return (
                locality,
                normalize_department(
                    department
                ),
            )

    return (
        locality_name,
        None,
    )


def decode_js_string(
    value: str,
) -> str:
    return json.loads(
        f'"{value}"'
    )


def read_area_code_js(
) -> list[dict[str, str]]:
    text = AREA_CODE_PATH.read_text(
        encoding="utf-8",
    )

    object_pattern = re.compile(
        r"\{(.*?)\}",
        re.DOTALL,
    )

    field_patterns = {
        "province": re.compile(
            r'provincia\s*:\s*"((?:\\.|[^"\\])*)"',
            re.DOTALL,
        ),

        "locality": re.compile(
            r'localidad\s*:\s*"((?:\\.|[^"\\])*)"',
            re.DOTALL,
        ),

        "code": re.compile(
            r'codigo\s*:\s*"((?:\\.|[^"\\])*)"',
            re.DOTALL,
        ),
    }

    rows: list[
        dict[str, str]
    ] = []

    for object_match in (
        object_pattern.finditer(
            text
        )
    ):
        body = (
            object_match.group(1)
        )

        values: dict[
            str,
            str,
        ] = {}

        for (
            field_name,
            pattern,
        ) in (
            field_patterns.items()
        ):
            match = pattern.search(
                body
            )

            if match is None:
                break

            values[
                field_name
            ] = (
                decode_js_string(
                    match.group(1)
                ).strip()
            )

        if len(values) != 3:
            continue

        rows.append(
            values
        )

    return rows


def read_official_localities(
) -> list[dict[str, Any]]:
    data = json.loads(
        LOCALITIES_PATH.read_text(
            encoding="utf-8",
        )
    )

    fields = [
        field["id"]
        for field
        in data["fields"]
    ]

    localities: list[
        dict[str, Any]
    ] = []

    for record in data[
        "records"
    ]:
        raw = dict(
            zip(
                fields,
                record,
            )
        )

        geometry_text = raw.get(
            "geojson"
        )

        if not geometry_text:
            continue

        geometry = json.loads(
            str(
                geometry_text
            )
        )

        if (
            geometry.get("type")
            != "Point"
        ):
            continue

        province = str(
            raw.get(
                "nom_prov"
            )
            or ""
        ).strip()

        department = str(
            raw.get(
                "nom_depto"
            )
            or ""
        ).strip()

        locality = str(
            raw.get(
                "nombre"
            )
            or ""
        ).strip()

        locality_type = str(
            raw.get(
                "tipo"
            )
            or ""
        ).strip()

        source = str(
            raw.get(
                "fuente"
            )
            or ""
        ).strip()

        forms = name_forms(
            locality
        )

        localities.append(
            {
                "id":
                    raw.get("_id"),

                "province":
                    province,

                "department":
                    department,

                "locality":
                    locality,

                "type":
                    locality_type,

                "source":
                    source,

                "geometry":
                    geometry,

                "province_normalized":
                    normalize_province(
                        province
                    ),

                "department_normalized":
                    normalize_department(
                        department
                    ),

                "name_exact":
                    forms["exact"],

                "name_loose":
                    forms["loose"],

                "name_core":
                    forms["core"],

                "name_compact":
                    forms["compact"],

                "name_skeleton":
                    forms[
                        "skeleton"
                    ],

                "name_significant":
                    forms[
                        "significant"
                    ],
            }
        )

    return localities


def build_indexes(
    localities: list[
        dict[str, Any]
    ],
) -> tuple[
    dict[
        str,
        dict[
            tuple[str, str],
            list[dict[str, Any]],
        ],
    ],
    dict[
        str,
        list[dict[str, Any]],
    ],
]:
    indexes: dict[
        str,
        dict[
            tuple[str, str],
            list[dict[str, Any]],
        ],
    ] = {}

    for form_name in (
        "exact",
        "loose",
        "core",
        "compact",
        "skeleton",
        "significant",
    ):
        indexes[
            form_name
        ] = defaultdict(
            list
        )

    province_index: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(
        list
    )

    for locality in localities:
        province = locality[
            "province_normalized"
        ]

        for form_name in indexes:
            form_value = locality[
                f"name_{form_name}"
            ]

            if not form_value:
                continue

            indexes[
                form_name
            ][
                (
                    province,
                    form_value,
                )
            ].append(
                locality
            )

        province_index[
            province
        ].append(
            locality
        )

    return (
        indexes,
        province_index,
    )


def choose_by_type_priority(
    candidates: list[
        dict[str, Any]
    ],
) -> dict[str, Any] | None:
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    best_priority = max(
        TYPE_PRIORITY.get(
            str(
                candidate["type"]
            ),
            0,
        )
        for candidate
        in candidates
    )

    best_candidates = [
        candidate
        for candidate
        in candidates
        if (
            TYPE_PRIORITY.get(
                str(
                    candidate["type"]
                ),
                0,
            )
            == best_priority
        )
    ]

    if len(
        best_candidates
    ) == 1:
        return (
            best_candidates[0]
        )

    return None


def filter_by_department_hint(
    candidates: list[
        dict[str, Any]
    ],
    department_hint: str | None,
) -> list[dict[str, Any]]:
    if not department_hint:
        return []

    return [
        candidate
        for candidate
        in candidates
        if (
            candidate[
                "department_normalized"
            ]
            == department_hint
        )
    ]


def choose_index_match(
    candidates: list[
        dict[str, Any]
    ],
    department_hint: str | None,
) -> tuple[
    dict[str, Any] | None,
    bool,
]:
    department_candidates = (
        filter_by_department_hint(
            candidates,
            department_hint,
        )
    )

    if department_candidates:
        choice = (
            choose_by_type_priority(
                department_candidates
            )
        )

        if choice is not None:
            return (
                choice,
                True,
            )

    return (
        choose_by_type_priority(
            candidates
        ),
        False,
    )


def sequence_ratio(
    first: str,
    second: str,
) -> float:
    if (
        not first
        or not second
    ):
        return 0.0

    return SequenceMatcher(
        None,
        first,
        second,
    ).ratio()


def token_similarity(
    first: str,
    second: str,
) -> float:
    first_tokens = set(
        first.split()
    )

    second_tokens = set(
        second.split()
    )

    if (
        not first_tokens
        or not second_tokens
    ):
        return 0.0

    intersection = (
        first_tokens
        & second_tokens
    )

    union = (
        first_tokens
        | second_tokens
    )

    return (
        len(intersection)
        / len(union)
    )


def calculate_fuzzy_score(
    query_forms: dict[
        str,
        str,
    ],
    candidate: dict[
        str,
        Any,
    ],
) -> float:
    ratios = [
        sequence_ratio(
            query_forms[
                "exact"
            ],
            candidate[
                "name_exact"
            ],
        ),

        sequence_ratio(
            query_forms[
                "loose"
            ],
            candidate[
                "name_loose"
            ],
        ),

        sequence_ratio(
            query_forms[
                "core"
            ],
            candidate[
                "name_core"
            ],
        ),

        sequence_ratio(
            query_forms[
                "compact"
            ],
            candidate[
                "name_compact"
            ],
        ),

        sequence_ratio(
            query_forms[
                "skeleton"
            ],
            candidate[
                "name_skeleton"
            ],
        ),

        sequence_ratio(
            query_forms[
                "significant"
            ],
            candidate[
                "name_significant"
            ],
        ),
    ]

    best_ratio = max(
        ratios
    )

    token_score = (
        token_similarity(
            query_forms[
                "significant"
            ],
            candidate[
                "name_significant"
            ],
        )
    )

    combined = (
        best_ratio * 0.90
        + token_score * 0.10
    )

    return min(
        combined,
        1.0,
    )


def score_province_candidates(
    locality_name: str,
    candidates: list[
        dict[str, Any]
    ],
) -> list[
    tuple[
        float,
        dict[str, Any],
    ]
]:
    query_forms = (
        name_forms(
            locality_name
        )
    )

    scored = [
        (
            calculate_fuzzy_score(
                query_forms,
                candidate,
            ),
            candidate,
        )
        for candidate
        in candidates
    ]

    scored.sort(
        key=lambda item: (
            item[0],
            TYPE_PRIORITY.get(
                str(
                    item[1][
                        "type"
                    ]
                ),
                0,
            ),
        ),
        reverse=True,
    )

    return scored


def should_auto_accept_fuzzy(
    scored: list[
        tuple[
            float,
            dict[str, Any],
        ]
    ],
) -> tuple[
    bool,
    float,
    float,
]:
    if not scored:
        return (
            False,
            0.0,
            0.0,
        )

    best_score = (
        scored[0][0]
    )

    second_score = (
        scored[1][0]
        if len(scored) > 1
        else 0.0
    )

    margin = (
        best_score
        - second_score
    )

    candidate = (
        scored[0][1]
    )

    candidate_type = str(
        candidate["type"]
    )

    if candidate_type in {
        "LOCALIDAD",
        "ENTIDAD",
    }:
        if (
            best_score >= 0.94
            and margin >= 0.05
        ):
            return (
                True,
                best_score,
                margin,
            )

        if (
            best_score >= 0.90
            and margin >= 0.12
        ):
            return (
                True,
                best_score,
                margin,
            )

        if (
            best_score >= 0.86
            and margin >= 0.20
        ):
            return (
                True,
                best_score,
                margin,
            )

    if (
        candidate_type
        == "SITIO EDIFICADO"
    ):
        if (
            best_score >= 0.96
            and margin >= 0.08
        ):
            return (
                True,
                best_score,
                margin,
            )

        if (
            best_score >= 0.92
            and margin >= 0.16
        ):
            return (
                True,
                best_score,
                margin,
            )

    return (
        False,
        best_score,
        margin,
    )


def candidate_summary(
    candidate: dict[str, Any],
    score: float | None = None,
) -> dict[str, Any]:
    summary: dict[
        str,
        Any,
    ] = {
        "id":
            candidate["id"],

        "province":
            candidate["province"],

        "department":
            candidate[
                "department"
            ],

        "locality":
            candidate[
                "locality"
            ],

        "type":
            candidate["type"],

        "source":
            candidate["source"],

        "geometry":
            candidate[
                "geometry"
            ],
    }

    if score is not None:
        summary["score"] = (
            round(
                score,
                4,
            )
        )

    return summary


def get_suggestions_from_scored(
    scored: list[
        tuple[
            float,
            dict[str, Any],
        ]
    ],
    limit: int = 5,
) -> list[
    dict[str, Any]
]:
    return [
        candidate_summary(
            candidate,
            score,
        )
        for (
            score,
            candidate,
        ) in scored[:limit]
    ]


def build_feature(
    area_row: dict[
        str,
        str,
    ],
    locality: dict[
        str,
        Any,
    ],
    match_method: str,
    match_score: float | None = None,
    match_margin: float | None = None,
    department_hint: str | None = None,
    geographic_distance_km: float | None = None,
    geographic_next_distance_km: float | None = None,
) -> dict[str, Any]:
    properties: dict[
        str,
        Any,
    ] = {
        "area_code":
            area_row["code"],

        "area_code_length":
            len(
                area_row[
                    "code"
                ]
            ),

        "locality":
            area_row[
                "locality"
            ],

        "province":
            area_row[
                "province"
            ],

        "official_locality":
            locality[
                "locality"
            ],

        "official_province":
            locality[
                "province"
            ],

        "department":
            locality[
                "department"
            ],

        "official_id":
            locality[
                "id"
            ],

        "locality_type":
            locality[
                "type"
            ],

        "locality_source":
            locality[
                "source"
            ],

        "match_method":
            match_method,
    }

    if department_hint:
        properties[
            "source_department_hint"
        ] = department_hint

    if match_score is not None:
        properties[
            "match_score"
        ] = round(
            match_score,
            4,
        )

    if match_margin is not None:
        properties[
            "match_margin"
        ] = round(
            match_margin,
            4,
        )

    if (
        geographic_distance_km
        is not None
    ):
        properties[
            "geographic_distance_km"
        ] = round(
            geographic_distance_km,
            2,
        )

    if (
        geographic_next_distance_km
        is not None
    ):
        properties[
            "geographic_next_distance_km"
        ] = round(
            geographic_next_distance_km,
            2,
        )

    return {
        "type":
            "Feature",

        "properties":
            properties,

        "geometry":
            locality[
                "geometry"
            ],
    }


def method_name(
    form_name: str,
    candidates: list[
        dict[str, Any]
    ],
    used_department: bool,
) -> str:
    if used_department:
        return (
            f"department_{form_name}"
        )

    if len(candidates) == 1:
        return (
            f"{form_name}_unique"
        )

    return (
        f"{form_name}_type_preference"
    )


def prepare_source_row(
    area_row: dict[
        str,
        str,
    ],
) -> dict[str, Any]:
    (
        match_locality,
        department_hint,
    ) = extract_department_hint(
        area_row[
            "locality"
        ]
    )

    return {
        **area_row,

        "_match_locality":
            match_locality,

        "_department_hint":
            department_hint,

        "_forms":
            name_forms(
                match_locality
            ),

        "_province_normalized":
            normalize_province(
                area_row[
                    "province"
                ]
            ),
    }


def is_significant_containment(
    first: str,
    second: str,
) -> bool:
    """
    Conservative containment relationship.

    Examples accepted:

        AMEGHINO
        FLORENTINO AMEGHINO

        JUAN ALBERDI
        JUAN BAUTISTA ALBERDI

        ESCOBAR
        BELEN ESCOBAR

    Exact significant forms are handled before this stage.
    """

    if numeric_conflict(
        first,
        second,
    ):
        return False

    first_tokens = set(
        significant_tokens(
            first
        )
    )

    second_tokens = set(
        significant_tokens(
            second
        )
    )

    if (
        not first_tokens
        or not second_tokens
    ):
        return False

    if (
        first_tokens
        == second_tokens
    ):
        return True

    shorter = (
        first_tokens
        if len(first_tokens)
        <= len(second_tokens)
        else second_tokens
    )

    longer = (
        second_tokens
        if shorter
        is first_tokens
        else first_tokens
    )

    if not shorter.issubset(
        longer
    ):
        return False

    # Multi-token containment is reasonably strong.
    if len(shorter) >= 2:
        return True

    # A single-token containment match is only allowed for
    # a fairly distinctive word, and only when the expanded
    # candidate contains at most one additional significant
    # token.
    only_token = next(
        iter(shorter)
    )

    if (
        len(only_token) >= 6
        and len(longer) <= 2
    ):
        return True

    return False


def find_containment_candidates(
    locality_name: str,
    candidates: list[
        dict[str, Any]
    ],
    department_hint: str | None,
) -> list[
    dict[str, Any]
]:
    matches = [
        candidate
        for candidate
        in candidates
        if is_significant_containment(
            locality_name,
            candidate[
                "locality"
            ],
        )
    ]

    if department_hint:
        department_matches = (
            filter_by_department_hint(
                matches,
                department_hint,
            )
        )

        if department_matches:
            return (
                department_matches
            )

    return matches

def find_typo_match(
    locality_name: str,
    candidates: list[
        dict[str, Any]
    ],
) -> dict[str, Any] | None:
    """
    Accept only a very clear one-character spelling error.

    Safeguards:
      - same province is already guaranteed by the caller
      - numeric conflicts are forbidden
      - normalized name must contain at least 6 characters
      - best candidate must be exactly 1 edit away
      - no second candidate may also be 1 edit away
      - next-best candidate must be at least 3 edits away

    This is deliberately much stricter than fuzzy matching.
    """

    source_form = (
        typo_comparison_form(
            locality_name
        )
    )

    if len(source_form) < 6:
        return None

    scored: list[
        tuple[
            int,
            float,
            dict[str, Any],
        ]
    ] = []

    source_forms = name_forms(
        locality_name
    )

    for candidate in candidates:
        if numeric_conflict(
            locality_name,
            candidate[
                "locality"
            ],
        ):
            continue

        candidate_form = (
            typo_comparison_form(
                candidate[
                    "locality"
                ]
            )
        )

        if len(candidate_form) < 6:
            continue

        # A single edit cannot bridge a large length gap,
        # so avoid unnecessary comparisons.
        if (
            abs(
                len(source_form)
                - len(candidate_form)
            )
            > 1
        ):
            continue

        distance = edit_distance(
            source_form,
            candidate_form,
        )

        if distance > 3:
            continue

        fuzzy_score = (
            calculate_fuzzy_score(
                source_forms,
                candidate,
            )
        )

        scored.append(
            (
                distance,
                fuzzy_score,
                candidate,
            )
        )

    if not scored:
        return None

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1],
            -TYPE_PRIORITY.get(
                str(
                    item[2]["type"]
                ),
                0,
            ),
        )
    )

    best_distance = (
        scored[0][0]
    )

    if best_distance != 1:
        return None

    # If two places are both one edit away, we cannot
    # determine which typo correction was intended.
    same_best = [
        item
        for item in scored
        if item[0]
        == best_distance
    ]

    if len(same_best) != 1:
        return None

    next_distance = (
        scored[1][0]
        if len(scored) > 1
        else 999
    )

    if next_distance < 3:
        return None

    return {
        "candidate":
            scored[0][2],

        "distance":
            best_distance,

        "next_distance":
            (
                next_distance
                if next_distance != 999
                else None
            ),

        "score":
            scored[0][1],
    }

def make_unresolved_record(
    row: dict[str, Any],
    reason: str,
    scored: list[
        tuple[
            float,
            dict[str, Any],
        ]
    ],
    candidates: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    best_score = (
        scored[0][0]
        if scored
        else 0.0
    )

    second_score = (
        scored[1][0]
        if len(scored) > 1
        else 0.0
    )

    margin = (
        best_score
        - second_score
    )

    forms = row[
        "_forms"
    ]

    return {
        "province":
            row["province"],

        "locality":
            row["locality"],

        "code":
            row["code"],

        "reason":
            reason,

        "normalized_province":
            row[
                "_province_normalized"
            ],

        "match_locality":
            row[
                "_match_locality"
            ],

        "department_hint":
            row[
                "_department_hint"
            ],

        "normalized_locality":
            forms["exact"],

        "loose_locality":
            forms["loose"],

        "core_locality":
            forms["core"],

        "compact_locality":
            forms[
                "compact"
            ],

        "skeleton_locality":
            forms[
                "skeleton"
            ],

        "significant_locality":
            forms[
                "significant"
            ],

        "numeric_signature":
            list(
                numeric_signature(
                    row[
                        "_match_locality"
                    ]
                )
            ),

        "best_fuzzy_score":
            round(
                best_score,
                4,
            ),

        "best_fuzzy_margin":
            round(
                margin,
                4,
            ),

        "candidates":
            [
                candidate_summary(
                    candidate
                )
                for candidate
                in candidates
            ],

        "suggestions":
            get_suggestions_from_scored(
                scored
            ),
    }


def process_text_matches(
    area_rows: list[
        dict[str, str]
    ],
    indexes: dict[
        str,
        dict[
            tuple[str, str],
            list[dict[str, Any]],
        ],
    ],
    province_index: dict[
        str,
        list[dict[str, Any]],
    ],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    Counter,
]:
    features: list[
        dict[str, Any]
    ] = []

    unresolved: list[
        dict[str, Any]
    ] = []

    fuzzy_review: list[
        dict[str, Any]
    ] = []

    match_methods: Counter = (
        Counter()
    )

    form_order = (
        "exact",
        "loose",
        "core",
        "compact",
        "skeleton",
        "significant",
    )

    for raw_row in area_rows:
        row = prepare_source_row(
            raw_row
        )

        code = row["code"]

        province = row[
            "_province_normalized"
        ]

        forms = row[
            "_forms"
        ]

        department_hint = row[
            "_department_hint"
        ]

        forced_unresolved_key = (
            province,
            forms["exact"],
            code,
        )

        if (
            forced_unresolved_key
            in FORCED_UNRESOLVED
        ):
            unresolved.append(
                {
                    "province":
                        raw_row[
                            "province"
                        ],

                    "locality":
                        raw_row[
                            "locality"
                        ],

                    "code":
                        code,

                    "reason":
                        "forced_unresolved",

                    "normalized_province":
                        province,

                    "match_locality":
                        row[
                            "_match_locality"
                        ],

                    "department_hint":
                        department_hint,

                    "normalized_locality":
                        forms[
                            "exact"
                        ],

                    "suggestions":
                        [],
                }
            )

            match_methods[
                "forced_unresolved"
            ] += 1

            continue

        manual_override_id = (
            MANUAL_OVERRIDES.get(
                (
                    province,
                    normalize_text(
                        raw_row[
                            "locality"
                        ]
                    ),
                )
            )
        )

        if (
            manual_override_id
            is not None
        ):
            override_candidates = [
                candidate
                for candidate
                in province_index.get(
                    province,
                    [],
                )
                if (
                    candidate["id"]
                    == manual_override_id
                )
            ]

            if (
                len(
                    override_candidates
                )
                != 1
            ):
                raise ValueError(
                    "Manual override did "
                    "not resolve uniquely: "
                    f"{province} / "
                    f"{raw_row['locality']}"
                )

            features.append(
                build_feature(
                    raw_row,
                    override_candidates[
                        0
                    ],
                    "manual_override",
                    department_hint=(
                        department_hint
                    ),
                )
            )

            match_methods[
                "manual_override"
            ] += 1

            continue

        if (
            code == "11"
            and "AMBA"
            in normalize_text(
                raw_row[
                    "locality"
                ]
            )
        ):
            unresolved.append(
                {
                    "province":
                        raw_row[
                            "province"
                        ],

                    "locality":
                        raw_row[
                            "locality"
                        ],

                    "code":
                        code,

                    "reason":
                        "special_amba_aggregate",

                    "normalized_province":
                        province,

                    "match_locality":
                        row[
                            "_match_locality"
                        ],

                    "department_hint":
                        department_hint,

                    "normalized_locality":
                        forms[
                            "exact"
                        ],

                    "suggestions":
                        [],
                }
            )

            match_methods[
                "special_amba_aggregate"
            ] += 1

            continue

        matched = False

        form_candidates: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        # -------------------------------------------------
        # Deterministic equality forms
        # -------------------------------------------------

        for form_name in (
            form_order
        ):
            form_value = forms[
                form_name
            ]

            candidates = (
                indexes[
                    form_name
                ].get(
                    (
                        province,
                        form_value,
                    ),
                    [],
                )
                if form_value
                else []
            )

            form_candidates[
                form_name
            ] = candidates

            (
                choice,
                used_department,
            ) = choose_index_match(
                candidates,
                department_hint,
            )

            if choice is None:
                continue

            method = method_name(
                form_name,
                candidates,
                used_department,
            )

            features.append(
                build_feature(
                    raw_row,
                    choice,
                    method,
                    department_hint=(
                        department_hint
                    ),
                )
            )

            match_methods[
                method
            ] += 1

            matched = True

            break

        if matched:
            continue

        province_candidates = (
            province_index.get(
                province,
                [],
            )
        )

        # -------------------------------------------------
        # Significant-token containment
        # -------------------------------------------------

        containment_candidates = (
            find_containment_candidates(
                row[
                    "_match_locality"
                ],
                province_candidates,
                department_hint,
            )
        )

        if (
            len(
                containment_candidates
            )
            == 1
        ):
            candidate = (
                containment_candidates[
                    0
                ]
            )

            method = (
                "department_containment"
                if (
                    department_hint
                    and candidate[
                        "department_normalized"
                    ]
                    == department_hint
                )
                else
                "containment_unique"
            )

            score = (
                calculate_fuzzy_score(
                    forms,
                    candidate,
                )
            )

            features.append(
                build_feature(
                    raw_row,
                    candidate,
                    method,
                    match_score=score,
                    department_hint=(
                        department_hint
                    ),
                )
            )

            fuzzy_review.append(
                {
                    "method":
                        method,

                    "code":
                        code,

                    "source_province":
                        raw_row[
                            "province"
                        ],

                    "source_locality":
                        raw_row[
                            "locality"
                        ],

                    "department_hint":
                        department_hint,

                    "official_id":
                        candidate[
                            "id"
                        ],

                    "official_department":
                        candidate[
                            "department"
                        ],

                    "official_locality":
                        candidate[
                            "locality"
                        ],

                    "official_type":
                        candidate[
                            "type"
                        ],

                    "score":
                        round(
                            score,
                            4,
                        ),

                    "margin":
                        None,
                }
            )

            match_methods[
                method
            ] += 1

            continue
        
        # -------------------------------------------------
        # Conservative one-character typo correction
        # -------------------------------------------------

        typo_match = (
            find_typo_match(
                row[
                    "_match_locality"
                ],
                province_candidates,
            )
        )

        if typo_match is not None:
            candidate = (
                typo_match[
                    "candidate"
                ]
            )

            score = float(
                typo_match[
                    "score"
                ]
            )

            next_distance = (
                typo_match[
                    "next_distance"
                ]
            )

            features.append(
                build_feature(
                    raw_row,
                    candidate,
                    "edit_distance_auto",
                    match_score=score,
                    department_hint=(
                        department_hint
                    ),
                )
            )

            fuzzy_review.append(
                {
                    "method":
                        "edit_distance_auto",

                    "code":
                        code,

                    "source_province":
                        raw_row[
                            "province"
                        ],

                    "source_locality":
                        raw_row[
                            "locality"
                        ],

                    "department_hint":
                        department_hint,

                    "official_id":
                        candidate[
                            "id"
                        ],

                    "official_department":
                        candidate[
                            "department"
                        ],

                    "official_locality":
                        candidate[
                            "locality"
                        ],

                    "official_type":
                        candidate[
                            "type"
                        ],

                    "score":
                        round(
                            score,
                            4,
                        ),

                    "margin":
                        None,

                    "edit_distance":
                        typo_match[
                            "distance"
                        ],

                    "next_edit_distance":
                        next_distance,
                }
            )

            match_methods[
                "edit_distance_auto"
            ] += 1

            continue

        # -------------------------------------------------
        # Conservative text fuzzy
        # -------------------------------------------------

        scored = (
            score_province_candidates(
                row[
                    "_match_locality"
                ],
                province_candidates,
            )
        )

        # Never allow an otherwise high fuzzy score to
        # bridge conflicting numeric locality names.
        scored = [
            (
                score,
                candidate,
            )
            for (
                score,
                candidate,
            ) in scored
            if not numeric_conflict(
                row[
                    "_match_locality"
                ],
                candidate[
                    "locality"
                ],
            )
        ]

        if department_hint:
            department_scored = [
                item
                for item
                in scored
                if (
                    item[1][
                        "department_normalized"
                    ]
                    == department_hint
                )
            ]

            if department_scored:
                (
                    accept,
                    score,
                    margin,
                ) = (
                    should_auto_accept_fuzzy(
                        department_scored
                    )
                )

                if accept:
                    candidate = (
                        department_scored[
                            0
                        ][1]
                    )

                    features.append(
                        build_feature(
                            raw_row,
                            candidate,
                            "department_fuzzy",
                            score,
                            margin,
                            department_hint,
                        )
                    )

                    fuzzy_review.append(
                        {
                            "method":
                                "department_fuzzy",

                            "code":
                                code,

                            "source_province":
                                raw_row[
                                    "province"
                                ],

                            "source_locality":
                                raw_row[
                                    "locality"
                                ],

                            "department_hint":
                                department_hint,

                            "official_id":
                                candidate[
                                    "id"
                                ],

                            "official_department":
                                candidate[
                                    "department"
                                ],

                            "official_locality":
                                candidate[
                                    "locality"
                                ],

                            "official_type":
                                candidate[
                                    "type"
                                ],

                            "score":
                                round(
                                    score,
                                    4,
                                ),

                            "margin":
                                round(
                                    margin,
                                    4,
                                ),
                        }
                    )

                    match_methods[
                        "department_fuzzy"
                    ] += 1

                    continue

        (
            auto_accept,
            best_score,
            margin,
        ) = (
            should_auto_accept_fuzzy(
                scored
            )
        )

        if (
            auto_accept
            and scored
        ):
            candidate = (
                scored[0][1]
            )

            features.append(
                build_feature(
                    raw_row,
                    candidate,
                    "fuzzy_auto",
                    best_score,
                    margin,
                    department_hint,
                )
            )

            fuzzy_review.append(
                {
                    "method":
                        "fuzzy_auto",

                    "code":
                        code,

                    "source_province":
                        raw_row[
                            "province"
                        ],

                    "source_locality":
                        raw_row[
                            "locality"
                        ],

                    "department_hint":
                        department_hint,

                    "official_id":
                        candidate[
                            "id"
                        ],

                    "official_department":
                        candidate[
                            "department"
                        ],

                    "official_locality":
                        candidate[
                            "locality"
                        ],

                    "official_type":
                        candidate[
                            "type"
                        ],

                    "score":
                        round(
                            best_score,
                            4,
                        ),

                    "margin":
                        round(
                            margin,
                            4,
                        ),

                    "next_best":
                        (
                            candidate_summary(
                                scored[
                                    1
                                ][1],
                                scored[
                                    1
                                ][0],
                            )
                            if len(
                                scored
                            ) > 1
                            else None
                        ),
                }
            )

            match_methods[
                "fuzzy_auto"
            ] += 1

            continue

        reason = (
            "no_confident_match"
        )

        unresolved_candidates: list[
            dict[str, Any]
        ] = []

        for form_name in form_order:
            candidates = (
                form_candidates[
                    form_name
                ]
            )

            if candidates:
                reason = (
                    f"ambiguous_"
                    f"{form_name}_match"
                )

                unresolved_candidates = (
                    candidates
                )

                break

        if (
            reason
            == "no_confident_match"
            and len(
                containment_candidates
            ) > 1
        ):
            reason = (
                "ambiguous_containment_match"
            )

            unresolved_candidates = (
                containment_candidates
            )

        unresolved.append(
            make_unresolved_record(
                row,
                reason,
                scored,
                unresolved_candidates,
            )
        )

        match_methods[
            reason
        ] += 1

    return (
        features,
        unresolved,
        fuzzy_review,
        match_methods,
    )


def haversine_km(
    first: list[float],
    second: list[float],
) -> float:
    lon1, lat1 = first
    lon2, lat2 = second

    radius = 6371.0088

    phi1 = math.radians(
        lat1
    )

    phi2 = math.radians(
        lat2
    )

    delta_phi = math.radians(
        lat2 - lat1
    )

    delta_lambda = (
        math.radians(
            lon2 - lon1
        )
    )

    value = (
        math.sin(
            delta_phi / 2
        ) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(
            delta_lambda / 2
        ) ** 2
    )

    return (
        2
        * radius
        * math.asin(
            math.sqrt(
                value
            )
        )
    )


def build_code_anchor_index(
    features: list[
        dict[str, Any]
    ],
) -> dict[
    tuple[str, str],
    list[list[float]],
]:
    anchors: dict[
        tuple[str, str],
        list[list[float]],
    ] = defaultdict(
        list
    )

    for feature in features:
        properties = feature[
            "properties"
        ]

        code = str(
            properties[
                "area_code"
            ]
        )

        province = (
            normalize_province(
                str(
                    properties[
                        "province"
                    ]
                )
            )
        )

        coordinates = (
            feature[
                "geometry"
            ][
                "coordinates"
            ]
        )

        anchors[
            (
                province,
                code,
            )
        ].append(
            coordinates
        )

    return anchors


def nearest_anchor_distance(
    candidate: dict[
        str,
        Any,
    ],
    anchors: list[
        list[float]
    ],
) -> float | None:
    if not anchors:
        return None

    coordinate = (
        candidate[
            "geometry"
        ][
            "coordinates"
        ]
    )

    return min(
        haversine_km(
            coordinate,
            anchor,
        )
        for anchor
        in anchors
    )


def geographic_text_floor(
    source_name: str,
    candidate: dict[str, Any],
) -> float:
    strong_containment = (
        is_significant_containment(
            source_name,
            candidate[
                "locality"
            ],
        )
    )

    if strong_containment:
        return 0.80

    if (
        candidate[
            "type"
        ]
        == "SITIO EDIFICADO"
    ):
        return 0.86

    return 0.84


def choose_geographic_match(
    unresolved_row: dict[
        str,
        Any,
    ],
    province_candidates: list[
        dict[str, Any]
    ],
    anchors: list[
        list[float]
    ],
) -> dict[str, Any] | None:
    if not anchors:
        return None

    source_name = str(
        unresolved_row.get(
            "match_locality"
        )
        or unresolved_row[
            "locality"
        ]
    )

    department_hint = (
        unresolved_row.get(
            "department_hint"
        )
    )

    scored = (
        score_province_candidates(
            source_name,
            province_candidates,
        )
    )

    # Numeric differences are a hard rejection.
    scored = [
        (
            score,
            candidate,
        )
        for (
            score,
            candidate,
        ) in scored
        if not numeric_conflict(
            source_name,
            candidate[
                "locality"
            ],
        )
    ]

    if not scored:
        return None

    best_text_score = (
        scored[0][0]
    )

    plausible: list[
        dict[str, Any]
    ] = []

    for (
        score,
        candidate,
    ) in scored:
        if department_hint:
            if (
                candidate[
                    "department_normalized"
                ]
                != department_hint
            ):
                continue

        floor = (
            geographic_text_floor(
                source_name,
                candidate,
            )
        )

        if score < floor:
            continue

        # Geography may resolve a tie or validate a name,
        # but cannot rescue a candidate whose name is much
        # worse than the best text candidate.
        if (
            score
            < best_text_score
            - 0.04
        ):
            continue

        distance = (
            nearest_anchor_distance(
                candidate,
                anchors,
            )
        )

        if distance is None:
            continue

        if distance > 30.0:
            continue

        plausible.append(
            {
                "score":
                    score,

                "candidate":
                    candidate,

                "distance":
                    distance,

                "strong_containment":
                    is_significant_containment(
                        source_name,
                        candidate[
                            "locality"
                        ],
                    ),
            }
        )

    if not plausible:
        return None

    # -----------------------------------------------------
    # Only one plausible candidate
    # -----------------------------------------------------

    if len(plausible) == 1:
        item = plausible[0]

        score = float(
            item["score"]
        )

        distance = float(
            item["distance"]
        )

        strong_containment = bool(
            item[
                "strong_containment"
            ]
        )

        if strong_containment:
            if (
                score >= 0.80
                and distance <= 20.0
            ):
                return {
                    **item,
                    "next_distance":
                        None,
                }

            return None

        if (
            score >= 0.92
            and distance <= 30.0
        ):
            return {
                **item,
                "next_distance":
                    None,
            }

        if (
            score >= 0.88
            and distance <= 20.0
        ):
            return {
                **item,
                "next_distance":
                    None,
            }

        if (
            score >= 0.84
            and distance <= 10.0
        ):
            return {
                **item,
                "next_distance":
                    None,
            }

        return None

    # -----------------------------------------------------
    # Multiple plausible candidates
    # -----------------------------------------------------

    plausible.sort(
        key=lambda item: (
            item[
                "distance"
            ],
            -item[
                "score"
            ],
        )
    )

    best = plausible[0]
    second = plausible[1]

    best_distance = float(
        best["distance"]
    )

    second_distance = float(
        second["distance"]
    )

    distance_gap = (
        second_distance
        - best_distance
    )

    distance_ratio = (
        second_distance
        / max(
            best_distance,
            0.5,
        )
    )

    # Exact duplicate names require strong geographic
    # separation before we pick one.
    if (
        best["score"]
        >= 0.98
    ):
        if (
            best_distance <= 20.0
            and distance_gap >= 10.0
            and distance_ratio >= 2.0
        ):
            return {
                **best,

                "next_distance":
                    second_distance,
            }

        return None

    # Fuzzy alternatives need similarly convincing
    # geographic separation.
    if (
        best_distance <= 15.0
        and distance_gap >= 8.0
        and distance_ratio >= 2.0
    ):
        return {
            **best,

            "next_distance":
                second_distance,
        }

    return None


def process_geographic_matches(
    features: list[
        dict[str, Any]
    ],
    unresolved: list[
        dict[str, Any]
    ],
    province_index: dict[
        str,
        list[dict[str, Any]],
    ],
    match_methods: Counter,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Second pass.

    Anchors are built once from pass-one matches.

    Geographic matches accepted here do not become anchors
    during this same run. This prevents cascading guesses.
    """

    anchor_index = (
        build_code_anchor_index(
            features
        )
    )

    remaining: list[
        dict[str, Any]
    ] = []

    geographic_review: list[
        dict[str, Any]
    ] = []

    new_features: list[
        dict[str, Any]
    ] = []

    for row in unresolved:
        if row["reason"] in {
            "special_amba_aggregate",
            "forced_unresolved",
        }:
            remaining.append(
                row
            )

            continue

        province = str(
            row[
                "normalized_province"
            ]
        )

        code = str(
            row[
                "code"
            ]
        )

        anchors = (
            anchor_index.get(
                (
                    province,
                    code,
                ),
                [],
            )
        )

        if not anchors:
            remaining.append(
                row
            )

            continue

        choice = (
            choose_geographic_match(
                row,
                province_index.get(
                    province,
                    [],
                ),
                anchors,
            )
        )

        if choice is None:
            remaining.append(
                row
            )

            continue

        candidate = (
            choice[
                "candidate"
            ]
        )

        score = float(
            choice[
                "score"
            ]
        )

        distance = float(
            choice[
                "distance"
            ]
        )

        next_distance = (
            choice.get(
                "next_distance"
            )
        )

        ambiguous_exact = (
            row[
                "reason"
            ]
            == "ambiguous_exact_match"
        )

        method = (
            "geographic_ambiguous_exact"
            if ambiguous_exact
            else
            "geographic_fuzzy"
        )

        raw_row = {
            "province":
                row[
                    "province"
                ],

            "locality":
                row[
                    "locality"
                ],

            "code":
                row[
                    "code"
                ],
        }

        new_features.append(
            build_feature(
                raw_row,
                candidate,
                method,
                match_score=score,
                department_hint=(
                    row.get(
                        "department_hint"
                    )
                ),
                geographic_distance_km=(
                    distance
                ),
                geographic_next_distance_km=(
                    next_distance
                ),
            )
        )

        previous_reason = (
            row["reason"]
        )

        match_methods[
            previous_reason
        ] -= 1

        if (
            match_methods[
                previous_reason
            ]
            <= 0
        ):
            del match_methods[
                previous_reason
            ]

        match_methods[
            method
        ] += 1

        geographic_review.append(
            {
                "method":
                    method,

                "code":
                    code,

                "source_province":
                    row[
                        "province"
                    ],

                "source_locality":
                    row[
                        "locality"
                    ],

                "department_hint":
                    row.get(
                        "department_hint"
                    ),

                "previous_reason":
                    previous_reason,

                "official_id":
                    candidate[
                        "id"
                    ],

                "official_department":
                    candidate[
                        "department"
                    ],

                "official_locality":
                    candidate[
                        "locality"
                    ],

                "official_type":
                    candidate[
                        "type"
                    ],

                "text_score":
                    round(
                        score,
                        4,
                    ),

                "strong_containment":
                    bool(
                        choice[
                            "strong_containment"
                        ]
                    ),

                "distance_km":
                    round(
                        distance,
                        2,
                    ),

                "next_distance_km":
                    (
                        round(
                            float(
                                next_distance
                            ),
                            2,
                        )
                        if (
                            next_distance
                            is not None
                        )
                        else None
                    ),
            }
        )

    features.extend(
        new_features
    )

    return (
        features,
        remaining,
        geographic_review,
    )
    
def add_area_code_11_seeds(
    features: list[
        dict[str, Any]
    ],
    official_localities: list[
        dict[str, Any]
    ],
) -> tuple[int, int]:
    """
    Add synthetic code-11 seeds throughout CABA and the
    core Greater Buenos Aires partidos.

    A synthetic AMBA seed is skipped whenever its official
    coordinate is already occupied by a real matched source
    seed. Real telephone data always takes precedence over
    our synthetic approximation.
    """

    coordinate_rounding = 8

    occupied_coordinates: set[
        tuple[float, float]
    ] = set()

    for feature in features:
        geometry = feature.get(
            "geometry",
            {}
        )

        if (
            geometry.get("type")
            != "Point"
        ):
            continue

        coordinates = geometry.get(
            "coordinates"
        )

        if (
            not coordinates
            or len(coordinates) < 2
        ):
            continue

        occupied_coordinates.add(
            (
                round(
                    float(
                        coordinates[0]
                    ),
                    coordinate_rounding,
                ),
                round(
                    float(
                        coordinates[1]
                    ),
                    coordinate_rounding,
                ),
            )
        )

    added = 0
    skipped_existing = 0

    for locality in official_localities:
        province = locality[
            "province_normalized"
        ]

        department = locality[
            "department_normalized"
        ]

        locality_type = locality[
            "type"
        ]

        is_caba = (
            province
            == "CIUDAD DE BUENOS AIRES"
        )

        is_core_gba = (
            province
            == "BUENOS AIRES"
            and department
            in AREA_CODE_11_DEPARTMENTS
        )

        if not (
            is_caba
            or is_core_gba
        ):
            continue

        if locality_type not in {
            "LOCALIDAD",
            "ENTIDAD",
        }:
            continue

        geometry = locality[
            "geometry"
        ]

        coordinates = geometry.get(
            "coordinates"
        )

        if (
            not coordinates
            or len(coordinates) < 2
        ):
            continue

        coordinate_key = (
            round(
                float(
                    coordinates[0]
                ),
                coordinate_rounding,
            ),
            round(
                float(
                    coordinates[1]
                ),
                coordinate_rounding,
            ),
        )

        if (
            coordinate_key
            in occupied_coordinates
        ):
            skipped_existing += 1
            continue

        features.append(
            {
                "type":
                    "Feature",

                "properties":
                    {
                        "area_code":
                            "11",

                        "area_code_length":
                            2,

                        "locality":
                            locality[
                                "locality"
                            ],

                        "province":
                            locality[
                                "province"
                            ],

                        "official_locality":
                            locality[
                                "locality"
                            ],

                        "official_province":
                            locality[
                                "province"
                            ],

                        "department":
                            locality[
                                "department"
                            ],

                        "official_id":
                            locality[
                                "id"
                            ],

                        "locality_type":
                            locality[
                                "type"
                            ],

                        "locality_source":
                            locality[
                                "source"
                            ],

                        "match_method":
                            "special_amba_seed",
                    },

                "geometry":
                    geometry,
            }
        )

        occupied_coordinates.add(
            coordinate_key
        )

        added += 1

    return (
        added,
        skipped_existing,
    )

def validate_output(
    area_rows: list[
        dict[str, str]
    ],
    features: list[
        dict[str, Any]
    ],
    unresolved: list[
        dict[str, Any]
    ],
) -> None:
    if (
        len(features)
        + len(unresolved)
        != len(area_rows)
    ):
        raise ValueError(
            "Processed row count does "
            "not match source row count."
        )

    source_codes = {
        str(
            row["code"]
        )
        for row
        in area_rows
    }

    output_codes = {
        str(
            feature[
                "properties"
            ][
                "area_code"
            ]
        )
        for feature
        in features
    }

    output_codes.update(
        str(
            row["code"]
        )
        for row
        in unresolved
    )

    if (
        source_codes
        != output_codes
    ):
        raise ValueError(
            "Output does not preserve "
            "all source area codes."
        )


def write_outputs(
    features: list[
        dict[str, Any]
    ],
    unresolved: list[
        dict[str, Any]
    ],
    fuzzy_review: list[
        dict[str, Any]
    ],
    geographic_review: list[
        dict[str, Any]
    ],
) -> None:
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_GEOJSON_PATH.write_text(
        json.dumps(
            {
                "type":
                    "FeatureCollection",

                "features":
                    features,
            },
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        ),
        encoding="utf-8",
    )

    UNRESOLVED_PATH.write_text(
        json.dumps(
            unresolved,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    fuzzy_sorted = sorted(
        fuzzy_review,
        key=lambda row: (
            row.get(
                "score",
                0,
            ),
            (
                row.get(
                    "margin"
                )
                if row.get(
                    "margin"
                )
                is not None
                else 999
            ),
        ),
    )

    FUZZY_REVIEW_PATH.write_text(
        json.dumps(
            fuzzy_sorted,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    geographic_sorted = sorted(
        geographic_review,
        key=lambda row: (
            row[
                "text_score"
            ],
            -row[
                "distance_km"
            ],
        ),
    )

    GEOGRAPHIC_REVIEW_PATH.write_text(
        json.dumps(
            geographic_sorted,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def print_report(
    area_rows: list[
        dict[str, str]
    ],
    features: list[
        dict[str, Any]
    ],
    unresolved: list[
        dict[str, Any]
    ],
    fuzzy_review: list[
        dict[str, Any]
    ],
    geographic_review: list[
        dict[str, Any]
    ],
    match_methods: Counter,
) -> None:
    print()
    print(
        "=" * 72
    )

    print(
        "ARGENTINA PHONE-CODE "
        "LOCALITY MATCHING"
    )

    print(
        "=" * 72
    )

    print(
        f"Source rows: "
        f"{len(area_rows):,}"
    )

    print(
        f"Matched rows: "
        f"{len(features):,}"
    )

    print(
        f"Unresolved rows: "
        f"{len(unresolved):,}"
    )

    match_rate = (
        len(features)
        / len(area_rows)
        * 100
        if area_rows
        else 0
    )

    print(
        f"Match rate: "
        f"{match_rate:.2f}%"
    )

    print()
    print(
        "Match methods:"
    )

    for (
        method,
        count,
    ) in (
        match_methods.most_common()
    ):
        print(
            f"  {method}: "
            f"{count:,}"
        )

    source_codes = {
        row["code"]
        for row
        in area_rows
    }

    matched_codes = {
        feature[
            "properties"
        ][
            "area_code"
        ]
        for feature
        in features
    }

    unresolved_codes = {
        row["code"]
        for row
        in unresolved
    }

    print()

    print(
        f"Distinct source codes: "
        f"{len(source_codes):,}"
    )

    print(
        "Codes represented by "
        "matched points: "
        f"{len(matched_codes):,}"
    )

    print(
        "Codes appearing in "
        "unresolved rows: "
        f"{len(unresolved_codes):,}"
    )

    codes_without_match = (
        source_codes
        - matched_codes
    )

    print(
        "Codes with no matched "
        "point at all: "
        f"{len(codes_without_match):,}"
    )

    if codes_without_match:
        print()
        print(
            "Codes with no "
            "matched point:"
        )

        print(
            "  "
            + ", ".join(
                sorted(
                    codes_without_match,
                    key=lambda value: (
                        len(value),
                        value,
                    ),
                )
            )
        )

    department_methods = {
        method:
            count
        for (
            method,
            count,
        ) in match_methods.items()
        if method.startswith(
            "department_"
        )
    }

    containment_count = sum(
        count
        for (
            method,
            count,
        ) in match_methods.items()
        if "containment"
        in method
    )

    print()

    print(
        "Department-hint matches: "
        f"{sum(department_methods.values()):,}"
    )

    for (
        method,
        count,
    ) in sorted(
        department_methods.items()
    ):
        print(
            f"  {method}: "
            f"{count:,}"
        )

    print()

    print(
        "Containment matches: "
        f"{containment_count:,}"
    )

    print(
        "Automatically reviewed "
        "text/containment matches: "
        f"{len(fuzzy_review):,}"
    )

    print(
        "Automatically accepted "
        "geographic matches: "
        f"{len(geographic_review):,}"
    )

    if geographic_review:
        print()
        print(
            "Geographic matches:"
        )

        rows = sorted(
            geographic_review,
            key=lambda row: (
                row[
                    "text_score"
                ],
                row[
                    "distance_km"
                ],
            ),
        )

        for row in rows[:60]:
            print()

            print(
                f"  {row['code']} | "
                f"{row['source_province']} | "
                f"{row['source_locality']}"
            )

            print(
                "    -> "
                f"{row['official_locality']} | "
                f"{row['official_department']} | "
                f"{row['official_type']}"
            )

            print(
                f"    method: "
                f"{row['method']} | "
                f"text: "
                f"{row['text_score']:.4f} | "
                f"distance: "
                f"{row['distance_km']:.1f} km | "
                f"containment: "
                f"{row['strong_containment']}"
            )

            if (
                row[
                    "next_distance_km"
                ]
                is not None
            ):
                print(
                    "    next plausible "
                    "distance: "
                    f"{row['next_distance_km']:.1f} km"
                )

    print()
    print(
        "First 40 unresolved rows:"
    )

    for row in unresolved[:40]:
        print()

        print(
            f"  {row['code']} | "
            f"{row['province']} | "
            f"{row['locality']}"
        )

        print(
            f"    reason: "
            f"{row['reason']}"
        )

        if row.get(
            "department_hint"
        ):
            print(
                "    department hint: "
                f"{row['department_hint']}"
            )

        print(
            f"    best score: "
            f"{row.get('best_fuzzy_score', 0):.4f} | "
            f"margin: "
            f"{row.get('best_fuzzy_margin', 0):.4f}"
        )

        for suggestion in (
            row.get(
                "suggestions",
                [],
            )[:3]
        ):
            print(
                "    -> "
                f"{suggestion['locality']} | "
                f"{suggestion['department']} | "
                f"{suggestion['type']} | "
                f"{suggestion['score']:.4f}"
            )


def main() -> None:
    print(
        "Loading Argentina "
        "phone-code data..."
    )

    area_rows = (
        read_area_code_js()
    )

    official_localities = (
        read_official_localities()
    )

    (
        indexes,
        province_index,
    ) = build_indexes(
        official_localities
    )

    (
        features,
        unresolved,
        fuzzy_review,
        match_methods,
    ) = process_text_matches(
        area_rows,
        indexes,
        province_index,
    )

    print()
    print(
        "Pass 1 complete:"
    )

    print(
        f"  matched: "
        f"{len(features):,}"
    )

    print(
        f"  unresolved: "
        f"{len(unresolved):,}"
    )

    (
        features,
        unresolved,
        geographic_review,
    ) = process_geographic_matches(
        features,
        unresolved,
        province_index,
        match_methods,
    )

    validate_output(
        area_rows,
        features,
        unresolved,
    )
    
    (
        amba_seed_count,
        amba_skipped_count,
    ) = add_area_code_11_seeds(
        features,
        official_localities,
    )

    print()
    print(
        f"Added synthetic code-11 "
        f"AMBA seeds: "
        f"{amba_seed_count:,}"
    )

    print(
        f"Skipped AMBA seeds already "
        f"occupied by real phone data: "
        f"{amba_skipped_count:,}"
    )

    write_outputs(
        features,
        unresolved,
        fuzzy_review,
        geographic_review,
    )

    print_report(
        area_rows,
        features,
        unresolved,
        fuzzy_review,
        geographic_review,
        match_methods,
    )

    print()
    print(
        "Wrote:"
    )

    print(
        f"  {OUTPUT_GEOJSON_PATH}"
    )

    print(
        f"  {UNRESOLVED_PATH}"
    )

    print(
        f"  {FUZZY_REVIEW_PATH}"
    )

    print(
        f"  {GEOGRAPHIC_REVIEW_PATH}"
    )


if __name__ == "__main__":
    main()