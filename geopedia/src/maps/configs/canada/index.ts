/**
 * Provides a single export point for all Canada map configurations.
 *
 * Each Canada map is defined in its own file and re-exported here. The root
 * map registry can then import all Canada maps from this folder at once without
 * needing to know about each individual map file.
 *
 * New Canada maps should be exported here after their map
 * configuration is created.
 */

export { canadaCensusDivisionsMap } from "./censusDivisionsMap";
export { canadaPhoneCodesMap } from "./phoneCodesMap";
export { canadaProvincesMap } from "./provincesMap";
