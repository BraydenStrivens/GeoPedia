/**
 * Quiz configuration for Indonesia's second-level kabupaten and kota.
 *
 * Regencies and cities can be grouped by region or province.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_REGENCY_QUESTIONS } from "./data/admin";

const INDONESIA_REGENCIES_DESCRIPTION =
  `Learn all ${INDONESIA_REGENCY_QUESTIONS.length} regencies and cities of Indonesia. ` +
  `They can be grouped by region or province for more focused practice.`;

export const indonesiaRegenciesQuiz: FeatureQuiz = {
  id: "indonesia-regencies",
  name: "Kabupaten & Kota (Regencies & Cities)",
  description: INDONESIA_REGENCIES_DESCRIPTION,

  kind: "feature",
  mapId: "indonesia-regencies",

  answerProperty: "regency_id",
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
    ],
  },

  questions: INDONESIA_REGENCY_QUESTIONS,
};
