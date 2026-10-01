/**
 * Quiz configuration for Vietnam's pre-reform second-level districts.
 *
 * Districts can be grouped by their parent province for focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_PRE_REFORM_DISTRICT_QUESTIONS } from "./data/pre-reform-admin";

const DESCRIPTION =
  `Learn all ${VIETNAM_PRE_REFORM_DISTRICT_QUESTIONS.length.toLocaleString()} ` +
  `districts of Vietnam before the 2025 reform, which abolished the district ` +
  `level. These boundaries remain useful for GeoGuessr coverage before 2025. ` +
  `Group the quiz by province for focused practice.`;

export const vietnamPreReformDistrictsQuiz: FeatureQuiz = {
  id: "vietnam-pre-reform-districts",
  name: "Huyện (Districts) — Pre-Reform",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "vietnam-pre-reform-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
    ],
  },

  questions: VIETNAM_PRE_REFORM_DISTRICT_QUESTIONS,
};
