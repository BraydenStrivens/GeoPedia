/**
 * Feature quiz for the Philippines' municipalities and cities.
 *
 * Municipalities and cities can be grouped by region or their immediate
 * province / province-level parent.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PHILIPPINES_MUNICIPALITY_CITY_QUESTIONS } from "./data/municipalities-cities";

const DESCRIPTION =
  `Learn all ${PHILIPPINES_MUNICIPALITY_CITY_QUESTIONS.length} ` +
  `municipalities and cities of the Philippines.\n\n` +
  `Group the quiz by region or province to break the country into smaller ` +
  `sets.`;

export const philippinesMunicipalitiesCitiesQuiz: FeatureQuiz = {
  id: "philippines-municipalities-cities",
  name: "Municipalities and Cities",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "philippines-municipalities-cities",

  answerProperty: "municipality_city_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
    ],
  },

  questions: PHILIPPINES_MUNICIPALITY_CITY_QUESTIONS,
};
