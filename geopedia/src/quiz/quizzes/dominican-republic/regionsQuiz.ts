import type { FeatureQuiz } from "@/types/quiz";

/**
 * Dominican Republic administrative region names keyed by their normalized
 * two-digit ONE region IDs.
 */
export const DOMINICAN_REPUBLIC_REGION_NAMES_BY_ID: Record<
  string,
  string
> = {
  "01": "Cibao Nordeste",
  "02": "Cibao Noroeste",
  "03": "Cibao Norte",
  "04": "Cibao Sur",
  "05": "El Valle",
  "06": "Enriquillo",
  "07": "Higuamo",
  "08": "Ozama",
  "09": "Valdesia",
  "10": "Yuma",
};

/**
 * Questions for the Dominican Republic's regions quiz.
 */
const DOMINICAN_REPUBLIC_REGION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(DOMINICAN_REPUBLIC_REGION_NAMES_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

/**
 * User-facing description for the Dominican Republic's regions quiz.
 */
const DOMINICAN_REPUBLIC_REGIONS_DESCRIPTION =
  `Learn all ${DOMINICAN_REPUBLIC_REGION_QUESTIONS.length} administrative ` +
  `regions of the Dominican Republic.`;

/**
 * Quiz configuration for the Dominican Republic's 10 administrative regions.
 */
export const dominicanRepublicRegionsQuiz: FeatureQuiz = {
  id: "dominican-republic-regions",
  name: "Dominican Republic Regions",
  description: DOMINICAN_REPUBLIC_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "dominican-republic-regions",

  answerProperty: "region_id",
  answerType: "single",

  questions: DOMINICAN_REPUBLIC_REGION_QUESTIONS,
};
