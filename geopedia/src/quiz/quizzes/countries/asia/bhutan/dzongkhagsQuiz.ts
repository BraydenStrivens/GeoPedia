/**
 * Feature quiz for Bhutan's 20 dzongkhags (districts).
 *
 * Includes English and Dzongkha names.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { bhutanDzongkhagQuestions } from "./data/admin";

const DESCRIPTION =
  `Learn all ${bhutanDzongkhagQuestions.length} dzongkhags (districts) of Bhutan. ` +
  `Study their locations using English or Dzongkha names.`;

export const bhutanDzongkhagsQuiz: FeatureQuiz = {
  id: "bhutan-dzongkhags",
  name: "རྫོང་ཁག - Dzongkhags (Districts)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "bhutan-dzongkhags",

  answerProperty: "admin_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: bhutanDzongkhagQuestions,
};
