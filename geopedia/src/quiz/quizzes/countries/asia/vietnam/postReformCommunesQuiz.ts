/**
 * Quiz configuration for Vietnam's post-reform commune-level administrative
 * units.
 *
 * Commune-level units belong directly to provinces in the post-reform
 * two-tier administrative system and can be grouped by province.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_POST_REFORM_COMMUNE_QUESTIONS } from "./data/post-reform-admin";

const DESCRIPTION =
  `Learn all ${VIETNAM_POST_REFORM_COMMUNE_QUESTIONS.length.toLocaleString()} ` +
  `commune-level units of Vietnam after the 2025 reform. Districts were ` +
  `abolished, making these units the second administrative tier. Group the ` +
  `quiz by province for focused practice.`;

export const vietnamPostReformCommunesQuiz: FeatureQuiz = {
  id: "vietnam-post-reform-communes",
  name: "Xã, Phường & Đặc khu (Communes, Wards & Special Zones) — Post-Reform",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "vietnam-post-reform-communes",

  answerProperty: "commune_id",
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

  questions: VIETNAM_POST_REFORM_COMMUNE_QUESTIONS,
};
