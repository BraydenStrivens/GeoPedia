/**
 * Creates and manages the labels used by Show Answers mode.
 *
 * Show Answers labels are rendered as MapLibre HTML markers rather than
 * as a MapLibre symbol layer.
 *
 * Using HTML markers gives GeoPedia several useful capabilities:
 *
 * - Exactly one label can be created for each geographic feature.
 * - Multi-answer features can display readable combined labels such as
 *   "208 / 986".
 * - Labels can use a solid rounded-rectangle appearance.
 * - Individual labels can react to the hover state of their geographic
 *   feature.
 * - Labels can be recreated as the user pans and zooms so only relevant
 *   features need DOM elements.
 */

import pointOnFeature from "@turf/point-on-feature";
import type { Feature, Geometry } from "geojson";
import type {
  Map as MapLibreMap,
  MapGeoJSONFeature,
  Marker,
} from "maplibre-gl";
import * as maplibregl from "maplibre-gl";

import type { Quiz } from "@/types/quiz";

import { AnswerLabelConfig } from "./types";

/**
 * Stores the MapLibre marker and its underlying HTML element.
 *
 * The HTML element is retained separately because Show Answers hover
 * behavior changes the marker's styling directly.
 */
export type AnswerLabelMarker = {
  marker: Marker;
  element: HTMLDivElement;
};

/**
 * Normalizes a feature's answer property into an array of strings.
 *
 * Single-answer feature:
 *
 *   "MN"
 *   -> ["MN"]
 *
 * Multi-answer feature:
 *
 *   ["208", "986"]
 *   -> ["208", "986"]
 */
function getFeatureAnswers(featureValue: unknown): string[] {
  if (typeof featureValue === "string") {
    return [featureValue];
  }

  if (
    Array.isArray(featureValue) &&
    featureValue.every((value) => typeof value === "string")
  ) {
    return featureValue;
  }

  return [];
}

/**
 * Returns the user-facing Show Answers label for one geographic feature.
 *
 * Quiz question display values are preferred so generated quiz formats such
 * as ZIP prefixes can show their intended representation.
 *
 * Examples:
 *
 *   ["207"]          -> "207"
 *   ["208", "986"]   -> "208 / 986"
 *   ["562"]          -> "562--" when the quiz defines that display value
 */
function getFeatureDisplayLabel(
  feature: MapGeoJSONFeature,
  quiz: Quiz,
): string {
  const featureValue = feature.properties?.[quiz.answerProperty];

  const answers = getFeatureAnswers(featureValue);

  return answers
    .map((answer) => {
      const question = quiz.questions.find(
        (question) => question.answer === answer,
      );

      return question?.display ?? question?.answer ?? answer;
    })
    .join(" / ");
}

/**
 * Creates the HTML element shown inside a MapLibre answer marker.
 *
 * The default appearance is a solid light rounded rectangle. Hover styling
 * is applied separately by setAnswerLabelHovered().
 */
function createLabelElement(label: string): HTMLDivElement {
  const element = document.createElement("div");

  element.textContent = label;

  element.className = [
    "pointer-events-none",
    "whitespace-nowrap",
    "rounded-md",
    "border",
    "border-gray-300",
    "bg-white",
    "px-2",
    "py-1",
    "text-xs",
    "font-semibold",
    "text-gray-900",
    "shadow-sm",
    "transition-all",
    "duration-150",
  ].join(" ");

  return element;
}

/**
 * Applies the Show Answers hover appearance to the marker belonging to the
 * currently hovered geographic feature.
 *
 * All other answer markers are returned to their normal appearance.
 */
export function setAnswerLabelHovered(
  labelMarkers: globalThis.Map<string, AnswerLabelMarker>,
  featureId: string | null,
): void {
  for (const [id, labelMarker] of labelMarkers) {
    const isHovered = id === featureId;

    labelMarker.element.classList.toggle("bg-gray-800", isHovered);

    labelMarker.element.classList.toggle("text-white", isHovered);

    labelMarker.element.classList.toggle("border-gray-800", isHovered);

    /*
     * Remove the normal light appearance while hovered so conflicting
     * Tailwind background/text classes are not active simultaneously.
     */
    labelMarker.element.classList.toggle("bg-white", !isHovered);

    labelMarker.element.classList.toggle("text-gray-900", !isHovered);

    labelMarker.element.classList.toggle("border-gray-300", !isHovered);
  }
}

/**
 * Removes every currently rendered Show Answers marker from the map and
 * empties the marker dictionary.
 */
export function clearAnswerLabels(
  labelMarkers: globalThis.Map<string, AnswerLabelMarker>,
): void {
  for (const { marker } of labelMarkers.values()) {
    marker.remove();
  }

  labelMarkers.clear();
}

/**
 * Converts a MapLibre-rendered feature into the normal GeoJSON Feature shape
 * expected by Turf.
 *
 * MapGeoJSONFeature contains additional MapLibre-specific fields such as
 * source and layer information. Turf only needs the feature's geometry and
 * properties.
 */
function toGeoJsonFeature(feature: MapGeoJSONFeature): Feature<Geometry> {
  return {
    type: "Feature",

    properties: feature.properties ?? {},

    geometry: feature.geometry,
  };
}

/**
 * Searches a GeoJSON geometry for the first valid longitude/latitude pair.
 *
 * This supports both normal coordinate-based geometries and
 * GeometryCollection.
 */
function findFirstValidCoordinate(
  geometry: Geometry,
): [number, number] | null {
  if (geometry.type === "GeometryCollection") {
    for (const childGeometry of geometry.geometries) {
      const coordinate = findFirstValidCoordinate(childGeometry);

      if (coordinate) {
        return coordinate;
      }
    }

    return null;
  }

  function searchCoordinates(
    coordinates: unknown,
  ): [number, number] | null {
    if (!Array.isArray(coordinates)) {
      return null;
    }

    if (
      coordinates.length >= 2 &&
      typeof coordinates[0] === "number" &&
      typeof coordinates[1] === "number" &&
      Number.isFinite(coordinates[0]) &&
      Number.isFinite(coordinates[1])
    ) {
      return [coordinates[0], coordinates[1]];
    }

    for (const child of coordinates) {
      const coordinate = searchCoordinates(child);

      if (coordinate) {
        return coordinate;
      }
    }

    return null;
  }

  return searchCoordinates(geometry.coordinates);
}

/**
 * Returns a safe geographic position for a Show Answers marker.
 *
 * Turf's pointOnFeature is preferred because it usually gives a useful point
 * located on the feature. Rendered MapLibre geometry can occasionally be
 * invalid or clipped, so a valid source coordinate is used as a fallback
 * instead of allowing one bad feature to crash the map.
 */
function getFeatureAnchor(
  feature: MapGeoJSONFeature,
): [number, number] | null {
  try {
    const anchor = pointOnFeature(toGeoJsonFeature(feature));

    const [longitude, latitude] = anchor.geometry.coordinates;

    if (Number.isFinite(longitude) && Number.isFinite(latitude)) {
      return [longitude, latitude];
    }
  } catch (error) {
    console.warn(
      "Could not calculate answer label position:",
      feature.id,
      error,
    );
  }

  /*
   * Turf failed, so fall back to any valid coordinate contained in the
   * feature rather than crashing Show Answers entirely.
   */
  return findFirstValidCoordinate(feature.geometry);
}

/**
 * Selects items at roughly even intervals through an array.
 *
 * This avoids simply taking the first N features returned by MapLibre, which
 * could heavily cluster the visible labels in one portion of the map.
 */
function selectEvenlyDistributedFeatures<T>(
  features: T[],
  maxCount: number,
): T[] {
  if (features.length <= maxCount) {
    return features;
  }

  const selected: T[] = [];

  const step = features.length / maxCount;

  for (let index = 0; index < maxCount; index++) {
    selected.push(features[Math.floor(index * step)]);
  }

  return selected;
}

/**
 * Rebuilds Show Answers labels for features currently visible in the map.
 *
 * Features are first deduplicated by their promoted feature ID so each
 * logical geography receives at most one answer label.
 *
 * Dense maps can optionally limit the number of labels rendered at low zoom
 * levels. Sparse maps continue rendering every visible label.
 */
export function updateAnswerLabels(
  map: MapLibreMap,
  quiz: Quiz,
  labelMarkers: globalThis.Map<string, AnswerLabelMarker>,
  answerLabelConfig?: AnswerLabelConfig,
  initialZoom?: number,
): void {
  clearAnswerLabels(labelMarkers);

  const renderedFeatures = map.queryRenderedFeatures({
    layers: ["features-fill"],
  });

  /**
   * queryRenderedFeatures may return the same logical feature more than once.
   * Store only the first occurrence of each promoted feature ID.
   */
  const uniqueFeatures = new globalThis.Map<string, MapGeoJSONFeature>();

  for (const feature of renderedFeatures) {
    if (feature.id === undefined || feature.id === null) {
      continue;
    }

    const featureId = String(feature.id);

    if (uniqueFeatures.has(featureId)) {
      continue;
    }

    uniqueFeatures.set(featureId, feature);
  }

  /**
   * Start with every unique visible feature.
   *
   * This is important: maps without an answerLabels configuration should
   * behave exactly as they did before density throttling was introduced.
   */
  let featuresToLabel = Array.from(uniqueFeatures.entries());

  /**
   * Only throttle labels when:
   *
   * 1. This map explicitly provides density configuration.
   * 2. The number of visible features exceeds its configured threshold.
   */
  if (answerLabelConfig !== undefined) {
    const densityThreshold =
      answerLabelConfig.densityThreshold ?? Infinity;

    if (featuresToLabel.length > densityThreshold) {
      const initialMaxLabels = answerLabelConfig.initialMaxLabels ?? 100;

      const labelsPerZoom = answerLabelConfig.labelsPerZoom ?? 250;

      const currentZoom = map.getZoom();

      const baseZoom = initialZoom ?? currentZoom;

      const zoomDifference = Math.max(0, currentZoom - baseZoom);

      const maxLabels = Math.max(
        1,
        Math.floor(initialMaxLabels + zoomDifference * labelsPerZoom),
      );

      featuresToLabel = selectEvenlyDistributedFeatures(
        featuresToLabel,
        maxLabels,
      );
    }
  }

  /**
   * Create exactly one marker for each selected feature.
   */
  for (const [featureId, feature] of featuresToLabel) {
    const label = getFeatureDisplayLabel(feature, quiz);

    if (!label) {
      continue;
    }

    const anchor = getFeatureAnchor(feature);

    /*
     * Invalid or unusable geometry should only suppress this individual
     * feature's label, never crash Show Answers for the entire map.
     */
    if (!anchor) {
      continue;
    }

    const [longitude, latitude] = anchor;

    const element = createLabelElement(label);

    const marker = new maplibregl.Marker({
      element,
      anchor: "center",
    })
      .setLngLat([longitude, latitude])
      .addTo(map);

    labelMarkers.set(featureId, {
      marker,
      element,
    });
  }
}
