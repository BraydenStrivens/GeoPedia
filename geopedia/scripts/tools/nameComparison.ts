/**
 * Shared geographic-name comparison helpers used by GeoPedia's data-generation
 * scripts.
 *
 * These helpers determine whether two names differ meaningfully enough to
 * justify separate user-facing representations.
 *
 * Comparison intentionally ignores capitalization, diacritics, whitespace,
 * punctuation, and separator formatting while preserving Unicode letters and
 * numbers. Characters are not transliterated between writing systems, so
 * genuinely different names such as `Tokyo` / `東京`, `Vienna` / `Wien`, and
 * `Moscow` / `Москва` remain distinct.
 */

/**
 * Normalizes a geographic name for loose display-equivalence comparison.
 *
 * The normalization ignores:
 *
 * - capitalization
 * - accents and diacritics
 * - punctuation
 * - whitespace
 * - separator formatting such as spaces, hyphens, and slashes
 *
 * Unicode letters and numbers are preserved. The function deliberately does
 * not transliterate between writing systems or attempt fuzzy spelling
 * correction.
 *
 * Examples that normalize identically include:
 *
 * - `Bacău` / `Bacau`
 * - `Random Property` / `random-property`
 * - `Random Property` / `random - property`
 * - `Random Property` / `random/property`
 *
 * Examples that remain different include:
 *
 * - `Tokyo` / `東京`
 * - `Vienna` / `Wien`
 * - `Moscow` / `Москва`
 *
 * @param value - Geographic name to normalize.
 * @returns Comparable Unicode name key.
 */
export function normalizeNameForComparison(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLocaleLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, "");
}

/**
 * Determines whether two geographic names differ only by superficial display
 * formatting or orthographic differences ignored by GeoPedia.
 *
 * This comparison is suitable for deciding whether a separate native-language
 * display value is useful. It does not apply feature-specific semantic rules,
 * such as treating an optional `City` suffix as equivalent for town names.
 *
 * @param firstName - First geographic name.
 * @param secondName - Second geographic name.
 * @returns Whether the two names are equivalent for general display purposes.
 */
export function areNamesEquivalent(
  firstName: string,
  secondName: string,
): boolean {
  return (
    normalizeNameForComparison(firstName) ===
    normalizeNameForComparison(secondName)
  );
}

/**
 * Returns whether two names are visually equivalent for display purposes.
 *
 * Comparison ignores capitalization and punctuation/separator differences,
 * but preserves diacritics and script differences because those differences
 * are useful when displaying native/local names.
 */
export function areDisplayNamesEquivalent(
  firstName: string,
  secondName: string,
): boolean {
  const normalize = (value: string): string =>
    value
      .normalize("NFC")
      .toLocaleLowerCase()
      .replace(/[^\p{Letter}\p{Number}]+/gu, "");

  return normalize(firstName) === normalize(secondName);
}
