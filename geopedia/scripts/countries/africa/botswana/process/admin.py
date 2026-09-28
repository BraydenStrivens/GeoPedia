"""
Process Botswana's district and sub-district boundaries for GeoPedia.

Districts come from the SimpleMaps Botswana boundary dataset, which contains
10 rural districts and 6 urban districts.

Sub-districts come from geoBoundaries ADM2. Their parent hierarchy is assigned
explicitly because the ADM2 source does not include ADM1 parent properties and
its boundaries do not perfectly nest within the separate district source.

Twenty-four sub-districts are assigned to one of Botswana's 10 rural
districts. The Gaborone sub-district is assigned to the Gaborone urban
district, producing 11 district grouping values for the sub-district quiz.

The processed files are already small enough for runtime use, so they are
written directly to the public data directory without a separate
simplification stage.

Inputs:
    data/raw/countries/botswana/bw.json
    data/raw/countries/botswana/geoBoundaries-BWA-ADM2.geojson

Outputs:
    public/data/countries/botswana/geojson/districts.geojson
    public/data/countries/botswana/geojson/sub-districts.geojson
"""

import json
from pathlib import Path

from shapely.geometry import shape


RAW_ROOT = Path("data/raw/countries/botswana")

DISTRICTS_SOURCE = RAW_ROOT / "bw.json"
SUB_DISTRICTS_SOURCE = (
    RAW_ROOT / "geoBoundaries-BWA-ADM2.geojson"
)

OUTPUT_ROOT = Path(
    "public/data/countries/botswana/geojson"
)

DISTRICTS_OUTPUT = OUTPUT_ROOT / "districts.geojson"
SUB_DISTRICTS_OUTPUT = OUTPUT_ROOT / "sub-districts.geojson"

EXPECTED_DISTRICT_COUNT = 16
EXPECTED_SUB_DISTRICT_COUNT = 25


# Canonical district names keyed by the IDs supplied by the district source.
#
# Keeping this explicit validates that the source still represents the exact
# 16-district system expected by GeoPedia.
DISTRICTS_BY_ID = {
    "BWCE": "Central",
    "BWCH": "Chobe",
    "BWFR": "Francistown",
    "BWGA": "Gaborone",
    "BWGH": "Ghanzi",
    "BWJW": "Jwaneng",
    "BWKG": "Kgalagadi",
    "BWKL": "Kgatleng",
    "BWKW": "Kweneng",
    "BWLO": "Lobatse",
    "BWNE": "North East",
    "BWNW": "North West",
    "BWSP": "Selibe Phikwe",
    "BWSE": "South East",
    "BWSO": "Southern",
    "BWST": "Sowa Town",
}


# Parent district for every geoBoundaries ADM2 feature.
#
# The 10 rural districts provide the normal administrative grouping. Gaborone
# is retained as its own group because geoBoundaries contains a Gaborone ADM2
# feature and it does not fit cleanly inside any single rural district.
SUB_DISTRICT_PARENT_IDS = {
    "Barolong": "BWSO",
    "Bobonong": "BWCE",
    "Chobe": "BWCH",
    "Gaborone": "BWGA",
    "Gemsbok": "BWKG",
    "Ghanzi": "BWGH",
    "Hukunsti": "BWKG",
    "Kgatleng": "BWKL",
    "Kweneng North": "BWKW",
    "Kweneng South": "BWKW",
    "Lethlakane": "BWCE",
    "Machaneng": "BWCE",
    "Mahalapye": "BWCE",
    "Masungu": "BWNE",
    "Ngamiland East": "BWNW",
    "Ngamiland West": "BWNW",
    "Ngwaketse Central": "BWSO",
    "Ngwaketse North": "BWSO",
    "Ngwaketse South": "BWSO",
    "Palapye": "BWCE",
    "Serowe": "BWCE",
    "South East": "BWSE",
    "Tshabong": "BWKG",
    "Tuli": "BWCE",
    "Tutume": "BWCE",
}


def load_feature_collection(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def validate_geometry(
    geometry_data: dict | None,
    feature_name: str,
) -> None:
    """Validate that a feature has usable polygon geometry."""

    if geometry_data is None:
        raise ValueError(
            f"{feature_name} has no geometry."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"{feature_name} has empty geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{feature_name} has invalid geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{feature_name} has unsupported geometry type "
            f"{geometry.geom_type}."
        )


def process_districts(source: dict) -> dict:
    """Convert the 16-district source to GeoPedia's canonical schema."""

    features = source["features"]

    if len(features) != EXPECTED_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected Botswana district count: "
            f"expected {EXPECTED_DISTRICT_COUNT}, "
            f"found {len(features)}."
        )

    processed = []
    seen_ids = set()
    seen_names = set()

    for feature in features:
        properties = feature.get("properties") or {}

        district_id = properties.get("id")
        source_name = properties.get("name")

        if not isinstance(district_id, str):
            raise ValueError(
                f"Invalid district ID: {district_id!r}"
            )

        if not isinstance(source_name, str):
            raise ValueError(
                f"Invalid district name: {source_name!r}"
            )

        if district_id in seen_ids:
            raise ValueError(
                f"Duplicate district ID: {district_id}"
            )

        expected_name = DISTRICTS_BY_ID.get(district_id)

        if expected_name is None:
            raise ValueError(
                f"Unexpected district ID: {district_id}"
            )

        # SimpleMaps supplies the names in uppercase. Compare
        # case-insensitively while emitting GeoPedia's canonical casing.
        if source_name.strip().casefold() != expected_name.casefold():
            raise ValueError(
                f"Unexpected name for {district_id}: "
                f"{source_name!r}; expected {expected_name!r}."
            )

        if expected_name in seen_names:
            raise ValueError(
                f"Duplicate district name: {expected_name}"
            )

        geometry_data = feature.get("geometry")

        validate_geometry(
            geometry_data,
            expected_name,
        )

        processed.append(
            {
                "type": "Feature",
                "properties": {
                    "district_id": district_id,
                    "district": expected_name,
                },
                "geometry": geometry_data,
            }
        )

        seen_ids.add(district_id)
        seen_names.add(expected_name)

    expected_ids = set(DISTRICTS_BY_ID)

    if seen_ids != expected_ids:
        missing = sorted(expected_ids - seen_ids)
        unexpected = sorted(seen_ids - expected_ids)

        raise ValueError(
            "Unexpected Botswana district set. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )

    processed.sort(
        key=lambda feature:
        feature["properties"]["district"]
    )

    return {
        "type": "FeatureCollection",
        "features": processed,
    }


def process_sub_districts(source: dict) -> dict:
    """Convert ADM2 features and attach their canonical district parents."""

    features = source["features"]

    if len(features) != EXPECTED_SUB_DISTRICT_COUNT:
        raise ValueError(
            "Unexpected Botswana sub-district count: "
            f"expected {EXPECTED_SUB_DISTRICT_COUNT}, "
            f"found {len(features)}."
        )

    processed = []
    seen_ids = set()
    seen_names = set()

    for feature in features:
        properties = feature.get("properties") or {}

        sub_district_id = properties.get("shapeID")
        sub_district = properties.get("shapeName")

        if not isinstance(sub_district_id, str) or not sub_district_id:
            raise ValueError(
                f"Invalid sub-district ID: {sub_district_id!r}"
            )

        if not isinstance(sub_district, str) or not sub_district:
            raise ValueError(
                f"Invalid sub-district name: {sub_district!r}"
            )

        if sub_district_id in seen_ids:
            raise ValueError(
                f"Duplicate sub-district ID: {sub_district_id}"
            )

        if sub_district in seen_names:
            raise ValueError(
                f"Duplicate sub-district name: {sub_district}"
            )

        district_id = SUB_DISTRICT_PARENT_IDS.get(
            sub_district
        )

        if district_id is None:
            raise ValueError(
                "No parent district mapping for sub-district "
                f"{sub_district!r}."
            )

        district = DISTRICTS_BY_ID[district_id]

        geometry_data = feature.get("geometry")

        validate_geometry(
            geometry_data,
            sub_district,
        )

        processed.append(
            {
                "type": "Feature",
                "properties": {
                    "sub_district_id": sub_district_id,
                    "sub_district": sub_district,
                    "district_id": district_id,
                    "district": district,
                },
                "geometry": geometry_data,
            }
        )

        seen_ids.add(sub_district_id)
        seen_names.add(sub_district)

    expected_names = set(SUB_DISTRICT_PARENT_IDS)

    if seen_names != expected_names:
        missing = sorted(expected_names - seen_names)
        unexpected = sorted(seen_names - expected_names)

        raise ValueError(
            "Unexpected Botswana sub-district set. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )

    processed.sort(
        key=lambda feature:
        feature["properties"]["sub_district"]
    )

    return {
        "type": "FeatureCollection",
        "features": processed,
    }


def write_geojson(
    data: dict,
    path: Path,
) -> None:
    """Write compact runtime GeoJSON to the public data directory."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    """Process Botswana's district and sub-district datasets."""

    print("Processing Botswana administrative boundaries...")
    print()

    districts_source = load_feature_collection(
        DISTRICTS_SOURCE
    )
    sub_districts_source = load_feature_collection(
        SUB_DISTRICTS_SOURCE
    )

    districts = process_districts(
        districts_source
    )
    sub_districts = process_sub_districts(
        sub_districts_source
    )

    write_geojson(
        districts,
        DISTRICTS_OUTPUT,
    )
    write_geojson(
        sub_districts,
        SUB_DISTRICTS_OUTPUT,
    )

    district_count = len(districts["features"])
    sub_district_count = len(sub_districts["features"])

    district_size = (
        DISTRICTS_OUTPUT.stat().st_size / 1_000_000
    )
    sub_district_size = (
        SUB_DISTRICTS_OUTPUT.stat().st_size / 1_000_000
    )

    grouping_values = {
        feature["properties"]["district"]
        for feature in sub_districts["features"]
    }

    print(
        f"Districts       {district_count:>3} features | "
        f"{district_size:.2f} MB"
    )
    print(
        f"Sub-districts   {sub_district_count:>3} features | "
        f"{sub_district_size:.2f} MB"
    )
    print(
        f"ADM2 groups     {len(grouping_values):>3} districts"
    )

    print()
    print(f"Output: {DISTRICTS_OUTPUT}")
    print(f"Output: {SUB_DISTRICTS_OUTPUT}")
    print()
    print("Botswana administrative processing complete.")


if __name__ == "__main__":
    main()