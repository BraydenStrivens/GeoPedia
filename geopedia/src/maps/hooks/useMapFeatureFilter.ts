/**
 * Restricts GeoPedia's geographic layers to a selected set of feature IDs.
 *
 * Quiz grouping uses this hook to display and interact with only the
 * geographic features belonging to the currently active group.
 *
 * The underlying GeoJSON source remains unchanged. Filtering is applied
 * directly to GeoPedia's existing MapLibre layers.
 */

import type {
  FilterSpecification,
  Map as MapLibreMap,
} from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

/**
 * GeoPedia layers that represent the quiz's geographic feature set.
 */
const FILTERED_FEATURE_LAYER_IDS = [
  "features-fill",
  "features-hover",
  "features-borders",
] as const;

/**
 * Values required to synchronize an active feature filter.
 */
type UseMapFeatureFilterParams = {
  /** Current MapLibre map instance. */
  mapRef: RefObject<MapLibreMap | null>;

  /** Whether GeoPedia's geographic layers are ready. */
  isMapReady: boolean;

  /**
   * GeoJSON property used by MapLibre as the stable feature ID.
   *
   * Group filtering uses the same property so the resolver and rendered map
   * identify geographic features consistently.
   */
  promoteId?: string;

  /**
   * Feature IDs belonging to the active group.
   *
   * `null` represents Full Quiz and removes all grouping filters.
   */
  featureIds: string[] | null;
};

/**
 * Applies the active quiz group's feature IDs to all GeoPedia geographic
 * layers.
 *
 * Full Quiz clears the filters so every source feature is displayed.
 *
 * @param params - Map readiness and active feature IDs.
 */
export function useMapFeatureFilter({
  mapRef,
  isMapReady,
  promoteId,
  featureIds,
}: UseMapFeatureFilterParams): void {
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    /**
     * Full Quiz uses the entire GeoJSON source and therefore needs no filter.
     */
    if (featureIds === null) {
      for (const layerId of FILTERED_FEATURE_LAYER_IDS) {
        if (map.getLayer(layerId)) {
          map.setFilter(layerId, null);
        }
      }

      return;
    }

    /*
     * Filtered groups require the same stable source property used to promote
     * feature IDs.
     */
    if (!promoteId) {
      return;
    }

    /*
     * Restrict each geographic layer to features whose promoted-ID source
     * property belongs to the active group.
     */
    const featureFilter: FilterSpecification = [
      "in",
      ["get", promoteId],
      ["literal", featureIds],
    ];

    for (const layerId of FILTERED_FEATURE_LAYER_IDS) {
      if (map.getLayer(layerId)) {
        map.setFilter(layerId, featureFilter);
      }
    }
  }, [mapRef, isMapReady, promoteId, featureIds]);
}
