/**
 * Restricts GeoPedia's geographic quiz layers to a selected set of feature IDs.
 *
 * Quiz grouping uses this hook to keep the rendered and interactive geography
 * synchronized with the feature subset resolved by the active quiz group.
 *
 * The underlying GeoJSON source is never modified. Filtering is applied only
 * to GeoPedia's normal geographic layers:
 *
 * - Feature fill.
 * - Hover overlay.
 * - Geographic borders.
 *
 * The dedicated manual-selection overlay is intentionally excluded because its
 * filtering is owned independently by `useManualSelectionColors`.
 */

"use client";

import type {
  FilterSpecification,
  Map as MapLibreMap,
} from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import {
  FEATURE_BORDER_LAYER_ID,
  FEATURE_FILL_LAYER_ID,
  FEATURE_HOVER_LAYER_ID,
} from "../constants/mapLayerIds";

/**
 * GeoPedia layers whose visible feature set follows the currently active quiz
 * group.
 */
const GROUP_FILTER_LAYER_IDS = [
  FEATURE_BORDER_LAYER_ID,
  FEATURE_FILL_LAYER_ID,
  FEATURE_HOVER_LAYER_ID,
] as const;

/**
 * Values required to synchronize an active geographic feature filter.
 */
type UseMapFeatureFilterParams = {
  /** Ref containing the current MapLibre map instance. */
  mapRef: RefObject<MapLibreMap | null>;

  /** Whether GeoPedia's geographic source and layers are ready for updates. */
  isMapReady: boolean;

  /**
   * GeoJSON property used as the stable geographic feature identifier.
   *
   * Group filtering reads this same source property used by MapLibre's
   * `promoteId` configuration so React-side resolution and rendered geography
   * identify features consistently.
   */
  promoteId?: string;

  /**
   * Stable feature IDs belonging to the active group.
   *
   * `null` represents Full Quiz and removes all grouping filters.
   *
   * An empty array represents a resolved group containing no features and
   * therefore intentionally hides every group-filtered geographic feature.
   */
  featureIds: string[] | null;
};

/**
 * Applies one filter to every normal geographic layer controlled by active
 * quiz grouping.
 *
 * Missing layers are ignored so synchronization remains safe during map-style
 * lifecycle transitions.
 *
 * @param map - MapLibre map receiving the filter.
 * @param filter - Filter to apply, or `null` to restore the complete source.
 */
function applyGroupFilter(
  map: MapLibreMap,
  filter: FilterSpecification | null,
): void {
  for (const layerId of GROUP_FILTER_LAYER_IDS) {
    if (!map.getLayer(layerId)) {
      continue;
    }

    map.setFilter(layerId, filter);
  }
}

/**
 * Synchronizes the active quiz group's resolved feature IDs with GeoPedia's
 * normal geographic MapLibre layers.
 *
 * Full Quiz clears all group filters. Filtered groups match the configured
 * promoted-ID source property against the resolved feature-ID list.
 *
 * @param params - Map state, stable-ID property, and active feature IDs.
 */
export function useMapFeatureFilter({
  mapRef,
  isMapReady,
  promoteId,
  featureIds,
}: UseMapFeatureFilterParams): void {
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    /*
     * Full Quiz uses the complete GeoJSON source and therefore requires no
     * active-group filter.
     */
    if (featureIds === null) {
      applyGroupFilter(map, null);

      return;
    }

    /*
     * Filtered groups require the stable source property used to identify
     * geographic features consistently with React-side group resolution.
     */
    if (!promoteId) {
      return;
    }

    /*
     * Stable feature IDs are normalized to strings throughout the grouping
     * system, so normalize the GeoJSON source value before comparing it with
     * the resolved ID list.
     */
    const featureFilter: FilterSpecification = [
      "in",
      ["to-string", ["get", promoteId]],
      ["literal", featureIds],
    ];

    applyGroupFilter(map, featureFilter);
  }, [mapRef, isMapReady, promoteId, featureIds]);
}
