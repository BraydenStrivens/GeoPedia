import type { FeatureQuiz } from "@/types/quiz";

/**
 * Guatemala's 22 departments keyed by the normalized department IDs used by
 * the processed Guatemala departments GeoJSON.
 */
const GUATEMALA_DEPARTMENT_QUESTIONS = [
  { answer: "01", display: "Guatemala" },
  { answer: "02", display: "El Progreso" },
  { answer: "03", display: "Sacatepéquez" },
  { answer: "04", display: "Chimaltenango" },
  { answer: "05", display: "Escuintla" },
  { answer: "06", display: "Santa Rosa" },
  { answer: "07", display: "Sololá" },
  { answer: "08", display: "Totonicapán" },
  { answer: "09", display: "Quetzaltenango" },
  { answer: "10", display: "Suchitepéquez" },
  { answer: "11", display: "Retalhuleu" },
  { answer: "12", display: "San Marcos" },
  { answer: "13", display: "Huehuetenango" },
  { answer: "14", display: "Quiché" },
  { answer: "15", display: "Baja Verapaz" },
  { answer: "16", display: "Alta Verapaz" },
  { answer: "17", display: "Petén" },
  { answer: "18", display: "Izabal" },
  { answer: "19", display: "Zacapa" },
  { answer: "20", display: "Chiquimula" },
  { answer: "21", display: "Jalapa" },
  { answer: "22", display: "Jutiapa" },
] as const;

/**
 * Full-name quiz for Guatemala's 22 departments.
 */
export const guatemalaDepartmentsQuiz: FeatureQuiz = {
  id: "guatemala-departments",
  name: "Departments",
  description: `Learn all ${GUATEMALA_DEPARTMENT_QUESTIONS.length} departments of Guatemala.`,

  kind: "feature",
  mapId: "guatemala-departments",

  answerProperty: "department_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: [...GUATEMALA_DEPARTMENT_QUESTIONS],
};
