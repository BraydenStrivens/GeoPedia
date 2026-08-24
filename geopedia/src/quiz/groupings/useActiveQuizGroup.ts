/**
 * Owns the quiz group currently applied to a quiz and derives the geographic
 * features and questions belonging to that group.
 *
 * The active group is temporary quiz state. Saved-group persistence will be
 * handled separately so loading or editing saved groups does not become
 * coupled to group resolution.
 */

"use client";

import { useMemo, useState } from "react";

import type { MapConfig } from "@/maps/types";
import { resolveQuizGroup } from "@/quiz/groupings/resolveQuizGroup";
import type {
  ActiveQuizGroup,
  ResolvedQuizGroup,
} from "@/quiz/groupings/types";
import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/useQuizGroupingData";
import type { Quiz } from "@/types/quiz";

/**
 * Default group representing the complete unfiltered quiz.
 */
const FULL_QUIZ_GROUP: ActiveQuizGroup = {
  type: "full",
};

/**
 * Values required to manage the active quiz group.
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

  /** Concrete features and answers belonging to the active group. */
  resolvedGroup: ResolvedQuizGroup | null;

  /** Quiz containing only questions belonging to the active group. */
  activeQuiz: Quiz;

  /** Applies a new group to the quiz. */
  applyGroup: (group: ActiveQuizGroup) => void;

  /** Restores the complete unfiltered quiz. */
  resetToFullQuiz: () => void;
};

/**
 * Manages the currently applied quiz group and derives its active question
 * subset.
 *
 * The original quiz object is returned unchanged for Full Quiz. Property and
 * manually selected groups create a derived quiz containing only questions
 * whose answers occur in the resolved geographic feature set.
 *
 * @param params - Quiz, map, and loaded GeoJSON required for group resolution.
 * @returns Active group, resolved membership, filtered quiz, and group controls.
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
   * Resolves the active group into concrete feature IDs and quiz answers.
   *
   * Non-full groups cannot be resolved until the GeoJSON has loaded.
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
   * Creates the quiz definition consumed by the quiz engine.
   *
   * Full Quiz preserves the original Quiz object. A filtered group keeps all
   * quiz metadata but replaces `questions` with only the answers belonging to
   * the resolved geographic subset.
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
        resolvedGroup?.answers.has(question.answer),
      ),
    };
  }, [quiz, activeGroup, resolvedGroup]);

  /**
   * Applies a property-based, manually selected, or Full Quiz group.
   *
   * Group application will later be exposed through the Groups sidebar.
   *
   * @param group - Group that should become active.
   */
  function applyGroup(group: ActiveQuizGroup): void {
    setActiveGroup(group);
  }

  /**
   * Restores the complete quiz.
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
