/**
 * Creates the base MapLibre style used by a GeoPedia map.
 *
 * GeoPedia maps can use either:
 *
 * - A full MapTiler streets style.
 * - A minimal style containing only a solid background.
 *
 * Remote MapTiler styles are fetched before map creation so GeoPedia can apply
 * initial label visibility before MapLibre renders its first frame.
 */

import type {
  LayerSpecification,
  StyleSpecification,
} from "maplibre-gl";

import { isQuizRelevantBaseMapLabelLayer } from "@/maps/style/mapStyleVisibility";
import type { MapStyle } from "@/maps/types";

/**
 * Applies GeoPedia's initial base-label visibility directly to a style
 * specification before MapLibre renders it.
 *
 * Quiz-relevant settlement and state/province labels always remain hidden.
 * Other symbol layers follow the user's persisted base-label setting.
 *
 * @param style - Loaded MapLibre style specification.
 * @param shouldShowLabels - Current persisted base-label setting.
 */
function applyInitialLabelVisibility(
  style: StyleSpecification,
  shouldShowLabels: boolean,
): void {
  for (const layer of style.layers) {
    if (layer.type !== "symbol") {
      continue;
    }

    const shouldHide =
      isQuizRelevantBaseMapLabelLayer(layer as LayerSpecification) ||
      !shouldShowLabels;

    if (!shouldHide) {
      continue;
    }

    layer.layout = {
      ...layer.layout,
      visibility: "none",
    };
  }
}

/**
 * Converts a GeoPedia map-style configuration into a fully prepared MapLibre
 * style specification.
 *
 * MapTiler styles are downloaded before MapLibre creation. This lets GeoPedia
 * remove answer-revealing labels before the first rendered map frame and
 * eliminates the visible base-label flash.
 *
 * @param mapStyle - GeoPedia base-style configuration.
 * @param shouldShowLabels - Current persisted base-label visibility setting.
 * @returns Prepared MapLibre style specification.
 */
export async function createMapStyle(
  mapStyle: MapStyle,
  shouldShowLabels: boolean,
): Promise<StyleSpecification> {
  if (mapStyle.type === "maptiler") {
    const mapTilerApiKey = process.env.NEXT_PUBLIC_MAPTILER_KEY;

    const styleUrl =
      "https://api.maptiler.com/maps/streets-v2/style.json?key=" +
      mapTilerApiKey;

    const response = await fetch(styleUrl);

    if (!response.ok) {
      throw new Error(
        `Failed to load MapTiler style: ${response.status} ${response.statusText}`,
      );
    }

    const style = (await response.json()) as StyleSpecification;

    applyInitialLabelVisibility(style, shouldShowLabels);

    return style;
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
