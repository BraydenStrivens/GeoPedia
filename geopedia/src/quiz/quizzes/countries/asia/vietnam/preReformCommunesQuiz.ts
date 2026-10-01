/**
 * Quiz configuration for Vietnam's pre-reform commune-level administrative
 * units.
 *
 * Units can be grouped by province or district for focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_PRE_REFORM_COMMUNE_QUESTIONS } from "./data/pre-reform-admin";

const DESCRIPTION =
  `Learn all ${VIETNAM_PRE_REFORM_COMMUNE_QUESTIONS.length.toLocaleString()} ` +
  `commune-level units of Vietnam before the 2025 reform. Older GeoGuessr ` +
  `coverage reflects this three-tier system. Group the quiz by province or ` +
  `district for focused practice.`;

export const vietnamPreReformCommunesQuiz: FeatureQuiz = {
  id: "vietnam-pre-reform-communes",
  name: "Xã, Phường & Thị trấn (Communes, Wards & Towns) — Pre-Reform",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "vietnam-pre-reform-communes",

  answerProperty: "commune_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: VIETNAM_PRE_REFORM_COMMUNE_QUESTIONS,
};
