"""
Inspect OSM populated places relevant to South Africa's geographic telephone
area-code regions.

The script searches the intermediate OSM place dataset for settlements named
in the area-code reference material and prints each match together with its
GeoPedia ward, municipality, district, and province.

This is a research/inspection script. It does not generate runtime data.

Input:
    data/intermediate/countries/south-africa/osm/places.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/inspect/area-code-places.py
"""

from __future__ import annotations

import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


PLACES_PATH = Path(
    "data/intermediate/countries/south-africa/osm/places.geojson"
)


# Towns/localities explicitly named in the Plonk It area-code legend.
#
# The keys are geographic area codes. Names here are search terms rather than
# canonical GeoPedia data, so alternate spellings and renamed settlements can
# be added as we encounter them in OSM.
AREA_CODE_PLACES: dict[str, list[str]] = {
    "010": [
        "Johannesburg",
    ],
    "011": [
        "Johannesburg",
        "Ekurhuleni",
    ],
    "012": [
        "Pretoria",
        "Tshwane",
        "Brits",
    ],
    "013": [
        "Bronkhorstspruit",
        "Emalahleni",
        "Middelburg",
        "Lydenburg",
        "Mbombela",
        "Nelspruit",
    ],
    "014": [
        "Lephalale",
        "Modimolle",
        "Bela-Bela",
        "Rustenburg",
    ],
    "015": [
        "Polokwane",
        "Tzaneen",
        "Hoedspruit",
    ],
    "016": [
        "Vanderbijlpark",
        "Vereeniging",
        "Heidelberg",
        "Sasolburg",
    ],
    "017": [
        "Ermelo",
        "Secunda",
        "Standerton",
    ],
    "018": [
        "Klerksdorp",
        "Lichtenburg",
        "Potchefstroom",
        "Ventersdorp",
    ],
    "021": [
        "Cape Town",
        "Gordon's Bay",
        "Gordons Bay",
        "Somerset West",
        "Stellenbosch",
        "Paarl",
        "Wellington",
    ],
    "022": [
        "Malmesbury",
        "Vredenburg",
    ],
    "023": [
        "Beaufort West",
        "Robertson",
        "Worcester",
    ],
    "027": [
        "Alexander Bay",
        "Calvinia",
        "Clanwilliam",
        "Port Nolloth",
        "Springbok",
    ],
    "028": [
        "Caledon",
        "Hermanus",
        "Swellendam",
    ],
    "031": [
        "Durban",
    ],
    "032": [
        "Ballito",
        "Stanger",
        "KwaDukuza",
        "Tongaat",
        "Verulam",
    ],
    "033": [
        "Pietermaritzburg",
    ],
    "034": [
        "Newcastle",
        "Vryheid",
    ],
    "035": [
        "Richards Bay",
        "St Lucia",
        "Ulundi",
    ],
    "036": [
        "Ladysmith",
    ],
    "039": [
        "Port Shepstone",
    ],
    "040": [
        "Alice",
        "Bhisho",
        "Bisho",
    ],
    "041": [
        "Gqeberha",
        "Port Elizabeth",
        "Kariega",
        "Uitenhage",
    ],
    "042": [
        "Jeffreys Bay",
        "Humansdorp",
    ],
    "043": [
        "East London",
        "Bhisho",
        "Bisho",
        "Alice",
    ],
    "044": [
        "George",
        "Knysna",
        "Mossel Bay",
        "Oudtshoorn",
        "Plettenberg Bay",
    ],
    "045": [
        "Queenstown",
        "Dordrecht",
        "Elliot",
    ],
    "046": [
        "Bathurst",
        "Grahamstown",
        "Makhanda",
        "Kenton-on-Sea",
        "Kenton",
    ],
    "047": [
        "Butterworth",
        "Mthatha",
    ],
    "048": [
        "Cradock",
        "Steynsburg",
    ],
    "049": [
        "Graaff-Reinet",
    ],
    "051": [
        "Aliwal North",
        "Bloemfontein",
    ],
    "053": [
        "Kimberley",
    ],
    "054": [
        "Upington",
    ],
    "056": [
        "Kroonstad",
        "Parys",
    ],
    "057": [
        "Welkom",
    ],
    "058": [
        "Bethlehem",
    ],
}


def normalize_name(value: str) -> str:
    """
    Normalize a place name for forgiving case/accent/punctuation comparison.
    """
    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    return "".join(
        character.casefold()
        for character in value
        if character.isalnum()
    )


def get_searchable_names(
    properties: dict[str, Any],
) -> set[str]:
    """
    Return normalized current and alternate names stored from OSM.
    """
    names: set[str] = set()

    for property_name in (
        "name",
        "name_en",
        "official_name",
        "alt_name",
        "old_name",
    ):
        value = properties.get(property_name)

        if isinstance(value, str) and value.strip():
            names.add(normalize_name(value))

    return names


def load_places() -> list[dict[str, Any]]:
    """
    Load the intermediate OSM populated-place dataset.
    """
    if not PLACES_PATH.exists():
        raise FileNotFoundError(
            f"OSM place dataset not found: {PLACES_PATH}"
        )

    with PLACES_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "OSM place dataset must be a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "OSM place dataset contains no feature list."
        )

    return features


def build_name_index(
    places: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Index places by all current/alternate OSM names retained during extraction.
    """
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for feature in places:
        properties = feature["properties"]

        for name in get_searchable_names(properties):
            index[name].append(feature)

    return index


def describe_match(feature: dict[str, Any]) -> str:
    """
    Format one OSM match and its assigned administrative hierarchy.
    """
    properties = feature["properties"]
    longitude, latitude = feature["geometry"]["coordinates"]

    ward = properties.get(
        "ward",
        "UNMATCHED",
    )
    ward_id = properties.get(
        "ward_id",
        "UNMATCHED",
    )
    municipality = properties.get(
        "municipality",
        "UNMATCHED",
    )
    district = properties.get(
        "district",
        "UNMATCHED",
    )
    province = properties.get(
        "province",
        "UNMATCHED",
    )

    return (
        f"{properties['name']} "
        f"[{properties['place']}] "
        f"({latitude:.5f}, {longitude:.5f})\n"
        f"      Ward:         {ward}\n"
        f"      Ward ID:      {ward_id}\n"
        f"      Municipality: {municipality}\n"
        f"      District:     {district}\n"
        f"      Province:     {province}"
    )


def main() -> None:
    places = load_places()
    index = build_name_index(places)

    total_queries = 0
    matched_queries = 0
    missing: list[tuple[str, str]] = []

    for area_code, search_names in AREA_CODE_PLACES.items():
        print()
        print("=" * 80)
        print(area_code)
        print("=" * 80)

        # Some legend entries contain old/current aliases for the same place.
        # Avoid printing the same OSM feature repeatedly within one code.
        printed_osm_ids: set[int] = set()

        for search_name in search_names:
            total_queries += 1

            matches = index.get(
                normalize_name(search_name),
                [],
            )

            if not matches:
                print(f"  ? {search_name:<24} NO MATCH")
                missing.append((area_code, search_name))
                continue

            matched_queries += 1

            new_matches = [
                feature
                for feature in matches
                if feature["properties"]["osm_id"]
                not in printed_osm_ids
            ]

            if not new_matches:
                # This search term was an alias of a feature already shown.
                continue

            print(f"  {search_name}")

            for feature in new_matches:
                print(
                    "    "
                    + describe_match(feature).replace(
                        "\n",
                        "\n    ",
                    )
                )

                printed_osm_ids.add(
                    feature["properties"]["osm_id"]
                )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"OSM places loaded: {len(places):,}")
    print(f"Search names:      {total_queries:,}")
    print(f"Matched names:     {matched_queries:,}")
    print(f"Missing names:     {len(missing):,}")

    if missing:
        print()
        print("Missing searches:")

        for area_code, name in missing:
            print(f"  {area_code}  {name}")


if __name__ == "__main__":
    main()