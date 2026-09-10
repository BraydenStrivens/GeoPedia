"""
Process Colombia ADM1 and ADM2 GeoJSON data for GeoPedia.

Outputs:
- Colombia's 33 first-order administrative divisions
  (32 departments plus Bogotá D.C.).
- Colombia's 1,122 second-order administrative divisions.

The postal dataset is used to provide stable 2-digit department IDs and
5-digit municipality IDs. Because the geoBoundaries ADM2 source does not
contain parent-department information, municipalities are assigned to their
parent ADM1 feature spatially before being matched to postal records.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from difflib import SequenceMatcher

import geopandas as gpd
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    mapping,
)
from shapely.geometry.base import BaseGeometry

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "countries" / "colombia"
OUTPUT_DIR = (
    PROJECT_ROOT / "public" / "data" / "countries" / "colombia" / "geojson"
)

ADM1_PATH = RAW_DIR / "geoBoundaries-COL-ADM1.geojson"
ADM2_PATH = RAW_DIR / "geoBoundaries-COL-ADM2.geojson"
POSTAL_PATH = RAW_DIR / "postal" / "zipcodes.co.json"

DEPARTMENTS_OUTPUT_PATH = OUTPUT_DIR / "departments.geojson"
MUNICIPALITIES_OUTPUT_PATH = OUTPUT_DIR / "municipalities.geojson"

# Roughly 110 meters at Colombia's latitude.
DEPARTMENT_SIMPLIFY_TOLERANCE = 0.001

# Roughly 28 meters at Colombia's latitude.
#
# Municipalities are much smaller than departments, so a more conservative
# tolerance retains useful local boundary detail.
MUNICIPALITY_SIMPLIFY_TOLERANCE = 0.0005

PHONE_CODE_BY_DEPARTMENT_NAME = {
    "Bogotá D.C.": "601",
    "Cundinamarca": "601",
    "Cauca": "602",
    "Nariño": "602",
    "Valle del Cauca": "602",
    "Antioquia": "604",
    "Chocó": "604",
    "Córdoba": "604",
    "Atlántico": "605",
    "Bolívar": "605",
    "Cesar": "605",
    "La Guajira": "605",
    "Magdalena": "605",
    "Sucre": "605",
    "Caldas": "606",
    "Quindío": "606",
    "Risaralda": "606",
    "Arauca": "607",
    "Norte de Santander": "607",
    "Santander": "607",
    "Amazonas": "608",
    "Boyacá": "608",
    "Caquetá": "608",
    "Casanare": "608",
    "Guainía": "608",
    "Guaviare": "608",
    "Huila": "608",
    "Meta": "608",
    "Putumayo": "608",
    "San Andrés y Providencia": "608",
    "Tolima": "608",
    "Vaupés": "608",
    "Vichada": "608",
}


DEPARTMENT_NAME_OVERRIDES = {
    "Bogota Capital District": "Bogotá D.C.",
    "Archipiélago de San Andrés, Providencia y Santa Catalina":
        "San Andrés y Providencia",
}

MUNICIPALITY_NAME_OVERRIDES = {
    ("Antioquia", "Santuario"): "El Santuario",
    (
        "Atlántico",
        "Distrito Especial, Industrial Y Portuario De Barr*",
    ): "Barranquilla",
    ("Boyacá", "Labranza Grande"): "Labranzagrande",

    ("Bolívar", "Tiquiso"): "Tiquisio",
    ("Antioquia", "San Andrès"): "San Andrés de Cuerquía",
    ("Cundinamarca", "Ubate"): "Villa de San Diego de Ubate",
    ("Córdoba", "San Andres De Sotavento"): "San Andrés Sotavento",
    ("Santander", "Jordán Sube"): "Jordán",
    ("Magdalena", "Cerro De San Antonio"): "Cerro San Antonio",
    ("Magdalena", "Chivolo"): "Chibolo",
    ("Valle del Cauca", "Buga"): "Guadalajara de Buga",
    ("Sucre", "Ricaurte (Coloso)"): "Coloso",
    ("Tolima", "San Sebastián De Mariquita"): "Mariquita",
    ("Chocó", "El Carmen"): "El Carmen de Atrato",
    ("Bolívar", "Cartagena De Indias"): "Cartagena",
    ("Amazonas", "Santander (Araracuara)"): "Puerto Santander",
    ("Putumayo", "Puerto Leguízamo"): "Leguízamo",
    ("Nariño", "Tumaco"): "San Andres de Tumaco",
    ("Cesar", "Manaure Balcón Del Cesar"): "Manaure",
    ("Guainía", "Barranco Mina"): "Barranco Minas",
    ("Cesar", "Becerrill"): "Becerril",
}

POSTAL_DEPARTMENT_NAME_OVERRIDES = {
    "Bogota, D.C.": "Bogotá D.C.",
    "Archipielago De San Andres": "San Andrés y Providencia",
}

def count_coordinates(geometry: BaseGeometry) -> int:
    """Count coordinate pairs contained in a polygonal geometry."""
    if geometry is None or geometry.is_empty:
        return 0

    if isinstance(geometry, Polygon):
        count = len(geometry.exterior.coords)

        for interior in geometry.interiors:
            count += len(interior.coords)

        return count

    if isinstance(geometry, MultiPolygon):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    if isinstance(geometry, GeometryCollection):
        return sum(
            count_coordinates(part)
            for part in geometry.geoms
        )

    return 0
  
def simplify_geometries(
    gdf: gpd.GeoDataFrame,
    tolerance: float,
    label: str,
) -> gpd.GeoDataFrame:
    """
    Simplify administrative boundaries while preserving polygon topology.

    Coordinate counts are reported so the effect of each tolerance can be
    evaluated before the resulting GeoJSON is used at runtime.
    """
    result = gdf.copy()

    coordinates_before = sum(
        count_coordinates(geometry)
        for geometry in result.geometry
    )

    result.geometry = result.geometry.simplify(
        tolerance,
        preserve_topology=True,
    )

    coordinates_after = sum(
        count_coordinates(geometry)
        for geometry in result.geometry
    )

    print(
        f"{label} coordinates before simplification: "
        f"{coordinates_before:,}"
    )
    print(
        f"{label} coordinates after simplification:  "
        f"{coordinates_after:,}"
    )

    if coordinates_before:
        reduction = (
            1 - coordinates_after / coordinates_before
        ) * 100

        print(f"{label} coordinate reduction: {reduction:.1f}%")

    if result.geometry.isna().any():
        raise ValueError(
            f"{label} simplification produced null geometries."
        )

    if result.geometry.is_empty.any():
        raise ValueError(
            f"{label} simplification produced empty geometries."
        )

    if (~result.geometry.is_valid).any():
        raise ValueError(
            f"{label} simplification produced invalid geometries."
        )

    return result

def clean_display_name(value: str) -> str:
    """
    Clean source-provided geographic names for display.

    Repeated whitespace is collapsed while preserving capitalization,
    accents, punctuation, and otherwise meaningful source spelling.
    """
    return " ".join(value.split())

def normalize_name(value: str) -> str:
    """
    Normalize a geographic name for comparison.

    Accents, punctuation, repeated whitespace, and capitalization are ignored.
    The original source spelling is preserved separately for display.
    """
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def normalize_department_name(value: str) -> str:
    """Convert known department-name variants to GeoPedia display names."""
    return DEPARTMENT_NAME_OVERRIDES.get(value, value)


def normalize_postal_department_name(value: str) -> str:
    """Convert postal-source department names to GeoPedia display names."""
    return POSTAL_DEPARTMENT_NAME_OVERRIDES.get(value, value)


def load_postal_records() -> list[dict]:
    """Load Colombia postal-code records."""
    with POSTAL_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_postal_department_data(
    postal_records: list[dict],
) -> dict[str, dict]:
    """
    Build department metadata from the postal source.

    Each department must resolve to exactly one 2-digit department/postal code.
    """
    values_by_department: dict[str, set[str]] = defaultdict(set)

    for record in postal_records:
        department_name = clean_display_name(
            normalize_postal_department_name(record["state"])
        )
        department_code = record["zipcode"][:2]
        values_by_department[department_name].add(department_code)

    result = {}

    for department_name, codes in values_by_department.items():
        if len(codes) != 1:
            raise ValueError(
                f"{department_name!r} maps to multiple department codes: "
                f"{sorted(codes)}"
            )

        result[normalize_name(department_name)] = {
            "id": next(iter(codes)),
            "name": department_name,
        }

    if len(result) != 33:
        raise ValueError(
            f"Expected 33 postal departments, found {len(result)}."
        )

    return result


def build_postal_municipality_data(
    postal_records: list[dict],
) -> dict[tuple[str, str], dict]:
    """
    Build municipality metadata keyed by normalized department and municipality.

    The five-digit `province_code` is retained as the municipality ID.
    All unique four-digit postal prefixes for each municipality are collected
    for use by the later postal-code quiz.
    """
    municipality_data: dict[tuple[str, str], dict] = {}

    grouped: dict[tuple[str, str, str], set[str]] = defaultdict(set)

    for record in postal_records:
        department_name = normalize_postal_department_name(record["state"])
        municipality_name = clean_display_name(record["province"])
        municipality_id = record["province_code"]

        grouped[
            (
                department_name,
                municipality_name,
                municipality_id,
            )
        ].add(record["zipcode"][:4])

    for (
        department_name,
        municipality_name,
        municipality_id,
    ), postal_prefixes in grouped.items():
        key = (
            normalize_name(department_name),
            normalize_name(municipality_name),
        )

        if key in municipality_data:
            previous = municipality_data[key]

            raise ValueError(
                "Duplicate normalized municipality key: "
                f"{department_name} / {municipality_name} "
                f"({municipality_id}) conflicts with "
                f"{previous['name']} ({previous['id']})."
            )

        municipality_data[key] = {
            "id": municipality_id,
            "name": municipality_name,
            "postal_code_4_digit": sorted(postal_prefixes),
        }

    if len(municipality_data) != 1122:
        raise ValueError(
            "Expected 1,122 postal municipalities, found "
            f"{len(municipality_data)}."
        )

    return municipality_data


def build_department_features(
    adm1: gpd.GeoDataFrame,
    postal_departments: dict[str, dict],
) -> list[dict]:
    """Create cleaned Colombia department GeoJSON features."""
    features = []

    for _, row in adm1.iterrows():
        source_name = row["shapeName"]
        name = normalize_department_name(source_name)
        key = normalize_name(name)

        postal_data = postal_departments.get(key)

        if postal_data is None:
            raise ValueError(
                f"Could not find postal department data for {source_name!r}."
            )

        phone_code = PHONE_CODE_BY_DEPARTMENT_NAME.get(name)

        if phone_code is None:
            raise ValueError(
                f"No phone code configured for department {name!r}."
            )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": postal_data["id"],
                    "name": name,
                    "iso": row["shapeISO"],
                    "postal_code_2_digit": postal_data["id"],
                    "phone_code": phone_code,
                },
                "geometry": mapping(row.geometry),
            }
        )

    features.sort(key=lambda feature: feature["properties"]["id"])

    if len(features) != 33:
        raise ValueError(
            f"Expected 33 department features, found {len(features)}."
        )

    return features


def assign_parent_departments(
    adm1: gpd.GeoDataFrame,
    adm2: gpd.GeoDataFrame,
) -> list[str]:
    """
    Determine each ADM2 feature's parent ADM1 division spatially.

    A representative point is used because it is guaranteed to lie within the
    municipality geometry and avoids centroid problems with irregular polygons.
    """
    parent_lookup = adm1[["shapeName", "geometry"]].copy()

    representative_points = adm2[["geometry"]].copy()
    representative_points["geometry"] = adm2.geometry.representative_point()

    joined = gpd.sjoin(
        representative_points,
        parent_lookup,
        how="left",
        predicate="within",
    )

    if joined["shapeName"].isna().any():
        missing = joined[joined["shapeName"].isna()]

        raise ValueError(
            f"{len(missing)} ADM2 features could not be assigned to an ADM1 "
            "department."
        )

    if joined.index.duplicated().any():
        duplicated = joined[joined.index.duplicated(keep=False)]

        raise ValueError(
            f"{len(duplicated)} spatial-join rows are ambiguous across ADM1 "
            "boundaries."
        )

    return joined["shapeName"].tolist()

def normalize_municipality_name(
    department_name: str,
    municipality_name: str,
) -> str:
    """
    Convert known municipality-name variants to the postal source's naming.

    Overrides are scoped by department because municipality names are not
    globally unique in Colombia.
    """
    return MUNICIPALITY_NAME_OVERRIDES.get(
        (department_name, municipality_name),
        municipality_name,
    )
    
def normalize_municipality_match_name(value: str) -> str:
    """
    Normalize a municipality name for secondary source matching.

    Parenthetical locality or administrative-seat descriptions are removed,
    then the standard name normalization is applied. Spaces are removed to
    tolerate differences such as "Rioviejo" versus "Rio Viejo".

    This normalization is only used as a fallback after the normal exact
    normalized-name match fails.
    """
    value = re.sub(r"\([^)]*\)", "", value)
    value = normalize_name(value)
    return value.replace(" ", "")

def find_closest_postal_municipalities(
    department_name: str,
    municipality_name: str,
    postal_municipalities: dict[tuple[str, str], dict],
    limit: int = 5,
) -> list[tuple[float, str, str]]:
    """
    Find the closest postal-source municipality names within a department.

    This is diagnostic only. Similarity scores are never used to
    automatically match administrative features.
    """
    department_key = normalize_name(department_name)
    source_name = normalize_municipality_match_name(municipality_name)

    candidates: list[tuple[float, str, str]] = []

    for (postal_department_key, _), postal_data in postal_municipalities.items():
        if postal_department_key != department_key:
            continue

        postal_name = postal_data["name"]
        normalized_postal_name = normalize_municipality_match_name(postal_name)

        score = SequenceMatcher(
            None,
            source_name,
            normalized_postal_name,
        ).ratio()

        candidates.append(
            (
                score,
                postal_name,
                postal_data["id"],
            )
        )

    candidates.sort(reverse=True)

    return candidates[:limit]

def build_municipality_features(
    adm2: gpd.GeoDataFrame,
    parent_department_names: list[str],
    postal_departments: dict[str, dict],
    postal_municipalities: dict[tuple[str, str], dict],
) -> list[dict]:
    """Create cleaned Colombia municipality GeoJSON features."""
    features = []
    matched_postal_keys: set[tuple[str, str]] = set()
    
    unmatched_adm2: list[tuple[str, str]] = []
    
    loose_postal_lookup: dict[
        tuple[str, str],
        list[tuple[tuple[str, str], dict]],
    ] = defaultdict(list)

    for postal_key, postal_data in postal_municipalities.items():
        department_key, municipality_key = postal_key

        loose_key = (
            department_key,
            normalize_municipality_match_name(postal_data["name"]),
        )

        loose_postal_lookup[loose_key].append(
            (
                postal_key,
                postal_data,
            )
        )

    for (_, row), source_parent_name in zip(
        adm2.iterrows(),
        parent_department_names,
        strict=True,
    ):
        department_name = normalize_department_name(source_parent_name)
        municipality_name = normalize_municipality_name(
            department_name,
            row["shapeName"],
        )

        department_key = normalize_name(department_name)
        municipality_key = normalize_name(municipality_name)

        postal_department = postal_departments.get(department_key)

        if postal_department is None:
            raise ValueError(
                f"No postal department record for {department_name!r}."
            )

        key = (department_key, municipality_key)
        postal_municipality = postal_municipalities.get(key)

        if postal_municipality is None:
            loose_key = (
                department_key,
                normalize_municipality_match_name(municipality_name),
            )
            loose_matches = loose_postal_lookup.get(loose_key, [])

            if len(loose_matches) == 1:
                key, postal_municipality = loose_matches[0]
            elif len(loose_matches) > 1:
                raise ValueError(
                    "Ambiguous loose municipality match: "
                    f"{department_name} / {municipality_name} -> "
                    f"{[match[1]['name'] for match in loose_matches]}"
                )
            else:
                unmatched_adm2.append(
                    (
                        department_name,
                        municipality_name,
                    )
                )
                continue

        if key in matched_postal_keys:
            raise ValueError(
                "Postal municipality matched more than once: "
                f"{department_name} / {municipality_name}"
            )

        matched_postal_keys.add(key)

        postal_codes = postal_municipality["postal_code_4_digit"]

        # Bogotá's twenty contiguous 4-digit prefixes are intentionally
        # represented as one logical GeoPedia range question.
        if postal_municipality["id"] == "11001":
            expected_bogota_codes = [
                f"{value:04d}"
                for value in range(1101, 1121)
            ]

            if postal_codes != expected_bogota_codes:
                raise ValueError(
                    "Bogotá postal prefixes no longer match the expected "
                    "continuous 1101-1120 range."
                )

            postal_code_answer: str | list[str] = "bogota-1101-1120"
        elif len(postal_codes) == 1:
            postal_code_answer = postal_codes[0]
        else:
            postal_code_answer = postal_codes

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": postal_municipality["id"],
                    "department_id": postal_department["id"],
                    "name": postal_municipality["name"],
                    "postal_code_4_digit": postal_code_answer,
                },
                "geometry": mapping(row.geometry),
            }
        )
        
    if unmatched_adm2:
        print()
        print(
            f"Unmatched ADM2 municipalities: {len(unmatched_adm2)}"
        )

        for department_name, municipality_name in unmatched_adm2:
            print()
            print(f"  {department_name} / {municipality_name}")

            candidates = find_closest_postal_municipalities(
                department_name,
                municipality_name,
                postal_municipalities,
            )

            for score, postal_name, municipality_id in candidates:
                print(
                    f"    {score:.3f}  {municipality_id}  {postal_name}"
                )

        raise ValueError(
            f"{len(unmatched_adm2)} ADM2 municipalities could not be matched "
            "to postal data."
        )

    unmatched_postal_keys = set(postal_municipalities) - matched_postal_keys

    if unmatched_postal_keys:
        preview = sorted(unmatched_postal_keys)[:20]

        raise ValueError(
            f"{len(unmatched_postal_keys)} postal municipalities were not "
            f"matched to ADM2 geometry. First matches: {preview}"
        )

    features.sort(key=lambda feature: feature["properties"]["id"])

    if len(features) != 1122:
        raise ValueError(
            f"Expected 1,122 municipality features, found {len(features)}."
        )

    return features


def write_feature_collection(path: Path, features: list[dict]) -> None:
    """Write a compact UTF-8 GeoJSON FeatureCollection."""
    path.parent.mkdir(parents=True, exist_ok=True)

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            feature_collection,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    """Process and validate Colombia's administrative boundary datasets."""
    print("Loading raw datasets...")

    adm1 = gpd.read_file(ADM1_PATH)
    adm2 = gpd.read_file(ADM2_PATH)
    postal_records = load_postal_records()

    if len(adm1) != 33:
        raise ValueError(f"Expected 33 ADM1 features, found {len(adm1)}.")

    if len(adm2) != 1122:
        raise ValueError(f"Expected 1,122 ADM2 features, found {len(adm2)}.")

    if adm1.crs != adm2.crs:
        print(f"Reprojecting ADM2 from {adm2.crs} to {adm1.crs}...")
        adm2 = adm2.to_crs(adm1.crs)

    print("Building postal lookup data...")

    postal_departments = build_postal_department_data(postal_records)
    postal_municipalities = build_postal_municipality_data(postal_records)

    print("Assigning municipalities to departments...")

    parent_department_names = assign_parent_departments(adm1, adm2)

    print()

    print("Simplifying department geometries...")

    adm1 = simplify_geometries(
        adm1,
        DEPARTMENT_SIMPLIFY_TOLERANCE,
        "Department",
    )

    print()

    print("Simplifying municipality geometries...")

    adm2 = simplify_geometries(
        adm2,
        MUNICIPALITY_SIMPLIFY_TOLERANCE,
        "Municipality",
    )

    print()

    print("Processing departments...")

    department_features = build_department_features(
        adm1,
        postal_departments,
    )

    print("Matching municipalities to postal records...")

    municipality_features = build_municipality_features(
        adm2,
        parent_department_names,
        postal_departments,
        postal_municipalities,
    )

    print("Writing GeoJSON...")

    write_feature_collection(
        DEPARTMENTS_OUTPUT_PATH,
        department_features,
    )
    write_feature_collection(
        MUNICIPALITIES_OUTPUT_PATH,
        municipality_features,
    )

    print()
    print("Colombia administrative processing complete.")
    print(f"Departments:    {len(department_features)}")
    print(f"Municipalities: {len(municipality_features)}")
    print(f"Departments output:    {DEPARTMENTS_OUTPUT_PATH}")
    print(f"Municipalities output: {MUNICIPALITIES_OUTPUT_PATH}")


if __name__ == "__main__":
    main()