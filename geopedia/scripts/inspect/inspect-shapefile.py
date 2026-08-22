"""
Generic shapefile inspection utility.

Prints:

- feature count
- field names
- the first few records

Usage:

    python scripts/inspect/inspect_shapefile.py path/to/file.shp
"""

import sys
from pathlib import Path

import shapefile


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python "
            "scripts/inspect/inspect_shapefile.py "
            "<shapefile>"
        )
        return

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(
            f"ERROR: File not found: {file_path}"
        )
        return

    reader = shapefile.Reader(
        str(file_path)
    )

    field_names = [
        field[0]
        for field in reader.fields[1:]
    ]

    print(
        "Feature count:",
        len(reader),
    )

    print("\nFields:")

    for field_name in field_names:
        print(
            f"  {field_name}"
        )

    print("\nFirst 5 records:")

    for record in reader.records()[:5]:
        values = {
            field_names[index]: value
            for index, value in enumerate(
                record
            )
        }

        print(values)


if __name__ == "__main__":
    main()