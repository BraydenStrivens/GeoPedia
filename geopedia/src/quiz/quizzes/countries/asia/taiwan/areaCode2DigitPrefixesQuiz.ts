/**
 * Feature quiz for Taiwan's 2-digit significant telephone-code prefixes.
 *
 * The stored answers omit Taiwan's leading domestic trunk `0`. Question
 * display values restore the `0` and use a trailing "-" when the value is
 * only a prefix of a longer detailed telephone area code.
 *
 * Some prefixes share the same geographic feature, so the map's `area_codes`
 * property provides multiple accepted answers for those features.
 *
 * Questions can be grouped by their 1-digit significant prefix.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_AREA_CODE_PREFIX_2_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn all ${TAIWAN_AREA_CODE_PREFIX_2_QUESTIONS.length} 2-digit ` +
  `significant telephone-code prefixes of Taiwan. A domestic landline number ` +
  `totals 9 digits, including the area code, while the prefixes in this quiz ` +
  `group more specific area codes into broader telephone regions. ` +
  `For example, Miaoli uses the 2-digit area code 037 with a 7-digit ` +
  `local number, such as 037-345-6789.`;

export const taiwanAreaCode2DigitPrefixesQuiz: FeatureQuiz = {
  id: "taiwan-area-code-prefix-2",
  name: "2-Digit Telephone Code Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "taiwan-area-code-prefix-2",

  answerProperty: "area_codes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string-array",
      },
    ],
  },

  questions: TAIWAN_AREA_CODE_PREFIX_2_QUESTIONS,
};
