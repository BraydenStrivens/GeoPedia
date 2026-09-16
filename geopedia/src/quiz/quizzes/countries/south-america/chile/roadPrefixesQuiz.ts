/**
 * Defines Chile's regional road-letter prefix quiz.
 *
 * Some geographic areas contain more than one valid road prefix, so the quiz
 * uses multiple-answer feature matching.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CHILE_ROAD_PREFIXES } from "./data/roadPrefixes";

const CHILE_ROAD_PREFIX_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(CHILE_ROAD_PREFIXES).map(([prefix]) => ({
    answer: prefix,
  }));

const CHILE_ROAD_PREFIXES_DESCRIPTION =
  `Learn all ${CHILE_ROAD_PREFIX_QUESTIONS.length} regional road letter ` +
  `prefixes of Chile. These prefixes appear before route numbers, such as ` +
  `A-27, B-245, and Q-45.`;

export const chileRoadPrefixesQuiz: FeatureQuiz = {
  id: "chile-road-prefixes",
  name: "Road Prefixes",
  description: CHILE_ROAD_PREFIXES_DESCRIPTION,

  kind: "feature",
  mapId: "chile-road-prefixes",

  answerProperty: "road_prefixes",
  answerType: "multiple",

  questions: CHILE_ROAD_PREFIX_QUESTIONS,
};
