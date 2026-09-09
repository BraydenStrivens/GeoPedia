import type { FeatureQuiz } from "@/types/quiz";

import { DOMINICAN_REPUBLIC_REGION_NAMES_BY_ID } from "./regionsQuiz";

/**
 * Dominican Republic province names keyed by their normalized four-digit
 * ONE province IDs.
 */
export const DOMINICAN_REPUBLIC_PROVINCE_NAMES_BY_ID: Record<
  string,
  string
> = {
  "0101": "Duarte",
  "0102": "Hermanas Mirabal",
  "0103": "María Trinidad Sánchez",
  "0104": "Samaná",

  "0201": "Dajabón",
  "0202": "Monte Cristi",
  "0203": "Santiago Rodríguez",
  "0204": "Valverde",

  "0301": "Espaillat",
  "0302": "Puerto Plata",
  "0303": "Santiago",

  "0401": "La Vega",
  "0402": "Monseñor Nouel",
  "0403": "Sánchez Ramírez",

  "0501": "Elías Piña",
  "0502": "San Juan",

  "0601": "Baoruco",
  "0602": "Barahona",
  "0603": "Independencia",
  "0604": "Pedernales",

  "0701": "Hato Mayor",
  "0702": "Monte Plata",
  "0703": "San Pedro de Macorís",

  "0801": "Distrito Nacional",
  "0802": "Santo Domingo",

  "0901": "Azua",
  "0902": "Peravia",
  "0903": "San Cristóbal",
  "0904": "San José de Ocoa",

  "1001": "El Seibo",
  "1002": "La Altagracia",
  "1003": "La Romana",
};

/**
 * Quiz configuration for the Dominican Republic's 32 province-level
 * administrative divisions.
 */
export const dominicanRepublicProvincesQuiz: FeatureQuiz = {
  id: "dominican-republic-provinces",
  name: "Dominican Republic Provinces",
  description:
    "Learn the 31 provinces and Distrito Nacional of the Dominican Republic, with filters that let you practice provinces from any desired region or combination of regions.",

  kind: "feature",
  mapId: "dominican-republic-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: DOMINICAN_REPUBLIC_REGION_NAMES_BY_ID,
      },
    ],
  },

  questions: Object.entries(
    DOMINICAN_REPUBLIC_PROVINCE_NAMES_BY_ID,
  ).map(([answer, display]) => ({
    answer,
    display,
  })),
};
