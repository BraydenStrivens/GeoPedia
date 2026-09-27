/**
 * Feature quiz for Taiwan's detailed telephone area codes.
 *
 * Questions use individual telephone area codes as answers. Some codes share
 * the same geographic telephone region, so the map's `area_codes` property
 * provides multiple accepted answers for those features.
 *
 * Questions can be grouped by either their 1-digit or 2-digit significant
 * prefix. The grouping prefixes omit Taiwan's leading domestic trunk `0`.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_AREA_CODE_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn all ${TAIWAN_AREA_CODE_QUESTIONS.length} telephone area codes of ` +
  `Taiwan. A domestic landline number totals 9 digits, including the area ` +
  `code, so longer area codes are followed by shorter local numbers. Some ` +
  `area codes share the same geographic region and are shown together on the ` +
  `map. For example, Taipei uses the 2-digit area code 02 with an 8-digit ` +
  `local number, such as 02-2345-6789.`;

export const taiwanAreaCodesQuiz: FeatureQuiz = {
  id: "taiwan-area-codes",
  name: "Telephone Area Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "taiwan-area-codes",

  answerProperty: "area_codes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string-array",
      },
      {
        property: "prefix_2",
        label: "2-Digit Prefix",
        valueType: "string-array",
      },
    ],
  },

  questions: TAIWAN_AREA_CODE_QUESTIONS,
};
