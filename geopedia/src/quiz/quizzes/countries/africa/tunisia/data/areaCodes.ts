/**
 * Tunisia geographic landline area-code quiz data.
 *
 * Each question represents one 2-digit geographic landline code. Codes 70,
 * 71, and 79 share the same Grand Tunis geographic region, while codes 72
 * through 78 each represent their own regional group of governorates.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

/**
 * All geographic landline area codes represented by Tunisia's area-code map.
 */
export const TUNISIA_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "70" },
  { answer: "71" },
  { answer: "72" },
  { answer: "73" },
  { answer: "74" },
  { answer: "75" },
  { answer: "76" },
  { answer: "77" },
  { answer: "78" },
  { answer: "79" },
];
