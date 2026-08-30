/**
 * Defines the state and dependencies used by GeoPedia's quiz-map interaction
 * modules.
 *
 * Quiz interaction listeners remain installed for the lifetime of the current
 * MapLibre map. React values that may change during that lifetime are supplied
 * through refs so handlers can read current state without being recreated.
 */

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";

import type { HoverConfig, IncorrectSelection } from "@/maps/types";
import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * Click behaviors supported specifically by `QuizMap`.
 *
 * Navigation is intentionally absent because the world-navigation map owns its
 * own interaction system.
 */
export type QuizMapClickBehavior = "quiz" | "select" | "none";

/**
 * Mutable hover identity shared by quiz click and hover handlers.
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
 * Dependencies required by GeoPedia's quiz-map interaction system.
 */
export type QuizMapInteractionContext = {
  /*
   * Map instance.
   */

  /** MapLibre map receiving quiz interaction handlers. */
  map: maplibregl.Map;

  /*
   * Runtime interaction state.
   */

  /** Current behavior performed when a geographic feature is clicked. */
  clickBehaviorRef: RefObject<QuizMapClickBehavior>;

  /** Static hover configuration supported by the map. */
  hover?: HoverConfig;

  /** Determines whether geographic feature hover is currently enabled. */
  hoverEnabledRef: RefObject<boolean>;

  /*
   * Runtime quiz state.
   */

  /** Latest quiz definition associated with the map. */
  quizRef: RefObject<Quiz>;

  /**
   * Whether the quiz is currently accepting scored answers.
   *
   * When false, quiz-map clicks reveal the selected feature's answer rather than
   * submitting a response.
   */
  isQuizRunningRef: RefObject<boolean>;

  /** Latest Normal/Hard quiz mode. */
  quizModeRef: RefObject<QuizMode>;

  /** Latest quiz question currently being asked. */
  currentQuestionRef: RefObject<QuizQuestion | undefined>;

  /** Latest completion result for every answered quiz question. */
  answerStatusesRef: RefObject<Record<string, AnswerStatus>>;

  /** Current function used to submit a geographic quiz selection. */
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
};
