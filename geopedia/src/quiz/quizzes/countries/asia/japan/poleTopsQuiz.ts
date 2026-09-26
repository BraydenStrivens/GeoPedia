/**
 * Defines the Japan pole tops quiz.
 *
 * This quiz uses the shared Japan pole-meta regions map and asks the user to
 * identify regions by the tops of Japanese utility poles.
 *
 * The quiz contains 3 pole top questions for each of the 10 pole-meta regions,
 * for a total of 30 questions. Multiple questions can therefore correspond to
 * the same map region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { JAPAN_POLE_TOP_QUESTIONS } from "./data/poleMetaQuestions";

const JAPAN_POLE_TOPS_DESCRIPTION =
  `Learn Japan's 10 pole-meta regions by identifying utility pole tops. ` +
  `Includes ${JAPAN_POLE_TOP_QUESTIONS.length} questions, with 3 examples for each region.`;

export const japanPoleTopsQuiz: FeatureQuiz = {
  id: "japan-pole-tops",
  name: "Pole Tops",
  description: JAPAN_POLE_TOPS_DESCRIPTION,

  kind: "feature",
  mapId: "japan-pole-meta-regions",

  answerProperty: "pole_meta_region_ids",
  answerType: "multiple",

  imageSizeMultiplier: 2,

  questions: JAPAN_POLE_TOP_QUESTIONS,
};
