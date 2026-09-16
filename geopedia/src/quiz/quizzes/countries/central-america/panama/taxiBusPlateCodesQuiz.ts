import type { FeatureQuiz } from "@/types/quiz";

/**
 * All geographically useful taxi and bus licence-plate codes represented by
 * Panama's processed plate-code GeoJSON.
 */
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

/**
 * User-facing description derived from the question array so it remains
 * accurate if the useful plate-code set changes later.
 */
const PANAMA_TAXI_BUS_PLATE_CODES_DESCRIPTION =
  `Learn ${PANAMA_TAXI_BUS_PLATE_CODE_QUESTIONS.length} regional taxi and bus licence-plate codes in Panama. ` +
  `The regional code appears at the beginning of the plate before a letter, such as 4B-0067 for Chiriquí or 7T-196 for Los Santos. ` +
  `Most regional codes contain one digit, while Panamá Oeste uses the two-digit code 13. `;
/**
 * Quiz definition for identifying Panama's regional taxi and bus licence-plate
 * codes.
 */
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
