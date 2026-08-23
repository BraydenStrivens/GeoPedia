/**
 * Provides centralized access to GeoPedia's static country data.
 *
 * Individual country data files are organized geographically and imported
 * into a single country registry. The rest of the application can then
 * retrieve a country's information using its country ID without needing
 * to know where that country's data file is physically stored.
 *
 * New countries should be imported and added to `countries` as their
 * country data is added to GeoPedia.
 */

import { CountryData } from "@/types/country";

import { usaData } from "./north-america/usa";

/**
 * Maps each GeoPedia country ID to its corresponding static country data.
 */
const countries: Partial<Record<string, CountryData>> = {
  usa: usaData,
};

/**
 * Returns the static data associated with a country.
 *
 * Country IDs are normalized to lowercase because external geographic
 * data, such as ISO alpha-3 codes, may provide them in uppercase.
 *
 * Returns `undefined` when no country with the provided ID is registered.
 */
export function getCountry(countryId: string) {
  const normalizedCountryId = countryId.toLowerCase();

  return countries[normalizedCountryId];
}
