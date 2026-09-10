import type { FeatureQuiz } from "@/types/quiz";

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
 * Maps the raw province / territory abbreviations stored in the GeoJSON to
 * user-facing labels shown by the Property Groups interface.
 *
 * The processed phone-code dataset stores province membership as a string
 * array because some telephone regions span multiple jurisdictions.
 */
const CANADIAN_SUBDIVISION_NAMES_BY_ABBREVIATION: Record<
  string,
  string
> = {
  AB: "Alberta",
  BC: "British Columbia",
  MB: "Manitoba",
  NB: "New Brunswick",
  NL: "Newfoundland and Labrador",
  NS: "Nova Scotia",
  NT: "Northwest Territories",
  NU: "Nunavut",
  ON: "Ontario",
  PE: "Prince Edward Island",
  QC: "Quebec",
  SK: "Saskatchewan",
  YT: "Yukon",
};

/**
 * User-facing description derived from the question array so it remains
 * accurate if the legacy area-code set changes later.
 */
const CANADA_PHONE_CODES_DESCRIPTION = `Learn ${CANADA_PHONE_CODE_QUESTIONS.length} geographically distinct Canadian telephone area-code regions, with province and territory filtering to practice any desired subset.`;

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
        valueLabels: CANADIAN_SUBDIVISION_NAMES_BY_ABBREVIATION,
      },
    ],
  },

  questions: CANADA_PHONE_CODE_QUESTIONS,
};
