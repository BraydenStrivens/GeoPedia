import type { FeatureQuiz } from "@/types/quiz";

/**
 * Ecuador's provincial flags.
 */
const ECUADOR_PROVINCE_FLAG_QUESTIONS: FeatureQuiz["questions"] = [
  {
    answer: "EC01",
    display: "Azuay",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec01.svg",
      alt: "Azuay flag",
    },
  },
  {
    answer: "EC02",
    display: "Bolívar",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec02.svg",
      alt: "Bolívar flag",
    },
  },
  {
    answer: "EC03",
    display: "Cañar",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec03.svg",
      alt: "Cañar flag",
    },
  },
  {
    answer: "EC04",
    display: "Carchi",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec04.svg",
      alt: "Carchi flag",
    },
  },
  {
    answer: "EC05",
    display: "Cotopaxi",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec05.svg",
      alt: "Cotopaxi flag",
    },
  },
  {
    answer: "EC06",
    display: "Chimborazo",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec06.svg",
      alt: "Chimborazo flag",
    },
  },
  {
    answer: "EC07",
    display: "El Oro",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec07.svg",
      alt: "El Oro flag",
    },
  },
  {
    answer: "EC08",
    display: "Esmeraldas",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec08.svg",
      alt: "Esmeraldas flag",
    },
  },
  {
    answer: "EC09",
    display: "Guayas",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec09.svg",
      alt: "Guayas flag",
    },
  },
  {
    answer: "EC10",
    display: "Imbabura",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec10.svg",
      alt: "Imbabura flag",
    },
  },
  {
    answer: "EC11",
    display: "Loja",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec11.svg",
      alt: "Loja flag",
    },
  },
  {
    answer: "EC12",
    display: "Los Ríos",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec12.svg",
      alt: "Los Ríos flag",
    },
  },
  {
    answer: "EC13",
    display: "Manabí",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec13.svg",
      alt: "Manabí flag",
    },
  },
  {
    answer: "EC14",
    display: "Morona Santiago",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec14.svg",
      alt: "Morona Santiago flag",
    },
  },
  {
    answer: "EC15",
    display: "Napo",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec15.svg",
      alt: "Napo flag",
    },
  },
  {
    answer: "EC16",
    display: "Pastaza",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec16.svg",
      alt: "Pastaza flag",
    },
  },
  {
    answer: "EC17",
    display: "Pichincha",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec17.svg",
      alt: "Pichincha flag",
    },
  },
  {
    answer: "EC18",
    display: "Tungurahua",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec18.svg",
      alt: "Tungurahua flag",
    },
  },
  {
    answer: "EC19",
    display: "Zamora Chinchipe",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec19.svg",
      alt: "Zamora Chinchipe flag",
    },
  },
  {
    answer: "EC20",
    display: "Galápagos",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec20.svg",
      alt: "Galápagos flag",
    },
  },
  {
    answer: "EC21",
    display: "Sucumbíos",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec21.svg",
      alt: "Sucumbíos flag",
    },
  },
  {
    answer: "EC22",
    display: "Orellana",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec22.svg",
      alt: "Orellana flag",
    },
  },
  {
    answer: "EC23",
    display: "Santo Domingo de los Tsáchilas",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec23.svg",
      alt: "Santo Domingo de los Tsáchilas flag",
    },
  },
  {
    answer: "EC24",
    display: "Santa Elena",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/ecuador/flags/ec24.svg",
      alt: "Santa Elena flag",
    },
  },
];

/**
 * Description shown for Ecuador's Province Flags quiz.
 */
const ECUADOR_PROVINCE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${ECUADOR_PROVINCE_FLAG_QUESTIONS.length} provinces ` +
  `of Ecuador by identifying the corresponding province on the map.`;

/**
 * Quiz for identifying Ecuador's provinces from their flags.
 */
export const ecuadorProvinceFlagsQuiz: FeatureQuiz = {
  id: "ecuador-province-flags",
  name: "Province Flags",
  description: ECUADOR_PROVINCE_FLAGS_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: ECUADOR_PROVINCE_FLAG_QUESTIONS,
};
