"""
Process Indonesia administrative boundaries into GeoPedia's canonical schema.

Purpose
-------
This script streams the raw Indonesia administrative-boundary GeoJSON files,
keeps only the properties required by GeoPedia, validates the administrative
hierarchy, repairs invalid polygon geometry, attaches GeoPedia's major
geographic-region metadata, and writes canonical intermediate GeoJSON files
for later simplification.

Indonesia's seven major geographic regions are generated separately by:

    scripts/countries/indonesia/process/regions.py

That script must be run before this one. It creates:

    data/intermediate/countries/indonesia/regions.geojson

This administrative processor loads that region dataset, validates its
metadata, and assigns every province to one of the seven regions using stable
Admin 1 pcodes. Region information is then propagated through all four
administrative levels.

Processing order
----------------
Run the Indonesia processing pipeline in this order:

    python scripts/countries/indonesia/process/regions.py
    python scripts/countries/indonesia/process/admin.py
    python scripts/countries/indonesia/process/simplify-admin.py
    python scripts/countries/indonesia/generate/admin-quiz-data.py

Inputs
------
Raw administrative boundaries:

    data/raw/countries/indonesia/idn_admin_boundaries.geojson/
        idn_admin1.geojson
        idn_admin2.geojson
        idn_admin3.geojson
        idn_admin4.geojson

Generated region metadata:

    data/intermediate/countries/indonesia/
        regions.geojson

Outputs
-------
    data/intermediate/countries/indonesia/
        provinces.geojson
        regencies.geojson
        sub-districts.geojson
        villages.geojson

Canonical properties
---------------------
provinces.geojson:
    province_id
    province
    region_id
    region
    region_english

regencies.geojson:
    regency_id
    regency
    province_id
    province
    region_id
    region
    region_english

sub-districts.geojson:
    sub_district_id
    sub_district
    regency_id
    regency
    province_id
    province
    region_id
    region
    region_english

villages.geojson:
    village_id
    village
    sub_district_id
    sub_district
    regency_id
    regency
    province_id
    province
    region_id
    region
    region_english

Region properties
-----------------
The seven geographic regions are:

    Sumatera
    Jawa
    Nusa Tenggara
    Kalimantan
    Sulawesi
    Maluku
    Papua

`region` contains the Indonesian/native name.

`region_english` contains the English name. Some names are identical in both
languages.

Province-to-region membership is keyed by stable province pcode rather than
province name. This makes the relationship independent of display-name
normalization.

Province-name normalization
---------------------------
Two source province names are shortened for GeoPedia:

    Dki Jakarta                 -> Jakarta
    Daerah Istimewa Yogyakarta -> Yogyakarta

The stable province IDs remain unchanged. The normalized names are propagated
through all child administrative datasets.

Stable IDs
----------
The source administrative pcodes are preserved as GeoPedia's stable IDs:

    adm1_pcode -> province_id
    adm2_pcode -> regency_id
    adm3_pcode -> sub_district_id
    adm4_pcode -> village_id

Geometry repair
---------------
The source inspection found a small number of invalid geometries in Admin 2,
Admin 3, and Admin 4. Invalid geometries are repaired with Shapely make_valid().

If make_valid() returns a GeometryCollection, only polygonal components are
retained and combined into a Polygon or MultiPolygon. The script then verifies
that every output geometry is non-empty, polygonal, and valid.

Hierarchy validation
--------------------
Every child feature is checked against the canonical IDs and names present in
its parent dataset.

This also ensures that normalized province names and region metadata are
propagated consistently instead of trusting repeated source strings at every
administrative level.

Expected feature counts
-----------------------
    Provinces:        34
    Regencies:       522
    Sub-Districts: 7,069
    Villages:     81,912

The large source files are streamed with ijson rather than loaded completely
into memory.

Requirements
------------
    pip install ijson shapely

Run from the GeoPedia project root:

    python scripts/countries/indonesia/process/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import ijson
from shapely.geometry import GeometryCollection, MultiPolygon, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "indonesia"
    / "idn_admin_boundaries.geojson"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "indonesia"
)

REGIONS_PATH = OUTPUT_DIRECTORY / "regions.geojson"


# ---------------------------------------------------------------------------
# Expected counts
# ---------------------------------------------------------------------------

EXPECTED_REGION_COUNT = 7
EXPECTED_PROVINCE_COUNT = 34


# ---------------------------------------------------------------------------
# Display-name normalization
# ---------------------------------------------------------------------------

PROVINCE_NAME_OVERRIDES = {
    "Dki Jakarta": "Jakarta",
    "Daerah Istimewa Yogyakarta": "Yogyakarta",
}


# ---------------------------------------------------------------------------
# Geographic regions
# ---------------------------------------------------------------------------

REGION_PROVINCES = {
    "sumatra": {
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
    "java": {
        "ID31",  # Jakarta
        "ID32",  # Jawa Barat
        "ID33",  # Jawa Tengah
        "ID34",  # Yogyakarta
        "ID35",  # Jawa Timur
        "ID36",  # Banten
    },
    "nusa-tenggara": {
        "ID51",  # Bali
        "ID52",  # Nusa Tenggara Barat
        "ID53",  # Nusa Tenggara Timur
    },
    "kalimantan": {
        "ID61",  # Kalimantan Barat
        "ID62",  # Kalimantan Tengah
        "ID63",  # Kalimantan Selatan
        "ID64",  # Kalimantan Timur
        "ID65",  # Kalimantan Utara
    },
    "sulawesi": {
        "ID71",  # Sulawesi Utara
        "ID72",  # Sulawesi Tengah
        "ID73",  # Sulawesi Selatan
        "ID74",  # Sulawesi Tenggara
        "ID75",  # Gorontalo
        "ID76",  # Sulawesi Barat
    },
    "maluku": {
        "ID81",  # Maluku
        "ID82",  # Maluku Utara
    },
    "papua": {
        "ID91",  # Papua Barat
        "ID94",  # Papua
    },
}


# ---------------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------------

DATASETS = (
    {
        "label": "Provinces",
        "input": RAW_DIRECTORY / "idn_admin1.geojson",
        "output": OUTPUT_DIRECTORY / "provinces.geojson",
        "expected_count": 34,
        "properties": (
            ("province_id", "adm1_pcode"),
            ("province", "adm1_name"),
        ),
        "id_property": "province_id",
    },
    {
        "label": "Regencies",
        "input": RAW_DIRECTORY / "idn_admin2.geojson",
        "output": OUTPUT_DIRECTORY / "regencies.geojson",
        "expected_count": 522,
        "properties": (
            ("regency_id", "adm2_pcode"),
            ("regency", "adm2_name"),
            ("province_id", "adm1_pcode"),
            ("province", "adm1_name"),
        ),
        "id_property": "regency_id",
    },
    {
        "label": "Sub-Districts",
        "input": RAW_DIRECTORY / "idn_admin3.geojson",
        "output": OUTPUT_DIRECTORY / "sub-districts.geojson",
        "expected_count": 7_069,
        "properties": (
            ("sub_district_id", "adm3_pcode"),
            ("sub_district", "adm3_name"),
            ("regency_id", "adm2_pcode"),
            ("regency", "adm2_name"),
            ("province_id", "adm1_pcode"),
            ("province", "adm1_name"),
        ),
        "id_property": "sub_district_id",
    },
    {
        "label": "Villages",
        "input": RAW_DIRECTORY / "idn_admin4.geojson",
        "output": OUTPUT_DIRECTORY / "villages.geojson",
        "expected_count": 81_912,
        "properties": (
            ("village_id", "adm4_pcode"),
            ("village", "adm4_name"),
            ("sub_district_id", "adm3_pcode"),
            ("sub_district", "adm3_name"),
            ("regency_id", "adm2_pcode"),
            ("regency", "adm2_name"),
            ("province_id", "adm1_pcode"),
            ("province", "adm1_name"),
        ),
        "id_property": "village_id",
    },
)


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

RegionMetadata = tuple[
    str,  # region
    str,  # region_english
]

RegionIndex = dict[
    str,  # region_id
    RegionMetadata,
]

ProvinceRegionIndex = dict[
    str,  # province_id
    str,  # region_id
]

ProvinceIndex = dict[
    str,  # province_id
    tuple[
        str,  # province
        str,  # region_id
        str,  # region
    ],
]

RegencyIndex = dict[
    str,  # regency_id
    tuple[
        str,  # regency
        str,  # province_id
        str,  # province
        str,  # region_id
        str,  # region
    ],
]

SubDistrictIndex = dict[
    str,  # sub_district_id
    tuple[
        str,  # sub_district
        str,  # regency_id
        str,  # regency
        str,  # province_id
        str,  # province
        str,  # region_id
        str,  # region
    ],
]


# ---------------------------------------------------------------------------
# Streaming helpers
# ---------------------------------------------------------------------------

def stream_features(
    path: Path,
) -> Iterator[dict[str, Any]]:
    """Stream features from a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required source file not found:\n{path}"
        )

    with path.open(
        "rb",
    ) as file:
        yield from ijson.items(
            file,
            "features.item",
        )


# ---------------------------------------------------------------------------
# Property helpers
# ---------------------------------------------------------------------------

def require_properties(
    feature: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    """Return a feature's properties object."""

    properties = feature.get(
        "properties"
    )

    if not isinstance(
        properties,
        dict,
    ):
        raise ValueError(
            f"{label} has missing or malformed properties."
        )

    return properties


def require_string(
    properties: dict[str, Any],
    property_name: str,
    *,
    label: str,
) -> str:
    """Read a required non-empty string property."""

    value = properties.get(
        property_name
    )

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{label} has non-string property {property_name!r}: "
            f"{value!r}"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{label} has blank property {property_name!r}."
        )

    return value


def canonical_properties(
    source_properties: dict[str, Any],
    mappings: tuple[tuple[str, str], ...],
    *,
    label: str,
) -> dict[str, str]:
    """Build GeoPedia's canonical property object."""

    return {
        output_name: require_string(
            source_properties,
            source_name,
            label=label,
        )
        for (
            output_name,
            source_name,
        ) in mappings
    }


def normalize_province_name(
    province: str,
) -> str:
    """Apply GeoPedia's province display-name normalization."""

    return PROVINCE_NAME_OVERRIDES.get(
        province,
        province,
    )


# ---------------------------------------------------------------------------
# Region loading and validation
# ---------------------------------------------------------------------------

def build_province_region_index() -> ProvinceRegionIndex:
    """
    Build the stable province-ID-to-region-ID lookup.

    Also validates that all 34 expected provinces occur exactly once.
    """

    province_regions: ProvinceRegionIndex = {}

    for (
        region_id,
        province_ids,
    ) in REGION_PROVINCES.items():
        for province_id in province_ids:
            if province_id in province_regions:
                raise ValueError(
                    f"Province {province_id!r} is assigned to multiple "
                    "geographic regions."
                )

            province_regions[
                province_id
            ] = region_id

    if len(province_regions) != EXPECTED_PROVINCE_COUNT:
        raise ValueError(
            "Province-to-region mapping should contain exactly "
            f"{EXPECTED_PROVINCE_COUNT} provinces, but contains "
            f"{len(province_regions)}."
        )

    return province_regions


def load_regions() -> tuple[
    RegionIndex,
    ProvinceRegionIndex,
]:
    """
    Load and validate the generated intermediate regions GeoJSON.

    Region geometry is intentionally not used here. The administrative
    hierarchy can inherit region membership deterministically through stable
    province IDs, avoiding spatial intersection against thousands of child
    features.
    """

    if not REGIONS_PATH.exists():
        raise FileNotFoundError(
            "Generated Indonesia region GeoJSON was not found:\n"
            f"{REGIONS_PATH}\n\n"
            "Run this first:\n"
            "  python scripts/countries/indonesia/process/regions.py"
        )

    with REGIONS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "regions.geojson is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            "regions.geojson does not contain a valid features array."
        )

    if len(features) != EXPECTED_REGION_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_REGION_COUNT} regions, "
            f"found {len(features)}."
        )

    regions: RegionIndex = {}

    for index, feature in enumerate(
        features,
        start=1,
    ):
        properties = require_properties(
            feature,
            label=f"Region feature {index}",
        )

        region_id = require_string(
            properties,
            "region_id",
            label=f"Region feature {index}",
        )

        region = require_string(
            properties,
            "region",
            label=f"Region feature {index}",
        )

        region_english = require_string(
            properties,
            "region_english",
            label=f"Region feature {index}",
        )

        if region_id in regions:
            raise ValueError(
                f"Duplicate region_id {region_id!r}."
            )

        regions[
            region_id
        ] = (
            region,
            region_english,
        )

    expected_region_ids = set(
        REGION_PROVINCES
    )

    actual_region_ids = set(
        regions
    )

    missing_region_ids = (
        expected_region_ids
        - actual_region_ids
    )

    unexpected_region_ids = (
        actual_region_ids
        - expected_region_ids
    )

    if missing_region_ids:
        raise ValueError(
            "regions.geojson is missing expected region IDs: "
            + ", ".join(
                sorted(
                    missing_region_ids
                )
            )
        )

    if unexpected_region_ids:
        raise ValueError(
            "regions.geojson contains unexpected region IDs: "
            + ", ".join(
                sorted(
                    unexpected_region_ids
                )
            )
        )

    province_regions = build_province_region_index()

    return (
        regions,
        province_regions,
    )


def add_region_properties(
    properties: dict[str, str],
    regions: RegionIndex,
    province_regions: ProvinceRegionIndex,
    *,
    label: str,
) -> None:
    """Attach region metadata based on a feature's province ID."""

    province_id = properties[
        "province_id"
    ]

    region_id = province_regions.get(
        province_id
    )

    if region_id is None:
        raise ValueError(
            f"{label} references province {province_id!r}, which has "
            "no geographic-region assignment."
        )

    region_metadata = regions.get(
        region_id
    )

    if region_metadata is None:
        raise ValueError(
            f"{label} maps to unknown region_id {region_id!r}."
        )

    (
        region,
        region_english,
    ) = region_metadata

    properties[
        "region_id"
    ] = region_id

    properties[
        "region"
    ] = region


# ---------------------------------------------------------------------------
# Geometry repair
# ---------------------------------------------------------------------------

def extract_polygonal_geometry(
    geometry: BaseGeometry,
    *,
    label: str,
) -> BaseGeometry:
    """
    Return only Polygon/MultiPolygon components from a repaired geometry.

    make_valid() can occasionally return a GeometryCollection containing
    polygonal and lower-dimensional pieces. Administrative boundary datasets
    need only the polygonal components.
    """

    if geometry.geom_type in {
        "Polygon",
        "MultiPolygon",
    }:
        return geometry

    if not isinstance(
        geometry,
        GeometryCollection,
    ):
        raise ValueError(
            f"{label} produced unsupported geometry type "
            f"{geometry.geom_type!r}."
        )

    polygons = []

    for component in geometry.geoms:
        if component.geom_type == "Polygon":
            polygons.append(
                component
            )

        elif component.geom_type == "MultiPolygon":
            polygons.extend(
                component.geoms
            )

    if not polygons:
        raise ValueError(
            f"{label} contains no polygonal geometry after repair."
        )

    if len(
        polygons
    ) == 1:
        return polygons[0]

    return MultiPolygon(
        polygons
    )


def process_geometry(
    feature: dict[str, Any],
    *,
    label: str,
) -> tuple[BaseGeometry, bool]:
    """
    Parse and validate a feature geometry.

    Returns:
        (geometry, repaired)

    repaired is True only when make_valid() was required.
    """

    geometry_data = feature.get(
        "geometry"
    )

    if not isinstance(
        geometry_data,
        dict,
    ):
        raise ValueError(
            f"{label} has missing or malformed geometry."
        )

    try:
        geometry = shape(
            geometry_data
        )

    except Exception as error:
        raise ValueError(
            f"{label} could not be parsed by Shapely: {error}"
        ) from error

    if geometry.is_empty:
        raise ValueError(
            f"{label} has empty geometry."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{label} has unexpected geometry type "
            f"{geometry.geom_type!r}."
        )

    repaired = False

    if not geometry.is_valid:
        repaired = True

        geometry = make_valid(
            geometry
        )

        geometry = extract_polygonal_geometry(
            geometry,
            label=label,
        )

    if geometry.is_empty:
        raise ValueError(
            f"{label} has empty geometry after repair."
        )

    if geometry.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"{label} has unexpected geometry type "
            f"{geometry.geom_type!r} after repair."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"{label} remains invalid after geometry repair."
        )

    return (
        geometry,
        repaired,
    )


# ---------------------------------------------------------------------------
# GeoJSON writer
# ---------------------------------------------------------------------------

class FeatureCollectionWriter:
    """
    Stream GeoJSON features directly to disk.

    This avoids holding large processed datasets such as the 81,912-feature
    village dataset in memory.
    """

    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = path
        self.file = None
        self.first_feature = True

    def __enter__(
        self,
    ) -> "FeatureCollectionWriter":
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.file = self.path.open(
            "w",
            encoding="utf-8",
        )

        self.file.write(
            '{"type":"FeatureCollection","features":['
        )

        return self

    def write(
        self,
        *,
        properties: dict[str, str],
        geometry: BaseGeometry,
    ) -> None:
        if self.file is None:
            raise RuntimeError(
                "FeatureCollectionWriter is not open."
            )

        if not self.first_feature:
            self.file.write(
                ","
            )

        feature = {
            "type": "Feature",
            "properties": properties,
            "geometry": mapping(
                geometry
            ),
        }

        json.dump(
            feature,
            self.file,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

        self.first_feature = False

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        if self.file is None:
            return

        if exc_type is None:
            self.file.write(
                "]}"
            )

        self.file.close()

        if (
            exc_type is not None
            and self.path.exists()
        ):
            self.path.unlink()


# ---------------------------------------------------------------------------
# Hierarchy validation
# ---------------------------------------------------------------------------

def validate_regency_parent(
    properties: dict[str, str],
    provinces: ProvinceIndex,
    *,
    label: str,
) -> None:
    """Validate an Admin 2 feature against its canonical Admin 1 parent."""

    province_id = properties[
        "province_id"
    ]

    parent = provinces.get(
        province_id
    )

    if parent is None:
        raise ValueError(
            f"{label} references unknown province_id {province_id!r}."
        )

    (
        expected_province,
        expected_region_id,
        expected_region,
    ) = parent

    actual = (
        properties["province"],
        properties["region_id"],
        properties["region"],
    )

    expected = (
        expected_province,
        expected_region_id,
        expected_region,
    )

    if actual != expected:
        raise ValueError(
            f"{label} has inconsistent Admin 1/region hierarchy.\n"
            f"Actual:   {actual}\n"
            f"Expected: {expected}"
        )


def validate_sub_district_parent(
    properties: dict[str, str],
    regencies: RegencyIndex,
    *,
    label: str,
) -> None:
    """Validate an Admin 3 feature against its canonical Admin 2 parent."""

    regency_id = properties[
        "regency_id"
    ]

    parent = regencies.get(
        regency_id
    )

    if parent is None:
        raise ValueError(
            f"{label} references unknown regency_id {regency_id!r}."
        )

    (
        expected_regency,
        expected_province_id,
        expected_province,
        expected_region_id,
        expected_region,
    ) = parent

    actual = (
        properties["regency"],
        properties["province_id"],
        properties["province"],
        properties["region_id"],
        properties["region"],
    )

    expected = (
        expected_regency,
        expected_province_id,
        expected_province,
        expected_region_id,
        expected_region,
    )

    if actual != expected:
        raise ValueError(
            f"{label} has inconsistent Admin 2/Admin 1/region hierarchy.\n"
            f"Actual:   {actual}\n"
            f"Expected: {expected}"
        )


def validate_village_parent(
    properties: dict[str, str],
    sub_districts: SubDistrictIndex,
    *,
    label: str,
) -> None:
    """Validate an Admin 4 feature against its canonical Admin 3 parent."""

    sub_district_id = properties[
        "sub_district_id"
    ]

    parent = sub_districts.get(
        sub_district_id
    )

    if parent is None:
        raise ValueError(
            f"{label} references unknown sub_district_id "
            f"{sub_district_id!r}."
        )

    (
        expected_sub_district,
        expected_regency_id,
        expected_regency,
        expected_province_id,
        expected_province,
        expected_region_id,
        expected_region,
    ) = parent

    actual = (
        properties["sub_district"],
        properties["regency_id"],
        properties["regency"],
        properties["province_id"],
        properties["province"],
        properties["region_id"],
        properties["region"],
    )

    expected = (
        expected_sub_district,
        expected_regency_id,
        expected_regency,
        expected_province_id,
        expected_province,
        expected_region_id,
        expected_region,
    )

    if actual != expected:
        raise ValueError(
            f"{label} has inconsistent Admin 3/Admin 2/Admin 1/region "
            "hierarchy.\n"
            f"Actual:   {actual}\n"
            f"Expected: {expected}"
        )


# ---------------------------------------------------------------------------
# Dataset processing
# ---------------------------------------------------------------------------

def process_provinces(
    dataset: dict[str, Any],
    regions: RegionIndex,
    province_regions: ProvinceRegionIndex,
) -> ProvinceIndex:
    """Process Admin 1 and return the canonical province lookup."""

    provinces: ProvinceIndex = {}

    count = 0
    repaired_count = 0

    with FeatureCollectionWriter(
        dataset["output"]
    ) as writer:
        for feature in stream_features(
            dataset["input"]
        ):
            count += 1

            source_properties = require_properties(
                feature,
                label=f"Province feature {count:,}",
            )

            properties = canonical_properties(
                source_properties,
                dataset["properties"],
                label=f"Province feature {count:,}",
            )

            province_id = properties[
                "province_id"
            ]

            if province_id in provinces:
                raise ValueError(
                    f"Duplicate province_id {province_id!r}."
                )

            properties[
                "province"
            ] = normalize_province_name(
                properties["province"]
            )

            add_region_properties(
                properties,
                regions,
                province_regions,
                label=f"Province {province_id}",
            )

            geometry, repaired = process_geometry(
                feature,
                label=f"Province {province_id}",
            )

            if repaired:
                repaired_count += 1

            provinces[
                province_id
            ] = (
                properties["province"],
                properties["region_id"],
                properties["region"],
            )

            writer.write(
                properties=properties,
                geometry=geometry,
            )

    validate_count(
        count,
        dataset,
    )

    if set(provinces) != set(province_regions):
        missing = set(province_regions) - set(provinces)
        unexpected = set(provinces) - set(province_regions)

        raise ValueError(
            "Processed province IDs do not exactly match the "
            "province-to-region mapping.\n"
            f"Missing: {sorted(missing)}\n"
            f"Unexpected: {sorted(unexpected)}"
        )

    print_dataset_result(
        dataset,
        count=count,
        repaired_count=repaired_count,
    )

    return provinces


def process_regencies(
    dataset: dict[str, Any],
    provinces: ProvinceIndex,
    regions: RegionIndex,
    province_regions: ProvinceRegionIndex,
) -> RegencyIndex:
    """Process Admin 2 and return the canonical regency lookup."""

    regencies: RegencyIndex = {}

    count = 0
    repaired_count = 0

    with FeatureCollectionWriter(
        dataset["output"]
    ) as writer:
        for feature in stream_features(
            dataset["input"]
        ):
            count += 1

            source_properties = require_properties(
                feature,
                label=f"Regency feature {count:,}",
            )

            properties = canonical_properties(
                source_properties,
                dataset["properties"],
                label=f"Regency feature {count:,}",
            )

            regency_id = properties[
                "regency_id"
            ]

            if regency_id in regencies:
                raise ValueError(
                    f"Duplicate regency_id {regency_id!r}."
                )

            properties[
                "province"
            ] = normalize_province_name(
                properties["province"]
            )

            add_region_properties(
                properties,
                regions,
                province_regions,
                label=f"Regency {regency_id}",
            )

            validate_regency_parent(
                properties,
                provinces,
                label=f"Regency {regency_id}",
            )

            geometry, repaired = process_geometry(
                feature,
                label=f"Regency {regency_id}",
            )

            if repaired:
                repaired_count += 1

            regencies[
                regency_id
            ] = (
                properties["regency"],
                properties["province_id"],
                properties["province"],
                properties["region_id"],
                properties["region"],
            )

            writer.write(
                properties=properties,
                geometry=geometry,
            )

    validate_count(
        count,
        dataset,
    )

    print_dataset_result(
        dataset,
        count=count,
        repaired_count=repaired_count,
    )

    return regencies


def process_sub_districts(
    dataset: dict[str, Any],
    regencies: RegencyIndex,
    regions: RegionIndex,
    province_regions: ProvinceRegionIndex,
) -> SubDistrictIndex:
    """Process Admin 3 and return the canonical sub-district lookup."""

    sub_districts: SubDistrictIndex = {}

    count = 0
    repaired_count = 0

    with FeatureCollectionWriter(
        dataset["output"]
    ) as writer:
        for feature in stream_features(
            dataset["input"]
        ):
            count += 1

            source_properties = require_properties(
                feature,
                label=f"Sub-district feature {count:,}",
            )

            properties = canonical_properties(
                source_properties,
                dataset["properties"],
                label=f"Sub-district feature {count:,}",
            )

            sub_district_id = properties[
                "sub_district_id"
            ]

            if sub_district_id in sub_districts:
                raise ValueError(
                    f"Duplicate sub_district_id {sub_district_id!r}."
                )

            properties[
                "province"
            ] = normalize_province_name(
                properties["province"]
            )

            add_region_properties(
                properties,
                regions,
                province_regions,
                label=f"Sub-district {sub_district_id}",
            )

            validate_sub_district_parent(
                properties,
                regencies,
                label=f"Sub-district {sub_district_id}",
            )

            geometry, repaired = process_geometry(
                feature,
                label=f"Sub-district {sub_district_id}",
            )

            if repaired:
                repaired_count += 1

            sub_districts[
                sub_district_id
            ] = (
                properties["sub_district"],
                properties["regency_id"],
                properties["regency"],
                properties["province_id"],
                properties["province"],
                properties["region_id"],
                properties["region"],
            )

            writer.write(
                properties=properties,
                geometry=geometry,
            )

    validate_count(
        count,
        dataset,
    )

    print_dataset_result(
        dataset,
        count=count,
        repaired_count=repaired_count,
    )

    return sub_districts


def process_villages(
    dataset: dict[str, Any],
    sub_districts: SubDistrictIndex,
    regions: RegionIndex,
    province_regions: ProvinceRegionIndex,
) -> None:
    """Process Admin 4."""

    village_ids: set[str] = set()

    count = 0
    repaired_count = 0

    with FeatureCollectionWriter(
        dataset["output"]
    ) as writer:
        for feature in stream_features(
            dataset["input"]
        ):
            count += 1

            source_properties = require_properties(
                feature,
                label=f"Village feature {count:,}",
            )

            properties = canonical_properties(
                source_properties,
                dataset["properties"],
                label=f"Village feature {count:,}",
            )

            village_id = properties[
                "village_id"
            ]

            if village_id in village_ids:
                raise ValueError(
                    f"Duplicate village_id {village_id!r}."
                )

            village_ids.add(
                village_id
            )

            properties[
                "province"
            ] = normalize_province_name(
                properties["province"]
            )

            add_region_properties(
                properties,
                regions,
                province_regions,
                label=f"Village {village_id}",
            )

            validate_village_parent(
                properties,
                sub_districts,
                label=f"Village {village_id}",
            )

            geometry, repaired = process_geometry(
                feature,
                label=f"Village {village_id}",
            )

            if repaired:
                repaired_count += 1

            writer.write(
                properties=properties,
                geometry=geometry,
            )

            if count % 10_000 == 0:
                print(
                    f"    Processed {count:,} villages..."
                )

    validate_count(
        count,
        dataset,
    )

    print_dataset_result(
        dataset,
        count=count,
        repaired_count=repaired_count,
    )


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

def validate_count(
    count: int,
    dataset: dict[str, Any],
) -> None:
    """Validate a processed dataset's feature count."""

    expected_count = dataset[
        "expected_count"
    ]

    if count != expected_count:
        raise ValueError(
            f"{dataset['label']} feature-count mismatch: "
            f"expected {expected_count:,}, got {count:,}."
        )


def file_size_mb(
    path: Path,
) -> float:
    """Return a file size in MiB."""

    return (
        path.stat().st_size
        / (1024 * 1024)
    )


def print_dataset_result(
    dataset: dict[str, Any],
    *,
    count: int,
    repaired_count: int,
) -> None:
    """Print a compact summary for one processed dataset."""

    print(
        f"  Features:          {count:,}"
    )
    print(
        f"  Repaired geometry: {repaired_count:,}"
    )
    print(
        f"  Output size:       "
        f"{file_size_mb(dataset['output']):,.2f} MB"
    )
    print(
        f"  Output:            "
        f"{dataset['output'].relative_to(PROJECT_ROOT)}"
    )
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Processing Indonesia administrative boundaries..."
    )
    print()

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Loading geographic regions..."
    )

    (
        regions,
        province_regions,
    ) = load_regions()

    print(
        f"  Regions:   {len(regions):,}"
    )
    print(
        f"  Provinces: {len(province_regions):,} region assignments"
    )
    print()

    print(
        "Processing Admin 1 - Provinces..."
    )

    provinces = process_provinces(
        DATASETS[0],
        regions,
        province_regions,
    )

    print(
        "Processing Admin 2 - Regencies..."
    )

    regencies = process_regencies(
        DATASETS[1],
        provinces,
        regions,
        province_regions,
    )

    print(
        "Processing Admin 3 - Sub-Districts..."
    )

    sub_districts = process_sub_districts(
        DATASETS[2],
        regencies,
        regions,
        province_regions,
    )

    print(
        "Processing Admin 4 - Villages..."
    )

    process_villages(
        DATASETS[3],
        sub_districts,
        regions,
        province_regions,
    )

    print(
        "=" * 78
    )
    print(
        "Indonesia administrative-boundary processing complete."
    )
    print(
        "=" * 78
    )
    print()
    print(
        f"Regions:       {len(regions):,}"
    )
    print(
        f"Provinces:     {len(provinces):,}"
    )
    print(
        f"Regencies:     {len(regencies):,}"
    )
    print(
        f"Sub-Districts: {len(sub_districts):,}"
    )
    print(
        "Villages:      81,912"
    )


if __name__ == "__main__":
    main()