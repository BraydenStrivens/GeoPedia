import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Panama's regional taxi and bus licence-plate codes.
 */
export const panamaTaxiBusPlateCodesMap = createMapConfig({
  id: "panama-taxi-bus-plate-codes",

  geojsonUrl:
    "/data/countries/panama/geojson/taxi-bus-plate-codes.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-80.5, 8.5],
    zoom: 5.7,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
