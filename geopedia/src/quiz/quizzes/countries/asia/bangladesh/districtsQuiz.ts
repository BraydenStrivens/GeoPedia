/**
 * Feature quiz for Bangladesh's 64 districts.
 * */
import type { FeatureQuiz } from "@/types/quiz";

import { BANGLADESH_DISTRICT_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn all ${BANGLADESH_DISTRICT_QUESTIONS.length.toLocaleString()} districts (zilas) of Bangladesh. Group by division to study smaller sets.`;

export const bangladeshDistrictsQuiz: FeatureQuiz = {
  id: "bangladesh-districts",
  name: "জেলা - Zila (Districts)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",

  mapId: "bangladesh-districts",
  answerProperty: "admin_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "division",
        label: "Division",
        valueType: "string",
      },
    ],
  },

  questions: BANGLADESH_DISTRICT_QUESTIONS,
};
