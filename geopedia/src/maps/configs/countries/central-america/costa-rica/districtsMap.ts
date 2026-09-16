import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Costa Rica's 492 districts.
 *
 * District IDs correspond to Costa Rica's 5-digit administrative codes and
 * can also be used directly as 5-digit postal codes.
 */
export const costaRicaDistrictsMap = createMapConfig({
  id: "costa-rica-districts",
  geojsonUrl: "/data/countries/costa-rica/geojson/districts.geojson",
  featureProperty: "name",

  answerLabels: {
    densityThreshold: 250,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  promoteId: "district_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-84.1, 9.8],
    zoom: 6.5,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
