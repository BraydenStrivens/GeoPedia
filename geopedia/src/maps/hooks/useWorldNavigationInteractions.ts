/**
 * Owns interaction and availability styling for GeoPedia's home world
 * navigation map.
 *
 * This hook is intentionally specific to the world navigation experience. It:
 *
 * - Marks countries according to quiz availability.
 * - Gives unavailable countries a separate base fill.
 * - Draws a repeating diagonal hatch over unavailable countries.
 * - Applies hover highlighting only to countries with quizzes.
 * - Reports hover-label information for every country.
 * - Uses a pointer cursor only for navigable countries.
 * - Prevents navigation when a country has no registered quizzes.
 */

"use client";

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import {
  FEATURE_FILL_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";
import { hasCountryQuizzes } from "@/quiz/quizzes";

/**
 * Base fill placed over countries that currently have no registered quizzes.
 *
 * This is intentionally separate from the normal map fill so active-country
 * styling can continue to come from the map configuration.
 */
const NO_QUIZZES_FILL_COLOR = "#d1d5db";

/** MapLibre image ID used by the unavailable-country hatch layer. */
const NO_QUIZZES_PATTERN_ID = "world-navigation-no-quizzes-pattern";

/** Layer containing the unavailable-country background fill. */
const NO_QUIZZES_FILL_LAYER_ID = "world-navigation-no-quizzes-fill";

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
  /** MapLibre instance created by `useMap`. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether GeoPedia's geographic source and layers are ready. */
  isMapReady: boolean;

  /** GeoJSON property containing the user-facing country name. */
  labelProperty: string;

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
 * Navigation availability layers should appear above the normal country fill
 * but beneath country borders. Finding the line layer dynamically avoids
 * coupling this hook to a particular border-layer constant.
 *
 * @param map - Current MapLibre map.
 * @returns Layer ID before which availability fills should be inserted.
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
 * Marks each country feature with its current quiz availability.
 *
 * @param map - Ready MapLibre map.
 */
function applyCountryAvailabilityState(map: maplibregl.Map): void {
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
        hasQuizzes: hasCountryQuizzes(featureId),
      },
    );
  }
}

/**
 * Adds the unavailable-country fill and hatch layers.
 *
 * @param map - Ready MapLibre map.
 */
function addUnavailableCountryLayers(map: maplibregl.Map): void {
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

  if (!map.getLayer(NO_QUIZZES_FILL_LAYER_ID)) {
    map.addLayer(
      {
        id: NO_QUIZZES_FILL_LAYER_ID,
        type: "fill",
        source: FEATURE_SOURCE_ID,

        paint: {
          "fill-color": NO_QUIZZES_FILL_COLOR,

          "fill-opacity": unavailableOpacity,
        },
      },
      beforeLayerId,
    );
  }

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
 * Registers availability styling and home-world navigation interactions.
 *
 * @param params - Ready map state and navigation callbacks.
 */
export function useWorldNavigationInteractions({
  mapRef,
  isMapReady,
  labelProperty,
  navigateToCountry,
  setHoveredCountry,
}: UseWorldNavigationInteractionsParams): void {
  useEffect(() => {
    const currentMap = mapRef.current;

    if (!currentMap || !isMapReady) {
      return;
    }

    const map = currentMap;

    applyCountryAvailabilityState(map);

    addUnavailableCountryLayers(map);

    /**
     * ID of the currently highlighted navigable country.
     *
     * Unavailable countries intentionally never receive MapLibre hover state.
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

      const countryHasQuizzes = hasCountryQuizzes(countryId);

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
       * Only countries containing quizzes receive the darker hover treatment.
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

    function handleMouseLeave(): void {
      clearHoverState();

      map.getCanvas().style.cursor = "";

      setHoveredCountry(null);
    }

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

      /*
       * Unavailable countries remain visible and hoverable for identification,
       * but they do not navigate anywhere.
       */
      if (!hasCountryQuizzes(countryId)) {
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
       * resources belong to the map instance itself and are destroyed by
       * `useMap` when the map is removed.
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
    navigateToCountry,
    setHoveredCountry,
  ]);
}
