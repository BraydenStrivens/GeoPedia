"""
Process Tunisia's raw administrative boundary GeoJSON into GeoPedia's
canonical administrative schema.

Source
------
data/raw/countries/tunisia/tun_admin_boundaries.geojson/

    tun_admin1.geojson
    tun_admin2.geojson
    tun_admin3.geojson
    tun_admin4.geojson

Output
------
data/intermediate/countries/tunisia/admin/

    governorates.geojson
    delegations.geojson
    municipalities.geojson

ADM1 contains six broad geographic regions. These regions do not receive
their own runtime GeoJSON because GeoPedia does not provide a region quiz
for them. Their IDs and names are instead propagated to ADM2-ADM4 features
for quiz grouping.

Canonical properties
--------------------
Governorates:
    governorate_id
    governorate
    native_governorate
    region_id
    region
    native_region

Delegations:
    delegation_id
    delegation
    native_delegation
    governorate_id
    governorate
    native_governorate
    region_id
    region
    native_region

Municipalities:
    municipality_id
    municipality
    native_municipality
    delegation_id
    delegation
    native_delegation
    governorate_id
    governorate
    native_governorate
    region_id
    region
    native_region

The source PCODE values are retained as stable GeoPedia IDs.

English names come from the source's primary administrative-name fields.
Arabic names come from the corresponding name1 fields.

Parent names are resolved from the processed parent records rather than
copied independently from descendant features. This keeps the hierarchy
internally consistent.

Geometry is preserved unchanged. Runtime simplification is handled by the
separate Tunisia administrative simplification script.
"""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "tunisia"
    / "tun_admin_boundaries.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "tunisia"
    / "admin"
)


ADM1_INPUT = RAW_DIR / "tun_admin1.geojson"
ADM2_INPUT = RAW_DIR / "tun_admin2.geojson"
ADM3_INPUT = RAW_DIR / "tun_admin3.geojson"
ADM4_INPUT = RAW_DIR / "tun_admin4.geojson"

GOVERNORATES_OUTPUT = OUTPUT_DIR / "governorates.geojson"
DELEGATIONS_OUTPUT = OUTPUT_DIR / "delegations.geojson"
MUNICIPALITIES_OUTPUT = OUTPUT_DIR / "municipalities.geojson"


EXPECTED_REGIONS = 6
EXPECTED_GOVERNORATES = 24
EXPECTED_DELEGATIONS = 264
EXPECTED_MUNICIPALITIES = 2084


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
            f"{path} has an invalid features array."
        )

    return data


def get_properties(feature: dict) -> dict:
    """Return a feature's properties or raise an error."""
    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError(
            "GeoJSON feature is missing properties."
        )

    return properties


def require_string(
    properties: dict,
    property_name: str,
) -> str:
    """Return a required non-empty string property."""
    value = properties.get(property_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Missing or invalid required property: "
            f"{property_name}"
        )

    return value.strip()


def optional_string(
    properties: dict,
    property_name: str,
) -> str | None:
    """Return an optional trimmed string property."""
    value = properties.get(property_name)

    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(
            f"Invalid string property: {property_name}"
        )

    value = value.strip()

    return value or None


def validate_feature_count(
    features: list[dict],
    expected_count: int,
    label: str,
) -> None:
    """Verify that a source level has the expected feature count."""
    if len(features) != expected_count:
        raise ValueError(
            f"Expected {expected_count} {label}, "
            f"found {len(features)}."
        )


def validate_unique_ids(
    features: list[dict],
    id_property: str,
    label: str,
) -> None:
    """Verify that all canonical feature IDs are unique."""
    ids = [
        require_string(
            get_properties(feature),
            id_property,
        )
        for feature in features
    ]

    if len(set(ids)) != len(ids):
        raise ValueError(
            f"{label} IDs are not unique."
        )


def create_feature(
    source_feature: dict,
    properties: dict,
) -> dict:
    """Create a canonical feature while preserving source geometry."""
    geometry = source_feature.get("geometry")

    if not isinstance(geometry, dict):
        raise ValueError(
            "GeoJSON feature is missing geometry."
        )

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry,
    }


def create_feature_collection(
    features: list[dict],
) -> dict:
    """Create a compact canonical GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def write_feature_collection(
    path: Path,
    features: list[dict],
) -> None:
    """Write a canonical FeatureCollection as compact UTF-8 GeoJSON."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = create_feature_collection(
        features
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------


def process_regions(
    source_features: list[dict],
) -> dict[str, dict]:
    """
    Process ADM1 region metadata.

    Regions are retained only in memory because their geometry is not needed
    by GeoPedia. Their canonical metadata is propagated to all lower levels.
    """
    validate_feature_count(
        source_features,
        EXPECTED_REGIONS,
        "regions",
    )

    regions: dict[str, dict] = {}

    for feature in source_features:
        properties = get_properties(feature)

        region_id = require_string(
            properties,
            "adm1_pcode",
        )

        if region_id in regions:
            raise ValueError(
                f"Duplicate region ID: {region_id}"
            )

        regions[region_id] = {
            "region_id": region_id,
            "region": require_string(
                properties,
                "adm1_name",
            ),
            "native_region": optional_string(
                properties,
                "adm1_name1",
            ),
        }

    return regions


# ---------------------------------------------------------------------------
# Governorates
# ---------------------------------------------------------------------------


def process_governorates(
    source_features: list[dict],
    regions: dict[str, dict],
) -> tuple[list[dict], dict[str, dict]]:
    """Process ADM2 governorates and resolve their parent regions."""
    validate_feature_count(
        source_features,
        EXPECTED_GOVERNORATES,
        "governorates",
    )

    features = []
    governorates: dict[str, dict] = {}

    for feature in source_features:
        source = get_properties(feature)

        governorate_id = require_string(
            source,
            "adm2_pcode",
        )

        region_id = require_string(
            source,
            "adm1_pcode",
        )

        region = regions.get(region_id)

        if region is None:
            raise ValueError(
                f"Governorate {governorate_id} references "
                f"unknown region {region_id}."
            )

        if governorate_id in governorates:
            raise ValueError(
                f"Duplicate governorate ID: {governorate_id}"
            )

        properties = {
            "governorate_id": governorate_id,
            "governorate": require_string(
                source,
                "adm2_name",
            ),
            "native_governorate": optional_string(
                source,
                "adm2_name1",
            ),
            "region_id": region["region_id"],
            "region": region["region"],
            "native_region": region["native_region"],
        }

        governorates[governorate_id] = properties

        features.append(
            create_feature(
                feature,
                properties,
            )
        )

    validate_unique_ids(
        features,
        "governorate_id",
        "Governorate",
    )

    return features, governorates


# ---------------------------------------------------------------------------
# Delegations
# ---------------------------------------------------------------------------


def process_delegations(
    source_features: list[dict],
    governorates: dict[str, dict],
    regions: dict[str, dict],
) -> tuple[list[dict], dict[str, dict]]:
    """Process ADM3 delegations and resolve their parent hierarchy."""
    validate_feature_count(
        source_features,
        EXPECTED_DELEGATIONS,
        "delegations",
    )

    features = []
    delegations: dict[str, dict] = {}

    for feature in source_features:
        source = get_properties(feature)

        delegation_id = require_string(
            source,
            "adm3_pcode",
        )

        governorate_id = require_string(
            source,
            "adm2_pcode",
        )

        region_id = require_string(
            source,
            "adm1_pcode",
        )

        governorate = governorates.get(
            governorate_id
        )

        if governorate is None:
            raise ValueError(
                f"Delegation {delegation_id} references "
                f"unknown governorate {governorate_id}."
            )

        region = regions.get(
            region_id
        )

        if region is None:
            raise ValueError(
                f"Delegation {delegation_id} references "
                f"unknown region {region_id}."
            )

        if governorate["region_id"] != region_id:
            raise ValueError(
                f"Delegation {delegation_id} has inconsistent "
                f"governorate/region hierarchy."
            )

        if delegation_id in delegations:
            raise ValueError(
                f"Duplicate delegation ID: {delegation_id}"
            )

        properties = {
            "delegation_id": delegation_id,
            "delegation": require_string(
                source,
                "adm3_name",
            ),
            "native_delegation": optional_string(
                source,
                "adm3_name1",
            ),
            "governorate_id": governorate["governorate_id"],
            "governorate": governorate["governorate"],
            "native_governorate": governorate["native_governorate"],
            "region_id": region["region_id"],
            "region": region["region"],
            "native_region": region["native_region"],
        }

        delegations[delegation_id] = properties

        features.append(
            create_feature(
                feature,
                properties,
            )
        )

    validate_unique_ids(
        features,
        "delegation_id",
        "Delegation",
    )

    return features, delegations


# ---------------------------------------------------------------------------
# Municipalities
# ---------------------------------------------------------------------------


def process_municipalities(
    source_features: list[dict],
    delegations: dict[str, dict],
    governorates: dict[str, dict],
    regions: dict[str, dict],
) -> list[dict]:
    """Process ADM4 municipalities and resolve their complete hierarchy."""
    validate_feature_count(
        source_features,
        EXPECTED_MUNICIPALITIES,
        "municipalities",
    )

    features = []

    for feature in source_features:
        source = get_properties(feature)

        municipality_id = require_string(
            source,
            "adm4_pcode",
        )

        delegation_id = require_string(
            source,
            "adm3_pcode",
        )

        governorate_id = require_string(
            source,
            "adm2_pcode",
        )

        region_id = require_string(
            source,
            "adm1_pcode",
        )

        delegation = delegations.get(
            delegation_id
        )

        if delegation is None:
            raise ValueError(
                f"Municipality {municipality_id} references "
                f"unknown delegation {delegation_id}."
            )

        governorate = governorates.get(
            governorate_id
        )

        if governorate is None:
            raise ValueError(
                f"Municipality {municipality_id} references "
                f"unknown governorate {governorate_id}."
            )

        region = regions.get(
            region_id
        )

        if region is None:
            raise ValueError(
                f"Municipality {municipality_id} references "
                f"unknown region {region_id}."
            )

        if delegation["governorate_id"] != governorate_id:
            raise ValueError(
                f"Municipality {municipality_id} has inconsistent "
                f"delegation/governorate hierarchy."
            )

        if delegation["region_id"] != region_id:
            raise ValueError(
                f"Municipality {municipality_id} has inconsistent "
                f"delegation/region hierarchy."
            )

        if governorate["region_id"] != region_id:
            raise ValueError(
                f"Municipality {municipality_id} has inconsistent "
                f"governorate/region hierarchy."
            )

        properties = {
            "municipality_id": municipality_id,
            "municipality": require_string(
                source,
                "adm4_name",
            ),
            "native_municipality": optional_string(
                source,
                "adm4_name1",
            ),
            "delegation_id": delegation["delegation_id"],
            "delegation": delegation["delegation"],
            "native_delegation": delegation["native_delegation"],
            "governorate_id": governorate["governorate_id"],
            "governorate": governorate["governorate"],
            "native_governorate": governorate["native_governorate"],
            "region_id": region["region_id"],
            "region": region["region"],
            "native_region": region["native_region"],
        }

        features.append(
            create_feature(
                feature,
                properties,
            )
        )

    validate_unique_ids(
        features,
        "municipality_id",
        "Municipality",
    )

    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Process Tunisia's ADM1-ADM4 administrative hierarchy."""
    print(
        "Processing Tunisia administrative boundaries..."
    )

    adm1_data = load_feature_collection(
        ADM1_INPUT
    )

    adm2_data = load_feature_collection(
        ADM2_INPUT
    )

    adm3_data = load_feature_collection(
        ADM3_INPUT
    )

    adm4_data = load_feature_collection(
        ADM4_INPUT
    )

    regions = process_regions(
        adm1_data["features"]
    )

    governorate_features, governorates = process_governorates(
        adm2_data["features"],
        regions,
    )

    delegation_features, delegations = process_delegations(
        adm3_data["features"],
        governorates,
        regions,
    )

    municipality_features = process_municipalities(
        adm4_data["features"],
        delegations,
        governorates,
        regions,
    )

    write_feature_collection(
        GOVERNORATES_OUTPUT,
        governorate_features,
    )

    write_feature_collection(
        DELEGATIONS_OUTPUT,
        delegation_features,
    )

    write_feature_collection(
        MUNICIPALITIES_OUTPUT,
        municipality_features,
    )

    print()
    print(
        "Tunisia administrative processing complete."
    )

    print(
        f"  Regions (grouping only): {len(regions)}"
    )

    print(
        f"  Governorates:            {len(governorate_features)}"
    )

    print(
        f"  Delegations:             {len(delegation_features)}"
    )

    print(
        f"  Municipalities:          {len(municipality_features)}"
    )

    print()
    print("Output:")

    print(
        f"  {GOVERNORATES_OUTPUT}"
    )

    print(
        f"  {DELEGATIONS_OUTPUT}"
    )

    print(
        f"  {MUNICIPALITIES_OUTPUT}"
    )


if __name__ == "__main__":
    main()