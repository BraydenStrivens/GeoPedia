import { createMapConfig } from "@/maps/configs/createMapConfig";

export const argentinaPhoneCodes2DigitMap = createMapConfig({
  id: "argentina-phone-codes-2-digit",

  geojsonUrl:
    "/data/countries/argentina/geojson/phone-codes-2-digit.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64, -38],
    zoom: 3.6,
  },

  layers: {
    borders: {
      width: 1.25,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
