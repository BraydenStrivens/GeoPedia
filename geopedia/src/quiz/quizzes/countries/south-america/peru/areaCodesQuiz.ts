import type { FeatureQuiz } from "@/types/quiz";

const PERU_AREA_CODE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "1", display: "1" },

  { answer: "41", display: "41" },
  { answer: "42", display: "42" },
  { answer: "43", display: "43" },
  { answer: "44", display: "44" },

  { answer: "51", display: "51" },
  { answer: "52", display: "52" },
  { answer: "53", display: "53" },
  { answer: "54", display: "54" },
  { answer: "56", display: "56" },

  { answer: "61", display: "61" },
  { answer: "62", display: "62" },
  { answer: "63", display: "63" },
  { answer: "64", display: "64" },
  { answer: "65", display: "65" },
  { answer: "66", display: "66" },
  { answer: "67", display: "67" },

  { answer: "72", display: "72" },
  { answer: "73", display: "73" },
  { answer: "74", display: "74" },
  { answer: "76", display: "76" },

  { answer: "82", display: "82" },
  { answer: "83", display: "83" },
  { answer: "84", display: "84" },
];

const PERU_AREA_CODES_DESCRIPTION =
  `Learn all ${PERU_AREA_CODE_QUESTIONS.length} geographic fixed-line ` +
  `telephone area codes used across Peru. ` +
  `Lima and Callao use the single-digit area code 1, as in +51 1 234 5678, ` +
  `while other regions use 2-digit area codes, such as +51 84 234 567 in ` +
  `Cusco. Mobile numbers do not use these geographic area codes and instead ` +
  `use a 9-digit number beginning with 9, such as +51 912 345 678. Filter by ` +
  `first digit to practice related groups of area codes.`;

export const peruAreaCodesQuiz: FeatureQuiz = {
  id: "peru-area-codes",
  name: "Area Codes",
  description: PERU_AREA_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "peru-regions",

  answerProperty: "phone_code",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "phone_code_first_digit",
        label: "First Digit",
        valueType: "string",
      },
    ],
  },

  questions: PERU_AREA_CODE_QUESTIONS,
};
