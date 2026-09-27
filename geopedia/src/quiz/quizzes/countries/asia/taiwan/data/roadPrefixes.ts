/**
 * Question data for Taiwan's county-road prefix character quiz.
 *
 * Taiwan's county roads use a Chinese character before the route number
 * to identify the county or municipality. Each question maps one unique
 * prefix character to the corresponding county_id in GeoPedia's Taiwan
 * county GeoJSON.
 *
 * Keelung City, Hsinchu City, and Chiayi City use 市 rather than unique
 * county-specific characters, while Taipei City has no prefix on the
 * provided reference map. Kinmen and Lienchiang are not represented by
 * unique prefix characters on the reference map.
 */

import type { FeatureQuizQuestion } from "@/types/quiz";

export const TAIWAN_ROAD_PREFIX_QUESTIONS: FeatureQuizQuestion[] = [
  { answer: "TWN.7.13_1", display: "桃" },
  { answer: "TWN.3.1_1", display: "北" },
  { answer: "TWN.7.5_1", display: "竹" },
  { answer: "TWN.7.8_1", display: "苗" },
  { answer: "TWN.4.1_1", display: "中" },
  { answer: "TWN.7.1_1", display: "彰" },
  { answer: "TWN.7.15_1", display: "雲" },
  { answer: "TWN.7.3_1", display: "嘉" },
  { answer: "TWN.5.1_1", display: "南" },
  { answer: "TWN.2.1_1", display: "高" },
  { answer: "TWN.7.11_1", display: "屏" },
  { answer: "TWN.7.14_1", display: "宜" },
  { answer: "TWN.7.9_1", display: "投" },
  { answer: "TWN.7.6_1", display: "花" },
  { answer: "TWN.7.12_1", display: "東" },
  { answer: "TWN.7.10_1", display: "澎" },
  { answer: "city", display: "市" },
];
