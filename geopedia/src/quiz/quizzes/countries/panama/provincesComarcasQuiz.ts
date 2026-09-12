import type { FeatureQuiz } from "@/types/quiz";

/**
 * Panama's province-level administrative divisions by stable source ID.
 *
 * This includes the country's 10 provinces and four province-level comarcas.
 */
export const PANAMA_PROVINCE_COMARCA_NAMES_BY_ID = {
  "01": "Bocas del Toro",
  "02": "Coclé",
  "03": "Colón",
  "04": "Chiriquí",
  "05": "Darién",
  "06": "Herrera",
  "07": "Los Santos",
  "08": "Panamá",
  "09": "Veraguas",
  "10": "Kuna Yala",
  "11": "Emberá Wounaán",
  "12": "Ngäbe Buglé",
  "13": "Panamá Oeste",
  "14": "Naso Tjër Di",
} as const;

/**
 * Questions for Panama's Provinces & Comarcas quiz.
 */
const PANAMA_PROVINCE_COMARCA_QUESTIONS = Object.entries(
  PANAMA_PROVINCE_COMARCA_NAMES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

/**
 * Quiz configuration for Panama's provinces and province-level comarcas.
 */
export const panamaProvincesComarcasQuiz: FeatureQuiz = {
  id: "panama-provinces-comarcas",
  name: "Provinces & Comarcas",
  description: `Learn all ${PANAMA_PROVINCE_COMARCA_QUESTIONS.length} provinces and province-level comarcas of Panama.`,

  kind: "feature",
  mapId: "panama-provinces-comarcas",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PANAMA_PROVINCE_COMARCA_QUESTIONS,
};
