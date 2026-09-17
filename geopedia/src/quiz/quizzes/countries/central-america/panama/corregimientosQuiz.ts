/**
 * Quiz for identifying Panama's corregimientos.
 *
 * Corregimientos can be grouped by district or province/comarca. Duplicate
 * names are disambiguated by district and, when necessary, administrative ID.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PANAMA_CORREGIMIENTOS_BY_ID,
  PANAMA_DISTRICTS_BY_ID,
  PANAMA_PROVINCES_COMARCAS_BY_ID,
} from "./data/admin";

const PANAMA_CORREGIMIENTO_QUESTIONS = Object.entries(
  PANAMA_CORREGIMIENTOS_BY_ID,
).map(([id, corregimiento]) => ({
  answer: id,
  display: corregimiento.name,
}));

const PANAMA_DISTRICT_NAME_VALUE_LABELS = Object.fromEntries(
  Object.entries(PANAMA_DISTRICTS_BY_ID).map(([id, district]) => [
    id,
    district.name,
  ]),
);

export const panamaCorregimientosQuiz: FeatureQuiz = {
  id: "panama-corregimientos",
  name: "Corregimientos",
  description: `Learn all ${PANAMA_CORREGIMIENTO_QUESTIONS.length} corregimientos of Panama, with filters that let you practice corregimientos by district, province, or comarca.`,

  kind: "feature",
  mapId: "panama-corregimientos",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "districtId",
        label: "District",
        valueType: "string",
        valueLabels: PANAMA_DISTRICT_NAME_VALUE_LABELS,
      },
      {
        property: "provinceId",
        label: "Province / Comarca",
        valueType: "string",
        valueLabels: PANAMA_PROVINCES_COMARCAS_BY_ID,
      },
    ],
  },

  questions: PANAMA_CORREGIMIENTO_QUESTIONS,
};
