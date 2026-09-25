/**
 * South Africa four-digit postcode feature quiz.
 *
 * Uses the highest-resolution reconstructed postcode geography and generated
 * questions matching every postcode present in the runtime GeoJSON.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_POSTCODES_4_QUIZ_QUESTIONS } from "./data/postcodes";

const DESCRIPTION =
  `Learn the 4-digit postal codes of South Africa.\n\n` +
  `South African postal codes contain four digits, including leading zeros. ` +
  `Examples include 0872 for Xihoko and 2192 for Abbotsford in Johannesburg, ` +
  `Use the grouping options to focus on postal codes within a particular 1-, 2-, ` +
  `or 3-digit prefix.`;

export const southAfricaPostcodes4DigitQuiz: FeatureQuiz = {
  id: "south-africa-postcodes-4",
  name: "4-Digit Postcodes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-postcodes-4",

  answerProperty: "postcode",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
      {
        property: "prefix_2",
        label: "2-Digit Prefix",
        valueType: "string",
      },
      {
        property: "prefix_3",
        label: "3-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: SOUTH_AFRICA_POSTCODES_4_QUIZ_QUESTIONS,
};
