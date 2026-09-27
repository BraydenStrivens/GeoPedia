/**
 * Feature quiz for Taiwan's 1-digit significant telephone-code prefixes.
 *
 * These seven prefixes represent Taiwan's broadest telephone-code regions.
 * The stored answers omit the leading domestic trunk `0`, while question
 * display values restore it.
 *
 * A trailing "-" is shown when the displayed value continues into longer
 * telephone area codes. Complete codes such as 02 and 07 do not use "-".
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_AREA_CODE_PREFIX_1_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn the ${TAIWAN_AREA_CODE_PREFIX_1_QUESTIONS.length} broad telephone-code ` +
  `regions of Taiwan. A domestic landline number totals 9 digits, including ` +
  `the area code. For example, the Matsu Islands use 4-digit ` +
  `area codes such as 08362, which are followed by a 4-digit local number. ` +
  `This would appear as 08- in this 1-digit prefix quiz.`;

export const taiwanAreaCode1DigitPrefixesQuiz: FeatureQuiz = {
  id: "taiwan-area-code-prefix-1",
  name: "1-Digit Telephone Code Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "taiwan-area-code-prefix-1",

  answerProperty: "area_codes",
  answerType: "multiple",

  questions: TAIWAN_AREA_CODE_PREFIX_1_QUESTIONS,
};
