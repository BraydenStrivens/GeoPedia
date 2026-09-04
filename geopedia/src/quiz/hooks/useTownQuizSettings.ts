/**
 * Loads and persists user settings for GeoPedia town quizzes.
 *
 * Town quiz settings are stored in browser localStorage and scoped by both
 * country ID and quiz ID so every quiz can retain its own configuration.
 *
 * This hook is expected to run only after GeoPedia's existing quiz hydration
 * boundary has completed. That prevents server rendering from accessing
 * localStorage and ensures the map is initially created using the persisted
 * settings rather than briefly rendering defaults.
 */

"use client";

import {
  type Dispatch,
  type SetStateAction,
  useCallback,
  useMemo,
  useState,
} from "react";

import {
  DEFAULT_TOWN_QUIZ_SETTINGS,
  type TownQuizSettings,
} from "@/types/townQuizSettings";

/** localStorage key containing the town quiz settings dictionary for every quiz. */
const TOWN_QUIZ_SETTINGS_STORAGE_KEY = "town-quiz-settings";

/**
 * Result returned by `useTownQuizSettings`.
 */
type UseTownQuizSettingsResult = {
  /** Current persisted town settings. */
  settings: TownQuizSettings;

  /**
   * React-compatible settings setter.
   *
   * Both direct objects and functional updates are supported.
   */
  setSettings: Dispatch<SetStateAction<TownQuizSettings>>;
};

/**
 * Builds the localStorage key belonging to one country quiz.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Unique town quiz identifier.
 * @returns Stable localStorage key.
 */
function getStorageKey(countryId: string, quizId: string): string {
  return [
    TOWN_QUIZ_SETTINGS_STORAGE_KEY,
    countryId.toLowerCase(),
    quizId.toLowerCase(),
  ].join(":");
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
 * Parses persisted settings while safely falling back field-by-field.
 *
 * Field-level fallbacks make settings forward-compatible. If a future version
 * adds or changes one setting, valid existing values can still be retained.
 *
 * @param rawValue - Raw localStorage string.
 * @returns Validated town quiz settings.
 */
function parseStoredSettings(
  rawValue: string | null,
): TownQuizSettings {
  if (!rawValue) {
    return {
      ...DEFAULT_TOWN_QUIZ_SETTINGS,
    };
  }

  try {
    const parsed = JSON.parse(rawValue) as Record<string, unknown>;

    return {
      mode: isTownQuizMode(parsed.mode)
        ? parsed.mode
        : DEFAULT_TOWN_QUIZ_SETTINGS.mode,

      questionLanguage: isQuestionLanguage(parsed.questionLanguage)
        ? parsed.questionLanguage
        : DEFAULT_TOWN_QUIZ_SETTINGS.questionLanguage,

      showLabels:
        typeof parsed.showLabels === "boolean"
          ? parsed.showLabels
          : DEFAULT_TOWN_QUIZ_SETTINGS.showLabels,
    };
  } catch {
    return {
      ...DEFAULT_TOWN_QUIZ_SETTINGS,
    };
  }
}

/**
 * Loads and persists settings belonging to one town quiz.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Town quiz identifier.
 * @returns Current settings and a persistence-aware setter.
 */
export function useTownQuizSettings(
  countryId: string,
  quizId: string,
): UseTownQuizSettingsResult {
  const storageKey = useMemo(
    () => getStorageKey(countryId, quizId),
    [countryId, quizId],
  );

  /**
   * The surrounding quiz hydration boundary guarantees this initializer runs in
   * the browser, where localStorage is available.
   */
  const [settings, setSettingsState] = useState<TownQuizSettings>(
    () =>
      parseStoredSettings(window.localStorage.getItem(storageKey)),
  );

  /**
   * Persists every settings update at the same time React state changes.
   */
  const setSettings = useCallback<
    Dispatch<SetStateAction<TownQuizSettings>>
  >(
    (nextSettings) => {
      setSettingsState((currentSettings) => {
        const resolvedSettings =
          typeof nextSettings === "function"
            ? nextSettings(currentSettings)
            : nextSettings;

        window.localStorage.setItem(
          storageKey,
          JSON.stringify(resolvedSettings),
        );

        return resolvedSettings;
      });
    },
    [storageKey],
  );

  return {
    settings,
    setSettings,
  };
}
