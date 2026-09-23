/**
 * Feature quiz for São Tomé and Príncipe's two provinces.
 */

import type { FeatureQuiz } from "@/types/quiz";

const QUESTIONS: FeatureQuiz["questions"] = [
  {
    answer: "ST-P",
    display: "Príncipe Province",
  },
  {
    answer: "ST-S",
    display: "São Tomé Province",
  },
];

const DESCRIPTION = `Learn both provinces of São Tomé and Príncipe.`;

export const saoTomeAndPrincipeProvincesQuiz: FeatureQuiz = {
  id: "sao-tome-and-principe-provinces",
  name: "Provinces",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "sao-tome-and-principe-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: QUESTIONS,
};
