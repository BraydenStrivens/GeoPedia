/**
 * Defines the shared state and dependencies used by GeoPedia's MapLibre
 * interaction modules.
 *
 * Interaction handlers receive changing React values through refs so the
 * handlers can remain installed without recreating the MapLibre map.
 */

import type * as maplibregl from "maplibre-gl";
import type React from "react";

import type {
  HoverConfig,
  HoveredFeature,
  IncorrectSelection,
  MapClickBehavior,
} from "@/maps/types";
import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * Mutable MapLibre hover state shared by hover and click interactions.
 */
export type FeatureHoverState = {
  /** ID of the feature currently carrying MapLibre hover state. */
  featureId: string | null;
};

/**
 * Dependencies required by GeoPedia's map interaction system.
 */
export type MapInteractionContext = {
  /** MapLibre map receiving feature interaction handlers. */
  map: maplibregl.Map;

  /** Current click behavior without requiring MapLibre reinitialization. */
  clickBehaviorRef: React.RefObject<MapClickBehavior>;

  /** Static hover configuration supported by the map. */
  hover?: HoverConfig;

  /** Determines whether feature hover is currently enabled. */
  hoverEnabledRef: React.RefObject<boolean>;

  /** Latest quiz definition associated with the map. */
  quizRef: React.RefObject<Quiz | undefined>;

  /** Latest Normal/Hard quiz mode. */
  quizModeRef: React.RefObject<QuizMode>;

  /** Latest quiz question currently being asked. */
  currentQuestionRef: React.RefObject<QuizQuestion | undefined>;

  /** Function used to submit the result of a geographic selection. */
  answerQuestionRef: React.RefObject<(isCorrect: boolean) => void>;

  /** Latest completion result for every answered quiz question. */
  answerStatusesRef: React.RefObject<Record<string, AnswerStatus>>;

  /** Determines whether incorrect selections display their actual answer. */
  showIncorrectSelectionRef: React.RefObject<boolean>;

  /** Reports the currently hovered feature ID to React. */
  setHoveredFeatureId: (featureId: string | null) => void;

  /** Updates temporary incorrect-selection feedback. */
  setIncorrectSelection: (
    selection: IncorrectSelection | null,
  ) => void;

  /** Navigates to the country represented by a navigation-map feature. */
  navigateToCountry: (countryId: string) => void;

  /** Updates the floating hover label used by navigation maps. */
  setHoveredFeature: (feature: HoveredFeature | null) => void;
};
