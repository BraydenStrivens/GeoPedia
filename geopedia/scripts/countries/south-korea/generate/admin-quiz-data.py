"""
Generate reusable South Korea administrative quiz-support data from GeoPedia's
canonical intermediate administrative GeoJSON files.

Province, municipality, and submunicipality geometry remains in the runtime
GeoJSON files. This generated module contains only names, native names, display
names, and hierarchy metadata needed by quiz configurations.

Duplicate municipality names are disambiguated independently in romanized
Korean and Korean using their parent province.

Duplicate submunicipality names are disambiguated progressively:
1. The municipality is added when the name is duplicated globally.
2. The province is also added when the municipality-qualified display would
   still be duplicated.

Romanized Korean administrative names are preserved exactly as supplied by the
canonical administrative data. Suffixes such as -do, -si, -gun, -gu, -eup,
-myeon, and -dong are intentionally not translated.

Inputs:
    data/intermediate/countries/south-korea/geojson/provinces.geojson
    data/intermediate/countries/south-korea/geojson/municipalities.geojson
    data/intermediate/countries/south-korea/geojson/submunicipalities.geojson

Output:
    src/quiz/quizzes/countries/asia/south-korea/data/admin.ts
"""

import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "south-korea"
    / "geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "asia"
    / "south-korea"
    / "data"
    / "admin.ts"
)

PROVINCES_INPUT = INPUT_DIR / "provinces.geojson"

MUNICIPALITIES_INPUT = (
    INPUT_DIR / "municipalities.geojson"
)

SUBMUNICIPALITIES_INPUT = (
    INPUT_DIR / "submunicipalities.geojson"
)

EXPECTED_PROVINCE_COUNT = 17
EXPECTED_MUNICIPALITY_COUNT = 250
EXPECTED_SUBMUNICIPALITY_COUNT = 3504


def load_features(
    path: Path,
    expected_count: int,
) -> list[dict]:
    """Load and validate features from a canonical GeoJSON file."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features", [])

    if len(features) != expected_count:
        raise ValueError(
            f"{path.name} has {len(features)} features; "
            f"expected {expected_count}."
        )

    return features


def require_string(
    properties: dict,
    key: str,
    level: str,
) -> str:
    """Read and validate one required canonical string property."""

    value = properties.get(key)

    if not isinstance(value, str) or not value:
        raise ValueError(
            f"{level} feature has invalid {key}: "
            f"{value!r}"
        )

    return value


def ts_string(value: str) -> str:
    """Serialize a string using JSON-compatible TypeScript syntax."""

    return json.dumps(
        value,
        ensure_ascii=False,
    )


def build_provinces(
    features: list[dict],
) -> list[dict[str, str]]:
    """Extract and validate province quiz metadata."""

    provinces = []
    seen_ids = set()
    seen_names = set()
    seen_native_names = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        province_id = require_string(
            properties,
            "province_id",
            "Province",
        )

        province = require_string(
            properties,
            "province",
            "Province",
        )

        native_province = require_string(
            properties,
            "native_province",
            "Province",
        )

        if province_id in seen_ids:
            raise ValueError(
                f"Duplicate province ID: {province_id}"
            )

        if province in seen_names:
            raise ValueError(
                f"Duplicate province name: {province}"
            )

        if native_province in seen_native_names:
            raise ValueError(
                "Duplicate native province name: "
                f"{native_province}"
            )

        seen_ids.add(province_id)
        seen_names.add(province)
        seen_native_names.add(
            native_province
        )

        provinces.append(
            {
                "id": province_id,
                "name": province,
                "nativeName": native_province,
            }
        )

    return sorted(
        provinces,
        key=lambda item: item["name"],
    )


def build_municipalities(
    features: list[dict],
) -> list[dict[str, str]]:
    """
    Extract municipality metadata and create language-specific displays.

    Duplicate romanized municipality names receive their romanized province
    name. Duplicate Korean municipality names independently receive their
    Korean province name.
    """

    municipalities = []
    seen_ids = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        municipality_id = require_string(
            properties,
            "municipality_id",
            "Municipality",
        )

        municipality = require_string(
            properties,
            "municipality",
            "Municipality",
        )

        native_municipality = require_string(
            properties,
            "native_municipality",
            "Municipality",
        )

        province_id = require_string(
            properties,
            "province_id",
            "Municipality",
        )

        province = require_string(
            properties,
            "province",
            "Municipality",
        )

        native_province = require_string(
            properties,
            "native_province",
            "Municipality",
        )

        if municipality_id in seen_ids:
            raise ValueError(
                "Duplicate municipality ID: "
                f"{municipality_id}"
            )

        seen_ids.add(municipality_id)

        municipalities.append(
            {
                "id": municipality_id,
                "name": municipality,
                "display": municipality,
                "nativeName": native_municipality,
                "nativeDisplay": native_municipality,
                "provinceId": province_id,
                "province": province,
                "nativeProvince": native_province,
            }
        )

    romanized_counts = Counter(
        item["name"]
        for item in municipalities
    )

    native_counts = Counter(
        item["nativeName"]
        for item in municipalities
    )

    for item in municipalities:
        if romanized_counts[item["name"]] > 1:
            item["display"] = (
                f"{item['name']} "
                f"({item['province']})"
            )

        if native_counts[item["nativeName"]] > 1:
            item["nativeDisplay"] = (
                f"{item['nativeName']} "
                f"({item['nativeProvince']})"
            )

    return sorted(
        municipalities,
        key=lambda item: (
            item["province"],
            item["name"],
            item["id"],
        ),
    )


def build_submunicipalities(
    features: list[dict],
) -> list[dict[str, str]]:
    """
    Extract submunicipality metadata and create language-specific displays.

    Duplicate names first receive their municipality. If those displays are
    still duplicated, the province is also included.

    Romanized and Korean displays are disambiguated independently because the
    duplicate sets are not necessarily identical between the two languages.
    """

    submunicipalities = []
    seen_ids = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        submunicipality_id = require_string(
            properties,
            "submunicipality_id",
            "Submunicipality",
        )

        submunicipality = require_string(
            properties,
            "submunicipality",
            "Submunicipality",
        )

        native_submunicipality = require_string(
            properties,
            "native_submunicipality",
            "Submunicipality",
        )

        municipality_id = require_string(
            properties,
            "municipality_id",
            "Submunicipality",
        )

        municipality = require_string(
            properties,
            "municipality",
            "Submunicipality",
        )

        native_municipality = require_string(
            properties,
            "native_municipality",
            "Submunicipality",
        )

        province_id = require_string(
            properties,
            "province_id",
            "Submunicipality",
        )

        province = require_string(
            properties,
            "province",
            "Submunicipality",
        )

        native_province = require_string(
            properties,
            "native_province",
            "Submunicipality",
        )

        if submunicipality_id in seen_ids:
            raise ValueError(
                "Duplicate submunicipality ID: "
                f"{submunicipality_id}"
            )

        seen_ids.add(
            submunicipality_id
        )

        submunicipalities.append(
            {
                "id": submunicipality_id,
                "name": submunicipality,
                "display": submunicipality,
                "nativeName": native_submunicipality,
                "nativeDisplay": native_submunicipality,
                "municipalityId": municipality_id,
                "municipality": municipality,
                "nativeMunicipality": native_municipality,
                "provinceId": province_id,
                "province": province,
                "nativeProvince": native_province,
            }
        )

    romanized_name_counts = Counter(
        item["name"]
        for item in submunicipalities
    )

    native_name_counts = Counter(
        item["nativeName"]
        for item in submunicipalities
    )

    # First disambiguation level:
    # add the municipality to globally duplicated names.
    for item in submunicipalities:
        if romanized_name_counts[item["name"]] > 1:
            item["display"] = (
                f"{item['name']} "
                f"({item['municipality']})"
            )

        if native_name_counts[item["nativeName"]] > 1:
            item["nativeDisplay"] = (
                f"{item['nativeName']} "
                f"({item['nativeMunicipality']})"
            )

    # Some municipality names are themselves duplicated across provinces.
    # Count the resulting displays to determine which entries still need the
    # province included.
    romanized_display_counts = Counter(
        item["display"]
        for item in submunicipalities
    )

    native_display_counts = Counter(
        item["nativeDisplay"]
        for item in submunicipalities
    )

    for item in submunicipalities:
        if (
            romanized_display_counts[
                item["display"]
            ]
            > 1
        ):
            item["display"] = (
                f"{item['name']} "
                f"({item['municipality']}, "
                f"{item['province']})"
            )

        if (
            native_display_counts[
                item["nativeDisplay"]
            ]
            > 1
        ):
            item["nativeDisplay"] = (
                f"{item['nativeName']} "
                f"({item['nativeMunicipality']}, "
                f"{item['nativeProvince']})"
            )

    return sorted(
        submunicipalities,
        key=lambda item: (
            item["province"],
            item["municipality"],
            item["name"],
            item["id"],
        ),
    )


def render_provinces(
    provinces: list[dict[str, str]],
) -> str:
    """Render the province lookup as TypeScript."""

    lines = [
        "export const SOUTH_KOREA_PROVINCES_BY_ID = {",
    ]

    for item in provinces:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                (
                    "    nativeName: "
                    f"{ts_string(item['nativeName'])},"
                ),
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def render_municipalities(
    municipalities: list[dict[str, str]],
) -> str:
    """Render the municipality lookup as TypeScript."""

    lines = [
        "export const SOUTH_KOREA_MUNICIPALITIES_BY_ID = {",
    ]

    for item in municipalities:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                (
                    "    display: "
                    f"{ts_string(item['display'])},"
                ),
                (
                    "    nativeName: "
                    f"{ts_string(item['nativeName'])},"
                ),
                (
                    "    nativeDisplay: "
                    f"{ts_string(item['nativeDisplay'])},"
                ),
                (
                    "    provinceId: "
                    f"{ts_string(item['provinceId'])},"
                ),
                (
                    "    province: "
                    f"{ts_string(item['province'])},"
                ),
                (
                    "    nativeProvince: "
                    f"{ts_string(item['nativeProvince'])},"
                ),
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def render_submunicipalities(
    submunicipalities: list[dict[str, str]],
) -> str:
    """Render the submunicipality lookup as TypeScript."""

    lines = [
        "export const SOUTH_KOREA_SUBMUNICIPALITIES_BY_ID = {",
    ]

    for item in submunicipalities:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                (
                    "    display: "
                    f"{ts_string(item['display'])},"
                ),
                (
                    "    nativeName: "
                    f"{ts_string(item['nativeName'])},"
                ),
                (
                    "    nativeDisplay: "
                    f"{ts_string(item['nativeDisplay'])},"
                ),
                (
                    "    municipalityId: "
                    f"{ts_string(item['municipalityId'])},"
                ),
                (
                    "    municipality: "
                    f"{ts_string(item['municipality'])},"
                ),
                (
                    "    nativeMunicipality: "
                    f"{ts_string(item['nativeMunicipality'])},"
                ),
                (
                    "    provinceId: "
                    f"{ts_string(item['provinceId'])},"
                ),
                (
                    "    province: "
                    f"{ts_string(item['province'])},"
                ),
                (
                    "    nativeProvince: "
                    f"{ts_string(item['nativeProvince'])},"
                ),
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def write_output(
    provinces: list[dict[str, str]],
    municipalities: list[dict[str, str]],
    submunicipalities: list[dict[str, str]],
) -> None:
    """Write the generated TypeScript quiz-support module."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = f"""/**
 * Generated South Korea administrative quiz-support data.
 *
 * Do not edit this file manually.
 *
 * Regenerate with:
 *   python scripts/countries/south-korea/generate/admin-quiz-data.py
 */

{render_provinces(provinces)}

{render_municipalities(municipalities)}

{render_submunicipalities(submunicipalities)}
"""

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )


def count_duplicate_values(
    items: list[dict[str, str]],
    key: str,
) -> int:
    """Count distinct values that occur more than once."""

    return sum(
        1
        for count in Counter(
            item[key]
            for item in items
        ).values()
        if count > 1
    )


def count_disambiguated_values(
    items: list[dict[str, str]],
    name_key: str,
    display_key: str,
) -> int:
    """Count entries whose display differs from their canonical name."""

    return sum(
        1
        for item in items
        if item[display_key] != item[name_key]
    )


def count_duplicate_displays(
    items: list[dict[str, str]],
    key: str,
) -> int:
    """Count distinct generated displays that still occur more than once."""

    return count_duplicate_values(
        items,
        key,
    )


def main() -> None:
    """Generate South Korea's reusable administrative quiz metadata."""

    print(
        "Generating South Korea administrative "
        "quiz data..."
    )
    print()

    province_features = load_features(
        PROVINCES_INPUT,
        EXPECTED_PROVINCE_COUNT,
    )

    municipality_features = load_features(
        MUNICIPALITIES_INPUT,
        EXPECTED_MUNICIPALITY_COUNT,
    )

    submunicipality_features = load_features(
        SUBMUNICIPALITIES_INPUT,
        EXPECTED_SUBMUNICIPALITY_COUNT,
    )

    provinces = build_provinces(
        province_features
    )

    municipalities = build_municipalities(
        municipality_features
    )

    submunicipalities = build_submunicipalities(
        submunicipality_features
    )

    write_output(
        provinces,
        municipalities,
        submunicipalities,
    )

    municipality_duplicate_romanized = (
        count_duplicate_values(
            municipalities,
            "name",
        )
    )

    municipality_duplicate_native = (
        count_duplicate_values(
            municipalities,
            "nativeName",
        )
    )

    municipality_disambiguated_romanized = (
        count_disambiguated_values(
            municipalities,
            "name",
            "display",
        )
    )

    municipality_disambiguated_native = (
        count_disambiguated_values(
            municipalities,
            "nativeName",
            "nativeDisplay",
        )
    )

    submunicipality_duplicate_romanized = (
        count_duplicate_values(
            submunicipalities,
            "name",
        )
    )

    submunicipality_duplicate_native = (
        count_duplicate_values(
            submunicipalities,
            "nativeName",
        )
    )

    submunicipality_disambiguated_romanized = (
        count_disambiguated_values(
            submunicipalities,
            "name",
            "display",
        )
    )

    submunicipality_disambiguated_native = (
        count_disambiguated_values(
            submunicipalities,
            "nativeName",
            "nativeDisplay",
        )
    )

    remaining_romanized_displays = (
        count_duplicate_displays(
            submunicipalities,
            "display",
        )
    )

    remaining_native_displays = (
        count_duplicate_displays(
            submunicipalities,
            "nativeDisplay",
        )
    )

    print(
        "South Korea administrative quiz-data "
        "generation complete."
    )
    print(
        f"  Provinces:                           "
        f"{len(provinces)}"
    )
    print(
        f"  Municipalities:                      "
        f"{len(municipalities)}"
    )
    print(
        f"  Submunicipalities:                   "
        f"{len(submunicipalities)}"
    )

    print()
    print("Municipalities:")
    print(
        "  Duplicate romanized names:           "
        f"{municipality_duplicate_romanized}"
    )
    print(
        "  Disambiguated romanized entries:     "
        f"{municipality_disambiguated_romanized}"
    )
    print(
        "  Duplicate Korean names:              "
        f"{municipality_duplicate_native}"
    )
    print(
        "  Disambiguated Korean entries:        "
        f"{municipality_disambiguated_native}"
    )

    print()
    print("Submunicipalities:")
    print(
        "  Duplicate romanized names:           "
        f"{submunicipality_duplicate_romanized}"
    )
    print(
        "  Disambiguated romanized entries:     "
        f"{submunicipality_disambiguated_romanized}"
    )
    print(
        "  Duplicate Korean names:              "
        f"{submunicipality_duplicate_native}"
    )
    print(
        "  Disambiguated Korean entries:        "
        f"{submunicipality_disambiguated_native}"
    )
    print(
        "  Remaining duplicate romanized "
        "displays: "
        f"{remaining_romanized_displays}"
    )
    print(
        "  Remaining duplicate Korean displays: "
        f"{remaining_native_displays}"
    )

    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()