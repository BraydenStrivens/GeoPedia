/**
 * Quiz configuration for the province-identifying first letters used by
 * Argentina's modern Código Postal Argentino (CPA).
 *
 * Questions use stable province IDs as map answers and display the
 * corresponding CPA postal letter to the player.
 */

export const ARGENTINA_POSTAL_LETTER_BY_PROVINCE_ID = {
  AR002: "C", // Ciudad de Buenos Aires (CABA)
  AR006: "B", // Buenos Aires Province
  AR010: "K", // Catamarca
  AR014: "X", // Córdoba
  AR018: "W", // Corrientes
  AR022: "H", // Chaco
  AR026: "U", // Chubut
  AR030: "E", // Entre Ríos
  AR034: "P", // Formosa
  AR038: "Y", // Jujuy
  AR042: "L", // La Pampa
  AR046: "F", // La Rioja
  AR050: "M", // Mendoza
  AR054: "N", // Misiones
  AR058: "Q", // Neuquén
  AR062: "R", // Río Negro
  AR066: "A", // Salta
  AR070: "J", // San Juan
  AR074: "D", // San Luis
  AR078: "Z", // Santa Cruz
  AR082: "S", // Santa Fe
  AR086: "G", // Santiago del Estero
  AR090: "T", // Tucumán
  AR094: "V", // Tierra del Fuego
} as const;

/**
 * Union of all CPA province-letter values used by Argentina.
 *
 * Example:
 *   "B" | "C" | "K" | ...
 */
export type ArgentinaPostalLetter =
  (typeof ARGENTINA_POSTAL_LETTER_BY_PROVINCE_ID)[keyof typeof ARGENTINA_POSTAL_LETTER_BY_PROVINCE_ID];
