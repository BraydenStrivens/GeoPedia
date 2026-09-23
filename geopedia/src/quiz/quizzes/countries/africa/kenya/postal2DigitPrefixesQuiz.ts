/**
 * Feature quiz for Kenya's 2-digit postal-code prefixes.
 *
 * Each question corresponds to one of Kenya's ten broad postal regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { KENYA_POSTAL_2_DIGIT_QUESTIONS } from "./data/postalCodes";

const DESCRIPTION =
  `Learn all ${KENYA_POSTAL_2_DIGIT_QUESTIONS.length} 2-digit postal-code ` +
  `prefixes of Kenya. Kenyan postal codes contain five digits, so a prefix ` +
  `such as 10--- represents postal codes beginning with 10. For example, ` +
  `10100 is Nyeri, 30100 is Eldoret, 40100 is Kisumu, and 80100 is Mombasa GPO.`;

export const kenyaPostal2DigitPrefixesQuiz: FeatureQuiz = {
  id: "kenya-postal-2-digit-prefixes",
  name: "2-Digit Postal Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "kenya-postal-2-digit-prefixes",

  answerProperty: "postal_prefix",
  answerType: "single",

  questions: KENYA_POSTAL_2_DIGIT_QUESTIONS,
};
