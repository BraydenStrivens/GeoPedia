/**
 * Feature quiz configuration for Namibia's 14 regions.
 *
 * Region pcodes provide stable answer identity while region names are shown
 * to the player.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { NAMIBIA_REGIONS_QUIZ_QUESTIONS } from "./data/admin";

const NAMIBIA_REGIONS_DESCRIPTION = `Learn all ${NAMIBIA_REGIONS_QUIZ_QUESTIONS.length} regions of Namibia.`;

export const namibiaRegionsQuiz: FeatureQuiz = {
  id: "namibia-regions",
  name: "Regions",
  description: NAMIBIA_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "namibia-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  questions: NAMIBIA_REGIONS_QUIZ_QUESTIONS,
};
