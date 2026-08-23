/**
 * Creates the base MapLibre style used by a GeoPedia map.
 *
 * GeoPedia maps can use either:
 *
 * - A full MapTiler streets style.
 * - A minimal style containing only a solid background.
 *
 * GeoPedia's own geographic feature layers are added separately after the
 * base style finishes loading.
 */

import type { StyleSpecification } from "maplibre-gl";

import type { MapStyle } from "@/maps/types";

/**
 * Converts a GeoPedia map-style configuration into a MapLibre-compatible
 * style value.
 *
 * MapTiler configurations return a remote style URL. Minimal configurations
 * return an inline MapLibre style specification containing only a background
 * layer.
 *
 * @param mapStyle - GeoPedia base-style configuration.
 * @returns A MapLibre style URL or inline style specification.
 */
export function createMapStyle(
  mapStyle: MapStyle,
): string | StyleSpecification {
  if (mapStyle.type === "maptiler") {
    const mapTilerApiKey = process.env.NEXT_PUBLIC_MAPTILER_KEY;

    return (
      "https://api.maptiler.com/maps/streets-v2/style.json?key=" +
      mapTilerApiKey
    );
  }

  return {
    version: 8,

    sources: {},

    layers: [
      {
        id: "background",
        type: "background",

        paint: {
          "background-color": mapStyle.backgroundColor,
        },
      },
    ],
  };
}
