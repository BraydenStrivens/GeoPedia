/**
 * Renders the most recent town-quiz guess result on a MapLibre map.
 *
 * Result feedback consists of:
 *
 * - A marker at the user's guessed location.
 * - A line connecting the guess to the correct town.
 *
 * The correct town itself is revealed and highlighted by `useTownQuizLabels`,
 * which owns GeoPedia's quiz-town markers and labels.
 *
 * The guess marker color reflects the score earned by the guess. A zero-percent
 * score is red, a perfect score is green, and partial scores interpolate
 * between those endpoints.
 *
 * The connecting line starts with the same score-derived color at the guessed
 * location and transitions to solid green at the correct town.
 *
 * Only the most recent result is displayed. Whenever `lastResult` changes, the
 * existing source data and colors are replaced. Clearing `lastResult` removes
 * the visible result geometry while leaving reusable sources and layers
 * attached to the map.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import type { TownQuizGuessResult } from "@/quiz/hooks/useTownQuiz";

import { TOWN_QUIZ_MARKER_LAYER_ID } from "./useTownQuizLabels";

/**
 * Parameters required to synchronize town quiz result feedback.
 */
type UseTownQuizResultParams = {
  /** MapLibre instance owned by the town-map lifecycle hook. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether the map is ready for runtime source and layer operations. */
  isMapReady: boolean;

  /** Most recent answered-town result, or `undefined` when none is visible. */
  lastResult: TownQuizGuessResult | undefined;
};

/** GeoJSON source containing the line from the guess to the correct town. */
const RESULT_LINE_SOURCE_ID = "town-quiz-result-line-source";

/** MapLibre layer displaying the result line. */
const RESULT_LINE_LAYER_ID = "town-quiz-result-line";

/** GeoJSON source containing the user's guessed location. */
const GUESS_MARKER_SOURCE_ID = "town-quiz-guess-marker-source";

/** MapLibre layer displaying the user's guessed location. */
const GUESS_MARKER_LAYER_ID = "town-quiz-guess-marker";

/** Color representing a completely incorrect guess. */
const INCORRECT_COLOR = {
  red: 220,
  green: 38,
  blue: 38,
};

/** Color representing a perfect guess and the correct town. */
const CORRECT_COLOR = {
  red: 22,
  green: 163,
  blue: 74,
};

/**
 * Clamps a normalized score to the valid range.
 */
function clampScore(score: number): number {
  return Math.min(Math.max(score, 0), 1);
}

/**
 * Converts a normalized quiz score into a color between red and green.
 *
 * @param score - Normalized quiz score from 0 to 1.
 * @returns CSS RGB color string.
 */
function getScoreColor(score: number): string {
  const normalizedScore = clampScore(score);

  const red = Math.round(
    INCORRECT_COLOR.red +
      (CORRECT_COLOR.red - INCORRECT_COLOR.red) * normalizedScore,
  );

  const green = Math.round(
    INCORRECT_COLOR.green +
      (CORRECT_COLOR.green - INCORRECT_COLOR.green) * normalizedScore,
  );

  const blue = Math.round(
    INCORRECT_COLOR.blue +
      (CORRECT_COLOR.blue - INCORRECT_COLOR.blue) * normalizedScore,
  );

  return `rgb(${red}, ${green}, ${blue})`;
}

/**
 * Returns the fixed color representing the correct town.
 */
function getCorrectColor(): string {
  return `rgb(${CORRECT_COLOR.red}, ${CORRECT_COLOR.green}, ${CORRECT_COLOR.blue})`;
}

/**
 * Creates empty GeoJSON suitable for the result-line source.
 */
function createEmptyLineData(): GeoJSON.FeatureCollection<GeoJSON.LineString> {
  return {
    type: "FeatureCollection",
    features: [],
  };
}

/**
 * Creates empty GeoJSON suitable for the guess-marker source.
 */
function createEmptyPointData(): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return {
    type: "FeatureCollection",
    features: [],
  };
}

/**
 * Creates the line connecting the user's guess to the correct town.
 *
 * @param result - Most recent town quiz result.
 * @returns One-feature line collection.
 */
function createResultLineData(
  result: TownQuizGuessResult,
): GeoJSON.FeatureCollection<GeoJSON.LineString> {
  return {
    type: "FeatureCollection",

    features: [
      {
        type: "Feature",
        properties: {},

        geometry: {
          type: "LineString",

          coordinates: [
            [result.guess.longitude, result.guess.latitude],
            [result.town.longitude, result.town.latitude],
          ],
        },
      },
    ],
  };
}

/**
 * Creates the point representing the user's guessed location.
 *
 * @param result - Most recent town quiz result.
 * @returns One-feature point collection.
 */
function createGuessMarkerData(
  result: TownQuizGuessResult,
): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return {
    type: "FeatureCollection",

    features: [
      {
        type: "Feature",
        properties: {},

        geometry: {
          type: "Point",

          coordinates: [
            result.guess.longitude,
            result.guess.latitude,
          ],
        },
      },
    ],
  };
}

/**
 * Returns a GeoJSON source with its MapLibre-specific source type.
 *
 * @param map - Map containing the source.
 * @param sourceId - MapLibre source identifier.
 */
function getGeoJsonSource(
  map: maplibregl.Map,
  sourceId: string,
): maplibregl.GeoJSONSource | null {
  const source = map.getSource(sourceId);

  if (!source) {
    return null;
  }

  return source as maplibregl.GeoJSONSource;
}

/**
 * Creates the result sources and layers when they do not already exist.
 *
 * The result line uses `lineMetrics: true`, which MapLibre requires for
 * `line-gradient`.
 *
 * When the quiz-town marker layer already exists, the result line is inserted
 * beneath it so the correct-town marker remains visually above the line.
 *
 * @param map - Active town quiz map.
 */
function ensureResultLayers(map: maplibregl.Map): void {
  if (!map.getSource(RESULT_LINE_SOURCE_ID)) {
    map.addSource(RESULT_LINE_SOURCE_ID, {
      type: "geojson",
      data: createEmptyLineData(),
      lineMetrics: true,
    });
  }

  if (!map.getLayer(RESULT_LINE_LAYER_ID)) {
    const resultLineLayer: maplibregl.LineLayerSpecification = {
      id: RESULT_LINE_LAYER_ID,

      type: "line",

      source: RESULT_LINE_SOURCE_ID,

      paint: {
        "line-width": 4,
        "line-opacity": 0.9,

        "line-gradient": [
          "interpolate",
          ["linear"],
          ["line-progress"],
          0,
          getScoreColor(0),
          1,
          getCorrectColor(),
        ],
      },
    };

    const beforeLayerId = map.getLayer(TOWN_QUIZ_MARKER_LAYER_ID)
      ? TOWN_QUIZ_MARKER_LAYER_ID
      : undefined;

    map.addLayer(resultLineLayer, beforeLayerId);
  }

  if (!map.getSource(GUESS_MARKER_SOURCE_ID)) {
    map.addSource(GUESS_MARKER_SOURCE_ID, {
      type: "geojson",
      data: createEmptyPointData(),
    });
  }

  if (!map.getLayer(GUESS_MARKER_LAYER_ID)) {
    map.addLayer({
      id: GUESS_MARKER_LAYER_ID,

      type: "circle",

      source: GUESS_MARKER_SOURCE_ID,

      paint: {
        "circle-radius": 5,
        "circle-color": getScoreColor(0),
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });
  }
}

/**
 * Clears visible result geometry while leaving reusable sources and layers
 * attached to the map.
 *
 * @param map - Active town quiz map.
 */
function clearResult(map: maplibregl.Map): void {
  getGeoJsonSource(map, RESULT_LINE_SOURCE_ID)?.setData(
    createEmptyLineData(),
  );

  getGeoJsonSource(map, GUESS_MARKER_SOURCE_ID)?.setData(
    createEmptyPointData(),
  );
}

/**
 * Displays the latest result geometry and score-aware colors.
 *
 * @param map - Active town quiz map.
 * @param result - Most recent town quiz result.
 */
function showResult(
  map: maplibregl.Map,
  result: TownQuizGuessResult,
): void {
  const guessColor = getScoreColor(result.score);

  getGeoJsonSource(map, RESULT_LINE_SOURCE_ID)?.setData(
    createResultLineData(result),
  );

  getGeoJsonSource(map, GUESS_MARKER_SOURCE_ID)?.setData(
    createGuessMarkerData(result),
  );

  map.setPaintProperty(
    GUESS_MARKER_LAYER_ID,
    "circle-color",
    guessColor,
  );

  map.setPaintProperty(RESULT_LINE_LAYER_ID, "line-gradient", [
    "interpolate",
    ["linear"],
    ["line-progress"],
    0,
    guessColor,
    1,
    getCorrectColor(),
  ]);
}

/**
 * Synchronizes the latest town quiz result with MapLibre.
 *
 * A new answer immediately replaces the previous result. Skip leaves
 * `lastResult` unchanged, so the previous visualization remains visible.
 * Stopping or restarting the quiz clears `lastResult`, which removes the
 * visualization.
 */
export function useTownQuizResult({
  mapRef,
  isMapReady,
  lastResult,
}: UseTownQuizResultParams): void {
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    ensureResultLayers(map);

    if (!lastResult) {
      clearResult(map);

      return;
    }

    showResult(map, lastResult);
  }, [mapRef, isMapReady, lastResult]);
}
