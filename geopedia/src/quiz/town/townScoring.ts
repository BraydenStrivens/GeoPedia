/**
 * Provides geographic distance and scoring utilities for GeoPedia town quizzes.
 *
 * Town quiz guesses are arbitrary longitude/latitude coordinates rather than
 * predefined map features. This module calculates the great-circle distance
 * between a user's guess and the target town, then converts that geographic
 * error into a normalized quiz score.
 *
 * Town scoring intentionally includes a small perfect-score radius because
 * requiring a pixel-perfect city-center selection would provide false precision
 * at the country-scale zoom levels used by these quizzes. Outside that radius,
 * scores use a softened nonlinear falloff until reaching the country-specific
 * maximum error distance.
 *
 * Geographic math remains independent from React quiz state so scoring can be
 * tested and tuned without modifying the quiz lifecycle.
 */

/** Mean Earth radius used by the Haversine distance calculation. */
const EARTH_RADIUS_KM = 6371;

/**
 * Distance around the target town that receives a perfect score.
 *
 * Five kilometers is intentionally small relative to country-scale quiz maps
 * while forgiving insignificant differences between the user's click and the
 * exact coordinate chosen for a town.
 */
const PERFECT_SCORE_RADIUS_KM = 5;

/**
 * Controls how aggressively scores fall after leaving the perfect-score radius.
 *
 * Values below 1 make intermediate guesses less punishing than a linear
 * falloff while preserving 100% at the perfect radius and 0% at maxErrorKm.
 */
const SCORE_CURVE_EXPONENT = 0.65;

/**
 * Latitude/longitude coordinate used by town quiz geographic calculations.
 */
export type GeographicCoordinate = {
  /** Latitude measured in decimal degrees. */
  latitude: number;

  /** Longitude measured in decimal degrees. */
  longitude: number;
};

/**
 * Converts degrees to radians.
 *
 * @param degrees - Angle measured in degrees.
 * @returns Equivalent angle measured in radians.
 */
function degreesToRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/**
 * Calculates the great-circle distance between two geographic coordinates
 * using the Haversine formula.
 *
 * @param first - First geographic coordinate.
 * @param second - Second geographic coordinate.
 * @returns Distance between the coordinates in kilometers.
 */
export function getGeographicDistanceKm(
  first: GeographicCoordinate,
  second: GeographicCoordinate,
): number {
  const firstLatitude = degreesToRadians(first.latitude);

  const secondLatitude = degreesToRadians(second.latitude);

  const latitudeDifference = degreesToRadians(
    second.latitude - first.latitude,
  );

  const longitudeDifference = degreesToRadians(
    second.longitude - first.longitude,
  );

  const haversine =
    Math.sin(latitudeDifference / 2) ** 2 +
    Math.cos(firstLatitude) *
      Math.cos(secondLatitude) *
      Math.sin(longitudeDifference / 2) ** 2;

  const angularDistance =
    2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));

  return EARTH_RADIUS_KM * angularDistance;
}

/**
 * Converts geographic error distance into a normalized score from 0 through 1.
 *
 * Guesses within the perfect-score radius receive full credit. Guesses at or
 * beyond the country's configured maximum error distance receive zero.
 *
 * Intermediate guesses use a softened nonlinear falloff. This gives useful
 * partial credit to answers that demonstrate approximately correct geographic
 * knowledge while still strongly rewarding accurate placement.
 *
 * The country-specific `maxErrorKm` should represent a clearly unreasonable
 * answer for that country's geographic scale rather than an ordinary mistake.
 *
 * @param distanceKm - Distance between the guess and target in kilometers.
 * @param maxErrorKm - Distance at which the score reaches zero.
 * @returns Normalized score from 0 through 1.
 */
export function getTownGuessScore(
  distanceKm: number,
  maxErrorKm: number,
): number {
  /*
   * Degenerate configurations cannot provide a useful scoring range. Preserve
   * exact-match behavior rather than dividing by zero or a negative distance.
   */
  if (maxErrorKm <= 0) {
    return distanceKm === 0 ? 1 : 0;
  }

  /* Nearby guesses are effectively exact at country-scale map zooms. */
  if (distanceKm <= PERFECT_SCORE_RADIUS_KM) {
    return 1;
  }

  /*
   * A maximum error smaller than the perfect radius leaves no partial-credit
   * interval, so every guess outside the perfect radius receives zero.
   */
  if (maxErrorKm <= PERFECT_SCORE_RADIUS_KM) {
    return 0;
  }

  /*
   * Remove the perfect-radius portion before normalization so the partial-credit
   * curve spans the complete remaining distance to maxErrorKm.
   */
  const adjustedDistanceKm = distanceKm - PERFECT_SCORE_RADIUS_KM;

  const adjustedMaxErrorKm = maxErrorKm - PERFECT_SCORE_RADIUS_KM;

  const normalizedDistance = Math.min(
    Math.max(adjustedDistanceKm / adjustedMaxErrorKm, 0),
    1,
  );

  /*
   * The exponent below 1 softens intermediate errors while still preserving the
   * exact endpoints:
   *
   * normalizedDistance = 0 → score 1
   * normalizedDistance = 1 → score 0
   */
  return Math.pow(1 - normalizedDistance, SCORE_CURVE_EXPONENT);
}
