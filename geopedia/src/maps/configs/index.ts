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

import * as ghanaMaps from "./countries/africa/ghana";
import * as kenyaMaps from "./countries/africa/kenya";
import * as nigeriaMaps from "./countries/africa/nigeria";
import * as rwandaMaps from "./countries/africa/rwanda";
import * as saoTomeMaps from "./countries/africa/sao_tome_and_principe";
import * as senegalMaps from "./countries/africa/senegal";
import * as tunisiaMaps from "./countries/africa/tunisia";
import * as ugandaMaps from "./countries/africa/uganda";
import * as costaRicaMaps from "./countries/central-america/costa-rica";
import * as dominicanRepublicMaps from "./countries/central-america/dominican-republic";
import * as guatemalaMaps from "./countries/central-america/guatemala";
import * as panamaMaps from "./countries/central-america/panama";
import * as canadaMaps from "./countries/north-america/canada";
import * as mexicoMaps from "./countries/north-america/mexico";
import * as puertoRicoMaps from "./countries/north-america/puerto-rico";
import * as usVirginIslandMaps from "./countries/north-america/us-virgin-islands";
import * as usaMaps from "./countries/north-america/usa";
import * as argentinaMaps from "./countries/south-america/argentina";
import * as boliviaMaps from "./countries/south-america/bolivia";
import * as brazilMaps from "./countries/south-america/brazil";
import * as chileMaps from "./countries/south-america/chile";
import * as colombiaMaps from "./countries/south-america/colombia";
import * as ecuadorMaps from "./countries/south-america/ecuador";
import * as paraguayMaps from "./countries/south-america/paraguay";
import * as peruMaps from "./countries/south-america/peru";
import * as uruguayMaps from "./countries/south-america/uruguay";
import * as globalMaps from "./global";

/**
 * Maps each country ID to every map configuration registered for that country.
 *
 * Object.values() converts a country's module exports into an array, so newly
 * exported map configurations are automatically included without maintaining
 * a second manual list.
 */
const countryMapRegistry: Record<string, MapConfig[]> = {
  // North America
  usa: Object.values(usaMaps),
  can: Object.values(canadaMaps),
  mex: Object.values(mexicoMaps),
  pri: Object.values(puertoRicoMaps),
  vir: Object.values(usVirginIslandMaps),

  // Central America
  cri: Object.values(costaRicaMaps),
  pan: Object.values(panamaMaps),
  dom: Object.values(dominicanRepublicMaps),
  gtm: Object.values(guatemalaMaps),

  // South America
  col: Object.values(colombiaMaps),
  bra: Object.values(brazilMaps),
  ecu: Object.values(ecuadorMaps),
  per: Object.values(peruMaps),
  bol: Object.values(boliviaMaps),
  pry: Object.values(paraguayMaps),
  ury: Object.values(uruguayMaps),
  arg: Object.values(argentinaMaps),
  chl: Object.values(chileMaps),

  // Africa
  sen: Object.values(senegalMaps),
  tun: Object.values(tunisiaMaps),
  gha: Object.values(ghanaMaps),
  nga: Object.values(nigeriaMaps),
  stp: Object.values(saoTomeMaps),
  ken: Object.values(kenyaMaps),
  uga: Object.values(ugandaMaps),
  rwa: Object.values(rwandaMaps),
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
