/**
 * Quiz configuration for Vietnam's pre-reform province and municipality
 * abbreviations.
 *
 * Uses the existing pre-reform province map and GeoGuessr-oriented
 * abbreviations documented by Plonk It.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_PRE_REFORM_PROVINCE_ABBREVIATION_QUESTIONS } from "./data/province-abbreviations";

const DESCRIPTION =
  `Learn the abbreviations for all ` +
  `${VIETNAM_PRE_REFORM_PROVINCE_ABBREVIATION_QUESTIONS.length.toLocaleString()} ` +
  `provinces and municipalities of Vietnam before the 2025 reform. ` +
  `These abbreviations remain useful for identifying provinces in GeoGuessr ` +
  `coverage captured before the reform.`;

export const vietnamPreReformProvinceAbbreviationsQuiz: FeatureQuiz =
  {
    id: "vietnam-pre-reform-province-abbreviations",
    name: "Province Abbreviations — Pre-Reform",
    description: DESCRIPTION,

    quizTopic: "Administrative Regions",
    kind: "feature",
    mapId: "vietnam-pre-reform-provinces",

    answerProperty: "province_id",
    answerType: "single",

    questions: VIETNAM_PRE_REFORM_PROVINCE_ABBREVIATION_QUESTIONS,
  };
