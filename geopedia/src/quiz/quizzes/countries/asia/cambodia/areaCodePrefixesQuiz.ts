/**
 * Quiz configuration for Cambodia's one-digit geographic landline
 * area-code prefixes.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CAMBODIA_AREA_CODE_PREFIX_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn Cambodia's ${CAMBODIA_AREA_CODE_PREFIX_QUESTIONS.length.toLocaleString()} landline ` +
  `area-code prefixes. Domestic landline numbers are 9–10 digits and use a 0XX area code; ` +
  `for example, Battambang's 053 belongs to the 05- prefix.`;

export const cambodiaAreaCodePrefixesQuiz: FeatureQuiz = {
  id: "cambodia-area-code-prefixes",
  name: "1-Digit Area Code Prefixes",
  description: DESCRIPTION,

  quizTopic: "Area Codes",
  kind: "feature",
  mapId: "cambodia-area-code-prefixes",

  answerProperty: "area_code_prefix",
  answerType: "single",

  questions: CAMBODIA_AREA_CODE_PREFIX_QUESTIONS,
};
