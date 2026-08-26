/**
 * Discovers the selectable values available for a configured property-based
 * quiz group.
 *
 * Options are derived directly from the quiz's GeoJSON dataset so the Property
 * Groups UI only displays values that actually occur in the map data.
 *
 * Raw GeoJSON values are preserved for matching and persistence. Optional
 * `valueLabels` affect presentation only.
 */

import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/hooks/useQuizGroupingData";
import type { QuizGroupingProperty } from "@/quiz/groupings/types";
import { getFeatureGroupingValues } from "@/quiz/groupings/utils/groupingFeatures";

/**
 * Represents one selectable property value displayed by the Property Groups
 * interface.
 */
export type QuizGroupingOption = {
  /** Raw GeoJSON value used for matching and saved-group persistence. */
  value: string;

  /** User-facing label displayed beside the property-group checkbox. */
  label: string;
};

/**
 * Discovers every unique value available for one configured grouping property.
 *
 * Each geographic feature may contribute either one grouping value or multiple
 * grouping values depending on the property's configured `valueType`.
 *
 * Raw values remain unchanged for group resolution and persistence. When a
 * `valueLabels` mapping exists, it is used only to produce the user-facing
 * label.
 *
 * Results are sorted alphabetically by their display labels.
 *
 * @param featureCollection - Complete GeoJSON dataset used by the quiz.
 * @param groupingProperty - Configured GeoJSON property used to create groups.
 * @returns Alphabetically sorted selectable grouping options.
 */
export function getGroupingOptions(
  featureCollection: QuizGroupingFeatureCollection,
  groupingProperty: QuizGroupingProperty,
): QuizGroupingOption[] {
  /** Unique raw values discovered across the complete GeoJSON dataset. */
  const uniqueValues = new Set<string>();

  for (const feature of featureCollection.features) {
    const featureValues = getFeatureGroupingValues(
      feature,
      groupingProperty,
    );

    for (const value of featureValues) {
      uniqueValues.add(value);
    }
  }

  return Array.from(uniqueValues)
    .map((value) => ({
      value,

      label: groupingProperty.valueLabels?.[value] ?? value,
    }))
    .sort((firstOption, secondOption) =>
      firstOption.label.localeCompare(secondOption.label),
    );
}
