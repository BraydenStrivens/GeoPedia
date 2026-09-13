import { PARAGUAY_DEPARTMENTS_BY_ID } from "@/data/countries/paraguay/admin";
import type { FeatureQuiz } from "@/types/quiz";

const PARAGUAY_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(PARAGUAY_DEPARTMENTS_BY_ID).map(
    ([departmentId, department]) => ({
      answer: departmentId,
      display: department,
    }),
  );

const PARAGUAY_DEPARTMENTS_DESCRIPTION =
  `Learn all ${PARAGUAY_DEPARTMENT_QUESTIONS.length} department-level ` +
  `divisions of Paraguay. Paraguay has 17 departments plus Asunción, the ` +
  `capital district, which is treated as a department-level unit.`;

export const paraguayDepartmentsQuiz: FeatureQuiz = {
  id: "paraguay-departments",
  name: "Departments",
  description: PARAGUAY_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "paraguay-departments",

  answerProperty: "department_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PARAGUAY_DEPARTMENT_QUESTIONS,
};
