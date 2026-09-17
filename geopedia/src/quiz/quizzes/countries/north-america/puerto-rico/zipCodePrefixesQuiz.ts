/**
 * Quiz for identifying Puerto Rico's 3-digit ZIP-code prefix regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PUERTO_RICO_ZIP_CODE_PREFIX_QUESTIONS } from "./data/postalCodes";

const PUERTO_RICO_ZIP_CODE_PREFIXES_DESCRIPTION =
  `Learn all ${PUERTO_RICO_ZIP_CODE_PREFIX_QUESTIONS.length} 3-digit ZIP-code ` +
  `prefixes, which represent the first three digits of an otherwise 5-digit ` +
  `Puerto Rico ZIP code.`;

export const puertoRicoZipCodePrefixesQuiz: FeatureQuiz = {
  id: "puerto-rico-zip-code-prefixes",
  name: "3-Digit ZIP Prefixes",
  description: PUERTO_RICO_ZIP_CODE_PREFIXES_DESCRIPTION,

  kind: "feature",
  mapId: "puerto-rico-zip-code-prefixes",

  answerProperty: "prefix_3",
  answerType: "single",

  questions: PUERTO_RICO_ZIP_CODE_PREFIX_QUESTIONS,
};
