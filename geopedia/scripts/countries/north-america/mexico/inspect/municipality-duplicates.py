"""
Inspect duplicate municipality names in INEGI's 2025 Mexico municipality layer.

Source
------
INEGI Marco Geoestadístico Integrado 2025:

    data/raw/countries/mexico/mg_2025_integrado/
        conjunto_de_datos/
            00mun.shp
            00mun.shx
            00mun.dbf
            00mun.prj
            00mun.cpg

Relevant fields:
    CVEGEO  -> globally unique five-digit municipality identifier
    CVE_ENT -> two-digit INEGI state/entity identifier
    CVE_MUN -> three-digit municipality code within the state
    NOMGEO  -> municipality name

Purpose
-------
Count municipality names that occur more than once across Mexico and show
which states/entities contain each duplicate.

This helps determine whether municipality quiz display names need
disambiguation. If duplicate names are uncommon, GeoPedia can keep ordinary
municipality labels short and only append a state abbreviation when a
municipality name is duplicated.

The source `.cpg` declares the encoding as `88591`, which represents
ISO-8859-1 but is not recognized directly by PyShp, so the DBF is opened
explicitly with `latin1`.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import shapefile


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_SHP = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "mexico"
    / "mg_2025_integrado"
    / "conjunto_de_datos"
    / "00mun.shp"
)


# ---------------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 2478


# ---------------------------------------------------------------------------
# State names
# ---------------------------------------------------------------------------

MEXICO_STATE_NAMES_BY_ID = {
    "01": "Aguascalientes",
    "02": "Baja California",
    "03": "Baja California Sur",
    "04": "Campeche",
    "05": "Coahuila de Zaragoza",
    "06": "Colima",
    "07": "Chiapas",
    "08": "Chihuahua",
    "09": "Ciudad de México",
    "10": "Durango",
    "11": "Guanajuato",
    "12": "Guerrero",
    "13": "Hidalgo",
    "14": "Jalisco",
    "15": "México",
    "16": "Michoacán de Ocampo",
    "17": "Morelos",
    "18": "Nayarit",
    "19": "Nuevo León",
    "20": "Oaxaca",
    "21": "Puebla",
    "22": "Querétaro",
    "23": "Quintana Roo",
    "24": "San Luis Potosí",
    "25": "Sinaloa",
    "26": "Sonora",
    "27": "Tabasco",
    "28": "Tamaulipas",
    "29": "Tlaxcala",
    "30": "Veracruz de Ignacio de la Llave",
    "31": "Yucatán",
    "32": "Zacatecas",
}


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def main() -> None:
    """Find and print duplicate municipality names."""

    if not SOURCE_SHP.exists():
        raise FileNotFoundError(
            f"Missing INEGI municipality shapefile:\n  {SOURCE_SHP}"
        )

    reader = shapefile.Reader(
        str(SOURCE_SHP),
        encoding="latin1",
    )

    try:
        records = list(reader.iterRecords())
    finally:
        reader.close()

    if len(records) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected municipality count: "
            f"expected {EXPECTED_FEATURE_COUNT}, found {len(records)}."
        )

    municipalities_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)

    for record in records:
        municipality_id = str(record["CVEGEO"]).strip()
        state_id = str(record["CVE_ENT"]).strip()
        municipality_code = str(record["CVE_MUN"]).strip()
        name = str(record["NOMGEO"]).strip()

        if not municipality_id:
            raise ValueError("Found municipality with empty CVEGEO.")

        if not state_id:
            raise ValueError(
                f"Municipality {municipality_id} has empty CVE_ENT."
            )

        if not name:
            raise ValueError(
                f"Municipality {municipality_id} has empty NOMGEO."
            )

        state_name = MEXICO_STATE_NAMES_BY_ID.get(state_id)

        if state_name is None:
            raise ValueError(
                f"Unknown state ID {state_id!r} for municipality "
                f"{municipality_id} ({name})."
            )

        municipalities_by_name[name].append(
            {
                "municipality_id": municipality_id,
                "municipality_code": municipality_code,
                "state_id": state_id,
                "state_name": state_name,
            }
        )

    duplicates = {
        name: municipalities
        for name, municipalities in municipalities_by_name.items()
        if len(municipalities) > 1
    }

    duplicate_municipality_count = sum(
        len(municipalities)
        for municipalities in duplicates.values()
    )

    unique_name_count = len(municipalities_by_name)

    print("Mexico municipality duplicate-name inspection")
    print("----------------------------------------------")
    print(f"Total municipalities: {len(records):,}")
    print(f"Unique municipality names: {unique_name_count:,}")
    print(f"Duplicated names: {len(duplicates):,}")
    print(
        "Municipalities involved in duplicates: "
        f"{duplicate_municipality_count:,}"
    )
    print(
        "Share of municipalities needing disambiguation: "
        f"{duplicate_municipality_count / len(records) * 100:.2f}%"
    )

    if not duplicates:
        print()
        print("✓ No duplicate municipality names found.")
        return

    print()
    print("Duplicate names")
    print("---------------")

    for name in sorted(
        duplicates,
        key=lambda duplicate_name: (
            -len(duplicates[duplicate_name]),
            duplicate_name,
        ),
    ):
        municipalities = duplicates[name]

        print()
        print(f"{name} ({len(municipalities)})")

        for municipality in sorted(
            municipalities,
            key=lambda item: item["municipality_id"],
        ):
            print(
                f"  {municipality['municipality_id']}  "
                f"{municipality['state_name']}"
            )


if __name__ == "__main__":
    main()