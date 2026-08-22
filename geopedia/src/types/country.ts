/**
 * Defines the structure of the static country information used by GeoPedia.
 *
 * Country data contains the geographic and general information displayed
 * on each country's page, such as its name, region, flag, capital, and
 * population. Quiz definitions are stored separately and associated with
 * countries through their country IDs.
 */
export type CountryData = {
  /** Unique lowercase three-letter identifier used by GeoPedia. */
  id: string;

  name: string;
  officialName: string;
  continent: string;
  region: string;
  callingCode: string;
  drivingSide: "left" | "right";
  flagUrl: string;
  imageUrl: string;
  capital: string;
  population: number;
};
