import type { FeatureQuiz } from "@/types/quiz";

/**
 * Brazil's two-digit geographic telephone area codes.
 */
const BRAZIL_PHONE_CODE_2_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "11" },
    { answer: "12" },
    { answer: "13" },
    { answer: "14" },
    { answer: "15" },
    { answer: "16" },
    { answer: "17" },
    { answer: "18" },
    { answer: "19" },
    { answer: "21" },
    { answer: "22" },
    { answer: "24" },
    { answer: "27" },
    { answer: "28" },
    { answer: "31" },
    { answer: "32" },
    { answer: "33" },
    { answer: "34" },
    { answer: "35" },
    { answer: "37" },
    { answer: "38" },
    { answer: "41" },
    { answer: "42" },
    { answer: "43" },
    { answer: "44" },
    { answer: "45" },
    { answer: "46" },
    { answer: "47" },
    { answer: "48" },
    { answer: "49" },
    { answer: "51" },
    { answer: "53" },
    { answer: "54" },
    { answer: "55" },
    { answer: "61" },
    { answer: "62" },
    { answer: "63" },
    { answer: "64" },
    { answer: "65" },
    { answer: "66" },
    { answer: "67" },
    { answer: "68" },
    { answer: "69" },
    { answer: "71" },
    { answer: "73" },
    { answer: "74" },
    { answer: "75" },
    { answer: "77" },
    { answer: "79" },
    { answer: "81" },
    { answer: "82" },
    { answer: "83" },
    { answer: "84" },
    { answer: "85" },
    { answer: "86" },
    { answer: "87" },
    { answer: "88" },
    { answer: "89" },
    { answer: "91" },
    { answer: "92" },
    { answer: "93" },
    { answer: "94" },
    { answer: "95" },
    { answer: "96" },
    { answer: "97" },
    { answer: "98" },
    { answer: "99" },
  ];

/**
 * Description shown for Brazil's 2-Digit Area Codes quiz.
 */
/**
 * Description shown for Brazil's 2-Digit Area Codes quiz.
 */
const BRAZIL_PHONE_CODES_2_DIGIT_DESCRIPTION =
  `Learn all ${BRAZIL_PHONE_CODE_2_DIGIT_QUESTIONS.length} two-digit ` +
  `geographic telephone area codes used across Brazil. Area codes commonly ` +
  `appear before the local number as (XX) or XX followed by a space. The ` +
  `remaining telephone number contains 8 or 9 digits.`;

/**
 * Quiz configuration for Brazil's two-digit telephone area codes.
 */
export const brazilPhoneCodes2DigitQuiz: FeatureQuiz = {
  id: "brazil-phone-codes-2-digit",
  name: "2-Digit Area Codes",
  description: BRAZIL_PHONE_CODES_2_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-phone-codes-2-digit",

  answerProperty: "phone_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "phone_code_1_digit",
        label: "First Digit",
        valueType: "string",
      },
    ],
  },

  questions: BRAZIL_PHONE_CODE_2_DIGIT_QUESTIONS,
};
