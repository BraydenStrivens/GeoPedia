/**
 * Loads and persists user-created quiz groups for an individual quiz.
 *
 * Saved groups are stored in localStorage and keyed by country ID and quiz ID
 * so each quiz maintains its own independent collection.
 *
 * This hook owns:
 *
 * - Loading saved groups for one quiz.
 * - Creating saved groups.
 * - Updating saved groups.
 * - Deleting saved groups.
 * - Persisting changes back to localStorage.
 */

"use client";

import { useEffect, useState } from "react";

import type {
  QuizGroupSource,
  SavedQuizGroup,
} from "@/quiz/groupings/types";

/** localStorage key containing saved groups for every quiz. */
const STORAGE_KEY = "quiz-groups";

/** Saved groups indexed by a quiz-specific storage key. */
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

  /** Updates an existing saved group's metadata and selection definition. */
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
 * Builds the localStorage key used to identify one quiz's saved groups.
 *
 * @param countryId - Country containing the quiz.
 * @param quizId - Stable quiz ID.
 * @returns Quiz-specific storage key.
 */
function getQuizStorageKey(
  countryId: string,
  quizId: string,
): string {
  return `${countryId}_${quizId}`;
}

/**
 * Reads every saved quiz-group collection from localStorage.
 *
 * Invalid or unavailable storage falls back to an empty collection so quiz
 * grouping remains usable even if persisted data cannot be read.
 *
 * @returns Saved groups indexed by quiz-specific storage key.
 */
function readStoredQuizGroups(): StoredQuizGroups {
  if (typeof window === "undefined") {
    return {};
  }

  try {
    const storedValue = localStorage.getItem(STORAGE_KEY);

    if (!storedValue) {
      return {};
    }

    return JSON.parse(storedValue) as StoredQuizGroups;
  } catch (error) {
    console.error("Failed to load saved quiz groups:", error);

    return {};
  }
}

/**
 * Persists every saved quiz-group collection to localStorage.
 *
 * @param storedGroups - Saved groups indexed by quiz-specific storage key.
 */
function writeStoredQuizGroups(storedGroups: StoredQuizGroups): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(storedGroups));
  } catch (error) {
    console.error("Failed to save quiz groups:", error);
  }
}

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
  /** Storage key identifying the current quiz's saved-group collection. */
  const quizStorageKey = getQuizStorageKey(countryId, quizId);

  /** Saved groups belonging to the current quiz. */
  const [savedGroups, setSavedGroups] = useState<SavedQuizGroup[]>(
    () => {
      const storedGroups = readStoredQuizGroups();

      return storedGroups[quizStorageKey] ?? [];
    },
  );

  /**
   * Persists the current quiz's saved groups whenever its collection changes.
   *
   * Other quizzes stored under the same top-level localStorage key are
   * preserved.
   */
  useEffect(() => {
    const storedGroups = readStoredQuizGroups();

    storedGroups[quizStorageKey] = savedGroups;

    writeStoredQuizGroups(storedGroups);
  }, [quizStorageKey, savedGroups]);

  /**
   * Creates and persists a new saved quiz group.
   *
   * @param name - User-facing name assigned to the group.
   * @param description - Optional explanation of the group's purpose.
   * @param source - Property or manual feature selection defining the group.
   * @returns Newly created saved group.
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
   * Groups whose IDs do not match remain unchanged.
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
