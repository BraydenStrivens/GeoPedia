"""
Process São Tomé and Príncipe's raw geoBoundaries administrative boundaries
directly into GeoPedia's runtime GeoJSON files.

The country has only two ADM1 provinces and seven ADM2 districts, so a
separate intermediate administrative dataset is unnecessary. Raw properties
are converted to GeoPedia's canonical runtime properties and the small
geometries are conservatively simplified in the same processing step.

Inputs:
    data/raw/countries/sao_tome_and_principe/geoBoundaries-STP-ADM1.geojson
    data/raw/countries/sao_tome_and_principe/geoBoundaries-STP-ADM2.geojson

Outputs:
    public/data/countries/sao_tome_and_principe/geojson/provinces.geojson
    public/data/countries/sao_tome_and_principe/geojson/districts.geojson
"""

import json
from pathlib import Path

from shapely.geometry import mapping, shape


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "sao_tome_and_principe"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "sao_tome_and_principe"
    / "geojson"
)

PROVINCES_INPUT = RAW_DIR / "geoBoundaries-STP-ADM1.geojson"
DISTRICTS_INPUT = RAW_DIR / "geoBoundaries-STP-ADM2.geojson"

PROVINCES_OUTPUT = OUTPUT_DIR / "provinces.geojson"
DISTRICTS_OUTPUT = OUTPUT_DIR / "districts.geojson"

EXPECTED_PROVINCE_COUNT = 2
EXPECTED_DISTRICT_COUNT = 7

SIMPLIFICATION_TOLERANCE = 0.00025


def load_geojson(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    return data


def simplify_geometry(geometry_data: dict) -> dict:
    """Conservatively simplify a geometry while preserving its topology."""
    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            "Cannot process an empty geometry."
        )

    simplified = geometry.simplify(
        SIMPLIFICATION_TOLERANCE,
        preserve_topology=True,
    )

    if simplified.is_empty:
        raise ValueError(
            "Simplification produced an empty geometry."
        )

    return mapping(simplified)


def write_geojson(
    path: Path,
    features: list[dict],
) -> None:
    """Write a compact runtime GeoJSON FeatureCollection."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def process_provinces(
    raw_data: dict,
) -> list[dict]:
    """Convert ADM1 features into simplified runtime province features."""
    features = []
    seen_ids = set()

    for feature in raw_data["features"]:
        properties = feature.get("properties", {})

        province_id = properties.get(
            "shapeISO",
            "",
        ).strip()

        province = properties.get(
            "shapeName",
            "",
        ).strip()

        if not province_id:
            raise ValueError(
                f"Province is missing shapeISO: {province!r}"
            )

        if not province:
            raise ValueError(
                f"Province {province_id!r} is missing shapeName."
            )

        if province_id in seen_ids:
            raise ValueError(
                f"Duplicate province ID: {province_id}"
            )

        seen_ids.add(province_id)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "province_id": province_id,
                    "province": province,
                },
                "geometry": simplify_geometry(
                    feature["geometry"]
                ),
            }
        )

    if len(features) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_PROVINCE_COUNT} provinces, "
            f"found {len(features)}."
        )

    return features


def process_districts(
    raw_data: dict,
) -> list[dict]:
    """Convert ADM2 features into simplified runtime district features."""
    features = []
    seen_ids = set()
    seen_names = set()

    for feature in raw_data["features"]:
        properties = feature.get("properties", {})

        district_id = properties.get(
            "shapeID",
            "",
        ).strip()

        district = properties.get(
            "shapeName",
            "",
        ).strip()

        if not district_id:
            raise ValueError(
                f"District is missing shapeID: {district!r}"
            )

        if not district:
            raise ValueError(
                f"District {district_id!r} is missing shapeName."
            )

        if district_id in seen_ids:
            raise ValueError(
                f"Duplicate district ID: {district_id}"
            )

        if district in seen_names:
            raise ValueError(
                f"Duplicate district name: {district}"
            )

        seen_ids.add(district_id)
        seen_names.add(district)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "district_id": district_id,
                    "district": district,
                },
                "geometry": simplify_geometry(
                    feature["geometry"]
                ),
            }
        )

    if len(features) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DISTRICT_COUNT} districts, "
            f"found {len(features)}."
        )

    return features


def format_size(path: Path) -> str:
    """Format an output file size as kilobytes."""
    return f"{path.stat().st_size / 1024:.1f} KB"


def main() -> None:
    """Create São Tomé and Príncipe's runtime administrative GeoJSON."""
    print(
        "Processing São Tomé and Príncipe "
        "administrative boundaries..."
    )
    print()

    raw_provinces = load_geojson(
        PROVINCES_INPUT
    )

    raw_districts = load_geojson(
        DISTRICTS_INPUT
    )

    provinces = process_provinces(
        raw_provinces
    )

    districts = process_districts(
        raw_districts
    )

    write_geojson(
        PROVINCES_OUTPUT,
        provinces,
    )

    write_geojson(
        DISTRICTS_OUTPUT,
        districts,
    )

    print(
        "São Tomé and Príncipe administrative "
        "processing complete."
    )
    print(
        f"  Provinces: {len(provinces)} "
        f"({format_size(PROVINCES_OUTPUT)})"
    )
    print(
        f"  Districts: {len(districts)} "
        f"({format_size(DISTRICTS_OUTPUT)})"
    )
    print()
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()