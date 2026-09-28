from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

LOCALITIES_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "argentina"
    / "c1fc1f5b-dfe3-5231-9f3b-f7c703b906c7.json"
)


# Broad inspection box around Buenos Aires / Greater Buenos Aires.
#
# This is intentionally wider than the final code-11 region.
# We want to see nearby competing localities too.
MIN_LON = -59.30
MAX_LON = -57.35
MIN_LAT = -35.35
MAX_LAT = -33.20


TYPE_PRIORITY = {
    "LOCALIDAD": 3,
    "ENTIDAD": 2,
    "SITIO EDIFICADO": 1,
}


def read_localities(
) -> list[dict[str, Any]]:
    data = json.loads(
        LOCALITIES_PATH.read_text(
            encoding="utf-8",
        )
    )

    fields = [
        field["id"]
        for field in data["fields"]
    ]

    rows: list[
        dict[str, Any]
    ] = []

    for record in data["records"]:
        raw = dict(
            zip(
                fields,
                record,
            )
        )

        geometry_text = raw.get(
            "geojson"
        )

        if not geometry_text:
            continue

        geometry = json.loads(
            str(geometry_text)
        )

        if (
            geometry.get("type")
            != "Point"
        ):
            continue

        coordinates = geometry.get(
            "coordinates"
        )

        if (
            not coordinates
            or len(coordinates) < 2
        ):
            continue

        lon = float(
            coordinates[0]
        )

        lat = float(
            coordinates[1]
        )

        if not (
            MIN_LON <= lon <= MAX_LON
            and MIN_LAT <= lat <= MAX_LAT
        ):
            continue

        province = str(
            raw.get("nom_prov")
            or ""
        ).strip()

        if province not in {
            "BUENOS AIRES",
            "CIUDAD DE BUENOS AIRES",
        }:
            continue

        rows.append(
            {
                "id":
                    raw.get("_id"),

                "province":
                    province,

                "department":
                    str(
                        raw.get("nom_depto")
                        or ""
                    ).strip(),

                "locality":
                    str(
                        raw.get("nombre")
                        or ""
                    ).strip(),

                "type":
                    str(
                        raw.get("tipo")
                        or ""
                    ).strip(),

                "source":
                    str(
                        raw.get("fuente")
                        or ""
                    ).strip(),

                "lon":
                    lon,

                "lat":
                    lat,
            }
        )

    return rows


def main() -> None:
    rows = read_localities()

    print()
    print(
        "=" * 90
    )

    print(
        "ARGENTINA AMBA LOCALITY INSPECTION"
    )

    print(
        "=" * 90
    )

    print(
        f"Bounding box: "
        f"{MIN_LON}, {MIN_LAT} "
        f"to "
        f"{MAX_LON}, {MAX_LAT}"
    )

    print(
        f"Official points in box: "
        f"{len(rows):,}"
    )

    type_counts = Counter(
        row["type"]
        for row in rows
    )

    print()
    print(
        "Types:"
    )

    for (
        locality_type,
        count,
    ) in type_counts.most_common():
        print(
            f"  {locality_type}: "
            f"{count:,}"
        )

    province_counts = Counter(
        row["province"]
        for row in rows
    )

    print()
    print(
        "Provinces:"
    )

    for (
        province,
        count,
    ) in province_counts.items():
        print(
            f"  {province}: "
            f"{count:,}"
        )

    by_department: dict[
        tuple[str, str],
        list[dict[str, Any]],
    ] = defaultdict(list)

    for row in rows:
        by_department[
            (
                row["province"],
                row["department"],
            )
        ].append(
            row
        )

    print()
    print(
        "=" * 90
    )

    print(
        "LOCALIDAD + ENTIDAD POINTS BY DEPARTMENT"
    )

    print(
        "=" * 90
    )

    for (
        province,
        department,
    ) in sorted(
        by_department
    ):
        department_rows = [
            row
            for row in by_department[
                (
                    province,
                    department,
                )
            ]
            if row["type"] in {
                "LOCALIDAD",
                "ENTIDAD",
            }
        ]

        if not department_rows:
            continue

        department_rows.sort(
            key=lambda row: (
                -TYPE_PRIORITY.get(
                    row["type"],
                    0,
                ),
                row["locality"],
            )
        )

        print()
        print(
            f"{province} | "
            f"{department}"
        )

        print(
            "-" * 90
        )

        for row in department_rows:
            print(
                f"  id={row['id']} | "
                f"{row['type']} | "
                f"{row['locality']} | "
                f"{row['lat']:.5f}, "
                f"{row['lon']:.5f}"
            )


if __name__ == "__main__":
    main()