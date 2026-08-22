/**
 * Creates the MapLibre base style used by a GeoPedia map.
 *
 * GeoPedia maps can either use a full MapTiler style or a minimal
 * style consisting only of a solid background. Geographic feature
 * layers are added separately after the style has loaded.
 */

import type { StyleSpecification } from "maplibre-gl";

import type { MapStyle } from "@/maps/types";

/**
 * Converts a GeoPedia MapStyle configuration into a MapLibre style.
 */
export function createMapStyle(
  style: MapStyle,
): string | StyleSpecification {
  if (style.type === "maptiler") {
    return (
      "https://api.maptiler.com/maps/streets-v2/style.json?key=" +
      process.env.NEXT_PUBLIC_MAPTILER_KEY
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
          "background-color": style.backgroundColor,
        },
      },
    ],
  };
}
