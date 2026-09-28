from pathlib import Path

import geopandas as gpd
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[4]

DEPARTMENTS_SOURCE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "uruguay"
    / "uy.json"
)

MUNICIPALITIES_SOURCE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "uruguay"
    / "municipios_20250507"
    / "municipios_20250507.shp"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "uruguay"
    / "admin"
)

DEPARTMENTS_OUTPUT = OUTPUT_DIR / "departments.geojson"
MUNICIPALITIES_OUTPUT = OUTPUT_DIR / "municipalities.geojson"


EXPECTED_DEPARTMENT_COUNT = 19
EXPECTED_MUNICIPALITY_COUNT = 136


DEPARTMENT_BY_SOURCE_NAME = {
    "ARTIGAS": {
        "id": "UY01",
        "name": "Artigas",
    },
    "CANELONES": {
        "id": "UY02",
        "name": "Canelones",
    },
    "CERRO LARGO": {
        "id": "UY03",
        "name": "Cerro Largo",
    },
    "COLONIA": {
        "id": "UY04",
        "name": "Colonia",
    },
    "DURAZNO": {
        "id": "UY05",
        "name": "Durazno",
    },
    "FLORES": {
        "id": "UY06",
        "name": "Flores",
    },
    "FLORIDA": {
        "id": "UY07",
        "name": "Florida",
    },
    "LAVALLEJA": {
        "id": "UY08",
        "name": "Lavalleja",
    },
    "MALDONADO": {
        "id": "UY09",
        "name": "Maldonado",
    },
    "MONTEVIDEO": {
        "id": "UY10",
        "name": "Montevideo",
    },
    "PAYSANDU": {
        "id": "UY11",
        "name": "Paysandú",
    },
    "RIO NEGRO": {
        "id": "UY12",
        "name": "Río Negro",
    },
    "RIVERA": {
        "id": "UY13",
        "name": "Rivera",
    },
    "ROCHA": {
        "id": "UY14",
        "name": "Rocha",
    },
    "SALTO": {
        "id": "UY15",
        "name": "Salto",
    },
    "SAN JOSE": {
        "id": "UY16",
        "name": "San José",
    },
    "SORIANO": {
        "id": "UY17",
        "name": "Soriano",
    },
    "TACUAREMBO": {
        "id": "UY18",
        "name": "Tacuarembó",
    },
    "TREINTA Y TRES": {
        "id": "UY19",
        "name": "Treinta y Tres",
    },
}

def normalize_department_name(name: str) -> str:
    normalized = unicodedata.normalize("NFD", name)

    without_accents = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )

    return without_accents.upper()

def load_departments() -> gpd.GeoDataFrame:
    print("Loading departments...")

    departments = gpd.read_file(DEPARTMENTS_SOURCE)

    if len(departments) != EXPECTED_DEPARTMENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_DEPARTMENT_COUNT} departments, "
            f"found {len(departments)}."
        )

    if departments.crs is None:
        raise ValueError("Department source has no CRS.")

    departments = departments.to_crs("EPSG:4326")

    required_columns = {
        "id",
        "name",
        "geometry",
    }

    missing_columns = required_columns - set(departments.columns)

    if missing_columns:
        raise ValueError(
            "Department source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if departments["id"].isna().any():
        raise ValueError("Department source contains missing IDs.")

    if departments["id"].duplicated().any():
        duplicates = departments.loc[
            departments["id"].duplicated(keep=False),
            "id",
        ].tolist()

        raise ValueError(
            f"Duplicate department source IDs found: {duplicates}"
        )

    if departments["name"].isna().any():
        raise ValueError("Department source contains missing names.")

    source_names = {
        normalize_department_name(name)
        for name in departments["name"]
    }

    expected_names = set(DEPARTMENT_BY_SOURCE_NAME)

    if source_names != expected_names:
        missing = sorted(
            expected_names - source_names
        )
        unexpected = sorted(
            source_names - expected_names
        )

        raise ValueError(
            "Department names do not match expected Uruguay departments.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    departments = departments[
        [
            "name",
            "geometry",
        ]
    ].copy()

    departments["source_name"] = departments[
        "name"
    ].map(normalize_department_name)

    departments["department_id"] = departments[
        "source_name"
    ].map(
        lambda name: DEPARTMENT_BY_SOURCE_NAME[name]["id"]
    )

    departments["department"] = departments[
        "source_name"
    ].map(
        lambda name: DEPARTMENT_BY_SOURCE_NAME[name]["name"]
    )

    departments = departments[
        [
            "department_id",
            "department",
            "geometry",
        ]
    ]

    return departments

def load_municipalities() -> gpd.GeoDataFrame:
    print("Loading municipalities...")

    municipalities = gpd.read_file(MUNICIPALITIES_SOURCE)

    if len(municipalities) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(municipalities)}."
        )

    if municipalities.crs is None:
        raise ValueError("Municipality source has no CRS.")

    municipalities = municipalities.to_crs("EPSG:4326")

    required_columns = {
        "depto",
        "municipio",
        "cod_muni",
        "geometry",
    }

    missing_columns = required_columns - set(municipalities.columns)

    if missing_columns:
        raise ValueError(
            "Municipality source is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if municipalities["cod_muni"].isna().any():
        raise ValueError("Municipality source contains missing IDs.")

    if municipalities["cod_muni"].duplicated().any():
        duplicates = municipalities.loc[
            municipalities["cod_muni"].duplicated(keep=False),
            "cod_muni",
        ].tolist()

        raise ValueError(
            f"Duplicate municipality IDs found: {duplicates}"
        )

    if municipalities["municipio"].isna().any():
        raise ValueError(
            "Municipality source contains missing names."
        )

    unknown_departments = sorted(
        set(municipalities["depto"])
        - set(DEPARTMENT_BY_SOURCE_NAME)
    )

    if unknown_departments:
        raise ValueError(
            "Unknown municipality department names found: "
            f"{unknown_departments}"
        )

    municipalities = municipalities[
        [
            "cod_muni",
            "municipio",
            "depto",
            "geometry",
        ]
    ].copy()

    municipalities["department_id"] = municipalities[
        "depto"
    ].map(
        lambda name: DEPARTMENT_BY_SOURCE_NAME[name]["id"]
    )

    municipalities["department"] = municipalities[
        "depto"
    ].map(
        lambda name: DEPARTMENT_BY_SOURCE_NAME[name]["name"]
    )

    municipalities = municipalities.rename(
        columns={
            "cod_muni": "municipality_id",
            "municipio": "municipality",
        }
    )

    municipalities = municipalities[
        [
            "municipality_id",
            "municipality",
            "department_id",
            "department",
            "geometry",
        ]
    ]

    return municipalities


def validate_geometry(
    label: str,
    gdf: gpd.GeoDataFrame,
) -> None:
    invalid = int((~gdf.geometry.is_valid).sum())
    empty = int(gdf.geometry.is_empty.sum())
    missing = int(gdf.geometry.isna().sum())

    if invalid:
        raise ValueError(
            f"{label} contains {invalid} invalid geometries."
        )

    if empty:
        raise ValueError(
            f"{label} contains {empty} empty geometries."
        )

    if missing:
        raise ValueError(
            f"{label} contains {missing} missing geometries."
        )


def print_duplicate_municipality_names(
    municipalities: gpd.GeoDataFrame,
) -> None:
    duplicate_mask = municipalities[
        "municipality"
    ].duplicated(keep=False)

    duplicates = municipalities.loc[
        duplicate_mask,
        [
            "municipality_id",
            "municipality",
            "department",
        ],
    ].sort_values(
        [
            "municipality",
            "department",
        ]
    )

    print()
    print("Duplicate municipality names:")

    if duplicates.empty:
        print("  None")
        return

    for _, row in duplicates.iterrows():
        print(
            f"  {row['municipality']} "
            f"({row['department']}) "
            f"-> {row['municipality_id']}"
        )


def write_geojson(
    label: str,
    gdf: gpd.GeoDataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    gdf.to_file(
        path,
        driver="GeoJSON",
    )

    size_mb = path.stat().st_size / 1_000_000

    print(
        f"{label}: "
        f"{len(gdf)} features -> "
        f"{path}"
    )

    print(
        f"  Size: {size_mb:.3f} MB"
    )


def main() -> None:
    print(
        "Processing Uruguay administrative boundaries..."
    )
    print()

    departments = load_departments()
    municipalities = load_municipalities()

    validate_geometry(
        "Departments",
        departments,
    )

    validate_geometry(
        "Municipalities",
        municipalities,
    )

    print_duplicate_municipality_names(
        municipalities
    )

    print()
    print("Writing intermediate GeoJSON...")

    write_geojson(
        "Departments",
        departments,
        DEPARTMENTS_OUTPUT,
    )

    write_geojson(
        "Municipalities",
        municipalities,
        MUNICIPALITIES_OUTPUT,
    )

    print()
    print("Complete.")
    print(
        f"Departments: {len(departments)}"
    )
    print(
        f"Municipalities: {len(municipalities)}"
    )
    print("CRS: EPSG:4326")


if __name__ == "__main__":
    main()