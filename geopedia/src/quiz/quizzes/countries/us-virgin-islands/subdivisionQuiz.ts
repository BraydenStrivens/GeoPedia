import type { FeatureQuiz } from "@/types/quiz";

import { US_VIRGIN_ISLANDS_ISLAND_NAMES_BY_ID } from "./islandsQuiz";

/**
 * Questions for the U.S. Virgin Islands subdivisions quiz.
 *
 * Repeated subdivision names are disambiguated with their parent island.
 */
const US_VIRGIN_ISLANDS_SUBDIVISION_QUESTIONS = [
  {
    answer: "14107722B43744720873682",
    display: "Anna's Hope Village",
  },
  {
    answer: "14107722B79998694319746",
    display: "Christiansted",
  },
  {
    answer: "14107722B33559227839929",
    display: "East End (St. Croix)",
  },
  {
    answer: "14107722B15861276143824",
    display: "Frederiksted",
  },
  {
    answer: "14107722B85576057808906",
    display: "Northcentral",
  },
  {
    answer: "14107722B90781227780181",
    display: "Northwest",
  },
  {
    answer: "14107722B29624786914200",
    display: "Sion Farm",
  },
  {
    answer: "14107722B28780315816844",
    display: "Southcentral",
  },
  {
    answer: "14107722B42287109537478",
    display: "Southwest",
  },

  {
    answer: "14107722B57080281041215",
    display: "Central",
  },
  {
    answer: "14107722B12871426157568",
    display: "Coral Bay",
  },
  {
    answer: "14107722B26143784528084",
    display: "Cruz Bay",
  },
  {
    answer: "14107722B55601588722947",
    display: "East End (St. John)",
  },

  {
    answer: "14107722B76650624566102",
    display: "Charlotte Amalie",
  },
  {
    answer: "14107722B29975845079470",
    display: "East End (St. Thomas)",
  },
  {
    answer: "14107722B24288160029538",
    display: "Northside",
  },
  {
    answer: "14107722B32705273814462",
    display: "Southside",
  },
  {
    answer: "14107722B9156851144334",
    display: "Tutu",
  },
  {
    answer: "14107722B91344262939858",
    display: "Water Island",
  },
  {
    answer: "14107722B91101269147428",
    display: "West End",
  },
];

/**
 * Quiz configuration for the U.S. Virgin Islands' subdivisions.
 */
export const usVirginIslandsSubdivisionsQuiz: FeatureQuiz = {
  id: "us-virgin-islands-subdivisions",
  name: "Subdivisions",
  description: `Learn all ${US_VIRGIN_ISLANDS_SUBDIVISION_QUESTIONS.length} subdivisions of the U.S. Virgin Islands, with filters that let you practice subdivisions by island.`,

  kind: "feature",
  mapId: "us-virgin-islands-subdivisions",

  answerProperty: "subdivision_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "island_id",
        label: "Island",
        valueType: "string",
        valueLabels: US_VIRGIN_ISLANDS_ISLAND_NAMES_BY_ID,
      },
    ],
  },

  questions: US_VIRGIN_ISLANDS_SUBDIVISION_QUESTIONS,
};
