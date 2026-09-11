import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Mexico's geographic telephone-code regions.
 *
 * Individual geographic features may contain multiple valid phone-code
 * answers, such as the shared 55 / 56 region around Mexico City.
 */
export const mexicoPhoneCodesMap = createMapConfig({
  id: "mexico-phone-codes",
  geojsonUrl: "/data/countries/mexico/geojson/phone-codes.geojson",

  featureProperty: "area_codes",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  promoteId: "phone_code_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-102, 23.5],
    zoom: 3.6,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "area_codes",
  },
});
