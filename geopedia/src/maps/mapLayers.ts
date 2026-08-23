/**
 * Adds GeoPedia's shared GeoJSON source and visual feature layers
 * to an existing MapLibre map.
 *
 * This file is responsible only for creating the geographic source,
 * feature fill layer, and feature border layer. Interaction behavior
 * such as clicking and hovering is configured elsewhere.
 */

import type * as maplibregl from "maplibre-gl";

import type { MapConfig } from "@/maps/types";

type AddMapLayersParams = {
  geojsonUrl: string;
  promoteId?: string;
  layers: MapConfig["layers"];
  hover?: MapConfig["hover"];
  showShading: boolean;
  showBorders: boolean;
};

/**
 * Adds the map's GeoJSON source, fill layer, and border layer.
 */
export function addMapLayers(
  map: maplibregl.Map,
  {
    geojsonUrl,
    promoteId,
    layers,
    showShading,
    showBorders,
  }: AddMapLayersParams,
) {
  map.addSource("features", {
    type: "geojson",
    data: geojsonUrl,
    promoteId,
  });

  map.addLayer({
    id: "features-fill",
    type: "fill",
    source: "features",
    paint: {
      /*
       * Shading is controlled through the fill-color expression rather than
       * fill-opacity. Keeping the layer opacity constant allows Shading to be
       * turned back on after the map initially loads with it disabled.
       */
      "fill-color": showShading ? layers.fill.color : "rgba(0, 0, 0, 0)",

      "fill-opacity": layers.fill.opacity,

      "fill-outline-color": "rgba(0, 0, 0, 0)",
    },
  });

  map.addLayer({
    id: "features-hover",
    type: "fill",
    source: "features",
    paint: {
      "fill-color": "#000000",
      "fill-opacity": [
        "case",
        ["boolean", ["feature-state", "hover"], false],
        0.2,
        0,
      ],
      "fill-outline-color": "rgba(0, 0, 0, 0)",
    },
  });

  map.addLayer({
    id: "features-borders",
    type: "line",
    source: "features",

    layout: {
      visibility: showBorders ? "visible" : "none",
    },

    paint: {
      "line-color": layers.borders.color,
      "line-width": layers.borders.width,
    },
  });
}
