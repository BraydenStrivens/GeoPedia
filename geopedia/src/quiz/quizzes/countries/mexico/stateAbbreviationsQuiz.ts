import type { FeatureQuiz } from "@/types/quiz";

/**
 * Conventional Mexican state and federal-entity abbreviations keyed by their
 * two-digit INEGI ID.
 */
export const MEXICO_STATE_ABBREVIATIONS_BY_ID = {
  "01": "Ags.",
  "02": "B.C.",
  "03": "B.C.S.",
  "04": "Camp.",
  "05": "Coah.",
  "06": "Col.",
  "07": "Chis.",
  "08": "Chih.",
  "09": "CDMX",
  "10": "Dgo.",
  "11": "Gto.",
  "12": "Gro.",
  "13": "Hgo.",
  "14": "Jal.",
  "15": "Méx.",
  "16": "Mich.",
  "17": "Mor.",
  "18": "Nay.",
  "19": "N.L.",
  "20": "Oax.",
  "21": "Pue.",
  "22": "Qro.",
  "23": "Q. Roo",
  "24": "S.L.P.",
  "25": "Sin.",
  "26": "Son.",
  "27": "Tab.",
  "28": "Tamps.",
  "29": "Tlax.",
  "30": "Ver.",
  "31": "Yuc.",
  "32": "Zac.",
} as const;

/**
 * Questions for Mexico's state abbreviations quiz.
 */
const MEXICO_STATE_ABBREVIATION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(MEXICO_STATE_ABBREVIATIONS_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

/**
 * User-facing description for Mexico's state abbreviations quiz.
 */
const MEXICO_STATE_ABBREVIATIONS_DESCRIPTION =
  `Learn the conventional abbreviations for all ` +
  `${MEXICO_STATE_ABBREVIATION_QUESTIONS.length} Mexican federal entities.`;

/**
 * Quiz for learning conventional abbreviations of Mexico's states and
 * federal entities.
 */
export const mexicoStateAbbreviationsQuiz: FeatureQuiz = {
  id: "mexico-state-abbreviations",
  name: "State Abbreviations",
  description: MEXICO_STATE_ABBREVIATIONS_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: MEXICO_STATE_ABBREVIATION_QUESTIONS,
};
