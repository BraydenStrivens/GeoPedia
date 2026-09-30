/**
 * Quiz configuration for the flags of Malaysia's states and federal
 * territories.
 *
 * The existing state and federal territory map is reused while each question
 * presents the corresponding flag as an image prompt.
 */

import { FeatureQuiz } from "@/types/quiz";

import { MALAYSIA_STATE_QUESTIONS } from "./data/admin";

const MALAYSIA_STATE_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  MALAYSIA_STATE_QUESTIONS.map((question) => ({
    answer: question.answer,
    display: question.display,
    prompt: {
      type: "image",
      imageUrl: `/data/countries/malaysia/flags/${question.answer.toLowerCase()}.svg`,
      alt: `${question.display} flag`,
    },
  }));

const MALAYSIA_STATE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${MALAYSIA_STATE_FLAG_QUESTIONS.length} states and federal territories ` +
  `of Malaysia by identifying each flag on the map.`;

export const malaysiaStateFlagsQuiz: FeatureQuiz = {
  id: "malaysia-state-flags",
  name: "State & Federal Territory Flags",
  description: MALAYSIA_STATE_FLAGS_DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "malaysia-states",

  answerProperty: "state_id",
  answerType: "single",

  questions: MALAYSIA_STATE_FLAG_QUESTIONS,
};
