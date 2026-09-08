/**
 * Synchronizes GeoPedia's custom town presentation for town quizzes.
 *
 * Town quizzes use one GeoJSON source containing the towns participating in
 * the active quiz. Two MapLibre layers render that source:
 *
 * - A circle layer marks each town's exact quiz coordinate.
 * - A symbol layer displays the town's name.
 *
 * In Normal mode, every active town is available to MapLibre's collision
 * system. In Hard mode, town markers and labels remain hidden until a question
 * is answered, at which point only the most recently answered town is revealed.
 *
 * Population rank controls label collision priority so more significant towns
 * are preferred when multiple labels compete for screen space. National
 * capitals receive the highest priority.
 *
 * MapTiler's built-in settlement labels are suppressed by `useTownQuizMap`
 * before this hook runs, so this hook owns only GeoPedia's custom town layers.
 */

"use client";

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import type { TownQuizGuessResult } from "@/quiz/hooks/useTownQuiz";
import type { TownQuizTown } from "@/types/quiz";
import type { TownQuizMode } from "@/types/townQuizSettings";

/** GeoJSON source containing towns from the currently active quiz group. */
const TOWN_QUIZ_SOURCE_ID = "town-quiz-labels-source";

/** Circle layer marking the exact coordinate of each displayed quiz town. */
export const TOWN_QUIZ_MARKER_LAYER_ID = "town-quiz-markers";

/**
 * Circle layer drawing the smaller center dot used to distinguish capitals.
 */
const TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID = "town-quiz-capital-markers";

/** Symbol layer displaying GeoPedia-controlled town labels. */
const TOWN_QUIZ_LABEL_LAYER_ID = "town-quiz-labels";

/**
 * Feature-state property indicating whether MapLibre successfully placed a
 * town's label after collision detection.
 */
const TOWN_LABEL_VISIBLE_STATE = "labelVisible";

/**
 * Shows a town marker only while its corresponding label has survived
 * MapLibre's collision placement.
 */
const TOWN_MARKER_OPACITY_EXPRESSION: maplibregl.ExpressionSpecification =
  [
    "case",
    ["boolean", ["feature-state", TOWN_LABEL_VISIBLE_STATE], false],
    1,
    0,
  ];

const CORRECT_TOWN_COLOR = "#16a34a";

const NORMAL_TOWN_TEXT_COLOR = "#141414";
const NORMAL_TOWN_TEXT_HALO_COLOR = "#ffffff";

const NORMAL_TOWN_MARKER_COLOR = "#ffffff";
const NORMAL_TOWN_MARKER_STROKE_COLOR = "#1f2937";

/**
 * Parameters required to synchronize town quiz markers and labels.
 */
type UseTownQuizLabelsParams = {
  /** MapLibre instance owned by the town-map lifecycle hook. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether the map is ready for runtime source and layer operations. */
  isMapReady: boolean;

  /** Towns currently participating in the quiz. */
  towns: TownQuizTown[];

  /** Current Normal/Hard town quiz display mode. */
  mode: TownQuizMode;

  /**
   * Result of the most recently answered question, or `undefined` before a
   * question has been answered.
   */
  lastResult: TownQuizGuessResult | undefined;
};

/**
 * Builds the text rendered for one custom town label.
 *
 * Towns with a distinct native name display the primary quiz name first and
 * the native name beneath it. Towns without a distinct native name remain
 * single-line labels.
 *
 * @param town - Town represented by the custom quiz layer.
 * @returns Text rendered beside the town's coordinate marker.
 */
function getTownLabelText(town: TownQuizTown): string {
  if (!town.nativeName) {
    return town.name;
  }

  return [town.name, town.nativeName].join("\n");
}

/**
 * Converts the active town set into the GeoJSON consumed by MapLibre.
 *
 * Population rank and capital status are included as feature properties so
 * MapLibre can prioritize significant towns during collision placement.
 *
 * @param towns - Towns participating in the active quiz.
 * @returns GeoJSON FeatureCollection containing one point per town.
 */
function createTownQuizGeoJson(towns: TownQuizTown[]) {
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
        label: getTownLabelText(town),
        population: town.population,
        populationRank: town.populationRank,
        isCapital: town.isCapital,
      },
    })),
  };
}

/**
 * Creates or updates the GeoJSON source containing the active quiz towns.
 *
 * @param map - Active town quiz map.
 * @param towns - Towns currently participating in the quiz.
 */
function synchronizeTownQuizSource(
  map: maplibregl.Map,
  towns: TownQuizTown[],
): void {
  const geoJson = createTownQuizGeoJson(towns);

  const existingSource = map.getSource(TOWN_QUIZ_SOURCE_ID);

  if (existingSource) {
    const geoJsonSource = existingSource as maplibregl.GeoJSONSource;

    geoJsonSource.setData(geoJson);

    return;
  }

  map.addSource(TOWN_QUIZ_SOURCE_ID, {
    type: "geojson",
    data: geoJson,
  });
}

/**
 * Synchronizes marker visibility with MapLibre's actual symbol placement.
 *
 * Only towns whose labels survive MapLibre's collision detection receive
 * `labelVisible` feature state. Their coordinate markers therefore disappear
 * whenever there is not enough room to display the corresponding town name.
 *
 * @param map - Active town quiz map.
 * @param townIds - IDs belonging to towns in the active quiz.
 * @param previouslyVisibleTownIds - IDs whose markers were visible during the
 * previous synchronization.
 * @returns IDs whose labels are currently rendered.
 */
function synchronizeTownMarkerVisibility(
  map: maplibregl.Map,
  townIds: ReadonlySet<string>,
  previouslyVisibleTownIds: ReadonlySet<string>,
): Set<string> {
  if (!map.getLayer(TOWN_QUIZ_LABEL_LAYER_ID)) {
    return new Set();
  }

  const renderedLabels = map.queryRenderedFeatures({
    layers: [TOWN_QUIZ_LABEL_LAYER_ID],
  });

  const visibleTownIds = new Set<string>();

  for (const feature of renderedLabels) {
    const rawId = feature.properties?.id;

    if (typeof rawId !== "string" || !townIds.has(rawId)) {
      continue;
    }

    visibleTownIds.add(rawId);
  }

  /*
   * Reveal markers whose labels have newly become visible.
   */
  for (const townId of visibleTownIds) {
    if (previouslyVisibleTownIds.has(townId)) {
      continue;
    }

    map.setFeatureState(
      {
        source: TOWN_QUIZ_SOURCE_ID,
        id: townId,
      },
      {
        [TOWN_LABEL_VISIBLE_STATE]: true,
      },
    );
  }

  /*
   * Hide markers whose labels were displaced by MapLibre's collision system.
   */
  for (const townId of previouslyVisibleTownIds) {
    if (visibleTownIds.has(townId)) {
      continue;
    }

    map.setFeatureState(
      {
        source: TOWN_QUIZ_SOURCE_ID,
        id: townId,
      },
      {
        [TOWN_LABEL_VISIBLE_STATE]: false,
      },
    );
  }

  return visibleTownIds;
}

/**
 * Creates the marker and label layers used to present quiz towns when they do
 * not already exist.
 *
 * The coordinate-marker layer is added before the text layer so labels render
 * visually above their corresponding markers.
 *
 * @param map - Active town quiz map.
 */
function ensureTownQuizLayers(map: maplibregl.Map): void {
  if (!map.getLayer(TOWN_QUIZ_MARKER_LAYER_ID)) {
    map.addLayer({
      id: TOWN_QUIZ_MARKER_LAYER_ID,

      type: "circle",

      source: TOWN_QUIZ_SOURCE_ID,

      paint: {
        /*
         * Capitals use a slightly larger version of the normal white marker. Their
         * separate center-dot layer distinguishes them without changing the palette.
         */
        "circle-radius": [
          "case",
          ["==", ["get", "isCapital"], true],
          4,
          3,
        ],

        "circle-color": NORMAL_TOWN_MARKER_COLOR,
        "circle-stroke-color": NORMAL_TOWN_MARKER_STROKE_COLOR,
        "circle-stroke-width": 1.5,

        "circle-opacity": TOWN_MARKER_OPACITY_EXPRESSION,
        "circle-stroke-opacity": TOWN_MARKER_OPACITY_EXPRESSION,
      },
    });
  }

  if (!map.getLayer(TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID)) {
    map.addLayer({
      id: TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID,

      type: "circle",

      source: TOWN_QUIZ_SOURCE_ID,

      /*
       * Only capitals receive the inner dot. The larger normal marker beneath
       * provides the surrounding white fill and dark outer outline.
       */
      filter: ["==", ["get", "isCapital"], true],

      paint: {
        "circle-radius": 2.25,
        "circle-color": NORMAL_TOWN_MARKER_STROKE_COLOR,
        "circle-opacity": TOWN_MARKER_OPACITY_EXPRESSION,
      },
    });
  }

  if (map.getLayer(TOWN_QUIZ_LABEL_LAYER_ID)) {
    return;
  }

  map.addLayer({
    id: TOWN_QUIZ_LABEL_LAYER_ID,

    type: "symbol",

    source: TOWN_QUIZ_SOURCE_ID,

    layout: {
      "text-field": ["get", "label"],
      /*
       * Capitals receive a modestly larger label while retaining the same
       * typography as ordinary towns.
       */
      "text-size": [
        "case",
        ["==", ["get", "isCapital"], true],
        16,
        14,
      ],
      "text-font": ["Noto Sans Regular"],

      /*
       * Every active town remains in the source. MapLibre's collision engine
       * decides which labels have enough room to render at the current zoom.
       */
      "text-allow-overlap": false,
      "text-ignore-placement": false,

      /*
       * National capitals receive first placement priority. Remaining towns
       * are prioritized by population rank.
       */
      "symbol-sort-key": [
        "case",
        ["==", ["get", "isCapital"], true],
        0,
        ["+", ["get", "populationRank"], 1],
      ],

      /*
       * Render the town name immediately above its exact coordinate marker.
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
 * Applies the current town quiz mode to one custom town layer.
 *
 * Normal mode displays the complete active town set. Hard mode hides every
 * town before a result exists and afterward reveals only the most recently
 * answered town.
 *
 * @param map - Active town quiz map.
 * @param layerId - Custom town layer being filtered.
 * @param mode - Current town quiz display mode.
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
     * An impossible ID hides every town while leaving the layer loaded and
     * available for immediate result feedback.
     */
    map.setFilter(layerId, ["==", ["get", "id"], "__no-town__"]);

    return;
  }

  map.setFilter(layerId, ["==", ["get", "id"], correctTownId]);
}

/**
 * Creates a MapLibre paint expression that highlights the most recently
 * answered town while preserving the normal color for all other towns.
 *
 * @param correctTownId - Most recently answered town, when one exists.
 * @param normalColor - Layer color used for every other town.
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
 * Applies quiz-mode visibility to the capital center-dot layer while retaining
 * its permanent requirement that only capital features may render.
 *
 * @param map - Active town quiz map.
 * @param mode - Current Normal/Hard town quiz display mode.
 * @param correctTownId - Most recently answered town, when one exists.
 */
function applyCapitalMarkerLayerFilter(
  map: maplibregl.Map,
  mode: TownQuizMode,
  correctTownId: string | undefined,
): void {
  if (!map.getLayer(TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID)) {
    return;
  }

  if (mode === "normal") {
    map.setFilter(TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID, [
      "==",
      ["get", "isCapital"],
      true,
    ]);

    return;
  }

  if (!correctTownId) {
    map.setFilter(TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID, [
      "all",
      ["==", ["get", "isCapital"], true],
      ["==", ["get", "id"], "__no-town__"],
    ]);

    return;
  }

  map.setFilter(TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID, [
    "all",
    ["==", ["get", "isCapital"], true],
    ["==", ["get", "id"], correctTownId],
  ]);
}

/**
 * Applies quiz mode and result feedback to the existing town layers.
 *
 * @param map - Active town quiz map.
 * @param mode - Current Normal/Hard display mode.
 * @param correctTownId - Most recently answered town, when one exists.
 */
function applyTownQuizPresentation(
  map: maplibregl.Map,
  mode: TownQuizMode,
  correctTownId: string | undefined,
): void {
  applyTownLayerFilter(
    map,
    TOWN_QUIZ_MARKER_LAYER_ID,
    mode,
    correctTownId,
  );

  applyCapitalMarkerLayerFilter(map, mode, correctTownId);

  applyTownLayerFilter(
    map,
    TOWN_QUIZ_LABEL_LAYER_ID,
    mode,
    correctTownId,
  );

  if (map.getLayer(TOWN_QUIZ_MARKER_LAYER_ID)) {
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
  }

  if (map.getLayer(TOWN_QUIZ_LABEL_LAYER_ID)) {
    map.setPaintProperty(
      TOWN_QUIZ_LABEL_LAYER_ID,
      "text-color",
      createCorrectTownColorExpression(
        correctTownId,
        NORMAL_TOWN_TEXT_COLOR,
      ),
    );
  }
}

/**
 * Synchronizes GeoPedia's custom town quiz source, layers, display mode, and
 * most recent result feedback with the active MapLibre map.
 */
export function useTownQuizLabels({
  mapRef,
  isMapReady,
  towns,
  mode,
  lastResult,
}: UseTownQuizLabelsParams): void {
  /**
   * Creates the custom town source and layers once the map is ready and keeps
   * the source synchronized with changes to the active town set.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    synchronizeTownQuizSource(map, towns);

    ensureTownQuizLayers(map);
  }, [mapRef, isMapReady, towns]);

  /**
   * Synchronizes Normal/Hard mode and most-recent-answer feedback.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    applyTownQuizPresentation(map, mode, lastResult?.town.id);
  }, [mapRef, isMapReady, mode, lastResult]);

  /**
   * Keeps coordinate markers synchronized with MapLibre's rendered town labels.
   *
   * The render event is used because label collision placement can change while
   * zooming or panning. Feature state is updated only when a town's visibility
   * actually changes, avoiding unnecessary MapLibre state updates.
   */
  useEffect(() => {
    const currentMap = mapRef.current;

    if (!currentMap || !isMapReady) {
      return;
    }

    /*
     * Capture the ready MapLibre instance so callbacks registered below do not
     * depend on the nullable React ref.
     */
    const map: maplibregl.Map = currentMap;

    const townIds = new Set(towns.map((town) => town.id));

    let visibleTownIds = new Set<string>();

    function synchronizeVisibility(): void {
      visibleTownIds = synchronizeTownMarkerVisibility(
        map,
        townIds,
        visibleTownIds,
      );
    }

    map.on("render", synchronizeVisibility);

    synchronizeVisibility();

    return () => {
      map.off("render", synchronizeVisibility);
    };
  }, [mapRef, isMapReady, towns]);
}
