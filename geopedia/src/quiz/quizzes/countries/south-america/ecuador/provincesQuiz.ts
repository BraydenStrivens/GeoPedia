import type { FeatureQuiz } from "@/types/quiz";

/**
 * Ecuador's 24 provinces.
 *
 * The IDs correspond to the official ADM1 PCODE values retained from the
 * processed Ecuador administrative-boundary data.
 */
const ECUADOR_PROVINCE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "EC01", display: "Azuay" },
  { answer: "EC02", display: "Bolívar" },
  { answer: "EC03", display: "Cañar" },
  { answer: "EC04", display: "Carchi" },
  { answer: "EC05", display: "Cotopaxi" },
  { answer: "EC06", display: "Chimborazo" },
  { answer: "EC07", display: "El Oro" },
  { answer: "EC08", display: "Esmeraldas" },
  { answer: "EC09", display: "Guayas" },
  { answer: "EC10", display: "Imbabura" },
  { answer: "EC11", display: "Loja" },
  { answer: "EC12", display: "Los Ríos" },
  { answer: "EC13", display: "Manabí" },
  { answer: "EC14", display: "Morona Santiago" },
  { answer: "EC15", display: "Napo" },
  { answer: "EC16", display: "Pastaza" },
  { answer: "EC17", display: "Pichincha" },
  { answer: "EC18", display: "Tungurahua" },
  { answer: "EC19", display: "Zamora Chinchipe" },
  { answer: "EC20", display: "Galápagos" },
  { answer: "EC21", display: "Sucumbíos" },
  { answer: "EC22", display: "Orellana" },
  { answer: "EC23", display: "Santo Domingo de los Tsáchilas" },
  { answer: "EC24", display: "Santa Elena" },
];

/**
 * Description shown for Ecuador's Provinces quiz.
 */
const ECUADOR_PROVINCES_DESCRIPTION =
  `Learn all ${ECUADOR_PROVINCE_QUESTIONS.length} provinces of Ecuador and ` +
  `where they are located across the country.`;

/**
 * Quiz configuration for Ecuador's provinces.
 */
export const ecuadorProvincesQuiz: FeatureQuiz = {
  id: "ecuador-provinces",
  name: "Provinces",
  description: ECUADOR_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: ECUADOR_PROVINCE_QUESTIONS,
};
