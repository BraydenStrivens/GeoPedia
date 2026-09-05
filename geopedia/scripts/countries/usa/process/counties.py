"""
Processes the Census cartographic county shapefile for GeoPedia.

The output keeps only the properties needed by the application:

- geoid: unique county/county-equivalent identifier
- name: short county name
- fullName: full Census label such as "Santa Clara County"
- state: two-letter state/territory abbreviation
- stateName: full state/territory name

The cartographic boundary source is already simplified, so no additional
geometry simplification is applied initially.
"""

import json
from pathlib import Path

import shapefile
from shapely.geometry import mapping, shape


INPUT_FILE = Path(
    "data/raw/cb_2025_us_county_500k/"
    "cb_2025_us_county_500k.shp"
)

OUTPUT_FILE = Path(
    "public/data/us-counties.geojson"
)

SIMPLIFY_TOLERANCE = 0.005

def main():
    if not INPUT_FILE.exists():
        print(
            f"ERROR: Input file not found: "
            f"{INPUT_FILE}"
        )
        return

    reader = shapefile.Reader(
        str(INPUT_FILE)
    )

    field_names = [
        field[0]
        for field in reader.fields[1:]
    ]

    geoid_index = field_names.index(
        "GEOID"
    )

    name_index = field_names.index(
        "NAME"
    )

    full_name_index = field_names.index(
        "NAMELSAD"
    )

    state_index = field_names.index(
        "STUSPS"
    )

    state_name_index = field_names.index(
        "STATE_NAME"
    )

    output_features = []

    for shape_record in reader.iterShapeRecords():
        record = shape_record.record

        geoid = str(
            record[geoid_index]
        )

        county_name = str(
            record[name_index]
        )

        full_name = str(
            record[full_name_index]
        )

        state = str(
            record[state_index]
        )

        state_name = str(
            record[state_name_index]
        )

        geometry = shape(
            shape_record.shape.__geo_interface__
        )
        
        geometry = geometry.simplify(
            SIMPLIFY_TOLERANCE,
            preserve_topology=True,
        )

        output_features.append(
            {
                "type": "Feature",
                "id": geoid,
                "properties": {
                    "geoid": geoid,
                    "name": county_name,
                    "fullName": full_name,
                    "state": state,
                    "stateName": state_name,
                },
                "geometry": mapping(
                    geometry
                ),
            }
        )

    output_features.sort(
        key=lambda feature: (
            feature["properties"]["state"],
            feature["properties"]["name"],
        )
    )

    output_geojson = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output_geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    size_mb = (
        OUTPUT_FILE.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"Wrote {OUTPUT_FILE}"
    )

    print(
        f"Features: "
        f"{len(output_features)}"
    )

    print(
        f"Size: {size_mb:.2f} MB"
    )


if __name__ == "__main__":
    main()