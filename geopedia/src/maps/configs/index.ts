/**
 * Provides centralized access to GeoPedia's country-specific and global map
 * configurations.
 *
 * Each country's maps are stored in its own folder and exported through that
 * folder's index file. Global maps are stored separately because they are not
 * owned by one individual country.
 *
 * This module combines those exports into registries so application code can
 * retrieve maps by country and map ID, or retrieve maps used by GeoPedia's
 * Global section, without knowing where the underlying configuration files are
 * stored.
 *
 * New countries should be imported and added to `countryMapRegistry` as their
 * maps are added to GeoPedia. New global maps should be exported from the
 * Global map index so they are automatically included in `globalMapRegistry`.
 */

import type { MapConfig } from "@/maps/types";

import * as globalMaps from "./global";
import * as usaMaps from "./usa";

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
 * Stores every map configuration registered for GeoPedia's Global section.
 *
 * Object.values() converts the Global map module exports into an array, so
 * newly exported global map configurations are automatically included without
 * maintaining a second manual list.
 */
const globalMapRegistry: MapConfig[] = Object.values(globalMaps);

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
export function getCountryMap(
  countryId: string,
  mapId: string,
): MapConfig | undefined {
  return getCountryMaps(countryId).find(
    (mapConfig) => mapConfig.id === mapId,
  );
}

/**
 * Returns every map configuration registered for GeoPedia's Global section.
 *
 * @returns All registered global map configurations.
 */
export function getGlobalMaps(): MapConfig[] {
  return globalMapRegistry;
}

/**
 * Finds a specific map configuration registered for GeoPedia's Global section.
 *
 * @param mapId - Unique identifier of the global map configuration to retrieve.
 * @returns The matching global map configuration, or `undefined` when the map
 * is not registered.
 */
export function getGlobalMap(mapId: string): MapConfig | undefined {
  return globalMapRegistry.find(
    (mapConfig) => mapConfig.id === mapId,
  );
}
