/**
 * Resolves GeoPedia's preferred native language for country data generation.
 *
 * Countries with exactly one native-name language resolve automatically.
 * Countries with multiple native-name languages also resolve automatically
 * when every available common name is meaningfully equivalent under
 * GeoPedia's shared geographic-name comparison rules.
 *
 * Countries whose native common names differ meaningfully must have an
 * explicit entry in `COUNTRY_NATIVE_LANGUAGE_OVERRIDES`, preventing REST
 * Countries source ordering from silently determining GeoPedia's language
 * choice.
 *
 * A null override explicitly disables native-language generation.
 */

import { areNamesEquivalent } from "../../../tools/nameComparison";
import { COUNTRY_NATIVE_LANGUAGE_OVERRIDES } from "./countryNativeLanguages";

interface RestNativeName {
  common?: string;
  official?: string;
}

/**
 * Returns whether all available native common names are meaningfully
 * equivalent.
 *
 * Native-name entries without a usable common name are ignored for comparison.
 */
function areAllNativeNamesEquivalent(
  nativeNames: Record<string, RestNativeName>,
): boolean {
  const commonNames = Object.values(nativeNames)
    .map((nativeName) => nativeName.common)
    .filter(
      (name): name is string =>
        typeof name === "string" && name.length > 0,
    );

  if (commonNames.length <= 1) {
    return true;
  }

  const firstName = commonNames[0];

  return commonNames.every((name) =>
    areNamesEquivalent(firstName, name),
  );
}

/**
 * Returns the preferred REST Countries native-language code for a country.
 *
 * Countries without native-name data return null naturally. When multiple
 * languages provide equivalent native common names, the first source language
 * is safe to use because the resulting user-facing name is equivalent
 * regardless of which language entry supplies it.
 *
 * @throws If a country has meaningfully different native common names but no
 * explicit override, or if an override references a native-name language
 * absent from the source record.
 */
export function getCountryNativeLanguage(
  countryCode: string,
  nativeNames: Record<string, RestNativeName>,
): string | null {
  if (
    Object.prototype.hasOwnProperty.call(
      COUNTRY_NATIVE_LANGUAGE_OVERRIDES,
      countryCode,
    )
  ) {
    const override = COUNTRY_NATIVE_LANGUAGE_OVERRIDES[countryCode];

    if (override === null) {
      return null;
    }

    if (!(override in nativeNames)) {
      throw new Error(
        `${countryCode} native-language override '${override}' ` +
          "does not exist in its REST Countries native names.",
      );
    }

    return override;
  }

  const nativeLanguageCodes = Object.keys(nativeNames);

  if (nativeLanguageCodes.length === 0) {
    return null;
  }

  if (
    nativeLanguageCodes.length === 1 ||
    areAllNativeNamesEquivalent(nativeNames)
  ) {
    return nativeLanguageCodes[0];
  }

  throw new Error(
    `${countryCode} has meaningfully different REST Countries ` +
      "native-name languages but no GeoPedia preferred-language " +
      `override: ${nativeLanguageCodes.join(", ")}`,
  );
}
