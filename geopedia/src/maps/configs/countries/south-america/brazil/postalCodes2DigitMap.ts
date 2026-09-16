import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Brazil's 2-digit CEP postal-code regions.
 *
 * Geographic features store their complete set of valid CEP-2 answers in the
 * `postal_codes` array. Most features contain one answer, while major
 * municipalities such as São Paulo, Rio de Janeiro, and Brasília may contain
 * several valid prefixes.
 *
 * Disconnected geographic areas with the same complete answer set are stored
 * as parts of the same Polygon/MultiPolygon feature.
 */
export const brazilPostalCodes2DigitMap = createMapConfig({
  id: "brazil-postal-codes",

  geojsonUrl: "/data/countries/brazil/geojson/postal-codes.geojson",

  featureProperty: "postal_codes",
  promoteId: "postal_code_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-52.5, -14.5],
    zoom: 3.2,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "postal_codes",
  },
});
