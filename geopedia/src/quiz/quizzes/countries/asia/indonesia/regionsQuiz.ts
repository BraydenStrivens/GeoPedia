/**
 * Quiz configuration for Indonesia's seven major geographic regions.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_REGION_QUESTIONS } from "./data/admin";

const INDONESIA_REGIONS_DESCRIPTION = `Learn the ${INDONESIA_REGION_QUESTIONS.length} major geographic regions of Indonesia.`;

export const indonesiaRegionsQuiz: FeatureQuiz = {
  id: "indonesia-regions",
  name: "Wilayah (Regions)",
  description: INDONESIA_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "indonesia-regions",

  answerProperty: "region_id",
  answerType: "single",

  questions: INDONESIA_REGION_QUESTIONS,
};
