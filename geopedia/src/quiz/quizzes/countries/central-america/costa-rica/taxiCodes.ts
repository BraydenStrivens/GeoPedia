/**
 * Quiz for identifying Costa Rica's taxi codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

const COSTA_RICA_TAXI_CODE_QUESTIONS = [
  { answer: "1", display: "TSJ" },
  { answer: "2", display: "TA" },
  { answer: "3", display: "TC" },
  { answer: "4", display: "TH" },
  { answer: "5", display: "TG" },
  { answer: "6", display: "TP" },
  { answer: "7", display: "TL" },
];

const DESCRIPTION =
  `Learn all ${COSTA_RICA_TAXI_CODE_QUESTIONS.length} province-specific taxi codes ` +
  `in Costa Rica. Taxis may have triangular stickers containing several lines of ` +
  `information, with a 2-3 letter code at the top that identifies the province.`;

export const costaRicaTaxiCodesQuiz: FeatureQuiz = {
  id: "costa-rica-taxi-codes",
  name: "Taxi Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "costa-rica-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: COSTA_RICA_TAXI_CODE_QUESTIONS,
};
