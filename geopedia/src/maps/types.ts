/**
 * Defines the shared configuration and state types used by GeoPedia's reusable
 * map system.
 *
 * These types describe:
 *
 * - Base-map styling.
 * - Initial camera position.
 * - Geographic feature styling.
 * - Stable feature identity.
 * - Click and hover behavior.
 * - Show Answers label density.
 * - Temporary map interaction state.
 *
 * Country- and quiz-specific map definitions use `MapConfig`, allowing the
 * shared map system to remain independent of individual countries and quizzes.
 */

import { AnswerLabelContent } from "./labels/feature/answerLabelTypes";

/**
 * Defines the base visual style rendered underneath GeoPedia's geographic
 * feature layers.
 *
 * - `maptiler` uses GeoPedia's configured MapTiler style.
 * - `minimal` renders only a solid background beneath GeoPedia's own layers.
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
 * Determines what happens when the user clicks a geographic feature on a QuizMap.
 *
 * - `quiz` treats the selected feature as an attempted quiz answer.
 * - `select` toggles the feature in a manual quiz-group selection.
 * - `none` disables geographic feature click behavior.
 */
export type QuizMapClickBehavior = "quiz" | "select" | "none";

/**
 * Defines the camera position used when a map is first displayed.
 */
export type MapInitialView = {
  /** Initial longitude and latitude of the map center. */
  center: [number, number];

  /** Initial MapLibre zoom level. */
  zoom: number;
};

/**
 * Defines the appearance of GeoPedia's geographic fill layer.
 */
export type FeatureFillConfig = {
  /** Default fill color of geographic features. */
  color: string;

  /** Opacity applied to the geographic fill layer. */
  opacity: number;
};

/**
 * Defines the appearance of GeoPedia's geographic border layer.
 */
export type FeatureBorderConfig = {
  /** Color of geographic feature boundary lines. */
  color: string;

  /** Width of geographic feature boundary lines. */
  width: number;
};

/**
 * Defines the appearance of GeoPedia's geographic feature layers.
 */
export type MapLayerConfig = {
  /** Configuration for the main geographic polygon fill layer. */
  fill: FeatureFillConfig;

  /** Configuration for the explicit geographic boundary layer. */
  borders: FeatureBorderConfig;
};

/**
 * Defines the behavior and appearance of geographic feature hovering.
 */
export type HoverConfig = {
  /** Determines whether this map supports geographic feature hovering. */
  enabled: boolean;

  /** Color used to visually distinguish a hovered feature. */
  color: string;

  /** GeoJSON property used by maps that display a floating hover label. */
  labelProperty: string;
};

/**
 * Controls Show Answers label throttling for maps containing large numbers of
 * geographic features.
 *
 * Maps without this configuration render all eligible answer labels.
 */
export type AnswerLabelConfig = {
  /** Visible-feature count above which label throttling begins. */
  densityThreshold?: number;

  /** Maximum labels rendered at the map's initial zoom level. */
  initialMaxLabels?: number;

  /** Additional labels allowed for each zoom level above the initial zoom. */
  labelsPerZoom?: number;
};

/**
 * Represents the feature currently displayed by a map's floating hover label.
 */
export type HoveredFeature = {
  /** Text displayed in the floating hover label. */
  name: string;

  /** Horizontal cursor position relative to the map. */
  x: number;

  /** Vertical cursor position relative to the map. */
  y: number;
};

/**
 * Represents temporary feedback displayed after an incorrect map selection.
 */
export type IncorrectSelection = {
  /** Complete answer-label content belonging to the selected feature. */
  content: AnswerLabelContent;

  /** Horizontal cursor position at which the selection occurred. */
  x: number;

  /** Vertical cursor position at which the selection occurred. */
  y: number;
};

/**
 * Controls which contextual labels and administrative boundaries supplied by
 * the base-map style are available on a GeoPedia map.
 *
 * Every property is optional and defaults to `true`. Map configurations only
 * need to specify categories they want to hide.
 *
 * These values describe the map itself rather than a user's runtime display
 * preferences. Global settings such as Show Labels and Show Borders may still
 * hide categories that a map configuration allows.
 */
export type BaseMapLayerVisibilityConfig = {
  /** Whether country-name labels supplied by the base map are visible. */
  countryLabels?: boolean;

  /** Whether state, province, and other first-level subdivision labels are visible. */
  subdivisionLabels?: boolean;

  /** Whether settlement labels such as capitals, cities, towns, and villages are visible. */
  townLabels?: boolean;

  /** Whether international/country boundaries supplied by the base map are visible. */
  countryBorders?: boolean;

  /** Whether internal administrative subdivision boundaries are visible. */
  subdivisionBorders?: boolean;
};

/**
 * Defines the data, appearance, initial camera state, and supported
 * interactions of a GeoPedia map.
 *
 * Map configurations contain only map-specific information. Quiz-specific
 * behavior, such as which GeoJSON property represents the correct answer,
 * belongs to the corresponding `Quiz` definition instead.
 */
export type MapConfig = {
  /** Unique identifier used to retrieve this map configuration. */
  id: string;

  /** URL of the GeoJSON file containing this map's geographic features. */
  geojsonUrl: string;

  /**
   * GeoJSON property representing the map's primary geographic feature value.
   *
   * This describes the map data itself and remains separate from a quiz's
   * `answerProperty`.
   */
  featureProperty: string;

  /** Base visual style rendered underneath GeoPedia's geographic layers. */
  style: MapStyle;

  /**
   * Optional visibility overrides for labels and administrative boundaries
   * supplied by the base-map style.
   *
   * Omitted values default to visible.
   */
  baseMapLayers?: BaseMapLayerVisibilityConfig;

  /**
   * GeoJSON property promoted by MapLibre to `feature.id`.
   *
   * Stable feature identity is used by:
   *
   * - Hover feature-state.
   * - Show Answers label matching.
   * - Quiz-group resolution.
   * - Manual feature selection.
   * - Active-group map filtering.
   */
  promoteId?: string;

  /** Initial camera position displayed when the map opens. */
  initialView: MapInitialView;

  /** Appearance of GeoPedia's geographic feature layers. */
  layers: MapLayerConfig;

  /** Optional hover behavior supported by this map. */
  hover?: HoverConfig;

  /** Optional Show Answers label-density configuration for large maps. */
  answerLabels?: AnswerLabelConfig;
};
