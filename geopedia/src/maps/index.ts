/**
 * Provides centralized access to GeoPedia's country-specific map
 * configurations.
 *
 * Each country's maps are stored in its own folder and exported through
 * that folder's index file. This file combines those exports into a country
 * map registry so the rest of the application can retrieve maps using
 * country and map IDs without needing to know where the map files are
 * physically stored.
 *
 * New countries should be imported and added to `countryMaps` as their
 * maps are added to GeoPedia.
 */

import * as usaMaps from "./country/usa";

/**
 * Maps each country ID to all map configurations exported for that country.
 *
 * Object.values() converts each country's module exports into an array,
 * allowing multiple maps to be added to a country without manually
 * maintaining a separate map array.
 */
const countryMaps = {
  usa: Object.values(usaMaps),
};

/**
 * Returns all map configurations available for a country.
 *
 * Country IDs are normalized to lowercase because external geographic
 * data, such as ISO alpha-3 codes, may provide them in uppercase.
 */
export function getCountryMaps(countryId: string) {
  const normalizedCountryId = countryId.toLowerCase();

  return (
    countryMaps[normalizedCountryId as keyof typeof countryMaps] ?? []
  );
}

/**
 * Finds a specific map configuration belonging to a country.
 *
 * Returns `undefined` when the country does not exist or when no map
 * with the provided map ID is registered for that country.
 */
export function getMap(countryId: string, mapId: string) {
  return getCountryMaps(countryId).find((map) => map.id === mapId);
}
