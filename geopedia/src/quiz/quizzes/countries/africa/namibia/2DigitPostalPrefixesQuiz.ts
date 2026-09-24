/**
 * Feature quiz configuration for Namibia's 2-digit postal code prefixes.
 *
 * Namibian post codes contain five digits. The first two digits identify the
 * political region, while the remaining three identify a more specific postal
 * location. For example, Windhoek uses 10005 and Swakopmund uses 13001.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

const NAMIBIA_2_DIGIT_POSTAL_PREFIX_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "NA05", display: "10---" }, // Khomas
    { answer: "NA09", display: "11---" }, // Omaheke
    { answer: "NA07", display: "12---" }, // Otjozondjupa
    { answer: "NA02", display: "13---" }, // Erongo
    { answer: "NA11", display: "14---" }, // Oshikoto
    { answer: "NA10", display: "15---" }, // Oshana
    { answer: "NA08", display: "16---" }, // Omusati
    { answer: "NA12", display: "17---" }, // Ohangwena
    { answer: "NA13", display: "18---" }, // Kavango West
    { answer: "NA14", display: "19---" }, // Kavango East
    { answer: "NA01", display: "20---" }, // Zambezi
    { answer: "NA04", display: "21---" }, // Kunene
    { answer: "NA06", display: "22---" }, // Hardap
    { answer: "NA03", display: "23---" }, // //Karas
  ];

const NAMIBIA_2_DIGIT_POSTAL_PREFIXES_DESCRIPTION =
  `Learn all ${NAMIBIA_2_DIGIT_POSTAL_PREFIX_QUESTIONS.length} of Namibia's ` +
  "2-digit postal code prefixes. Namibian post codes contain 5 digits, with " +
  "the first 2 identifying the political region. For example, Windhoek uses " +
  "10005 and Swakopmund uses 13001.";

export const namibia2DigitPostalPrefixesQuiz: FeatureQuiz = {
  id: "namibia-2-digit-postal-prefixes",
  name: "2-Digit Postal Code Prefixes",
  description: NAMIBIA_2_DIGIT_POSTAL_PREFIXES_DESCRIPTION,

  kind: "feature",
  mapId: "namibia-regions",

  answerProperty: "region_id",
  answerType: "single",

  questions: NAMIBIA_2_DIGIT_POSTAL_PREFIX_QUESTIONS,
};
