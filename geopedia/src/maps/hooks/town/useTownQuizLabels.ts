/**
 * Synchronizes town-label rendering for GeoPedia town quizzes.
 *
 * Town quizzes intentionally suppress MapTiler's built-in settlement labels so
 * the quiz never exposes towns outside GeoPedia's currently active question set.
 *
 * In Normal mode, GeoPedia adds one lightweight GeoJSON source containing only
 * the towns participating in the quiz and renders those towns through a single
 * MapLibre symbol layer. MapLibre's normal collision engine decides which labels
 * fit at the current zoom level.
 *
 * In Hard mode, the custom symbol layer is hidden while the underlying source
 * remains available. This allows mode changes to occur immediately without
 * recreating the map or rebuilding the source.
 *
 * Population rank controls collision priority so more significant towns are
 * preferred when multiple labels compete for the same screen space. National
 * capitals receive the highest priority.
 */

"use client";

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import type { TownQuizMode } from "@/components/quiz/controls/town/TownQuizModeControl";
import type { TownQuizTown } from "@/types/quiz";

/** GeoJSON source containing towns from the currently active quiz group. */
const TOWN_QUIZ_LABEL_SOURCE_ID = "town-quiz-labels-source";

/** Symbol layer displaying GeoPedia-controlled town labels. */
const TOWN_QUIZ_LABEL_LAYER_ID = "town-quiz-labels";

/** Circle layer marking the exact coordinate of every displayed quiz town. */
const TOWN_QUIZ_MARKER_LAYER_ID = "town-quiz-markers";

/**
 * MapTiler place-label layers that must never be visible during a town quiz.
 *
 * Country and state labels intentionally remain untouched because they provide
 * useful geographic context without revealing town answers.
 */
const HIDDEN_BASE_TOWN_LAYER_IDS = [
  "Capital city labels",
  "City labels",
  "Town labels",
  "Place labels",
] as const;

/**
 * Parameters required to synchronize town quiz labels.
 */
type UseTownQuizLabelsParams = {
  /** MapLibre instance owned by the town map. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether the MapLibre style is ready for runtime source/layer operations. */
  isMapReady: boolean;

  /** Towns currently participating in the quiz. */
  towns: TownQuizTown[];

  /** Current Normal / Hard town quiz display mode. */
  mode: TownQuizMode;
};

/**
 * Converts active town records into the GeoJSON consumed by MapLibre.
 *
 * Population rank is copied into feature properties so `symbol-sort-key` can
 * prioritize important towns during collision placement.
 *
 * @param towns - Towns included in the active quiz.
 * @returns GeoJSON FeatureCollection containing one point per town.
 */
function createTownLabelGeoJson(towns: TownQuizTown[]) {
  return {
    type: "FeatureCollection" as const,

    features: towns.map((town) => ({
      type: "Feature" as const,

      id: town.id,

      geometry: {
        type: "Point" as const,

        coordinates: [town.longitude, town.latitude],
      },

      properties: {
        id: town.id,
        name: town.name,

        population: town.population,

        populationRank: town.populationRank,

        isCapital: town.isCapital,
      },
    })),
  };
}

/**
 * Hides settlement labels supplied by the MapTiler base style.
 *
 * These layers remain hidden regardless of whether the town quiz is currently
 * using Normal or Hard mode.
 *
 * @param map - MapLibre map whose base labels should be suppressed.
 */
function hideBaseTownLabels(map: maplibregl.Map): void {
  for (const layerId of HIDDEN_BASE_TOWN_LAYER_IDS) {
    if (!map.getLayer(layerId)) {
      continue;
    }

    map.setLayoutProperty(layerId, "visibility", "none");
  }
}

/**
 * Creates GeoPedia's town-quiz source, coordinate-marker layer, and symbol
 * layer when they do not already exist.
 *
 * Each town receives a small map marker positioned at its exact geographic
 * coordinate. The town name is rendered immediately above that marker so Normal
 * mode can teach both the place name and its precise quiz target.
 *
 * @param map - MapLibre map receiving the custom town presentation.
 * @param towns - Towns belonging to the active quiz.
 */
function ensureTownLabelLayer(
  map: maplibregl.Map,
  towns: TownQuizTown[],
): void {
  const geoJson = createTownLabelGeoJson(towns);

  const existingSource = map.getSource(TOWN_QUIZ_LABEL_SOURCE_ID);

  if (!existingSource) {
    map.addSource(TOWN_QUIZ_LABEL_SOURCE_ID, {
      type: "geojson",
      data: geoJson,
    });
  }

  /*
   * Draw the coordinate markers before the text layer so town names remain
   * visually above their corresponding markers.
   */
  if (!map.getLayer(TOWN_QUIZ_MARKER_LAYER_ID)) {
    map.addLayer({
      id: TOWN_QUIZ_MARKER_LAYER_ID,

      type: "circle",

      source: TOWN_QUIZ_LABEL_SOURCE_ID,

      paint: {
        /*
         * A small white center with a dark outline remains readable over both
         * light and dark map geography without becoming visually dominant.
         */
        "circle-radius": 3,
        "circle-color": "#ffffff",
        "circle-stroke-color": "#1f2937",
        "circle-stroke-width": 1.5,
      },
    });
  }

  if (map.getLayer(TOWN_QUIZ_LABEL_LAYER_ID)) {
    return;
  }

  map.addLayer({
    id: TOWN_QUIZ_LABEL_LAYER_ID,

    type: "symbol",

    source: TOWN_QUIZ_LABEL_SOURCE_ID,

    layout: {
      "text-field": ["get", "name"],
      "text-size": 14,
      "text-font": ["Open Sans Regular"],

      /*
       * MapLibre's collision engine chooses which town names have enough room to
       * render. Every selected town remains in the source at every zoom level.
       */
      "text-allow-overlap": false,
      "text-ignore-placement": false,

      /*
       * National capitals receive first placement priority. Remaining towns are
       * prioritized according to population rank.
       */
      "symbol-sort-key": [
        "case",

        ["==", ["get", "isCapital"], true],

        0,

        ["+", ["get", "populationRank"], 1],
      ],

      /*
       * Place the name above its exact coordinate marker rather than directly
       * over it.
       */
      "text-anchor": "bottom",
      "text-offset": [0, -0.25],
    },

    paint: {
      // "text-color": "#1f2937",
      // "text-halo-color": "rgba(255, 255, 255, 0.95)",
      "text-color": "rgba(255, 255, 255, 0.95)",
      "text-halo-color": "#242c38d7",
      "text-halo-width": 1.5,
      "text-halo-blur": 0.5,
    },
  });
}

/**
 * Updates the existing GeoJSON source when the active town set changes.
 *
 * This becomes especially important once the town Filter panel selects Top 10,
 * Top 25, custom counts, and other subsets.
 *
 * `Map#getSource` exposes MapLibre's broad `Source` type even though this source
 * was created specifically as GeoJSON. Cast it to `GeoJSONSource` after checking
 * that the source exists so TypeScript exposes the GeoJSON-specific `setData`
 * method.
 *
 * @param map - MapLibre map containing the source.
 * @param towns - Current quiz towns.
 */
function updateTownLabelSource(
  map: maplibregl.Map,
  towns: TownQuizTown[],
): void {
  const source = map.getSource(TOWN_QUIZ_LABEL_SOURCE_ID);

  if (!source) {
    return;
  }

  const geoJsonSource = source as maplibregl.GeoJSONSource;

  geoJsonSource.setData(createTownLabelGeoJson(towns));
}

/**
 * Synchronizes MapTiler settlement suppression and GeoPedia town labels.
 */
export function useTownQuizLabels({
  mapRef,
  isMapReady,
  towns,
  mode,
}: UseTownQuizLabelsParams): void {
  /**
   * Creates the custom source/layer once the MapLibre style becomes ready.
   *
   * MapTiler settlement labels are also suppressed here and remain suppressed
   * for the lifetime of the town quiz map.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    hideBaseTownLabels(map);

    ensureTownLabelLayer(map, towns);
  }, [isMapReady, mapRef, towns]);

  /**
   * Keeps the source synchronized when the active Filter selection changes.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    updateTownLabelSource(map, towns);
  }, [isMapReady, mapRef, towns]);

  /**
   * Changes custom town visibility immediately when the user switches between
   * Normal and Hard mode.
   *
   * Both labels and their exact-coordinate markers are hidden in Hard mode so no
   * town-location hints remain on the map.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    const visibility = mode === "normal" ? "visible" : "none";

    if (map.getLayer(TOWN_QUIZ_MARKER_LAYER_ID)) {
      map.setLayoutProperty(
        TOWN_QUIZ_MARKER_LAYER_ID,
        "visibility",
        visibility,
      );
    }

    if (map.getLayer(TOWN_QUIZ_LABEL_LAYER_ID)) {
      map.setLayoutProperty(
        TOWN_QUIZ_LABEL_LAYER_ID,
        "visibility",
        visibility,
      );
    }
  }, [isMapReady, mapRef, mode]);
}
