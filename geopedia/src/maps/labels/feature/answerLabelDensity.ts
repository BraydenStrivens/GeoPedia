/**
 * Controls how many Show Answers labels should be rendered on dense maps.
 *
 * Sparse maps can display every visible answer. Maps containing thousands
 * of small geographic features can instead limit the initial number of DOM
 * markers and progressively reveal more labels as the user zooms in.
 */

import type {
  Map as MapLibreMap,
  MapGeoJSONFeature,
} from "maplibre-gl";

import type { AnswerLabelConfig } from "@/maps/types";

type FeatureEntry = [string, MapGeoJSONFeature];

/**
 * Selects items at approximately even intervals through an array.
 *
 * This avoids simply taking the first N features returned by MapLibre, which
 * could cluster all rendered labels in one portion of the result set.
 *
 * @param items - Items available for selection.
 * @param maxCount - Maximum number of items to return.
 * @returns Original items when under the limit, otherwise an evenly sampled
 * subset.
 */
function selectEvenlyDistributedItems<T>(
  items: T[],
  maxCount: number,
): T[] {
  if (items.length <= maxCount) {
    return items;
  }

  const selectedItems: T[] = [];

  const selectionInterval = items.length / maxCount;

  for (let index = 0; index < maxCount; index++) {
    selectedItems.push(items[Math.floor(index * selectionInterval)]);
  }

  return selectedItems;
}

/**
 * Applies a map's optional Show Answers density limit to visible features.
 *
 * Maps without density configuration return every feature. Configured maps
 * begin throttling only after their visible-feature threshold is exceeded.
 * The maximum label count then increases as the user zooms beyond the map's
 * initial zoom level.
 *
 * @param map - MapLibre map used to determine the current zoom level.
 * @param features - Deduplicated visible geographic features.
 * @param config - Optional label-density configuration for the map.
 * @param initialZoom - Zoom level used when the map initially opens.
 * @returns Features that should currently receive answer labels.
 */
export function limitAnswerLabelFeatures(
  map: MapLibreMap,
  features: FeatureEntry[],
  config?: AnswerLabelConfig,
  initialZoom?: number,
): FeatureEntry[] {
  if (!config) {
    return features;
  }

  const densityThreshold = config.densityThreshold ?? Infinity;

  if (features.length <= densityThreshold) {
    return features;
  }

  const initialMaxLabels = config.initialMaxLabels ?? 100;

  const labelsPerZoom = config.labelsPerZoom ?? 250;

  const currentZoom = map.getZoom();

  const baseZoom = initialZoom ?? currentZoom;

  const zoomDifference = Math.max(0, currentZoom - baseZoom);

  const maxLabels = Math.max(
    1,
    Math.floor(initialMaxLabels + zoomDifference * labelsPerZoom),
  );

  return selectEvenlyDistributedItems(features, maxLabels);
}
