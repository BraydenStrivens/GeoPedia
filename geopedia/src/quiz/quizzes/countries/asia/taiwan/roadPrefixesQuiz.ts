/**
 * Feature quiz for Taiwan's county-road prefix characters.
 *
 * Questions use the Chinese character shown before a county-road number
 * and map it directly to the corresponding feature in Taiwan's existing
 * county map.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_ROAD_PREFIX_QUESTIONS } from "./data/roadPrefixes";

const DESCRIPTION =
  `Learn the ${TAIWAN_ROAD_PREFIX_QUESTIONS.length} unique characters used ` +
  `as prefixes on Taiwan's county road numbers. The character identifies ` +
  `the county or municipality: for example, 雲101 is in Yunlin and ` +
  `roads beginning with 桃 are in Taoyuan. Keelung, Hsinchu City, and Chiayi City use 市 instead of a ` +
  `unique character, while Taipei has no prefix on the reference map.`;

export const taiwanRoadPrefixesQuiz: FeatureQuiz = {
  id: "taiwan-road-prefixes",
  name: "County Road Prefix Characters",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "taiwan-road-prefixes",

  answerProperty: "road_prefix_id",
  answerType: "single",

  questions: TAIWAN_ROAD_PREFIX_QUESTIONS,
};
