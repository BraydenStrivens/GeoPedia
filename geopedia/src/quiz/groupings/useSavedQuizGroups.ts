/**
 * Loads and persists user-created quiz groups for an individual quiz.
 *
 * Saved groups are stored in localStorage and keyed by country ID and quiz ID
 * so each quiz maintains its own independent collection.
 */

"use client";

import { useEffect, useState } from "react";

import type {
  QuizGroupSource,
  SavedQuizGroup,
} from "@/quiz/groupings/types";

/**
 * localStorage key containing saved groups for every quiz.
 */
const STORAGE_KEY = "quiz-groups";

/**
 * Saved groups indexed by quiz-specific storage key.
 */
type StoredQuizGroups = Record<string, SavedQuizGroup[]>;

/**
 * Result returned by `useSavedQuizGroups`.
 */
type UseSavedQuizGroupsResult = {
  /** Groups currently saved for this quiz. */
  savedGroups: SavedQuizGroup[];

  /** Creates and persists a new saved group. */
  saveGroup: (
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ) => SavedQuizGroup;

  /** Updates an existing saved group's name and selection definition. */
  updateGroup: (
    groupId: string,
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ) => void;

  /** Permanently removes a saved group. */
  deleteGroup: (groupId: string) => void;
};

/**
 * Loads and manages user-created groups belonging to one quiz.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Quiz whose groups should be loaded.
 * @returns Saved groups and functions for creating, updating, and deleting them.
 */
export function useSavedQuizGroups(
  countryId: string,
  quizId: string,
): UseSavedQuizGroupsResult {
  const quizKey = `${countryId}_${quizId}`;

  /**
   * Saved groups belonging to the current quiz.
   */
  const [savedGroups, setSavedGroups] = useState<SavedQuizGroup[]>(
    () => {
      if (typeof window === "undefined") {
        return [];
      }

      try {
        const storedValue = localStorage.getItem(STORAGE_KEY);

        if (!storedValue) {
          return [];
        }

        const storedGroups = JSON.parse(
          storedValue,
        ) as StoredQuizGroups;

        return storedGroups[quizKey] ?? [];
      } catch (error) {
        console.error("Failed to load saved quiz groups:", error);

        return [];
      }
    },
  );

  /**
   * Persists this quiz's saved groups whenever the collection changes.
   */
  useEffect(() => {
    try {
      const storedValue = localStorage.getItem(STORAGE_KEY);

      const storedGroups: StoredQuizGroups = storedValue
        ? JSON.parse(storedValue)
        : {};

      storedGroups[quizKey] = savedGroups;

      localStorage.setItem(STORAGE_KEY, JSON.stringify(storedGroups));
    } catch (error) {
      console.error("Failed to save quiz groups:", error);
    }
  }, [quizKey, savedGroups]);

  /**
   * Creates and persists a new quiz group.
   *
   * @param name - User-facing name assigned to the group.
   * @param description - Optional explanation of the group's purpose.
   * @param source - Property or manual feature selection defining the group.
   * @returns The newly created saved group.
   */
  function saveGroup(
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ): SavedQuizGroup {
    const trimmedDescription = description?.trim();

    const newGroup: SavedQuizGroup = {
      id: crypto.randomUUID(),
      name: name.trim(),

      description: trimmedDescription || undefined,

      source,
    };

    setSavedGroups((previousGroups) => [...previousGroups, newGroup]);

    return newGroup;
  }

  /**
   * Updates an existing saved group's metadata and selection definition.
   *
   * @param groupId - Stable ID of the group being edited.
   * @param name - Updated user-facing group name.
   * @param description - Updated optional group description.
   * @param source - Updated group selection definition.
   */
  function updateGroup(
    groupId: string,
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ): void {
    const trimmedDescription = description?.trim();

    setSavedGroups((previousGroups) =>
      previousGroups.map((group) =>
        group.id === groupId
          ? {
              ...group,

              name: name.trim(),

              description: trimmedDescription || undefined,

              source,
            }
          : group,
      ),
    );
  }

  /**
   * Permanently removes a saved quiz group.
   *
   * @param groupId - Stable ID of the group to delete.
   */
  function deleteGroup(groupId: string): void {
    setSavedGroups((previousGroups) =>
      previousGroups.filter((group) => group.id !== groupId),
    );
  }

  return {
    savedGroups,
    saveGroup,
    updateGroup,
    deleteGroup,
  };
}
