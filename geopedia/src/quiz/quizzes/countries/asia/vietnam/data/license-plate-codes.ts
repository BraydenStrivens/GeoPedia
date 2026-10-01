/**
 * Question data for Vietnam's license plate code quiz.
 *
 * License plate codes follow the province-level geographic assignments shown
 * by Plonk It. Answers use GeoPedia's stable pre-reform province IDs so the
 * quiz can reuse the existing province map.
 *
 * Provinces and cities with multiple assigned codes are represented by a
 * single question listing all of their codes.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

export const VIETNAM_LICENSE_PLATE_CODE_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "1", display: "43" },
    { answer: "2", display: "39, 60" },
    { answer: "3", display: "66" },
    { answer: "4", display: "48" },
    { answer: "5", display: "47" },
    { answer: "6", display: "27" },
    { answer: "7", display: "67" },
    { answer: "8", display: "72" },
    { answer: "9", display: "77" },
    { answer: "10", display: "61" },
    { answer: "11", display: "93" },
    { answer: "12", display: "86" },
    { answer: "13", display: "94" },
    { answer: "14", display: "98" },
    { answer: "15", display: "97" },
    { answer: "16", display: "99" },
    { answer: "17", display: "71" },
    { answer: "18", display: "69" },
    { answer: "19", display: "11" },
    { answer: "20", display: "65" },
    { answer: "21", display: "81" },
    { answer: "22", display: "23" },
    { answer: "23", display: "29-33, 40" },
    { answer: "24", display: "90" },
    { answer: "25", display: "38" },
    { answer: "26", display: "50-59, 41" },
    { answer: "27", display: "28" },
    { answer: "28", display: "89" },
    { answer: "29", display: "34" },
    { answer: "30", display: "15, 16" },
    { answer: "31", display: "95" },
    { answer: "32", display: "79" },
    { answer: "33", display: "68" },
    { answer: "34", display: "82" },
    { answer: "35", display: "24" },
    { answer: "36", display: "49" },
    { answer: "37", display: "25" },
    { answer: "38", display: "12" },
    { answer: "39", display: "62" },
    { answer: "40", display: "18" },
    { answer: "41", display: "37" },
    { answer: "42", display: "35" },
    { answer: "43", display: "85" },
    { answer: "44", display: "19" },
    { answer: "45", display: "78" },
    { answer: "46", display: "73" },
    { answer: "47", display: "92" },
    { answer: "48", display: "76" },
    { answer: "49", display: "14" },
    { answer: "50", display: "74" },
    { answer: "51", display: "83" },
    { answer: "52", display: "26" },
    { answer: "53", display: "70" },
    { answer: "54", display: "17" },
    { answer: "55", display: "20" },
    { answer: "56", display: "75" },
    { answer: "57", display: "36" },
    { answer: "58", display: "63" },
    { answer: "59", display: "84" },
    { answer: "60", display: "22" },
    { answer: "61", display: "64" },
    { answer: "62", display: "88" },
    { answer: "63", display: "21" },
  ];
