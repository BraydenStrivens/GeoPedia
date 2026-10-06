"""
Create Cambodia's merged landline area-code prefix GeoJSON.

Merges the finalized Cambodia province polygons by their one-digit geographic
landline area-code prefix. The resulting GeoJSON contains one feature for each
prefix from 02 through 07 and is used by the area-code prefix quiz.

Input:
    public/data/countries/cambodia/geojson/provinces.geojson

Output:
    public/data/countries/cambodia/geojson/area-code-prefixes.geojson

Usage:
    python scripts/countries/asia/cambodia/process/area-code-prefixes.py

Requires:
    shapely
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


PROJECT_ROOT = Path(__file__).resolve().parents[5]

INPUT_PATH = (
    PROJECT_ROOT
    / "public/data/countries/cambodia/geojson/provinces.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public/data/countries/cambodia/geojson/area-code-prefixes.geojson"
)


PREFIX_BY_PROVINCE_ID = {
    # 02-
    "12": "02",
    "08": "02",
    "05": "02",
    "04": "02",

    # 03-
    "21": "03",
    "07": "03",
    "18": "03",
    "09": "03",
    "23": "03",

    # 04-
    "03": "04",
    "14": "04",
    "20": "04",
    "25": "04",

    # 05-
    "15": "05",
    "02": "05",
    "01": "05",
    "24": "05",

    # 06-
    "06": "06",
    "17": "06",
    "13": "06",
    "22": "06",

    # 07-
    "10": "07",
    "11": "07",
    "19": "07",
    "16": "07",
}


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_geojson(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    source = load_geojson(INPUT_PATH)

    geometries_by_prefix: dict[str, list[Any]] = {
        prefix: []
        for prefix in sorted(set(PREFIX_BY_PROVINCE_ID.values()))
    }

    found_province_ids: set[str] = set()

    for feature in source["features"]:
        properties = feature["properties"]

        province_id = str(
            properties["province_id"]
        ).strip()

        if province_id not in PREFIX_BY_PROVINCE_ID:
            raise ValueError(
                f"No area-code prefix mapped for province ID "
                f"{province_id!r}."
            )

        if province_id in found_province_ids:
            raise ValueError(
                f"Duplicate province ID {province_id!r}."
            )

        found_province_ids.add(province_id)

        prefix = PREFIX_BY_PROVINCE_ID[province_id]

        geometries_by_prefix[prefix].append(
            shape(feature["geometry"])
        )

    expected_province_ids = set(
        PREFIX_BY_PROVINCE_ID
    )

    missing = expected_province_ids - found_province_ids
    unexpected = found_province_ids - expected_province_ids

    if missing:
        raise ValueError(
            "Missing province IDs: "
            + ", ".join(sorted(missing))
        )

    if unexpected:
        raise ValueError(
            "Unexpected province IDs: "
            + ", ".join(sorted(unexpected))
        )

    output_features = []

    for prefix, geometries in geometries_by_prefix.items():
        if not geometries:
            raise ValueError(
                f"No geometries found for prefix {prefix}."
            )

        merged = unary_union(geometries)

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "area_code_prefix": prefix,
                },
                "geometry": mapping(merged),
            }
        )

    output = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    write_geojson(
        OUTPUT_PATH,
        output,
    )

    print("Cambodia area-code prefix GeoJSON generated.")
    print()
    print(
        f"Prefixes    {len(output_features):>2} features"
    )
    print()
    print(
        OUTPUT_PATH.relative_to(PROJECT_ROOT)
    )


if __name__ == "__main__":
    main()