/**
 * Defines the United States states quiz.
 *
 * This quiz uses the shared US states map and asks the user to identify states
 * by name. Each quiz answer corresponds to the `name` property in the US
 * states GeoJSON dataset.
 *
 * The quiz also supports property-based grouping by US region.
 */

import type { FeatureQuiz } from "@/types/quiz";

const US_STATE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "Alabama" },
  { answer: "Alaska" },
  { answer: "Arizona" },
  { answer: "Arkansas" },
  { answer: "California" },
  { answer: "Colorado" },
  { answer: "Connecticut" },
  { answer: "Delaware" },
  { answer: "Florida" },
  { answer: "Georgia" },
  { answer: "Hawaii" },
  { answer: "Idaho" },
  { answer: "Illinois" },
  { answer: "Indiana" },
  { answer: "Iowa" },
  { answer: "Kansas" },
  { answer: "Kentucky" },
  { answer: "Louisiana" },
  { answer: "Maine" },
  { answer: "Maryland" },
  { answer: "Massachusetts" },
  { answer: "Michigan" },
  { answer: "Minnesota" },
  { answer: "Mississippi" },
  { answer: "Missouri" },
  { answer: "Montana" },
  { answer: "Nebraska" },
  { answer: "Nevada" },
  { answer: "New Hampshire" },
  { answer: "New Jersey" },
  { answer: "New Mexico" },
  { answer: "New York" },
  { answer: "North Carolina" },
  { answer: "North Dakota" },
  { answer: "Ohio" },
  { answer: "Oklahoma" },
  { answer: "Oregon" },
  { answer: "Pennsylvania" },
  { answer: "Rhode Island" },
  { answer: "South Carolina" },
  { answer: "South Dakota" },
  { answer: "Tennessee" },
  { answer: "Texas" },
  { answer: "Utah" },
  { answer: "Vermont" },
  { answer: "Virginia" },
  { answer: "Washington" },
  { answer: "West Virginia" },
  { answer: "Wisconsin" },
  { answer: "Wyoming" },
];

const US_STATES_DESCRIPTION = `Learn all ${US_STATE_QUESTIONS.length} US states by their location on the map. This quiz includes the 50 states only and does not include US territories.`;

/**
 * Quiz definition for identifying US states by name.
 */
export const usStatesQuiz: FeatureQuiz = {
  id: "us-states",
  name: "US States",
  description: US_STATES_DESCRIPTION,

  kind: "feature",
  mapId: "us-states",

  answerProperty: "name",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: US_STATE_QUESTIONS,
};
