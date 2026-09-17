/**
 * Quiz for identifying Costa Rica's districts.
 *
 * Districts can be grouped by province or canton. Duplicate district names
 * are disambiguated by their canton.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  COSTA_RICA_CANTONS_BY_ID,
  COSTA_RICA_DISTRICTS_BY_ID,
  COSTA_RICA_PROVINCES_BY_ID,
} from "./data/admin";

const COSTA_RICA_DISTRICT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COSTA_RICA_DISTRICTS_BY_ID).map(
    ([answer, district]) => ({
      answer,
      display: district.name,
    }),
  );

const COSTA_RICA_CANTON_NAME_VALUE_LABELS = Object.fromEntries(
  Object.entries(COSTA_RICA_CANTONS_BY_ID).map(
    ([cantonId, canton]) => [cantonId, canton.name],
  ),
);

const COSTA_RICA_DISTRICTS_DESCRIPTION =
  `Learn all ${COSTA_RICA_DISTRICT_QUESTIONS.length} districts of Costa Rica. ` +
  `Filters let you practice districts by province or canton.`;

export const costaRicaDistrictsQuiz: FeatureQuiz = {
  id: "costa-rica-districts",
  name: "Districts",
  description: COSTA_RICA_DISTRICTS_DESCRIPTION,

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

  questions: [...COSTA_RICA_DISTRICT_QUESTIONS],
};
