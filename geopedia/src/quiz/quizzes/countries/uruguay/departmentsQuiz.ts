import { URUGUAY_DEPARTMENTS_BY_ID } from "@/data/countries/uruguay/admin";
import type { FeatureQuiz } from "@/types/quiz";

const URUGUAY_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(URUGUAY_DEPARTMENTS_BY_ID).map(
    ([departmentId, department]) => ({
      answer: departmentId,
      display: department,
    }),
  );

const URUGUAY_DEPARTMENTS_DESCRIPTION =
  `Learn all ${URUGUAY_DEPARTMENT_QUESTIONS.length} departments of Uruguay ` +
  `by identifying each department on the map.`;

export const uruguayDepartmentsQuiz: FeatureQuiz = {
  id: "uruguay-departments",
  name: "Departments",
  description: URUGUAY_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "uruguay-departments",

  answerProperty: "department_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
    subdivisionBorders: false,
  },

  questions: URUGUAY_DEPARTMENT_QUESTIONS,
};
