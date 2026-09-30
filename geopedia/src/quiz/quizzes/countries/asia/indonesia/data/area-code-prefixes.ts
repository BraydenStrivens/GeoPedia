/**
 * Generated quiz-question data for Indonesia's landline area-code prefixes.
 *
 * Source:
 * - /public/data/countries/indonesia/geojson/area-code-prefixes-1.geojson
 * - /public/data/countries/indonesia/geojson/area-code-prefixes-2.geojson
 *
 * Regenerate with:
 * python scripts/countries/asia/indonesia/generate/area-code-prefix-quiz-data.py
 *
 * Display convention:
 * - 1-digit prefix: answer "2" -> display "02-"
 * - 2-digit prefix: answer "21" -> display "021"
 *
 * The leading zero reflects how Indonesian landline area codes appear in-game.
 * The 1-digit set uses "-" to make the incomplete prefix explicit.
 */
import { FeatureQuizQuestion } from "@/types/quiz";

export const INDONESIA_AREA_CODE_PREFIX_1_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "2", display: "02-" },
  { answer: "3", display: "03-" },
  { answer: "4", display: "04-" },
  { answer: "5", display: "05-" },
  { answer: "6", display: "06-" },
  { answer: "7", display: "07-" },
  { answer: "9", display: "09-" },
];

export const INDONESIA_AREA_CODE_PREFIX_2_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "21", display: "021" },
  { answer: "22", display: "022" },
  { answer: "23", display: "023" },
  { answer: "24", display: "024" },
  { answer: "25", display: "025" },
  { answer: "26", display: "026" },
  { answer: "27", display: "027" },
  { answer: "28", display: "028" },
  { answer: "29", display: "029" },
  { answer: "31", display: "031" },
  { answer: "32", display: "032" },
  { answer: "33", display: "033" },
  { answer: "34", display: "034" },
  { answer: "35", display: "035" },
  { answer: "36", display: "036" },
  { answer: "37", display: "037" },
  { answer: "38", display: "038" },
  { answer: "40", display: "040" },
  { answer: "41", display: "041" },
  { answer: "42", display: "042" },
  { answer: "43", display: "043" },
  { answer: "44", display: "044" },
  { answer: "45", display: "045" },
  { answer: "46", display: "046" },
  { answer: "47", display: "047" },
  { answer: "48", display: "048" },
  { answer: "51", display: "051" },
  { answer: "52", display: "052" },
  { answer: "53", display: "053" },
  { answer: "54", display: "054" },
  { answer: "55", display: "055" },
  { answer: "56", display: "056" },
  { answer: "61", display: "061" },
  { answer: "62", display: "062" },
  { answer: "63", display: "063" },
  { answer: "64", display: "064" },
  { answer: "65", display: "065" },
  { answer: "71", display: "071" },
  { answer: "72", display: "072" },
  { answer: "73", display: "073" },
  { answer: "74", display: "074" },
  { answer: "75", display: "075" },
  { answer: "76", display: "076" },
  { answer: "77", display: "077" },
  { answer: "90", display: "090" },
  { answer: "91", display: "091" },
  { answer: "92", display: "092" },
  { answer: "95", display: "095" },
  { answer: "96", display: "096" },
  { answer: "97", display: "097" },
  { answer: "98", display: "098" },
];
