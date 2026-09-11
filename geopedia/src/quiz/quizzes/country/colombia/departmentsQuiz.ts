import type { FeatureQuiz } from "@/types/quiz";

/**
 * Colombia's department and capital-district names keyed by their two-digit
 * administrative identifiers.
 */
export const COLOMBIA_DEPARTMENT_NAMES_BY_ID = {
  "05": "Antioquia",
  "08": "Atlántico",
  "11": "Bogotá D.C.",
  "13": "Bolívar",
  "15": "Boyacá",
  "17": "Caldas",
  "18": "Caquetá",
  "19": "Cauca",
  "20": "Cesar",
  "23": "Córdoba",
  "25": "Cundinamarca",
  "27": "Chocó",
  "41": "Huila",
  "44": "La Guajira",
  "47": "Magdalena",
  "50": "Meta",
  "52": "Nariño",
  "54": "Norte de Santander",
  "63": "Quindío",
  "66": "Risaralda",
  "68": "Santander",
  "70": "Sucre",
  "73": "Tolima",
  "76": "Valle del Cauca",
  "81": "Arauca",
  "85": "Casanare",
  "86": "Putumayo",
  "88": "San Andrés y Providencia",
  "91": "Amazonas",
  "94": "Guainía",
  "95": "Guaviare",
  "97": "Vaupés",
  "99": "Vichada",
} as const;

/**
 * Questions for Colombia's departments quiz.
 */
const COLOMBIA_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COLOMBIA_DEPARTMENT_NAMES_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

/**
 * Description shown for Colombia's Departments quiz.
 */
const COLOMBIA_DEPARTMENTS_DESCRIPTION =
  `Learn all ${COLOMBIA_DEPARTMENT_QUESTIONS.length} department-level ` +
  `divisions of Colombia, including Bogotá D.C.`;

/**
 * Quiz configuration for Colombia's departments.
 */
export const colombiaDepartmentsQuiz: FeatureQuiz = {
  id: "colombia-departments",
  name: "Departments",
  description: COLOMBIA_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-departments",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: COLOMBIA_DEPARTMENT_QUESTIONS,
};
