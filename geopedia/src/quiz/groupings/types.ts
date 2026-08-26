/**
 * Defines the shared data structures used by GeoPedia's quiz-grouping system.
 *
 * Quiz groups reduce a complete quiz to a subset of its geographic features
 * and questions.
 *
 * Groups can be defined in two ways:
 *
 * - Property groups select features using configured GeoJSON property values.
 * - Feature groups select individual geographic features by stable ID.
 *
 * Saved groups persist one of those selection definitions for later reuse.
 */

/**
 * Identifies a group created from one or more values of a configured GeoJSON
 * property.
 *
 * For example, a US area-code group could use a normalized `states` property
 * with the values `OR`, `WA`, and `CA`.
 */
export type PropertyQuizGroupSource = {
  /** Identifies this as a GeoJSON property-based group. */
  type: "property";

  /** GeoJSON property used to determine geographic feature membership. */
  property: string;

  /**
   * Raw GeoJSON property values whose matching features belong to the group.
   *
   * These values are stored exactly as they appear in the normalized dataset.
   * User-facing labels are handled separately by the grouping configuration.
   */
  values: string[];
};

/**
 * Identifies a group created by manually selecting geographic features.
 */
export type FeatureQuizGroupSource = {
  /** Identifies this as a manually selected feature group. */
  type: "features";

  /**
   * Stable geographic feature IDs belonging to the group.
   *
   * IDs are normalized to strings before being stored.
   */
  featureIds: string[];
};

/**
 * Describes how the geographic features belonging to a non-full quiz group are
 * selected.
 */
export type QuizGroupSource =
  PropertyQuizGroupSource | FeatureQuizGroupSource;

/**
 * Represents a user-created quiz group persisted for later reuse.
 */
export type SavedQuizGroup = {
  /** Stable unique identifier for the saved group. */
  id: string;

  /** User-facing name assigned to the group. */
  name: string;

  /** Optional user-facing description of the group. */
  description?: string;

  /** Selection definition used to resolve the group's features and answers. */
  source: QuizGroupSource;
};

/**
 * Describes the group currently applied to a quiz.
 *
 * `full` represents the complete unfiltered quiz. Other values reuse the same
 * property-based and feature-based selection definitions supported by saved
 * groups.
 */
export type ActiveQuizGroup =
  | {
      /** Uses every groupable geographic feature and quiz question. */
      type: "full";
    }
  | QuizGroupSource;

/**
 * Represents the concrete geographic and question subset produced after
 * resolving an active quiz group against the map's GeoJSON data.
 *
 * The map and quiz engine consume the same resolved result so visible and
 * interactive geography remains synchronized with the available questions.
 */
export type ResolvedQuizGroup = {
  /** Stable feature IDs belonging to the resolved group. */
  featureIds: ReadonlySet<string>;

  /** Distinct quiz answer values belonging to the resolved group. */
  answers: ReadonlySet<string>;
};

/**
 * Defines one GeoJSON property that can be used to create property-based quiz
 * groups.
 */
export type QuizGroupingProperty = {
  /** GeoJSON property used to determine group membership. */
  property: string;

  /** User-facing name of the grouping dimension. */
  label: string;

  /** Shape of the grouping value stored in the GeoJSON. */
  valueType: "string" | "string-array";

  /**
   * Optional mapping from raw GeoJSON values to user-facing display labels.
   *
   * Raw values remain unchanged for group matching and persistence. When no
   * mapping exists for a value, the raw value itself is displayed.
   */
  valueLabels?: Record<string, string>;
};

/**
 * Defines the property-based grouping capabilities available to an individual
 * quiz.
 *
 * Quizzes without meaningful preset grouping properties may omit grouping
 * configuration entirely.
 */
export type QuizGroupingConfig = {
  /** GeoJSON properties that may be used to construct property-based groups. */
  properties: QuizGroupingProperty[];
};
