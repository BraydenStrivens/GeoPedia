/**
 * Feature quiz for Bhutan's 205 gewogs (subdistricts).
 *
 * Uses English names and supports grouping by dzongkhag.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { bhutanGewogQuestions } from "./data/admin";

const DESCRIPTION =
  `Learn all ${bhutanGewogQuestions.length} gewogs (subdistricts) of Bhutan. ` +
  `Group them by dzongkhag to study smaller sets.`;

export const bhutanGewogsQuiz: FeatureQuiz = {
  id: "bhutan-gewogs",
  name: "རྒེད་འོག - Gewogs (Subdistricts)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "bhutan-gewogs",

  answerProperty: "admin_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "dzongkhag",
        label: "Dzongkhag",
        valueType: "string",
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: bhutanGewogQuestions,
};
