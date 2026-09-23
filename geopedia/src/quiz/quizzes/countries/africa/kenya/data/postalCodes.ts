/**
 * Question data for Kenya's postal-code prefix quizzes.
 *
 * Kenyan postal codes contain five digits. Question displays show the known
 * prefix followed by hyphens for the remaining digits so that the relationship
 * between each quiz answer and the full postal-code format remains visible.
 *
 * Some 3-digit prefixes share the same map geometry, but each remains an
 * individual quiz question and accepted answer.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

export const KENYA_POSTAL_2_DIGIT_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "00", display: "00---" },
  { answer: "10", display: "10---" },
  { answer: "20", display: "20---" },
  { answer: "30", display: "30---" },
  { answer: "40", display: "40---" },
  { answer: "50", display: "50---" },
  { answer: "60", display: "60---" },
  { answer: "70", display: "70---" },
  { answer: "80", display: "80---" },
  { answer: "90", display: "90---" },
];

export const KENYA_POSTAL_3_DIGIT_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "0", display: "0----" },
  { answer: "101", display: "101--" },
  { answer: "102", display: "102--" },
  { answer: "103", display: "103--" },
  { answer: "104", display: "104--" },
  { answer: "201", display: "201--" },
  { answer: "202", display: "202--" },
  { answer: "203", display: "203--" },
  { answer: "204", display: "204--" },
  { answer: "205", display: "205--" },
  { answer: "206", display: "206--" },
  { answer: "301", display: "301--" },
  { answer: "302", display: "302--" },
  { answer: "303", display: "303--" },
  { answer: "304", display: "304--" },
  { answer: "305", display: "305--" },
  { answer: "306", display: "306--" },
  { answer: "401", display: "401--" },
  { answer: "402", display: "402--" },
  { answer: "403", display: "403--" },
  { answer: "404", display: "404--" },
  { answer: "405", display: "405--" },
  { answer: "406", display: "406--" },
  { answer: "501", display: "501--" },
  { answer: "502", display: "502--" },
  { answer: "503", display: "503--" },
  { answer: "504", display: "504--" },
  { answer: "601", display: "601--" },
  { answer: "602", display: "602--" },
  { answer: "603", display: "603--" },
  { answer: "604", display: "604--" },
  { answer: "605", display: "605--" },
  { answer: "607", display: "607--" },
  { answer: "701", display: "701--" },
  { answer: "702", display: "702--" },
  { answer: "703", display: "703--" },
  { answer: "801", display: "801--" },
  { answer: "802", display: "802--" },
  { answer: "803", display: "803--" },
  { answer: "804", display: "804--" },
  { answer: "805", display: "805--" },
  { answer: "901", display: "901--" },
  { answer: "902", display: "902--" },
  { answer: "903", display: "903--" },
  { answer: "904", display: "904--" },
];
