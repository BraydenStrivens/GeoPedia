/**
 * Defines the state and dependencies used by GeoPedia's feature quiz map
 * interaction modules.
 *
 * Feature quiz interaction listeners remain installed for the lifetime of the
 * current MapLibre map. React values that may change during that lifetime are
 * supplied through refs so handlers can read current state without being
 * recreated.
 *
 * The interaction context supports both active quiz behavior and inactive map
 * inspection. Temporary feature-selection feedback is shared by those
 * interactions, while settings that specifically govern incorrect-answer
 * feedback remain separately named.
 */

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";

import type { FeatureSelection, HoverConfig } from "@/maps/types";
import type { QuizMode } from "@/types/featureQuizSettings";
import type {
  AnswerStatus,
  FeatureQuiz,
  QuizQuestion,
} from "@/types/quiz";

/**
 * Click behaviors supported specifically by feature quiz maps.
 *
 * Navigation is intentionally absent because the world-navigation map owns its
 * own interaction system.
 */
export type QuizMapClickBehavior = "quiz" | "select" | "none";

/**
 * Mutable hover identity shared by feature quiz click and hover handlers.
 *
 * GeoPedia stores this identity as a normalized string so React-side hover
 * state, Show Answers labels, and quiz interactions all use one consistent
 * feature-ID representation.
 */
export type FeatureHoverState = {
  /** Normalized ID of the feature currently carrying MapLibre hover state. */
  featureId: string | null;
};

/**
 * Dependencies required by GeoPedia's feature quiz map interaction system.
 */
export type QuizMapInteractionContext = {
  /*
   * Map instance.
   */

  /** MapLibre map receiving feature quiz interaction handlers. */
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

  /** Latest feature quiz definition associated with the map. */
  quizRef: RefObject<FeatureQuiz>;

  /**
   * Whether the feature quiz is currently accepting scored answers.
   *
   * When false, normal quiz-map clicks act as lightweight study interactions
   * and temporarily reveal the selected feature's answer instead of submitting
   * a scored response.
   */
  isQuizRunningRef: RefObject<boolean>;

  /** Latest Normal/Hard feature quiz mode. */
  quizModeRef: RefObject<QuizMode>;

  /** Latest feature quiz question currently being asked. */
  currentQuestionRef: RefObject<QuizQuestion | undefined>;

  /** Latest completion result for every answered feature quiz question. */
  answerStatusesRef: RefObject<Record<string, AnswerStatus>>;

  /** Current function used to submit a geographic quiz selection. */
  answerQuestionRef: RefObject<(isCorrect: boolean) => void>;

  /**
   * Determines whether an incorrect selection made during an active quiz
   * reveals the selected feature's actual answer.
   *
   * This setting is specific to incorrect quiz feedback even though the
   * temporary feature-selection state itself is also used by inactive-map
   * inspection.
   */
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

  /**
   * Updates temporary feature-selection feedback.
   *
   * The selection may represent incorrect-answer feedback during an active
   * quiz or temporary answer inspection while the quiz is inactive.
   */
  setFeatureSelection: (selection: FeatureSelection | null) => void;
};
