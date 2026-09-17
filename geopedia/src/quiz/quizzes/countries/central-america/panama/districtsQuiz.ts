/**
 * Quiz for identifying Panama's districts.
 *
 * Districts can be grouped by their parent province or comarca.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PANAMA_DISTRICTS_BY_ID,
  PANAMA_PROVINCES_COMARCAS_BY_ID,
} from "./data/admin";

const PANAMA_DISTRICT_QUESTIONS = Object.entries(
  PANAMA_DISTRICTS_BY_ID,
).map(([id, district]) => ({
  answer: id,
  display: district.name,
}));

export const panamaDistrictsQuiz: FeatureQuiz = {
  id: "panama-districts",
  name: "Districts",
  description: `Learn all ${PANAMA_DISTRICT_QUESTIONS.length} districts of Panama, with filters that let you practice districts by province or comarca.`,

  kind: "feature",
  mapId: "panama-districts",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "provinceId",
        label: "Province / Comarca",
        valueType: "string",
        valueLabels: PANAMA_PROVINCES_COMARCAS_BY_ID,
      },
    ],
  },

  questions: PANAMA_DISTRICT_QUESTIONS,
};
