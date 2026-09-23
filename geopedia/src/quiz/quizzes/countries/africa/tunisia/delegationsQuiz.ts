/**
 * Feature quiz for Tunisia's mutamadiyat (delegations).
 *
 * Delegations can be grouped by governorate or broad administrative region.
 * Question labels include both source and Arabic-native display forms, with
 * duplicate names already disambiguated by the generated administrative data.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { TUNISIA_DELEGATIONS_BY_ID } from "./data/admin";

const TUNISIA_DELEGATION_QUESTIONS: FeatureQuizQuestion[] =
  Object.entries(TUNISIA_DELEGATIONS_BY_ID).map(
    ([delegationId, delegation]) => ({
      answer: delegationId,
      display: delegation.display,
      nativeDisplay: delegation.nativeDisplay,
    }),
  );

const DESCRIPTION =
  `Learn all ${TUNISIA_DELEGATION_QUESTIONS.length} mutamadiyat (delegations) ` +
  `of Tunisia. They can be grouped by governorate or region for more focused practice.`;

export const tunisiaDelegationsQuiz: FeatureQuiz = {
  id: "tunisia-delegations",
  name: "Mutamadiyat (Delegations)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "tunisia-delegations",

  answerProperty: "delegation_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: Object.fromEntries(
          Object.values(TUNISIA_DELEGATIONS_BY_ID).map(
            (delegation) => [delegation.regionId, delegation.region],
          ),
        ),
      },
      {
        property: "governorate_id",
        label: "Governorate",
        valueType: "string",
        valueLabels: Object.fromEntries(
          Object.values(TUNISIA_DELEGATIONS_BY_ID).map(
            (delegation) => [
              delegation.governorateId,
              delegation.governorate,
            ],
          ),
        ),
      },
    ],
  },

  questions: TUNISIA_DELEGATION_QUESTIONS,
};
