import type { FeatureQuiz } from "@/types/quiz";

/**
 * Maps Canadian province and territory abbreviations to their full
 * user-facing names.
 */
export const CANADA_PROVINCE_NAMES_BY_ABBREVIATION = {
  NL: "Newfoundland and Labrador",
  PE: "Prince Edward Island",
  NS: "Nova Scotia",
  NB: "New Brunswick",
  QC: "Quebec",
  ON: "Ontario",
  MB: "Manitoba",
  SK: "Saskatchewan",
  AB: "Alberta",
  BC: "British Columbia",
  YT: "Yukon",
  NT: "Northwest Territories",
  NU: "Nunavut",
} as const;

/**
 * Questions for Canada's provinces and territories quiz.
 */
const CANADA_PROVINCE_QUESTIONS: FeatureQuiz["questions"] =
  Object.values(CANADA_PROVINCE_NAMES_BY_ABBREVIATION).map(
    (answer) => ({
      answer,
    }),
  );

/**
 * User-facing description for Canada's provinces and territories quiz.
 */
const CANADA_PROVINCES_DESCRIPTION =
  `Learn all ${CANADA_PROVINCE_QUESTIONS.length} Canadian provinces and ` +
  `territories by their location on the map.`;

/**
 * Quiz definition for identifying Canadian provinces and territories by name.
 */
export const canadaProvincesQuiz: FeatureQuiz = {
  id: "canada-provinces",
  name: "Provinces and Territories",
  description: CANADA_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "canada-provinces",

  answerProperty: "name",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: CANADA_PROVINCE_QUESTIONS,
};
