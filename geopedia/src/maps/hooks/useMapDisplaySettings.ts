/**
 * Synchronizes runtime map-display settings with an existing MapLibre map.
 *
 * Initial persisted settings are applied by `useMap` while the map is being
 * created. This hook handles changes made by the user after the map is ready.
 */

import type { Map as MapLibreMap } from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import { applyBaseMapLayerVisibility } from "@/maps/style/mapStyleVisibility";
import type { BaseMapLayerVisibilityConfig } from "@/maps/types";

/**
 * Values required to synchronize runtime display settings.
 */
type UseMapDisplaySettingsParams = {
  /** Current MapLibre map instance. */
  mapRef: RefObject<MapLibreMap | null>;

  /** Whether GeoPedia's geographic source and layers are ready. */
  isMapReady: boolean;

  /**
   * Map-specific visibility permissions for contextual base-map layers.
   *
   * Omitted values default to visible.
   */
  baseMapLayers?: BaseMapLayerVisibilityConfig;

  /** Global master switch controlling base-map labels. */
  showLabels: boolean;

  /** Global master switch controlling geographic borders. */
  showBorders: boolean;
};

/**
 * Applies runtime label and border setting changes to the existing map.
 *
 * Map-specific base-layer visibility and user display settings are combined
 * rather than applied independently. A layer is visible only when both the
 * map configuration permits it and the corresponding global setting is on.
 *
 * @param params - Map readiness and display settings to synchronize.
 */
export function useMapDisplaySettings({
  mapRef,
  isMapReady,
  baseMapLayers,
  showLabels,
  showBorders,
}: UseMapDisplaySettingsParams): void {
  /**
   * Synchronizes contextual labels and administrative boundaries supplied by
   * the base-map style.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    applyBaseMapLayerVisibility(
      map,
      baseMapLayers,
      showLabels,
      showBorders,
    );
  }, [mapRef, isMapReady, baseMapLayers, showLabels, showBorders]);

  /**
   * Synchronizes GeoPedia's own geographic feature-border layer.
   *
   * This layer is separate from administrative boundaries supplied by the
   * base-map style and therefore follows only GeoPedia's global Borders
   * setting.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map || !map.getLayer("features-borders")) {
      return;
    }

    map.setLayoutProperty(
      "features-borders",
      "visibility",
      showBorders ? "visible" : "none",
    );
  }, [mapRef, isMapReady, showBorders]);
}
