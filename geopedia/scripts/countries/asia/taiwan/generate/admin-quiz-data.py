"""
Generate Taiwan administrative quiz question data for GeoPedia.

Source files
------------
public/data/countries/taiwan/geojson/provinces.geojson
public/data/countries/taiwan/geojson/counties.geojson
public/data/countries/taiwan/geojson/townships.geojson

Output
------
src/quiz/quizzes/countries/asia/taiwan/data/admin.ts

The generated TypeScript file contains:

    TAIWAN_PROVINCE_QUESTIONS
    TAIWAN_COUNTY_QUESTIONS
    TAIWAN_TOWNSHIP_QUESTIONS

Each question contains:

    {
      answer: "...",
      display: "...",
      nativeDisplay: "...",
    }

Question behavior
-----------------
- `answer` is the stable feature ID used by the map.
- `display` is the English administrative name.
- `nativeDisplay` is the native Traditional Chinese name.
- Duplicate English names are disambiguated using their parent division.
- When a duplicate is disambiguated, the native display is also
  disambiguated using the native parent name.

Example:

    {
      answer: "...",
      display: "East District (Chiayi City)",
      nativeDisplay: "東區 (嘉義市)",
    }

Run from the GeoPedia project root:

    python scripts/countries/taiwan/generate/admin-quiz-data.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[4]

PUBLIC_DIR = (
    ROOT
    / "public"
    / "data"
    / "countries"
    / "taiwan"
    / "geojson"
)

OUTPUT_PATH = (
    ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "asia"
    / "taiwan"
    / "data"
    / "admin.ts"
)

PROVINCES_PATH = PUBLIC_DIR / "provinces.geojson"
COUNTIES_PATH = PUBLIC_DIR / "counties.geojson"
TOWNSHIPS_PATH = PUBLIC_DIR / "townships.geojson"


# ---------------------------------------------------------------------------
# Expected counts
# ---------------------------------------------------------------------------

EXPECTED_PROVINCES = 7
EXPECTED_COUNTIES = 22
EXPECTED_TOWNSHIPS = 368


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_features(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing source file: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
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


def validate_features(
    features: list[dict],
    *,
    expected_count: int,
    id_property: str,
    name_property: str,
    native_property: str,
    label: str,
) -> None:
    if len(features) != expected_count:
        raise ValueError(
            f"{label}: expected {expected_count} features, "
            f"found {len(features)}."
        )

    ids: list[str] = []

    for feature in features:
        props = feature.get("properties") or {}

        for property_name in (
            id_property,
            name_property,
            native_property,
        ):
            value = props.get(property_name)

            if value is None or str(value).strip() == "":
                raise ValueError(
                    f"{label}: feature is missing "
                    f"{property_name!r}."
                )

        ids.append(
            str(props[id_property]).strip()
        )

    if len(ids) != len(set(ids)):
        duplicates = sorted(
            value
            for value, count in Counter(ids).items()
            if count > 1
        )

        raise ValueError(
            f"{label}: duplicate IDs found: "
            f"{duplicates}"
        )


def ts_string(value: str) -> str:
    """
    Encode a string as a valid TypeScript string while preserving
    Unicode characters.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
    )


def make_questions(
    features: list[dict],
    *,
    id_property: str,
    name_property: str,
    native_property: str,
    parent_property: str | None = None,
    native_parent_property: str | None = None,
) -> list[tuple[str, str, str]]:
    """
    Create question tuples:

        (answer, display, native_display)

    Duplicate English display names are disambiguated with their parent
    division. The native display is disambiguated in the same way using
    the native parent name.
    """

    names = [
        str(
            feature["properties"][name_property]
        ).strip()
        for feature in features
    ]

    name_counts = Counter(names)

    questions: list[tuple[str, str, str]] = []

    for feature in features:
        props = feature["properties"]

        answer = str(
            props[id_property]
        ).strip()

        display = str(
            props[name_property]
        ).strip()

        native_display = str(
            props[native_property]
        ).strip()

        if name_counts[display] > 1:
            if (
                parent_property is None
                or native_parent_property is None
            ):
                raise ValueError(
                    f"Duplicate display name {display!r} "
                    "cannot be disambiguated because parent "
                    "properties were not provided."
                )

            parent = str(
                props[parent_property]
            ).strip()

            native_parent = str(
                props[native_parent_property]
            ).strip()

            display = (
                f"{display} ({parent})"
            )

            native_display = (
                f"{native_display} ({native_parent})"
            )

        questions.append(
            (
                answer,
                display,
                native_display,
            )
        )

    # Sort by the final English display shown to the player.
    questions.sort(
        key=lambda item: (
            item[1].casefold(),
            item[0],
        )
    )

    return questions


def render_questions(
    constant_name: str,
    questions: list[tuple[str, str, str]],
) -> str:
    lines = [
        (
            f"export const {constant_name}: "
            "FeatureQuizQuestion[] = ["
        )
    ]

    for answer, display, native_display in questions:
        lines.append(
            "  { "
            f"answer: {ts_string(answer)}, "
            f"display: {ts_string(display)}, "
            f"nativeDisplay: {ts_string(native_display)} "
            "},"
        )

    lines.append("];")

    return "\n".join(lines)


def get_duplicate_names(
    features: list[dict],
    property_name: str,
) -> list[str]:
    counts = Counter(
        str(
            feature["properties"][property_name]
        ).strip()
        for feature in features
    )

    return sorted(
        name
        for name, count in counts.items()
        if count > 1
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Loading Taiwan public administrative data..."
    )

    provinces = load_features(
        PROVINCES_PATH
    )

    counties = load_features(
        COUNTIES_PATH
    )

    townships = load_features(
        TOWNSHIPS_PATH
    )

    # -----------------------------------------------------------------------
    # Validate source data
    # -----------------------------------------------------------------------

    validate_features(
        provinces,
        expected_count=EXPECTED_PROVINCES,
        id_property="province_id",
        name_property="province",
        native_property="native_province",
        label="Provinces",
    )

    validate_features(
        counties,
        expected_count=EXPECTED_COUNTIES,
        id_property="county_id",
        name_property="county",
        native_property="native_county",
        label="Counties",
    )

    validate_features(
        townships,
        expected_count=EXPECTED_TOWNSHIPS,
        id_property="township_id",
        name_property="township",
        native_property="native_township",
        label="Townships",
    )

    # -----------------------------------------------------------------------
    # Generate questions
    # -----------------------------------------------------------------------

    province_questions = make_questions(
        provinces,
        id_property="province_id",
        name_property="province",
        native_property="native_province",
    )

    county_questions = make_questions(
        counties,
        id_property="county_id",
        name_property="county",
        native_property="native_county",
    )

    township_questions = make_questions(
        townships,
        id_property="township_id",
        name_property="township",
        native_property="native_township",
        parent_property="county",
        native_parent_property="native_county",
    )

    # -----------------------------------------------------------------------
    # Render TypeScript
    # -----------------------------------------------------------------------

    sections = [
        (
            "/*\n"
            " * AUTO-GENERATED FILE.\n"
            " *\n"
            " * Generated by:\n"
            " *   scripts/countries/taiwan/generate/"
            "admin-quiz-data.py\n"
            " *\n"
            " * Source data:\n"
            " *   public/data/countries/taiwan/geojson/"
            "provinces.geojson\n"
            " *   public/data/countries/taiwan/geojson/"
            "counties.geojson\n"
            " *   public/data/countries/taiwan/geojson/"
            "townships.geojson\n"
            " *\n"
            " * Do not edit manually. Regenerate this file after "
            "changing\n"
            " * Taiwan administrative source data.\n"
            " */\n\n"
            'import type { FeatureQuizQuestion } '
            'from "@/types/quiz";'
        ),
        render_questions(
            "TAIWAN_PROVINCE_QUESTIONS",
            province_questions,
        ),
        render_questions(
            "TAIWAN_COUNTY_QUESTIONS",
            county_questions,
        ),
        render_questions(
            "TAIWAN_TOWNSHIP_QUESTIONS",
            township_questions,
        ),
    ]

    output = "\n\n".join(sections) + "\n"

    # -----------------------------------------------------------------------
    # Write output
    # -----------------------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    duplicate_province_names = get_duplicate_names(
        provinces,
        "province",
    )

    duplicate_county_names = get_duplicate_names(
        counties,
        "county",
    )

    duplicate_township_names = get_duplicate_names(
        townships,
        "township",
    )

    print()
    print(
        "Taiwan administrative quiz data generated."
    )
    print()

    print(
        f"Provinces: {len(province_questions)}"
    )

    print(
        f"Counties:  {len(county_questions)}"
    )

    print(
        f"Townships: {len(township_questions)}"
    )

    print()

    print(
        f"Output: {OUTPUT_PATH.relative_to(ROOT)}"
    )

    print()

    print(
        "Duplicate province names disambiguated: "
        f"{len(duplicate_province_names)}"
    )

    for name in duplicate_province_names:
        print(f"  {name}")

    print()

    print(
        "Duplicate county names disambiguated: "
        f"{len(duplicate_county_names)}"
    )

    for name in duplicate_county_names:
        print(f"  {name}")

    print()

    print(
        "Duplicate township names disambiguated: "
        f"{len(duplicate_township_names)}"
    )

    for name in duplicate_township_names:
        print(f"  {name}")


if __name__ == "__main__":
    main()