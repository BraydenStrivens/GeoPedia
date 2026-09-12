"""
Generates Ecuador's geographic fixed-line telephone area-code regions by
dissolving GeoPedia's existing province geometries.

Input:
    public/data/countries/ecuador/geojson/provinces.geojson

Output:
    public/data/countries/ecuador/geojson/area-codes.geojson

Ecuador uses six geographic fixed-line area-code regions:

02 - Pichincha, Santo Domingo de los Tsáchilas
03 - Tungurahua, Cotopaxi, Chimborazo, Bolívar, Pastaza
04 - Guayas, Santa Elena
05 - Manabí, Los Ríos, Galápagos
06 - Esmeraldas, Carchi, Imbabura, Sucumbíos, Orellana, Napo
07 - El Oro, Azuay, Cañar, Loja, Morona Santiago, Zamora Chinchipe
"""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

INPUT_PATH = Path(
    "public/data/countries/ecuador/geojson/provinces.geojson"
)

OUTPUT_PATH = Path(
    "public/data/countries/ecuador/geojson/area-codes.geojson"
)


# ---------------------------------------------------------------------------
# Area-code definitions
# ---------------------------------------------------------------------------

AREA_CODE_DEFINITIONS = {
    "02": [
        "EC17",  # Pichincha
        "EC23",  # Santo Domingo de los Tsáchilas
    ],
    "03": [
        "EC18",  # Tungurahua
        "EC05",  # Cotopaxi
        "EC06",  # Chimborazo
        "EC02",  # Bolívar
        "EC16",  # Pastaza
    ],
    "04": [
        "EC09",  # Guayas
        "EC24",  # Santa Elena
    ],
    "05": [
        "EC13",  # Manabí
        "EC12",  # Los Ríos
        "EC20",  # Galápagos
    ],
    "06": [
        "EC08",  # Esmeraldas
        "EC04",  # Carchi
        "EC10",  # Imbabura
        "EC21",  # Sucumbíos
        "EC22",  # Orellana
        "EC15",  # Napo
    ],
    "07": [
        "EC07",  # El Oro
        "EC01",  # Azuay
        "EC03",  # Cañar
        "EC11",  # Loja
        "EC14",  # Morona Santiago
        "EC19",  # Zamora Chinchipe
    ],
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Input GeoJSON does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Expected input GeoJSON to be a FeatureCollection."
        )

    return data


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_input_features(features: list[dict]) -> dict[str, dict]:
    """
    Validates the province GeoJSON and indexes features by province_id.
    """

    by_id: dict[str, dict] = {}

    for feature in features:
        properties = feature.get("properties", {})

        province_id = properties.get("province_id")
        province_name = properties.get("province")

        if not isinstance(province_id, str):
            raise ValueError(
                "Province feature is missing a string province_id."
            )

        if not isinstance(province_name, str):
            raise ValueError(
                f"{province_id} is missing a string province name."
            )

        if province_id in by_id:
            raise ValueError(
                f"Duplicate province_id in input GeoJSON: {province_id}"
            )

        if feature.get("geometry") is None:
            raise ValueError(
                f"{province_id} has no geometry."
            )

        by_id[province_id] = feature

    if len(by_id) != 24:
        raise ValueError(
            f"Expected 24 Ecuador provinces but found {len(by_id)}."
        )

    return by_id


def validate_area_code_definitions(
    provinces_by_id: dict[str, dict],
) -> None:
    """
    Ensures every Ecuador province appears exactly once in the area-code
    mapping.
    """

    assigned_ids = [
        province_id
        for province_ids in AREA_CODE_DEFINITIONS.values()
        for province_id in province_ids
    ]

    if len(assigned_ids) != 24:
        raise ValueError(
            f"Expected 24 province assignments but found "
            f"{len(assigned_ids)}."
        )

    if len(set(assigned_ids)) != 24:
        duplicates = sorted(
            province_id
            for province_id in set(assigned_ids)
            if assigned_ids.count(province_id) > 1
        )

        raise ValueError(
            "Province IDs appear in multiple area-code regions: "
            + ", ".join(duplicates)
        )

    input_ids = set(provinces_by_id)
    assigned_id_set = set(assigned_ids)

    missing = sorted(input_ids - assigned_id_set)
    unknown = sorted(assigned_id_set - input_ids)

    if missing:
        raise ValueError(
            "Provinces missing from area-code definitions: "
            + ", ".join(missing)
        )

    if unknown:
        raise ValueError(
            "Unknown province IDs in area-code definitions: "
            + ", ".join(unknown)
        )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def create_area_code_feature(
    area_code: str,
    province_ids: list[str],
    provinces_by_id: dict[str, dict],
) -> dict:
    """
    Dissolves all provinces belonging to one area code into a single feature.
    """

    province_features = [
        provinces_by_id[province_id]
        for province_id in province_ids
    ]

    province_names = [
        feature["properties"]["province"]
        for feature in province_features
    ]

    geometries = [
        shape(feature["geometry"])
        for feature in province_features
    ]

    dissolved_geometry = unary_union(geometries)

    if dissolved_geometry.is_empty:
        raise ValueError(
            f"Dissolved geometry for area code {area_code} is empty."
        )

    if not dissolved_geometry.is_valid:
        repaired_geometry = dissolved_geometry.buffer(0)

        if repaired_geometry.is_empty or not repaired_geometry.is_valid:
            raise ValueError(
                f"Unable to produce valid geometry for area code "
                f"{area_code}."
            )

        dissolved_geometry = repaired_geometry

    return {
        "type": "Feature",
        "properties": {
            "area_code_id": area_code,
            "area_code": area_code,
            "province_ids": province_ids,
            "provinces": province_names,
        },
        "geometry": mapping(dissolved_geometry),
    }


def generate_area_code_geojson(
    provinces_by_id: dict[str, dict],
) -> dict:
    features = [
        create_area_code_feature(
            area_code,
            province_ids,
            provinces_by_id,
        )
        for area_code, province_ids
        in AREA_CODE_DEFINITIONS.items()
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
    }


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------

def validate_output(output: dict) -> None:
    features = output["features"]

    if len(features) != 6:
        raise ValueError(
            f"Expected 6 area-code features but generated "
            f"{len(features)}."
        )

    expected_codes = set(AREA_CODE_DEFINITIONS)

    actual_codes = {
        feature["properties"]["area_code_id"]
        for feature in features
    }

    if actual_codes != expected_codes:
        raise ValueError(
            f"Area-code IDs do not match expected values. "
            f"Expected {sorted(expected_codes)}, "
            f"found {sorted(actual_codes)}."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Generating Ecuador area-code regions...\n")

    input_geojson = load_geojson(INPUT_PATH)

    provinces_by_id = validate_input_features(
        input_geojson["features"]
    )

    validate_area_code_definitions(provinces_by_id)

    output_geojson = generate_area_code_geojson(
        provinces_by_id
    )

    validate_output(output_geojson)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output_geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print("Generated area-code regions:")

    for feature in output_geojson["features"]:
        properties = feature["properties"]

        print(
            f"  {properties['area_code']}  "
            f"{', '.join(properties['provinces'])}"
        )

    size_bytes = OUTPUT_PATH.stat().st_size

    print("")
    print(f"Features: {len(output_geojson['features'])}")
    print(f"Size: {size_bytes:,} bytes")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()