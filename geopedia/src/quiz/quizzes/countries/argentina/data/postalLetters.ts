/**
 * Argentina CPA postal-letter quiz data.
 *
 * Argentina's modern Código Postal Argentino (CPA) uses an 8-character
 * alphanumeric postal code with the format:
 *
 *   A9999AAA
 *
 * The first letter identifies one of Argentina's 23 provinces or the
 * Autonomous City of Buenos Aires. Each first-level administrative unit
 * has a unique letter. The letters I and O are not used.
 *
 * This mapping connects GeoPedia's Argentina province IDs to their
 * corresponding CPA postal letters. The province IDs are the same stable
 * source PCODE values used by the Argentina province GeoJSON.
 *
 * This file is maintained manually because the province-letter mapping is
 * fixed reference data rather than data generated from the numeric postal
 * code dataset.
 *
 * Numeric postal-code quiz data is kept separately in postalCodes.ts.
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
