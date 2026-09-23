/**
 * Feature quiz for Tunisia's geographic landline area codes.
 *
 * Tunisia's governorates are grouped into eight geographic landline regions.
 * Most regions use one area code, while Grand Tunis uses 70, 71, and 79.
 * Mobile prefixes are not part of this geographic quiz.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TUNISIA_AREA_CODE_QUESTIONS } from "./data/areaCodes";

const DESCRIPTION =
  `Learn all ${TUNISIA_AREA_CODE_QUESTIONS.length} geographic landline area ` +
  `codes of Tunisia. Tunisian landline numbers use a 2-digit geographic code ` +
  `followed by a 6-digit subscriber number. Neighboring governorates often ` +
  `share the same code; for example, 72 covers Bizerte, Nabeul, and Zaghouan, ` +
  `while 73 covers Sousse, Monastir, and Mahdia.`;

export const tunisiaAreaCodesQuiz: FeatureQuiz = {
  id: "tunisia-area-codes",
  name: "Landline Area Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "tunisia-area-codes",

  answerProperty: "area_codes",
  answerType: "multiple",

  questions: TUNISIA_AREA_CODE_QUESTIONS,
};
