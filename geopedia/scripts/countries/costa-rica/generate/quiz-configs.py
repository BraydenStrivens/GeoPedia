"""Generate Costa Rica's larger feature-quiz configuration files.

This script generates TypeScript quiz configs from GeoPedia's processed
Costa Rica runtime GeoJSON.

Generated quizzes:
- Cantons
- Districts
- 3-digit postal-code prefixes
- 5-digit postal codes

The province-name dictionary is owned and exported by provincesQuiz.ts.
The canton-name dictionary is generated and exported by cantonsQuiz.ts.
Other generated quiz files import those dictionaries rather than
duplicating them.

Canton questions are derived from the exported canton-name dictionary.

District questions are generated explicitly because duplicate district
names must be disambiguated with their canton name.

Postal-code questions:
- 3-digit prefixes are derived from the canton-name dictionary.
- 5-digit postal codes are generated explicitly from district IDs.

Inputs:
    public/data/countries/costa-rica/geojson/cantons.geojson
    public/data/countries/costa-rica/geojson/districts.geojson

Outputs:
    src/quiz/quizzes/costa-rica/cantonsQuiz.ts
    src/quiz/quizzes/costa-rica/districtsQuiz.ts
    src/quiz/quizzes/costa-rica/postalCodePrefixes3DigitQuiz.ts
    src/quiz/quizzes/costa-rica/postalCodesQuiz.ts
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

CANTONS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "costa-rica"
    / "geojson"
    / "cantons.geojson"
)

DISTRICTS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "costa-rica"
    / "geojson"
    / "districts.geojson"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "costa-rica"
)

EXPECTED_CANTON_COUNT = 84
EXPECTED_DISTRICT_COUNT = 492

EXPECTED_PROVINCE_IDS = {
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
}


def load_features(path: Path) -> list[dict[str, Any]]:
    """Load and return features from a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file does not exist: {path}"
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected a GeoJSON FeatureCollection: {path}"
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"GeoJSON contains no valid features array: {path}"
        )

    return features


def get_properties(
    feature: dict[str, Any],
) -> dict[str, Any]:
    """Return a feature's properties object."""
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            "GeoJSON feature contains no valid properties object."
        )

    return properties


def require_string(
    properties: dict[str, Any],
    property_name: str,
) -> str:
    """Read and validate a required non-empty string property."""
    value = properties.get(property_name)

    if not isinstance(value, str):
        raise ValueError(
            f"Property {property_name!r} must be a string. "
            f"Got: {value!r}"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"Property {property_name!r} cannot be blank."
        )

    return value


def validate_cantons(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Validate and normalize the processed canton records."""
    if len(features) != EXPECTED_CANTON_COUNT:
        raise ValueError(
            "Unexpected processed canton count: "
            f"{len(features)}. Expected {EXPECTED_CANTON_COUNT}."
        )

    records: list[dict[str, str]] = []

    for feature in features:
        properties = get_properties(
            feature
        )

        canton_id = require_string(
            properties,
            "canton_id",
        )

        name = require_string(
            properties,
            "name",
        )

        province_id = require_string(
            properties,
            "province_id",
        )

        if (
            len(canton_id) != 3
            or not canton_id.isdigit()
        ):
            raise ValueError(
                f"Invalid canton ID: {canton_id!r}"
            )

        if province_id not in EXPECTED_PROVINCE_IDS:
            raise ValueError(
                f"Invalid province ID: {province_id!r}"
            )

        if canton_id[0] != province_id:
            raise ValueError(
                "Canton/province hierarchy mismatch: "
                f"{canton_id} -> {province_id}"
            )

        records.append(
            {
                "canton_id": canton_id,
                "name": name,
                "province_id": province_id,
            }
        )

    canton_ids = [
        record["canton_id"]
        for record in records
    ]

    if len(set(canton_ids)) != len(canton_ids):
        raise ValueError(
            "Processed canton data contains duplicate canton IDs."
        )

    canton_names = [
        record["name"]
        for record in records
    ]

    if len(set(canton_names)) != len(canton_names):
        raise ValueError(
            "Processed canton data contains duplicate canton names."
        )

    return sorted(
        records,
        key=lambda record: record["canton_id"],
    )


def validate_districts(
    features: list[dict[str, Any]],
    canton_names_by_id: dict[str, str],
) -> list[dict[str, str]]:
    """Validate and normalize the processed district records."""
    if len(features) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected processed district count: "
            f"{len(features)}. Expected {EXPECTED_DISTRICT_COUNT}."
        )

    records: list[dict[str, str]] = []

    for feature in features:
        properties = get_properties(
            feature
        )

        district_id = require_string(
            properties,
            "district_id",
        )

        name = require_string(
            properties,
            "name",
        )

        canton_id = require_string(
            properties,
            "canton_id",
        )

        province_id = require_string(
            properties,
            "province_id",
        )

        if (
            len(district_id) != 5
            or not district_id.isdigit()
        ):
            raise ValueError(
                f"Invalid district ID: {district_id!r}"
            )

        if canton_id not in canton_names_by_id:
            raise ValueError(
                "District references an unknown canton: "
                f"{district_id} -> {canton_id}"
            )

        if province_id not in EXPECTED_PROVINCE_IDS:
            raise ValueError(
                "District references an unknown province: "
                f"{district_id} -> {province_id}"
            )

        if district_id[:3] != canton_id:
            raise ValueError(
                "District/canton hierarchy mismatch: "
                f"{district_id} -> {canton_id}"
            )

        if district_id[0] != province_id:
            raise ValueError(
                "District/province hierarchy mismatch: "
                f"{district_id} -> {province_id}"
            )

        if canton_id[0] != province_id:
            raise ValueError(
                "Canton/province hierarchy mismatch: "
                f"{canton_id} -> {province_id}"
            )

        records.append(
            {
                "district_id": district_id,
                "name": name,
                "canton_id": canton_id,
                "province_id": province_id,
            }
        )

    district_ids = [
        record["district_id"]
        for record in records
    ]

    if len(set(district_ids)) != len(district_ids):
        raise ValueError(
            "Processed district data contains duplicate district IDs."
        )

    return sorted(
        records,
        key=lambda record: record["district_id"],
    )


def ts_string(value: str) -> str:
    """Encode a string as a TypeScript-compatible string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def generate_string_map(
    constant_name: str,
    values: dict[str, str],
    documentation: str,
    export: bool = False,
) -> str:
    """Generate a documented TypeScript string lookup object."""
    declaration = (
        "export const"
        if export
        else "const"
    )

    lines = [
        "/**",
        f" * {documentation}",
        " */",
        f"{declaration} {constant_name} = {{",
    ]

    for key in sorted(values):
        lines.append(
            f"  {ts_string(key)}: {ts_string(values[key])},"
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def generate_questions(
    constant_name: str,
    questions: list[tuple[str, str]],
    documentation: str,
) -> str:
    """Generate a documented TypeScript quiz-question array."""
    lines = [
        "/**",
        f" * {documentation}",
        " */",
        f"const {constant_name} = [",
    ]

    for answer, display in questions:
        lines.append(
            "  { "
            f"answer: {ts_string(answer)}, "
            f"display: {ts_string(display)} "
            "},"
        )

    lines.extend(
        [
            "] as const;",
            "",
        ]
    )

    return "\n".join(lines)


def write_typescript(
    filename: str,
    content: str,
) -> None:
    """Write a generated TypeScript quiz configuration."""
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        OUTPUT_DIRECTORY
        / filename
    )

    path.write_text(
        content.rstrip() + "\n",
        encoding="utf-8",
    )

    print(
        f"Wrote: {path}"
    )


def generate_cantons_quiz(
    cantons: list[dict[str, str]],
) -> None:
    """Generate Costa Rica's canton quiz."""
    canton_names_by_id = {
        record["canton_id"]: record["name"]
        for record in cantons
    }

    canton_map = generate_string_map(
        "COSTA_RICA_CANTON_NAMES_BY_ID",
        canton_names_by_id,
        (
            "Costa Rica canton names keyed by their "
            "3-digit administrative ID."
        ),
        export=True,
    )

    content = f'''import {{ COSTA_RICA_PROVINCE_NAMES_BY_ID }} from "./provincesQuiz";
import type {{ FeatureQuiz }} from "@/types/quiz";

{canton_map}
/**
 * Questions for Costa Rica's cantons.
 */
const COSTA_RICA_CANTON_QUESTIONS = Object.entries(
  COSTA_RICA_CANTON_NAMES_BY_ID,
).map(([answer, display]) => ({{
  answer,
  display,
}}));

/**
 * Canton quiz for Costa Rica.
 */
export const costaRicaCantonsQuiz: FeatureQuiz = {{
  id: "costa-rica-cantons",
  name: "Cantons",
  description: `Learn all ${{COSTA_RICA_CANTON_QUESTIONS.length}} cantons of Costa Rica. Filters let you practice cantons by province.`,

  kind: "feature",
  mapId: "costa-rica-cantons",

  answerProperty: "canton_id",
  answerType: "single",

  grouping: {{
    properties: [
      {{
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCE_NAMES_BY_ID,
      }},
    ],
  }},

  questions: COSTA_RICA_CANTON_QUESTIONS,
}};
'''

    write_typescript(
        "cantonsQuiz.ts",
        content,
    )


def generate_districts_quiz(
    districts: list[dict[str, str]],
    canton_names_by_id: dict[str, str],
) -> None:
    """Generate Costa Rica's district quiz."""
    name_counts = Counter(
        record["name"]
        for record in districts
    )

    questions: list[tuple[str, str]] = []

    for record in districts:
        name = record["name"]

        if name_counts[name] > 1:
            display = (
                f"{name} "
                f"({canton_names_by_id[record['canton_id']]})"
            )
        else:
            display = name

        questions.append(
            (
                record["district_id"],
                display,
            )
        )

    displays = [
        display
        for _, display in questions
    ]

    duplicate_displays = sorted(
        display
        for display, count in Counter(displays).items()
        if count > 1
    )

    if duplicate_displays:
        raise ValueError(
            "Canton-based district disambiguation did not produce "
            "unique display values: "
            f"{duplicate_displays}"
        )

    question_array = generate_questions(
        "COSTA_RICA_DISTRICT_QUESTIONS",
        questions,
        (
            "Costa Rica's districts, with duplicate names "
            "disambiguated by canton."
        ),
    )

    content = f'''import {{ COSTA_RICA_CANTON_NAMES_BY_ID }} from "./cantonsQuiz";
import {{ COSTA_RICA_PROVINCE_NAMES_BY_ID }} from "./provincesQuiz";
import type {{ FeatureQuiz }} from "@/types/quiz";

{question_array}
/**
 * District quiz for Costa Rica.
 */
export const costaRicaDistrictsQuiz: FeatureQuiz = {{
  id: "costa-rica-districts",
  name: "Districts",
  description: `Learn all ${{COSTA_RICA_DISTRICT_QUESTIONS.length}} districts of Costa Rica. Filters let you practice districts by province or canton.`,

  kind: "feature",
  mapId: "costa-rica-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {{
    properties: [
      {{
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCE_NAMES_BY_ID,
      }},
      {{
        property: "canton_id",
        label: "Canton",
        valueType: "string",
        valueLabels: COSTA_RICA_CANTON_NAMES_BY_ID,
      }},
    ],
  }},

  questions: [...COSTA_RICA_DISTRICT_QUESTIONS],
}};
'''

    write_typescript(
        "districtsQuiz.ts",
        content,
    )


def generate_postal_prefixes_quiz() -> None:
    """Generate Costa Rica's 3-digit postal-code-prefix quiz."""
    content = '''import { COSTA_RICA_CANTON_NAMES_BY_ID } from "./cantonsQuiz";
import { COSTA_RICA_PROVINCE_NAMES_BY_ID } from "./provincesQuiz";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Questions for Costa Rica's 3-digit postal-code prefixes.
 *
 * Two trailing dashes show each prefix's position within a 5-digit
 * postal code.
 */
const COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS = Object.keys(
  COSTA_RICA_CANTON_NAMES_BY_ID,
).map((answer) => ({
  answer,
  display: `${answer}--`,
}));

/**
 * Tests Costa Rica's 3-digit postal-code prefixes.
 *
 * Each prefix corresponds to a canton and represents the first three digits
 * of Costa Rica's otherwise 5-digit postal codes.
 */
export const costaRicaPostalCodePrefixes3DigitQuiz: FeatureQuiz = {
  id: "costa-rica-postal-code-prefixes-3-digit",
  name: "3 Digit Postal Codes",
  description: `Learn Costa Rica's ${COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS.length} 3-digit postal-code prefixes, which represent the first three digits of an otherwise 5-digit postal code. Filters let you practice prefixes by province.`,

  kind: "feature",
  mapId: "costa-rica-cantons",

  answerProperty: "canton_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCE_NAMES_BY_ID,
      },
    ],
  },

  questions: COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS,
};
'''

    write_typescript(
        "postalCodePrefixes3DigitQuiz.ts",
        content,
    )


def generate_postal_codes_quiz(
    districts: list[dict[str, str]],
) -> None:
    """Generate Costa Rica's full 5-digit postal-code quiz."""
    questions = [
        (
            record["district_id"],
            record["district_id"],
        )
        for record in districts
    ]

    question_array = generate_questions(
        "COSTA_RICA_POSTAL_CODE_QUESTIONS",
        questions,
        "Costa Rica's full 5-digit postal codes.",
    )

    content = f'''import {{ COSTA_RICA_CANTON_NAMES_BY_ID }} from "./cantonsQuiz";
import {{ COSTA_RICA_PROVINCE_NAMES_BY_ID }} from "./provincesQuiz";
import type {{ FeatureQuiz }} from "@/types/quiz";

{question_array}
/**
 * Tests Costa Rica's full 5-digit postal codes.
 *
 * Costa Rica's postal codes correspond directly to its 5-digit district
 * identifiers.
 */
export const costaRicaPostalCodesQuiz: FeatureQuiz = {{
  id: "costa-rica-postal-codes",
  name: "5 Digit Postal Codes",
  description: `Learn all ${{COSTA_RICA_POSTAL_CODE_QUESTIONS.length}} 5-digit postal codes of Costa Rica. Filters let you practice postal codes by province or canton.`,

  kind: "feature",
  mapId: "costa-rica-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {{
    properties: [
      {{
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCE_NAMES_BY_ID,
      }},
      {{
        property: "canton_id",
        label: "Canton",
        valueType: "string",
        valueLabels: COSTA_RICA_CANTON_NAMES_BY_ID,
      }},
    ],
  }},

  questions: [...COSTA_RICA_POSTAL_CODE_QUESTIONS],
}};
'''

    write_typescript(
        "postalCodesQuiz.ts",
        content,
    )


def main() -> None:
    """Validate Costa Rica runtime data and generate quiz configs."""
    print("Reading processed Costa Rica GeoJSON...")
    print()

    canton_features = load_features(
        CANTONS_PATH
    )

    district_features = load_features(
        DISTRICTS_PATH
    )

    cantons = validate_cantons(
        canton_features
    )

    canton_names_by_id = {
        record["canton_id"]: record["name"]
        for record in cantons
    }

    districts = validate_districts(
        district_features,
        canton_names_by_id,
    )

    print(
        f"Validated cantons: {len(cantons)}"
    )
    print(
        f"Validated districts: {len(districts)}"
    )

    duplicate_district_names = {
        name: count
        for name, count in Counter(
            record["name"]
            for record in districts
        ).items()
        if count > 1
    }

    print(
        "Duplicate district names requiring disambiguation: "
        f"{len(duplicate_district_names)}"
    )
    print()

    generate_cantons_quiz(
        cantons
    )

    generate_districts_quiz(
        districts,
        canton_names_by_id,
    )

    generate_postal_prefixes_quiz()

    generate_postal_codes_quiz(
        districts
    )

    print()
    print(
        "Costa Rica quiz-config generation passed."
    )


if __name__ == "__main__":
    main()