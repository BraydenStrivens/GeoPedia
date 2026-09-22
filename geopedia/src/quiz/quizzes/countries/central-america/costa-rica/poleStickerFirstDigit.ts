/**
 * Quiz for identifying Costa Rica's pole sticker number's first digit.
 *
 * The first digit corresponds to the province id for each province.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COSTA_RICA_PROVINCES_BY_ID } from "./data/admin";

const COSTA_RICA_POLE_STICKER_FIRST_DIGIT_QUESTIONS = Object.entries(
  COSTA_RICA_PROVINCES_BY_ID,
).map(([provinceId]) => ({
  answer: provinceId,
  display: `${provinceId}---`,
}));

const DESCRIPTION =
  `Learn all ${COSTA_RICA_POLE_STICKER_FIRST_DIGIT_QUESTIONS.length} province-specific ` +
  `pole sticker first digits in Costa Rica. Poles may have stickers containing multiple ` +
  `lines of text, and the first digit of the topmost number identifies the province.`;

export const costaRicaPoleStickerFirstDigitQuiz: FeatureQuiz = {
  id: "costa-rica-pole-sticker-first-digits",
  name: "Pole Sticker First Digits",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "costa-rica-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: COSTA_RICA_POLE_STICKER_FIRST_DIGIT_QUESTIONS,
};
