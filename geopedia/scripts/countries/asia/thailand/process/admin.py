"""
Process Thailand's administrative boundaries for GeoPedia.

Reads the raw ADM1–ADM3 GeoJSON files, simplifies their geometry using
Shapely, and writes compact GeoJSON containing only the properties needed
for maps, quizzes, and administrative grouping.

English and Thai names are preserved at every level. Duplicate district
names are disambiguated by province; duplicate subdistrict names are
disambiguated by district only.

Inputs:
    data/raw/countries/thailand/tha_admin_boundaries.geojson/
        tha_admin1.geojson
        tha_admin2.geojson
        tha_admin3.geojson

Outputs:
    public/data/countries/thailand/geojson/
        provinces.geojson
        districts.geojson
        subdistricts.geojson

Usage:
    python scripts/countries/asia/thailand/process/admin.py

Dependencies:
    pip install shapely ijson
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import ijson
from shapely.geometry import mapping, shape


PROJECT_ROOT = Path(__file__).resolve().parents[5]

RAW_DIR = (
    PROJECT_ROOT
    / "data/raw/countries/thailand/tha_admin_boundaries.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public/data/countries/thailand/geojson"
)

DATASETS = {
    "provinces": {
        "input": "tha_admin1.geojson",
        "tolerance": 0.001,
        "expected_count": 77,
    },
    "districts": {
        "input": "tha_admin2.geojson",
        "tolerance": 0.0005,
        "expected_count": 928,
    },
    "subdistricts": {
        "input": "tha_admin3.geojson",
        "tolerance": 0.0001,
        "expected_count": 7425,
    },
}


def stream_features(path: Path):
    """Read GeoJSON features without loading the full file."""

    with path.open("rb") as file:
        yield from ijson.items(
            file,
            "features.item",
            use_float=True,
        )


def clean_pcode(value: str) -> str:
    """Remove Thailand's TH prefix while retaining leading zeros."""

    if not isinstance(value, str) or not value.startswith("TH"):
        raise ValueError(f"Unexpected PCode: {value!r}")

    return value[2:]


def required_string(
    properties: dict[str, Any],
    key: str,
) -> str:
    """Read a required nonempty string property."""

    value = properties.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid property: {key}")

    return value.strip()


def count_names(
    path: Path,
    name_field: str,
) -> Counter[str]:
    """Count names to identify duplicates before processing."""

    counts: Counter[str] = Counter()

    for feature in stream_features(path):
        properties = feature["properties"]
        name = required_string(properties, name_field)
        counts[name] += 1

    return counts


def simplify_geometry(
    geometry_data: dict[str, Any],
    tolerance: float,
) -> dict[str, Any]:
    """Simplify a geometry while preserving its individual topology."""

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError("Empty geometry encountered.")

    simplified = geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    if simplified.is_empty or not simplified.is_valid:
        raise ValueError("Simplification produced invalid geometry.")

    return mapping(simplified)


def province_properties(
    source: dict[str, Any],
) -> dict[str, str]:
    return {
        "province_id": clean_pcode(
            required_string(source, "adm1_pcode")
        ),
        "province": required_string(source, "adm1_name"),
        "province_native": required_string(source, "adm1_name1"),
    }


def district_properties(
    source: dict[str, Any],
    name_counts: Counter[str],
) -> dict[str, str]:
    district = required_string(source, "adm2_name")
    province = required_string(source, "adm1_name")

    display_name = (
        f"{district} ({province})"
        if name_counts[district] > 1
        else district
    )

    return {
        "district_id": clean_pcode(
            required_string(source, "adm2_pcode")
        ),
        "district": display_name,
        "district_native": required_string(source, "adm2_name1"),
        "province_id": clean_pcode(
            required_string(source, "adm1_pcode")
        ),
        "province": province,
    }


def subdistrict_properties(
    source: dict[str, Any],
    name_counts: Counter[str],
) -> dict[str, str]:
    subdistrict = required_string(source, "adm3_name")
    district = required_string(source, "adm2_name")
    province = required_string(source, "adm1_name")

    display_name = (
        f"{subdistrict} ({district})"
        if name_counts[subdistrict] > 1
        else subdistrict
    )

    return {
        "subdistrict_id": clean_pcode(
            required_string(source, "adm3_pcode")
        ),
        "subdistrict": display_name,
        "subdistrict_native": required_string(source, "adm3_name1"),
        "district_id": clean_pcode(
            required_string(source, "adm2_pcode")
        ),
        "district": district,
        "province_id": clean_pcode(
            required_string(source, "adm1_pcode")
        ),
        "province": province,
    }


def process_dataset(
    dataset_name: str,
    config: dict[str, Any],
) -> None:
    input_path = RAW_DIR / config["input"]
    output_path = OUTPUT_DIR / f"{dataset_name}.geojson"

    tolerance = config["tolerance"]
    expected_count = config["expected_count"]

    print()
    print(f"Processing {dataset_name}...")
    print(f"  Simplification tolerance: {tolerance}")

    name_counts: Counter[str] = Counter()

    if dataset_name == "districts":
        name_counts = count_names(
            input_path,
            "adm2_name",
        )

    elif dataset_name == "subdistricts":
        name_counts = count_names(
            input_path,
            "adm3_name",
        )

    seen_ids: set[str] = set()
    display_names: list[str] = []

    count = 0

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open("w", encoding="utf-8") as output:
        output.write('{"type":"FeatureCollection","features":[')

        for feature in stream_features(input_path):
            source = feature["properties"]

            if dataset_name == "provinces":
                properties = province_properties(source)
                feature_id = properties["province_id"]
                display_name = properties["province"]

            elif dataset_name == "districts":
                properties = district_properties(
                    source,
                    name_counts,
                )
                feature_id = properties["district_id"]
                display_name = properties["district"]

            else:
                properties = subdistrict_properties(
                    source,
                    name_counts,
                )
                feature_id = properties["subdistrict_id"]
                display_name = properties["subdistrict"]

            if feature_id in seen_ids:
                raise ValueError(
                    f"Duplicate ID: {feature_id}"
                )

            seen_ids.add(feature_id)
            display_names.append(display_name)

            geometry = simplify_geometry(
                feature["geometry"],
                tolerance,
            )

            processed_feature = {
                "type": "Feature",
                "properties": properties,
                "geometry": geometry,
            }

            if count:
                output.write(",")

            json.dump(
                processed_feature,
                output,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            count += 1

            if count % 500 == 0:
                print(
                    f"  Processed {count:,} features...",
                    flush=True,
                )

        output.write("]}")

    if count != expected_count:
        raise ValueError(
            f"Expected {expected_count:,} features, found {count:,}."
        )

    duplicates = [
        name
        for name, occurrences in Counter(display_names).items()
        if occurrences > 1
    ]

    if duplicates:
        print(
            f"  Remaining duplicate display names: {len(duplicates):,} "
            "(allowed after parent disambiguation)"
        )

        for name in duplicates[:10]:
            print(f"    {name}")

    size_mb = output_path.stat().st_size / 1_000_000

    print(f"  Features: {count:,}")
    print(f"  Unique IDs: {len(seen_ids):,}")
    print(f"  Output size: {size_mb:.2f} MB")
    print(f"  Output: {output_path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    print("Thailand administrative boundary processing")

    for dataset_name, config in DATASETS.items():
        process_dataset(
            dataset_name,
            config,
        )

    print()
    print("Processing complete.")


if __name__ == "__main__":
    main()