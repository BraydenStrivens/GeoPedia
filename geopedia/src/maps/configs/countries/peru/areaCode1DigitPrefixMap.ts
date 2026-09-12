import { createMapConfig } from "@/maps/configs/createMapConfig";

export const peruAreaCodes1DigitPrefixMap = createMapConfig({
  id: "peru-area-code-prefixes",
  geojsonUrl:
    "/data/countries/peru/geojson/area-code-prefixes.geojson",

  featureProperty: "area_code_prefix",
  promoteId: "area_code_prefix",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-75.2, -9.3],
    zoom: 4.9,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "area_code_prefix",
  },
});
