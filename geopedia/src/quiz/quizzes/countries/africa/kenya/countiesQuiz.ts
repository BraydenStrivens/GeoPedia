/**
 * Feature quiz for Kenya's 47 counties.
 *
 * Questions use each county's stable canonical ID as the answer and its
 * county name as the player-facing display.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { KENYA_COUNTIES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  KENYA_COUNTIES_BY_ID,
).map(([countyId, county]) => ({
  answer: countyId,
  display: county.name,
}));

const DESCRIPTION = `Learn all ${QUESTIONS.length} counties of Kenya.`;

export const kenyaCountiesQuiz: FeatureQuiz = {
  id: "kenya-counties",
  name: "Counties",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "kenya-counties",

  answerProperty: "county_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  questions: QUESTIONS,
};
