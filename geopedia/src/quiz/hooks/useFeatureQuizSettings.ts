/**
 * Loads and persists user-configurable settings for an individual quiz.
 *
 * Settings for all quizzes are stored together in localStorage under one
 * shared storage entry. Each quiz is identified by a key built from its
 * country ID and quiz ID.
 */

"use client";

import { useEffect, useState } from "react";

import {
  DEFAULT_FEATURE_QUIZ_SETTINGS,
  type FeatureQuizSettings,
} from "@/types/featureQuizSettings";

/** localStorage key containing the feature quiz settings dictionary for every quiz. */
const FEATURE_QUIZ_SETTINGS_STORAGE_KEY = "feature-quiz-settings";

/** Dictionary of saved quiz settings keyed by country and quiz ID. */
type StoredQuizSettings = Record<string, FeatureQuizSettings>;

/**
 * Builds the unique localStorage dictionary key for a quiz.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Unique identifier of the quiz within that country.
 * @returns A stable key used to store and retrieve the quiz's settings.
 */
function createFeatureQuizSettingsKey(
  countryId: string,
  quizId: string,
): string {
  return `${countryId}_${quizId}`;
}

/**
 * Loads settings for one quiz and automatically persists future changes.
 *
 * Saved settings are merged over `defaultQuizSettings` when loaded. This
 * allows older localStorage entries to continue working after new settings
 * are added in later versions of GeoPedia.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Unique identifier of the quiz.
 * @returns The current settings and their React state setter.
 */
export function useFeatureQuizSettings(
  countryId: string,
  quizId: string,
) {
  const quizSettingsKey = createFeatureQuizSettingsKey(
    countryId,
    quizId,
  );

  /**
   * Loads the initial settings exactly once when this hook instance mounts.
   *
   * The lazy initializer avoids an extra render that would occur if settings
   * were first initialized with defaults and then replaced from an effect.
   */
  const [settings, setSettings] = useState<FeatureQuizSettings>(
    () => {
      if (typeof window === "undefined") {
        return DEFAULT_FEATURE_QUIZ_SETTINGS;
      }

      try {
        const storedValue = localStorage.getItem(
          FEATURE_QUIZ_SETTINGS_STORAGE_KEY,
        );

        if (!storedValue) {
          return DEFAULT_FEATURE_QUIZ_SETTINGS;
        }

        const storedSettings = JSON.parse(
          storedValue,
        ) as StoredQuizSettings;

        const savedQuizSettings = storedSettings[quizSettingsKey];

        if (!savedQuizSettings) {
          return DEFAULT_FEATURE_QUIZ_SETTINGS;
        }

        /*
         * Merge saved values over the current defaults so older saved
         * settings automatically receive newly-added properties.
         */
        return {
          ...DEFAULT_FEATURE_QUIZ_SETTINGS,
          ...savedQuizSettings,
        };
      } catch (error) {
        console.error("Failed to load quiz settings:", error);

        return DEFAULT_FEATURE_QUIZ_SETTINGS;
      }
    },
  );

  /**
   * Persists this quiz's settings whenever they change.
   *
   * Only this quiz's entry is replaced. Settings belonging to other quizzes
   * remain untouched in the shared localStorage dictionary.
   */
  useEffect(() => {
    try {
      const storedValue = localStorage.getItem(
        FEATURE_QUIZ_SETTINGS_STORAGE_KEY,
      );

      const storedSettings: StoredQuizSettings = storedValue
        ? JSON.parse(storedValue)
        : {};

      storedSettings[quizSettingsKey] = settings;

      localStorage.setItem(
        FEATURE_QUIZ_SETTINGS_STORAGE_KEY,
        JSON.stringify(storedSettings),
      );
    } catch (error) {
      console.error("Failed to save quiz settings:", error);
    }
  }, [settings, quizSettingsKey]);

  return {
    settings,
    setSettings,
  };
}
