/**
 * Geographic landline area-code prefix questions for Thailand.
 *
 * Answers match the area_code_prefix property in the processed
 * GeoJSON files. The leading domestic trunk prefix (0) is omitted
 * because it is common to every geographic landline area code.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

export const THAILAND_AREA_CODE_PREFIX_1_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "2", display: "02" },
    { answer: "3", display: "03-" },
    { answer: "4", display: "04-" },
    { answer: "5", display: "05-" },
    { answer: "7", display: "07-" },
  ];

export const THAILAND_AREA_CODE_PREFIX_2_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "02" },
    { answer: "32", display: "032" },
    { answer: "34", display: "034" },
    { answer: "35", display: "035" },
    { answer: "36", display: "036" },
    { answer: "37", display: "037" },
    { answer: "38", display: "038" },
    { answer: "39", display: "039" },
    { answer: "42", display: "042" },
    { answer: "43", display: "043" },
    { answer: "44", display: "044" },
    { answer: "45", display: "045" },
    { answer: "53", display: "053" },
    { answer: "54", display: "054" },
    { answer: "55", display: "055" },
    { answer: "56", display: "056" },
    { answer: "73", display: "073" },
    { answer: "74", display: "074" },
    { answer: "75", display: "075" },
    { answer: "76", display: "076" },
    { answer: "77", display: "077" },
  ];
