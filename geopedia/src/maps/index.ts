/**
 * Provides centralized access to GeoPedia's country-specific map
 * configurations.
 *
 * Each country's maps are stored in its own folder and exported through that
 * folder's index file. This module combines those exports into one registry
 * so application code can retrieve maps by country and map ID without knowing
 * where the underlying configuration files are stored.
 *
 * New countries should be imported and added to `countryMapRegistry` as their
 * maps are added to GeoPedia.
 */

import type { MapConfig } from "@/maps/types";

import * as usaMaps from "./configs/usa";

/**
 * Maps each country ID to every map configuration registered for that country.
 *
 * Object.values() converts a country's module exports into an array, so newly
 * exported map configurations are automatically included without maintaining
 * a second manual list.
 */
const countryMapRegistry: Record<string, MapConfig[]> = {
  usa: Object.values(usaMaps),
};

/**
 * Returns every map configuration registered for a country.
 *
 * Country IDs are normalized to lowercase because routing or external
 * geographic data may provide IDs using different capitalization.
 *
 * @param countryId - Country whose map configurations should be retrieved.
 * @returns All maps registered for the country, or an empty array when the
 * country is not registered.
 */
export function getCountryMaps(countryId: string): MapConfig[] {
  const normalizedCountryId = countryId.toLowerCase();

  return countryMapRegistry[normalizedCountryId] ?? [];
}

/**
 * Finds a specific map configuration registered for a country.
 *
 * @param countryId - Country containing the requested map.
 * @param mapId - Unique identifier of the map configuration to retrieve.
 * @returns The matching map configuration, or `undefined` when either the
 * country or map is not registered.
 */
export function getMap(
  countryId: string,
  mapId: string,
): MapConfig | undefined {
  return getCountryMaps(countryId).find(
    (mapConfig) => mapConfig.id === mapId,
  );
}
