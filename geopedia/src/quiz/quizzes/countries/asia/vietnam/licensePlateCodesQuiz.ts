/**
 * Quiz configuration for Vietnam's province-level license plate codes.
 *
 * License plate codes correspond to the pre-reform province and municipality
 * boundaries, allowing this quiz to reuse the existing province map.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_LICENSE_PLATE_CODE_QUESTIONS } from "./data/license-plate-codes";

const DESCRIPTION =
  `Learn the license plate codes for all pre-reform ${VIETNAM_LICENSE_PLATE_CODE_QUESTIONS.length.toLocaleString()} ` +
  `provinces and municipalities of Vietnam. A typical registration follows the format ` +
  `province code + series letter + 5-digit sequential number, such as 43A-345.67, with the ` +
  `first two digits identifying where the vehicle is registered. License plates are blurred ` +
  `in GeoGuessr, but these registration numbers can sometimes be found written on the sides ` +
  `of vehicles.`;

export const vietnamLicensePlateCodesQuiz: FeatureQuiz = {
  id: "vietnam-license-plate-codes",
  name: "License Plate Codes",
  description: DESCRIPTION,

  quizTopic: "Other",
  kind: "feature",
  mapId: "vietnam-pre-reform-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: VIETNAM_LICENSE_PLATE_CODE_QUESTIONS,
};
