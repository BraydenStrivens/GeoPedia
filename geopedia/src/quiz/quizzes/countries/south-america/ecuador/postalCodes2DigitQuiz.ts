/**
 * Quiz configuration for the first two digits of Ecuador's postal codes.
 *
 * The first two digits identify the province associated with the postal code.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ECUADOR_POSTAL_CODE_QUESTIONS } from "./data/postalCodes2Digit";

const ECUADOR_POSTAL_CODES_DESCRIPTION =
  `Learn all ${ECUADOR_POSTAL_CODE_QUESTIONS.length} two-digit province postal ` +
  `code prefixes used across Ecuador. Ecuadorian postal codes contain six ` +
  `digits, with the first two digits identifying the province.`;

export const ecuadorPostalCodes2DigitQuiz: FeatureQuiz = {
  id: "ecuador-postal-codes",
  name: "2-Digit Postal Codes",
  description: ECUADOR_POSTAL_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: [...ECUADOR_POSTAL_CODE_QUESTIONS],
};
