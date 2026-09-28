"""
Generate Chile road-prefix polygons from GeoPedia's canonical
administrative GeoJSON.

The Chilean regional road-prefix system can be represented using a mixture
of complete regions and provinces.

Most prefixes correspond to an entire region. In regions where prefixes
divide the territory more finely, province polygons are used instead.

Special cases
-------------
A:
    Arica y Parinacota + Tarapacá are dissolved into one feature.

E / F:
    Both prefixes are valid for the complete Valparaíso Region. The region
    remains one feature with both answers rather than inventing an
    unsupported E/F boundary.

W:
    Chiloé + Palena provinces are dissolved into one feature.

Input
-----
data/intermediate/countries/chile/admin/regions.geojson
data/intermediate/countries/chile/admin/provinces.geojson

Output
------
data/intermediate/countries/chile/road-prefixes.geojson

Run with:

    python scripts/countries/chile/process/road-prefixes.py
"""

import json
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


PROJECT_ROOT = Path(__file__).resolve().parents[4]

ADMIN_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "admin"
)

REGIONS_INPUT = ADMIN_DIR / "regions.geojson"
PROVINCES_INPUT = ADMIN_DIR / "provinces.geojson"

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "road-prefixes.geojson"
)


# ---------------------------------------------------------------------------
# Road-prefix mapping
# ---------------------------------------------------------------------------

# Complete regions used by each prefix.
#
# A spans two complete regions and is dissolved into one feature.
# E/F intentionally share the same Valparaíso Region feature.
REGION_PREFIXES = {
    "A": ["CL15", "CL01"],
    "B": ["CL02"],
    "C": ["CL03"],
    "D": ["CL04"],
    "E/F": ["CL05"],
    "G": ["CL13"],
    "H": ["CL06"],
    "N": ["CL16"],
    "T": ["CL14"],
    "X": ["CL11"],
    "Y": ["CL12"],
}


# Prefixes that divide regions along province boundaries.
PROVINCE_PREFIXES = {
    # Maule
    "J": ["CL073"],  # Curicó
    "K": ["CL071"],  # Talca
    "L": ["CL074"],  # Linares
    "M": ["CL072"],  # Cauquenes

    # Bío-Bío
    "O": ["CL081"],  # Concepción
    "P": ["CL082"],  # Arauco
    "Q": ["CL083"],  # Bío-Bío

    # La Araucanía
    "R": ["CL092"],  # Malleco
    "S": ["CL091"],  # Cautín

    # Los Lagos
    "U": ["CL103"],  # Osorno
    "V": ["CL101"],  # Llanquihue
    "W": [
        "CL102",     # Chiloé
        "CL104",     # Palena
    ],
}


EXPECTED_FEATURES = 23

EXPECTED_ANSWERS = {
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_features(
    path: Path,
) -> list[dict]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features",
        [],
    )

    if not isinstance(features, list):
        raise ValueError(
            f"{path} has an invalid features array."
        )

    return features


def index_features(
    features: list[dict],
    id_property: str,
) -> dict[str, dict]:
    indexed = {}

    for feature in features:
        properties = feature.get(
            "properties"
        )

        if not isinstance(properties, dict):
            raise ValueError(
                "Feature is missing properties."
            )

        feature_id = properties.get(
            id_property
        )

        if not feature_id:
            raise ValueError(
                f"Feature is missing {id_property}."
            )

        feature_id = str(feature_id)

        if feature_id in indexed:
            raise ValueError(
                f"Duplicate {id_property}: {feature_id}"
            )

        indexed[feature_id] = feature

    return indexed


def get_geometry(
    feature: dict,
):
    geometry = feature.get(
        "geometry"
    )

    if geometry is None:
        raise ValueError(
            "Feature is missing geometry."
        )

    result = shape(
        geometry
    )

    if result.is_empty:
        raise ValueError(
            "Feature has empty geometry."
        )

    return result


def dissolve_features(
    feature_ids: list[str],
    feature_index: dict[str, dict],
):
    geometries = []

    for feature_id in feature_ids:
        feature = feature_index.get(
            feature_id
        )

        if feature is None:
            raise ValueError(
                f"Could not find administrative "
                f"feature {feature_id}."
            )

        geometries.append(
            get_geometry(feature)
        )

    result = unary_union(
        geometries
    )

    if result.is_empty:
        raise ValueError(
            f"Dissolve produced empty geometry "
            f"for {feature_ids}."
        )

    if result.geom_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(
            f"Dissolve for {feature_ids} produced "
            f"{result.geom_type}."
        )

    return result


def create_feature(
    prefix_key: str,
    geometry,
) -> dict:
    answers = prefix_key.split("/")

    return {
        "type": "Feature",
        "properties": {
            "road_prefix_id": prefix_key,
            "road_prefixes": answers,
            "road_prefix": " / ".join(answers),
        },
        "geometry": mapping(
            geometry
        ),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_output(
    features: list[dict],
) -> None:
    if len(features) != EXPECTED_FEATURES:
        raise ValueError(
            f"Expected {EXPECTED_FEATURES} road-prefix "
            f"features, found {len(features)}."
        )

    ids = [
        feature["properties"]["road_prefix_id"]
        for feature in features
    ]

    if len(set(ids)) != len(ids):
        raise ValueError(
            "Road-prefix feature IDs are not unique."
        )

    answers = set()

    for feature in features:
        properties = feature[
            "properties"
        ]

        feature_answers = properties.get(
            "road_prefixes"
        )

        if not isinstance(
            feature_answers,
            list,
        ):
            raise ValueError(
                "road_prefixes must be an array."
            )

        answers.update(
            feature_answers
        )

    if answers != EXPECTED_ANSWERS:
        missing = sorted(
            EXPECTED_ANSWERS - answers
        )

        extra = sorted(
            answers - EXPECTED_ANSWERS
        )

        raise ValueError(
            "Road-prefix answers do not match expected "
            f"values. Missing: {missing}; extra: {extra}"
        )

    for feature in features:
        geometry = shape(
            feature["geometry"]
        )

        if geometry.is_empty:
            raise ValueError(
                "Output contains empty geometry."
            )

        if not geometry.is_valid:
            raise ValueError(
                "Output contains invalid geometry for "
                f"{feature['properties']['road_prefix_id']}."
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "Generating Chile road-prefix GeoJSON..."
    )

    region_features = load_features(
        REGIONS_INPUT
    )

    province_features = load_features(
        PROVINCES_INPUT
    )

    regions_by_id = index_features(
        region_features,
        "region_id",
    )

    provinces_by_id = index_features(
        province_features,
        "province_id",
    )

    output_features = []

    for prefix, region_ids in REGION_PREFIXES.items():
        geometry = dissolve_features(
            region_ids,
            regions_by_id,
        )

        output_features.append(
            create_feature(
                prefix,
                geometry,
            )
        )

    for prefix, province_ids in PROVINCE_PREFIXES.items():
        geometry = dissolve_features(
            province_ids,
            provinces_by_id,
        )

        output_features.append(
            create_feature(
                prefix,
                geometry,
            )
        )

    output_features.sort(
        key=lambda feature:
        feature["properties"]["road_prefix_id"]
    )

    validate_output(
        output_features
    )

    output = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_mb = (
        OUTPUT_PATH.stat().st_size
        / 1024
        / 1024
    )

    print()
    print(
        f"Features: {len(output_features)}"
    )
    print(
        f"Answers:  {len(EXPECTED_ANSWERS)}"
    )
    print(
        f"Size:     {size_mb:.2f} MB"
    )
    print(
        f"Saved:    {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()