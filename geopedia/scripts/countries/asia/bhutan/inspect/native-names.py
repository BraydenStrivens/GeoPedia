
"""
Compare Bhutan geoBoundaries names against a JavaScript dataset
containing English and Dzongkha administrative names.

Inputs:
  data/raw/countries/bhutan/
    geoBoundaries-BTN-ADM1.geojson
    geoBoundaries-BTN-ADM2.geojson
    subdivisions_with_native_names.js

Output:
  Console report of matches, unmatched names, and suggestions.

Run:
  python scripts/countries/asia/bhutan/inspect/native_names.py
"""

import json
import re
import unicodedata
from collections import Counter
from difflib import get_close_matches
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / "data/raw/countries/bhutan"

JS_PATH = RAW / "subdivisions_with_native_names.js"


def normalize(name):
    value = unicodedata.normalize("NFKC", name).casefold()
    return "".join(char for char in value if char.isalnum())


def load_geo_names(level):
    path = RAW / f"geoBoundaries-BTN-ADM{level}.geojson"

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    return [
        feature["properties"]["shapeName"]
        for feature in data["features"]
    ]


def load_native_names():
    text = JS_PATH.read_text(encoding="utf-8")

    districts = re.findall(
        r'dzongkhag:\s*"([^"]+)"\s*,\s*'
        r'dzongkhagDzongkha:\s*"([^"]+)"',
        text,
    )

    gewogs = re.findall(
        r'\{\s*name:\s*"([^"]+)"\s*,\s*'
        r'dzongkha:\s*"([^"]+)"\s*\}',
        text,
    )

    return districts, gewogs


def compare(level, geo_names, native_records):
    print(f"\n{'=' * 60}")
    print(f"ADM{level}")
    print("=" * 60)

    native_lookup = {}

    for english, native in native_records:
        native_lookup.setdefault(normalize(english), []).append(
            (english, native)
        )

    matched = []
    unmatched = []

    for name in geo_names:
        candidates = native_lookup.get(normalize(name), [])

        if candidates:
            matched.append(name)
        else:
            unmatched.append(name)

    print(f"geoBoundaries features: {len(geo_names)}")
    print(f"Native-name records: {len(native_records)}")
    print(f"Unique native English names: {len(native_lookup)}")
    print(f"Matched: {len(matched)}/{len(geo_names)}")
    print(f"Unmatched: {len(unmatched)}")

    duplicates = {
        key: records
        for key, records in native_lookup.items()
        if len(records) > 1
    }

    if duplicates:
        print("\nDUPLICATE REFERENCE NAMES:")

        for records in duplicates.values():
            print(
                f"  {records[0][0]}: "
                f"{len(records)} entries"
            )

    if unmatched:
        print("\nUNMATCHED GEOboundaries NAMES:")

        choices = list(native_lookup)

        for name in unmatched:
            suggestions = get_close_matches(
                normalize(name),
                choices,
                n=3,
                cutoff=0.55,
            )

            suggested_names = [
                native_lookup[key][0][0]
                for key in suggestions
            ]

            print(f"\n  {name}")

            if suggested_names:
                print(
                    "    Suggestions: "
                    + ", ".join(suggested_names)
                )

    geo_keys = {normalize(name) for name in geo_names}

    unused = [
        english
        for english, _ in native_records
        if normalize(english) not in geo_keys
    ]

    if unused:
        print("\nUNUSED REFERENCE NAMES:")

        for name in sorted(set(unused)):
            print(f"  {name}")


def main():
    districts, gewogs = load_native_names()

    print("Bhutan native-name matching report")

    compare(
        1,
        load_geo_names(1),
        districts,
    )

    compare(
        2,
        load_geo_names(2),
        gewogs,
    )


if __name__ == "__main__":
    main()
