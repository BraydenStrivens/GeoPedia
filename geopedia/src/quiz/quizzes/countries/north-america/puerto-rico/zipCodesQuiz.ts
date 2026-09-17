/**
 * Quiz for identifying Puerto Rico's 5-digit ZIP-code regions.
 *
 * ZIP codes can be grouped by their 3-digit prefix.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PUERTO_RICO_ZIP_CODE_QUESTIONS } from "./data/postalCodes";

const PUERTO_RICO_ZIP_CODES_DESCRIPTION =
  `Learn all ${PUERTO_RICO_ZIP_CODE_QUESTIONS.length} mapped 5-digit ZIP codes ` +
  `of Puerto Rico, with filters that let you practice ZIP codes by 3-digit ` +
  `prefix.`;

export const puertoRicoZipCodesQuiz: FeatureQuiz = {
  id: "puerto-rico-zip-codes",
  name: "ZIP Codes",
  description: PUERTO_RICO_ZIP_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "puerto-rico-zip-codes",

  answerProperty: "zip_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "prefix_3",
        label: "3-Digit Prefix",
        valueType: "string",
        valueLabels: {
          "006": "006",
          "007": "007",
          "009": "009",
        },
      },
    ],
  },

  questions: PUERTO_RICO_ZIP_CODE_QUESTIONS,
};
