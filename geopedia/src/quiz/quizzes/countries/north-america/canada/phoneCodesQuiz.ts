import type { FeatureQuiz } from "@/types/quiz";

import { CANADA_PROVINCE_NAMES_BY_ABBREVIATION } from "./provincesQuiz";

/**
 * All legacy Canadian telephone area codes represented by the processed
 * Canada phone-code GeoJSON.
 *
 * These 19 regions are geographically distinct and useful for GeoGuessr-style
 * learning. Modern overlay codes are intentionally excluded because they share
 * the same geographic regions as older area codes and therefore do not add new
 * map geography to identify.
 */
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

/**
 * User-facing description derived from the question array so it remains
 * accurate if the legacy area-code set changes later.
 */
const CANADA_PHONE_CODES_DESCRIPTION =
  `Learn ${CANADA_PHONE_CODE_QUESTIONS.length} geographically distinct legacy ` +
  `Canadian telephone area-code regions, with province and territory filtering ` +
  `to practice any desired subset. In a Canadian phone number such as ` +
  `(204) 555-1234, the three-digit area code appears before the seven-digit ` +
  `local number. `;

/**
 * Quiz definition for identifying Canada's legacy telephone area-code regions.
 *
 * Each GeoJSON feature represents one three-digit area code. Province and
 * territory grouping uses the feature's `provinces` string-array property, so
 * multi-jurisdiction regions such as 902 and 867 appear under every province or
 * territory they belong to.
 */
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
