/**
 * Quiz configuration for the U.S. Virgin Islands' ZIP codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

const US_VIRGIN_ISLANDS_ZIP_CODE_QUESTIONS = [
  { answer: "00802" },
  { answer: "00820" },
  { answer: "00830" },
  { answer: "00840" },
  { answer: "00850" },
  { answer: "00851" },
];

const US_VIRGIN_ISLANDS_ZIP_CODES_DESCRIPTION = `
  Learn all ${US_VIRGIN_ISLANDS_ZIP_CODE_QUESTIONS.length} mapped 5-digit
  ZIP codes of the U.S. Virgin Islands.
`;

export const usVirginIslandsZipCodesQuiz: FeatureQuiz = {
  id: "us-virgin-islands-zip-codes",
  name: "ZIP Codes",
  description: US_VIRGIN_ISLANDS_ZIP_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "us-virgin-islands-zip-codes",

  answerProperty: "zip_code",
  answerType: "single",

  questions: US_VIRGIN_ISLANDS_ZIP_CODE_QUESTIONS,
};
