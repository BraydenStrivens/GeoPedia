import type { FeatureQuiz } from "@/types/quiz";

const BOLIVIA_AREA_CODE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "2" },
  { answer: "3" },
  { answer: "4" },
];

const BOLIVIA_AREA_CODES_DESCRIPTION =
  `Learn all ${BOLIVIA_AREA_CODE_QUESTIONS.length} geographic landline area ` +
  `codes used across Bolivia. Landlines use ` +
  `a 1-digit regional area code followed by a 7-digit subscriber number, ` +
  `such as +591 2 212 3456 in the western region or +591 4 456 7890 in the ` +
  `central and southern region. Mobile numbers do not use geographic area ` +
  `codes and instead contain 8 digits beginning with 6 or 7, such as ` +
  `+591 712 34567.`;

export const boliviaAreaCodesQuiz: FeatureQuiz = {
  id: "bolivia-area-codes",
  name: "Area Codes",
  description: BOLIVIA_AREA_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "bolivia-area-codes",

  answerProperty: "area_code",
  answerType: "single",

  questions: BOLIVIA_AREA_CODE_QUESTIONS,
};
