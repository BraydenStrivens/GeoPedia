/**
 * Feature quiz for Bangladesh's 8 divisions.
 */
import type { FeatureQuiz } from "@/types/quiz";

import { BANGLADESH_DIVISION_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn all ${BANGLADESH_DIVISION_QUESTIONS.length.toLocaleString()} divisions of Bangladesh.`;

export const bangladeshDivisionsQuiz: FeatureQuiz = {
  id: "bangladesh-divisions",
  name: "বিভাগ - Bibhag (Divisions)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "bangladesh-divisions",

  answerProperty: "admin_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: BANGLADESH_DIVISION_QUESTIONS,
};
