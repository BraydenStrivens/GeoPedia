/**
 * Generated quiz-question data for the Philippines' telephone area codes.
 *
 * Complete area-code answers use domestic dialing format, including the
 * leading 0.
 *
 * Prefix questions append "-" to the display when the answer represents the
 * beginning of a family of area codes. 02 is already a complete area code and
 * therefore does not use a separate display value.
 *
 * Regenerate with:
 *
 *   python scripts/countries/philippines/generate/area-code-quiz-data.py
 */

import { FeatureQuizQuestion } from "@/types/quiz";

export const PHILIPPINES_AREA_CODE_PREFIX_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "02" },
    { answer: "03", display: "03-" },
    { answer: "04", display: "04-" },
    { answer: "05", display: "05-" },
    { answer: "06", display: "06-" },
    { answer: "07", display: "07-" },
    { answer: "08", display: "08-" },
  ];

export const PHILIPPINES_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "02" },
    { answer: "032" },
    { answer: "033" },
    { answer: "034" },
    { answer: "035" },
    { answer: "036" },
    { answer: "038" },
    { answer: "042" },
    { answer: "043" },
    { answer: "044" },
    { answer: "045" },
    { answer: "046" },
    { answer: "047" },
    { answer: "048" },
    { answer: "049" },
    { answer: "052" },
    { answer: "053" },
    { answer: "054" },
    { answer: "055" },
    { answer: "056" },
    { answer: "062" },
    { answer: "063" },
    { answer: "064" },
    { answer: "065" },
    { answer: "068" },
    { answer: "072" },
    { answer: "074" },
    { answer: "075" },
    { answer: "077" },
    { answer: "078" },
    { answer: "082" },
    { answer: "083" },
    { answer: "084" },
    { answer: "085" },
    { answer: "086" },
    { answer: "087" },
    { answer: "088" },
  ];
