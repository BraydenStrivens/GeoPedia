import type { FeatureQuiz } from "@/types/quiz";

const URUGUAY_PHONE_CODE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "UY01", display: "477-" },
  { answer: "UY02", display: "433-" },
  { answer: "UY03", display: "464-" },
  { answer: "UY04", display: "452-" },
  { answer: "UY05", display: "436-" },
  { answer: "UY06", display: "4364" },
  { answer: "UY07", display: "435-" },
  { answer: "UY08", display: "444-" },
  { answer: "UY09", display: "42--" },
  { answer: "UY10", display: "2---" },
  { answer: "UY11", display: "472-" },
  { answer: "UY12", display: "456-" },
  { answer: "UY13", display: "462-" },
  { answer: "UY14", display: "447-" },
  { answer: "UY15", display: "473-" },
  { answer: "UY16", display: "434-" },
  { answer: "UY17", display: "453-" },
  { answer: "UY18", display: "463-" },
  { answer: "UY19", display: "445-" },
];

const URUGUAY_PHONE_CODES_DESCRIPTION =
  `Learn all ${URUGUAY_PHONE_CODE_QUESTIONS.length} department landline ` +
  `telephone prefixes of Uruguay, which vary in length from prefixes such ` +
  `as 2---, 42--, 462-, and 4364. Landline numbers have 8 digits, such as 4522 4999, while ` +
  `mobile numbers use the local format 09X XXX XXX, such as 099 123 456.`;

export const uruguayPhoneCodesQuiz: FeatureQuiz = {
  id: "uruguay-phone-codes",
  name: "Telephone Codes",
  description: URUGUAY_PHONE_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "uruguay-departments",

  answerProperty: "department_id",
  answerType: "single",

  questions: URUGUAY_PHONE_CODE_QUESTIONS,
};
