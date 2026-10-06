"""
Prepare Cambodia administrative GeoJSON files for GeoPedia.

This script converts the raw HumData/OCHA administrative boundaries into
minimal intermediate GeoJSON files. Geometry is preserved exactly; geometry
cleaning and simplification are intentionally handled by a separate script.

Province and district Khmer names are joined from cambodia_gazetteer.json
using administrative codes. Commune data is taken entirely from HumData
because the gazetteer represents a newer commune structure that does not
exactly match the boundary dataset.

District display names use the shorter HumData names rather than gazetteer
suffixes such as "Municipality" and "Khan". Duplicate district names are
disambiguated with their parent province.

Inputs:
    data/raw/countries/cambodia/cambodia_gazetteer.json

    data/raw/countries/cambodia/khm_admin_boundaries/
        khm_admin1.geojson
        khm_admin2.geojson
        khm_admin3.geojson

Outputs:
    data/intermediate/countries/cambodia/
        provinces.geojson
        districts.geojson
        communes.geojson

Usage:
    python scripts/countries/asia/cambodia/process/prepare-admin-geojson.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = PROJECT_ROOT / "data/raw/countries/cambodia"
HUMDATA_DIR = RAW_DIR / "khm_admin_boundaries"

GAZETTEER_PATH = RAW_DIR / "cambodia_gazetteer.json"

ADM1_PATH = HUMDATA_DIR / "khm_admin1.geojson"
ADM2_PATH = HUMDATA_DIR / "khm_admin2.geojson"
ADM3_PATH = HUMDATA_DIR / "khm_admin3.geojson"

OUTPUT_DIR = PROJECT_ROOT / "public/data/countries/cambodia/geojson"

PROVINCES_OUTPUT = OUTPUT_DIR / "provinces.geojson"
DISTRICTS_OUTPUT = OUTPUT_DIR / "districts.geojson"
COMMUNES_OUTPUT = OUTPUT_DIR / "communes.geojson"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_geojson(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def strip_kh_prefix(value: Any) -> str:
    value = str(value).strip()

    if value.startswith("KH"):
        return value[2:]

    return value


def normalize_province_code(value: Any) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())

    if not digits:
        raise ValueError(f"Invalid province code: {value!r}")

    return digits[-2:].zfill(2)


def normalize_district_code(value: Any) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())

    if not digits:
        raise ValueError(f"Invalid district code: {value!r}")

    return digits[-4:].zfill(4)


def build_gazetteer_indexes(
    gazetteer: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
]:
    provinces: dict[str, dict[str, str]] = {}
    districts: dict[str, dict[str, str]] = {}

    for province in gazetteer:
        province_id = normalize_province_code(province["code"])

        if province_id in provinces:
            raise ValueError(
                f"Duplicate gazetteer province code: {province_id}"
            )

        provinces[province_id] = {
            "name": str(province.get("latin", "")).strip(),
            "native": str(province.get("khmer", "")).strip(),
        }

        for district in province.get("districts", []):
            district_id = normalize_district_code(district["code"])

            if district_id in districts:
                raise ValueError(
                    f"Duplicate gazetteer district code: {district_id}"
                )

            districts[district_id] = {
                "name": str(district.get("latin", "")).strip(),
                "native": str(district.get("khmer", "")).strip(),
                "province_id": province_id,
            }

    return provinces, districts


def make_feature(
    source_feature: dict[str, Any],
    properties: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": source_feature["geometry"],
    }


def prepare_provinces(
    source: dict[str, Any],
    gazetteer_provinces: dict[str, dict[str, str]],
) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    for feature in source["features"]:
        source_properties = feature.get("properties") or {}

        province_id = strip_kh_prefix(
            source_properties["adm1_pcode"]
        )

        gazetteer = gazetteer_provinces.get(province_id)

        if gazetteer is None:
            raise ValueError(
                f"No gazetteer province for HumData ID {province_id}"
            )

        if not gazetteer["native"]:
            raise ValueError(
                f"Missing Khmer province name for {province_id}"
            )

        # Use the shorter HumData display name. The gazetteer calls
        # Phnom Penh "Phnom Penh Capital", while the boundary dataset
        # simply uses "Phnom Penh".
        province = str(
            source_properties["adm1_name"]
        ).strip()

        features.append(
            make_feature(
                feature,
                {
                    "province_id": province_id,
                    "province": province,
                    "province_native": gazetteer["native"],
                },
            )
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def prepare_districts(
    source: dict[str, Any],
    gazetteer_districts: dict[str, dict[str, str]],
) -> dict[str, Any]:
    source_records: list[
        tuple[dict[str, Any], str, str, str, str]
    ] = []

    base_name_counts: Counter[str] = Counter()

    for feature in source["features"]:
        source_properties = feature.get("properties") or {}

        district_id = strip_kh_prefix(
            source_properties["adm2_pcode"]
        )
        province_id = strip_kh_prefix(
            source_properties["adm1_pcode"]
        )

        district = str(
            source_properties["adm2_name"]
        ).strip()
        province = str(
            source_properties["adm1_name"]
        ).strip()

        gazetteer = gazetteer_districts.get(district_id)

        if gazetteer is None:
            raise ValueError(
                f"No gazetteer district for HumData ID {district_id}"
            )

        if gazetteer["province_id"] != province_id:
            raise ValueError(
                f"District {district_id} parent mismatch: "
                f"HumData={province_id}, "
                f"gazetteer={gazetteer['province_id']}"
            )

        if not gazetteer["native"]:
            raise ValueError(
                f"Missing Khmer district name for {district_id}"
            )

        base_name_counts[district] += 1

        source_records.append(
            (
                feature,
                district_id,
                district,
                province_id,
                province,
            )
        )

    features: list[dict[str, Any]] = []

    for (
        feature,
        district_id,
        district,
        province_id,
        province,
    ) in source_records:
        gazetteer = gazetteer_districts[district_id]

        if base_name_counts[district] > 1:
            display_name = f"{district} ({province})"
        else:
            display_name = district

        features.append(
            make_feature(
                feature,
                {
                    "district_id": district_id,
                    "district": display_name,
                    "district_native": gazetteer["native"],
                    "province_id": province_id,
                    "province": province,
                },
            )
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def prepare_communes(
    source: dict[str, Any],
) -> dict[str, Any]:
    records: list[
        tuple[dict[str, Any], str, str, str, str, str, str]
    ] = []

    commune_name_counts: Counter[str] = Counter()

    for feature in source["features"]:
        source_properties = feature.get("properties") or {}

        commune_id = strip_kh_prefix(
            source_properties["adm3_pcode"]
        )
        district_id = strip_kh_prefix(
            source_properties["adm2_pcode"]
        )
        province_id = strip_kh_prefix(
            source_properties["adm1_pcode"]
        )

        commune = str(
            source_properties["adm3_name"]
        ).strip()
        district = str(
            source_properties["adm2_name"]
        ).strip()
        province = str(
            source_properties["adm1_name"]
        ).strip()

        commune_name_counts[commune] += 1

        records.append(
            (
                feature,
                commune_id,
                commune,
                district_id,
                district,
                province_id,
                province,
            )
        )

    features: list[dict[str, Any]] = []

    for (
        feature,
        commune_id,
        commune,
        district_id,
        district,
        province_id,
        province,
    ) in records:
        # Follow GeoPedia's normal duplicate-label convention:
        # append only the immediate parent when a raw name is duplicated.
        if commune_name_counts[commune] > 1:
            display_name = f"{commune} ({district})"
        else:
            display_name = commune

        features.append(
            make_feature(
                feature,
                {
                    "commune_id": commune_id,
                    "commune": display_name,
                    "district_id": district_id,
                    "district": district,
                    "province_id": province_id,
                    "province": province,
                },
            )
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def validate_unique_property(
    data: dict[str, Any],
    property_name: str,
) -> None:
    values = [
        feature["properties"][property_name]
        for feature in data["features"]
    ]

    duplicates = [
        value
        for value, count in Counter(values).items()
        if count > 1
    ]

    if duplicates:
        preview = ", ".join(sorted(duplicates)[:10])

        raise ValueError(
            f"{property_name} is not unique. "
            f"Duplicate values include: {preview}"
        )


def print_output(
    label: str,
    path: Path,
    data: dict[str, Any],
) -> None:
    size_bytes = path.stat().st_size

    print(
        f"{label:<10} "
        f"{len(data['features']):>5,} features | "
        f"{size_bytes / 1024 / 1024:>7.2f} MB | "
        f"{path.relative_to(PROJECT_ROOT)}"
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    gazetteer = load_json(GAZETTEER_PATH)

    if not isinstance(gazetteer, list):
        raise TypeError(
            "Expected cambodia_gazetteer.json to contain a JSON array."
        )

    gazetteer_provinces, gazetteer_districts = (
        build_gazetteer_indexes(gazetteer)
    )

    adm1 = load_json(ADM1_PATH)
    adm2 = load_json(ADM2_PATH)
    adm3 = load_json(ADM3_PATH)

    provinces = prepare_provinces(
        adm1,
        gazetteer_provinces,
    )
    districts = prepare_districts(
        adm2,
        gazetteer_districts,
    )
    communes = prepare_communes(adm3)

    # IDs must always be unique.
    validate_unique_property(provinces, "province_id")
    validate_unique_property(districts, "district_id")
    validate_unique_property(communes, "commune_id")

    # Final display labels must also be unique. This catches any duplicate
    # that remains after immediate-parent disambiguation.
    validate_unique_property(provinces, "province")
    validate_unique_property(districts, "district")

    if len(provinces["features"]) != 25:
        raise ValueError(
            f"Expected 25 provinces, got {len(provinces['features'])}"
        )

    if len(districts["features"]) != 197:
        raise ValueError(
            f"Expected 197 districts, got {len(districts['features'])}"
        )

    if len(communes["features"]) != 1633:
        raise ValueError(
            f"Expected 1,633 communes, got {len(communes['features'])}"
        )

    write_geojson(PROVINCES_OUTPUT, provinces)
    write_geojson(DISTRICTS_OUTPUT, districts)
    write_geojson(COMMUNES_OUTPUT, communes)

    print()
    print("Cambodia administrative intermediate GeoJSONs prepared.")
    print("Geometry was copied unchanged from HumData/OCHA.")
    print()

    print_output(
        "Provinces",
        PROVINCES_OUTPUT,
        provinces,
    )
    print_output(
        "Districts",
        DISTRICTS_OUTPUT,
        districts,
    )
    print_output(
        "Communes",
        COMMUNES_OUTPUT,
        communes,
    )


if __name__ == "__main__":
    main()