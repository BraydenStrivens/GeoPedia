"""
Generate reusable Japan administrative quiz-support data from GeoPedia's
canonical intermediate administrative GeoJSON files.

Region, prefecture, and municipality geometry remains in the runtime GeoJSON
files. This generated module contains only names, native names, display names,
and hierarchy metadata needed by quiz configurations.

Duplicate municipality names are disambiguated independently in English and
Japanese using their parent prefecture. If identically named municipalities
remain within the same prefecture, their displays remain identical because the
available administrative hierarchy provides no truthful way to distinguish
them further.

Inputs:
    data/intermediate/countries/japan/geojson/regions.geojson
    data/intermediate/countries/japan/geojson/prefectures.geojson
    data/intermediate/countries/japan/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/countries/asia/japan/data/admin.ts
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
    / "japan"
    / "geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "asia"
    / "japan"
    / "data"
    / "admin.ts"
)

REGIONS_INPUT = INPUT_DIR / "regions.geojson"
PREFECTURES_INPUT = INPUT_DIR / "prefectures.geojson"
MUNICIPALITIES_INPUT = INPUT_DIR / "municipalities.geojson"

EXPECTED_REGION_COUNT = 9
EXPECTED_PREFECTURE_COUNT = 47
EXPECTED_MUNICIPALITY_COUNT = 1892


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
            f"{level} feature has invalid {key}: {value!r}"
        )

    return value


def ts_string(value: str) -> str:
    """Serialize a string using JSON-compatible TypeScript syntax."""

    return json.dumps(
        value,
        ensure_ascii=False,
    )


def build_regions(
    features: list[dict],
) -> list[dict[str, str]]:
    """Extract and validate region quiz metadata."""

    regions = []
    seen_ids = set()
    seen_names = set()
    seen_native_names = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        region_id = require_string(
            properties,
            "region_id",
            "Region",
        )

        region = require_string(
            properties,
            "region",
            "Region",
        )

        native_region = require_string(
            properties,
            "native_region",
            "Region",
        )

        if region_id in seen_ids:
            raise ValueError(
                f"Duplicate region ID: {region_id}"
            )

        if region in seen_names:
            raise ValueError(
                f"Duplicate region name: {region}"
            )

        if native_region in seen_native_names:
            raise ValueError(
                f"Duplicate native region name: {native_region}"
            )

        seen_ids.add(region_id)
        seen_names.add(region)
        seen_native_names.add(native_region)

        regions.append(
            {
                "id": region_id,
                "name": region,
                "nativeName": native_region,
            }
        )

    return sorted(
        regions,
        key=lambda item: item["name"],
    )


def build_prefectures(
    features: list[dict],
) -> list[dict[str, str]]:
    """Extract and validate prefecture quiz and hierarchy metadata."""

    prefectures = []
    seen_ids = set()
    seen_names = set()
    seen_native_names = set()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        prefecture_id = require_string(
            properties,
            "prefecture_id",
            "Prefecture",
        )

        prefecture = require_string(
            properties,
            "prefecture",
            "Prefecture",
        )

        native_prefecture = require_string(
            properties,
            "native_prefecture",
            "Prefecture",
        )

        region_id = require_string(
            properties,
            "region_id",
            "Prefecture",
        )

        region = require_string(
            properties,
            "region",
            "Prefecture",
        )

        native_region = require_string(
            properties,
            "native_region",
            "Prefecture",
        )

        if prefecture_id in seen_ids:
            raise ValueError(
                f"Duplicate prefecture ID: {prefecture_id}"
            )

        if prefecture in seen_names:
            raise ValueError(
                f"Duplicate prefecture name: {prefecture}"
            )

        if native_prefecture in seen_native_names:
            raise ValueError(
                "Duplicate native prefecture name: "
                f"{native_prefecture}"
            )

        seen_ids.add(prefecture_id)
        seen_names.add(prefecture)
        seen_native_names.add(native_prefecture)

        prefectures.append(
            {
                "id": prefecture_id,
                "name": prefecture,
                "nativeName": native_prefecture,
                "regionId": region_id,
                "region": region,
                "nativeRegion": native_region,
            }
        )

    return sorted(
        prefectures,
        key=lambda item: (
            item["region"],
            item["name"],
        ),
    )


def build_municipalities(
    features: list[dict],
) -> list[dict[str, str]]:
    """
    Extract municipality metadata and create language-specific displays.

    Duplicate English municipality names receive their English prefecture
    name. Duplicate Japanese municipality names independently receive their
    Japanese prefecture name.

    If duplicates remain within the same prefecture, their displays remain
    identical because the available hierarchy provides no truthful additional
    distinction.
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

        prefecture_id = require_string(
            properties,
            "prefecture_id",
            "Municipality",
        )

        prefecture = require_string(
            properties,
            "prefecture",
            "Municipality",
        )

        native_prefecture = require_string(
            properties,
            "native_prefecture",
            "Municipality",
        )

        region_id = require_string(
            properties,
            "region_id",
            "Municipality",
        )

        region = require_string(
            properties,
            "region",
            "Municipality",
        )

        native_region = require_string(
            properties,
            "native_region",
            "Municipality",
        )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id}"
            )

        seen_ids.add(municipality_id)

        municipalities.append(
            {
                "id": municipality_id,
                "name": municipality,
                "display": municipality,
                "nativeName": native_municipality,
                "nativeDisplay": native_municipality,
                "prefectureId": prefecture_id,
                "prefecture": prefecture,
                "nativePrefecture": native_prefecture,
                "regionId": region_id,
                "region": region,
                "nativeRegion": native_region,
            }
        )

    english_counts = Counter(
        item["name"]
        for item in municipalities
    )

    native_counts = Counter(
        item["nativeName"]
        for item in municipalities
    )

    for item in municipalities:
        if english_counts[item["name"]] > 1:
            item["display"] = (
                f"{item['name']} "
                f"({item['prefecture']})"
            )

        if native_counts[item["nativeName"]] > 1:
            item["nativeDisplay"] = (
                f"{item['nativeName']} "
                f"({item['nativePrefecture']})"
            )

    return sorted(
        municipalities,
        key=lambda item: (
            item["region"],
            item["prefecture"],
            item["name"],
        ),
    )


def render_regions(
    regions: list[dict[str, str]],
) -> str:
    """Render the region lookup as TypeScript."""

    lines = [
        "export const JAPAN_REGIONS_BY_ID = {",
    ]

    for item in regions:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    nativeName: {ts_string(item['nativeName'])},",
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def render_prefectures(
    prefectures: list[dict[str, str]],
) -> str:
    """Render the prefecture lookup as TypeScript."""

    lines = [
        "export const JAPAN_PREFECTURES_BY_ID = {",
    ]

    for item in prefectures:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    nativeName: {ts_string(item['nativeName'])},",
                f"    regionId: {ts_string(item['regionId'])},",
                f"    region: {ts_string(item['region'])},",
                f"    nativeRegion: {ts_string(item['nativeRegion'])},",
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
        "export const JAPAN_MUNICIPALITIES_BY_ID = {",
    ]

    for item in municipalities:
        lines.extend(
            [
                f"  {ts_string(item['id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    display: {ts_string(item['display'])},",
                f"    nativeName: {ts_string(item['nativeName'])},",
                f"    nativeDisplay: {ts_string(item['nativeDisplay'])},",
                f"    prefectureId: {ts_string(item['prefectureId'])},",
                f"    prefecture: {ts_string(item['prefecture'])},",
                (
                    "    nativePrefecture: "
                    f"{ts_string(item['nativePrefecture'])},"
                ),
                f"    regionId: {ts_string(item['regionId'])},",
                f"    region: {ts_string(item['region'])},",
                f"    nativeRegion: {ts_string(item['nativeRegion'])},",
                "  },",
            ]
        )

    lines.append("} as const;")

    return "\n".join(lines)


def write_output(
    regions: list[dict[str, str]],
    prefectures: list[dict[str, str]],
    municipalities: list[dict[str, str]],
) -> None:
    """Write the generated TypeScript quiz-support module."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = f"""/**
 * Generated Japan administrative quiz-support data.
 *
 * Do not edit this file manually.
 *
 * Regenerate with:
 *   python scripts/countries/japan/generate/admin-quiz-data.py
 */

{render_regions(regions)}

{render_prefectures(prefectures)}

{render_municipalities(municipalities)}
"""

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )


def main() -> None:
    """Generate Japan's reusable administrative quiz metadata."""

    print("Generating Japan administrative quiz data...")
    print()

    region_features = load_features(
        REGIONS_INPUT,
        EXPECTED_REGION_COUNT,
    )

    prefecture_features = load_features(
        PREFECTURES_INPUT,
        EXPECTED_PREFECTURE_COUNT,
    )

    municipality_features = load_features(
        MUNICIPALITIES_INPUT,
        EXPECTED_MUNICIPALITY_COUNT,
    )

    regions = build_regions(
        region_features
    )

    prefectures = build_prefectures(
        prefecture_features
    )

    municipalities = build_municipalities(
        municipality_features
    )

    write_output(
        regions,
        prefectures,
        municipalities,
    )

    duplicate_english_names = sum(
        1
        for count in Counter(
            item["name"]
            for item in municipalities
        ).values()
        if count > 1
    )

    duplicate_native_names = sum(
        1
        for count in Counter(
            item["nativeName"]
            for item in municipalities
        ).values()
        if count > 1
    )

    disambiguated_english = sum(
        1
        for item in municipalities
        if item["display"] != item["name"]
    )

    disambiguated_native = sum(
        1
        for item in municipalities
        if item["nativeDisplay"] != item["nativeName"]
    )

    print(
        "Japan administrative quiz-data "
        "generation complete."
    )
    print(
        f"  Regions:                       {len(regions)}"
    )
    print(
        f"  Prefectures:                   {len(prefectures)}"
    )
    print(
        f"  Municipalities:                {len(municipalities)}"
    )
    print(
        "  Duplicate English names:       "
        f"{duplicate_english_names}"
    )
    print(
        "  Disambiguated English entries: "
        f"{disambiguated_english}"
    )
    print(
        "  Duplicate Japanese names:      "
        f"{duplicate_native_names}"
    )
    print(
        "  Disambiguated Japanese entries:"
        f" {disambiguated_native}"
    )
    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()