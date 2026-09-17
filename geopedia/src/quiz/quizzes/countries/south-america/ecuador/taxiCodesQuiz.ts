/**
 * Quiz configuration for Ecuador's province-identifying taxi license-plate
 * codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ECUADOR_TAXI_CODE_QUESTIONS } from "./data/taxiCodes";

/**
 * Description shown for Ecuador's Taxi Codes quiz.
 */
const ECUADOR_TAXI_CODES_DESCRIPTION =
  `Learn all ${ECUADOR_TAXI_CODE_QUESTIONS.length} Ecuadorian province ` +
  `license-plate first-letter codes commonly useful for identifying taxis and ` +
  `other vehicles. Standard Ecuadorian plates normally contain 3 letters ` +
  `followed by 3 or 4 digits, such as PBX-1234, where P identifies Pichincha, ` +
  `or GRT-456, where G identifies Guayas. Commercial and public vehicles such ` +
  `as taxis and buses use colored plates and can appear in formats such as ` +
  `AHA-123, while government vehicles may use different formats such as E-1234.`;

/**
 * Quiz for identifying Ecuadorian provinces from the first letter of a vehicle
 * license plate.
 */
export const ecuadorTaxiCodesQuiz: FeatureQuiz = {
  id: "ecuador-taxi-codes",
  name: "Taxi Codes",
  description: ECUADOR_TAXI_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: [...ECUADOR_TAXI_CODE_QUESTIONS],
};
