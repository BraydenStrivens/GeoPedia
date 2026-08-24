/**
 * Defines the data structures used by GeoPedia's quiz-grouping system.
 *
 * Quiz groups allow a full quiz to be reduced to a subset of its geographic
 * features and questions. Groups can be created either from configured
 * GeoJSON property values or by manually selecting individual map features.
 */

import { Feature } from "maplibre-gl";

/**
 * Identifies a group created from one or more values of a configured GeoJSON
 * property.
 *
 * For example, a US area-code group could use the `state` property with the
 * values `Oregon`, `Washington`, and `California`.
 */
export type PropertyQuizGroupSource = {
  /** Identifies this as a GeoJSON property-based group. */
  type: "property";

  /** GeoJSON property used to determine feature membership. */
  property: string;

  /** Property values whose geographic features belong to the group. */
  values: string[];
};

/**
 * Identifies a group created by manually selecting geographic features.
 */
export type FeatureQuizGroupSource = {
  /** Identifies this as a manually selected feature group. */
  type: "features";

  /** Promoted MapLibre feature IDs belonging to the group. */
  featureIds: string[];
};

/**
 * Describes how the geographic features belonging to a quiz group are
 * selected.
 */
export type QuizGroupSource =
  PropertyQuizGroupSource | FeatureQuizGroupSource;

/**
 * Represents a user-created quiz group persisted for later use.
 */
export type SavedQuizGroup = {
  /** Stable unique identifier for the saved group. */
  id: string;

  /** User-facing name assigned to the group. */
  name: string;

  /** Selection definition used to resolve the group's features and answers. */
  source: QuizGroupSource;
};

/**
 * Describes the group currently applied to a quiz.
 *
 * `full` represents the complete unfiltered quiz. Other values use the same
 * selection definitions supported by saved groups.
 */
export type ActiveQuizGroup =
  | {
      /** Uses every geographic feature and question in the quiz. */
      type: "full";
    }
  | QuizGroupSource;

/**
 * Represents the concrete feature and answer subset produced after resolving
 * an active quiz group against the map's GeoJSON data.
 *
 * The map and quiz engine both consume this result so they always operate on
 * the same subset.
 */
export type ResolvedQuizGroup = {
  /** Feature IDs that should remain visible and interactive. */
  featureIds: Set<string>;

  /** Quiz answer values that should be included in the question queue. */
  answers: Set<string>;
};

/**
 * Defines one GeoJSON property that can be used to create property-based
 * quiz groups.
 */
export type QuizGroupingProperty = {
  /** GeoJSON property used to determine group membership. */
  property: string;

  /** User-facing name of the grouping dimension. */
  label: string;

  /** Shape of the grouping value stored in the GeoJSON. */
  valueType: "string" | "string-array";

  /**
   * Optional mapping from raw GeoJSON values to user-facing display names.
   *
   * When no mapping exists for a value, the raw GeoJSON value is displayed.
   */
  valueLabels?: Record<string, string>;
};

/**
 * Defines the grouping capabilities available to an individual quiz.
 */
export type QuizGroupingConfig = {
  /** GeoJSON properties that may be used to construct property-based groups. */
  properties: QuizGroupingProperty[];
};
