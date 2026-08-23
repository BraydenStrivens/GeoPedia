/**
 * Defines the static country information used throughout GeoPedia.
 *
 * Country data contains the geographic and general information displayed
 * on country pages and used elsewhere in the application. Quiz definitions
 * are stored separately and associated with countries through their country
 * IDs.
 */
export type CountryData = {
  /** Unique lowercase three-letter identifier used by GeoPedia. */
  id: string;

  /** Common user-facing name of the country. */
  name: string;

  /** Full official name of the country. */
  officialName: string;

  /** Continent containing the country. */
  continent: string;

  /** Geographic region containing the country. */
  region: string;

  /** International telephone calling code for the country. */
  callingCode: string;

  /** Side of the road on which vehicles drive in the country. */
  drivingSide: "left" | "right";

  /** URL of the country's flag image. */
  flagUrl: string;

  /** URL of the image used to represent the country. */
  imageUrl: string;

  /** Capital city of the country. */
  capital: string;

  /** Population of the country. */
  population: number;
};
