/**
 * Optimizes quiz image assets for GeoPedia.
 *
 * The script processes supported images in a supplied directory, resizes them
 * to fit within the configured maximum dimensions without enlarging smaller
 * images, converts them to WebP, and removes the original files after each
 * conversion succeeds.
 *
 * Output files preserve the original base filename:
 *
 *   bogota_1.png  -> bogota_1.webp
 *   medellin.jpg  -> medellin.webp
 *
 * Supported input formats:
 * - PNG
 * - JPG / JPEG
 * - SVG
 *
 * Usage:
 *
 *   npx tsx scripts/tools/optimize-images.ts <directory>
 *
 * Example:
 *
 *   npx tsx scripts/tools/optimize-images.ts public/data/countries/colombia/pole-lamps
 */

import { readdir, stat, unlink } from "node:fs/promises";
import path from "node:path";

import sharp from "sharp";

/** Longest permitted image dimension in pixels. */
const MAX_IMAGE_DIMENSION = 1000;

/** WebP quality used for optimized quiz images. */
const WEBP_QUALITY = 82;

/** File extensions accepted as source images. */
const SUPPORTED_EXTENSIONS = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".svg",
]);

/**
 * Formats a byte count for terminal output.
 *
 * @param bytes - Number of bytes to format.
 * @returns Human-readable file size.
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Determines whether a file extension represents a supported source image.
 *
 * Existing WebP files are intentionally excluded so already optimized assets
 * are not processed again.
 *
 * @param fileName - File name to inspect.
 * @returns Whether the file can be processed by this script.
 */
function isSupportedImage(fileName: string): boolean {
  return SUPPORTED_EXTENSIONS.has(
    path.extname(fileName).toLowerCase(),
  );
}

/**
 * Converts one source image to an optimized WebP file.
 *
 * The image is resized to fit inside the configured maximum dimensions while
 * preserving its aspect ratio. `withoutEnlargement` prevents small source
 * images from being unnecessarily upscaled.
 *
 * The original source file is deleted only after Sharp successfully writes the
 * WebP output.
 *
 * @param inputPath - Absolute or relative path to the source image.
 * @returns Original and optimized file sizes.
 */
async function optimizeImage(inputPath: string): Promise<{
  inputSize: number;
  outputSize: number;
  outputPath: string;
}> {
  const parsedPath = path.parse(inputPath);

  const outputPath = path.join(
    parsedPath.dir,
    `${parsedPath.name}.webp`,
  );

  const inputStats = await stat(inputPath);

  await sharp(inputPath)
    .resize({
      width: MAX_IMAGE_DIMENSION,
      height: MAX_IMAGE_DIMENSION,
      fit: "inside",
      withoutEnlargement: true,
    })
    .webp({
      quality: WEBP_QUALITY,
    })
    .toFile(outputPath);

  const outputStats = await stat(outputPath);

  /*
   * Delete the original only after the optimized WebP has been written and its
   * output file can be read successfully.
   */
  await unlink(inputPath);

  return {
    inputSize: inputStats.size,
    outputSize: outputStats.size,
    outputPath,
  };
}

/**
 * Optimizes every supported image directly inside a directory.
 *
 * The operation is intentionally non-recursive so processing one quiz asset
 * folder cannot unexpectedly modify images belonging to neighboring quizzes.
 *
 * @param directoryPath - Directory containing source quiz images.
 */
async function optimizeDirectory(
  directoryPath: string,
): Promise<void> {
  const entries = await readdir(directoryPath, {
    withFileTypes: true,
  });

  const imageEntries = entries
    .filter((entry) => entry.isFile() && isSupportedImage(entry.name))
    .sort((a, b) => a.name.localeCompare(b.name));

  if (imageEntries.length === 0) {
    console.log("No supported images found.");

    return;
  }

  let totalInputSize = 0;
  let totalOutputSize = 0;
  let successfulConversions = 0;

  console.log(
    `Optimizing ${imageEntries.length} image${
      imageEntries.length === 1 ? "" : "s"
    }...\n`,
  );

  for (const entry of imageEntries) {
    const inputPath = path.join(directoryPath, entry.name);

    try {
      const result = await optimizeImage(inputPath);

      totalInputSize += result.inputSize;
      totalOutputSize += result.outputSize;
      successfulConversions += 1;

      console.log(
        `${entry.name}  ${formatFileSize(result.inputSize)} -> ` +
          `${path.basename(result.outputPath)}  ` +
          `${formatFileSize(result.outputSize)}`,
      );
    } catch (error) {
      console.error(`Failed to optimize ${entry.name}.`);
      console.error(error);
    }
  }

  console.log("\nFinished.");

  if (successfulConversions === 0) {
    console.log("No images were successfully converted.");

    return;
  }

  const bytesSaved = totalInputSize - totalOutputSize;

  const percentSaved =
    totalInputSize > 0 ? (bytesSaved / totalInputSize) * 100 : 0;

  console.log(`Original:  ${formatFileSize(totalInputSize)}`);
  console.log(`Optimized: ${formatFileSize(totalOutputSize)}`);
  console.log(
    `Saved:     ${formatFileSize(bytesSaved)} (${percentSaved.toFixed(1)}%)`,
  );

  if (successfulConversions !== imageEntries.length) {
    console.log(
      `Converted: ${successfulConversions}/${imageEntries.length}`,
    );
  }
}

/**
 * Runs the image optimizer using the directory supplied on the command line.
 */
async function main(): Promise<void> {
  const directoryArgument = process.argv[2];

  if (!directoryArgument) {
    console.error(
      "Usage: npx tsx scripts/tools/optimize-images.ts <directory>",
    );

    process.exitCode = 1;

    return;
  }

  const directoryPath = path.resolve(directoryArgument);

  try {
    const directoryStats = await stat(directoryPath);

    if (!directoryStats.isDirectory()) {
      console.error(`Not a directory: ${directoryPath}`);
      process.exitCode = 1;

      return;
    }

    await optimizeDirectory(directoryPath);
  } catch (error) {
    console.error(`Unable to optimize directory: ${directoryPath}`);
    console.error(error);

    process.exitCode = 1;
  }
}

void main();
