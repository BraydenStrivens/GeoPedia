/**
 * Resolves an active quiz group into the concrete geographic features and quiz
 * answers belonging to that group.
 *
 * The resolved result is shared by both the map and quiz engine so visible and
 * interactive geography remains synchronized with the questions being asked.
 *
 * Supported group sources:
 *
 * - Full Quiz: every groupable feature in the dataset.
 * - Property group: features whose configured grouping values overlap with the
 *   values selected by the user.
 * - Manual group: features whose stable IDs were explicitly selected.
 */

import type { MapConfig } from "@/maps/types";
import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/feature/hooks/useQuizGroupingData";
import type {
  ActiveQuizGroup,
  QuizGroupingProperty,
  ResolvedQuizGroup,
} from "@/quiz/groupings/feature/types";
import {
  getFeatureGroupingValues,
  getFeatureQuizAnswers,
  getGroupableFeatureId,
} from "@/quiz/groupings/feature/utils/groupingFeatures";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Determines whether a feature belongs to a property-based quiz group.
 *
 * A feature matches when at least one of its configured grouping values appears
 * among the values selected by the user.
 *
 * @param featureValues - Grouping values represented by the geographic feature.
 * @param selectedValues - Grouping values selected by the user.
 * @returns Whether the feature belongs to the property group.
 */
function hasMatchingGroupingValue(
  featureValues: string[],
  selectedValues: ReadonlySet<string>,
): boolean {
  return featureValues.some((featureValue) =>
    selectedValues.has(featureValue),
  );
}

/**
 * Finds the quiz grouping configuration referenced by a property-based active
 * group.
 *
 * Property groups are only allowed to use grouping dimensions explicitly
 * configured by the quiz. Unknown GeoJSON properties therefore cannot be used
 * accidentally as grouping sources.
 *
 * @param quiz - Quiz containing the supported grouping configuration.
 * @param activeGroup - Active quiz group being resolved.
 * @returns Matching grouping property, or `undefined` when none is required or
 * supported.
 */
function getActiveGroupingProperty(
  quiz: FeatureQuiz,
  activeGroup: ActiveQuizGroup,
): QuizGroupingProperty | undefined {
  if (activeGroup.type !== "property") {
    return undefined;
  }

  return quiz.grouping?.properties.find(
    (property) => property.property === activeGroup.property,
  );
}

/**
 * Resolves an active quiz group against the quiz's complete GeoJSON dataset.
 *
 * Features without a stable groupable ID are ignored because they cannot be
 * safely synchronized between React grouping state and MapLibre.
 *
 * Property groups referencing a grouping property not configured by the quiz
 * resolve to an empty result rather than silently allowing arbitrary GeoJSON
 * properties.
 *
 * @param featureCollection - Complete GeoJSON dataset used by the quiz map.
 * @param quiz - Quiz whose answers should be resolved.
 * @param mapConfig - Map configuration providing stable feature identity.
 * @param activeGroup - Group currently applied to the quiz.
 * @returns Feature IDs and quiz answers belonging to the active group.
 */
export function resolveQuizGroup(
  featureCollection: QuizGroupingFeatureCollection,
  quiz: FeatureQuiz,
  mapConfig: MapConfig,
  activeGroup: ActiveQuizGroup,
): ResolvedQuizGroup {
  /** Stable geographic feature IDs belonging to the resolved group. */
  const featureIds = new Set<string>();

  /** Distinct quiz answers represented by the resolved geographic features. */
  const answers = new Set<string>();

  /**
   * Property configuration used when resolving a property-based group.
   */
  const groupingProperty = getActiveGroupingProperty(
    quiz,
    activeGroup,
  );

  /*
   * Invalid property groups resolve to an empty result rather than treating an
   * arbitrary GeoJSON property as a supported grouping dimension.
   */
  if (activeGroup.type === "property" && !groupingProperty) {
    return {
      featureIds,
      answers,
    };
  }

  /** Property-group values normalized to a Set for repeated feature lookups. */
  const selectedPropertyValues =
    activeGroup.type === "property"
      ? new Set(activeGroup.values)
      : null;

  /** Stable feature IDs explicitly selected by a manual group. */
  const selectedFeatureIds =
    activeGroup.type === "features"
      ? new Set(activeGroup.featureIds)
      : null;

  for (const feature of featureCollection.features) {
    const featureId = getGroupableFeatureId(
      feature,
      mapConfig.promoteId,
    );

    if (!featureId) {
      continue;
    }

    let belongsToGroup = activeGroup.type === "full";

    if (
      activeGroup.type === "property" &&
      groupingProperty &&
      selectedPropertyValues
    ) {
      const featureValues = getFeatureGroupingValues(
        feature,
        groupingProperty,
      );

      belongsToGroup = hasMatchingGroupingValue(
        featureValues,
        selectedPropertyValues,
      );
    }

    if (activeGroup.type === "features" && selectedFeatureIds) {
      belongsToGroup = selectedFeatureIds.has(featureId);
    }

    if (!belongsToGroup) {
      continue;
    }

    featureIds.add(featureId);

    const featureAnswers = getFeatureQuizAnswers(
      feature,
      quiz.answerProperty,
    );

    for (const answer of featureAnswers) {
      answers.add(answer);
    }
  }

  return {
    featureIds,
    answers,
  };
}
