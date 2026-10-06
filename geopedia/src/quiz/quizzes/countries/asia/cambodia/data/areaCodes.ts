/**
 * Manually maintained Cambodia landline area-code quiz data.
 *
 * Each question uses the province ID as the geographic answer and displays
 * either its one-digit geographic prefix or full two-digit area code.
 * The leading trunk prefix 0 is retained in the displayed telephone notation.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

export const CAMBODIA_AREA_CODE_PREFIX_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "02", display: "02-" },
    { answer: "03", display: "03-" },
    { answer: "04", display: "04-" },
    { answer: "05", display: "05-" },
    { answer: "06", display: "06-" },
    { answer: "07", display: "07-" },
  ];

export const CAMBODIA_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "12", display: "023" },
  { answer: "08", display: "024" },
  { answer: "05", display: "025" },
  { answer: "04", display: "026" },

  { answer: "21", display: "032" },
  { answer: "07", display: "033" },
  { answer: "18", display: "034" },
  { answer: "09", display: "035" },
  { answer: "23", display: "036" },

  { answer: "03", display: "042" },
  { answer: "14", display: "043" },
  { answer: "20", display: "044" },
  { answer: "25", display: "045" },

  { answer: "15", display: "052" },
  { answer: "02", display: "053" },
  { answer: "01", display: "054" },
  { answer: "24", display: "055" },

  { answer: "06", display: "062" },
  { answer: "17", display: "063" },
  { answer: "13", display: "064" },
  { answer: "22", display: "065" },

  { answer: "10", display: "072" },
  { answer: "11", display: "073" },
  { answer: "19", display: "074" },
  { answer: "16", display: "075" },
];
