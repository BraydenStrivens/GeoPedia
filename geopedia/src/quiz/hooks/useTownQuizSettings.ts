/**
 * Loads and persists user-configurable settings for an individual town quiz.
 *
 * Settings for all town quizzes are stored together in localStorage under one
 * shared storage entry. Each quiz is identified by a key built from its
 * country ID and quiz ID.
 *
 * Persisted values are validated field-by-field when loaded so invalid or
 * outdated values safely fall back to the current defaults.
 *
 * This hook is expected to run only after GeoPedia's existing quiz hydration
 * boundary has completed. That prevents server rendering from accessing
 * localStorage and ensures the quiz initially uses its persisted settings.
 */

"use client";

import {
  type Dispatch,
  type SetStateAction,
  useEffect,
  useState,
} from "react";

import {
  DEFAULT_TOWN_QUIZ_SETTINGS,
  type TownQuizSettings,
} from "@/types/townQuizSettings";

/** localStorage entry containing settings for every town quiz. */
const TOWN_QUIZ_SETTINGS_STORAGE_KEY = "town-quiz-settings";

/**
 * Persisted town-quiz settings keyed by country and quiz ID.
 *
 * Values are treated as unknown when loaded so each field can be validated
 * before being exposed to the application.
 */
type StoredTownQuizSettings = Record<string, unknown>;

/**
 * Result returned by `useTownQuizSettings`.
 */
type UseTownQuizSettingsResult = {
  /** Current persisted town quiz settings. */
  settings: TownQuizSettings;

  /** React state setter for the current town quiz settings. */
  setSettings: Dispatch<SetStateAction<TownQuizSettings>>;
};

/**
 * Builds the dictionary key belonging to one town quiz.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Unique town quiz identifier.
 * @returns Stable key within the shared settings dictionary.
 */
function createTownQuizSettingsKey(
  countryId: string,
  quizId: string,
): string {
  return `${countryId.toLowerCase()}_${quizId.toLowerCase()}`;
}

/**
 * Determines whether an unknown value is a supported town quiz mode.
 *
 * @param value - Unknown persisted value.
 */
function isTownQuizMode(
  value: unknown,
): value is TownQuizSettings["mode"] {
  return value === "normal" || value === "hard";
}

/**
 * Determines whether an unknown value is a supported question language.
 *
 * @param value - Unknown persisted value.
 */
function isQuestionLanguage(
  value: unknown,
): value is TownQuizSettings["questionLanguage"] {
  return value === "english" || value === "native";
}

/**
 * Parses one quiz's persisted settings with field-level fallbacks.
 *
 * Field-level validation allows valid existing settings to survive additions
 * or changes to the settings model while rejecting unsupported persisted
 * values.
 *
 * @param value - Persisted value belonging to one town quiz.
 * @returns Validated town quiz settings.
 */
function parseStoredQuizSettings(value: unknown): TownQuizSettings {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {
      ...DEFAULT_TOWN_QUIZ_SETTINGS,
    };
  }

  const storedSettings = value as Record<string, unknown>;

  return {
    mode: isTownQuizMode(storedSettings.mode)
      ? storedSettings.mode
      : DEFAULT_TOWN_QUIZ_SETTINGS.mode,

    questionLanguage: isQuestionLanguage(
      storedSettings.questionLanguage,
    )
      ? storedSettings.questionLanguage
      : DEFAULT_TOWN_QUIZ_SETTINGS.questionLanguage,

    showLabels:
      typeof storedSettings.showLabels === "boolean"
        ? storedSettings.showLabels
        : DEFAULT_TOWN_QUIZ_SETTINGS.showLabels,
  };
}

/**
 * Loads and persists settings belonging to one town quiz.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Town quiz identifier.
 * @returns Current settings and their React state setter.
 */
export function useTownQuizSettings(
  countryId: string,
  quizId: string,
): UseTownQuizSettingsResult {
  const quizSettingsKey = createTownQuizSettingsKey(
    countryId,
    quizId,
  );

  /**
   * Loads this quiz's initial settings exactly once when the hook mounts.
   *
   * The surrounding quiz hydration boundary guarantees that this initializer
   * runs in the browser, where localStorage is available.
   */
  const [settings, setSettings] = useState<TownQuizSettings>(() => {
    try {
      const storedValue = window.localStorage.getItem(
        TOWN_QUIZ_SETTINGS_STORAGE_KEY,
      );

      if (!storedValue) {
        return {
          ...DEFAULT_TOWN_QUIZ_SETTINGS,
        };
      }

      const storedSettings = JSON.parse(
        storedValue,
      ) as StoredTownQuizSettings;

      return parseStoredQuizSettings(storedSettings[quizSettingsKey]);
    } catch (error) {
      console.error("Failed to load town quiz settings:", error);

      return {
        ...DEFAULT_TOWN_QUIZ_SETTINGS,
      };
    }
  });

  /**
   * Persists this quiz's settings whenever they change.
   *
   * Only the current quiz's dictionary entry is replaced. Settings belonging
   * to other town quizzes remain untouched.
   */
  useEffect(() => {
    try {
      const storedValue = window.localStorage.getItem(
        TOWN_QUIZ_SETTINGS_STORAGE_KEY,
      );

      const storedSettings: StoredTownQuizSettings = storedValue
        ? (JSON.parse(storedValue) as StoredTownQuizSettings)
        : {};

      storedSettings[quizSettingsKey] = settings;

      window.localStorage.setItem(
        TOWN_QUIZ_SETTINGS_STORAGE_KEY,
        JSON.stringify(storedSettings),
      );
    } catch (error) {
      console.error("Failed to save town quiz settings:", error);
    }
  }, [quizSettingsKey, settings]);

  return {
    settings,
    setSettings,
  };
}
