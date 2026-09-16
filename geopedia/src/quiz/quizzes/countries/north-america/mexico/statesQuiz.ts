import type { FeatureQuiz } from "@/types/quiz";

/**
 * Full Mexican state and federal-entity names keyed by their two-digit INEGI ID.
 */
export const MEXICO_STATE_NAMES_BY_ID = {
  "01": "Aguascalientes",
  "02": "Baja California",
  "03": "Baja California Sur",
  "04": "Campeche",
  "05": "Coahuila de Zaragoza",
  "06": "Colima",
  "07": "Chiapas",
  "08": "Chihuahua",
  "09": "Ciudad de México",
  "10": "Durango",
  "11": "Guanajuato",
  "12": "Guerrero",
  "13": "Hidalgo",
  "14": "Jalisco",
  "15": "México",
  "16": "Michoacán de Ocampo",
  "17": "Morelos",
  "18": "Nayarit",
  "19": "Nuevo León",
  "20": "Oaxaca",
  "21": "Puebla",
  "22": "Querétaro",
  "23": "Quintana Roo",
  "24": "San Luis Potosí",
  "25": "Sinaloa",
  "26": "Sonora",
  "27": "Tabasco",
  "28": "Tamaulipas",
  "29": "Tlaxcala",
  "30": "Veracruz de Ignacio de la Llave",
  "31": "Yucatán",
  "32": "Zacatecas",
} as const;

/**
 * Questions for Mexico's states and federal entities quiz.
 */
const MEXICO_STATE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(MEXICO_STATE_NAMES_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

/**
 * User-facing description for Mexico's states quiz.
 */
const MEXICO_STATES_DESCRIPTION =
  `Learn all ${MEXICO_STATE_QUESTIONS.length} states and federal entities ` +
  `of Mexico.`;

/**
 * Full-name quiz for Mexico's states and federal entities.
 */
export const mexicoStatesQuiz: FeatureQuiz = {
  id: "mexico-states",
  name: "States",
  description: MEXICO_STATES_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: MEXICO_STATE_QUESTIONS,
};
