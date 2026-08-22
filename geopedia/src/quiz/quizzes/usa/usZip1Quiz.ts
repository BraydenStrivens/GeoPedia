/**
 * Defines the United States 1-digit ZIP-code prefix quiz.
 *
 * Each question represents the first digit
 * of a five-digit ZIP code. The remaining digits are displayed as hyphens
 * so the user can see that the question represents a ZIP-code prefix rather
 * than a complete ZIP code.
 */

import type { Quiz } from "@/types/quiz";

/**
 * Quiz definition for identifying US 1-digit ZIP-code regions.
 */
export const usZip1Quiz: Quiz = {
  id: "us-zip-1",
  name: "US 1-Digit ZIP Codes",
  mapId: "us-zip-1",
  answerProperty: "zip",
  answerType: "single",

  questions: [
    { answer: "0", display: "0----" },
    { answer: "1", display: "1----" },
    { answer: "2", display: "2----" },
    { answer: "3", display: "3----" },
    { answer: "4", display: "4----" },
    { answer: "5", display: "5----" },
    { answer: "6", display: "6----" },
    { answer: "7", display: "7----" },
    { answer: "8", display: "8----" },
    { answer: "9", display: "9----" },
  ],
};
