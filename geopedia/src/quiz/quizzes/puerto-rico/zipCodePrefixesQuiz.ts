import type { FeatureQuiz } from "@/types/quiz";

/**
 * Questions for Puerto Rico's 3-digit ZIP-code prefixes quiz.
 */
const PUERTO_RICO_ZIP_CODE_PREFIX_QUESTIONS = [
  {
    answer: "006",
    display: "006--",
  },
  {
    answer: "007",
    display: "007--",
  },
  {
    answer: "009",
    display: "009--",
  },
];

/**
 * Quiz configuration for Puerto Rico's 3-digit ZIP-code prefixes.
 */
export const puertoRicoZipCodePrefixesQuiz: FeatureQuiz = {
  id: "puerto-rico-zip-code-prefixes",
  name: "3-Digit ZIP Prefixes",
  description: `Learn all ${PUERTO_RICO_ZIP_CODE_PREFIX_QUESTIONS.length} 3-digit ZIP-code prefixes of the otherwise 5-digit ZIP-codes of Puerto Rico.`,

  kind: "feature",
  mapId: "puerto-rico-zip-code-prefixes",

  answerProperty: "prefix_3",
  answerType: "single",

  questions: PUERTO_RICO_ZIP_CODE_PREFIX_QUESTIONS,
};
