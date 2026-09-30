/**
 * Feature quiz for the Philippines' barangays.
 *
 * Barangays can be grouped by region, province / province-level unit, or
 * municipality / city.
 *
 * Stable barangay IDs are used as answers because many barangay names occur
 * more than once.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PHILIPPINES_BARANGAY_QUESTIONS } from "./data/barangays";

const DESCRIPTION =
  `Learn all ${PHILIPPINES_BARANGAY_QUESTIONS.length.toLocaleString()} ` +
  `barangays (villages) of the Philippines.\n\n` +
  `A barangay is the smallest local government unit in the Philippines.\n\n` +
  `Group the quiz by region, province, or municipality/city to break the ` +
  `country's more than 42,000 barangays into manageable sets.`;

export const philippinesBarangaysQuiz: FeatureQuiz = {
  id: "philippines-barangays",
  name: "Barangays (Villages)",
  description: DESCRIPTION,

  kind: "feature",
  quizTopic: "Administrative Regions",
  mapId: "philippines-barangays",

  answerProperty: "barangay_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "municipality_city",
        label: "Municipality / City",
        valueType: "string",
      },
    ],
  },

  questions: PHILIPPINES_BARANGAY_QUESTIONS,
};
