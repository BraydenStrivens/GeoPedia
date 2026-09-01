/**
 * Converts manually selected geographic feature IDs into display information
 * used by the Groups panel.
 *
 * Each selected map feature becomes one list item containing:
 *
 * - Its stable geographic feature ID.
 * - Every quiz answer represented by that feature.
 *
 * Feature identity and quiz-answer normalization reuse the same helpers used by
 * quiz-group resolution so the manual-selection UI cannot drift from the data
 * actually used by the active quiz.
 */

import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/feature/hooks/useQuizGroupingData";
import {
  getFeatureQuizAnswers,
  getGroupableFeatureId,
} from "@/quiz/groupings/feature/utils/groupingFeatures";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Display information for one manually selected geographic feature.
 */
export type ManualSelectionItem = {
  /** Stable geographic feature ID stored by the manual group. */
  featureId: string;

  /** Quiz answers represented by this geographic feature. */
  answers: string[];
};

/**
 * Builds display items for the geographic features currently selected by the
 * manual-group workflow.
 *
 * Selected feature IDs are matched using the same stable-ID rules as normal
 * quiz-group resolution. Quiz answers are likewise normalized through the
 * shared feature-answer helper.
 *
 * @param featureCollection - Complete GeoJSON dataset used by the quiz.
 * @param promoteId - Optional GeoJSON property promoted by MapLibre to feature.id.
 * @param quiz - Quiz whose answer property should be displayed.
 * @param selectedFeatureIds - Stable feature IDs currently selected by the user.
 * @returns Selected features together with their represented quiz answers.
 */
export function getManualSelectionItems(
  featureCollection: QuizGroupingFeatureCollection | null,
  promoteId: string | undefined,
  quiz: FeatureQuiz,
  selectedFeatureIds: ReadonlySet<string>,
): ManualSelectionItem[] {
  if (!featureCollection || selectedFeatureIds.size === 0) {
    return [];
  }

  const items: ManualSelectionItem[] = [];

  for (const feature of featureCollection.features) {
    const featureId = getGroupableFeatureId(feature, promoteId);

    if (!featureId || !selectedFeatureIds.has(featureId)) {
      continue;
    }

    items.push({
      featureId,

      answers: getFeatureQuizAnswers(feature, quiz.answerProperty),
    });
  }

  return items;
}
