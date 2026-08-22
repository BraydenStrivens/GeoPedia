import type { MapConfig } from "../../types";

export const usStateAbbreviationsMap: MapConfig = {
  id: "us-state-abbreviations",
  geojsonUrl: "/data/us-states.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-98.5, 39.8],
    zoom: 3.5,
  },

  layers: {
    fill: {
      color: "#969696",
      opacity: 0.35,
    },

    borders: {
      color: "#000000",
      width: 1.5,
    },
  },
};
