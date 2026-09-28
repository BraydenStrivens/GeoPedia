"""
Generate Ghana postcode quiz data from the researched postcode-district mapping
and GeoPedia's canonical administrative data.

The postcode source uses several district names that differ from GeoPedia's
canonical geoBoundaries names. Explicit aliases reconcile those differences
without modifying either source dataset.

The source also contains Guan (OG), which has no corresponding feature in
GeoPedia's current Ghana district boundaries and is intentionally excluded.

Inputs
------
data/raw/countries/ghana/postcode-districts.csv
data/intermediate/countries/ghana/admin/regions.geojson
data/intermediate/countries/ghana/admin/districts.geojson

Output
------
src/quiz/quizzes/countries/africa/ghana/data/postcodes.ts

Run
---
python scripts/countries/ghana/generate/postcode-quiz-data.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path
import re
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[4]

POSTCODE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "ghana"
    / "postcode-districts.csv"
)

REGIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ghana"
    / "admin"
    / "regions.geojson"
)

DISTRICTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "ghana"
    / "admin"
    / "districts.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "ghana"
    / "data"
    / "postcodes.ts"
)


EXPECTED_REGION_COUNT = 16
EXPECTED_DISTRICT_COUNT = 260
EXPECTED_SOURCE_POSTCODE_COUNT = 261
EXPECTED_UNUSED_POSTCODE_CODES = {"OG"}

# Administrative suffixes commonly included by geoBoundaries but omitted from
# the postcode source. These are ignored only while matching names; neither
# source dataset is modified.
ADMIN_SUFFIXES = {
    "district",
    "municipal",
    "municipality",
    "metropolitan",
    "metropolis",
    "assembly",
}


def normalize_name(value: str) -> str:
    """
    Normalize an administrative name for matching without modifying the
    original source value.

    Matching ignores capitalization, diacritics, punctuation, whitespace,
    and common administrative suffixes. Explicit aliases handle the remaining
    genuine naming differences between the two datasets.
    """
    value = unicodedata.normalize(
        "NFKD",
        value,
    )

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

    words = [
        word
        for word in value.split()
        if word not in ADMIN_SUFFIXES
    ]

    return " ".join(words)


# The postcode source and geoBoundaries represent the same districts using
# different names in these cases. Keys are (region, postcode-source name);
# values are GeoPedia's canonical district names.
DISTRICT_NAME_ALIASES = {
    ("Ashanti Region", "Akrofuom"): "Adansi Akrofuom",
    ("Ashanti Region", "Afigya Kwabre"): "Afigya Kwabre South",
    ("Ashanti Region", "Atwima Nwabiagya"): "Atwima Nwabiagya South",
    ("Ashanti Region", "Offinso South"): "Offinso Municipal",
    ("Ashanti Region", "Sekyere Afram Plains"): "Sekyere Afram Plains North",

    ("Bono Region", "Dormaa Central"): "Dormaa Municipal",

    ("Central Region", "Ajumako Enyan Esiam"): "Ajumako-enyan-essiam",
    ("Central Region", "Assin Central"): "Assin Fosu",
    ("Central Region", "Awutu Senya West"): "Awutu Senya",
    (
        "Central Region",
        "Komenda Edina Eguafo",
    ): "Komenda-edina-eguafo-abirem Municipal",
    ("Central Region", "Twifo Ati-Morkwa"): "Twifo Atti-morkwa",
    (
        "Central Region",
        "Hemang Lower Denkyira",
    ): "Twifo Hemang Lower Denkyira",

    ("Eastern Region", "Akuapem North"): "Akwapem North",
    ("Eastern Region", "Akuapem South"): "Akwapem South",
    ("Eastern Region", "Akyemansa"): "Akyem Mansa",
    ("Eastern Region", "Asene Manso Akroso"): "Asene Akroso Manso",
    ("Eastern Region", "Lower Manya Krobo"): "Lower Manya",
    ("Eastern Region", "Upper Manya Krobo"): "Upper Manya",

    ("Greater Accra Region", "Adentan"): "Adenta Municipal",

    ("North East Region", "Mamprugu Moaduri"): "Mamprugu Moagduri",

    ("Northern Region", "Gushiegu"): "Gushegu",
    ("Northern Region", "Tatale Sangule"): "Tatale Sanguli",

    ("Upper East Region", "Bolgatanga East"): "Bolga  East",
    (
        "Upper East Region",
        "Kassena Nankana East",
    ): "Kasena Nankana East",
    (
        "Upper East Region",
        "Kassena Nankana West",
    ): "Kasena Nankana West",

    ("Volta Region", "Afadjato South"): "Afadzato South",

    (
        "Western Region",
        "Effia Kwesimintim",
    ): "Effia Kwesimintsim Municipal",
}


def load_geojson(path: Path) -> dict:
    """Load a GeoJSON file."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_postcodes() -> list[dict[str, str]]:
    """Load and validate the researched postcode-district CSV."""
    if not POSTCODE_PATH.exists():
        raise FileNotFoundError(
            f"Postcode CSV not found: {POSTCODE_PATH}"
        )

    with POSTCODE_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        expected_fields = {
            "region",
            "district",
            "postcode_district_code",
        }

        if reader.fieldnames is None:
            raise ValueError(
                "Postcode CSV has no header."
            )

        missing_fields = (
            expected_fields
            - set(reader.fieldnames)
        )

        if missing_fields:
            raise ValueError(
                "Postcode CSV is missing fields: "
                f"{sorted(missing_fields)}"
            )

        rows = []

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            cleaned = {
                key: (row.get(key) or "").strip()
                for key in expected_fields
            }

            if not all(cleaned.values()):
                raise ValueError(
                    "Blank postcode value on CSV row "
                    f"{row_number}: {cleaned}"
                )

            rows.append(cleaned)

    if len(rows) != EXPECTED_SOURCE_POSTCODE_COUNT:
        raise ValueError(
            "Unexpected postcode source row count: "
            f"{len(rows)} "
            f"(expected {EXPECTED_SOURCE_POSTCODE_COUNT})"
        )

    codes = [
        row["postcode_district_code"]
        for row in rows
    ]

    if len(codes) != len(set(codes)):
        duplicates = sorted(
            {
                code
                for code in codes
                if codes.count(code) > 1
            }
        )

        raise ValueError(
            "Duplicate postcode district codes: "
            f"{duplicates}"
        )

    return rows


def get_features(
    geojson: dict,
    expected_count: int,
    label: str,
) -> list[dict]:
    """Return and validate the feature array of a canonical GeoJSON."""
    features = geojson.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{label} GeoJSON has no valid feature array."
        )

    if len(features) != expected_count:
        raise ValueError(
            f"Unexpected {label} feature count: "
            f"{len(features)} "
            f"(expected {expected_count})"
        )

    return features


def get_properties(
    feature: dict,
    required: set[str],
    label: str,
) -> dict:
    """Return a feature's properties after validating required values."""
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            f"{label} feature has no valid properties."
        )

    missing = [
        key
        for key in required
        if not properties.get(key)
    ]

    if missing:
        raise ValueError(
            f"{label} feature is missing values "
            f"for {missing}: {properties}"
        )

    return properties


def ts_string(value: str) -> str:
    """Encode a Python string as a TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def build_region_data(
    region_features: list[dict],
    postcode_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """
    Derive one first-character postcode prefix for each canonical region.
    """
    prefixes_by_region: dict[str, set[str]] = defaultdict(set)

    for row in postcode_rows:
        prefixes_by_region[
            row["region"]
        ].add(
            row["postcode_district_code"][0]
        )

    canonical_regions = []

    for feature in region_features:
        properties = get_properties(
            feature,
            {"region_id", "region"},
            "Region",
        )

        region_id = properties["region_id"]
        region = properties["region"]

        prefixes = prefixes_by_region.get(
            region,
            set(),
        )

        if len(prefixes) != 1:
            raise ValueError(
                f"Region {region!r} has "
                f"{len(prefixes)} postcode prefixes: "
                f"{sorted(prefixes)}"
            )

        canonical_regions.append(
            {
                "region_id": region_id,
                "name": region,
                "prefix": next(iter(prefixes)),
            }
        )

    source_regions = set(
        prefixes_by_region
    )

    canonical_region_names = {
        item["name"]
        for item in canonical_regions
    }

    extra_regions = (
        source_regions
        - canonical_region_names
    )

    if extra_regions:
        raise ValueError(
            "Postcode source contains unknown regions: "
            f"{sorted(extra_regions)}"
        )

    if len(canonical_regions) != EXPECTED_REGION_COUNT:
        raise ValueError(
            "Unexpected generated region count: "
            f"{len(canonical_regions)}"
        )

    prefixes = [
        item["prefix"]
        for item in canonical_regions
    ]

    if len(prefixes) != len(set(prefixes)):
        raise ValueError(
            "Regional postcode prefixes are not unique."
        )

    return sorted(
        canonical_regions,
        key=lambda item: item["name"],
    )


def build_district_data(
    district_features: list[dict],
    postcode_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Match postcode rows to canonical districts.

    Names are first normalized to ignore superficial differences such as
    punctuation and administrative suffixes. Explicit aliases handle the
    remaining known naming differences between the postcode source and
    GeoPedia's canonical geoBoundaries data.
    """
    canonical_by_key: dict[
        tuple[str, str],
        dict[str, str],
    ] = {}

    for feature in district_features:
        properties = get_properties(
            feature,
            {
                "district_id",
                "district",
                "region_id",
                "region",
            },
            "District",
        )

        key = (
            normalize_name(properties["region"]),
            normalize_name(properties["district"]),
        )

        if key in canonical_by_key:
            previous = canonical_by_key[key]

            raise ValueError(
                "Canonical district normalization collision: "
                f"{previous['region']} | {previous['name']} and "
                f"{properties['region']} | {properties['district']}"
            )

        canonical_by_key[key] = {
            "district_id": properties["district_id"],
            "name": properties["district"],
            "region_id": properties["region_id"],
            "region": properties["region"],
        }

    matched_by_district_id: dict[
        str,
        dict[str, str],
    ] = {}

    unused_rows = []

    for row in postcode_rows:
        source_key = (
            row["region"],
            row["district"],
        )

        canonical_name = DISTRICT_NAME_ALIASES.get(
            source_key,
            row["district"],
        )

        canonical_key = (
            normalize_name(row["region"]),
            normalize_name(canonical_name),
        )

        canonical = canonical_by_key.get(
            canonical_key
        )

        if canonical is None:
            unused_rows.append(row)
            continue

        district_id = canonical["district_id"]

        if district_id in matched_by_district_id:
            previous = matched_by_district_id[
                district_id
            ]

            raise ValueError(
                "Multiple postcode rows matched canonical "
                f"district {canonical['name']!r}: "
                f"{previous['code']!r} and "
                f"{row['postcode_district_code']!r}"
            )

        matched_by_district_id[district_id] = {
            **canonical,
            "code": row["postcode_district_code"],
        }

    canonical_ids = {
        item["district_id"]
        for item in canonical_by_key.values()
    }

    matched_ids = set(
        matched_by_district_id
    )

    missing_ids = (
        canonical_ids
        - matched_ids
    )

    if missing_ids:
        missing = sorted(
            (
                item
                for item in canonical_by_key.values()
                if item["district_id"] in missing_ids
            ),
            key=lambda item: (
                item["region"],
                item["name"],
            ),
        )

        details = "\n".join(
            f"  {item['region']} | "
            f"{item['name']} | "
            f"{item['district_id']}"
            for item in missing
        )

        raise ValueError(
            "Canonical districts without postcode codes:\n"
            f"{details}"
        )

    unused_codes = {
        row["postcode_district_code"]
        for row in unused_rows
    }

    if unused_codes != EXPECTED_UNUSED_POSTCODE_CODES:
        details = "\n".join(
            f"  {row['region']} | "
            f"{row['district']} | "
            f"{row['postcode_district_code']}"
            for row in unused_rows
        )

        raise ValueError(
            "Unexpected unused postcode source entries.\n"
            f"Expected unused codes: "
            f"{sorted(EXPECTED_UNUSED_POSTCODE_CODES)}\n"
            f"Found unused codes: {sorted(unused_codes)}\n"
            f"{details}"
        )

    districts = sorted(
        matched_by_district_id.values(),
        key=lambda item: (
            item["region"],
            item["name"],
        ),
    )

    if len(districts) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected generated district count: "
            f"{len(districts)} "
            f"(expected {EXPECTED_DISTRICT_COUNT})"
        )

    codes = [
        item["code"]
        for item in districts
    ]

    if len(codes) != len(set(codes)):
        raise ValueError(
            "Generated district postcode codes "
            "are not unique."
        )

    return districts, unused_rows
  

def render_typescript(
    regions: list[dict[str, str]],
    districts: list[dict[str, str]],
) -> str:
    """Render the validated postcode metadata as TypeScript."""
    lines = [
        "/**",
        " * Generated Ghana postcode quiz data.",
        " *",
        " * Do not edit this file manually.",
        " *",
        " * Regenerate with:",
        " * python scripts/countries/ghana/generate/postcode-quiz-data.py",
        " */",
        "",
        "export const GHANA_POSTAL_PREFIXES_BY_REGION_ID = {",
    ]

    for item in regions:
        lines.extend(
            [
                f"  {ts_string(item['region_id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    prefix: {ts_string(item['prefix'])},",
                "  },",
            ]
        )

    lines.extend(
        [
            "} as const;",
            "",
            "export const GHANA_POSTCODE_DISTRICTS_BY_ID = {",
        ]
    )

    for item in districts:
        lines.extend(
            [
                f"  {ts_string(item['district_id'])}: {{",
                f"    name: {ts_string(item['name'])},",
                f"    regionId: {ts_string(item['region_id'])},",
                f"    region: {ts_string(item['region'])},",
                f"    code: {ts_string(item['code'])},",
                "  },",
            ]
        )

    lines.extend(
        [
            "} as const;",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Generate Ghana's validated postcode quiz-support data."""
    print(
        "Generating Ghana postcode quiz data..."
    )
    print()

    postcode_rows = load_postcodes()

    regions_geojson = load_geojson(
        REGIONS_PATH
    )

    districts_geojson = load_geojson(
        DISTRICTS_PATH
    )

    region_features = get_features(
        regions_geojson,
        EXPECTED_REGION_COUNT,
        "region",
    )

    district_features = get_features(
        districts_geojson,
        EXPECTED_DISTRICT_COUNT,
        "district",
    )

    regions = build_region_data(
        region_features,
        postcode_rows,
    )

    districts, unused_rows = build_district_data(
        district_features,
        postcode_rows,
    )

    output = render_typescript(
        regions,
        districts,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print(
        "Ghana postcode quiz-data generation complete."
    )
    print(
        f"  Regional prefixes: {len(regions)}"
    )
    print(
        f"  District codes:     {len(districts)}"
    )
    print(
        f"  Source rows unused: {len(unused_rows)}"
    )

    for row in unused_rows:
        print(
            "    "
            f"{row['region']} | "
            f"{row['district']} | "
            f"{row['postcode_district_code']}"
        )

    print()
    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()