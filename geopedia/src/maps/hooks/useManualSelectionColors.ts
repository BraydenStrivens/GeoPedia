/**
 * Synchronizes manual quiz-group feature selections with MapLibre's dedicated
 * selection overlay.
 *
 * Selected feature IDs are applied as a layer filter so manual-selection
 * highlighting remains independent from:
 *
 * - Normal map shading.
 * - Quiz-result coloring.
 * - Hover highlighting.
 * - Active-group feature filtering.
 *
 * When no features are selected, the selection layer is hidden completely.
 */

"use client";

import type {
  FilterSpecification,
  Map as MapLibreMap,
} from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import { FEATURE_SELECTION_LAYER_ID } from "../constants/mapLayerIds";

/**
 * Parameters required to synchronize manual-selection coloring.
 */
type UseManualSelectionColorsParams = {
  /** Ref containing the MapLibre map instance. */
  mapRef: RefObject<MapLibreMap | null>;

  /** Whether GeoPedia's map source and feature layers are ready for updates. */
  isMapReady: boolean;

  /**
   * GeoJSON property used as the stable geographic feature identifier.
   *
   * Manual selection requires this property so the selected React-side feature
   * IDs can be matched back to MapLibre features.
   */
  promoteId?: string;

  /** Stable IDs of the geographic features currently selected. */
  selectedFeatureIds: ReadonlySet<string>;
};

/**
 * Filters GeoPedia's manual-selection overlay to the currently selected
 * geographic features.
 *
 * @param params - Map state, stable ID property, and selected feature IDs.
 */
export function useManualSelectionColors({
  mapRef,
  isMapReady,
  promoteId,
  selectedFeatureIds,
}: UseManualSelectionColorsParams): void {
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    if (!map.getLayer(FEATURE_SELECTION_LAYER_ID)) {
      return;
    }

    /*
     * Without a stable feature-ID property, React's selected feature IDs cannot
     * be matched safely to MapLibre features.
     */
    if (!promoteId) {
      return;
    }

    /*
     * Hide the overlay entirely when the manual-selection draft is empty.
     */
    if (selectedFeatureIds.size === 0) {
      map.setLayoutProperty(
        FEATURE_SELECTION_LAYER_ID,
        "visibility",
        "none",
      );

      return;
    }

    /*
     * Ensure the overlay is visible before applying the current selection
     * filter.
     */
    map.setLayoutProperty(
      FEATURE_SELECTION_LAYER_ID,
      "visibility",
      "visible",
    );

    /*
     * Match selected IDs against normalized string representations of the
     * configured GeoJSON feature-ID property.
     */
    const selectionFilter: FilterSpecification = [
      "in",
      ["to-string", ["get", promoteId]],
      ["literal", Array.from(selectedFeatureIds)],
    ];

    map.setFilter(FEATURE_SELECTION_LAYER_ID, selectionFilter);
  }, [mapRef, isMapReady, promoteId, selectedFeatureIds]);
}
