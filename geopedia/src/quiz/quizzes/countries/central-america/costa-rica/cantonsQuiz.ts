import type { FeatureQuiz } from "@/types/quiz";

import { COSTA_RICA_PROVINCE_NAMES_BY_ID } from "./provincesQuiz";

/**
 * Costa Rica canton names keyed by their 3-digit administrative ID.
 */
export const COSTA_RICA_CANTON_NAMES_BY_ID = {
  "101": "San José",
  "102": "Escazú",
  "103": "Desamparados",
  "104": "Puriscal",
  "105": "Tarrazú",
  "106": "Aserrí",
  "107": "Mora",
  "108": "Goicoechea",
  "109": "Santa Ana",
  "110": "Alajuelita",
  "111": "Vázquez de Coronado",
  "112": "Acosta",
  "113": "Tibás",
  "114": "Moravia",
  "115": "Montes de Oca",
  "116": "Turrubares",
  "117": "Dota",
  "118": "Curridabat",
  "119": "Pérez Zeledón",
  "120": "León Cortés Castro",
  "201": "Alajuela",
  "202": "San Ramón",
  "203": "Grecia",
  "204": "San Mateo",
  "205": "Atenas",
  "206": "Naranjo",
  "207": "Palmares",
  "208": "Poás",
  "209": "Orotina",
  "210": "San Carlos",
  "211": "Zarcero",
  "212": "Sarchí",
  "213": "Upala",
  "214": "Los Chiles",
  "215": "Guatuso",
  "216": "Río Cuarto",
  "301": "Cartago",
  "302": "Paraíso",
  "303": "La Unión",
  "304": "Jiménez",
  "305": "Turrialba",
  "306": "Alvarado",
  "307": "Oreamuno",
  "308": "El Guarco",
  "401": "Heredia",
  "402": "Barva",
  "403": "Santo Domingo",
  "404": "Santa Bárbara",
  "405": "San Rafael",
  "406": "San Isidro",
  "407": "Belén",
  "408": "Flores",
  "409": "San Pablo",
  "410": "Sarapiquí",
  "501": "Liberia",
  "502": "Nicoya",
  "503": "Santa Cruz",
  "504": "Bagaces",
  "505": "Carrillo",
  "506": "Cañas",
  "507": "Abangares",
  "508": "Tilarán",
  "509": "Nandayure",
  "510": "La Cruz",
  "511": "Hojancha",
  "601": "Puntarenas",
  "602": "Esparza",
  "603": "Buenos Aires",
  "604": "Montes de Oro",
  "605": "Osa",
  "606": "Quepos",
  "607": "Golfito",
  "608": "Coto Brus",
  "609": "Parrita",
  "610": "Corredores",
  "611": "Garabito",
  "612": "Monteverde",
  "613": "Puerto Jiménez",
  "701": "Limón",
  "702": "Pococí",
  "703": "Siquirres",
  "704": "Talamanca",
  "705": "Matina",
  "706": "Guácimo",
} as const;

/**
 * Questions for Costa Rica's cantons.
 */
const COSTA_RICA_CANTON_QUESTIONS = Object.entries(
  COSTA_RICA_CANTON_NAMES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

/**
 * User-facing description for Costa Rica's cantons quiz.
 */
const COSTA_RICA_CANTONS_DESCRIPTION =
  `Learn all ${COSTA_RICA_CANTON_QUESTIONS.length} cantons of Costa Rica. ` +
  `Filters let you practice cantons by province.`;

/**
 * Canton quiz for Costa Rica.
 */
export const costaRicaCantonsQuiz: FeatureQuiz = {
  id: "costa-rica-cantons",
  name: "Cantons",
  description: COSTA_RICA_CANTONS_DESCRIPTION,

  kind: "feature",
  mapId: "costa-rica-cantons",

  answerProperty: "canton_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCE_NAMES_BY_ID,
      },
    ],
  },

  questions: COSTA_RICA_CANTON_QUESTIONS,
};
