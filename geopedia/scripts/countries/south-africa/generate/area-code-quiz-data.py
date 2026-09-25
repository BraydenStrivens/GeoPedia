"""
Generate South Africa telephone area-code quiz question data.

The full area-code questions are derived from the runtime area-code GeoJSON so
the generated questions remain synchronized with the map features.

South Africa has 36 geographic regions in GeoPedia's area-code map but 37
quiz questions. 010 is an alternative Johannesburg code and shares one
geographic feature with 011. The shared feature has the stable ID
"010 / 011" and exposes both 010 and 011 as its accepted area-code values.

The one-digit prefix quiz contains prefixes 1- through 5-. Its feature answers
are the prefix digits themselves, while the displayed questions include the
trailing hyphen.

Inputs:
    public/data/countries/south-africa/geojson/
    area-codes.geojson

    public/data/countries/south-africa/geojson/
    area-code-prefixes.geojson

Outputs:
    src/quiz/quizzes/countries/africa/south-africa/data/
    areaCodes.ts

    src/quiz/quizzes/countries/africa/south-africa/data/
    areaCodePrefixes.ts

Run from the GeoPedia project root:
    python scripts/countries/south-africa/generate/area-code-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


AREA_CODES_INPUT = Path(
    "public/data/countries/south-africa/geojson/"
    "area-codes.geojson"
)

PREFIXES_INPUT = Path(
    "public/data/countries/south-africa/geojson/"
    "area-code-prefixes.geojson"
)

DATA_DIRECTORY = Path(
    "src/quiz/quizzes/countries/africa/south-africa/data"
)

AREA_CODES_OUTPUT = (
    DATA_DIRECTORY
    / "areaCodes.ts"
)

PREFIXES_OUTPUT = (
    DATA_DIRECTORY
    / "areaCodePrefixes.ts"
)


def load_feature_collection(
    path: Path,
) -> list[dict[str, Any]]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} has no valid features array."
        )

    return features


def ts_string(
    value: str,
) -> str:
    """Encode a string as a TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def generate_area_codes(
    features: list[dict[str, Any]],
) -> str:
    """
    Generate full South Africa area-code quiz questions.

    Each geographic feature exposes its accepted answers through the
    area_codes array. Most features contain one answer, while the shared
    Johannesburg feature contains both 010 and 011.

    Each accepted area code becomes its own quiz question. The quiz's
    multiple-answer infrastructure associates those questions with the
    appropriate geographic feature.
    """
    area_codes: list[str] = []

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        area_code_id = properties.get(
            "area_code_id"
        )

        feature_area_codes = properties.get(
            "area_codes"
        )

        if not isinstance(
            area_code_id,
            str,
        ):
            raise ValueError(
                "Area-code feature is missing area_code_id."
            )

        if (
            not isinstance(
                feature_area_codes,
                list,
            )
            or not feature_area_codes
            or not all(
                isinstance(area_code, str)
                for area_code in feature_area_codes
            )
        ):
            raise ValueError(
                f"Area-code feature {area_code_id} "
                "has invalid area_codes."
            )

        area_codes.extend(
            feature_area_codes
        )

    if len(area_codes) != len(set(area_codes)):
        raise ValueError(
            "An area code appears in more than one geographic feature."
        )

    area_codes.sort()

    if "010" not in area_codes or "011" not in area_codes:
        raise ValueError(
            "Expected both Johannesburg area codes 010 and 011."
        )

    lines = [
        "/**",
        " * GENERATED FILE — DO NOT EDIT MANUALLY.",
        " *",
        " * South Africa geographic telephone area-code quiz questions.",
        " * 010 and 011 are separate quiz answers that share one geographic",
        " * Johannesburg feature.",
        " *",
        " * Regenerate with:",
        " * python scripts/countries/south-africa/generate/area-code-quiz-data.py",
        " */",
        "",
        'import type { FeatureQuizQuestion } from "@/types/quiz";',
        "",
        "export const SOUTH_AFRICA_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] = [",
    ]

    for area_code in area_codes:
        lines.extend(
            [
                "  {",
                f"    answer: {ts_string(area_code)},",
                "  },",
            ]
        )

    lines.extend(
        [
            "];",
            "",
        ]
    )

    return "\n".join(
        lines
    )
      

def generate_prefixes(
    features: list[dict[str, Any]],
) -> str:
    """
    Generate one-digit South Africa area-code prefix quiz questions.

    Feature answers are the prefix digits themselves, while the displayed
    question uses the familiar prefix notation such as "1-" or "5-".
    """
    prefixes: list[str] = []

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        prefix = properties.get(
            "prefix_1"
        )

        if not isinstance(
            prefix,
            str,
        ):
            raise ValueError(
                "Prefix feature is missing prefix_1."
            )

        prefixes.append(
            prefix
        )

    prefixes.sort()

    lines = [
        "/**",
        " * GENERATED FILE — DO NOT EDIT MANUALLY.",
        " *",
        " * South Africa one-digit geographic telephone-prefix questions.",
        " *",
        " * Regenerate with:",
        " * python scripts/countries/south-africa/generate/area-code-quiz-data.py",
        " */",
        "",
        'import type { FeatureQuizQuestion } from "@/types/quiz";',
        "",
        "export const SOUTH_AFRICA_AREA_CODE_PREFIX_QUESTIONS: FeatureQuizQuestion[] = [",
    ]

    for prefix in prefixes:
        lines.extend(
            [
                "  {",
                f"    answer: {ts_string(prefix)},",
                f'    display: {ts_string("0" + prefix + "-")},',
                "  },",
            ]
        )

    lines.extend(
        [
            "];",
            "",
        ]
    )

    return "\n".join(
        lines
    )


def main() -> None:
    print("Loading runtime area-code data...")

    area_code_features = load_feature_collection(
        AREA_CODES_INPUT
    )

    prefix_features = load_feature_collection(
        PREFIXES_INPUT
    )

    print(
        f"Area-code features: {len(area_code_features):,}"
    )
    print(
        f"Prefix features:    {len(prefix_features):,}"
    )

    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    area_code_source = generate_area_codes(
        area_code_features
    )

    prefix_source = generate_prefixes(
        prefix_features
    )

    AREA_CODES_OUTPUT.write_text(
        area_code_source,
        encoding="utf-8",
    )

    PREFIXES_OUTPUT.write_text(
        prefix_source,
        encoding="utf-8",
    )

    print()
    print("Wrote:")
    print(
        f"  {AREA_CODES_OUTPUT}"
    )
    print(
        f"  {PREFIXES_OUTPUT}"
    )

    print()
    print(
        "Area-code questions: "
        f"{len(area_code_features) + 1:,}"
    )
    print(
        "Prefix questions:    "
        f"{len(prefix_features):,}"
    )


if __name__ == "__main__":
    main()