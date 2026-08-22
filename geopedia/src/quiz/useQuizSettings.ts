"use client";

/**
 * Loads and persists quiz settings for an individual quiz.
 *
 * Settings for all quizzes are stored together in localStorage and keyed
 * by country ID and quiz ID.
 */

import { useEffect, useState } from "react";

import {
  defaultQuizSettings,
  type QuizSettings,
} from "@/types/quizSettings";

const STORAGE_KEY = "quiz-settings";

type StoredQuizSettings = Record<string, QuizSettings>;

/**
 * Returns settings for one quiz and automatically persists changes.
 */
export function useQuizSettings(countryId: string, quizId: string) {
  const quizKey = `${countryId}_${quizId}`;

  const [settings, setSettings] = useState<QuizSettings>(() => {
    if (typeof window === "undefined") {
      return defaultQuizSettings;
    }

    try {
      const storedValue = localStorage.getItem(STORAGE_KEY);

      if (!storedValue) {
        return defaultQuizSettings;
      }

      const storedSettings = JSON.parse(storedValue) as StoredQuizSettings;

      const quizSettings = storedSettings[quizKey];

      if (!quizSettings) {
        return defaultQuizSettings;
      }

      /*
       * Merge saved settings over the defaults so older localStorage
       * entries automatically receive any settings added in the future.
       */
      return {
        ...defaultQuizSettings,
        ...quizSettings,
      };
    } catch (error) {
      console.error("Failed to load quiz settings:", error);

      return defaultQuizSettings;
    }
  });

  /*
   * Persist this quiz's settings whenever they change.
   */
  useEffect(() => {
    try {
      const storedValue = localStorage.getItem(STORAGE_KEY);

      const storedSettings: StoredQuizSettings = storedValue
        ? JSON.parse(storedValue)
        : {};

      storedSettings[quizKey] = settings;

      localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSettings));
    } catch (error) {
      console.error("Failed to save quiz settings:", error);
    }
  }, [settings, quizKey]);

  return {
    settings,
    setSettings,
  };
}
