/**
 * Feature quiz for Bangladesh's 544 upazilas.
 * */
import type { FeatureQuiz } from "@/types/quiz";

import { BANGLADESH_UPAZILA_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn all ${BANGLADESH_UPAZILA_QUESTIONS.length.toLocaleString()} upazilas and thanas of Bangladesh. Group by division or district to study smaller sets.`;

export const bangladeshUpazilasQuiz: FeatureQuiz = {
  id: "bangladesh-upazilas",
  name: "Upazilas / Thanas",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "bangladesh-upazilas",

  answerProperty: "admin_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "division",
        label: "Division",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: BANGLADESH_UPAZILA_QUESTIONS,
};
