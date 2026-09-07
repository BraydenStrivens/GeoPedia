/**
 * Owns interaction and quiz-availability behavior for GeoPedia's Home world
 * navigation map.
 *
 * This hook is intentionally specific to the world-navigation experience. It:
 *
 * - Marks countries according to quiz availability.
 * - Draws a repeating diagonal hatch over countries without quizzes.
 * - Applies hover highlighting only to countries with quizzes.
 * - Reports hover-label information for every country.
 * - Uses a pointer cursor only for navigable countries.
 * - Prevents navigation when a country has no registered quizzes.
 *
 * Base country coloring, including GeoGuessr versus non-GeoGuessr
 * classification, is handled separately by `useWorldNavigationMap`.
 */

"use client";

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import {
  FEATURE_FILL_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";

/** MapLibre image ID used by the unavailable-country hatch layer. */
const NO_QUIZZES_PATTERN_ID = "world-navigation-no-quizzes-pattern";

/** Layer containing the repeating diagonal unavailable-country hatch. */
const NO_QUIZZES_PATTERN_LAYER_ID =
  "world-navigation-no-quizzes-pattern";

/**
 * Information displayed by the floating world-navigation hover label.
 */
export type HoveredNavigationCountry = {
  /** User-facing country name. */
  name: string;

  /** Whether the country currently contains at least one registered quiz. */
  hasQuizzes: boolean;

  /** Horizontal pointer position relative to the map canvas. */
  x: number;

  /** Vertical pointer position relative to the map canvas. */
  y: number;
};

/**
 * Dependencies required by `useWorldNavigationInteractions`.
 */
type UseWorldNavigationInteractionsParams = {
  /** MapLibre instance created by `useWorldNavigationMap`. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether GeoPedia's world-country source and layers are ready. */
  isMapReady: boolean;

  /** GeoJSON property containing the user-facing country name. */
  labelProperty: string;

  /**
   * Country IDs containing at least one available feature or town quiz.
   *
   * Quiz availability is resolved before the interaction hook runs so hover
   * and click handlers can perform immediate synchronous availability checks.
   */
  countryIdsWithQuizzes: ReadonlySet<string>;

  /** Navigates to a country route after an available country is selected. */
  navigateToCountry: (countryId: string) => void;

  /** Updates the floating country hover label. */
  setHoveredCountry: (
    country: HoveredNavigationCountry | null,
  ) => void;
};

/**
 * Creates the small transparent image tiled across countries without quizzes.
 *
 * The image contains diagonal strokes only. The underlying country color stays
 * visible so GeoGuessr classification remains readable even when a country has
 * no available quizzes.
 *
 * @returns ImageData containing repeating diagonal strokes.
 */
function createNoQuizzesPattern(): ImageData {
  const size = 8;

  const canvas = document.createElement("canvas");

  canvas.width = size;
  canvas.height = size;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error(
      "Could not create world-navigation hatch pattern.",
    );
  }

  context.clearRect(0, 0, size, size);

  context.strokeStyle = "rgba(0, 0, 0, 0.16)";
  context.lineWidth = 1;

  context.beginPath();

  /*
   * Draw multiple segments so opposite canvas edges connect seamlessly when
   * MapLibre repeats the image.
   */
  context.moveTo(-1, size - 1);
  context.lineTo(size - 1, -1);

  context.moveTo(3, size + 1);
  context.lineTo(size + 1, 3);

  context.stroke();

  return context.getImageData(0, 0, size, size);
}

/**
 * Finds the first line layer belonging to GeoPedia's geographic source.
 *
 * The unavailable-country hatch should appear above the normal country fill
 * but beneath country borders. Finding the line layer dynamically avoids
 * coupling this hook to a particular border-layer constant.
 *
 * @param map - Current MapLibre map.
 * @returns Layer ID before which the hatch layer should be inserted.
 */
function findFeatureBorderLayerId(
  map: maplibregl.Map,
): string | undefined {
  return map
    .getStyle()
    .layers?.find(
      (layer) =>
        layer.type === "line" &&
        "source" in layer &&
        layer.source === FEATURE_SOURCE_ID,
    )?.id;
}

/**
 * Determines whether a country belongs to the resolved set of countries with
 * available quizzes.
 *
 * @param countryId - Country whose quiz availability should be checked.
 * @param countryIdsWithQuizzes - Resolved set of quiz-enabled country IDs.
 * @returns Whether the country contains at least one available quiz.
 */
function hasCountryQuizzes(
  countryId: string,
  countryIdsWithQuizzes: ReadonlySet<string>,
): boolean {
  return countryIdsWithQuizzes.has(countryId.toLowerCase());
}

/**
 * Marks each country feature with its current quiz availability.
 *
 * `querySourceFeatures` may return the same promoted feature more than once, so
 * each feature ID is processed only once before applying feature state.
 *
 * @param map - Ready MapLibre map.
 * @param countryIdsWithQuizzes - Resolved set of quiz-enabled country IDs.
 */
function applyCountryAvailabilityState(
  map: maplibregl.Map,
  countryIdsWithQuizzes: ReadonlySet<string>,
): void {
  const features = map.querySourceFeatures(FEATURE_SOURCE_ID);

  const processedIds = new Set<string>();

  for (const feature of features) {
    if (feature.id === undefined || feature.id === null) {
      continue;
    }

    const featureId = String(feature.id);

    if (processedIds.has(featureId)) {
      continue;
    }

    processedIds.add(featureId);

    map.setFeatureState(
      {
        source: FEATURE_SOURCE_ID,
        id: feature.id,
      },
      {
        hasQuizzes: hasCountryQuizzes(
          featureId,
          countryIdsWithQuizzes,
        ),
      },
    );
  }
}

/**
 * Adds the unavailable-country hatch layer.
 *
 * The layer is visible only when a country's `hasQuizzes` feature state is
 * false. No replacement fill is added, allowing the GeoGuessr/non-GeoGuessr
 * base color beneath the pattern to remain visible.
 *
 * @param map - Ready MapLibre map.
 */
function addUnavailableCountryPatternLayer(
  map: maplibregl.Map,
): void {
  if (!map.hasImage(NO_QUIZZES_PATTERN_ID)) {
    map.addImage(NO_QUIZZES_PATTERN_ID, createNoQuizzesPattern());
  }

  const beforeLayerId = findFeatureBorderLayerId(map);

  const unavailableOpacity: maplibregl.ExpressionSpecification = [
    "case",
    ["boolean", ["feature-state", "hasQuizzes"], false],
    0,
    1,
  ];

  if (!map.getLayer(NO_QUIZZES_PATTERN_LAYER_ID)) {
    map.addLayer(
      {
        id: NO_QUIZZES_PATTERN_LAYER_ID,
        type: "fill",
        source: FEATURE_SOURCE_ID,

        paint: {
          "fill-pattern": NO_QUIZZES_PATTERN_ID,
          "fill-opacity": unavailableOpacity,
        },
      },
      beforeLayerId,
    );
  }
}

/**
 * Registers quiz-availability styling and Home world-navigation interactions.
 *
 * @param params - Ready map state and navigation callbacks.
 */
export function useWorldNavigationInteractions({
  mapRef,
  isMapReady,
  labelProperty,
  countryIdsWithQuizzes,
  navigateToCountry,
  setHoveredCountry,
}: UseWorldNavigationInteractionsParams): void {
  useEffect(() => {
    const currentMap = mapRef.current;

    if (!currentMap || !isMapReady) {
      return;
    }

    const map = currentMap;

    applyCountryAvailabilityState(map, countryIdsWithQuizzes);

    addUnavailableCountryPatternLayer(map);

    /**
     * ID of the currently highlighted navigable country.
     *
     * Countries without quizzes intentionally never receive MapLibre hover
     * state, regardless of their GeoGuessr classification.
     */
    let hoveredFeatureId: string | number | null = null;

    /**
     * Clears active hover state from the previously highlighted country.
     */
    function clearHoverState(): void {
      if (hoveredFeatureId !== null) {
        map.setFeatureState(
          {
            source: FEATURE_SOURCE_ID,
            id: hoveredFeatureId,
          },
          {
            hover: false,
          },
        );

        hoveredFeatureId = null;
      }
    }

    /**
     * Handles pointer movement across world-country features.
     *
     * All countries report hover-label information, but only countries with
     * quizzes receive visual hover state and pointer-cursor behavior.
     */
    function handleMouseMove(
      event: maplibregl.MapMouseEvent & {
        features?: maplibregl.MapGeoJSONFeature[];
      },
    ): void {
      const feature = event.features?.[0];

      if (!feature) {
        return;
      }

      if (feature.id === undefined || feature.id === null) {
        return;
      }

      const countryId = String(feature.id);

      const countryHasQuizzes = hasCountryQuizzes(
        countryId,
        countryIdsWithQuizzes,
      );

      /*
       * Moving between countries always clears the previous visual hover state.
       */
      if (
        hoveredFeatureId !== null &&
        hoveredFeatureId !== feature.id
      ) {
        clearHoverState();
      }

      /*
       * Only countries containing quizzes receive the hover treatment.
       */
      if (countryHasQuizzes) {
        hoveredFeatureId = feature.id;

        map.setFeatureState(
          {
            source: FEATURE_SOURCE_ID,
            id: feature.id,
          },
          {
            hover: true,
          },
        );
      } else {
        clearHoverState();
      }

      map.getCanvas().style.cursor = countryHasQuizzes
        ? "pointer"
        : "default";

      const rawLabel = feature.properties?.[labelProperty];

      if (typeof rawLabel !== "string") {
        setHoveredCountry(null);

        return;
      }

      /*
       * All countries display their name. Countries without quizzes additionally
       * tell the user why they cannot be selected.
       */
      setHoveredCountry({
        name: rawLabel,
        hasQuizzes: countryHasQuizzes,
        x: event.point.x,
        y: event.point.y,
      });
    }

    /**
     * Clears all world-navigation hover UI when the pointer leaves the country
     * fill layer.
     */
    function handleMouseLeave(): void {
      clearHoverState();

      map.getCanvas().style.cursor = "";

      setHoveredCountry(null);
    }

    /**
     * Navigates to the selected country when that country contains quizzes.
     *
     * Countries without quizzes remain visible and identifiable but deliberately
     * do not navigate.
     */
    function handleClick(
      event: maplibregl.MapMouseEvent & {
        features?: maplibregl.MapGeoJSONFeature[];
      },
    ): void {
      const feature = event.features?.[0];

      if (
        !feature ||
        feature.id === undefined ||
        feature.id === null
      ) {
        return;
      }

      const countryId = String(feature.id).toLowerCase();

      if (!hasCountryQuizzes(countryId, countryIdsWithQuizzes)) {
        return;
      }

      navigateToCountry(countryId);
    }

    map.on("mousemove", FEATURE_FILL_LAYER_ID, handleMouseMove);

    map.on("mouseleave", FEATURE_FILL_LAYER_ID, handleMouseLeave);

    map.on("click", FEATURE_FILL_LAYER_ID, handleClick);

    return () => {
      /*
       * Remove only the listeners owned by this interaction effect.
       *
       * Feature state, custom layers, images, cursor state, and other MapLibre
       * resources belong to the map instance itself and are destroyed when the
       * world-navigation map is removed.
       */
      map.off("mousemove", FEATURE_FILL_LAYER_ID, handleMouseMove);

      map.off("mouseleave", FEATURE_FILL_LAYER_ID, handleMouseLeave);

      map.off("click", FEATURE_FILL_LAYER_ID, handleClick);

      setHoveredCountry(null);
    };
  }, [
    mapRef,
    isMapReady,
    labelProperty,
    countryIdsWithQuizzes,
    navigateToCountry,
    setHoveredCountry,
  ]);
}
