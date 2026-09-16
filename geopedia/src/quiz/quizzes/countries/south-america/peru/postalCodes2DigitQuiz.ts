import type { FeatureQuiz } from "@/types/quiz";

const PERU_POSTAL_CODES_2_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "01", display: "01---" },
    { answer: "02", display: "02---" },
    { answer: "03", display: "03---" },
    { answer: "04", display: "04---" },
    { answer: "05", display: "05---" },
    { answer: "06", display: "06---" },
    { answer: "07", display: "07---" },
    { answer: "08", display: "08---" },
    { answer: "09", display: "09---" },
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
  ];

const PERU_POSTAL_2_DIGIT_CODES_DESCRIPTION =
  `Learn all ${PERU_POSTAL_CODES_2_DIGIT_QUESTIONS.length} 2-digit postal-code ` +
  `prefixes used across Peru. Peruvian postal codes contain 5 digits, with ` +
  `the first 2 digits identifying the region.`;

export const peruPostalCodes2DigitQuiz: FeatureQuiz = {
  id: "peru-postal-codes",
  name: "2 Digit Postal Codes",
  description: PERU_POSTAL_2_DIGIT_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "peru-regions",

  answerProperty: "postal_code_prefix",
  answerType: "single",

  questions: PERU_POSTAL_CODES_2_DIGIT_QUESTIONS,
};
