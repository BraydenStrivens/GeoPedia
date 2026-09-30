/**
 * Feature quiz for Taiwan's 368 township-level divisions.
 *
 * Questions use each division's stable canonical ID as the answer and
 * provide both English and Traditional Chinese player-facing names.
 * Duplicate names are already disambiguated in the generated question
 * data. Divisions can be grouped by county or province.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { TAIWAN_TOWNSHIP_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${TAIWAN_TOWNSHIP_QUESTIONS.length} township-level divisions ` +
  `of Taiwan. 鄉 (xiāng) means rural township, 鎮 (zhèn) means urban ` +
  `township, 市 (shì) means city, and 區 (qū) means district. Use county ` +
  `and province groups to study them in smaller sets.`;

export const taiwanTownshipsQuiz: FeatureQuiz = {
  id: "taiwan-townships",
  name: "鄉鎮市區 (Xiāng Zhèn Shì Qū) (Townships & Districts)",
  description: DESCRIPTION,

  kind: "feature",
  quizTopic: "Administrative Regions",
  mapId: "taiwan-townships",

  answerProperty: "township_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "county",
        label: "County",
        valueType: "string",
      },
    ],
  },

  questions: TAIWAN_TOWNSHIP_QUESTIONS,
};
