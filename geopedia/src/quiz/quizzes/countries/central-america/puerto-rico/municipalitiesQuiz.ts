import type { FeatureQuiz } from "@/types/quiz";

/**
 * Puerto Rico municipality names keyed by Census county-equivalent GEOID.
 */
export const PUERTO_RICO_MUNICIPALITY_NAMES_BY_ID = {
  "72001": "Adjuntas",
  "72003": "Aguada",
  "72005": "Aguadilla",
  "72007": "Aguas Buenas",
  "72009": "Aibonito",
  "72011": "Añasco",
  "72013": "Arecibo",
  "72015": "Arroyo",
  "72017": "Barceloneta",
  "72019": "Barranquitas",
  "72021": "Bayamón",
  "72023": "Cabo Rojo",
  "72025": "Caguas",
  "72027": "Camuy",
  "72029": "Canóvanas",
  "72031": "Carolina",
  "72033": "Cataño",
  "72035": "Cayey",
  "72037": "Ceiba",
  "72039": "Ciales",
  "72041": "Cidra",
  "72043": "Coamo",
  "72045": "Comerío",
  "72047": "Corozal",
  "72049": "Culebra",
  "72051": "Dorado",
  "72053": "Fajardo",
  "72054": "Florida",
  "72055": "Guánica",
  "72057": "Guayama",
  "72059": "Guayanilla",
  "72061": "Guaynabo",
  "72063": "Gurabo",
  "72065": "Hatillo",
  "72067": "Hormigueros",
  "72069": "Humacao",
  "72071": "Isabela",
  "72073": "Jayuya",
  "72075": "Juana Díaz",
  "72077": "Juncos",
  "72079": "Lajas",
  "72081": "Lares",
  "72083": "Las Marías",
  "72085": "Las Piedras",
  "72087": "Loíza",
  "72089": "Luquillo",
  "72091": "Manatí",
  "72093": "Maricao",
  "72095": "Maunabo",
  "72097": "Mayagüez",
  "72099": "Moca",
  "72101": "Morovis",
  "72103": "Naguabo",
  "72105": "Naranjito",
  "72107": "Orocovis",
  "72109": "Patillas",
  "72111": "Peñuelas",
  "72113": "Ponce",
  "72115": "Quebradillas",
  "72117": "Rincón",
  "72119": "Río Grande",
  "72121": "Sabana Grande",
  "72123": "Salinas",
  "72125": "San Germán",
  "72127": "San Juan",
  "72129": "San Lorenzo",
  "72131": "San Sebastián",
  "72133": "Santa Isabel",
  "72135": "Toa Alta",
  "72137": "Toa Baja",
  "72139": "Trujillo Alto",
  "72141": "Utuado",
  "72143": "Vega Alta",
  "72145": "Vega Baja",
  "72147": "Vieques",
  "72149": "Villalba",
  "72151": "Yabucoa",
  "72153": "Yauco",
} as const;

/**
 * Questions for Puerto Rico's municipalities quiz.
 */
const PUERTO_RICO_MUNICIPALITY_QUESTIONS = Object.entries(
  PUERTO_RICO_MUNICIPALITY_NAMES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

/**
 * Quiz configuration for Puerto Rico's municipalities.
 */
export const puertoRicoMunicipalitiesQuiz: FeatureQuiz = {
  id: "puerto-rico-municipalities",
  name: "Municipalities",
  description: `Learn all ${PUERTO_RICO_MUNICIPALITY_QUESTIONS.length} municipalities of Puerto Rico.`,

  kind: "feature",

  mapId: "puerto-rico-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PUERTO_RICO_MUNICIPALITY_QUESTIONS,
};
