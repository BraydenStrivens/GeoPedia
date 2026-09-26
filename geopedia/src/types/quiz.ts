/**
 * Defines the core data types used by GeoPedia's quiz system.
 *
 * These types describe quiz definitions, questions, answers, and answer
 * results. They are shared across quiz configuration, quiz logic, map
 * interactions, and UI components to keep quiz data consistent throughout
 * the application.
 */

import { BaseMapLayerVisibilityConfig } from "@/maps/types";
import type { QuizGroupingConfig } from "@/quiz/groupings/feature/types";

/* ========================= SHARED ========================= */

/**
 * Represents the result of a completed quiz question.
 *
 * - `correct` indicates that the correct geographic feature was selected.
 * - `wrong` indicates that an incorrect geographic feature was selected.
 */
export type AnswerStatus = "correct" | "wrong";

/**
 * Determines how many quiz answers can belong to the same geographic feature.
 *
 * - `single` indicates that each feature represents one answer.
 * - `multiple` indicates that one feature can represent multiple answers.
 */
export type AnswerType = "single" | "multiple";

/**
 * Identifies the interaction model used by a quiz.
 *
 * - `feature` indicates that questions are answered by selecting geographic
 *   features represented by the quiz's GeoJSON data.
 *
 * - `town` indicates that questions are answered by selecting a geographic
 *   location for a town rather than selecting a GeoJSON feature.
 *
 * The quiz kind acts as a discriminant for the `Quiz` union, allowing quiz
 * logic and UI components to safely determine which properties and interaction
 * behavior are available for a particular quiz.
 */
export type QuizKind = "feature" | "town";

/**
 * Difficulty tier assigned to a quiz according to its total question count.
 */
export type QuizDifficulty = "easy" | "medium" | "hard" | "extreme";

/**
 * Language used when presenting quiz-answer names to the user.
 *
 * - `english` uses the quiz question's default English/international display.
 * - `native` prefers the question's native-language display when available.
 *
 * Questions without a native display fall back to their normal display and
 * then their raw answer value.
 */
export type QuizQuestionLanguage = "english" | "native";

/**
 * Defines the user-facing content displayed as a quiz question prompt.
 *
 * A prompt can either display text directly or display an image with
 * alternative text for accessibility.
 *
 * - `text` displays the supplied text as the question prompt.
 * - `image` displays the supplied image and uses `alt` to describe it.
 */
export type QuizQuestionPrompt =
  | {
      /** Identifies this prompt as a text prompt. */
      type: "text";

      /** Text displayed to the user for the question. */
      text: string;
    }
  | {
      /** Identifies this prompt as an image prompt. */
      type: "image";

      /** URL of the image displayed for the question. */
      imageUrl: string;

      /** Alternative text describing the image for accessibility. */
      alt: string;
    };

/**
 * Lightweight metadata describing a quiz that is available to the user.
 *
 * Quiz listings are used by navigation and selection interfaces that need to
 * display or link to available quizzes without loading the complete quiz
 * definition or its underlying question data.
 *
 * This is especially useful for generated town quizzes, whose full town
 * datasets do not need to be loaded merely to display the quiz on a country
 * page.
 */
export type QuizListing = {
  /** Stable identifier used to identify and route to the quiz. */
  id: string;

  /** User-facing name displayed when presenting the quiz. */
  name: string;

  /** Description explaining the quiz's content and available options. */
  description: string;

  /** Quiz type used to distinguish feature and town quiz listings. */
  kind: QuizKind;

  /** Difficulty derived from the total number of questions in the quiz. */
  difficulty: QuizDifficulty;

  /** Total number of questions in the full quiz. */
  questionCount: number;
};

/**
 * Defines properties shared by every GeoPedia quiz type.
 */
interface BaseQuiz {
  /** Unique identifier for the quiz. */
  id: string;

  /** User-facing name of the quiz. */
  name: string;

  /**
   * User-facing description explaining what the quiz covers and any relevant
   * details such as included territories, filtering, or grouping options.
   */
  description: string;
}

/**
 * Defines any quiz supported by GeoPedia.
 *
 * The `kind` property allows quiz logic and UI components to safely distinguish
 * feature-selection quizzes from location-based town quizzes.
 */
export type Quiz = FeatureQuiz | TownQuiz;

/* ========================= FEATURE ========================= */

/**
 * Represents one question that can be asked during a feature-based quiz.
 *
 * The answer corresponds to a value stored in the GeoJSON property identified
 * by the parent quiz's `answerProperty`.
 */
export interface FeatureQuizQuestion {
  /** Raw answer value the user must identify on the map. */
  answer: string;

  /**
   * Optional user-facing english/internation-latin question text.
   *
   * The raw `answer` value is displayed when this is omitted.
   */
  display?: string;

  /**
   * Optional native-language display text for this quiz answer.
   *
   * Native question language prefers this value for question prompts, Show
   * Answers labels, and temporary answer-feedback popups. When omitted, Native
   * mode falls back to `display` and then `answer`.
   */
  nativeDisplay?: string;

  /**
   * Optional explicit question prompt.
   *
   * When omitted, GeoPedia falls back to `display` and then `answer`, preserving
   * the behavior of all existing quizzes.
   */
  prompt?: QuizQuestionPrompt;
}

/**
 * Defines a feature-based quiz whose answers correspond to GeoJSON features.
 *
 * Feature quizzes identify answers through properties stored on map features
 * and support the existing region-based interaction system.
 */
export interface FeatureQuiz extends BaseQuiz {
  /** ID of the map configuration used by a feature-based quiz. */
  mapId: string;

  /** Identifies this quiz as a GeoJSON feature-based quiz. */
  kind: "feature";

  /** GeoJSON property containing the feature values used as quiz answers. */
  answerProperty: string;

  /** Determines whether one geographic feature can represent multiple answers. */
  answerType: AnswerType;

  /**
   * Optional multiplier applied to image-based quiz prompts and answer labels.
   *
   * A value of 1 uses the default image size. Values greater than 1 enlarge
   * images while preserving their aspect ratio.
   */
  imageSizeMultiplier?: number;

  /**
   * Optional visibility overrides for labels and administrative boundaries
   * supplied by the base-map style while this quiz is displayed.
   *
   * Omitted values remain visible.
   */
  baseMapLayers?: BaseMapLayerVisibilityConfig;

  /**
   * Optional property-based grouping configuration supported by this quiz.
   *
   * Manual feature selection does not require this configuration and remains
   * available independently.
   */
  grouping?: QuizGroupingConfig;

  /** Complete set of questions available to the quiz. */
  questions: FeatureQuizQuestion[];
}

/* ========================= TOWN ========================= */

/**
 * Represents one settlement available to GeoPedia's town quiz system.
 *
 * Town data describes the canonical geographic and population information
 * loaded from a country's generated town dataset. Quiz-specific presentation
 * such as question prompts is represented separately by `TownQuizQuestion`.
 */
export interface TownData {
  /** Stable GeoNames identifier for the settlement. */
  id: string;

  /**
   * Preferred English/international settlement name.
   *
   * This is the default question name and remains available for every town.
   */
  name: string;

  /** Locally used/native settlement name when it differs from `name`. */
  nativeName?: string;

  /** Latitude of the settlement's target location. */
  latitude: number;

  /** Longitude of the settlement's target location. */
  longitude: number;

  /** Population value used when ranking towns. */
  population: number;

  /** Population-based rank within the generated country dataset. */
  populationRank: number;

  /** Whether this settlement is the country's national capital. */
  isCapital: boolean;
}

/**
 * Represents one question in a location-based town quiz.
 *
 * Canonical settlement information is kept in `town`, while `prompt` contains
 * optional question-specific presentation. When no explicit prompt is
 * provided, the town's name is used by the normal town quiz experience.
 */
export interface TownQuizQuestion {
  /** Canonical settlement data identifying the question's target location. */
  town: TownData;

  /**
   * Optional explicit question prompt.
   *
   * Image-based town quizzes can provide an image prompt while normal town
   * quizzes omit this value and continue displaying the town's name.
   */
  prompt?: QuizQuestionPrompt;
}

/**
 * References one canonical town while defining question-specific presentation
 * for a configured town quiz.
 *
 * Canonical town metadata remains in the generated country town dataset and is
 * resolved by `townId` when the complete quiz is constructed.
 */
export interface TownQuizQuestionConfig {
  townId: string;
  prompt: QuizQuestionPrompt;
}

/**
 * Handwritten definition for a specialized town quiz.
 *
 * Configured town quizzes reference canonical generated towns by stable ID
 * rather than duplicating their names, coordinates, populations, or other
 * settlement metadata.
 */
export interface TownQuizConfig {
  id: string;
  name: string;
  description: string;
  questions: TownQuizQuestionConfig[];
}

/**
 * Runtime contents of one generated country town dataset.
 */
export interface TownQuizData {
  /** Canonical towns available from the country's generated dataset. */
  towns: TownData[];
}

/**
 * Defines a location-based town quiz.
 *
 * Unlike feature quizzes, town quizzes are answered by clicking a geographic
 * coordinate rather than selecting a GeoJSON feature.
 */
export interface TownQuiz extends BaseQuiz {
  /** Identifies this quiz as a town/location quiz. */
  kind: "town";

  /** Complete set of questions available to the quiz. */
  questions: TownQuizQuestion[];
}
