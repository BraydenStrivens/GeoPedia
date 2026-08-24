/**
 * Discovers the available values for a configured property-based quiz group.
 *
 * Options come directly from the quiz's GeoJSON dataset so the Groups UI only
 * displays values that actually occur in the map data.
 */

import type {
  FeatureCollection,
  GeoJsonProperties,
  Geometry,
} from "geojson";

import { getFeatureGroupingValues } from "@/quiz/groupings/groupingFeatures";
import type { QuizGroupingProperty } from "@/quiz/groupings/types";

/**
 * Represents one selectable value displayed by the Property Groups UI.
 */
export type QuizGroupingOption = {
  /** Raw GeoJSON value used for matching and persistence. */
  value: string;

  /** User-facing text displayed beside the checkbox. */
  label: string;
};

/**
 * Discovers all unique values available for one configured grouping property.
 *
 * Raw GeoJSON values remain unchanged for matching and persistence.
 * `valueLabels` affects presentation only.
 *
 * @param featureCollection - Complete GeoJSON dataset used by the quiz.
 * @param groupingProperty - Configured property used to create groups.
 * @returns Alphabetically sorted selectable grouping options.
 */
export function getGroupingOptions(
  featureCollection: FeatureCollection<Geometry, GeoJsonProperties>,
  groupingProperty: QuizGroupingProperty,
): QuizGroupingOption[] {
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
    .sort((a, b) => a.label.localeCompare(b.label));
}
