/**
 * Renders the most recent town-quiz guess result on a MapLibre map.
 *
 * Town quiz feedback consists of three visual elements:
 *
 * - A marker at the user's guessed location.
 * - A solid-green marker at the correct town location.
 * - A line connecting the guess to the correct location.
 *
 * The guess marker color reflects the score earned by the guess. A zero-percent
 * score is red, a perfect score is green, and partial scores interpolate between
 * those endpoints.
 *
 * The connecting line starts with the same score-derived color at the guessed
 * location and transitions to solid green at the correct location.
 *
 * Only the most recent result is displayed. Whenever `lastResult` changes, the
 * existing source data and colors are replaced. When `lastResult` becomes null,
 * all result geometry is cleared.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import { useEffect } from "react";

import type { TownQuizGuessResult } from "@/quiz/hooks/useTownQuiz";

import { TOWN_QUIZ_MARKER_LAYER_ID } from "./useTownQuizLabels";

/**
 * Properties consumed by the result-rendering hook.
 */
type UseTownQuizResultOptions = {
  /** MapLibre map owned by the town quiz map. */
  mapRef: React.RefObject<maplibregl.Map | null>;

  /** Whether the map's initial style has finished loading. */
  isMapReady: boolean;

  /** Most recently answered town, or null when no result should be visible. */
  lastResult: TownQuizGuessResult | undefined;
};

/** GeoJSON source containing the connecting result line. */
const RESULT_LINE_SOURCE_ID = "town-quiz-result-line-source";

/** MapLibre layer displaying the connecting result line. */
const RESULT_LINE_LAYER_ID = "town-quiz-result-line";

/** GeoJSON source containing the guessed location. */
const GUESS_MARKER_SOURCE_ID = "town-quiz-guess-marker-source";

/** MapLibre layer displaying the guessed location. */
const GUESS_MARKER_LAYER_ID = "town-quiz-guess-marker";

/** GeoJSON source containing the correct town location. */
const TARGET_MARKER_SOURCE_ID = "town-quiz-target-marker-source";

/**
 * Color representing a completely incorrect guess.
 */
const INCORRECT_COLOR = {
  red: 220,
  green: 38,
  blue: 38,
};

/**
 * Color representing a perfect guess and the correct target location.
 */
const CORRECT_COLOR = {
  red: 22,
  green: 163,
  blue: 74,
};

/**
 * Clamps a score to the valid normalized range.
 */
function clampScore(score: number): number {
  return Math.min(Math.max(score, 0), 1);
}

/**
 * Converts a normalized quiz score into an RGB color between red and green.
 *
 * A score of 0 returns the incorrect color. A score of 1 returns the correct
 * color. Scores in between linearly interpolate each RGB channel.
 *
 * @param score - Normalized quiz score.
 * @returns CSS rgb() color string.
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
 * Returns the fixed target color.
 */
function getTargetColor(): string {
  return `rgb(${CORRECT_COLOR.red}, ${CORRECT_COLOR.green}, ${CORRECT_COLOR.blue})`;
}

/**
 * Creates empty GeoJSON suitable for a line source.
 */
function createEmptyLineData(): GeoJSON.FeatureCollection<GeoJSON.LineString> {
  return {
    type: "FeatureCollection",
    features: [],
  };
}

/**
 * Creates empty GeoJSON suitable for a point source.
 */
function createEmptyPointData(): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return {
    type: "FeatureCollection",
    features: [],
  };
}

/**
 * Creates the GeoJSON connecting one guessed location to the correct town.
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
 * Creates GeoJSON containing the user's guess.
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
 * Creates GeoJSON containing the correct town location.
 */
function createTargetMarkerData(
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

          coordinates: [result.town.longitude, result.town.latitude],
        },
      },
    ],
  };
}

/**
 * Returns a GeoJSON source with the expected MapLibre type.
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
 * Adds the result sources and layers if they do not already exist.
 *
 * The line source uses `lineMetrics: true`, which is required by MapLibre's
 * `line-gradient` paint property.
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
    map.addLayer(
      {
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
            getTargetColor(),
          ],
        },
      },
      TOWN_QUIZ_MARKER_LAYER_ID,
    );
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

  if (!map.getSource(TARGET_MARKER_SOURCE_ID)) {
    map.addSource(TARGET_MARKER_SOURCE_ID, {
      type: "geojson",

      data: createEmptyPointData(),
    });
  }
}

/**
 * Removes all visible result geometry while leaving reusable sources and layers
 * attached to the map.
 */
function clearResult(map: maplibregl.Map): void {
  getGeoJsonSource(map, RESULT_LINE_SOURCE_ID)?.setData(
    createEmptyLineData(),
  );

  getGeoJsonSource(map, GUESS_MARKER_SOURCE_ID)?.setData(
    createEmptyPointData(),
  );

  getGeoJsonSource(map, TARGET_MARKER_SOURCE_ID)?.setData(
    createEmptyPointData(),
  );
}

/**
 * Updates all result geometry and score-aware colors.
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

  getGeoJsonSource(map, TARGET_MARKER_SOURCE_ID)?.setData(
    createTargetMarkerData(result),
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
    getTargetColor(),
  ]);
}

/**
 * Synchronizes the latest town quiz result with MapLibre.
 *
 * A new answer immediately replaces the previous result. Skip does not change
 * `lastResult`, so the previous result naturally remains visible. Stop and
 * restart clear `lastResult`, causing the visualization to disappear.
 */
export function useTownQuizResult({
  mapRef,
  isMapReady,
  lastResult,
}: UseTownQuizResultOptions): void {
  useEffect(() => {
    if (!isMapReady) {
      return;
    }

    const map = mapRef.current;

    if (!map) {
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
