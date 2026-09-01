/**
 * Defines country-specific geographic configuration for GeoPedia town quizzes.
 *
 * Town quizzes share the same MapLibre implementation and MapTiler base style,
 * so they do not require separate map configurations for each country. The only
 * values that vary by country are the initial camera position and the maximum
 * error distance used when scoring geographic guesses.
 *
 * This module centralizes those country-specific values so the generic town
 * quiz and town map implementations can resolve everything they need from a
 * country ID without requiring individual country quiz or map files.
 */

/**
 * Initial MapLibre camera position used when opening a country's town quiz.
 */
export type TownQuizInitialView = {
  /** Longitude and latitude displayed at the center of the map. */
  center: [number, number];

  /** Initial MapLibre zoom level used to frame the country. */
  zoom: number;
};

/**
 * Country-specific configuration required by the generic town quiz engine.
 */
export type TownCountryConfig = {
  /** Initial camera position used when the country's town map opens. */
  initialView: TownQuizInitialView;

  /**
   * Maximum geographic error distance used when scoring town guesses.
   *
   * Guesses at or beyond this distance receive the minimum score. The scoring
   * function determines how scores decrease between the target and this
   * maximum distance.
   */
  maxErrorKm: number;
};

/**
 * Returns the country-specific configuration for a town quiz.
 *
 * @param countryId - Lowercase three-letter GeoPedia country identifier.
 * @returns Town quiz configuration belonging to the country, or `undefined`
 * when the country does not currently have a configured town quiz.
 */
export function getTownCountryConfig(
  countryId: string,
): TownCountryConfig | undefined {
  return townCountryConfigs[countryId];
}

/**
 * Country-specific configuration used by GeoPedia town quizzes.
 *
 * Keys correspond to GeoPedia's lowercase three-letter country IDs and match
 * the filenames generated under `public/data/towns`.
 *
 * Additional countries should be added here as their town quizzes become
 * available.
 */
export const townCountryConfigs: Record<string, TownCountryConfig> = {
  usa: {
    initialView: {
      center: [-98.5, 39.5],
      zoom: 3,
    },
    maxErrorKm: 1250,
  },

  fra: {
    initialView: {
      center: [2.2, 46.2],
      zoom: 5,
    },
    maxErrorKm: 150,
  },

  jpn: {
    initialView: {
      center: [138, 37],
      zoom: 4.5,
    },
    maxErrorKm: 250,
  },
};
