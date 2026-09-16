import type { FeatureQuiz } from "@/types/quiz";

/**
 * Ecuador's two-digit province postal-code prefixes.
 *
 * Ecuadorian postal codes contain six digits. The first two digits identify
 * the province. These prefixes correspond to the province IDs used by
 * GeoPedia's processed Ecuador province GeoJSON after removing the `EC`
 * prefix from each stable administrative ID.
 */
const ECUADOR_POSTAL_CODE_QUESTIONS = [
  { answer: "EC01", display: "01----" },
  { answer: "EC02", display: "02----" },
  { answer: "EC03", display: "03----" },
  { answer: "EC04", display: "04----" },
  { answer: "EC05", display: "05----" },
  { answer: "EC06", display: "06----" },
  { answer: "EC07", display: "07----" },
  { answer: "EC08", display: "08----" },
  { answer: "EC09", display: "09----" },
  { answer: "EC10", display: "10----" },
  { answer: "EC11", display: "11----" },
  { answer: "EC12", display: "12----" },
  { answer: "EC13", display: "13----" },
  { answer: "EC14", display: "14----" },
  { answer: "EC15", display: "15----" },
  { answer: "EC16", display: "16----" },
  { answer: "EC17", display: "17----" },
  { answer: "EC18", display: "18----" },
  { answer: "EC19", display: "19----" },
  { answer: "EC20", display: "20----" },
  { answer: "EC21", display: "21----" },
  { answer: "EC22", display: "22----" },
  { answer: "EC23", display: "23----" },
  { answer: "EC24", display: "24----" },
] as const;

/**
 * Description shown for Ecuador's two-digit postal-code quiz.
 */
const ECUADOR_POSTAL_CODES_DESCRIPTION =
  `Learn all ${ECUADOR_POSTAL_CODE_QUESTIONS.length} two-digit province postal ` +
  `code prefixes used across Ecuador. Ecuadorian postal codes contain six ` +
  `digits, with the first two digits identifying the province.`;

/**
 * Quiz for identifying Ecuador's provinces from their two-digit postal-code
 * prefixes.
 */
export const ecuadorPostalCodes2DigitQuiz: FeatureQuiz = {
  id: "ecuador-postal-codes",
  name: "2-Digit Postal Codes",
  description: ECUADOR_POSTAL_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: [...ECUADOR_POSTAL_CODE_QUESTIONS],
};
