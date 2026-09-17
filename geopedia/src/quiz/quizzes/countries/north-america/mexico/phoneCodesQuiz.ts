/**
 * Quiz configuration for Mexico's geographic telephone area codes.
 *
 * Geographic features may contain multiple valid area codes, so the quiz
 * uses GeoPedia's multiple-answer feature semantics. Questions can be grouped
 * by first digit or state.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { MEXICO_STATES_BY_ID } from "./data/admin";
import { MEXICO_PHONE_CODE_QUESTIONS } from "./data/phoneCodes";

const MEXICO_PHONE_CODES_DESCRIPTION =
  `Learn all ${MEXICO_PHONE_CODE_QUESTIONS.length} Mexican phone codes, with ` +
  `filtering options to practice by first digit, state, or any desired subset. ` +
  `Mexican phone numbers contain 10 digits: 2-digit area codes are followed by ` +
  `an 8-digit local number, while 3-digit area codes are followed by a 7-digit ` +
  `local number.`;

export const mexicoPhoneCodesQuiz: FeatureQuiz = {
  id: "mexico-phone-codes",
  name: "Phone Codes",
  description: MEXICO_PHONE_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-phone-codes",

  answerProperty: "area_codes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "first_digit",
        label: "First Digit",
        valueType: "string",
      },
      {
        property: "state_ids",
        label: "State",
        valueType: "string-array",
        valueLabels: MEXICO_STATES_BY_ID,
      },
    ],
  },

  questions: MEXICO_PHONE_CODE_QUESTIONS,
};
