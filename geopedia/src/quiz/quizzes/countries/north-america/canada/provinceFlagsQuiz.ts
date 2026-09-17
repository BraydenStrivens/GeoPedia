/**
 * Defines the Canada province and territory flags quiz.
 *
 * This quiz uses the shared Canada provinces map and asks the user to identify
 * all 10 provinces and 3 territories by their flags. Each quiz answer
 * corresponds to the `name` property in the processed Canada province and
 * territory GeoJSON dataset.
 *
 * Flag assets use Statistics Canada's stable PRUID identifiers as filenames,
 * matching the identifiers retained in the processed boundary dataset.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CANADA_PROVINCE_FLAG_QUESTIONS } from "./data/provinceFlags";

const CANADA_PROVINCE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${CANADA_PROVINCE_FLAG_QUESTIONS.length} Canadian provinces ` +
  `and territories by identifying each one on the map.`;

export const canadaProvinceFlagsQuiz: FeatureQuiz = {
  id: "canada-province-flags",
  name: "Province and Territory Flags",
  description: CANADA_PROVINCE_FLAGS_DESCRIPTION,

  kind: "feature",
  mapId: "canada-provinces",

  answerProperty: "name",
  answerType: "single",

  questions: CANADA_PROVINCE_FLAG_QUESTIONS,
};
