import type { FeatureQuiz } from "@/types/quiz";

import { COLOMBIA_DEPARTMENT_NAMES_BY_ID } from "./departmentsQuiz";

/**
 * Questions used by the Colombia Department Flags quiz.
 *
 * Each answer is the full department name because the shared Colombia
 * departments map identifies features through its `name` property. Department
 * IDs are used only to resolve the corresponding flag SVG.
 */
const COLOMBIA_DEPARTMENT_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COLOMBIA_DEPARTMENT_NAMES_BY_ID).map(
    ([id, name]) => ({
      answer: name,
      display: name,
      prompt: {
        type: "image",
        imageUrl: `/data/countries/colombia/flags/${id}.svg`,
        alt: "Department flag",
      },
    }),
  );

/**
 * User-facing description for the Colombia department flags quiz.
 */
const COLOMBIA_DEPARTMENT_FLAGS_DESCRIPTION =
  `Learn the flags of all ${COLOMBIA_DEPARTMENT_FLAG_QUESTIONS.length} ` +
  `Colombian departments by identifying each department on the map.`;

/**
 * Tests recognition of the flags of Colombia's departments.
 */
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
