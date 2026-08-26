/**
 * Defines the shared state and dependencies used by GeoPedia's MapLibre
 * interaction modules.
 *
 * Click and hover handlers are installed for the lifetime of a MapLibre map.
 * React values that may change during that lifetime are therefore supplied
 * through refs so handlers can always read current state without requiring the
 * map or its listeners to be recreated.
 *
 * This shared context is consumed by:
 *
 * - Click interactions.
 * - Hover interactions.
 * - Navigation-map behavior.
 * - Quiz interaction.
 * - Manual feature selection.
 */

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";

import type {
  HoverConfig,
  HoveredFeature,
  IncorrectSelection,
  MapClickBehavior,
} from "@/maps/types";
import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * Mutable hover identity shared by click and hover interaction handlers.
 *
 * GeoPedia stores this identity as a normalized string so React-side hover
 * state, Show Answers labels, and quiz interaction all use one consistent
 * feature-ID representation.
 */
export type FeatureHoverState = {
  /** Normalized ID of the feature currently carrying MapLibre hover state. */
  featureId: string | null;
};

/**
 * Dependencies required by GeoPedia's geographic map interaction system.
 */
export type MapInteractionContext = {
  /*
   * Map instance.
   */

  /** MapLibre map receiving geographic interaction handlers. */
  map: maplibregl.Map;

  /*
   * Runtime interaction state.
   */

  /**
   * Current behavior performed when a geographic feature is clicked.
   *
   * The value may switch between navigation, quiz, manual selection, and
   * disabled interaction without reinstalling MapLibre listeners.
   */
  clickBehaviorRef: RefObject<MapClickBehavior>;

  /** Static hover configuration supported by the map. */
  hover?: HoverConfig;

  /** Determines whether geographic feature hover is currently enabled. */
  hoverEnabledRef: RefObject<boolean>;

  /*
   * Runtime quiz state.
   */

  /** Latest quiz definition associated with the map. */
  quizRef: RefObject<Quiz | undefined>;

  /** Latest Normal/Hard quiz mode. */
  quizModeRef: RefObject<QuizMode>;

  /** Latest quiz question currently being asked. */
  currentQuestionRef: RefObject<QuizQuestion | undefined>;

  /** Latest completion result for every answered quiz question. */
  answerStatusesRef: RefObject<Record<string, AnswerStatus>>;

  /** Current function used to submit the result of a geographic quiz selection. */
  answerQuestionRef: RefObject<(isCorrect: boolean) => void>;

  /** Determines whether incorrect selections display their actual answer. */
  showIncorrectSelectionRef: RefObject<boolean>;

  /*
   * Manual feature selection.
   */

  /** Latest callback used when manual-selection mode toggles a feature. */
  onFeatureSelectRef: RefObject<(featureId: string) => void>;

  /*
   * React interaction callbacks.
   */

  /** Reports the normalized ID of the geographic feature currently hovered. */
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
