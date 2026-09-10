/**
 * Defines the Canada province and territory flags quiz.
 *
 * This quiz uses the shared Canada provinces map and asks the user to identify
 * all 10 provinces and 3 territories by their flags. Each quiz answer
 * corresponds to the `name` property in the processed Canada province and
 * territory GeoJSON dataset.
 *
 * Flag assets use Statistics Canada's stable PRUID identifiers as filenames,
 * matching the identifiers retained in the processed boundary dataset.
 */

import type { FeatureQuiz } from "@/types/quiz";

const CANADA_PROVINCE_FLAG_QUESTIONS: FeatureQuiz["questions"] = [
  {
    answer: "Newfoundland and Labrador",
    display: "Newfoundland and Labrador",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/10.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Prince Edward Island",
    display: "Prince Edward Island",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/11.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Nova Scotia",
    display: "Nova Scotia",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/12.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "New Brunswick",
    display: "New Brunswick",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/13.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Quebec",
    display: "Quebec",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/24.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Ontario",
    display: "Ontario",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/35.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Manitoba",
    display: "Manitoba",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/46.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Saskatchewan",
    display: "Saskatchewan",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/47.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Alberta",
    display: "Alberta",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/48.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "British Columbia",
    display: "British Columbia",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/59.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Yukon",
    display: "Yukon",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/60.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Northwest Territories",
    display: "Northwest Territories",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/61.svg",
      alt: "Province and territory flag",
    },
  },
  {
    answer: "Nunavut",
    display: "Nunavut",
    prompt: {
      type: "image",
      imageUrl: "/data/countries/canada/flags/62.svg",
      alt: "Province and territory flag",
    },
  },
];

const CANADA_PROVINCE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${CANADA_PROVINCE_FLAG_QUESTIONS.length} Canadian provinces ` +
  `and territories by identifying each one on the map.`;

/**
 * Quiz definition for identifying Canadian provinces and territories by flag.
 */
export const canadaProvinceFlagsQuiz: FeatureQuiz = {
  id: "canada-province-flags",
  name: "Province and Territory Flags",
  description: CANADA_PROVINCE_FLAGS_DESCRIPTION,

  kind: "feature",
  mapId: "canada-provinces",

  answerProperty: "name",
  answerType: "single",

  questions: CANADA_PROVINCE_FLAG_QUESTIONS,
};
