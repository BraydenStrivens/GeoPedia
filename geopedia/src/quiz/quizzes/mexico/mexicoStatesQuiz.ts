import type { FeatureQuiz } from "@/types/quiz";

/**
 * Mexico's 32 federal entities.
 *
 * The IDs correspond to INEGI's official two-digit `CVE_ENT` identifiers used
 * by the processed Mexico states GeoJSON.
 *
 * Keeping the stable INEGI identifier as the quiz answer value means display
 * names can be changed independently without affecting feature matching.
 */
const MEXICO_STATE_QUESTIONS = [
  { answer: "01", display: "Aguascalientes" },
  { answer: "02", display: "Baja California" },
  { answer: "03", display: "Baja California Sur" },
  { answer: "04", display: "Campeche" },
  { answer: "05", display: "Coahuila de Zaragoza" },
  { answer: "06", display: "Colima" },
  { answer: "07", display: "Chiapas" },
  { answer: "08", display: "Chihuahua" },
  { answer: "09", display: "Ciudad de México" },
  { answer: "10", display: "Durango" },
  { answer: "11", display: "Guanajuato" },
  { answer: "12", display: "Guerrero" },
  { answer: "13", display: "Hidalgo" },
  { answer: "14", display: "Jalisco" },
  { answer: "15", display: "México" },
  { answer: "16", display: "Michoacán de Ocampo" },
  { answer: "17", display: "Morelos" },
  { answer: "18", display: "Nayarit" },
  { answer: "19", display: "Nuevo León" },
  { answer: "20", display: "Oaxaca" },
  { answer: "21", display: "Puebla" },
  { answer: "22", display: "Querétaro" },
  { answer: "23", display: "Quintana Roo" },
  { answer: "24", display: "San Luis Potosí" },
  { answer: "25", display: "Sinaloa" },
  { answer: "26", display: "Sonora" },
  { answer: "27", display: "Tabasco" },
  { answer: "28", display: "Tamaulipas" },
  { answer: "29", display: "Tlaxcala" },
  { answer: "30", display: "Veracruz de Ignacio de la Llave" },
  { answer: "31", display: "Yucatán" },
  { answer: "32", display: "Zacatecas" },
] as const;

/**
 * Full-name quiz for Mexico's 32 federal entities.
 *
 * This quiz uses INEGI state IDs as answers and displays the corresponding
 * full entity names to the user.
 */
export const mexicoStatesQuiz: FeatureQuiz = {
  id: "mexico-states",
  name: "Mexico States",
  description: `Learn all ${MEXICO_STATE_QUESTIONS.length} states and federal entities of Mexico.`,

  kind: "feature",
  mapId: "mexico-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: [...MEXICO_STATE_QUESTIONS],
};
