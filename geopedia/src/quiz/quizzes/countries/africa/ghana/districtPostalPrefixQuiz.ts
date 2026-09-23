/**
 * Feature quiz for Ghana's postcode district codes.
 *
 * Each question displays the postcode district code while using the existing
 * canonical district ID as the map answer. This allows the quiz to reuse
 * Ghana's district GeoJSON without duplicating geometry or adding postal
 * properties to the administrative dataset.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { GHANA_POSTCODE_DISTRICTS_BY_ID } from "./data/postcodes";

const QUESTIONS: FeatureQuiz["questions"] = Object.entries(
  GHANA_POSTCODE_DISTRICTS_BY_ID,
).map(([districtId, district]) => ({
  answer: districtId,
  display: district.code,
}));

const REGION_VALUE_LABELS = Object.fromEntries(
  Object.values(GHANA_POSTCODE_DISTRICTS_BY_ID).map((district) => [
    district.regionId,
    district.region,
  ]),
);

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} postcode district codes of Ghana. A ` +
  `GhanaPostGPS postal code combines a 2- or 3-character postcode district ` +
  `code with a 3- to 5-digit area number. For example, GD identifies Adentan ` +
  `in Greater Accra, while WK identifies Effia Kwesimintim in Western Region. ` +
  `A full Digital Address adds a 4-digit property number after the postal code.`;

export const ghanaDistrictPostcodesQuiz: FeatureQuiz = {
  id: "ghana-postcode-district-codes",
  name: "Postcode District Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "ghana-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: REGION_VALUE_LABELS,
      },
    ],
  },

  questions: QUESTIONS,
};
