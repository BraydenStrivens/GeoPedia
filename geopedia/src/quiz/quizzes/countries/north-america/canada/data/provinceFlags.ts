/**
 * Static question data for Canada's province and territory flag quiz.
 *
 * Each question maps a province or territory name to its corresponding
 * flag image stored in GeoPedia's public data.
 */

import { FeatureQuiz } from "@/types/quiz";

export const CANADA_PROVINCE_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  [
    {
      answer: "Newfoundland and Labrador",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/10.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Prince Edward Island",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/11.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Nova Scotia",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/12.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "New Brunswick",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/13.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Quebec",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/24.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Ontario",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/35.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Manitoba",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/46.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Saskatchewan",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/47.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Alberta",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/48.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "British Columbia",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/59.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Yukon",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/60.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Northwest Territories",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/61.svg",
        alt: "Province and territory flag",
      },
    },
    {
      answer: "Nunavut",
      prompt: {
        type: "image",
        imageUrl: "/data/countries/canada/flags/62.svg",
        alt: "Province and territory flag",
      },
    },
  ];
