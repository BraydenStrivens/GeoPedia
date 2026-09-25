/**
 * Quiz configuration for South Africa's one-digit geographic telephone
 * area-code prefixes.
 *
 * The prefixes represent the first meaningful digit after the national trunk
 * prefix 0, producing five geographic regions from 1- through 5-.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_AREA_CODE_PREFIX_QUESTIONS } from "./data/areaCodePrefixes";

const SOUTH_AFRICA_AREA_CODE_PREFIXES_DESCRIPTION = `
Learn South Africa's one-digit geographic telephone area-code prefixes.

The five regions cover prefixes 1- through 5- and provide a broader way to
learn the country's telephone geography before studying individual area codes.
`.trim();

export const southAfricaAreaCodePrefixesQuiz: FeatureQuiz = {
  id: "south-africa-area-code-prefixes",
  name: "South Africa Area Code Prefixes",
  description: SOUTH_AFRICA_AREA_CODE_PREFIXES_DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-area-code-prefixes",

  answerType: "single",
  answerProperty: "prefix_1",

  questions: SOUTH_AFRICA_AREA_CODE_PREFIX_QUESTIONS,
};
