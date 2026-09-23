/**
 * Feature quiz for Tunisia's 2-digit postal-code prefixes.
 *
 * Postal-prefix regions are derived from governorate geometry. Geographic
 * features may contain multiple valid prefixes, and the same prefix may be
 * valid for multiple features, so the quiz uses multiple-answer behavior.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TUNISIA_GOVERNORATES_BY_ID } from "./data/admin";
import { TUNISIA_POSTAL_PREFIX_QUESTIONS } from "./data/postalPrefixes";

/**
 * Display names for the broad administrative regions retained by the
 * postal-prefix runtime GeoJSON for grouping.
 */
const TUNISIA_REGION_NAMES_BY_ID = Object.fromEntries(
  Object.values(TUNISIA_GOVERNORATES_BY_ID).map((governorate) => [
    governorate.regionId,
    governorate.region,
  ]),
);

const DESCRIPTION =
  `Learn all ${TUNISIA_POSTAL_PREFIX_QUESTIONS.length} 2-digit postal-code ` +
  `prefixes of Tunisia. Tunisian postal codes contain 4 digits: the first two ` +
  `digits generally identify a geographic area. For example, 1000 (Tunis Ville) has 10--` +
  `and 8050 (Hammamet) has 80--.`;

export const tunisiaPostalPrefixesQuiz: FeatureQuiz = {
  id: "tunisia-postal-prefixes",
  name: "2-Digit Postal Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "tunisia-postal-prefixes",

  answerProperty: "postal_prefixes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: TUNISIA_REGION_NAMES_BY_ID,
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: TUNISIA_POSTAL_PREFIX_QUESTIONS,
};
