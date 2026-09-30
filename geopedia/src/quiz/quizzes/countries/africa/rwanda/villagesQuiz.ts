/**
 * Feature quiz for Rwanda's imidugudu (villages), grouped through the
 * administrative hierarchy from province to cell.
 *
 * This unusually large quiz contains nearly 15,000 village features.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { RWANDA_VILLAGES_QUIZ_QUESTIONS } from "./data/villages";

const DESCRIPTION =
  `Learn all ${RWANDA_VILLAGES_QUIZ_QUESTIONS.length.toLocaleString()} imidugudu (villages) ` +
  `of Rwanda.`;

export const rwandaVillagesQuiz: FeatureQuiz = {
  id: "rwanda-villages",
  name: "Imidugudu (Villages)",
  description: DESCRIPTION,

  kind: "feature",
  quizTopic: "Administrative Regions",
  mapId: "rwanda-villages",

  answerProperty: "village_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
      {
        property: "sector",
        label: "Sector",
        valueType: "string",
      },
      {
        property: "cell",
        label: "Cell",
        valueType: "string",
      },
    ],
  },

  questions: RWANDA_VILLAGES_QUIZ_QUESTIONS,
};
