from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[4]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "ecuador"
    / "ecu_adm_2024"
)


for level in range(5):
    path = DATA_DIR / f"ecu_adm_adm{level}_2024.shp"

    print()
    print(f"===== ADM{level} =====")
    print(f"File: {path.name}")

    data = gpd.read_file(path)

    print(f"Features: {len(data):,}")
    print(f"CRS: {data.crs}")
    print(
        "Geometry types:",
        data.geometry.geom_type.value_counts().to_dict(),
    )
    print("Columns:", list(data.columns))

    print()
    print("First 5 rows:")
    print(
        data.drop(columns=[data.geometry.name])
        .head()
        .to_string(index=False)
    )