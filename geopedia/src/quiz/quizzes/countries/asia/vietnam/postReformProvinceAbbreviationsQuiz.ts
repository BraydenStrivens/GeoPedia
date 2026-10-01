/**
 * Quiz configuration for Vietnam's post-reform province and city
 * abbreviations.
 *
 * Uses the existing post-reform province map and GeoGuessr-oriented
 * abbreviations documented by Plonk It.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_POST_REFORM_PROVINCE_ABBREVIATION_QUESTIONS } from "./data/province-abbreviations";

const DESCRIPTION =
  `Learn the abbreviations for all ` +
  `${VIETNAM_POST_REFORM_PROVINCE_ABBREVIATION_QUESTIONS.length.toLocaleString()} ` +
  `provinces and cities of Vietnam after the 2025 reform. The reform reduced ` +
  `the number of first-level administrative units from 63 to 34.`;

export const vietnamPostReformProvinceAbbreviationsQuiz: FeatureQuiz =
  {
    id: "vietnam-post-reform-province-abbreviations",
    name: "Province Abbreviations — Post-Reform",
    description: DESCRIPTION,

    quizTopic: "Administrative Regions",
    kind: "feature",
    mapId: "vietnam-post-reform-provinces",

    answerProperty: "province_id",
    answerType: "single",

    questions: VIETNAM_POST_REFORM_PROVINCE_ABBREVIATION_QUESTIONS,
  };
