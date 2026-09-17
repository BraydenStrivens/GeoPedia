/**
 * Quiz for identifying Costa Rica's 5-digit postal codes.
 *
 * Postal codes correspond directly to district IDs and can be grouped
 * by province or canton.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  COSTA_RICA_CANTONS_BY_ID,
  COSTA_RICA_DISTRICTS_BY_ID,
  COSTA_RICA_PROVINCES_BY_ID,
} from "./data/admin";

const COSTA_RICA_POSTAL_CODE_QUESTIONS: FeatureQuiz["questions"] =
  Object.keys(COSTA_RICA_DISTRICTS_BY_ID).map((answer) => ({
    answer,
  }));

const COSTA_RICA_CANTON_NAME_VALUE_LABELS = Object.fromEntries(
  Object.entries(COSTA_RICA_CANTONS_BY_ID).map(
    ([cantonId, canton]) => [cantonId, canton.name],
  ),
);

const COSTA_RICA_POSTAL_CODES_DESCRIPTION =
  `Learn all ${COSTA_RICA_POSTAL_CODE_QUESTIONS.length} 5-digit postal codes ` +
  `of Costa Rica. Filters let you practice postal codes by province or canton.`;

export const costaRicaPostalCodesQuiz: FeatureQuiz = {
  id: "costa-rica-postal-codes",
  name: "5 Digit Postal Codes",
  description: COSTA_RICA_POSTAL_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "costa-rica-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCES_BY_ID,
      },
      {
        property: "canton_id",
        label: "Canton",
        valueType: "string",
        valueLabels: COSTA_RICA_CANTON_NAME_VALUE_LABELS,
      },
    ],
  },

  questions: [...COSTA_RICA_POSTAL_CODE_QUESTIONS],
};
