/**
 * Defines the United States 2-digit ZIP-code prefix quiz.
 *
 * Each question represents the first two digits of a five-digit ZIP code. The
 * remaining digits are displayed as hyphens so the user can clearly see that
 * the question represents a ZIP-code prefix rather than a complete ZIP code.
 *
 * The quiz also supports property-based grouping by state. Because one ZIP
 * prefix region may overlap multiple states, the GeoJSON stores `states` as a
 * string array.
 */

import { US_SUBDIVISION_NAMES_BY_ABBREVIATION } from "@/constants/usSubdivisions";
import type { FeatureQuiz } from "@/types/quiz";

const US_ZIP_2_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "00", display: "00---" },
  { answer: "01", display: "01---" },
  { answer: "02", display: "02---" },
  { answer: "03", display: "03---" },
  { answer: "04", display: "04---" },
  { answer: "05", display: "05---" },
  { answer: "06", display: "06---" },
  { answer: "07", display: "07---" },
  { answer: "08", display: "08---" },
  { answer: "10", display: "10---" },
  { answer: "11", display: "11---" },
  { answer: "12", display: "12---" },
  { answer: "13", display: "13---" },
  { answer: "14", display: "14---" },
  { answer: "15", display: "15---" },
  { answer: "16", display: "16---" },
  { answer: "17", display: "17---" },
  { answer: "18", display: "18---" },
  { answer: "19", display: "19---" },
  { answer: "20", display: "20---" },
  { answer: "21", display: "21---" },
  { answer: "22", display: "22---" },
  { answer: "23", display: "23---" },
  { answer: "24", display: "24---" },
  { answer: "25", display: "25---" },
  { answer: "26", display: "26---" },
  { answer: "27", display: "27---" },
  { answer: "28", display: "28---" },
  { answer: "29", display: "29---" },
  { answer: "30", display: "30---" },
  { answer: "31", display: "31---" },
  { answer: "32", display: "32---" },
  { answer: "33", display: "33---" },
  { answer: "34", display: "34---" },
  { answer: "35", display: "35---" },
  { answer: "36", display: "36---" },
  { answer: "37", display: "37---" },
  { answer: "38", display: "38---" },
  { answer: "39", display: "39---" },
  { answer: "40", display: "40---" },
  { answer: "41", display: "41---" },
  { answer: "42", display: "42---" },
  { answer: "43", display: "43---" },
  { answer: "44", display: "44---" },
  { answer: "45", display: "45---" },
  { answer: "46", display: "46---" },
  { answer: "47", display: "47---" },
  { answer: "48", display: "48---" },
  { answer: "49", display: "49---" },
  { answer: "50", display: "50---" },
  { answer: "51", display: "51---" },
  { answer: "52", display: "52---" },
  { answer: "53", display: "53---" },
  { answer: "54", display: "54---" },
  { answer: "55", display: "55---" },
  { answer: "56", display: "56---" },
  { answer: "57", display: "57---" },
  { answer: "58", display: "58---" },
  { answer: "59", display: "59---" },
  { answer: "60", display: "60---" },
  { answer: "61", display: "61---" },
  { answer: "62", display: "62---" },
  { answer: "63", display: "63---" },
  { answer: "64", display: "64---" },
  { answer: "65", display: "65---" },
  { answer: "66", display: "66---" },
  { answer: "67", display: "67---" },
  { answer: "68", display: "68---" },
  { answer: "69", display: "69---" },
  { answer: "70", display: "70---" },
  { answer: "71", display: "71---" },
  { answer: "72", display: "72---" },
  { answer: "73", display: "73---" },
  { answer: "74", display: "74---" },
  { answer: "75", display: "75---" },
  { answer: "76", display: "76---" },
  { answer: "77", display: "77---" },
  { answer: "78", display: "78---" },
  { answer: "79", display: "79---" },
  { answer: "80", display: "80---" },
  { answer: "81", display: "81---" },
  { answer: "82", display: "82---" },
  { answer: "83", display: "83---" },
  { answer: "84", display: "84---" },
  { answer: "85", display: "85---" },
  { answer: "86", display: "86---" },
  { answer: "87", display: "87---" },
  { answer: "88", display: "88---" },
  { answer: "89", display: "89---" },
  { answer: "90", display: "90---" },
  { answer: "91", display: "91---" },
  { answer: "92", display: "92---" },
  { answer: "93", display: "93---" },
  { answer: "94", display: "94---" },
  { answer: "95", display: "95---" },
  { answer: "96", display: "96---" },
  { answer: "97", display: "97---" },
  { answer: "98", display: "98---" },
  { answer: "99", display: "99---" },
];

const US_ZIP_2_DESCRIPTION = `Learn all ${US_ZIP_2_QUESTIONS.length} US 2-digit ZIP code regions, including US territories, with filtering options to practice any desired subset.`;

/**
 * Quiz definition for identifying US 2-digit ZIP-code regions.
 */
export const usZip2Quiz: FeatureQuiz = {
  id: "us-zip-2",
  name: "US 2-Digit ZIP Codes",
  description: US_ZIP_2_DESCRIPTION,

  mapId: "us-zip-2",
  kind: "feature",

  answerProperty: "zip",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "states",
        label: "State",
        valueType: "string-array",
        valueLabels: US_SUBDIVISION_NAMES_BY_ABBREVIATION,
      },
    ],
  },

  questions: US_ZIP_2_QUESTIONS,
};
