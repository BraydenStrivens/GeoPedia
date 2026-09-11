import type { FeatureQuiz } from "@/types/quiz";

/**
 * Guatemala department names keyed by the normalized two-digit department IDs
 * used throughout GeoPedia's Guatemala datasets.
 */
export const GUATEMALA_DEPARTMENT_NAMES_BY_ID = {
  "01": "Guatemala",
  "02": "El Progreso",
  "03": "Sacatepéquez",
  "04": "Chimaltenango",
  "05": "Escuintla",
  "06": "Santa Rosa",
  "07": "Sololá",
  "08": "Totonicapán",
  "09": "Quetzaltenango",
  "10": "Suchitepéquez",
  "11": "Retalhuleu",
  "12": "San Marcos",
  "13": "Huehuetenango",
  "14": "Quiché",
  "15": "Baja Verapaz",
  "16": "Alta Verapaz",
  "17": "Petén",
  "18": "Izabal",
  "19": "Zacapa",
  "20": "Chiquimula",
  "21": "Jalapa",
  "22": "Jutiapa",
} as const;

/**
 * Questions for Guatemala's departments quiz.
 */
const GUATEMALA_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(GUATEMALA_DEPARTMENT_NAMES_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

/**
 * User-facing description for Guatemala's departments quiz.
 */
const GUATEMALA_DEPARTMENTS_DESCRIPTION = `Learn all ${GUATEMALA_DEPARTMENT_QUESTIONS.length} departments of Guatemala.`;

/**
 * Full-name quiz for Guatemala's departments.
 */
export const guatemalaDepartmentsQuiz: FeatureQuiz = {
  id: "guatemala-departments",
  name: "Departments",
  description: GUATEMALA_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "guatemala-departments",

  answerProperty: "department_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: GUATEMALA_DEPARTMENT_QUESTIONS,
};
