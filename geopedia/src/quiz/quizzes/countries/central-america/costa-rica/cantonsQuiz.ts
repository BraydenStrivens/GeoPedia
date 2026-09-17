/**
 * Quiz for identifying Costa Rica's cantons.
 *
 * Cantons can be grouped by their parent province.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  COSTA_RICA_CANTONS_BY_ID,
  COSTA_RICA_PROVINCES_BY_ID,
} from "./data/admin";

const COSTA_RICA_CANTON_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COSTA_RICA_CANTONS_BY_ID).map(
    ([answer, canton]) => ({
      answer,
      display: canton.name,
    }),
  );

const COSTA_RICA_CANTONS_DESCRIPTION =
  `Learn all ${COSTA_RICA_CANTON_QUESTIONS.length} cantons of Costa Rica. ` +
  `Filters let you practice cantons by province.`;

export const costaRicaCantonsQuiz: FeatureQuiz = {
  id: "costa-rica-cantons",
  name: "Cantons",
  description: COSTA_RICA_CANTONS_DESCRIPTION,

  kind: "feature",
  mapId: "costa-rica-cantons",

  answerProperty: "canton_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCES_BY_ID,
      },
    ],
  },

  questions: COSTA_RICA_CANTON_QUESTIONS,
};
