"""
Generate TypeScript quiz data for Japan's telephone area-code quizzes.

The processed public GeoJSON files are the canonical source for these
questions. This generator extracts only the properties needed by the quiz
configuration layer.

Generated datasets:

    JAPAN_AREA_CODES_BY_ID
        59 area-code regions keyed by their normalized area code.

    JAPAN_AREA_CODE_PREFIXES_BY_ID
        9 broad prefix regions keyed by their prefix ID.

Input:
    public/data/countries/japan/geojson/
        area-codes.geojson
        area-code-prefixes.geojson

Output:
    src/quiz/quizzes/countries/asia/japan/data/
        areaCodes.ts

Run from the GeoPedia project root:

    python scripts/countries/japan/generate/area-code-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

GEOJSON_DIR = Path(
    "public/data/countries/japan/geojson"
)

AREA_CODES_PATH = GEOJSON_DIR / "area-codes.geojson"
PREFIXES_PATH = GEOJSON_DIR / "area-code-prefixes.geojson"

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/asia/japan/data/areaCodes.ts"
)


# ---------------------------------------------------------------------------
# Expected counts
# ---------------------------------------------------------------------------

EXPECTED_AREA_CODE_COUNT = 59
EXPECTED_PREFIX_COUNT = 9


# ---------------------------------------------------------------------------
# GeoJSON loading
# ---------------------------------------------------------------------------


def load_features(
    path: Path,
) -> list[dict[str, Any]]:
    """Load the features from a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON input does not exist: {path}"
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
            f"{path} does not contain a valid features array."
        )

    return features


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def require_string(
    properties: dict[str, Any],
    property_name: str,
    *,
    label: str,
) -> str:
    """Return a required non-empty string property."""
    value = properties.get(property_name)

    if not isinstance(value, str) or not value:
        raise ValueError(
            f"{label} has invalid {property_name!r}: {value!r}"
        )

    return value


# ---------------------------------------------------------------------------
# Area-code data
# ---------------------------------------------------------------------------


def build_area_codes(
    features: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """
    Build the area-code dictionary used by the 59-region quiz.

    Each entry includes its player-facing area code and broad prefix so the
    generated data remains useful independently of the GeoJSON.
    """
    if len(features) != EXPECTED_AREA_CODE_COUNT:
        raise ValueError(
            "Unexpected area-code feature count: "
            f"expected {EXPECTED_AREA_CODE_COUNT}, "
            f"got {len(features)}."
        )

    result: dict[str, dict[str, str]] = {}

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Area-code feature {index} has invalid properties."
            )

        label = f"Area-code feature {index}"

        area_code_id = require_string(
            properties,
            "area_code_id",
            label=label,
        )

        area_code = require_string(
            properties,
            "area_code",
            label=label,
        )

        prefix_id = require_string(
            properties,
            "prefix_id",
            label=label,
        )

        prefix = require_string(
            properties,
            "prefix",
            label=label,
        )

        if area_code_id in result:
            raise ValueError(
                f"Duplicate area-code ID: {area_code_id}"
            )

        if area_code != area_code_id:
            raise ValueError(
                f"Area code {area_code_id} has inconsistent "
                f"display value {area_code!r}."
            )

        result[area_code_id] = {
            "name": area_code,
            "prefixId": prefix_id,
            "prefix": prefix,
        }

    return dict(sorted(result.items()))


# ---------------------------------------------------------------------------
# Prefix data
# ---------------------------------------------------------------------------


def build_prefixes(
    features: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """Build the dictionary used by the 9-region prefix quiz."""
    if len(features) != EXPECTED_PREFIX_COUNT:
        raise ValueError(
            "Unexpected prefix feature count: "
            f"expected {EXPECTED_PREFIX_COUNT}, "
            f"got {len(features)}."
        )

    result: dict[str, dict[str, str]] = {}

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Prefix feature {index} has invalid properties."
            )

        label = f"Prefix feature {index}"

        prefix_id = require_string(
            properties,
            "prefix_id",
            label=label,
        )

        prefix = require_string(
            properties,
            "prefix",
            label=label,
        )

        if prefix_id in result:
            raise ValueError(
                f"Duplicate prefix ID: {prefix_id}"
            )

        result[prefix_id] = {
            "name": prefix,
        }

    return dict(sorted(result.items()))


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def ts_string(value: str) -> str:
    """Return a JSON-compatible quoted string for TypeScript output."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_area_codes(
    area_codes: dict[str, dict[str, str]],
) -> str:
    """Render JAPAN_AREA_CODES_BY_ID."""
    lines = [
        "export const JAPAN_AREA_CODES_BY_ID = {",
    ]

    for area_code_id, data in area_codes.items():
        lines.append(
            f"  {ts_string(area_code_id)}: {{"
        )
        lines.append(
            f"    name: {ts_string(data['name'])},"
        )
        lines.append(
            f"    prefixId: {ts_string(data['prefixId'])},"
        )
        lines.append(
            f"    prefix: {ts_string(data['prefix'])},"
        )
        lines.append("  },")

    lines.append("} as const;")

    return "\n".join(lines)


def render_prefixes(
    prefixes: dict[str, dict[str, str]],
) -> str:
    """Render JAPAN_AREA_CODE_PREFIXES_BY_ID."""
    lines = [
        "export const JAPAN_AREA_CODE_PREFIXES_BY_ID = {",
    ]

    for prefix_id, data in prefixes.items():
        lines.append(
            f"  {ts_string(prefix_id)}: {{"
        )
        lines.append(
            f"    name: {ts_string(data['name'])},"
        )
        lines.append("  },")

    lines.append("} as const;")

    return "\n".join(lines)


def render_typescript(
    area_codes: dict[str, dict[str, str]],
    prefixes: dict[str, dict[str, str]],
) -> str:
    """Render the complete generated TypeScript module."""
    header = """/**
 * GENERATED FILE — DO NOT EDIT MANUALLY.
 *
 * Quiz data for Japan's telephone area-code geography.
 *
 * Regenerate with:
 *   python scripts/countries/japan/generate/area-code-quiz-data.py
 */
"""

    sections = [
        header.rstrip(),
        render_area_codes(area_codes),
        render_prefixes(prefixes),
    ]

    return "\n\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate Japan's telephone area-code quiz data."""
    print("Generating Japan area-code quiz data...")
    print()

    area_code_features = load_features(
        AREA_CODES_PATH
    )

    prefix_features = load_features(
        PREFIXES_PATH
    )

    area_codes = build_area_codes(
        area_code_features
    )

    prefixes = build_prefixes(
        prefix_features
    )

    output = render_typescript(
        area_codes,
        prefixes,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print("Japan area-code quiz-data generation complete.")
    print()
    print(
        f"  Area codes: {len(area_codes)}"
    )
    print(
        f"  Prefixes:   {len(prefixes)}"
    )
    print()
    print(f"Output: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()