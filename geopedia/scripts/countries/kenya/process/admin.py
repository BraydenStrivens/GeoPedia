"""
Process Kenya's raw geoBoundaries administrative boundaries into GeoPedia's
canonical intermediate administrative GeoJSON files.

The raw ADM2 and ADM3 datasets do not contain parent administrative metadata,
so parent relationships are derived spatially:

    County (ADM1)
        -> Sub-county (ADM2)
            -> Ward (ADM3)

Inputs:
    data/raw/countries/kenya/geoBoundaries-KEN-ADM1.geojson
    data/raw/countries/kenya/geoBoundaries-KEN-ADM2.geojson
    data/raw/countries/kenya/geoBoundaries-KEN-ADM3.geojson

Outputs:
    data/intermediate/countries/kenya/admin/counties.geojson
    data/intermediate/countries/kenya/admin/sub-counties.geojson
    data/intermediate/countries/kenya/admin/wards.geojson
"""

import json
from pathlib import Path

from shapely.geometry import shape


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "kenya"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "kenya"
    / "admin"
)

COUNTIES_INPUT = RAW_DIR / "geoBoundaries-KEN-ADM1.geojson"
SUB_COUNTIES_INPUT = RAW_DIR / "geoBoundaries-KEN-ADM2.geojson"
WARDS_INPUT = RAW_DIR / "geoBoundaries-KEN-ADM3.geojson"

COUNTIES_OUTPUT = OUTPUT_DIR / "counties.geojson"
SUB_COUNTIES_OUTPUT = OUTPUT_DIR / "sub-counties.geojson"
WARDS_OUTPUT = OUTPUT_DIR / "wards.geojson"

EXPECTED_COUNTY_COUNT = 47
EXPECTED_SUB_COUNTY_COUNT = 290
EXPECTED_WARD_COUNT = 1452


def load_geojson(path: Path) -> dict:
    """Load and validate a GeoJSON FeatureCollection."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    return data


def write_geojson(
    path: Path,
    features: list[dict],
) -> None:
    """Write a compact canonical GeoJSON FeatureCollection."""
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


def process_counties(
    raw_data: dict,
) -> list[dict]:
    """Convert ADM1 features into canonical county features."""
    features = []
    seen_ids = set()
    seen_names = set()

    for feature in raw_data["features"]:
        properties = feature.get("properties", {})

        county_id = properties.get(
            "shapeISO",
            "",
        ).strip()

        county = properties.get(
            "shapeName",
            "",
        ).strip()

        if not county_id:
            raise ValueError(
                f"County is missing shapeISO: {county!r}"
            )

        if not county:
            raise ValueError(
                f"County {county_id!r} is missing shapeName."
            )

        if county_id in seen_ids:
            raise ValueError(
                f"Duplicate county ID: {county_id}"
            )

        if county in seen_names:
            raise ValueError(
                f"Duplicate county name: {county}"
            )

        seen_ids.add(county_id)
        seen_names.add(county)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "county_id": county_id,
                    "county": county,
                },
                "geometry": feature["geometry"],
            }
        )

    if len(features) != EXPECTED_COUNTY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_COUNTY_COUNT} counties, "
            f"found {len(features)}."
        )

    return features


def build_spatial_lookup(
    features: list[dict],
    id_property: str,
    name_property: str,
) -> list[dict]:
    """Build a spatial lookup from canonical administrative features."""
    lookup = []

    for feature in features:
        geometry = shape(feature["geometry"])

        if geometry.is_empty:
            raise ValueError(
                f"Empty geometry for "
                f"{feature['properties'][name_property]!r}."
            )

        lookup.append(
            {
                "id": feature["properties"][id_property],
                "name": feature["properties"][name_property],
                "properties": feature["properties"],
                "geometry": geometry,
            }
        )

    return lookup


def find_parent(
    child_geometry,
    parent_lookup: list[dict],
    child_name: str,
    parent_level: str,
) -> dict:
    """
    Find a child's parent administrative feature.

    A representative point is used first because it provides a simple,
    unambiguous match for normally aligned administrative boundaries. If the
    source boundary levels do not align closely enough for that method, the
    parent sharing the greatest polygon area with the child is used instead.
    """
    point = child_geometry.representative_point()

    matches = [
        parent
        for parent in parent_lookup
        if parent["geometry"].covers(point)
    ]

    if len(matches) == 1:
        return matches[0]

    overlaps = []

    for parent in parent_lookup:
        parent_geometry = parent["geometry"]

        if not child_geometry.intersects(
            parent_geometry
        ):
            continue

        intersection = child_geometry.intersection(
            parent_geometry
        )

        if intersection.is_empty:
            continue

        overlap_area = intersection.area

        if overlap_area <= 0:
            continue

        overlaps.append(
            (
                overlap_area,
                parent,
            )
        )

    if not overlaps:
        raise ValueError(
            f"{child_name!r} could not be matched to any "
            f"{parent_level} by representative point or "
            "polygon overlap."
        )

    overlaps.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return overlaps[0][1]
  

def process_sub_counties(
    raw_data: dict,
    county_lookup: list[dict],
) -> list[dict]:
    """
    Convert ADM2 features into canonical sub-county features and spatially
    derive each feature's parent county.
    """
    features = []
    seen_ids = set()
    seen_names = set()

    for feature in raw_data["features"]:
        properties = feature.get("properties", {})

        sub_county_id = properties.get(
            "shapeID",
            "",
        ).strip()

        sub_county = properties.get(
            "shapeName",
            "",
        ).strip()

        if not sub_county_id:
            raise ValueError(
                f"Sub-county is missing shapeID: {sub_county!r}"
            )

        if not sub_county:
            raise ValueError(
                f"Sub-county {sub_county_id!r} "
                "is missing shapeName."
            )

        if sub_county_id in seen_ids:
            raise ValueError(
                f"Duplicate sub-county ID: {sub_county_id}"
            )

        if sub_county in seen_names:
            raise ValueError(
                f"Duplicate sub-county name: {sub_county}"
            )

        seen_ids.add(sub_county_id)
        seen_names.add(sub_county)

        child_geometry = shape(
            feature["geometry"]
        )

        if child_geometry.is_empty:
            raise ValueError(
                f"Empty sub-county geometry for {sub_county!r}."
            )

        parent = find_parent(
            child_geometry,
            county_lookup,
            sub_county,
            "county",
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "sub_county_id": sub_county_id,
                    "sub_county": sub_county,
                    "county_id": parent["id"],
                    "county": parent["name"],
                },
                "geometry": feature["geometry"],
            }
        )

    if len(features) != EXPECTED_SUB_COUNTY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SUB_COUNTY_COUNT} sub-counties, "
            f"found {len(features)}."
        )

    return features


def process_wards(
    raw_data: dict,
    sub_county_lookup: list[dict],
) -> list[dict]:
    """
    Convert ADM3 features into canonical ward features and spatially derive
    each ward's parent sub-county. County metadata is inherited from that
    matched sub-county.
    """
    features = []
    seen_ids = set()

    for feature in raw_data["features"]:
        properties = feature.get("properties", {})

        ward_id = properties.get(
            "shapeID",
            "",
        ).strip()

        ward = properties.get(
            "shapeName",
            "",
        ).strip()

        if not ward_id:
            raise ValueError(
                f"Ward is missing shapeID: {ward!r}"
            )

        if not ward:
            raise ValueError(
                f"Ward {ward_id!r} is missing shapeName."
            )

        if ward_id in seen_ids:
            raise ValueError(
                f"Duplicate ward ID: {ward_id}"
            )

        seen_ids.add(ward_id)

        child_geometry = shape(
            feature["geometry"]
        )

        if child_geometry.is_empty:
            raise ValueError(
                f"Empty ward geometry for {ward!r}."
            )

        parent = find_parent(
            child_geometry,
            sub_county_lookup,
            ward,
            "sub-county",
        )

        parent_properties = parent["properties"]

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "ward_id": ward_id,
                    "ward": ward,
                    "sub_county_id": parent["id"],
                    "sub_county": parent["name"],
                    "county_id": parent_properties["county_id"],
                    "county": parent_properties["county"],
                },
                "geometry": feature["geometry"],
            }
        )

    if len(features) != EXPECTED_WARD_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_WARD_COUNT} wards, "
            f"found {len(features)}."
        )

    return features


def validate_parent_coverage(
    parent_features: list[dict],
    child_features: list[dict],
    parent_id_property: str,
    child_parent_id_property: str,
    parent_level: str,
) -> None:
    """Ensure every parent administrative feature contains children."""
    parent_ids = {
        feature["properties"][parent_id_property]
        for feature in parent_features
    }

    represented_ids = {
        feature["properties"][child_parent_id_property]
        for feature in child_features
    }

    missing = parent_ids - represented_ids

    if missing:
        raise ValueError(
            f"{parent_level} features without children: "
            f"{sorted(missing)}"
        )


def main() -> None:
    """Process Kenya's three administrative boundary levels."""
    print("Processing Kenya administrative boundaries...")
    print()

    raw_counties = load_geojson(
        COUNTIES_INPUT
    )

    raw_sub_counties = load_geojson(
        SUB_COUNTIES_INPUT
    )

    raw_wards = load_geojson(
        WARDS_INPUT
    )

    print(
        f"Raw counties:     {len(raw_counties['features'])}"
    )
    print(
        f"Raw sub-counties: {len(raw_sub_counties['features'])}"
    )
    print(
        f"Raw wards:        {len(raw_wards['features'])}"
    )
    print()

    counties = process_counties(
        raw_counties
    )

    county_lookup = build_spatial_lookup(
        counties,
        "county_id",
        "county",
    )

    sub_counties = process_sub_counties(
        raw_sub_counties,
        county_lookup,
    )

    validate_parent_coverage(
        counties,
        sub_counties,
        "county_id",
        "county_id",
        "County",
    )

    sub_county_lookup = build_spatial_lookup(
        sub_counties,
        "sub_county_id",
        "sub_county",
    )

    wards = process_wards(
        raw_wards,
        sub_county_lookup,
    )

    validate_parent_coverage(
        sub_counties,
        wards,
        "sub_county_id",
        "sub_county_id",
        "Sub-county",
    )

    write_geojson(
        COUNTIES_OUTPUT,
        counties,
    )

    write_geojson(
        SUB_COUNTIES_OUTPUT,
        sub_counties,
    )

    write_geojson(
        WARDS_OUTPUT,
        wards,
    )

    print("Kenya administrative processing complete.")
    print(f"  Counties:     {len(counties)}")
    print(f"  Sub-counties: {len(sub_counties)}")
    print(f"  Wards:        {len(wards)}")
    print()
    print(f"Counties:     {COUNTIES_OUTPUT}")
    print(f"Sub-counties: {SUB_COUNTIES_OUTPUT}")
    print(f"Wards:        {WARDS_OUTPUT}")


if __name__ == "__main__":
    main()