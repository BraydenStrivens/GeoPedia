import type { FeatureQuiz } from "@/types/quiz";

/**
 * Brazil's geographic-region names keyed by their official IBGE region IDs.
 */
export const BRAZIL_REGION_NAMES_BY_ID = {
  "1": "Norte",
  "2": "Nordeste",
  "3": "Sudeste",
  "4": "Sul",
  "5": "Centro-Oeste",
} as const;

/**
 * Questions for Brazil's Regions quiz.
 */
const BRAZIL_REGION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_REGION_NAMES_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

/**
 * Description shown for Brazil's Regions quiz.
 */
const BRAZIL_REGIONS_DESCRIPTION =
  `Learn all ${BRAZIL_REGION_QUESTIONS.length} official geographic regions ` +
  `of Brazil.`;

/**
 * Quiz configuration for Brazil's geographic regions.
 */
export const brazilRegionsQuiz: FeatureQuiz = {
  id: "brazil-regions",
  name: "Regions",
  description: BRAZIL_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-regions",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: BRAZIL_REGION_QUESTIONS,
};
