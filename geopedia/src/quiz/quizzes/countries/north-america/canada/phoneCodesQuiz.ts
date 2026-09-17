/**
 * Quiz configuration for Canada's geographic telephone area codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CANADA_PROVINCE_NAMES_BY_ABBREVIATION } from "./provincesQuiz";

const CANADA_PHONE_CODE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "204" },
  { answer: "250" },
  { answer: "306" },
  { answer: "403" },
  { answer: "416" },
  { answer: "418" },
  { answer: "450" },
  { answer: "506" },
  { answer: "514" },
  { answer: "519" },
  { answer: "604" },
  { answer: "613" },
  { answer: "705" },
  { answer: "709" },
  { answer: "780" },
  { answer: "819" },
  { answer: "867" },
  { answer: "902" },
  { answer: "905" },
];

const CANADA_PHONE_CODES_DESCRIPTION =
  `Learn ${CANADA_PHONE_CODE_QUESTIONS.length} geographically distinct legacy ` +
  `Canadian telephone area-code regions, with province and territory filtering ` +
  `to practice any desired subset. In a Canadian phone number such as ` +
  `(204) 555-1234, the three-digit area code appears before the seven-digit ` +
  `local number. `;

export const canadaPhoneCodesQuiz: FeatureQuiz = {
  id: "canada-phone-codes",
  name: "Phone Codes",
  description: CANADA_PHONE_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "canada-phone-codes",

  answerProperty: "area_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "provinces",
        label: "Province / Territory",
        valueType: "string-array",
        valueLabels: CANADA_PROVINCE_NAMES_BY_ABBREVIATION,
      },
    ],
  },

  questions: CANADA_PHONE_CODE_QUESTIONS,
};
