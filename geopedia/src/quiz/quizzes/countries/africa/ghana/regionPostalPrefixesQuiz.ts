/**
 * Feature quiz for Ghana's one-character regional postal prefixes.
 *
 * Each question displays the first character used by postcode districts
 * within a region while using the existing region ID as the map answer.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { GHANA_POSTAL_PREFIXES_BY_REGION_ID } from "./data/postcodes";

const QUESTIONS: FeatureQuiz["questions"] = Object.entries(
  GHANA_POSTAL_PREFIXES_BY_REGION_ID,
).map(([regionId, region]) => ({
  answer: regionId,
  display: region.prefix,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} one-character regional postal prefixes of ` +
  `Ghana. GhanaPostGPS postal codes begin with a postcode district code, ` +
  `whose first character identifies the region, followed by a 3- to 5-digit ` +
  `area number. For example, GA184 uses G for Greater Accra, while AK039 ` +
  `uses A for Ashanti. A full Digital Address adds a 4-digit property number, ` +
  `such as AK-039-5028.`;

export const ghanaRegionPostalPrefixesQuiz: FeatureQuiz = {
  id: "ghana-regional-postal-prefixes",
  name: "Regional Postal Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "ghana-regions",

  answerProperty: "region_id",
  answerType: "single",

  questions: QUESTIONS,
};
