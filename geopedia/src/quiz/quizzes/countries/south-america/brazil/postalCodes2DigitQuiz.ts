/**
 * Quiz configuration for Brazil's 2-digit CEP postal-code prefixes.
 *
 * Some geographic features represent multiple valid prefixes, so the quiz
 * uses GeoPedia's multiple-answer feature semantics. Questions can be grouped
 * by first digit or state.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_POSTAL_CODE_QUESTIONS } from "./data/postalCodes";
import { BRAZIL_STATE_NAMES_BY_ABBREVIATION } from "./data/stateAbbreviations";

const BRAZIL_POSTAL_CODES_DESCRIPTION =
  `Learn Brazil's ${BRAZIL_POSTAL_CODE_QUESTIONS.length} 2-digit postal code prefixes and where they are located across the country. ` +
  `Brazilian postal codes, known as CEPs, contain 8 digits and are written in the format 12345-678. ` +
  `This quiz focuses on the first 2 digits of each CEP. For example, 01001-000 is shown as 01--- in the quiz.`;

export const brazilPostalCodes2DigitQuiz: FeatureQuiz = {
  id: "brazil-postal-codes",
  name: "2 Digit Postal Codes",
  description: BRAZIL_POSTAL_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-postal-codes",

  answerProperty: "postal_codes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "first_digits",
        label: "First Digit",
        valueType: "string-array",
      },
      {
        property: "states",
        label: "State",
        valueType: "string-array",
        valueLabels: BRAZIL_STATE_NAMES_BY_ABBREVIATION,
      },
    ],
  },

  questions: BRAZIL_POSTAL_CODE_QUESTIONS,
};
