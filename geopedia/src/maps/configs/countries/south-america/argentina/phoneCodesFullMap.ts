import { createMapConfig } from "@/maps/configs/createMapConfig";

export const argentinaPhoneCodesFullMap = createMapConfig({
  id: "argentina-phone-codes-full",

  geojsonUrl:
    "/data/countries/argentina/geojson/phone-codes-full.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64, -38],
    zoom: 3.6,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
