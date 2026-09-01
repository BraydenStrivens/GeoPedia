/**
 * Registers and manages quiz-map geographic hover behavior.
 *
 * Hover interactions control:
 *
 * - MapLibre feature-state highlighting.
 * - Completed-feature restrictions in Normal Mode.
 * - The hovered feature ID used by Show Answers labels.
 *
 * Navigation-map hover labels are intentionally handled by the separate world
 * navigation interaction system.
 */

import type * as maplibregl from "maplibre-gl";

import {
  FEATURE_FILL_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";

import {
  getFeatureAnswers,
  isFeatureFullyAnswered,
} from "../../labels/feature/featureAnswers";
import type {
  FeatureHoverState,
  QuizMapInteractionContext,
} from "./featureQuizInteractionTypes";

/**
 * MapLibre mouse event produced by an event registered against a geographic
 * layer.
 */
type FeatureMouseEvent = maplibregl.MapMouseEvent & {
  features?: maplibregl.MapGeoJSONFeature[];
};

/**
 * Clears MapLibre and React hover state for the currently hovered feature.
 *
 * @param context - Shared quiz-map interaction dependencies.
 * @param hoverState - Mutable feature hover state.
 */
function clearFeatureHover(
  { map, setHoveredFeatureId }: QuizMapInteractionContext,
  hoverState: FeatureHoverState,
): void {
  if (hoverState.featureId !== null) {
    map.setFeatureState(
      {
        source: FEATURE_SOURCE_ID,
        id: hoverState.featureId,
      },
      {
        hover: false,
      },
    );

    hoverState.featureId = null;
  }

  setHoveredFeatureId(null);
}

/**
 * Registers mousemove and mouseleave behavior for a quiz map's primary
 * geographic feature layer.
 *
 * @param context - Shared quiz-map interaction dependencies.
 * @param hoverState - Mutable hover state shared with click interactions.
 * @returns Cleanup function removing the registered listeners.
 */
export function registerQuizHoverInteractions(
  context: QuizMapInteractionContext,
  hoverState: FeatureHoverState,
): () => void {
  const {
    map,
    hover,
    hoverEnabledRef,
    clickBehaviorRef,
    quizRef,
    quizModeRef,
    answerStatusesRef,
    setHoveredFeatureId,
  } = context;

  if (!hover?.enabled) {
    return () => {};
  }

  function handleMouseMove(event: FeatureMouseEvent): void {
    /*
     * Runtime settings may disable hover after these event handlers were
     * installed. Clear any existing hover immediately when that happens.
     */
    if (!hoverEnabledRef.current) {
      clearFeatureHover(context, hoverState);

      return;
    }

    const feature = event.features?.[0];

    if (!feature) {
      return;
    }

    const featureId = feature.id;

    /*
     * Hover requires a stable MapLibre feature ID so feature-state can be
     * applied safely.
     */
    if (featureId === undefined || featureId === null) {
      return;
    }

    const normalizedFeatureId = String(featureId);

    /*
     * Remove hover from the previously highlighted feature before moving hover
     * state to another feature.
     */
    if (
      hoverState.featureId !== null &&
      hoverState.featureId !== normalizedFeatureId
    ) {
      map.setFeatureState(
        {
          source: FEATURE_SOURCE_ID,
          id: hoverState.featureId,
        },
        {
          hover: false,
        },
      );
    }

    const clickBehavior = clickBehaviorRef.current;

    /**
     * In Normal Mode, completed quiz features stop hovering so the user can
     * visually distinguish only selectable geography.
     *
     * Hard Mode keeps all features hoverable to avoid revealing information
     * through answer elimination.
     *
     * Show Answers uses click behavior `none`, so it bypasses this restriction
     * while retaining hover for answer labels.
     */
    if (clickBehavior === "quiz") {
      const quiz = quizRef.current;

      const featureValue = feature.properties?.[quiz.answerProperty];

      const featureAnswers = getFeatureAnswers(featureValue);

      const isHardMode = quizModeRef.current === "hard";

      if (
        !isHardMode &&
        isFeatureFullyAnswered(
          featureAnswers,
          answerStatusesRef.current,
        )
      ) {
        clearFeatureHover(context, hoverState);

        return;
      }
    }

    hoverState.featureId = normalizedFeatureId;

    setHoveredFeatureId(normalizedFeatureId);

    map.setFeatureState(
      {
        source: FEATURE_SOURCE_ID,
        id: featureId,
      },
      {
        hover: true,
      },
    );
  }

  function handleMouseLeave(): void {
    clearFeatureHover(context, hoverState);
  }

  map.on("mousemove", FEATURE_FILL_LAYER_ID, handleMouseMove);

  map.on("mouseleave", FEATURE_FILL_LAYER_ID, handleMouseLeave);

  return () => {
    map.off("mousemove", FEATURE_FILL_LAYER_ID, handleMouseMove);

    map.off("mouseleave", FEATURE_FILL_LAYER_ID, handleMouseLeave);

    clearFeatureHover(context, hoverState);
  };
}
