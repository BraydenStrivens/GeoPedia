import type { FeatureQuiz } from "@/types/quiz";

export const PERU_REGIONS_BY_ID = {
  PE01: "Amazonas",
  PE02: "Ancash",
  PE03: "Apurimac",
  PE04: "Arequipa",
  PE05: "Ayacucho",
  PE06: "Cajamarca",
  PE07: "Callao",
  PE08: "Cusco",
  PE09: "Huancavelica",
  PE10: "Huanuco",
  PE11: "Ica",
  PE12: "Junin",
  PE13: "La Libertad",
  PE14: "Lambayeque",
  PE15: "Lima",
  PE16: "Loreto",
  PE17: "Madre de Dios",
  PE18: "Moquegua",
  PE19: "Pasco",
  PE20: "Piura",
  PE21: "Puno",
  PE22: "San Martin",
  PE23: "Tacna",
  PE24: "Tumbes",
  PE25: "Ucayali",
} as const;

export const PERU_REGION_VALUE_LABELS = PERU_REGIONS_BY_ID;

const PERU_REGION_QUESTIONS = Object.entries(PERU_REGIONS_BY_ID).map(
  ([regionId, region]) => ({
    answer: regionId,
    display: region,
  }),
);

const PERU_REGIONS_DESCRIPTION =
  `Learn all ${PERU_REGION_QUESTIONS.length} first-level administrative ` +
  `regions of Peru, including the Constitutional Province of Callao.`;

export const peruRegionsQuiz: FeatureQuiz = {
  id: "peru-regions",
  name: "Regions",
  description: PERU_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "peru-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PERU_REGION_QUESTIONS,
};
