import type { FeatureQuiz } from "@/types/quiz";

/**
 * Costa Rica province names keyed by their 1-digit administrative ID.
 *
 * These IDs also correspond to the first digit of Costa Rica's 5-digit
 * postal codes.
 */
export const COSTA_RICA_PROVINCE_NAMES_BY_ID = {
  "1": "San José",
  "2": "Alajuela",
  "3": "Cartago",
  "4": "Heredia",
  "5": "Guanacaste",
  "6": "Puntarenas",
  "7": "Limón",
} as const;

/**
 * Questions for Costa Rica's provinces.
 */
const COSTA_RICA_PROVINCE_QUESTIONS = Object.entries(
  COSTA_RICA_PROVINCE_NAMES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

/**
 * Province quiz for Costa Rica.
 */
export const costaRicaProvincesQuiz: FeatureQuiz = {
  id: "costa-rica-provinces",
  name: "Provinces",
  description: `Learn all ${COSTA_RICA_PROVINCE_QUESTIONS.length} provinces of Costa Rica.`,

  kind: "feature",
  mapId: "costa-rica-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: COSTA_RICA_PROVINCE_QUESTIONS,
};
