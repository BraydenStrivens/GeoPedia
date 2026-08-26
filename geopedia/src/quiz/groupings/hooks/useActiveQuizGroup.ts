/**
 * Owns the quiz group currently applied to a quiz and derives the geographic
 * features and quiz questions belonging to that group.
 *
 * The active group is temporary session state. Persistence of saved groups is
 * handled separately so loading, editing, and storing saved groups remain
 * independent from group resolution.
 *
 * This hook is responsible for:
 *
 * - Tracking the currently active group.
 * - Resolving that group into concrete feature IDs and quiz answers.
 * - Producing the filtered Quiz object consumed by the quiz engine.
 * - Restoring the complete unfiltered quiz.
 */

"use client";

import { useMemo, useState } from "react";

import type { MapConfig } from "@/maps/types";
import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/hooks/useQuizGroupingData";
import type {
  ActiveQuizGroup,
  ResolvedQuizGroup,
} from "@/quiz/groupings/types";
import { resolveQuizGroup } from "@/quiz/groupings/utils/resolveQuizGroup";
import type { Quiz } from "@/types/quiz";

/**
 * Default group representing the complete unfiltered quiz.
 */
const FULL_QUIZ_GROUP: ActiveQuizGroup = {
  type: "full",
};

/**
 * Values required to manage and resolve the active quiz group.
 */
type UseActiveQuizGroupParams = {
  /** Complete quiz definition. */
  quiz: Quiz;

  /** Map configuration associated with the quiz. */
  mapConfig: MapConfig;

  /** Loaded GeoJSON used to resolve group membership. */
  featureCollection: QuizGroupingFeatureCollection | null;
};

/**
 * Values returned by `useActiveQuizGroup`.
 */
type UseActiveQuizGroupResult = {
  /** Group currently applied to the quiz. */
  activeGroup: ActiveQuizGroup;

  /**
   * Concrete feature IDs and answers belonging to the active group.
   *
   * `null` indicates that the GeoJSON required to resolve the group has not
   * loaded yet.
   */
  resolvedGroup: ResolvedQuizGroup | null;

  /**
   * Quiz definition currently consumed by the quiz engine.
   *
   * Full Quiz returns the original quiz object. Filtered groups return a
   * derived quiz containing only questions belonging to the resolved group.
   */
  activeQuiz: Quiz;

  /** Applies a property-based, manually selected, or Full Quiz group. */
  applyGroup: (group: ActiveQuizGroup) => void;

  /** Restores the complete unfiltered quiz. */
  resetToFullQuiz: () => void;
};

/**
 * Manages the currently applied quiz group and derives its geographic and
 * question subsets.
 *
 * Non-full groups depend on the quiz's GeoJSON. Until that data has loaded,
 * `resolvedGroup` remains `null` and the derived quiz temporarily contains no
 * questions.
 *
 * @param params - Quiz, map configuration, and loaded GeoJSON.
 * @returns Active group state, resolved membership, filtered quiz, and controls.
 */
export function useActiveQuizGroup({
  quiz,
  mapConfig,
  featureCollection,
}: UseActiveQuizGroupParams): UseActiveQuizGroupResult {
  /** Group currently applied to this quiz session. */
  const [activeGroup, setActiveGroup] =
    useState<ActiveQuizGroup>(FULL_QUIZ_GROUP);

  /**
   * Resolves the active group into concrete geographic feature IDs and quiz
   * answers.
   *
   * Resolution is deferred until the quiz's GeoJSON has loaded.
   */
  const resolvedGroup = useMemo(() => {
    if (!featureCollection) {
      return null;
    }

    return resolveQuizGroup(
      featureCollection,
      quiz,
      mapConfig,
      activeGroup,
    );
  }, [featureCollection, quiz, mapConfig, activeGroup]);

  /**
   * Creates the Quiz definition consumed by the quiz engine.
   *
   * Full Quiz preserves the original Quiz object. Filtered groups preserve all
   * quiz metadata while replacing `questions` with only the questions whose
   * answers belong to the resolved geographic subset.
   */
  const activeQuiz = useMemo(() => {
    if (activeGroup.type === "full") {
      return quiz;
    }

    if (!resolvedGroup) {
      return {
        ...quiz,
        questions: [],
      };
    }

    return {
      ...quiz,

      questions: quiz.questions.filter((question) =>
        resolvedGroup.answers.has(question.answer),
      ),
    };
  }, [quiz, activeGroup, resolvedGroup]);

  /**
   * Applies a new active quiz group.
   *
   * @param group - Group that should control the quiz.
   */
  function applyGroup(group: ActiveQuizGroup): void {
    setActiveGroup(group);
  }

  /**
   * Restores the complete unfiltered quiz.
   */
  function resetToFullQuiz(): void {
    setActiveGroup(FULL_QUIZ_GROUP);
  }

  return {
    activeGroup,
    resolvedGroup,
    activeQuiz,
    applyGroup,
    resetToFullQuiz,
  };
}
