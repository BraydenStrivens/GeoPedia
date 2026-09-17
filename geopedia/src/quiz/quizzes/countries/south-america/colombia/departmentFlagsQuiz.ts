/**
 * Quiz configuration for identifying Colombia's departments from their flags.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COLOMBIA_DEPARTMENTS_BY_ID } from "./data/admin";

const COLOMBIA_DEPARTMENT_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COLOMBIA_DEPARTMENTS_BY_ID).map(([id, name]) => ({
    answer: name,
    display: name,
    prompt: {
      type: "image",
      imageUrl: `/data/countries/colombia/flags/${id}.svg`,
      alt: "Department flag",
    },
  }));

const COLOMBIA_DEPARTMENT_FLAGS_DESCRIPTION =
  `Learn the flags of all ${COLOMBIA_DEPARTMENT_FLAG_QUESTIONS.length} ` +
  `Colombian departments by identifying each department on the map.`;

export const colombiaDepartmentFlagsQuiz: FeatureQuiz = {
  id: "colombia-department-flags",
  name: "Department Flags",
  description: COLOMBIA_DEPARTMENT_FLAGS_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-departments",

  answerProperty: "name",
  answerType: "single",

  questions: COLOMBIA_DEPARTMENT_FLAG_QUESTIONS,
};
