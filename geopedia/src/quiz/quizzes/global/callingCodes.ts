/**
 * Tests recognition of countries and territories from their international
 * calling codes.
 *
 * A calling code may belong to more than one geographic feature. Selecting any
 * feature whose `calling_codes` property contains the current answer is
 * considered a valid selection.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CALLING_CODE_QUESTIONS } from "./data/callingCodes";

const CALLING_CODES_DESCRIPTION =
  `Identify all ${CALLING_CODE_QUESTIONS.length} unique country calling codes, with filters ` +
  `for GeoGuessr countries only, continent, region, and subregion.`;

export const callingCodesQuiz: FeatureQuiz = {
  id: "calling-codes",
  name: "Calling Codes",
  description: CALLING_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "world-countries",

  answerProperty: "calling_codes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "continent",
        label: "Continent",
        valueType: "string",
      },
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "subregion",
        label: "Subregion",
        valueType: "string",
      },
    ],
  },

  questions: CALLING_CODE_QUESTIONS,
};
