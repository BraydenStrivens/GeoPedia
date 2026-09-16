import { BOLIVIA_DEPARTMENTS_BY_ID } from "@/data/countries/bolivia/admin";
import type { FeatureQuiz } from "@/types/quiz";

const BOLIVIA_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BOLIVIA_DEPARTMENTS_BY_ID).map(
    ([departmentId, department]) => ({
      answer: departmentId,
      display: department,
    }),
  );

const BOLIVIA_DEPARTMENTS_DESCRIPTION =
  `Learn all ${BOLIVIA_DEPARTMENT_QUESTIONS.length} departments of Bolivia. ` +
  `Departments are Bolivia's first-level administrative divisions.`;

export const boliviaDepartmentsQuiz: FeatureQuiz = {
  id: "bolivia-departments",
  name: "Departments",
  description: BOLIVIA_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "bolivia-departments",

  answerProperty: "department_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: BOLIVIA_DEPARTMENT_QUESTIONS,
};
