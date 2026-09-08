/**
 * Creates complete GeoPedia map configurations from map-specific values and
 * shared defaults.
 */

import {
  DEFAULT_FEATURE_HOVER_COLOR,
  DEFAULT_FEATURE_HOVER_ENABLED,
  DEFAULT_MAP_LAYERS,
} from "@/maps/configs/defaults";

import {
  FeatureBorderConfig,
  FeatureFillConfig,
  MapConfig,
} from "../types";

export type MapLayerOverrides = {
  /** Optional overrides to the standard geographic fill appearance. */
  fill?: Partial<FeatureFillConfig>;

  /** Optional overrides to the standard geographic border appearance. */
  borders?: Partial<FeatureBorderConfig>;
};

export type HoverConfigOverrides = {
  /** GeoJSON property displayed when identifying a hovered feature. */
  labelProperty: string;

  /** Optional override to the standard hover-enabled state. */
  enabled?: boolean;

  /** Optional override to the standard feature hover color. */
  color?: string;
};

export type MapConfigInput = Omit<MapConfig, "layers" | "hover"> & {
  /** Optional geographic-layer values overriding GeoPedia's defaults. */
  layers?: MapLayerOverrides;

  /**
   * Optional hover configuration.
   *
   * Omitting this entire property means that the map does not support feature
   * hovering.
   */
  hover?: HoverConfigOverrides;
};

/**
 * Creates a complete runtime map configuration.
 *
 * Map definitions only need to supply geographic-layer and hover values that
 * differ from GeoPedia's shared defaults. Missing values are filled here once,
 * allowing the rest of the map system to consume a complete `MapConfig`
 * without performing additional default resolution.
 *
 * @param input - Map-specific configuration and optional visual overrides.
 * @returns Complete map configuration ready for runtime use.
 */
export function createMapConfig(input: MapConfigInput): MapConfig {
  return {
    ...input,

    layers: {
      fill: {
        ...DEFAULT_MAP_LAYERS.fill,
        ...input.layers?.fill,
      },

      borders: {
        ...DEFAULT_MAP_LAYERS.borders,
        ...input.layers?.borders,
      },
    },

    hover: input.hover
      ? {
          labelProperty: input.hover.labelProperty,

          enabled:
            input.hover.enabled ?? DEFAULT_FEATURE_HOVER_ENABLED,

          color: input.hover.color ?? DEFAULT_FEATURE_HOVER_COLOR,
        }
      : undefined,
  };
}
