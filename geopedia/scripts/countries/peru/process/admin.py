"""
Processes Peru's raw administrative GeoJSON files into GeoPedia's simplified
intermediate and runtime GeoJSON files.

Inputs:
    data/raw/countries/peru/per_admin_boundaries.geojson/per_admin1.geojson
    data/raw/countries/peru/per_admin_boundaries.geojson/per_admin2.geojson
    data/raw/countries/peru/per_admin_boundaries.geojson/per_admin3.geojson

Intermediate outputs:
    data/intermediate/countries/peru/admin/regions.geojson
    data/intermediate/countries/peru/admin/provinces.geojson
    data/intermediate/countries/peru/admin/districts.geojson

Runtime outputs:
    public/data/countries/peru/geojson/regions.geojson
    public/data/countries/peru/geojson/provinces.geojson
    public/data/countries/peru/geojson/districts.geojson

The runtime files preserve only the properties GeoPedia needs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_DIRECTORY = Path(
    "data/raw/countries/peru/per_admin_boundaries.geojson"
)

INTERMEDIATE_DIRECTORY = Path(
    "data/intermediate/countries/peru/admin"
)

RUNTIME_DIRECTORY = Path(
    "public/data/countries/peru/geojson"
)

ADMIN1_INPUT = RAW_DIRECTORY / "per_admin1.geojson"
ADMIN2_INPUT = RAW_DIRECTORY / "per_admin2.geojson"
ADMIN3_INPUT = RAW_DIRECTORY / "per_admin3.geojson"

REGIONS_INTERMEDIATE_OUTPUT = (
    INTERMEDIATE_DIRECTORY / "regions.geojson"
)

PROVINCES_INTERMEDIATE_OUTPUT = (
    INTERMEDIATE_DIRECTORY / "provinces.geojson"
)

DISTRICTS_INTERMEDIATE_OUTPUT = (
    INTERMEDIATE_DIRECTORY / "districts.geojson"
)

REGIONS_RUNTIME_OUTPUT = (
    RUNTIME_DIRECTORY / "regions.geojson"
)

PROVINCES_RUNTIME_OUTPUT = (
    RUNTIME_DIRECTORY / "provinces.geojson"
)

DISTRICTS_RUNTIME_OUTPUT = (
    RUNTIME_DIRECTORY / "districts.geojson"
)


# ---------------------------------------------------------------------------
# Expected counts
# ---------------------------------------------------------------------------

EXPECTED_REGION_COUNT = 25
EXPECTED_PROVINCE_COUNT = 196
EXPECTED_DISTRICT_COUNT = 1873

# ---------------------------------------------------------------------------
# Maps for adding postal and area code properties to the regions geojson
# ---------------------------------------------------------------------------

POSTAL_CODE_BY_REGION_ID = {
    "PE01": "01",
    "PE02": "02",
    "PE03": "03",
    "PE04": "04",
    "PE05": "05",
    "PE06": "06",
    "PE07": "07",
    "PE08": "08",
    "PE09": "09",
    "PE10": "10",
    "PE11": "11",
    "PE12": "12",
    "PE13": "13",
    "PE14": "14",
    "PE15": "15",
    "PE16": "16",
    "PE17": "17",
    "PE18": "18",
    "PE19": "19",
    "PE20": "20",
    "PE21": "21",
    "PE22": "22",
    "PE23": "23",
    "PE24": "24",
    "PE25": "25",
}


PHONE_CODE_BY_REGION_ID = {
    "PE01": "41",  # Amazonas
    "PE02": "43",  # Ancash
    "PE03": "83",  # Apurimac
    "PE04": "54",  # Arequipa
    "PE05": "66",  # Ayacucho
    "PE06": "76",  # Cajamarca
    "PE07": "1",   # Callao
    "PE08": "84",  # Cusco
    "PE09": "67",  # Huancavelica
    "PE10": "62",  # Huánuco
    "PE11": "56",  # Ica
    "PE12": "64",  # Junín
    "PE13": "44",  # La Libertad
    "PE14": "74",  # Lambayeque
    "PE15": "1",   # Lima
    "PE16": "65",  # Loreto
    "PE17": "82",  # Madre de Dios
    "PE18": "53",  # Moquegua
    "PE19": "63",  # Pasco
    "PE20": "73",  # Piura
    "PE21": "51",  # Puno
    "PE22": "42",  # San Martín
    "PE23": "52",  # Tacna
    "PE24": "72",  # Tumbes
    "PE25": "61",  # Ucayali
}

# ---------------------------------------------------------------------------
# GeoJSON helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} does not contain a valid features array."
        )

    return data


def write_geojson(
    path: Path,
    features: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def require_string(
    properties: dict[str, Any],
    key: str,
    feature_label: str,
) -> str:
    value = properties.get(key)

    if not isinstance(value, str):
        raise ValueError(
            f"{feature_label} is missing string property {key!r}."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{feature_label} has an empty {key!r}."
        )

    return value


def require_geometry(
    feature: dict[str, Any],
    feature_label: str,
) -> dict[str, Any]:
    geometry = feature.get("geometry")

    if not isinstance(geometry, dict):
        raise ValueError(
            f"{feature_label} has no valid geometry."
        )

    geometry_type = geometry.get("type")

    if geometry_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{feature_label} has unsupported geometry type "
            f"{geometry_type!r}."
        )

    return geometry


# ---------------------------------------------------------------------------
# Region processing
# ---------------------------------------------------------------------------

def process_regions(
    raw_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    processed: list[dict[str, Any]] = []

    seen_ids: set[str] = set()

    for index, feature in enumerate(
        raw_features,
        start=1,
    ):
        properties = feature.get("properties", {})

        if not isinstance(properties, dict):
            raise ValueError(
                f"Region feature {index} has invalid properties."
            )

        region_id = require_string(
            properties,
            "adm1_pcode",
            f"Region feature {index}",
        )

        region_name = require_string(
            properties,
            "adm1_name",
            region_id,
        )

        if region_id in seen_ids:
            raise ValueError(
                f"Duplicate region ID: {region_id}"
            )

        seen_ids.add(region_id)

        geometry = require_geometry(
            feature,
            region_id,
        )
        
        postal_code_prefix = POSTAL_CODE_BY_REGION_ID.get(
            region_id
        )

        phone_code = PHONE_CODE_BY_REGION_ID.get(
            region_id
        )

        if postal_code_prefix is None:
            raise ValueError(
                f"No postal-code prefix configured for {region_id}."
            )

        if phone_code is None:
            raise ValueError(
                f"No phone code configured for {region_id}."
            )

        processed.append(
            {
                "type": "Feature",
                "properties": {
                    "region_id": region_id,
                    "region": region_name,
                    "postal_code_prefix": postal_code_prefix,
                    "phone_code": phone_code,
                    "phone_code_first_digit": phone_code[0],
                },
                "geometry": geometry,
            }
        )

    if len(processed) != EXPECTED_REGION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} regions but processed "
            f"{len(processed)}."
        )

    return processed


# ---------------------------------------------------------------------------
# Province processing
# ---------------------------------------------------------------------------

def process_provinces(
    raw_features: list[dict[str, Any]],
    valid_region_ids: set[str],
) -> list[dict[str, Any]]:
    processed: list[dict[str, Any]] = []

    seen_ids: set[str] = set()

    for index, feature in enumerate(
        raw_features,
        start=1,
    ):
        properties = feature.get("properties", {})

        if not isinstance(properties, dict):
            raise ValueError(
                f"Province feature {index} has invalid properties."
            )

        province_id = require_string(
            properties,
            "adm2_pcode",
            f"Province feature {index}",
        )

        province_name = require_string(
            properties,
            "adm2_name",
            province_id,
        )

        region_id = require_string(
            properties,
            "adm1_pcode",
            province_id,
        )

        region_name = require_string(
            properties,
            "adm1_name",
            province_id,
        )

        if province_id in seen_ids:
            raise ValueError(
                f"Duplicate province ID: {province_id}"
            )

        if region_id not in valid_region_ids:
            raise ValueError(
                f"{province_id} references unknown region "
                f"{region_id}."
            )

        if not province_id.startswith(region_id):
            raise ValueError(
                f"Province ID {province_id} does not nest under "
                f"region ID {region_id}."
            )

        seen_ids.add(province_id)

        geometry = require_geometry(
            feature,
            province_id,
        )

        processed.append(
            {
                "type": "Feature",
                "properties": {
                    "province_id": province_id,
                    "province": province_name,
                    "region_id": region_id,
                    "region": region_name,
                },
                "geometry": geometry,
            }
        )

    if len(processed) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_PROVINCE_COUNT} provinces but "
            f"processed {len(processed)}."
        )

    return processed


# ---------------------------------------------------------------------------
# District processing
# ---------------------------------------------------------------------------

def process_districts(
    raw_features: list[dict[str, Any]],
    valid_region_ids: set[str],
    valid_province_ids: set[str],
) -> list[dict[str, Any]]:
    processed: list[dict[str, Any]] = []

    seen_ids: set[str] = set()

    for index, feature in enumerate(
        raw_features,
        start=1,
    ):
        properties = feature.get("properties", {})

        if not isinstance(properties, dict):
            raise ValueError(
                f"District feature {index} has invalid properties."
            )

        district_id = require_string(
            properties,
            "adm3_pcode",
            f"District feature {index}",
        )

        district_name = require_string(
            properties,
            "adm3_name",
            district_id,
        )

        province_id = require_string(
            properties,
            "adm2_pcode",
            district_id,
        )

        province_name = require_string(
            properties,
            "adm2_name",
            district_id,
        )

        region_id = require_string(
            properties,
            "adm1_pcode",
            district_id,
        )

        region_name = require_string(
            properties,
            "adm1_name",
            district_id,
        )

        if district_id in seen_ids:
            raise ValueError(
                f"Duplicate district ID: {district_id}"
            )

        if province_id not in valid_province_ids:
            raise ValueError(
                f"{district_id} references unknown province "
                f"{province_id}."
            )

        if region_id not in valid_region_ids:
            raise ValueError(
                f"{district_id} references unknown region "
                f"{region_id}."
            )

        if not district_id.startswith(province_id):
            raise ValueError(
                f"District ID {district_id} does not nest under "
                f"province ID {province_id}."
            )

        if not province_id.startswith(region_id):
            raise ValueError(
                f"Province ID {province_id} does not nest under "
                f"region ID {region_id}."
            )

        seen_ids.add(district_id)

        geometry = require_geometry(
            feature,
            district_id,
        )

        processed.append(
            {
                "type": "Feature",
                "properties": {
                    "district_id": district_id,
                    "district": district_name,
                    "province_id": province_id,
                    "province": province_name,
                    "region_id": region_id,
                    "region": region_name,
                },
                "geometry": geometry,
            }
        )

    if len(processed) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DISTRICT_COUNT} districts but "
            f"processed {len(processed)}."
        )

    return processed


# ---------------------------------------------------------------------------
# Cross-level validation
# ---------------------------------------------------------------------------

def validate_names(
    regions: list[dict[str, Any]],
    provinces: list[dict[str, Any]],
    districts: list[dict[str, Any]],
) -> None:
    region_names_by_id = {
        feature["properties"]["region_id"]:
            feature["properties"]["region"]
        for feature in regions
    }

    province_names_by_id = {
        feature["properties"]["province_id"]:
            feature["properties"]["province"]
        for feature in provinces
    }

    for feature in provinces:
        properties = feature["properties"]

        region_id = properties["region_id"]

        expected_region_name = (
            region_names_by_id[region_id]
        )

        if properties["region"] != expected_region_name:
            raise ValueError(
                f"{properties['province_id']} uses region name "
                f"{properties['region']!r}, but {region_id} is "
                f"{expected_region_name!r}."
            )

    for feature in districts:
        properties = feature["properties"]

        region_id = properties["region_id"]
        province_id = properties["province_id"]

        expected_region_name = (
            region_names_by_id[region_id]
        )

        expected_province_name = (
            province_names_by_id[province_id]
        )

        if properties["region"] != expected_region_name:
            raise ValueError(
                f"{properties['district_id']} uses region name "
                f"{properties['region']!r}, but {region_id} is "
                f"{expected_region_name!r}."
            )

        if properties["province"] != expected_province_name:
            raise ValueError(
                f"{properties['district_id']} uses province name "
                f"{properties['province']!r}, but {province_id} is "
                f"{expected_province_name!r}."
            )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_output_summary(
    label: str,
    path: Path,
    feature_count: int,
) -> None:
    size_bytes = path.stat().st_size

    size_mb = size_bytes / 1_000_000

    print(
        f"{label:<10} "
        f"{feature_count:>6,} features   "
        f"{size_bytes:>12,} bytes   "
        f"{size_mb:>7.3f} MB"
    )

    print(
        f"           {path}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Processing Peru administrative boundaries...\n"
    )

    admin1 = load_geojson(
        ADMIN1_INPUT
    )

    admin2 = load_geojson(
        ADMIN2_INPUT
    )

    admin3 = load_geojson(
        ADMIN3_INPUT
    )

    regions = process_regions(
        admin1["features"]
    )

    region_ids = {
        feature["properties"]["region_id"]
        for feature in regions
    }

    provinces = process_provinces(
        admin2["features"],
        region_ids,
    )

    province_ids = {
        feature["properties"]["province_id"]
        for feature in provinces
    }

    districts = process_districts(
        admin3["features"],
        region_ids,
        province_ids,
    )

    validate_names(
        regions,
        provinces,
        districts,
    )

    print("Validation passed:")
    print(
        f"  Regions:   {len(regions):,}"
    )
    print(
        f"  Provinces: {len(provinces):,}"
    )
    print(
        f"  Districts: {len(districts):,}"
    )

    print("")

    # Intermediate files
    write_geojson(
        REGIONS_INTERMEDIATE_OUTPUT,
        regions,
    )

    write_geojson(
        PROVINCES_INTERMEDIATE_OUTPUT,
        provinces,
    )

    write_geojson(
        DISTRICTS_INTERMEDIATE_OUTPUT,
        districts,
    )

    # Runtime files
    #
    # For now the runtime versions intentionally contain the same simplified
    # features as the intermediate versions. We can simplify geometry
    # separately afterward based on the resulting file sizes and visual
    # quality, rather than destroying detail during the first processing step.
    write_geojson(
        REGIONS_RUNTIME_OUTPUT,
        regions,
    )

    write_geojson(
        PROVINCES_RUNTIME_OUTPUT,
        provinces,
    )

    write_geojson(
        DISTRICTS_RUNTIME_OUTPUT,
        districts,
    )

    print("Runtime outputs:")

    print_output_summary(
        "Regions",
        REGIONS_RUNTIME_OUTPUT,
        len(regions),
    )

    print_output_summary(
        "Provinces",
        PROVINCES_RUNTIME_OUTPUT,
        len(provinces),
    )

    print_output_summary(
        "Districts",
        DISTRICTS_RUNTIME_OUTPUT,
        len(districts),
    )

    print("")

    print(
        "Peru administrative boundary processing complete."
    )


if __name__ == "__main__":
    main()