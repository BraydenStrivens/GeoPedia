/**
 * Registers and manages geographic feature hover behavior.
 *
 * Hover interactions control MapLibre feature-state highlighting, navigation
 * hover labels, completed-feature restrictions in Normal Mode, and the
 * hovered feature ID used by Show Answers labels.
 */
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
        source: "features",
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
 * Registers mousemove and mouseleave behavior for GeoPedia's feature layer.
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

  map.on("mousemove", "features-fill", (event) => {
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
     * GeoPedia's interactive maps require promoted string IDs for
     * feature-state and Show Answers label matching.
     */
    if (typeof featureId !== "string") {
      return;
    }

    /*
     * Remove hover from the previously highlighted feature before moving
     * the hover state to another feature.
     */
    if (
      hoverState.featureId !== null &&
      hoverState.featureId !== featureId
    ) {
      map.setFeatureState(
        {
          source: "features",
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
     * visually distinguish only selectable features.
     *
     * Hard Mode keeps all features hoverable to prevent answer elimination.
     * Show Answers uses click behavior "none", so it also bypasses this rule.
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

    hoverState.featureId = featureId;

    setHoveredFeatureId(featureId);

    map.setFeatureState(
      {
        source: "features",
        id: featureId,
      },
      {
        hover: true,
      },
    );

    /*
     * Navigation maps additionally display a floating name beside the
     * pointer. Quiz maps and Show Answers use hover without this label.
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

  map.on("mouseleave", "features-fill", () => {
    clearFeatureHover(context, hoverState);
  });
}
