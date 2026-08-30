/**
 * Creates and manages MapLibre markers used by Show Answers mode.
 *
 * Show Answers uses HTML markers rather than a MapLibre symbol layer so
 * GeoPedia can create exactly one styled label per geographic feature,
 * combine multi-answer values into a readable label, and synchronize label
 * appearance with feature hover state.
 *
 * Marker positioning, density limiting, HTML styling, and answer formatting
 * are delegated to focused helper modules.
 */

import type {
  Map as MapLibreMap,
  MapGeoJSONFeature,
} from "maplibre-gl";
import * as maplibregl from "maplibre-gl";

import {
  getFeatureAnswers,
  getFeatureDisplayLabel,
} from "@/maps/interactions/featureAnswers";
import type { AnswerLabelConfig } from "@/maps/types";
import type { Quiz } from "@/types/quiz";

import { getAnswerLabelAnchor } from "../labels/answerLabelAnchors";
import { limitAnswerLabelFeatures } from "../labels/answerLabelDensity";
import { createAnswerLabelElement } from "../labels/answerLabelElements";
import type { AnswerLabelMarkers } from "../labels/answerLabelTypes";

/**
 * Removes every currently rendered Show Answers marker from the map and
 * clears the marker collection.
 *
 * @param labelMarkers - Collection of currently rendered answer markers.
 */
export function clearAnswerLabels(
  labelMarkers: AnswerLabelMarkers,
): void {
  for (const { marker } of labelMarkers.values()) {
    marker.remove();
  }

  labelMarkers.clear();
}

/**
 * Creates the user-facing Show Answers text for a geographic feature.
 *
 * Quiz display values are preferred when available. Multi-answer features
 * combine their answers using ` / `.
 *
 * @param feature - Geographic feature whose answer should be displayed.
 * @param quiz - Quiz definition used to interpret the answer property.
 * @returns User-facing answer label.
 */
function getAnswerLabelText(
  feature: MapGeoJSONFeature,
  quiz: Quiz,
): string {
  const featureValue = feature.properties?.[quiz.answerProperty];

  const featureAnswers = getFeatureAnswers(featureValue);

  return getFeatureDisplayLabel(featureAnswers, quiz);
}

/**
 * Returns the unique visible geographic features currently rendered by
 * GeoPedia's feature layer.
 *
 * MapLibre may return the same logical feature multiple times. Features are
 * deduplicated using their promoted feature ID so each geography receives at
 * most one Show Answers marker.
 *
 * @param map - MapLibre map containing GeoPedia's geographic feature layer.
 * @returns Unique visible features keyed by promoted feature ID.
 */
function getUniqueVisibleFeatures(
  map: MapLibreMap,
): Array<[string, MapGeoJSONFeature]> {
  const renderedFeatures = map.queryRenderedFeatures({
    layers: ["features-fill"],
  });

  const uniqueFeatures = new globalThis.Map<
    string,
    MapGeoJSONFeature
  >();

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

  return Array.from(uniqueFeatures.entries());
}

/**
 * Rebuilds Show Answers labels for geographic features currently visible in
 * the map.
 *
 * Visible features are deduplicated, optionally limited according to the
 * map's density configuration, converted into user-facing answer text, and
 * positioned using safe geographic anchors.
 *
 * Invalid geometry suppresses only the affected feature's label rather than
 * interrupting Show Answers for the entire map.
 *
 * @param map - MapLibre map receiving the answer markers.
 * @param quiz - Quiz whose answers should be displayed.
 * @param labelMarkers - Collection tracking currently rendered markers.
 * @param answerLabelConfig - Optional density configuration for large maps.
 * @param initialZoom - Map's initial zoom level used by density calculations.
 */
export function updateAnswerLabels(
  map: MapLibreMap,
  quiz: Quiz,
  labelMarkers: AnswerLabelMarkers,
  answerLabelConfig?: AnswerLabelConfig,
  initialZoom?: number,
): void {
  clearAnswerLabels(labelMarkers);

  const visibleFeatures = getUniqueVisibleFeatures(map);

  const featuresToLabel = limitAnswerLabelFeatures(
    map,
    visibleFeatures,
    answerLabelConfig,
    initialZoom,
  );

  for (const [featureId, feature] of featuresToLabel) {
    const label = getAnswerLabelText(feature, quiz);

    if (!label) {
      continue;
    }

    const anchor = getAnswerLabelAnchor(feature);

    /*
     * Invalid geometry should suppress only this feature's label rather than
     * breaking Show Answers for the rest of the map.
     */
    if (!anchor) {
      continue;
    }

    const [longitude, latitude] = anchor;

    const element = createAnswerLabelElement(label);

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
