/**
 * Quiz configuration for Malaysia's second-level administrative districts.
 *
 * Districts can be grouped by their parent state or federal territory.
 */

import { FeatureQuiz } from "@/types/quiz";

import {
  MALAYSIA_DISTRICT_QUESTIONS,
  MALAYSIA_STATE_QUESTIONS,
} from "./data/admin";

const MALAYSIA_DISTRICTS_DESCRIPTION =
  `Learn all ${MALAYSIA_DISTRICT_QUESTIONS.length} second-level administrative ` +
  `districts of Malaysia. Group them by state or federal territory ` +
  `for more focused practice.`;

const STATE_VALUE_LABELS: Record<string, string> = Object.fromEntries(
  MALAYSIA_STATE_QUESTIONS.map((question) => [
    question.answer,
    question.display ?? question.answer,
  ]),
);

export const malaysiaDistrictsQuiz: FeatureQuiz = {
  id: "malaysia-districts",
  name: "Daerah (Districts)",
  description: MALAYSIA_DISTRICTS_DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "malaysia-districts",

  answerProperty: "district_id",
  answerType: "single",

  // grouping: {
  //   properties: [
  //     {
  //       property: "state_id",
  //       label: "State / Federal Territory",
  //       valueType: "string",
  //       valueLabels: STATE_VALUE_LABELS,
  //     },
  //   ],
  // },

  grouping: {
    properties: [
      {
        property: "state",
        label: "State",
        valueType: "string",
      },
    ],
  },

  questions: MALAYSIA_DISTRICT_QUESTIONS,
};
