/**
 * Quiz for identifying the Dominican Republic's administrative regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { DOMINICAN_REPUBLIC_REGIONS_BY_ID } from "./data/admin";

const DOMINICAN_REPUBLIC_REGION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(DOMINICAN_REPUBLIC_REGIONS_BY_ID).map(
    ([answer, name]) => ({
      answer,
      display: name,
    }),
  );

const DOMINICAN_REPUBLIC_REGIONS_DESCRIPTION =
  `Learn all ${DOMINICAN_REPUBLIC_REGION_QUESTIONS.length} administrative ` +
  `regions of the Dominican Republic.`;

export const dominicanRepublicRegionsQuiz: FeatureQuiz = {
  id: "dominican-republic-regions",
  name: "Dominican Republic Regions",
  description: DOMINICAN_REPUBLIC_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "dominican-republic-regions",

  answerProperty: "region_id",
  answerType: "single",

  questions: DOMINICAN_REPUBLIC_REGION_QUESTIONS,
};
