/**
 * Feature quiz for Thailand's Thai-script province abbreviations.
 *
 * Reuses the existing province map and its stable province IDs.
 * Includes Bangkok's abbreviation alongside the 76 provinces.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { THAILAND_PROVINCE_ABBREVIATION_QUESTIONS } from "./data/provinceAbbreviations";

const DESCRIPTION =
  `Learn all ${THAILAND_PROVINCE_ABBREVIATION_QUESTIONS.length.toLocaleString()} Thai province-level abbreviations, including Bangkok. ` +
  `These short Thai-script abbreviations are useful for recognizing provinces on road markers and other signs.`;

export const thailandProvinceAbbreviationsQuiz: FeatureQuiz = {
  id: "thailand-province-abbreviations",
  name: "อักษรย่อจังหวัด - Changwat Abbreviations (Province Abbreviations)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "thailand-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: THAILAND_PROVINCE_ABBREVIATION_QUESTIONS,
};
