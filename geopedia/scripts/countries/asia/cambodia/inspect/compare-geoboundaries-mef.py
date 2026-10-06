"""
Compares Cambodia's MEF administrative units with geoBoundaries features.

MEF provides the administrative IDs and official English/Khmer names.
geoBoundaries provides geometry but lacks MEF parent/code fields at ADM2/ADM3.

The script conservatively matches features by normalized English name and
prints only:
- counts
- unmatched MEF IDs and names
- unmatched geoBoundaries names
- ambiguous names
- a few successful match examples

This is an inspection tool only. Final IDs/names should come from MEF.

Inputs:
    data/raw/countries/cambodia/mef-admin-data.json
    data/raw/countries/cambodia/geoBoundaries-KHM-ADM1.geojson
    data/raw/countries/cambodia/geoBoundaries-KHM-ADM2.geojson
    data/raw/countries/cambodia/geoBoundaries-KHM-ADM3.geojson

Run:
    python scripts/countries/asia/cambodia/inspect/compare-geoboundaries-mef.py
"""
import sys
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


RAW_DIR = Path("data/raw/countries/cambodia")
MEF_PATH = RAW_DIR / "mef-admin-data.json"

EXAMPLE_COUNT = 10

LEVELS = {
    "province": {
        "geo_file": "geoBoundaries-KHM-ADM1.geojson",
        "mef_code": "province_code",
        "mef_en": "province_en",
        "mef_kh": "province_kh",
    },
    "district": {
        "geo_file": "geoBoundaries-KHM-ADM2.geojson",
        "mef_code": "district_code",
        "mef_en": "district_en",
        "mef_kh": "district_kh",
    },
    "commune": {
        "geo_file": "geoBoundaries-KHM-ADM3.geojson",
        "mef_code": "commune_code",
        "mef_en": "commune_en",
        "mef_kh": "commune_kh",
    },
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_name(value: str) -> str:
    """
    Performs conservative formatting normalization only.

    This does not attempt fuzzy romanization matching.
    """
    value = unicodedata.normalize(
        "NFKD",
        str(value or ""),
    ).casefold()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def collect_mef(records, config):
    """
    Deduplicates the village-level MEF dataset by administrative ID.
    """
    entries = {}

    for record in records:
        code = str(
            record.get(config["mef_code"], "")
        ).strip()

        if not code:
            continue

        english = str(
            record.get(config["mef_en"], "")
        ).strip()

        khmer = str(
            record.get(config["mef_kh"], "")
        ).strip()

        if code not in entries:
            entries[code] = {
                "code": code,
                "english": english,
                "khmer": khmer,
            }

    return entries


def collect_geo(config):
    geojson = load_json(
        RAW_DIR / config["geo_file"]
    )

    entries = []

    for index, feature in enumerate(
        geojson["features"]
    ):
        properties = feature["properties"]

        entries.append(
            {
                "index": index,
                "name": str(
                    properties.get(
                        "shapeName",
                        "",
                    )
                ).strip(),
                "shapeID": str(
                    properties.get(
                        "shapeID",
                        "",
                    )
                ).strip(),
                "shapeISO": str(
                    properties.get(
                        "shapeISO",
                        "",
                    )
                ).strip(),
            }
        )

    return entries


def build_index(entries, get_name):
    index = defaultdict(list)

    for entry in entries:
        normalized = normalize_name(
            get_name(entry)
        )

        if normalized:
            index[normalized].append(entry)

    return index


def inspect_level(
    level,
    config,
    raw_mef_records,
):
    mef = collect_mef(
        raw_mef_records,
        config,
    )

    geo = collect_geo(config)

    mef_index = build_index(
        mef.values(),
        lambda item: item["english"],
    )

    geo_index = build_index(
        geo,
        lambda item: item["name"],
    )

    matches = []
    ambiguous = []

    matched_mef_codes = set()
    matched_geo_indices = set()

    for normalized in (
        set(mef_index)
        & set(geo_index)
    ):
        mef_items = mef_index[normalized]
        geo_items = geo_index[normalized]

        if (
            len(mef_items) == 1
            and len(geo_items) == 1
        ):
            mef_item = mef_items[0]
            geo_item = geo_items[0]

            matches.append(
                (mef_item, geo_item)
            )

            matched_mef_codes.add(
                mef_item["code"]
            )

            matched_geo_indices.add(
                geo_item["index"]
            )

        else:
            ambiguous.append(
                (
                    normalized,
                    mef_items,
                    geo_items,
                )
            )

    unmatched_mef = [
        item
        for code, item in mef.items()
        if code not in matched_mef_codes
    ]

    unmatched_geo = [
        item
        for item in geo
        if item["index"]
        not in matched_geo_indices
    ]

    matches.sort(
        key=lambda pair: pair[0]["code"]
    )

    unmatched_mef.sort(
        key=lambda item: item["code"]
    )

    unmatched_geo.sort(
        key=lambda item: item["name"]
    )

    print()
    print("=" * 72)
    print(level.upper())
    print("=" * 72)

    print(
        f"MEF units:              "
        f"{len(mef):,}"
    )
    print(
        f"geoBoundaries features: "
        f"{len(geo):,}"
    )
    print(
        f"Unique name matches:    "
        f"{len(matches):,}"
    )
    print(
        f"Unmatched MEF units:    "
        f"{len(unmatched_mef):,}"
    )
    print(
        f"Unmatched geo features: "
        f"{len(unmatched_geo):,}"
    )
    print(
        f"Ambiguous names:        "
        f"{len(ambiguous):,}"
    )

    print()
    print("MATCH EXAMPLES")
    print("-" * 72)

    for mef_item, geo_item in (
        matches[:EXAMPLE_COUNT]
    ):
        print(
            f"{mef_item['code']}: "
            f"MEF={mef_item['english']!r} | "
            f"Geo={geo_item['name']!r} | "
            f"shapeID={geo_item['shapeID']!r}"
        )

    print()
    print(
        f"UNMATCHED MEF IDS "
        f"({len(unmatched_mef):,})"
    )
    print("-" * 72)

    if not unmatched_mef:
        print("None")
    else:
        for item in unmatched_mef:
            print(
                f"{item['code']}: "
                f"{item['english']} | "
                f"{item['khmer']}"
            )

    print()
    print(
        f"UNMATCHED GEOboundaries "
        f"({len(unmatched_geo):,})"
    )
    print("-" * 72)

    if not unmatched_geo:
        print("None")
    else:
        for item in unmatched_geo:
            print(
                f"{item['name']} | "
                f"shapeID={item['shapeID']}"
            )

    if ambiguous:
        print()
        print(
            f"AMBIGUOUS NAMES "
            f"({len(ambiguous):,})"
        )
        print("-" * 72)

        for (
            normalized,
            mef_items,
            geo_items,
        ) in ambiguous:
            print(
                f"{normalized}:"
            )

            print(
                "  MEF: "
                + ", ".join(
                    f"{item['code']} "
                    f"{item['english']}"
                    for item in mef_items
                )
            )

            print(
                "  Geo: "
                + ", ".join(
                    item["name"]
                    for item in geo_items
                )
            )


def main():
    mef_records = load_json(
        MEF_PATH
    )

    print(
        "Cambodia geoBoundaries / "
        "MEF comparison"
    )

    print(
        f"MEF raw records: "
        f"{len(mef_records):,}"
    )

    for level, config in LEVELS.items():
        inspect_level(
            level,
            config,
            mef_records,
        )


if __name__ == "__main__":
    output_path = Path(
        "data/intermediate/countries/cambodia/"
        "geoboundaries-mef-comparison.txt"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        original_stdout = sys.stdout

        try:
            sys.stdout = output_file
            main()
        finally:
            sys.stdout = original_stdout

    print("Comparison complete.")
    print(f"Report: {output_path}")