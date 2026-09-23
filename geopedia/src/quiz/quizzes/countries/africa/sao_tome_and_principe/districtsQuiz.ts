/**
 * Feature quiz for São Tomé and Príncipe's seven districts.
 */

import type { FeatureQuiz } from "@/types/quiz";

const QUESTIONS: FeatureQuiz["questions"] = [
  {
    answer: "43174148B82261817076051",
    display: "Pagué",
  },
  {
    answer: "43174148B36740863505441",
    display: "Água Grande",
  },
  {
    answer: "43174148B25004726463593",
    display: "Lobata",
  },
  {
    answer: "43174148B76706884828518",
    display: "Mé-zóxi",
  },
  {
    answer: "43174148B99779095511190",
    display: "Cantagalo",
  },
  {
    answer: "43174148B20195011652309",
    display: "Lemba",
  },
  {
    answer: "43174148B37019359222323",
    display: "Caué",
  },
];

const DESCRIPTION = `Learn all ${QUESTIONS.length} districts of São Tomé and Príncipe.`;

export const saoTomeAndPrincipeDistrictsQuiz: FeatureQuiz = {
  id: "sao-tome-and-principe-districts",
  name: "Districts",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "sao-tome-and-principe-districts",

  answerProperty: "district_id",
  answerType: "single",

  questions: QUESTIONS,
};
