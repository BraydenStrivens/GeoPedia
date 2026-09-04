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

import { TownQuizGuessResult } from "@/quiz/hooks/useTownQuiz";
import type { TownQuizTown } from "@/types/quiz";
import type { TownQuizMode } from "@/types/townQuizSettings";

/** GeoJSON source containing towns from the currently active quiz group. */
const TOWN_QUIZ_LABEL_SOURCE_ID = "town-quiz-labels-source";

/** Symbol layer displaying GeoPedia-controlled town labels. */
const TOWN_QUIZ_LABEL_LAYER_ID = "town-quiz-labels";

/** Circle layer marking the exact coordinate of every displayed quiz town. */
export const TOWN_QUIZ_MARKER_LAYER_ID = "town-quiz-markers";

const CORRECT_TOWN_COLOR = "#16a34a";

const NORMAL_TOWN_TEXT_COLOR = "#141414";

const NORMAL_TOWN_TEXT_HALO_COLOR = "#ffffff";

const NORMAL_TOWN_MARKER_COLOR = "#ffffff";

const NORMAL_TOWN_MARKER_STROKE_COLOR = "#1f2937";

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

  /**
   * Object containing data about the last question and the user's answer
   * or `undefined` if no previous question has been answered.
   */
  lastResult: TownQuizGuessResult | undefined;
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
        // name: town.name,

        /**
         * Render-ready quiz label.
         *
         * This may contain a newline when English and native names differ.
         */
        label: getTownLabelText(town),

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
 * Builds the label rendered for one custom town quiz marker.
 *
 * Settlements with distinct native and English names use a two-line label with
 * the native/local form first and the English/international form second.
 *
 * Settlements whose names do not differ remain single-line labels.
 *
 * @param town - Town represented by the custom quiz layer.
 * @returns MapLibre text displayed beside the town marker.
 */
function getTownLabelText(town: TownQuizTown): string {
  if (!town.nativeName) {
    return town.name;
  }

  return [town.name, town.nativeName].join("\n");
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
        "circle-color": NORMAL_TOWN_MARKER_COLOR,
        "circle-stroke-color": NORMAL_TOWN_MARKER_STROKE_COLOR,
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
      "text-field": ["get", "label"],
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
      "text-color": NORMAL_TOWN_TEXT_COLOR,
      "text-halo-color": NORMAL_TOWN_TEXT_HALO_COLOR,
      "text-halo-width": 1.5,
      "text-halo-blur": 0.5,
    },
  });
}

/**
 * Creates a MapLibre paint expression that highlights the most recently
 * answered town while preserving the normal color for every other town.
 */
function createCorrectTownColorExpression(
  correctTownId: string | undefined,
  normalColor: string,
): maplibregl.ExpressionSpecification | string {
  if (!correctTownId) {
    return normalColor;
  }

  return [
    "case",

    ["==", ["get", "id"], correctTownId],

    CORRECT_TOWN_COLOR,

    normalColor,
  ];
}

/**
 * Applies the current town-quiz mode to one custom town layer.
 *
 * Normal mode exposes every town contained by the active quiz group. Hard mode
 * hides those hints before a question is answered, but reveals the most
 * recently answered town afterward so the player receives useful geographic
 * feedback.
 *
 * @param map - Active MapLibre map.
 * @param layerId - Custom town layer being filtered.
 * @param mode - Current town quiz difficulty mode.
 * @param correctTownId - Most recently answered town, when one exists.
 */
function applyTownLayerFilter(
  map: maplibregl.Map,
  layerId: string,
  mode: TownQuizMode,
  correctTownId: string | undefined,
): void {
  if (!map.getLayer(layerId)) {
    return;
  }

  if (mode === "normal") {
    map.setFilter(layerId, null);

    return;
  }

  if (!correctTownId) {
    /*
     * An impossible ID hides every custom quiz town while keeping the layer
     * itself loaded and ready for immediate result feedback.
     */
    map.setFilter(layerId, ["==", ["get", "id"], "__no-town__"]);

    return;
  }

  /* Hard mode reveals only the correct town from the most recent answer. */
  map.setFilter(layerId, ["==", ["get", "id"], correctTownId]);
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
  lastResult,
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

    const visibility = mode === "normal" ? "visible" : "visible"; // -------

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

    const correctTownId = lastResult?.town.id;

    /*
     * Normal mode displays the complete active town set. Hard mode displays only
     * the most recently answered town.
     */
    applyTownLayerFilter(
      map,
      TOWN_QUIZ_MARKER_LAYER_ID,
      mode,
      correctTownId,
    );

    applyTownLayerFilter(
      map,
      TOWN_QUIZ_LABEL_LAYER_ID,
      mode,
      correctTownId,
    );

    /*
     * Highlight the most recently answered town in both Normal and Hard modes.
     */
    map.setPaintProperty(
      TOWN_QUIZ_MARKER_LAYER_ID,
      "circle-color",
      createCorrectTownColorExpression(
        correctTownId,
        NORMAL_TOWN_MARKER_COLOR,
      ),
    );

    map.setPaintProperty(
      TOWN_QUIZ_MARKER_LAYER_ID,
      "circle-stroke-color",
      createCorrectTownColorExpression(
        correctTownId,
        NORMAL_TOWN_MARKER_STROKE_COLOR,
      ),
    );

    map.setPaintProperty(
      TOWN_QUIZ_LABEL_LAYER_ID,
      "text-color",
      createCorrectTownColorExpression(
        correctTownId,
        NORMAL_TOWN_TEXT_COLOR,
      ),
    );
  }, [isMapReady, mapRef, mode, lastResult]);
}
