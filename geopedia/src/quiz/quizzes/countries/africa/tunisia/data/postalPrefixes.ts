/**
 * Tunisia 2-digit postal-code prefix quiz data.
 *
 * Each question represents the first two digits of a four-digit Tunisian
 * postal code. The runtime postal-prefix GeoJSON determines which geographic
 * features accept each prefix.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

/**
 * All distinct 2-digit postal-code prefixes represented by the Tunisia
 * postal-prefix map.
 */
export const TUNISIA_POSTAL_PREFIX_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "10", display: "10--" },
    { answer: "11", display: "11--" },
    { answer: "12", display: "12--" },
    { answer: "20", display: "20--" },
    { answer: "21", display: "21--" },
    { answer: "22", display: "22--" },
    { answer: "30", display: "30--" },
    { answer: "31", display: "31--" },
    { answer: "32", display: "32--" },
    { answer: "40", display: "40--" },
    { answer: "41", display: "41--" },
    { answer: "42", display: "42--" },
    { answer: "50", display: "50--" },
    { answer: "51", display: "51--" },
    { answer: "60", display: "60--" },
    { answer: "61", display: "61--" },
    { answer: "70", display: "70--" },
    { answer: "71", display: "71--" },
    { answer: "80", display: "80--" },
    { answer: "81", display: "81--" },
    { answer: "90", display: "90--" },
    { answer: "91", display: "91--" },
  ];
