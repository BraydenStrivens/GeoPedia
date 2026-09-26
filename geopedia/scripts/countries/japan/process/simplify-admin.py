"""
Simplifies Japan's processed administrative GeoJSON for web delivery.

The full-resolution GeoJSON produced by admin.py is retained in the
gitignored intermediate data directory. This script creates smaller
topology-preserving versions for GeoPedia's public data directory.

Mapshaper is used so shared administrative boundaries are simplified
together rather than simplifying each feature independently. This helps
prevent visible gaps or mismatched borders between neighboring features.

Inputs:
    data/intermediate/countries/japan/geojson/regions.geojson
    data/intermediate/countries/japan/geojson/prefectures.geojson
    data/intermediate/countries/japan/geojson/municipalities.geojson

Outputs:
    public/data/countries/japan/geojson/regions.geojson
    public/data/countries/japan/geojson/prefectures.geojson
    public/data/countries/japan/geojson/municipalities.geojson

Run from the GeoPedia project root:

    python scripts/countries/japan/process/simplify-admin.py
"""

from pathlib import Path
import shutil
import subprocess


INPUT_DIR = Path(
    "data/intermediate/countries/japan/geojson"
)

OUTPUT_DIR = Path(
    "public/data/countries/japan/geojson"
)


# Percentage of removable vertices retained by Mapshaper.
#
# These are intentionally defined separately because the three datasets
# can be tuned independently after inspecting their resulting file sizes
# and appearance on the map.
SIMPLIFY_PERCENTAGES = {
    "regions": 75,
    "prefectures": 80,
    "municipalities": 40,
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
    Simplifies one administrative GeoJSON dataset with Mapshaper.
    """

    input_path = INPUT_DIR / f"{name}.geojson"
    output_path = OUTPUT_DIR / f"{name}.geojson"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    print(
        f"Simplifying {name} "
        f"({percentage}% retained)..."
    )

    command = [
        mapshaper,
        str(input_path),
        "-simplify",
        f"{percentage}%",
        "weighted",
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
    Simplifies all three Japan administrative datasets.
    """

    mapshaper = find_mapshaper()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Simplifying Japan administrative GeoJSON...")
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