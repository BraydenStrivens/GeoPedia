/**
 * Registers and manages geographic feature hover behavior.
 *
 * Hover interactions control:
 *
 * - MapLibre feature-state highlighting.
 * - Navigation-map hover labels.
 * - Completed-feature restrictions in Normal Mode.
 * - The hovered feature ID used by Show Answers labels.
 *
 * Runtime values are read through refs so hover behavior can change without
 * reinstalling the MapLibre event handlers.
 */

import {
  FEATURE_FILL_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";

import {
  getFeatureAnswers,
  isFeatureFullyAnswered,
} from "./featureAnswers";
import type {
  FeatureHoverState,
  MapInteractionContext,
} from "./interactionTypes";

/**
 * Clears MapLibre and React hover state for the currently hovered feature.
 *
 * @param context - Shared map interaction dependencies.
 * @param hoverState - Mutable feature hover state.
 */
function clearFeatureHover(
  {
    map,
    setHoveredFeature,
    setHoveredFeatureId,
  }: MapInteractionContext,
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
  setHoveredFeature(null);
}

/**
 * Registers mousemove and mouseleave behavior for GeoPedia's primary
 * geographic feature layer.
 *
 * @param context - Shared map interaction dependencies.
 * @param hoverState - Mutable hover state shared with click interactions.
 */
export function registerHoverInteractions(
  context: MapInteractionContext,
  hoverState: FeatureHoverState,
): void {
  const {
    map,
    hover,
    hoverEnabledRef,
    clickBehaviorRef,
    quizRef,
    quizModeRef,
    answerStatusesRef,
    setHoveredFeature,
    setHoveredFeatureId,
  } = context;

  if (!hover?.enabled) {
    return;
  }

  map.on("mousemove", FEATURE_FILL_LAYER_ID, (event) => {
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

    /*
     * GeoPedia normalizes stable feature identity to strings for React-side
     * state and Show Answers label matching.
     */
    const normalizedFeatureId = String(featureId);

    /*
     * Remove hover from the previously highlighted feature before moving
     * hover state to another feature.
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
     * Show Answers uses click behavior "none", so it bypasses this completed-
     * feature restriction and keeps hover available for answer labels.
     */
    if (clickBehavior === "quiz" && quizRef.current) {
      const featureValue =
        feature.properties?.[quizRef.current.answerProperty];

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

    /*
     * MapLibre receives the original string-or-number feature ID, while React
     * stores the normalized string representation.
     */
    map.setFeatureState(
      {
        source: FEATURE_SOURCE_ID,
        id: featureId,
      },
      {
        hover: true,
      },
    );

    /*
     * Navigation maps additionally display a floating geographic name beside
     * the pointer. Quiz maps and Show Answers use hover without this label.
     */
    if (clickBehavior !== "navigate") {
      return;
    }

    const hoverLabel = feature.properties?.[hover.labelProperty];

    if (typeof hoverLabel !== "string") {
      return;
    }

    setHoveredFeature({
      name: hoverLabel,
      x: event.point.x,
      y: event.point.y,
    });
  });

  map.on("mouseleave", FEATURE_FILL_LAYER_ID, () => {
    clearFeatureHover(context, hoverState);
  });
}
