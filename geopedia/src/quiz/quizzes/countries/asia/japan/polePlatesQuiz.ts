/**
 * Defines the Japan pole plates quiz.
 *
 * This quiz uses the shared Japan pole-meta regions map and asks the user to
 * identify regions by the identification plates found on Japanese utility
 * poles.
 *
 * The quiz contains 3 pole plate questions for each of the 10 pole-meta
 * regions, for a total of 30 questions. Multiple questions can therefore
 * correspond to the same map region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { JAPAN_POLE_PLATE_QUESTIONS } from "./data/poleMetaQuestions";

const JAPAN_POLE_PLATES_DESCRIPTION =
  `Learn Japan's 10 pole-meta regions by identifying utility pole plates. ` +
  `Includes ${JAPAN_POLE_PLATE_QUESTIONS.length} questions, with 3 examples for each region.`;

export const japanPolePlatesQuiz: FeatureQuiz = {
  id: "japan-pole-plates",
  name: "Pole Plates",
  description: JAPAN_POLE_PLATES_DESCRIPTION,

  kind: "feature",
  mapId: "japan-pole-meta-regions",

  answerProperty: "pole_meta_region_ids",
  answerType: "multiple",

  imageSizeMultiplier: 2,

  questions: JAPAN_POLE_PLATE_QUESTIONS,
};
