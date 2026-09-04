/**
 * Defines the core data types used by GeoPedia's quiz system.
 *
 * These types describe quiz definitions, questions, answers, and answer
 * results. They are shared across quiz configuration, quiz logic, map
 * interactions, and UI components to keep quiz data consistent throughout
 * the application.
 */

import type { QuizGroupingConfig } from "@/quiz/groupings/feature/types";

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
 * Represents one question that can be asked during a feature-based quiz.
 *
 * The answer corresponds to a value stored in the GeoJSON property identified
 * by the parent quiz's `answerProperty`.
 */
export interface QuizQuestion {
  /** Raw answer value the user must identify on the map. */
  answer: string;

  /**
   * Optional user-facing question text.
   *
   * The raw `answer` value is displayed when this is omitted.
   */
  display?: string;

  /**
   * Optional explicit question prompt.
   *
   * When omitted, GeoPedia falls back to `display` and then `answer`, preserving
   * the behavior of all existing quizzes.
   */
  prompt?: QuizQuestionPrompt;
}

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

  /** Quiz type used to distinguish feature and town quiz listings. */
  kind: QuizKind;
};

/**
 * Defines properties shared by every GeoPedia quiz type.
 */
interface BaseQuiz {
  /** Unique identifier for the quiz. */
  id: string;

  /** User-facing name of the quiz. */
  name: string;
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
   * Optional property-based grouping configuration supported by this quiz.
   *
   * Manual feature selection does not require this configuration and remains
   * available independently.
   */
  grouping?: QuizGroupingConfig;

  /** Complete set of questions available to the quiz. */
  questions: QuizQuestion[];
}

/**
 * Represents one town available to a location-based town quiz.
 */
export interface TownQuizTown {
  /** Stable GeoNames identifier for the settlement. */
  id: string;

  /**
   * Preferred English/international settlement name.
   *
   * This is the default question name and remains available for every town.
   */
  name: string;

  /**  Locally used/native settlement name when it differs from `name`. */
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
 * Runtime contents of one generated country town dataset.
 */
export interface TownQuizData {
  /** Towns available to the country's town quiz. */
  towns: TownQuizTown[];
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

  /**
   * Maximum distance from the target that can contribute toward the question's
   * score.
   *
   * The exact scoring function can use this value together with the perfect
   * answer radius.
   */
  // maxErrorKm: number;

  /** Complete set of towns available to the quiz. */
  towns: TownQuizTown[];
}

/**
 * Defines any quiz supported by GeoPedia.
 *
 * The `kind` property allows quiz logic and UI components to safely distinguish
 * feature-selection quizzes from location-based town quizzes.
 */
export type Quiz = FeatureQuiz | TownQuiz;
