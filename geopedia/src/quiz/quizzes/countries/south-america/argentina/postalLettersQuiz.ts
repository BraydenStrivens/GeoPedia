/**
 * Quiz configuration for the province-identifying first letters used by
 * Argentina's modern Código Postal Argentino (CPA).
 *
 * Questions use stable province IDs as map answers and display the
 * corresponding CPA postal letter to the player.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ARGENTINA_POSTAL_LETTER_BY_PROVINCE_ID } from "./data/postalLetters";

const ARGENTINA_POSTAL_LETTERS_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(ARGENTINA_POSTAL_LETTER_BY_PROVINCE_ID).map(
    ([provinceId, postalLetter]) => ({
      answer: provinceId,
      display: postalLetter,
    }),
  );

const ARGENTINA_POSTAL_LETTERS_DESCRIPTION =
  `Learn the ${ARGENTINA_POSTAL_LETTERS_QUESTIONS.length} province letters ` +
  `used by Argentina's modern Código Postal Argentino (CPA). Argentina's ` +
  `legacy postal system uses 4-digit numeric codes, while the newer CPA ` +
  `system uses the format A9999AAA. The first letter of a CPA code uniquely ` +
  `identifies one of Argentina's 23 provinces or the Autonomous City of ` +
  `Buenos Aires. This quiz focuses specifically on the province letters ` +
  `used by the newer CPA format.`;

export const argentinaPostalLettersQuiz: FeatureQuiz = {
  id: "argentina-postal-letters",
  name: "Postal Letters",
  description: ARGENTINA_POSTAL_LETTERS_DESCRIPTION,

  kind: "feature",
  mapId: "argentina-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: ARGENTINA_POSTAL_LETTERS_QUESTIONS,
};
