/**
 * Quiz configuration for Malaysia's state road prefixes.
 */

import { FeatureQuiz } from "@/types/quiz";

const MALAYSIA_ROAD_PREFIX_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "A" },
  { answer: "B" },
  { answer: "C" },
  { answer: "D" },
  { answer: "J" },
  { answer: "K" },
  { answer: "M" },
  { answer: "N" },
  { answer: "P" },
  { answer: "Q" },
  { answer: "R" },
  { answer: "SA" },
  { answer: "T" },
];

const MALAYSIA_ROAD_PREFIXES_DESCRIPTION =
  `Learn all ${MALAYSIA_ROAD_PREFIX_QUESTIONS.length} Malaysian state road prefixes. ` +
  `These letter prefixes appear before route numbers and can help identify the state ` +
  `when encountered on road signs.`;

export const malaysiaRoadPrefixesQuiz: FeatureQuiz = {
  id: "malaysia-road-prefixes",
  name: "State Road Prefixes",
  description: MALAYSIA_ROAD_PREFIXES_DESCRIPTION,

  quizTopic: "Other",
  kind: "feature",
  mapId: "malaysia-road-prefixes",

  answerProperty: "road_prefix",
  answerType: "single",

  questions: MALAYSIA_ROAD_PREFIX_QUESTIONS,
};
