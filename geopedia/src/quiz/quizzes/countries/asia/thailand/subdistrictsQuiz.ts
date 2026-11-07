/**
 * Feature quiz for Thailand's 7,425 subdistrict-level divisions.
 *
 * Includes tambon throughout the provinces and khwaeng in Bangkok.
 * Questions can be grouped by province and district.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { THAILAND_SUBDISTRICT_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${THAILAND_SUBDISTRICT_QUESTIONS.length.toLocaleString()} subdistrict-level divisions of Thailand. ` +
  `Most are tambon (subdistricts), while Bangkok uses khwaeng. Group them by province or district to study smaller sets.`;

export const thailandSubdistrictsQuiz: FeatureQuiz = {
  id: "thailand-subdistricts",
  name: "ตำบล - Tambon (Subdistricts)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "thailand-subdistricts",

  answerProperty: "subdistrict_id",
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

  questions: THAILAND_SUBDISTRICT_QUESTIONS,
};
