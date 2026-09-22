/**
 * Defines Colombia's town pole-lamps quiz.
 *
 * Each question references a canonical town from Colombia's generated town
 * dataset and uses an image of a locally useful pole-lamp style as its prompt.
 * Town names, coordinates, populations, and other settlement metadata remain
 * owned by the canonical town dataset.
 */

import type { TownQuizConfig } from "@/types/quiz";

export const colombiaTownPoleLampsQuizConfig: TownQuizConfig = {
  id: "col-town-pole-lamps",
  name: "Colombia Town Pole Lamps",
  description:
    "Learn to identify 6 major Colombian towns by their distinctive pole lamps.",
  questions: [
    {
      townId: "3688689",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/colombia/pole-lamps/bogota_1.webp",
        alt: "Pole lamp in Bogotá",
      },
    },
    {
      townId: "3674962",
      prompt: {
        type: "image",
        imageUrl:
          "/data/countries/colombia/pole-lamps/medellin_1.webp",
        alt: "Pole lamp in Medellín",
      },
    },
    {
      townId: "3687925",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/colombia/pole-lamps/cali_1.webp",
        alt: "Pole lamp in Cali",
      },
    },
    {
      townId: "3689147",
      prompt: {
        type: "image",
        imageUrl:
          "/data/countries/colombia/pole-lamps/barranquilla_1.webp",
        alt: "Pole lamp in Barranquilla",
      },
    },
    {
      townId: "3688465",
      prompt: {
        type: "image",
        imageUrl:
          "/data/countries/colombia/pole-lamps/bucaramanga_1.webp",
        alt: "Pole lamp in Bucaramanga",
      },
    },
    {
      townId: "3680656",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/colombia/pole-lamps/ibague_1.webp",
        alt: "Pole lamp in Ibagué",
      },
    },
  ],
};
