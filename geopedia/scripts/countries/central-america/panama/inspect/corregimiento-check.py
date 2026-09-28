"""Compare the 2022 and 2024 Santa Fe corregimiento geometries in Darién."""

from pathlib import Path

import geopandas as gpd


SOURCE_DIRECTORY = Path("data/raw/countries/panama")

OLD_ADM3_PATH = (
    SOURCE_DIRECTORY
    / "Panama_Corregimientos_Boundaries_2022_-3844174869162940437.geojson"
)

NEW_ADM3_PATH = (
    SOURCE_DIRECTORY
    / "Panama_Corregimientos_Boundaries_2024_-2164041707231143700.geojson"
)


def main() -> None:
    """Compare the old Santa Fe geometry with the two 2024 Santa Fe pieces."""

    print("Loading 2022 corregimientos...")
    old_adm3 = gpd.read_file(OLD_ADM3_PATH)

    print("Loading 2024 corregimientos...")
    new_adm3 = gpd.read_file(NEW_ADM3_PATH)

    old_ids = old_adm3["ID_CORR"].astype(str).str.strip()
    new_ids = new_adm3["ID_CORR"].astype(str).str.strip()

    old_santa_fe = old_adm3[
        old_ids == "050316"
    ]

    new_santa_fe = new_adm3[
        new_ids.isin({"050316", "050300"})
    ]

    print()
    print("2022 vs 2024 Santa Fe comparison:")
    print(f"2022 matching features: {len(old_santa_fe)}")
    print(f"2024 matching features: {len(new_santa_fe)}")

    if len(old_santa_fe) != 1:
        print()
        print(
            "Expected exactly one 2022 feature with "
            "ID_CORR 050316."
        )
        return

    new_050316 = new_santa_fe[
        new_santa_fe["ID_CORR"].astype(str).str.strip()
        == "050316"
    ]

    new_050300 = new_santa_fe[
        new_santa_fe["ID_CORR"].astype(str).str.strip()
        == "050300"
    ]

    if len(new_050316) != 1 or len(new_050300) != 1:
        print()
        print(
            "Expected exactly one 2024 feature for both "
            "050316 and 050300."
        )
        return

    old_geometry = old_santa_fe.iloc[0].geometry
    geometry_050316 = new_050316.iloc[0].geometry
    geometry_050300 = new_050300.iloc[0].geometry

    new_union = geometry_050316.union(geometry_050300)

    print()
    print(f"2022 050316 bounds: {old_geometry.bounds}")
    print(f"2024 050316 bounds: {geometry_050316.bounds}")
    print(f"2024 050300 bounds: {geometry_050300.bounds}")
    print(f"2024 union bounds: {new_union.bounds}")

    print()
    print(
        "2022 exactly equals 2024 union: "
        f"{old_geometry.equals(new_union)}"
    )
    print(
        "2022 intersects 2024 050316: "
        f"{old_geometry.intersects(geometry_050316)}"
    )
    print(
        "2022 intersects 2024 050300: "
        f"{old_geometry.intersects(geometry_050300)}"
    )

    print()
    print(
        "2022 area in source CRS: "
        f"{old_geometry.area}"
    )
    print(
        "2024 050316 area in source CRS: "
        f"{geometry_050316.area}"
    )
    print(
        "2024 050300 area in source CRS: "
        f"{geometry_050300.area}"
    )
    print(
        "2024 union area in source CRS: "
        f"{new_union.area}"
    )
    print(
        "2022 / 2024-union symmetric difference area: "
        f"{old_geometry.symmetric_difference(new_union).area}"
    )
    
        # Find which 2022 corregimientos occupied the area represented by
    # the new 2024 050300 Santa Fe feature.
    print()
    print("2022 features intersecting 2024 ID_CORR 050300:")

    geometry_050300 = new_050300.iloc[0].geometry

    intersecting_old = old_adm3[
        old_adm3.geometry.intersects(geometry_050300)
    ].copy()

    if intersecting_old.empty:
        print("  None")
    else:
        for _, row in intersecting_old.iterrows():
            old_geometry = row.geometry
            intersection = old_geometry.intersection(geometry_050300)

            intersection_area = intersection.area
            new_area = geometry_050300.area
            old_area = old_geometry.area

            new_coverage = (
                intersection_area / new_area * 100
                if new_area > 0
                else 0
            )

            old_coverage = (
                intersection_area / old_area * 100
                if old_area > 0
                else 0
            )

            print()
            print(f"  ID_CORR: {row['ID_CORR']!r}")
            print(f"  Provincia: {row['Provincia']!r}")
            print(f"  Distrito: {row['Distrito']!r}")
            print(
                f"  Corregimiento: "
                f"{row['Corregimiento']!r}"
            )
            print(
                f"  Intersection area: "
                f"{intersection_area}"
            )
            print(
                "  Percent of 050300 covered by this "
                f"2022 feature: {new_coverage:.2f}%"
            )
            print(
                "  Percent of old feature represented "
                f"by intersection: {old_coverage:.2f}%"
            )


if __name__ == "__main__":
    main()