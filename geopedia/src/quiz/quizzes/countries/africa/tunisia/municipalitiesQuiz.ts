/**
 * Feature quiz for Tunisia's baladiyat (municipalities).
 *
 * Municipalities can be grouped by delegation, governorate, or broad
 * administrative region. Question labels include both source and Arabic-native
 * display forms, with duplicate names already disambiguated by the generated
 * administrative data.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { TUNISIA_MUNICIPALITIES_BY_ID } from "./data/admin";

const TUNISIA_MUNICIPALITY_QUESTIONS: FeatureQuizQuestion[] =
  Object.entries(TUNISIA_MUNICIPALITIES_BY_ID).map(
    ([municipalityId, municipality]) => ({
      answer: municipalityId,
      display: municipality.display,
      nativeDisplay: municipality.nativeDisplay,
    }),
  );

const DESCRIPTION =
  `Learn all ${TUNISIA_MUNICIPALITY_QUESTIONS.length} baladiyat (municipalities) ` +
  `of Tunisia. They can be grouped by delegation, governorate, or region for more focused practice.`;

export const tunisiaMunicipalitiesQuiz: FeatureQuiz = {
  id: "tunisia-municipalities",
  name: "Baladiyat (Municipalities)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "tunisia-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: Object.fromEntries(
          Object.values(TUNISIA_MUNICIPALITIES_BY_ID).map(
            (municipality) => [
              municipality.regionId,
              municipality.region,
            ],
          ),
        ),
      },
      {
        property: "governorate_id",
        label: "Governorate",
        valueType: "string",
        valueLabels: Object.fromEntries(
          Object.values(TUNISIA_MUNICIPALITIES_BY_ID).map(
            (municipality) => [
              municipality.governorateId,
              municipality.governorate,
            ],
          ),
        ),
      },
      {
        property: "delegation_id",
        label: "Delegation",
        valueType: "string",
        valueLabels: Object.fromEntries(
          Object.values(TUNISIA_MUNICIPALITIES_BY_ID).map(
            (municipality) => [
              municipality.delegationId,
              municipality.delegation,
            ],
          ),
        ),
      },
    ],
  },

  questions: TUNISIA_MUNICIPALITY_QUESTIONS,
};
