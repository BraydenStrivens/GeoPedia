/**
 * Quiz configuration for Indonesia's fourth-level desa.
 *
 * Villages can be grouped by region, province, regency/city, or sub-district.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_VILLAGE_QUESTIONS } from "./data/villages";

const INDONESIA_VILLAGES_DESCRIPTION =
  `Learn all ${INDONESIA_VILLAGE_QUESTIONS.length.toLocaleString()} villages of ` +
  `Indonesia. They can be grouped by region, province, ` +
  `regency/city, or sub-district for more focused practice.`;

export const indonesiaVillagesQuiz: FeatureQuiz = {
  id: "indonesia-villages",
  name: "Desa (Villages)",
  description: INDONESIA_VILLAGES_DESCRIPTION,

  kind: "feature",
  quizTopic: "Administrative Regions",
  mapId: "indonesia-villages",

  answerProperty: "village_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "regency",
        label: "Regency / City",
        valueType: "string",
      },
      {
        property: "sub_district",
        label: "Sub-District",
        valueType: "string",
      },
    ],
  },

  questions: INDONESIA_VILLAGE_QUESTIONS,
};
