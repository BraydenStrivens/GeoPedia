/**
 * Resolves an active quiz group into the concrete geographic features and
 * quiz answers belonging to that group.
 *
 * The resolved result is shared by both the map and quiz engine so the
 * visible/selectable geographic features can never become disconnected from
 * the questions being asked.
 */

import type {
  FeatureCollection,
  GeoJsonProperties,
  Geometry,
} from "geojson";

import type { MapConfig } from "@/maps/types";
import {
  getFeatureGroupingValues,
  getFeatureQuizAnswers,
  getGroupableFeatureId,
} from "@/quiz/groupings/groupingFeatures";
import type {
  ActiveQuizGroup,
  ResolvedQuizGroup,
} from "@/quiz/groupings/types";
import type { Quiz } from "@/types/quiz";

/**
 * Determines whether a feature belongs to a property-based quiz group.
 *
 * A feature matches when at least one of its configured grouping values
 * appears among the values selected by the user.
 *
 * @param featureValues - Grouping values represented by the feature.
 * @param selectedValues - Grouping values selected by the user.
 * @returns Whether the feature belongs to the selected property group.
 */
function hasMatchingGroupingValue(
  featureValues: string[],
  selectedValues: string[],
): boolean {
  return featureValues.some((featureValue) =>
    selectedValues.includes(featureValue),
  );
}

/**
 * Resolves an active quiz group against the quiz's complete GeoJSON dataset.
 *
 * `full` includes every feature and every answer.
 *
 * Property groups include features whose configured GeoJSON grouping property
 * overlaps with one of the selected values.
 *
 * Manual groups include only features whose stable IDs were explicitly
 * selected by the user.
 *
 * @param featureCollection - Complete GeoJSON dataset used by the quiz map.
 * @param quiz - Quiz whose answers should be resolved.
 * @param mapConfig - Map configuration providing stable feature identity.
 * @param activeGroup - Group currently applied to the quiz.
 * @returns Feature IDs and quiz answers belonging to the active group.
 */
export function resolveQuizGroup(
  featureCollection: FeatureCollection<Geometry, GeoJsonProperties>,
  quiz: Quiz,
  mapConfig: MapConfig,
  activeGroup: ActiveQuizGroup,
): ResolvedQuizGroup {
  const featureIds = new Set<string>();
  const answers = new Set<string>();

  /*
   * Property-based groups must correspond to one of the grouping properties
   * explicitly supported by this quiz.
   */
  const groupingProperty =
    activeGroup.type === "property"
      ? quiz.grouping?.properties.find(
          (property) => property.property === activeGroup.property,
        )
      : undefined;

  /*
   * An invalid property-group definition should resolve to an empty group
   * instead of silently treating arbitrary GeoJSON properties as supported
   * grouping dimensions.
   */
  if (activeGroup.type === "property" && !groupingProperty) {
    return {
      featureIds,
      answers,
    };
  }

  const manuallySelectedIds =
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

    if (activeGroup.type === "property" && groupingProperty) {
      const featureValues = getFeatureGroupingValues(
        feature,
        groupingProperty,
      );

      belongsToGroup = hasMatchingGroupingValue(
        featureValues,
        activeGroup.values,
      );
    }

    if (activeGroup.type === "features") {
      belongsToGroup = manuallySelectedIds?.has(featureId) ?? false;
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
