import type { FeatureQuiz } from "@/types/quiz";

/**
 * Ecuadorian license-plate first-letter codes by province.
 *
 * The first letter of a standard Ecuadorian vehicle registration identifies
 * the province in which the vehicle was registered. These province letters
 * are especially useful in GeoGuessr on taxis and other commercial vehicles.
 */
const ECUADOR_TAXI_CODE_QUESTIONS = [
  { answer: "EC01", display: "A" }, // Azuay
  { answer: "EC02", display: "B" }, // Bolívar
  { answer: "EC03", display: "U" }, // Cañar
  { answer: "EC04", display: "C" }, // Carchi
  { answer: "EC05", display: "X" }, // Cotopaxi
  { answer: "EC06", display: "H" }, // Chimborazo
  { answer: "EC07", display: "O" }, // El Oro
  { answer: "EC08", display: "E" }, // Esmeraldas
  { answer: "EC09", display: "G" }, // Guayas
  { answer: "EC10", display: "I" }, // Imbabura
  { answer: "EC11", display: "L" }, // Loja
  { answer: "EC12", display: "R" }, // Los Ríos
  { answer: "EC13", display: "M" }, // Manabí
  { answer: "EC14", display: "V" }, // Morona Santiago
  { answer: "EC15", display: "N" }, // Napo
  { answer: "EC16", display: "S" }, // Pastaza
  { answer: "EC17", display: "P" }, // Pichincha
  { answer: "EC18", display: "T" }, // Tungurahua
  { answer: "EC19", display: "Z" }, // Zamora Chinchipe
  { answer: "EC20", display: "W" }, // Galápagos
  { answer: "EC21", display: "K" }, // Sucumbíos
  { answer: "EC22", display: "Q" }, // Orellana
  { answer: "EC23", display: "J" }, // Santo Domingo de los Tsáchilas
  { answer: "EC24", display: "Y" }, // Santa Elena
] as const;

/**
 * Description shown for Ecuador's Taxi Codes quiz.
 */
const ECUADOR_TAXI_CODES_DESCRIPTION =
  `Learn all ${ECUADOR_TAXI_CODE_QUESTIONS.length} Ecuadorian province ` +
  `license-plate first-letter codes commonly useful for identifying taxis and ` +
  `other vehicles. Standard Ecuadorian plates normally contain 3 letters ` +
  `followed by 3 or 4 digits, such as PBX-1234, where P identifies Pichincha, ` +
  `or GRT-456, where G identifies Guayas. Commercial and public vehicles such ` +
  `as taxis and buses use colored plates and can appear in formats such as ` +
  `AHA-123, while government vehicles may use different formats such as E-1234.`;

/**
 * Quiz for identifying Ecuadorian provinces from the first letter of a vehicle
 * license plate.
 */
export const ecuadorTaxiCodesQuiz: FeatureQuiz = {
  id: "ecuador-taxi-codes",
  name: "Taxi Codes",
  description: ECUADOR_TAXI_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: [...ECUADOR_TAXI_CODE_QUESTIONS],
};
