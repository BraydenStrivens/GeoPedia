/**
 * Synchronizes GeoPedia's custom town presentation for town quizzes.
 *
 * Normal town presentation uses one GeoJSON source containing the towns
 * represented by the active question set. Coordinate-marker and label layers
 * render that source. MapLibre collision detection determines which normal
 * labels survive, and coordinate markers follow that label visibility.
 *
 * Image-based town quizzes may additionally expose an inactive Show Answers
 * presentation. Show Answers uses a separate source and layers so every
 * configured image answer can be displayed without participating in normal
 * town-label collision detection. Each answer combines a normalized image and
 * the town's normal label text into one symbol, while a separate circle layer
 * continues to mark the town's exact coordinate.
 *
 * In Normal mode, every active town is available to MapLibre's collision
 * system. In Hard mode, normal town markers and labels remain hidden until a
 * question is answered, at which point only the most recently answered town is
 * revealed. Show Answers temporarily hides those normal layers regardless of
 * mode and renders every image answer instead.
 *
 * Population rank controls normal label collision priority and Show Answers
 * draw order so more significant towns remain visually prominent when answers
 * overlap. National capitals receive the highest priority.
 *
 * MapTiler's built-in settlement labels are suppressed by `useTownQuizMap`
 * before this hook runs, so this hook owns only GeoPedia's custom town layers.
 */

"use client";

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import type { TownQuizGuessResult } from "@/quiz/hooks/useTownQuiz";
import type { TownData, TownQuizQuestion } from "@/types/quiz";
import type { TownQuizMode } from "@/types/townQuizSettings";

/** GeoJSON source containing towns from the currently active quiz group. */
const TOWN_QUIZ_SOURCE_ID = "town-quiz-labels-source";

/** GeoJSON source containing image-based Show Answers towns. */
const TOWN_QUIZ_ANSWER_SOURCE_ID = "town-quiz-answers-source";

/** Circle layer marking the exact coordinate of each displayed quiz town. */
export const TOWN_QUIZ_MARKER_LAYER_ID = "town-quiz-markers";

/** Circle layer drawing the smaller center dot used to distinguish capitals. */
const TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID = "town-quiz-capital-markers";

/** Symbol layer displaying GeoPedia-controlled town labels. */
const TOWN_QUIZ_LABEL_LAYER_ID = "town-quiz-labels";

/** Circle layer marking every coordinate displayed by Show Answers. */
const TOWN_QUIZ_ANSWER_MARKER_LAYER_ID = "town-quiz-answer-markers";

/** Capital center-dot layer used by Show Answers. */
const TOWN_QUIZ_ANSWER_CAPITAL_MARKER_LAYER_ID =
  "town-quiz-answer-capital-markers";

/** Symbol layer displaying complete image-based Show Answers labels. */
const TOWN_QUIZ_ANSWER_LABEL_LAYER_ID = "town-quiz-answer-labels";

/**
 * Feature-state property indicating whether MapLibre successfully placed a
 * normal town label after collision detection.
 */
const TOWN_LABEL_VISIBLE_STATE = "labelVisible";

/** Prefix used for MapLibre images registered for town answer prompts. */
const TOWN_QUIZ_ANSWER_IMAGE_PREFIX = "town-quiz-answer-image-";

/**
 * Maximum CSS-pixel dimensions occupied by a normalized Show Answers image.
 *
 * Source images retain their aspect ratio and are fitted inside this box
 * without cropping or stretching.
 */
const ANSWER_IMAGE_MAX_WIDTH = 160;
const ANSWER_IMAGE_MAX_HEIGHT = 100;

/**
 * Pixel ratio used when rasterizing answer images for MapLibre.
 *
 * The backing canvas is rendered at twice the displayed resolution so images
 * remain reasonably sharp on high-density displays while retaining consistent
 * CSS-pixel dimensions.
 */
const ANSWER_IMAGE_PIXEL_RATIO = 2;

/**
 * Shows a normal town marker only while its corresponding label has survived
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
 * Parameters required to synchronize town quiz markers, labels, and optional
 * image-based Show Answers presentation.
 */
type UseTownQuizLabelsParams = {
  /** MapLibre instance owned by the town-map lifecycle hook. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether the map is ready for runtime source and layer operations. */
  isMapReady: boolean;

  /** Questions currently participating in the quiz. */
  questions: TownQuizQuestion[];

  /** Current Normal/Hard town quiz display mode. */
  mode: TownQuizMode;

  /**
   * Result of the most recently answered question, or `undefined` before a
   * question has been answered.
   */
  lastResult: TownQuizGuessResult | undefined;

  /**
   * Whether the inactive image-based quiz is currently displaying its complete
   * answer presentation.
   */
  showAnswers: boolean;
};

/**
 * Image question associated with one unique Show Answers town.
 */
type TownAnswerImage = {
  town: TownData;
  imageUrl: string;
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
function getTownLabelText(town: TownData): string {
  if (!town.nativeName) {
    return town.name;
  }

  return [town.name, town.nativeName].join("\n");
}

/**
 * Returns the deterministic MapLibre image ID used by one answer town.
 *
 * @param townId - Stable canonical town ID.
 * @returns MapLibre style-image ID.
 */
function getTownAnswerImageId(townId: string): string {
  return `${TOWN_QUIZ_ANSWER_IMAGE_PREFIX}${townId}`;
}

/**
 * Converts the active question set into the GeoJSON consumed by the normal
 * town presentation.
 *
 * Only one feature is created per unique canonical town. This keeps MapLibre
 * feature IDs stable even if a future configured quiz contains multiple
 * questions for the same town.
 *
 * @param questions - Town questions participating in the active quiz.
 * @returns GeoJSON FeatureCollection containing one point per unique town.
 */
function createTownQuizGeoJson(questions: TownQuizQuestion[]) {
  const uniqueTowns = new Map<string, TownData>();

  for (const question of questions) {
    if (!uniqueTowns.has(question.town.id)) {
      uniqueTowns.set(question.town.id, question.town);
    }
  }

  return {
    type: "FeatureCollection" as const,

    features: Array.from(uniqueTowns.values()).map((town) => ({
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
 * Extracts the first image prompt associated with each unique town.
 *
 * Current configured image-town quizzes use one image question per town. The
 * first-image rule keeps the map source valid if a future quiz contains
 * multiple image questions for the same canonical town without affecting quiz
 * gameplay, where those questions remain distinct.
 *
 * @param questions - Questions participating in the active quiz.
 * @returns One image answer definition per unique town with an image prompt.
 */
function getTownAnswerImages(
  questions: TownQuizQuestion[],
): TownAnswerImage[] {
  const answers = new Map<string, TownAnswerImage>();

  for (const question of questions) {
    if (
      question.prompt?.type !== "image" ||
      answers.has(question.town.id)
    ) {
      continue;
    }

    answers.set(question.town.id, {
      town: question.town,
      imageUrl: question.prompt.imageUrl,
    });
  }

  return Array.from(answers.values());
}

/**
 * Converts image-based questions into the separate GeoJSON consumed by Show
 * Answers.
 *
 * Every feature carries its registered MapLibre image ID plus the same town
 * label and ranking metadata used by the normal town presentation.
 *
 * @param answers - Unique image answers participating in the active quiz.
 * @returns GeoJSON FeatureCollection containing one point per answer town.
 */
function createTownAnswerGeoJson(answers: TownAnswerImage[]) {
  return {
    type: "FeatureCollection" as const,

    features: answers.map(({ town }) => ({
      type: "Feature" as const,

      id: town.id,

      geometry: {
        type: "Point" as const,
        coordinates: [town.longitude, town.latitude],
      },

      properties: {
        id: town.id,
        label: getTownLabelText(town),
        imageId: getTownAnswerImageId(town.id),
        population: town.population,
        populationRank: town.populationRank,
        isCapital: town.isCapital,
        hasNativeName: town.nativeName !== undefined,
      },
    })),
  };
}

/**
 * Creates or updates the GeoJSON source containing the active normal quiz
 * towns.
 *
 * @param map - Active town quiz map.
 * @param questions - Town questions currently participating in the quiz.
 */
function synchronizeTownQuizSource(
  map: maplibregl.Map,
  questions: TownQuizQuestion[],
): void {
  const geoJson = createTownQuizGeoJson(questions);

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
 * Creates or updates the separate GeoJSON source used by Show Answers.
 *
 * @param map - Active town quiz map.
 * @param answers - Unique image answers participating in the active quiz.
 */
function synchronizeTownAnswerSource(
  map: maplibregl.Map,
  answers: TownAnswerImage[],
): void {
  const geoJson = createTownAnswerGeoJson(answers);

  const existingSource = map.getSource(TOWN_QUIZ_ANSWER_SOURCE_ID);

  if (existingSource) {
    const geoJsonSource = existingSource as maplibregl.GeoJSONSource;

    geoJsonSource.setData(geoJson);

    return;
  }

  map.addSource(TOWN_QUIZ_ANSWER_SOURCE_ID, {
    type: "geojson",
    data: geoJson,
  });
}

/**
 * Loads one browser image from a public URL.
 *
 * @param imageUrl - URL of the image to load.
 * @returns Loaded HTML image element.
 */
function loadBrowserImage(
  imageUrl: string,
): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();

    image.onload = () => resolve(image);

    image.onerror = () => {
      reject(
        new Error(
          `Failed to load town quiz answer image "${imageUrl}".`,
        ),
      );
    };

    image.src = imageUrl;
  });
}

/**
 * Fits an arbitrary source image inside GeoPedia's standard answer-image box.
 *
 * The image keeps its original aspect ratio and is never cropped or stretched.
 * A transparent canvas is tightly sized to the resulting fitted image so
 * portrait, landscape, and square source assets all receive consistent maximum
 * dimensions without unnecessary transparent padding.
 *
 * @param image - Loaded source image.
 * @returns ImageData suitable for registration with MapLibre.
 */
function normalizeTownAnswerImage(
  image: HTMLImageElement,
): ImageData {
  const scale = Math.min(
    ANSWER_IMAGE_MAX_WIDTH / image.naturalWidth,
    ANSWER_IMAGE_MAX_HEIGHT / image.naturalHeight,
    1,
  );

  const displayWidth = Math.max(
    1,
    Math.round(image.naturalWidth * scale),
  );

  const displayHeight = Math.max(
    1,
    Math.round(image.naturalHeight * scale),
  );

  const canvas = document.createElement("canvas");

  canvas.width = displayWidth * ANSWER_IMAGE_PIXEL_RATIO;
  canvas.height = displayHeight * ANSWER_IMAGE_PIXEL_RATIO;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error(
      "Unable to create town quiz answer image canvas.",
    );
  }

  context.drawImage(image, 0, 0, canvas.width, canvas.height);

  return context.getImageData(0, 0, canvas.width, canvas.height);
}

/**
 * Loads, normalizes, and registers every answer image required by the current
 * configured town quiz.
 *
 * Existing style images are reused so toggling Show Answers does not repeatedly
 * decode or rasterize the same assets.
 *
 * @param map - Active town quiz map.
 * @param answers - Unique image answers participating in the active quiz.
 */
async function ensureTownAnswerImages(
  map: maplibregl.Map,
  answers: TownAnswerImage[],
): Promise<void> {
  await Promise.all(
    answers.map(async ({ town, imageUrl }) => {
      const imageId = getTownAnswerImageId(town.id);

      if (map.hasImage(imageId)) {
        return;
      }

      const image = await loadBrowserImage(imageUrl);
      const normalizedImage = normalizeTownAnswerImage(image);

      /*
       * The backing bitmap is rendered at 2× resolution while MapLibre treats
       * it as a normal CSS-sized image through the supplied pixel ratio.
       */
      map.addImage(imageId, normalizedImage, {
        pixelRatio: ANSWER_IMAGE_PIXEL_RATIO,
      });
    }),
  );
}

/**
 * Synchronizes marker visibility with MapLibre's actual normal-label placement.
 *
 * Only towns whose normal labels survive collision detection receive
 * `labelVisible` feature state. Show Answers does not use this state because
 * every answer marker and label must remain visible.
 *
 * @param map - Active town quiz map.
 * @param townIds - IDs belonging to towns in the active quiz.
 * @param previouslyVisibleTownIds - IDs whose markers were visible during the
 * previous synchronization.
 * @returns IDs whose normal labels are currently rendered.
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
 * Creates the normal marker and label layers used to present quiz towns when
 * they do not already exist.
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

      "text-size": [
        "case",
        ["==", ["get", "isCapital"], true],
        16,
        14,
      ],

      "text-font": ["Noto Sans Regular"],

      "text-allow-overlap": false,
      "text-ignore-placement": false,

      "symbol-sort-key": [
        "case",
        ["==", ["get", "isCapital"], true],
        0,
        ["+", ["get", "populationRank"], 1],
      ],

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
 * Creates the separate marker and image-label layers used by Show Answers.
 *
 * Collision participation is disabled for both the icon and text portions of
 * the answer symbol. Every configured answer therefore renders simultaneously.
 * Population rank controls draw order rather than visibility.
 *
 * @param map - Active town quiz map.
 */
function ensureTownAnswerLayers(map: maplibregl.Map): void {
  if (!map.getLayer(TOWN_QUIZ_ANSWER_MARKER_LAYER_ID)) {
    map.addLayer({
      id: TOWN_QUIZ_ANSWER_MARKER_LAYER_ID,

      type: "circle",

      source: TOWN_QUIZ_ANSWER_SOURCE_ID,

      layout: {
        visibility: "none",

        /*
         * Larger sort keys render above smaller sort keys. Inverting population
         * rank therefore gives more significant towns the higher draw priority.
         */
        "circle-sort-key": [
          "-",
          1000000,
          [
            "case",
            ["==", ["get", "isCapital"], true],
            0,
            ["+", ["get", "populationRank"], 1],
          ],
        ],
      },

      paint: {
        "circle-radius": [
          "case",
          ["==", ["get", "isCapital"], true],
          4,
          3,
        ],

        "circle-color": NORMAL_TOWN_MARKER_COLOR,
        "circle-stroke-color": NORMAL_TOWN_MARKER_STROKE_COLOR,
        "circle-stroke-width": 1.5,
      },
    });
  }

  if (!map.getLayer(TOWN_QUIZ_ANSWER_CAPITAL_MARKER_LAYER_ID)) {
    map.addLayer({
      id: TOWN_QUIZ_ANSWER_CAPITAL_MARKER_LAYER_ID,

      type: "circle",

      source: TOWN_QUIZ_ANSWER_SOURCE_ID,

      filter: ["==", ["get", "isCapital"], true],

      layout: {
        visibility: "none",
      },

      paint: {
        "circle-radius": 2.25,
        "circle-color": NORMAL_TOWN_MARKER_STROKE_COLOR,
      },
    });
  }

  if (map.getLayer(TOWN_QUIZ_ANSWER_LABEL_LAYER_ID)) {
    return;
  }

  map.addLayer({
    id: TOWN_QUIZ_ANSWER_LABEL_LAYER_ID,

    type: "symbol",

    source: TOWN_QUIZ_ANSWER_SOURCE_ID,

    layout: {
      visibility: "none",

      /*
       * The answer image and town text belong to the same symbol feature so
       * population-based ordering applies to the complete visual answer.
       */
      "icon-image": ["get", "imageId"],
      "icon-anchor": "bottom",

      /*
       * Move the image above the town text. Bilingual labels require additional
       * space because their text occupies two lines.
       */
      "icon-offset": [
        "case",
        ["==", ["get", "hasNativeName"], true],
        ["literal", [0, -42]],
        ["literal", [0, -25]],
      ],

      "icon-allow-overlap": true,
      "icon-ignore-placement": true,

      "text-field": ["get", "label"],

      "text-size": [
        "case",
        ["==", ["get", "isCapital"], true],
        16,
        14,
      ],

      "text-font": ["Noto Sans Regular"],

      "text-anchor": "bottom",
      "text-offset": [0, -0.25],

      "text-allow-overlap": true,
      "text-ignore-placement": true,

      /*
       * All answers render. The sort key only controls which complete answer
       * symbol is painted above another when their screen areas overlap.
       */
      "symbol-sort-key": [
        "-",
        1000000,
        [
          "case",
          ["==", ["get", "isCapital"], true],
          0,
          ["+", ["get", "populationRank"], 1],
        ],
      ],
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
 * Applies the current town quiz mode to one normal custom town layer.
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
 * Applies quiz-mode visibility to the normal capital center-dot layer while
 * retaining its permanent requirement that only capital features may render.
 *
 * @param map - Active town quiz map.
 * @param mode - Current town quiz display mode.
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
 * Sets one MapLibre layer's visibility when that layer exists.
 *
 * @param map - Active town quiz map.
 * @param layerId - Layer whose visibility should change.
 * @param isVisible - Whether the layer should be rendered.
 */
function setLayerVisibility(
  map: maplibregl.Map,
  layerId: string,
  isVisible: boolean,
): void {
  if (!map.getLayer(layerId)) {
    return;
  }

  map.setLayoutProperty(
    layerId,
    "visibility",
    isVisible ? "visible" : "none",
  );
}

/**
 * Applies quiz mode, result feedback, and Show Answers visibility.
 *
 * Normal town layers are hidden completely while Show Answers is active.
 * Answer layers are otherwise hidden and do not alter the normal town
 * presentation.
 *
 * @param map - Active town quiz map.
 * @param mode - Current Normal/Hard display mode.
 * @param correctTownId - Most recently answered town, when one exists.
 * @param showAnswers - Whether the inactive answer presentation is enabled.
 */
function applyTownQuizPresentation(
  map: maplibregl.Map,
  mode: TownQuizMode,
  correctTownId: string | undefined,
  showAnswers: boolean,
): void {
  setLayerVisibility(map, TOWN_QUIZ_MARKER_LAYER_ID, !showAnswers);

  setLayerVisibility(
    map,
    TOWN_QUIZ_CAPITAL_MARKER_LAYER_ID,
    !showAnswers,
  );

  setLayerVisibility(map, TOWN_QUIZ_LABEL_LAYER_ID, !showAnswers);

  setLayerVisibility(
    map,
    TOWN_QUIZ_ANSWER_MARKER_LAYER_ID,
    showAnswers,
  );

  setLayerVisibility(
    map,
    TOWN_QUIZ_ANSWER_CAPITAL_MARKER_LAYER_ID,
    showAnswers,
  );

  setLayerVisibility(
    map,
    TOWN_QUIZ_ANSWER_LABEL_LAYER_ID,
    showAnswers,
  );

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
 * Synchronizes GeoPedia's normal town presentation and optional image-based
 * Show Answers presentation with the active MapLibre map.
 */
export function useTownQuizLabels({
  mapRef,
  isMapReady,
  questions,
  mode,
  lastResult,
  showAnswers,
}: UseTownQuizLabelsParams): void {
  /**
   * Creates and synchronizes the normal town source/layers plus the separate
   * image-answer source/layers once the MapLibre map is ready.
   *
   * Answer images are loaded and registered here so the Show Answers symbol
   * layer can reference them by deterministic style-image ID.
   */
  useEffect(() => {
    const currentMap = mapRef.current;

    if (!currentMap || !isMapReady) {
      return;
    }

    const map: maplibregl.Map = currentMap;

    const answers = getTownAnswerImages(questions);

    synchronizeTownQuizSource(map, questions);

    ensureTownQuizLayers(map);

    /*
     * Normal town quizzes have no image answers and therefore do not need the
     * additional Show Answers source, layers, or registered style images.
     */
    if (answers.length === 0) {
      return;
    }

    synchronizeTownAnswerSource(map, answers);

    let isCancelled = false;

    async function prepareAnswerPresentation(): Promise<void> {
      try {
        await ensureTownAnswerImages(map, answers);

        if (isCancelled) {
          return;
        }

        ensureTownAnswerLayers(map);

        /*
         * The answer layers may have been created after the presentation effect
         * already ran, so immediately synchronize their visibility with the
         * current Show Answers state.
         */
        applyTownQuizPresentation(
          map,
          mode,
          lastResult?.question.town.id,
          showAnswers,
        );
      } catch (error) {
        /*
         * A failed answer image should not break the normal town quiz map.
         * Surface the failure for development/debugging while leaving the
         * ordinary town presentation intact.
         */
        console.error(
          "Failed to prepare town quiz Show Answers images.",
          error,
        );
      }
    }

    void prepareAnswerPresentation();

    return () => {
      isCancelled = true;
    };
  }, [mapRef, isMapReady, questions, mode, lastResult, showAnswers]);

  /**
   * Synchronizes Normal/Hard mode, most-recent-answer feedback, and Show
   * Answers visibility whenever those presentation states change.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    applyTownQuizPresentation(
      map,
      mode,
      lastResult?.question.town.id,
      showAnswers,
    );
  }, [mapRef, isMapReady, mode, lastResult, showAnswers]);

  /**
   * Keeps normal coordinate markers synchronized with MapLibre's rendered town
   * labels.
   *
   * The render event is used because normal label collision placement can
   * change while zooming or panning. Show Answers uses separate layers and
   * intentionally renders every configured answer, so its markers do not
   * participate in this synchronization.
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

    const townIds = new Set(
      questions.map((question) => question.town.id),
    );

    let visibleTownIds = new Set<string>();

    function synchronizeVisibility(): void {
      /*
       * Normal layers are hidden while Show Answers is active. There is no need
       * to query their rendered placement until the ordinary presentation is
       * restored.
       */
      if (showAnswers) {
        return;
      }

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
  }, [mapRef, isMapReady, questions, showAnswers]);
}
