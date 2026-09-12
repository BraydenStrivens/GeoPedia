import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_REGION_NAMES_BY_ID } from "./regionsQuiz";

/**
 * Brazil's state and Federal District names keyed by their official two-digit
 * IBGE identifiers.
 */
export const BRAZIL_STATE_NAMES_BY_ID = {
  "11": "Rondônia",
  "12": "Acre",
  "13": "Amazonas",
  "14": "Roraima",
  "15": "Pará",
  "16": "Amapá",
  "17": "Tocantins",
  "21": "Maranhão",
  "22": "Piauí",
  "23": "Ceará",
  "24": "Rio Grande do Norte",
  "25": "Paraíba",
  "26": "Pernambuco",
  "27": "Alagoas",
  "28": "Sergipe",
  "29": "Bahia",
  "31": "Minas Gerais",
  "32": "Espírito Santo",
  "33": "Rio de Janeiro",
  "35": "São Paulo",
  "41": "Paraná",
  "42": "Santa Catarina",
  "43": "Rio Grande do Sul",
  "50": "Mato Grosso do Sul",
  "51": "Mato Grosso",
  "52": "Goiás",
  "53": "Distrito Federal",
} as const;

/**
 * Questions for Brazil's States quiz.
 */
const BRAZIL_STATE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_STATE_NAMES_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

/**
 * Description shown for Brazil's States quiz.
 */
const BRAZIL_STATES_DESCRIPTION =
  `Learn all ${BRAZIL_STATE_QUESTIONS.length} state-level divisions of Brazil, ` +
  `including the Federal District.`;

/**
 * Quiz configuration for Brazil's states and Federal District.
 */
export const brazilStatesQuiz: FeatureQuiz = {
  id: "brazil-states",
  name: "States",
  description: BRAZIL_STATES_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-states",

  answerProperty: "id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: BRAZIL_REGION_NAMES_BY_ID,
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: BRAZIL_STATE_QUESTIONS,
};
