/**
 * Feature quiz for Taiwan's 22 county-level divisions.
 *
 * Questions use each division's stable canonical ID as the answer and
 * provide both English and Traditional Chinese player-facing names.
 * Divisions can be grouped by their parent province-level division.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_COUNTY_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${TAIWAN_COUNTY_QUESTIONS.length} county-level divisions of ` +
  `Taiwan. 縣 (xiàn) means county, while 市 (shì) means city. Use province ` +
  `groups to study them in smaller sets.`;

export const taiwanCountiesQuiz: FeatureQuiz = {
  id: "taiwan-counties",
  name: "縣 (Xiàn) (Counties)",
  description: DESCRIPTION,

  kind: "feature",
  quizTopic: "Administrative Regions",
  mapId: "taiwan-counties",

  answerProperty: "county_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
    ],
  },

  questions: TAIWAN_COUNTY_QUESTIONS,
};
