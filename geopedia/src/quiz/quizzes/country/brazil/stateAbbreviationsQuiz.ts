import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_REGION_NAMES_BY_ID } from "./regionsQuiz";

/**
 * Brazil's state and Federal District abbreviations keyed by their official
 * two-digit IBGE identifiers.
 */
export const BRAZIL_STATE_ABBREVIATIONS_BY_ID = {
  "11": "RO",
  "12": "AC",
  "13": "AM",
  "14": "RR",
  "15": "PA",
  "16": "AP",
  "17": "TO",
  "21": "MA",
  "22": "PI",
  "23": "CE",
  "24": "RN",
  "25": "PB",
  "26": "PE",
  "27": "AL",
  "28": "SE",
  "29": "BA",
  "31": "MG",
  "32": "ES",
  "33": "RJ",
  "35": "SP",
  "41": "PR",
  "42": "SC",
  "43": "RS",
  "50": "MS",
  "51": "MT",
  "52": "GO",
  "53": "DF",
} as const;

/**
 * Questions for Brazil's State Abbreviations quiz.
 */
const BRAZIL_STATE_ABBREVIATION_QUESTIONS: FeatureQuiz["questions"] =
  Object.values(BRAZIL_STATE_ABBREVIATIONS_BY_ID).map((answer) => ({
    answer,
  }));

/**
 * Description shown for Brazil's State Abbreviations quiz.
 */
const BRAZIL_STATE_ABBREVIATIONS_DESCRIPTION =
  `Learn all ${BRAZIL_STATE_ABBREVIATION_QUESTIONS.length} two-letter ` +
  `abbreviations used for Brazil's states and Federal District.`;

/**
 * Quiz configuration for Brazil's state and Federal District abbreviations.
 */
export const brazilStateAbbreviationsQuiz: FeatureQuiz = {
  id: "brazil-state-abbreviations",
  name: "State Abbreviations",
  description: BRAZIL_STATE_ABBREVIATIONS_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-states",

  answerProperty: "abbreviation",
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

  questions: BRAZIL_STATE_ABBREVIATION_QUESTIONS,
};
