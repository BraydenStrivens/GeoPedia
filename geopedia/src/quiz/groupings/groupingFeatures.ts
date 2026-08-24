/**
 * Provides utilities for reading grouping and answer information from
 * GeoJSON features.
 *
 * These helpers isolate the grouping system from differences between
 * single-string and string-array GeoJSON properties.
 */

import type { Feature, GeoJsonProperties, Geometry } from "geojson";

import type { QuizGroupingProperty } from "./types";

/**
 * GeoJSON feature shape used by the quiz-grouping system.
 */
export type GroupableFeature = Feature<Geometry, GeoJsonProperties>;

/**
 * Returns the grouping values represented by a GeoJSON feature.
 *
 * The configured `valueType` determines whether the property is expected to
 * contain one string or an array of strings. Invalid or missing values return
 * an empty array.
 *
 * @param feature - Geographic feature containing the grouping property.
 * @param groupingProperty - Configuration describing the property to read.
 * @returns Normalized array of raw grouping values.
 */
export function getFeatureGroupingValues(
  feature: GroupableFeature,
  groupingProperty: QuizGroupingProperty,
): string[] {
  const rawValue = feature.properties?.[groupingProperty.property];

  if (groupingProperty.valueType === "string") {
    return typeof rawValue === "string" ? [rawValue] : [];
  }

  if (
    Array.isArray(rawValue) &&
    rawValue.every((value) => typeof value === "string")
  ) {
    return rawValue;
  }

  return [];
}

/**
 * Returns the quiz answers represented by a geographic feature.
 *
 * A quiz answer property can contain either one answer string or multiple
 * answer strings depending on the quiz's `answerType`.
 *
 * @param feature - Geographic feature containing quiz-answer data.
 * @param answerProperty - GeoJSON property containing quiz answers.
 * @returns Normalized array of answers represented by the feature.
 */
export function getFeatureQuizAnswers(
  feature: GroupableFeature,
  answerProperty: string,
): string[] {
  const rawValue = feature.properties?.[answerProperty];

  if (typeof rawValue === "string") {
    return [rawValue];
  }

  if (
    Array.isArray(rawValue) &&
    rawValue.every((value) => typeof value === "string")
  ) {
    return rawValue;
  }

  return [];
}

/**
 * Returns the stable ID used to identify a geographic feature.
 *
 * GeoPedia normally identifies features through the GeoJSON property supplied
 * to MapLibre's `promoteId`. A native GeoJSON feature ID is used as a fallback.
 *
 * @param feature - Geographic feature whose ID should be resolved.
 * @param promoteId - Optional GeoJSON property used by MapLibre as feature.id.
 * @returns Stable feature ID, or null when the feature has no usable ID.
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
