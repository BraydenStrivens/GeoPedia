/**
 * Quiz for identifying Puerto Rico's barrios.
 *
 * Barrios can be grouped by their parent municipality. Duplicate barrio
 * names are disambiguated by municipality when necessary.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PUERTO_RICO_BARRIOS_BY_ID,
  PUERTO_RICO_MUNICIPALITIES_BY_ID,
} from "./data/admin";

const PUERTO_RICO_BARRIO_QUESTIONS = Object.entries(
  PUERTO_RICO_BARRIOS_BY_ID,
).map(([id, barrio]) => ({
  answer: id,
  display: barrio.name,
}));

export const puertoRicoBarriosQuiz: FeatureQuiz = {
  id: "puerto-rico-barrios",
  name: "Barrios",
  description: `Learn all ${PUERTO_RICO_BARRIO_QUESTIONS.length} mapped barrios of Puerto Rico, with filters that let you practice barrios by municipality.`,

  kind: "feature",
  mapId: "puerto-rico-barrios",

  answerProperty: "barrio_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "municipality_id",
        label: "Municipality",
        valueType: "string",
        valueLabels: PUERTO_RICO_MUNICIPALITIES_BY_ID,
      },
    ],
  },

  questions: PUERTO_RICO_BARRIO_QUESTIONS,
};
