import { FeatureQuiz } from "@/types/quiz";

/**
 * All geographically useful first-digit telephone prefixes represented by
 * Panama's processed 1-digit phone-code GeoJSON.
 */
export const PANAMA_PHONE_CODES_1_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "2" },
    { answer: "3" },
    { answer: "4" },
    { answer: "7" },
    { answer: "9" },
  ];

/**
 * All geographically useful regional telephone prefixes represented by
 * Panama's processed 2-digit phone-code GeoJSON.
 *
 * Some regions retain a broader 1-digit prefix where Plonk It does not
 * provide a more precise 2-digit regional prefix.
 */
export const PANAMA_PHONE_CODES_2_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "2" },
    { answer: "3" },
    { answer: "4" },
    { answer: "7" },
    { answer: "24" },
    { answer: "25" },
    { answer: "29" },
    { answer: "34" },
    { answer: "75" },
    { answer: "90" },
    { answer: "93" },
    { answer: "95" },
    { answer: "96" },
    { answer: "97" },
    { answer: "98" },
  ];
