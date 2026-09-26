from pathlib import Path

from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_JAPAN_DIR = PROJECT_ROOT / "data" / "raw" / "countries" / "japan"
PUBLIC_JAPAN_DIR = PROJECT_ROOT / "public" / "data" / "countries" / "japan"

IMAGE_SIZE = 1024

IMAGE_SETS = [
    "pole-plates",
    "pole-tops",
]

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def process_image(source_path: Path, output_path: Path) -> None:
    with Image.open(source_path) as image:
        # Respect EXIF orientation before cropping.
        image = ImageOps.exif_transpose(image)

        width, height = image.size

        if width < height:
            raise ValueError(
                f"{source_path} is taller than it is wide "
                f"({width}x{height}). Cannot create a square by cropping "
                "only the width."
            )

        # Keep the entire height and center-crop only the width.
        left = (width - height) // 2
        right = left + height

        image = image.crop((left, 0, right, height))

        # Resize the square crop to 512x512.
        image = image.resize(
            (IMAGE_SIZE, IMAGE_SIZE),
            Image.Resampling.LANCZOS,
        )

        # These are photographic quiz images, so RGB is sufficient.
        if image.mode != "RGB":
            image = image.convert("RGB")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        image.save(
            output_path,
            format="WEBP",
            quality=90,
            method=6,
        )


def process_image_set(image_set: str) -> None:
    source_dir = RAW_JAPAN_DIR / image_set
    output_dir = PUBLIC_JAPAN_DIR / image_set

    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source directory does not exist: {source_dir}"
        )

    source_files = sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    print()
    print(f"{image_set}: {len(source_files)} source images")

    for source_path in source_files:
        output_path = output_dir / f"{source_path.stem}.webp"

        process_image(source_path, output_path)

        print(
            f"  {source_path.name} -> "
            f"{output_path.relative_to(PROJECT_ROOT)}"
        )


def main() -> None:
    for image_set in IMAGE_SETS:
        process_image_set(image_set)

    print()
    print("Done.")


if __name__ == "__main__":
    main()