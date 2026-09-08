import type { MapLayerConfig } from "@/maps/types";

/**
 * Shared geographic-layer appearance used by GeoPedia maps unless a map
 * configuration explicitly overrides one of these values.
 */
export const DEFAULT_MAP_LAYERS: MapLayerConfig = {
  fill: {
    color: "#969696",
    opacity: 0.35,
  },

  borders: {
    color: "#000000",
    width: 1,
  },
};

/**
 * Default hover color used by interactive geographic features.
 */
export const DEFAULT_FEATURE_HOVER_COLOR = "#4e4e4e";

/**
 * Whether feature hovering is enabled when a map supplies hover configuration
 * but does not explicitly override its enabled state.
 */
export const DEFAULT_FEATURE_HOVER_ENABLED = true;
