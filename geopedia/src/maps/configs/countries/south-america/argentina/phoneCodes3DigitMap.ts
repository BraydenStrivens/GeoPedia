import { createMapConfig } from "@/maps/configs/createMapConfig";

export const argentinaPhoneCodes3DigitMap = createMapConfig({
  id: "argentina-phone-codes-3-digit",

  geojsonUrl:
    "/data/countries/argentina/geojson/phone-codes-3-digit.geojson",

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

  hover: {
    labelProperty: "area_code",
  },
});
