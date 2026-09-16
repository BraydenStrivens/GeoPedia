import type { FeatureQuiz } from "@/types/quiz";

import { PARAGUAY_DEPARTMENT_FLAG_QUESTIONS } from "./data/departmentFlags";

/**
 * Description shown for Paraguay's Department Flags quiz.
 */
const PARAGUAY_DEPARTMENT_FLAGS_DESCRIPTION =
  `Learn the flags of all ${PARAGUAY_DEPARTMENT_FLAG_QUESTIONS.length} ` +
  `department-level divisions of Paraguay by identifying the corresponding ` +
  `department or capital district on the map.`;

/**
 * Quiz for identifying Paraguay's department-level divisions from their flags.
 */
export const paraguayDepartmentFlagsQuiz: FeatureQuiz = {
  id: "paraguay-department-flags",
  name: "Department Flags",
  description: PARAGUAY_DEPARTMENT_FLAGS_DESCRIPTION,

  kind: "feature",
  mapId: "paraguay-departments",

  answerProperty: "department_id",
  answerType: "single",

  questions: PARAGUAY_DEPARTMENT_FLAG_QUESTIONS,
};
