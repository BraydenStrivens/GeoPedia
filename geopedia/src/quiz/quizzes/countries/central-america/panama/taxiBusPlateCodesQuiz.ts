/**
 * Quiz for identifying Panama's geographic taxi and bus license-plate codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

const PANAMA_TAXI_BUS_PLATE_CODE_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "1" },
    { answer: "2" },
    { answer: "3" },
    { answer: "4" },
    { answer: "5" },
    { answer: "6" },
    { answer: "7" },
    { answer: "8" },
    { answer: "9" },
    { answer: "13" },
  ];

const PANAMA_TAXI_BUS_PLATE_CODES_DESCRIPTION =
  `Learn ${PANAMA_TAXI_BUS_PLATE_CODE_QUESTIONS.length} regional taxi and bus licence-plate codes in Panama. ` +
  `The regional code appears at the beginning of the plate before a letter, such as 4B-0067 for Chiriquí or 7T-196 for Los Santos. ` +
  `Most regional codes contain one digit, while Panamá Oeste uses the two-digit code 13. `;

export const panamaTaxiBusPlateCodesQuiz: FeatureQuiz = {
  id: "panama-taxi-bus-plate-codes",
  name: "Taxi & Bus Plate Codes",
  description: PANAMA_TAXI_BUS_PLATE_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "panama-taxi-bus-plate-codes",

  answerProperty: "code",
  answerType: "single",

  questions: PANAMA_TAXI_BUS_PLATE_CODE_QUESTIONS,
};
