/**
 * Taiwan telephone area-code quiz questions.
 *
 * This file contains the question sets used by GeoPedia's three Taiwan
 * telephone-code quizzes:
 */

import { FeatureQuizQuestion } from "@/types/quiz";

export const TAIWAN_AREA_CODE_PREFIX_1_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "2", display: "02" },
    { answer: "3", display: "03-" },
    { answer: "4", display: "04-" },
    { answer: "5", display: "05-" },
    { answer: "6", display: "06-" },
    { answer: "7", display: "07" },
    { answer: "8", display: "08-" },
  ] as const;

export const TAIWAN_AREA_CODE_PREFIX_2_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "2", display: "02" },

    { answer: "32", display: "032" },
    { answer: "33", display: "033" },
    { answer: "34", display: "034" },
    { answer: "35", display: "035" },
    { answer: "36", display: "036" },
    { answer: "37", display: "037" },
    { answer: "38", display: "038" },
    { answer: "39", display: "039" },

    { answer: "42", display: "042-" },
    { answer: "43", display: "043" },
    { answer: "47", display: "047" },
    { answer: "48", display: "048" },
    { answer: "49", display: "049" },

    { answer: "52", display: "052" },
    { answer: "53", display: "053" },
    { answer: "55", display: "055" },
    { answer: "56", display: "056" },
    { answer: "57", display: "057" },

    { answer: "62", display: "062" },
    { answer: "63", display: "063" },
    { answer: "65", display: "065" },
    { answer: "66", display: "066" },
    { answer: "67", display: "067" },

    { answer: "7", display: "07" },

    { answer: "87", display: "087" },
    { answer: "88", display: "088" },
    { answer: "89", display: "089" },

    { answer: "69", display: "069" },
    { answer: "82", display: "082" },

    { answer: "83", display: "083-" },
  ] as const;

export const TAIWAN_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "02" },

  { answer: "032" },
  { answer: "033" },
  { answer: "034" },
  { answer: "035" },
  { answer: "036" },
  { answer: "037" },
  { answer: "038" },
  { answer: "039" },

  { answer: "0422" },
  { answer: "0423" },
  { answer: "0424" },
  { answer: "0425" },
  { answer: "0426" },
  { answer: "0427" },
  { answer: "043" },
  { answer: "047" },
  { answer: "048" },
  { answer: "049" },

  { answer: "052" },
  { answer: "053" },
  { answer: "055" },
  { answer: "056" },
  { answer: "057" },

  { answer: "062" },
  { answer: "063" },
  { answer: "065" },
  { answer: "066" },
  { answer: "067" },

  { answer: "07" },

  { answer: "087" },
  { answer: "088" },
  { answer: "089" },

  { answer: "069" },
  { answer: "082" },

  { answer: "08362" },
  { answer: "08365" },
  { answer: "08367" },
  { answer: "08368" },
] as const;
