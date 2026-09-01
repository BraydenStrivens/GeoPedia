/**
 * Provides utilities for reading grouping, quiz-answer, and stable identity
 * information from GeoJSON features.
 *
 * These helpers isolate the quiz-grouping system from differences in GeoJSON
 * property representation, including:
 *
 * - Single string grouping values.
 * - Arrays of grouping values.
 * - Single quiz answers.
 * - Multiple quiz answers.
 * - Promoted feature IDs.
 * - Native GeoJSON feature IDs.
 */

import type { Feature, GeoJsonProperties, Geometry } from "geojson";

import type { QuizGroupingProperty } from "@/quiz/groupings/feature/types";

/**
 * GeoJSON feature shape consumed by the quiz-grouping system.
 */
export type GroupableFeature = Feature<Geometry, GeoJsonProperties>;

/**
 * Determines whether an unknown GeoJSON value is an array containing only
 * strings.
 *
 * @param value - Unknown GeoJSON property value.
 * @returns Whether the value is a string array.
 */
function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string")
  );
}

/**
 * Returns the grouping values represented by a GeoJSON feature.
 *
 * The grouping configuration declares whether the property should contain one
 * string or an array of strings. Missing values and values that do not match
 * the configured representation are treated as unavailable and return an
 * empty array.
 *
 * @param feature - Geographic feature containing the grouping property.
 * @param groupingProperty - Configuration describing the property to read.
 * @returns Normalized raw grouping values represented by the feature.
 */
export function getFeatureGroupingValues(
  feature: GroupableFeature,
  groupingProperty: QuizGroupingProperty,
): string[] {
  const rawValue = feature.properties?.[groupingProperty.property];

  if (groupingProperty.valueType === "string") {
    return typeof rawValue === "string" ? [rawValue] : [];
  }

  if (isStringArray(rawValue)) {
    return rawValue;
  }

  return [];
}

/**
 * Returns the quiz answers represented by a geographic feature.
 *
 * GeoPedia supports answer properties containing either one answer string or
 * an array of answer strings. This helper normalizes both forms to a string
 * array so group resolution does not need to distinguish between them.
 *
 * Missing or invalid answer values return an empty array.
 *
 * @param feature - Geographic feature containing quiz-answer data.
 * @param answerProperty - GeoJSON property containing the quiz answer or answers.
 * @returns Normalized answers represented by the feature.
 */
export function getFeatureQuizAnswers(
  feature: GroupableFeature,
  answerProperty: string,
): string[] {
  const rawValue = feature.properties?.[answerProperty];

  if (typeof rawValue === "string") {
    return [rawValue];
  }

  if (isStringArray(rawValue)) {
    return rawValue;
  }

  return [];
}

/**
 * Returns the stable ID used by GeoPedia to identify a geographic feature.
 *
 * The property configured as MapLibre's `promoteId` is preferred because it
 * provides consistent identity between React-side grouping logic and MapLibre.
 *
 * When no usable promoted value exists, the feature's native GeoJSON `id` is
 * used as a fallback.
 *
 * String and numeric IDs are normalized to strings so grouping state uses one
 * consistent ID representation.
 *
 * @param feature - Geographic feature whose stable ID should be resolved.
 * @param promoteId - Optional GeoJSON property promoted by MapLibre to feature.id.
 * @returns Stable string feature ID, or `null` when no usable ID exists.
 */
export function getGroupableFeatureId(
  feature: GroupableFeature,
  promoteId?: string,
): string | null {
  if (promoteId) {
    const promotedValue = feature.properties?.[promoteId];

    if (
      typeof promotedValue === "string" ||
      typeof promotedValue === "number"
    ) {
      return String(promotedValue);
    }
  }

  if (feature.id !== undefined && feature.id !== null) {
    return String(feature.id);
  }

  return null;
}
