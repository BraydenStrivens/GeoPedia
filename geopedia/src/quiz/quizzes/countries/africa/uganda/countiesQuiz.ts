/**
 * Feature quiz for Uganda's counties.
 *
 * Counties can be grouped by their parent region or district. Stable county
 * IDs are used as answers because some county names occur more than once.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { UGANDA_COUNTIES_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn all ${UGANDA_COUNTIES_QUIZ_QUESTIONS.length} counties of Uganda.`;

export const ugandaCountiesQuiz: FeatureQuiz = {
  id: "uganda-counties",
  name: "Counties",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "uganda-counties",

  answerProperty: "county_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: UGANDA_COUNTIES_QUIZ_QUESTIONS,
};
