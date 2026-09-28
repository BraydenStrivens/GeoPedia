"""
Generate Indonesia's major geographic-region GeoJSON from province polygons.

Purpose
-------
GeoPedia uses seven major geographic regions for Indonesia:

    Sumatera
    Jawa
    Nusa Tenggara
    Kalimantan
    Sulawesi
    Maluku
    Papua

These regions are not an administrative level in the source boundary dataset,
so no standalone source GeoJSON exists for them in the Indonesia raw data.

This script creates the region layer by assigning each of the 34 provinces in
the processed province GeoJSON to one of the seven regions and dissolving the
province geometries belonging to each region.

The resulting region GeoJSON serves two purposes:

1. It provides the geometry for GeoPedia's Indonesia regions quiz.
2. Its region metadata becomes the top-level grouping information propagated
   into the Province, Regency/City, Sub-District, and Village datasets by the
   Indonesia administrative-data processing pipeline.

Input
-----
data/raw/countries/indonesia/idn_admin_boundaries.geojson/idn_admin1.geojson

Expected source properties:

    adm1_pcode
    adm1_name

The province IDs are the stable administrative pcodes preserved from the
original Indonesia administrative boundary source.

Output
------
data/intermediate/countries/indonesia/regions.geojson

Each output feature contains:

    region_id
    region
    region_english

`region` is the Indonesian/native geographic name used by GeoPedia for
grouping and native-name recognition.

`region_english` contains the corresponding English geographic name.

The output contains exactly seven features.

Region membership
-----------------
The region assignments are intentionally keyed by stable province IDs rather
than province names. This prevents spelling changes or GeoPedia display-name
normalization from changing geographic membership.

The assignments correspond to the 34 provinces present in GeoPedia's 2020
Indonesia administrative boundary source. They should not be expanded with
newer Indonesian provinces unless the underlying administrative source data
is also updated.

Geometry
--------
All province geometries belonging to a region are combined using Shapely's
unary_union.

The resulting geometry is normalized to Polygon or MultiPolygon geometry.
Invalid dissolved geometries are repaired with make_valid when necessary.

The script validates that:

- exactly 34 input provinces exist;
- every expected province ID exists;
- every province belongs to exactly one region;
- no unexpected province IDs exist;
- all seven regions are generated;
- every output geometry is non-empty;
- every output geometry is Polygon or MultiPolygon;
- every output geometry is valid.

Usage
-----
Run from the GeoPedia project root:

    python scripts/countries/indonesia/process/regions.py

This script is the first processing step in Indonesia's geographic/admin
pipeline. It reads the raw Admin 1 province boundaries directly and creates
the intermediate region layer.

Run this script before:

    scripts/countries/indonesia/process/admin.py

The administrative processor then reads regions.geojson and propagates the
region metadata into Admin 1 through Admin 4.

After generating regions.geojson, the administrative processor can be updated
or rerun to propagate region metadata into all four administrative levels.
The simplification script can then generate public versions of all five
Indonesia geographic/admin GeoJSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "indonesia"
    / "idn_admin_boundaries.geojson"
)

INTERMEDIATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "indonesia"
)

PROVINCES_PATH = RAW_DIR / "idn_admin1.geojson"
REGIONS_PATH = INTERMEDIATE_DIR / "regions.geojson"


# ---------------------------------------------------------------------------
# Expected source data
# ---------------------------------------------------------------------------

EXPECTED_PROVINCE_COUNT = 34
EXPECTED_REGION_COUNT = 7


# ---------------------------------------------------------------------------
# Region definitions
# ---------------------------------------------------------------------------

REGIONS = {
    "sumatra": {
        "region": "Sumatera",
        "region_english": "Sumatra",
        "province_ids": {
            "ID11",  # Aceh
            "ID12",  # Sumatera Utara
            "ID13",  # Sumatera Barat
            "ID14",  # Riau
            "ID15",  # Jambi
            "ID16",  # Sumatera Selatan
            "ID17",  # Bengkulu
            "ID18",  # Lampung
            "ID19",  # Kepulauan Bangka Belitung
            "ID21",  # Kepulauan Riau
        },
    },
    "java": {
        "region": "Jawa",
        "region_english": "Java",
        "province_ids": {
            "ID31",  # Jakarta
            "ID32",  # Jawa Barat
            "ID33",  # Jawa Tengah
            "ID34",  # Yogyakarta
            "ID35",  # Jawa Timur
            "ID36",  # Banten
        },
    },
    "nusa-tenggara": {
        "region": "Nusa Tenggara",
        "region_english": "Lesser Sunda Islands",
        "province_ids": {
            "ID51",  # Bali
            "ID52",  # Nusa Tenggara Barat
            "ID53",  # Nusa Tenggara Timur
        },
    },
    "kalimantan": {
        "region": "Kalimantan",
        "region_english": "Kalimantan",
        "province_ids": {
            "ID61",  # Kalimantan Barat
            "ID62",  # Kalimantan Tengah
            "ID63",  # Kalimantan Selatan
            "ID64",  # Kalimantan Timur
            "ID65",  # Kalimantan Utara
        },
    },
    "sulawesi": {
        "region": "Sulawesi",
        "region_english": "Sulawesi",
        "province_ids": {
            "ID71",  # Sulawesi Utara
            "ID72",  # Sulawesi Tengah
            "ID73",  # Sulawesi Selatan
            "ID74",  # Sulawesi Tenggara
            "ID75",  # Gorontalo
            "ID76",  # Sulawesi Barat
        },
    },
    "maluku": {
        "region": "Maluku",
        "region_english": "Maluku Islands",
        "province_ids": {
            "ID81",  # Maluku
            "ID82",  # Maluku Utara
        },
    },
    "papua": {
        "region": "Papua",
        "region_english": "Western New Guinea",
        "province_ids": {
            "ID91",  # Papua Barat
            "ID94",  # Papua
        },
    },
}


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def extract_polygonal_geometry(geometry: Any) -> Polygon | MultiPolygon:
    """
    Return only the polygonal portions of a Shapely geometry.

    make_valid() can occasionally return a GeometryCollection containing
    polygonal and non-polygonal components. GeoPedia's map datasets only need
    Polygon and MultiPolygon geometry, so non-polygonal components are
    discarded.
    """

    if isinstance(geometry, Polygon):
        return geometry

    if isinstance(geometry, MultiPolygon):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []

        for part in geometry.geoms:
            if isinstance(part, Polygon):
                polygons.append(part)

            elif isinstance(part, MultiPolygon):
                polygons.extend(part.geoms)

            elif isinstance(part, GeometryCollection):
                nested = extract_polygonal_geometry(part)

                if isinstance(nested, Polygon):
                    polygons.append(nested)
                else:
                    polygons.extend(nested.geoms)

        if not polygons:
            raise ValueError(
                "GeometryCollection contains no polygonal geometry."
            )

        if len(polygons) == 1:
            return polygons[0]

        return MultiPolygon(polygons)

    raise ValueError(
        "Expected Polygon, MultiPolygon, or GeometryCollection; "
        f"received {geometry.geom_type}."
    )


def normalize_geometry(
    geometry: Any,
    *,
    region_name: str,
) -> Polygon | MultiPolygon:
    """
    Validate and normalize a dissolved region geometry.
    """

    if geometry.is_empty:
        raise ValueError(
            f"{region_name}: dissolved geometry is empty."
        )

    if not geometry.is_valid:
        geometry = make_valid(geometry)

    geometry = extract_polygonal_geometry(geometry)

    if geometry.is_empty:
        raise ValueError(
            f"{region_name}: geometry became empty after normalization."
        )

    if not geometry.is_valid:
        geometry = make_valid(geometry)
        geometry = extract_polygonal_geometry(geometry)

    if geometry.is_empty:
        raise ValueError(
            f"{region_name}: repaired geometry is empty."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{region_name}: geometry remains invalid after repair."
        )

    return geometry


# ---------------------------------------------------------------------------
# Region-definition validation
# ---------------------------------------------------------------------------

def validate_region_definitions() -> set[str]:
    """
    Validate the hard-coded province-to-region mapping.

    Returns the complete set of expected province IDs.
    """

    if len(REGIONS) != EXPECTED_REGION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} region definitions, "
            f"found {len(REGIONS)}."
        )

    province_to_region: dict[str, str] = {}

    for region_id, region_data in REGIONS.items():
        province_ids = region_data["province_ids"]

        if not province_ids:
            raise ValueError(
                f"{region_id}: region contains no provinces."
            )

        for province_id in province_ids:
            existing_region = province_to_region.get(province_id)

            if existing_region is not None:
                raise ValueError(
                    f"Province {province_id} is assigned to both "
                    f"{existing_region} and {region_id}."
                )

            province_to_region[province_id] = region_id

    expected_ids = set(province_to_region)

    if len(expected_ids) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            "Region definitions should contain exactly "
            f"{EXPECTED_PROVINCE_COUNT} unique province IDs, "
            f"but contain {len(expected_ids)}."
        )

    return expected_ids


# ---------------------------------------------------------------------------
# Province loading
# ---------------------------------------------------------------------------

def load_provinces(
    expected_province_ids: set[str],
) -> dict[str, dict[str, Any]]:
    """
    Load and validate the intermediate province GeoJSON.
    """

    if not PROVINCES_PATH.exists():
        raise FileNotFoundError(
            "Intermediate province GeoJSON does not exist:\n"
            f"  {PROVINCES_PATH}\n\n"
            "Run the Indonesia administrative processor first."
        )

    with PROVINCES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "provinces.geojson is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "provinces.geojson does not contain a valid features array."
        )

    if len(features) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_PROVINCE_COUNT} provinces, "
            f"found {len(features)}."
        )

    provinces: dict[str, dict[str, Any]] = {}

    for index, feature in enumerate(features, start=1):
        properties = feature.get("properties") or {}

        province_id = properties.get("adm1_pcode")
        province_name = properties.get("adm1_name")

        if not isinstance(province_id, str) or not province_id.strip():
            raise ValueError(
                f"Province feature {index} has no valid province_id."
            )

        if not isinstance(province_name, str) or not province_name.strip():
            raise ValueError(
                f"Province {province_id} has no valid province name."
            )

        if province_id in provinces:
            raise ValueError(
                f"Duplicate province_id found: {province_id}"
            )

        geometry_data = feature.get("geometry")

        if geometry_data is None:
            raise ValueError(
                f"{province_id} ({province_name}) has no geometry."
            )

        geometry = shape(geometry_data)

        if geometry.is_empty:
            raise ValueError(
                f"{province_id} ({province_name}) has empty geometry."
            )

        if geometry.geom_type not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError(
                f"{province_id} ({province_name}) has unexpected "
                f"geometry type {geometry.geom_type}."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"{province_id} ({province_name}) has invalid geometry. "
                "The intermediate province dataset should already have "
                "valid geometry."
            )

        provinces[province_id] = {
            "name": province_name,
            "geometry": geometry,
        }

    actual_ids = set(provinces)

    missing_ids = expected_province_ids - actual_ids
    unexpected_ids = actual_ids - expected_province_ids

    if missing_ids:
        raise ValueError(
            "Province GeoJSON is missing expected IDs: "
            + ", ".join(sorted(missing_ids))
        )

    if unexpected_ids:
        raise ValueError(
            "Province GeoJSON contains unexpected IDs: "
            + ", ".join(sorted(unexpected_ids))
        )

    return provinces


# ---------------------------------------------------------------------------
# Region generation
# ---------------------------------------------------------------------------

def build_region_features(
    provinces: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Dissolve province polygons into the seven region features.
    """

    features: list[dict[str, Any]] = []

    for region_id, region_data in REGIONS.items():
        region_name = region_data["region"]
        region_english = region_data["region_english"]
        province_ids = region_data["province_ids"]

        geometries = [
            provinces[province_id]["geometry"]
            for province_id in province_ids
        ]

        dissolved = unary_union(geometries)

        dissolved = normalize_geometry(
            dissolved,
            region_name=region_name,
        )

        feature = {
            "type": "Feature",
            "properties": {
                "region_id": region_id,
                "region": region_name,
                "region_english": region_english,
            },
            "geometry": mapping(dissolved),
        }

        features.append(feature)

        print(
            f"  {region_name:<15} "
            f"{len(province_ids):>2} province(s)  "
            f"{dissolved.geom_type}"
        )

    if len(features) != EXPECTED_REGION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} output regions, "
            f"generated {len(features)}."
        )

    return features


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_regions(
    features: list[dict[str, Any]],
) -> None:
    """
    Write the generated region FeatureCollection.
    """

    REGIONS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    with REGIONS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Generating Indonesia geographic regions...")
    print()

    print("Validating region definitions...")
    expected_province_ids = validate_region_definitions()

    print(
        f"  Regions:   {len(REGIONS):,}"
    )
    print(
        f"  Provinces: {len(expected_province_ids):,}"
    )
    print()

    print("Loading raw Admin 1 provinces...")
    provinces = load_provinces(expected_province_ids)

    print(
        f"  Loaded: {len(provinces):,} provinces"
    )
    print()

    print("Dissolving provinces into regions...")
    features = build_region_features(provinces)

    print()
    print("Writing regions GeoJSON...")
    write_regions(features)

    size_mb = REGIONS_PATH.stat().st_size / (1024 * 1024)

    print()
    print("=" * 78)
    print("Indonesia region generation complete.")
    print("=" * 78)
    print()
    print(f"  Regions: {len(features):,}")
    print(f"  Output:  {REGIONS_PATH.relative_to(PROJECT_ROOT)}")
    print(f"  Size:    {size_mb:.2f} MB")


if __name__ == "__main__":
    main()