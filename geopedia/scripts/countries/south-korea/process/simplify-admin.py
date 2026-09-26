"""
Cleans and simplifies South Korea's processed administrative GeoJSON for web
delivery.

The full-resolution GeoJSON produced by admin.py is retained in the gitignored
intermediate data directory. This script creates smaller topology-preserving
versions for GeoPedia's public data directory.

Mapshaper is used so shared administrative boundaries are cleaned and
simplified together rather than processing each feature independently. This
helps prevent visible gaps or mismatched borders between neighboring features.

The South Korea source contains thousands of extremely small sliver polygons.
Testing showed that cleaning these before simplification removes unnecessary
geometry and prevents the large number of unrepaired intersections produced
when the uncleaned source is simplified directly.

All three administrative levels use 10% simplification. Visual inspection found
no meaningful difference between 10% and higher retention levels at GeoPedia's
map scales, while 10% substantially reduces file size.

Inputs:
    data/intermediate/countries/south-korea/geojson/provinces.geojson
    data/intermediate/countries/south-korea/geojson/municipalities.geojson
    data/intermediate/countries/south-korea/geojson/submunicipalities.geojson

Outputs:
    public/data/countries/south-korea/geojson/provinces.geojson
    public/data/countries/south-korea/geojson/municipalities.geojson
    public/data/countries/south-korea/geojson/submunicipalities.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-korea/process/simplify-admin.py
"""

from pathlib import Path
import shutil
import subprocess


INPUT_DIR = Path(
    "data/intermediate/countries/south-korea/geojson"
)

OUTPUT_DIR = Path(
    "public/data/countries/south-korea/geojson"
)


# Percentage of removable vertices retained by Mapshaper.
#
# Testing at 10%, 20%, and 30% found no meaningful visual difference at
# GeoPedia's intended map scales. Ten percent therefore provides the best
# balance between map appearance and web-delivery size.
#
# Percentages remain defined separately so individual administrative levels
# can be tuned later if necessary.
SIMPLIFY_PERCENTAGES = {
    "provinces": 10,
    "municipalities": 10,
    "submunicipalities": 10,
}


def find_mapshaper() -> str:
    """
    Finds an available Mapshaper executable.

    Supports either a globally installed `mapshaper` command or the
    project-local executable installed through npm.
    """

    global_mapshaper = shutil.which("mapshaper")

    if global_mapshaper:
        return global_mapshaper

    local_candidates = [
        Path("node_modules/.bin/mapshaper.cmd"),
        Path("node_modules/.bin/mapshaper"),
    ]

    for candidate in local_candidates:
        if candidate.exists():
            return str(candidate)

    raise RuntimeError(
        "Mapshaper was not found. Install it with:\n"
        "  npm install --save-dev mapshaper"
    )


def simplify_geojson(
    mapshaper: str,
    name: str,
    percentage: int,
) -> None:
    """
    Cleans and simplifies one administrative GeoJSON dataset with Mapshaper.

    Cleaning occurs before simplification so tiny source slivers are removed
    before Mapshaper calculates the simplified topology.
    """

    input_path = INPUT_DIR / f"{name}.geojson"
    output_path = OUTPUT_DIR / f"{name}.geojson"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    print(
        f"Cleaning and simplifying {name} "
        f"({percentage}% retained)..."
    )

    command = [
        mapshaper,
        str(input_path),
        "-clean",
        "-simplify",
        "weighted",
        f"{percentage}%",
        "keep-shapes",
        "-o",
        str(output_path),
        "format=geojson",
        "precision=0.000001",
    ]

    subprocess.run(
        command,
        check=True,
    )


def get_size_mb(path: Path) -> float:
    """
    Returns a file's size in megabytes.
    """

    return path.stat().st_size / (1024 * 1024)


def main() -> None:
    """
    Cleans and simplifies all three South Korea administrative datasets.
    """

    mapshaper = find_mapshaper()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Cleaning and simplifying South Korea "
        "administrative GeoJSON..."
    )
    print()

    for name, percentage in SIMPLIFY_PERCENTAGES.items():
        simplify_geojson(
            mapshaper,
            name,
            percentage,
        )

    print()
    print("Simplification complete.")
    print()

    for name in SIMPLIFY_PERCENTAGES:
        input_path = INPUT_DIR / f"{name}.geojson"
        output_path = OUTPUT_DIR / f"{name}.geojson"

        input_size = get_size_mb(input_path)
        output_size = get_size_mb(output_path)

        reduction = (
            1 - output_size / input_size
        ) * 100

        print(
            f"{name}: "
            f"{input_size:.2f} MB -> "
            f"{output_size:.2f} MB "
            f"({reduction:.1f}% smaller)"
        )


if __name__ == "__main__":
    main()