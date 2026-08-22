/**
 * Defines the configuration types used by GeoPedia's reusable map system.
 *
 * These types describe how a map is displayed and behaves, including its
 * base style, geographic data, initial camera position, feature styling,
 * click behavior, feature-state identity, and optional hover behavior.
 *
 * Individual map definitions use `MapConfig` so the shared Map component
 * can render maps for different countries and quizzes without containing
 * country-specific configuration.
 */

/**
 * Defines the base visual style used underneath a map's geographic
 * features.
 *
 * MapTiler uses the configured MapTiler style, while the minimal style
 * renders only a solid background underneath GeoPedia's own layers.
 */
export type MapStyle =
  | {
      type: "maptiler";
    }
  | {
      type: "minimal";
      backgroundColor: string;
    };

/**
 * Defines what should happen when the user clicks a geographic feature.
 *
 * `quiz` treats the clicked feature as a quiz answer.
 * `navigate` uses the clicked feature to navigate to another page.
 */
export type MapClickBehavior = "quiz" | "navigate" | "none";

/**
 * Defines the behavior and appearance of feature hovering on a map.
 */
export type HoverConfig = {
  enabled: boolean;
  color: string;

  /** GeoJSON property used as the feature's hover label. */
  labelProperty: string;
};

/**
 * Represents the feature currently being displayed by the map's
 * floating hover label.
 */
export type HoveredFeature = {
  /** Text displayed in the hover label. */
  name: string;

  /** Horizontal cursor position within the map. */
  x: number;

  /** Vertical cursor position within the map. */
  y: number;
};

/**
 * Describes temporary feedback shown after the user clicks an incorrect
 * geographic feature.
 */
export type IncorrectSelection = {
  label: string;
  x: number;
  y: number;
};

/**
 * Defines the data, appearance, and interaction behavior of a GeoPedia map.
 */
export type MapConfig = {
  /** Unique identifier used to retrieve this map configuration. */
  id: string;

  /** URL of the GeoJSON file containing the map's geographic features. */
  geojsonUrl: string;

  /**
   * Property used to identify geographic features within the map's data.
   *
   * Quiz answer matching is handled separately by the quiz's
   * `answerProperty`.
   */
  featureProperty: string;

  /** Base visual style displayed underneath the geographic features. */
  style: MapStyle;

  /**
   * GeoJSON property that MapLibre promotes to `feature.id`.
   *
   * This provides a stable feature identifier for MapLibre feature-state
   * operations such as hover highlighting. The property must exist inside
   * each GeoJSON feature's `properties` object.
   */
  promoteId?: string;

  /** Camera position used when the map is first displayed. */
  initialView: {
    center: [number, number];
    zoom: number;
  };

  /** Visual configuration for GeoPedia's geographic feature layers. */
  layers: {
    fill: {
      color: string;
      opacity: number;
    };

    borders: {
      color: string;
      width: number;
    };
  };

  /**
   * Optional behavior and appearance used when hovering over features.
   *
   * When enabled, the hovered feature can be highlighted and a selected
   * GeoJSON property can be displayed to the user.
   */
  hover?: {
    enabled: boolean;
    color: string;
    labelProperty: string;
  };
};
