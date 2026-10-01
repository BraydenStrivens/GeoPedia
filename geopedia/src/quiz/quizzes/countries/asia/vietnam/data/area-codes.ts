/**
 * Question data for Vietnam's telephone area-code quizzes.
 *
 * Full area codes are mapped to GeoPedia's stable province IDs using the
 * province boundaries shown in the Plonk It Vietnam area-code map.
 *
 * The two-digit prefix questions target dissolved prefix regions generated
 * from the same province-to-area-code mapping.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

export const VIETNAM_AREA_CODE_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "1", display: "0236" },
  { answer: "2", display: "0251" },
  { answer: "3", display: "0277" },
  { answer: "4", display: "0261" },
  { answer: "5", display: "0262" },
  { answer: "6", display: "0215" },
  { answer: "7", display: "0296" },
  { answer: "8", display: "0254" },
  { answer: "9", display: "0256" },
  { answer: "10", display: "0274" },
  { answer: "11", display: "0271" },
  { answer: "12", display: "0252" },
  { answer: "13", display: "0291" },
  { answer: "14", display: "0204" },
  { answer: "15", display: "0209" },
  { answer: "16", display: "0222" },
  { answer: "17", display: "0275" },
  { answer: "18", display: "0290" },
  { answer: "19", display: "0206" },
  { answer: "20", display: "0292" },
  { answer: "21", display: "0269" },
  { answer: "22", display: "0219" },
  { answer: "23", display: "024" },
  { answer: "24", display: "0226" },
  { answer: "25", display: "0239" },
  { answer: "26", display: "028" },
  { answer: "27", display: "0218" },
  { answer: "28", display: "0221" },
  { answer: "29", display: "0220" },
  { answer: "30", display: "0225" },
  { answer: "31", display: "0293" },
  { answer: "32", display: "0258" },
  { answer: "33", display: "0297" },
  { answer: "34", display: "0260" },
  { answer: "35", display: "0214" },
  { answer: "36", display: "0263" },
  { answer: "37", display: "0213" },
  { answer: "38", display: "0205" },
  { answer: "39", display: "0272" },
  { answer: "40", display: "0228" },
  { answer: "41", display: "0238" },
  { answer: "42", display: "0229" },
  { answer: "43", display: "0259" },
  { answer: "44", display: "0210" },
  { answer: "45", display: "0257" },
  { answer: "46", display: "0232" },
  { answer: "47", display: "0235" },
  { answer: "48", display: "0255" },
  { answer: "49", display: "0203" },
  { answer: "50", display: "0233" },
  { answer: "51", display: "0299" },
  { answer: "52", display: "0212" },
  { answer: "53", display: "0276" },
  { answer: "54", display: "0227" },
  { answer: "55", display: "0208" },
  { answer: "56", display: "0234" },
  { answer: "57", display: "0237" },
  { answer: "58", display: "0273" },
  { answer: "59", display: "0294" },
  { answer: "60", display: "0207" },
  { answer: "61", display: "0270" },
  { answer: "62", display: "0211" },
  { answer: "63", display: "0216" },
];

export const VIETNAM_AREA_CODE_PREFIX_2_QUESTIONS: FeatureQuizQuestion[] =
  [
    { answer: "20", display: "020-" },
    { answer: "21", display: "021-" },
    { answer: "22", display: "022-" },
    { answer: "23", display: "023-" },
    { answer: "24", display: "024-" },
    { answer: "25", display: "025-" },
    { answer: "26", display: "026-" },
    { answer: "27", display: "027-" },
    { answer: "28", display: "028-" },
    { answer: "29", display: "029-" },
  ];
