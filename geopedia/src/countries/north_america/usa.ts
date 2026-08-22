/**
 * Defines the static country information for the United States.
 *
 * This data is used to populate the United States country page and is
 * registered with GeoPedia through the central country data registry.
 * Quiz and map definitions are stored separately and associated with the
 * country through its `usa` country ID.
 */

import type { CountryData } from "@/types/country";

/**
 * Static country data for the United States.
 */
export const usaData: CountryData = {
  id: "usa",

  name: "United States",
  officialName: "United States of America",

  continent: "North America",
  region: "Northern America",

  callingCode: "+1",
  drivingSide: "right",

  flagUrl: "/data/flags/usa.svg",
  imageUrl: "/data/country-images/usa.svg",

  capital: "Washington D.C.",
  population: 340110988,
};
