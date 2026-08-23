/**
 * Synchronizes runtime map-display settings with an existing MapLibre map.
 *
 * Initial persisted settings are applied by `useMap` while the map is being
 * created. This hook handles changes made by the user after the map is ready.
 */

import type { Map as MapLibreMap } from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import {
  setBaseMapBordersVisible,
  setBaseMapLabelsVisible,
} from "@/maps/style/mapStyleVisibility";

/**
 * Values required to synchronize runtime display settings.
 */
type UseMapDisplaySettingsParams = {
  /** Current MapLibre map instance. */
  mapRef: RefObject<MapLibreMap | null>;

  /** Whether GeoPedia's geographic source and layers are ready. */
  isMapReady: boolean;

  /** Whether base-map labels should be visible. */
  showLabels: boolean;

  /** Whether geographic borders should be visible. */
  showBorders: boolean;
};

/**
 * Applies runtime label and border setting changes to the existing map.
 *
 * @param params - Map readiness and display settings to synchronize.
 */
export function useMapDisplaySettings({
  mapRef,
  isMapReady,
  showLabels,
  showBorders,
}: UseMapDisplaySettingsParams): void {
  /**
   * Synchronizes the visibility of symbol layers supplied by the base style.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    setBaseMapLabelsVisible(map, showLabels);
  }, [mapRef, isMapReady, showLabels]);

  /**
   * Synchronizes both GeoPedia feature borders and administrative boundaries
   * supplied by the base-map style.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map || !map.getLayer("features-borders")) {
      return;
    }

    /* GeoPedia geographic feature borders */
    map.setLayoutProperty(
      "features-borders",
      "visibility",
      showBorders ? "visible" : "none",
    );

    /* Administrative boundaries supplied by the base-map style */
    setBaseMapBordersVisible(map, showBorders);
  }, [mapRef, isMapReady, showBorders]);
}
