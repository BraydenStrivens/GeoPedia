import type { FeatureQuiz } from "@/types/quiz";

/**
 * Questions for the U.S. Virgin Islands ZIP codes quiz.
 */
const US_VIRGIN_ISLANDS_ZIP_CODE_QUESTIONS = [
  {
    answer: "00802",
    display: "00802",
  },
  {
    answer: "00820",
    display: "00820",
  },
  {
    answer: "00830",
    display: "00830",
  },
  {
    answer: "00840",
    display: "00840",
  },
  {
    answer: "00850",
    display: "00850",
  },
  {
    answer: "00851",
    display: "00851",
  },
];

/**
 * Quiz configuration for the U.S. Virgin Islands' ZIP codes.
 */
export const usVirginIslandsZipCodesQuiz: FeatureQuiz = {
  id: "us-virgin-islands-zip-codes",
  name: "ZIP Codes",
  description: `Learn all ${US_VIRGIN_ISLANDS_ZIP_CODE_QUESTIONS.length} mapped 5-digit ZIP codes of the U.S. Virgin Islands.`,

  kind: "feature",
  mapId: "us-virgin-islands-zip-codes",

  answerProperty: "zip_code",
  answerType: "single",

  questions: US_VIRGIN_ISLANDS_ZIP_CODE_QUESTIONS,
};
