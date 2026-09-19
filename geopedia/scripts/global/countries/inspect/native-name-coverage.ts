/**
 * Inspects REST Countries language and native-name coverage for GeoPedia's
 * country dataset.
 *
 * The report groups countries by native-name coverage, highlights source
 * inconsistencies, identifies countries whose available native common names
 * differ meaningfully enough to require a preferred-language decision, and
 * prints the final distinct native displays GeoPedia would generate for audit.
 *
 * Name equivalence uses GeoPedia's shared comparison rules, so differences
 * limited to capitalization, diacritics, punctuation, whitespace, or separator
 * formatting do not create unnecessary language-selection decisions.
 *
 * REST Countries' `UNK` code for Kosovo is normalized to GeoPedia's canonical
 * `XKX` identifier. Records without an ISO-3 code are outside GeoPedia's
 * 250-country dataset and are ignored.
 *
 * Run from the repository root with:
 *
 *   npx tsx scripts/global/countries/inspect/native-name-coverage.ts
 */

import { readFile } from "node:fs/promises";
import path from "node:path";

import { areNamesEquivalent } from "../../../tools/nameComparison";
import { getCountryNativeLanguage } from "../utils/getCountryNativeLanguage";

const REST_COUNTRIES_PATH = path.resolve(
  "data/raw/global/countries/rest-countries-v5.json",
);

/**
 * Maps REST Countries source-specific country codes to GeoPedia's canonical
 * ISO-3-style identifiers.
 */
const REST_COUNTRY_CODE_ALIASES: Readonly<Record<string, string>> = {
  UNK: "XKX",
};

interface RestLanguage {
  iso639_3?: string;
  name?: string;
  native_name?: string;
}

interface RestNativeName {
  common?: string;
  official?: string;
}

interface RestCountry {
  names?: {
    common?: string;
    native?: Record<string, RestNativeName>;
  };
  codes?: {
    alpha_3?: string | null;
  };
  languages?: RestLanguage[];
}

interface CountrySummary {
  code: string;
  englishName: string;
  languages: RestLanguage[];
  nativeNames: Record<string, RestNativeName>;
}

/**
 * Returns GeoPedia's canonical country code for a REST Countries record.
 */
function getCountryCode(country: RestCountry): string | undefined {
  const rawCode = country.codes?.alpha_3;

  if (typeof rawCode !== "string" || rawCode.length === 0) {
    return undefined;
  }

  return REST_COUNTRY_CODE_ALIASES[rawCode] ?? rawCode;
}

/**
 * Formats a language/native-name entry for readable console output.
 */
function formatNativeName(
  languageCode: string,
  nativeName: RestNativeName,
  languages: RestLanguage[],
): string {
  const language = languages.find(
    (candidate) => candidate.iso639_3 === languageCode,
  );

  const languageName = language?.name ?? "unknown language";
  const commonName = nativeName.common ?? "(missing common name)";

  return `${languageCode} (${languageName}): ${commonName}`;
}

/**
 * Loads the REST Countries dataset and reports native-name coverage.
 */
async function main(): Promise<void> {
  const rawText = await readFile(REST_COUNTRIES_PATH, "utf8");
  const rawCountries = JSON.parse(rawText) as RestCountry[];

  if (!Array.isArray(rawCountries)) {
    throw new Error("REST Countries raw data is not an array.");
  }

  const countries: CountrySummary[] = [];

  for (const country of rawCountries) {
    const code = getCountryCode(country);

    if (!code) {
      continue;
    }

    countries.push({
      code,
      englishName: country.names?.common ?? "(missing English name)",
      languages: country.languages ?? [],
      nativeNames: country.names?.native ?? {},
    });
  }

  console.log("\nPreferred native-language resolution:");

  let resolutionErrorCount = 0;

  for (const country of countries) {
    try {
      getCountryNativeLanguage(country.code, country.nativeNames);
    } catch (error: unknown) {
      resolutionErrorCount += 1;

      console.log(
        `  ${country.code} ${country.englishName}: ${
          error instanceof Error ? error.message : error
        }`,
      );
    }
  }

  if (resolutionErrorCount === 0) {
    console.log("  All 250 countries resolved successfully.");
  } else {
    console.log(
      `  ${resolutionErrorCount} country resolution error(s).`,
    );
  }

  countries.sort((a, b) => a.code.localeCompare(b.code));

  const noNativeNames = countries.filter(
    (country) => Object.keys(country.nativeNames).length === 0,
  );

  const oneNativeName = countries.filter(
    (country) => Object.keys(country.nativeNames).length === 1,
  );

  const multipleNativeNames = countries.filter(
    (country) => Object.keys(country.nativeNames).length > 1,
  );

  /**
   * Countries whose available native common names contain at least two
   * meaningfully different values.
   *
   * Superficial differences such as capitalization, punctuation, separators,
   * and diacritics do not create a language-selection decision.
   */
  const nativeNameDecisions = multipleNativeNames.filter(
    (country) => {
      const commonNames = Object.values(country.nativeNames)
        .map((nativeName) => nativeName.common)
        .filter(
          (name): name is string =>
            typeof name === "string" && name.length > 0,
        );

      if (commonNames.length <= 1) {
        return false;
      }

      const firstName = commonNames[0];

      return commonNames.some(
        (name) => !areNamesEquivalent(firstName, name),
      );
    },
  );

  const languageCodesWithoutNativeName: string[] = [];
  const nativeNamesWithoutLanguage: string[] = [];

  for (const country of countries) {
    const languageCodes = new Set(
      country.languages
        .map((language) => language.iso639_3)
        .filter(
          (code): code is string =>
            typeof code === "string" && code.length > 0,
        ),
    );

    const nativeNameCodes = new Set(Object.keys(country.nativeNames));

    for (const languageCode of languageCodes) {
      if (!nativeNameCodes.has(languageCode)) {
        languageCodesWithoutNativeName.push(
          `${country.code} ${country.englishName}: ${languageCode}`,
        );
      }
    }

    for (const nativeNameCode of nativeNameCodes) {
      if (!languageCodes.has(nativeNameCode)) {
        nativeNamesWithoutLanguage.push(
          `${country.code} ${country.englishName}: ${nativeNameCode}`,
        );
      }
    }
  }

  console.log("Native country-name coverage");
  console.log("============================");

  console.log(`Countries inspected: ${countries.length}`);
  console.log(
    `Countries with no native names: ${noNativeNames.length}`,
  );
  console.log(
    `Countries with one native name: ${oneNativeName.length}`,
  );
  console.log(
    `Countries with multiple native names: ${multipleNativeNames.length}`,
  );

  console.log("\nCountries with no native names:");

  if (noNativeNames.length === 0) {
    console.log("  none");
  } else {
    for (const country of noNativeNames) {
      console.log(`  ${country.code} ${country.englishName}`);
    }
  }

  console.log("\nLanguage codes without matching native names:");

  if (languageCodesWithoutNativeName.length === 0) {
    console.log("  none");
  } else {
    for (const entry of languageCodesWithoutNativeName) {
      console.log(`  ${entry}`);
    }
  }

  console.log("\nNative-name codes without matching languages:");

  if (nativeNamesWithoutLanguage.length === 0) {
    console.log("  none");
  } else {
    for (const entry of nativeNamesWithoutLanguage) {
      console.log(`  ${entry}`);
    }
  }

  console.log(
    "\nCountries requiring a preferred native-language decision:",
  );

  for (const country of nativeNameDecisions) {
    console.log(`\n${country.code} — ${country.englishName}`);

    for (const [languageCode, nativeName] of Object.entries(
      country.nativeNames,
    )) {
      console.log(
        `  ${formatNativeName(
          languageCode,
          nativeName,
          country.languages,
        )}`,
      );
    }
  }

  console.log(
    "\nFinal native displays that GeoPedia would generate:",
  );
  console.log("=================================================");

  let generatedNativeDisplayCount = 0;

  const countriesByEnglishName = [...countries].sort((a, b) =>
    a.englishName.localeCompare(b.englishName, "en"),
  );

  for (const country of countriesByEnglishName) {
    const nativeLanguageCode = getCountryNativeLanguage(
      country.code,
      country.nativeNames,
    );

    if (nativeLanguageCode === null) {
      continue;
    }

    const nativeDisplay =
      country.nativeNames[nativeLanguageCode]?.common?.trim();

    if (!nativeDisplay) {
      throw new Error(
        `${country.code} preferred native language '${nativeLanguageCode}' ` +
          "has no valid common name.",
      );
    }

    if (areNamesEquivalent(country.englishName, nativeDisplay)) {
      continue;
    }

    const language = country.languages.find(
      (candidate) => candidate.iso639_3 === nativeLanguageCode,
    );

    const languageName = language?.name ?? "unknown language";

    console.log(
      `  ${country.code} ${country.englishName} → ${nativeDisplay} ` +
        `[${nativeLanguageCode}, ${languageName}]`,
    );

    generatedNativeDisplayCount += 1;
  }

  console.log(
    `\nFinal distinct native displays: ${generatedNativeDisplayCount}`,
  );

  console.log(
    `\nCountries with multiple native-name entries: ${multipleNativeNames.length}`,
  );

  console.log(
    `Countries requiring a preferred native-language decision: ${nativeNameDecisions.length}`,
  );
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);

  process.exitCode = 1;
});
