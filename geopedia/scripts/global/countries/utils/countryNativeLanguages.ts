/**
 * GeoPedia's preferred native-language overrides for country data generation.
 *
 * These overrides are used when REST Countries provides multiple native-name
 * languages and GeoPedia therefore needs an explicit, deterministic choice.
 *
 * The selected language is intended to be the language most useful for
 * recognizing contemporary geographic names, map labels, signs, addresses,
 * and other geographic clues in the country or territory. It is not
 * necessarily the first official language, the governing country's language,
 * or the most culturally distinctive language.
 *
 * Countries with exactly one available native-name language do not need an
 * entry here because that language can be selected automatically.
 *
 * A null value explicitly disables native-language generation for a country.
 * India intentionally uses English-only GeoPedia quiz data rather than
 * selecting one of its many native-language scripts.
 *
 * Language codes are ISO 639-3 codes matching REST Countries'
 * `names.native` keys.
 */

export const COUNTRY_NATIVE_LANGUAGE_OVERRIDES: Readonly<
  Record<string, string | null>
> = {
  AFG: "prs", // Afghanistan — Dari
  ASM: "eng", // American Samoa — English
  BDI: "run", // Burundi — Rundi
  BEL: "nld", // Belgium — Dutch
  BES: "nld", // Caribbean Netherlands — Dutch
  BIH: "bos", // Bosnia and Herzegovina — Bosnian
  BLZ: "eng", // Belize — English
  BOL: "spa", // Bolivia — Spanish
  CAF: "sag", // Central African Republic — Sango
  CHE: "gsw", // Switzerland — Swiss German
  CMR: "fra", // Cameroon — French
  COD: "fra", // Democratic Republic of the Congo — French
  COG: "fra", // Republic of the Congo — French
  COK: "eng", // Cook Islands — English
  COM: "zdj", // Comoros — Comorian
  CUW: "pap", // Curaçao — Papiamento
  CYP: "ell", // Cyprus — Greek
  DJI: "fra", // Djibouti — French
  ERI: "tir", // Eritrea — Tigrinya
  ESH: "mey", // Western Sahara — Hassaniya Arabic
  FIN: "fin", // Finland — Finnish
  FJI: "eng", // Fiji — English
  FRO: "fao", // Faroe Islands — Faroese
  GGY: "eng", // Guernsey — English
  GNQ: "spa", // Equatorial Guinea — Spanish
  GUM: "eng", // Guam — English
  HKG: "zho", // Hong Kong — Chinese
  HTI: "fra", // Haiti — French
  IMN: "eng", // Isle of Man — English
  IND: null, // India — intentionally English-only
  IRL: "eng", // Ireland — English
  IRQ: "ara", // Iraq — Arabic
  ISR: "heb", // Israel — Hebrew
  JEY: "eng", // Jersey — English
  KAZ: "kaz", // Kazakhstan — Kazakh
  KGZ: "kir", // Kyrgyzstan — Kyrgyz
  LBN: "ara", // Lebanon — Arabic
  LKA: "sin", // Sri Lanka — Sinhala
  LUX: "ltz", // Luxembourg — Luxembourgish
  MAC: "zho", // Macau — Chinese
  MAR: "ara", // Morocco — Arabic
  MDG: "mlg", // Madagascar — Malagasy
  MHL: "mah", // Marshall Islands — Marshallese
  MNP: "eng", // Northern Mariana Islands — English
  MUS: "eng", // Mauritius — English
  MYS: "eng", // Malaysia — English
  NAM: "eng", // Namibia — English
  NFK: "eng", // Norfolk Island — English
  NOR: "nob", // Norway — Norwegian Bokmål
  NZL: "eng", // New Zealand — English
  PAK: "urd", // Pakistan — Urdu
  PER: "spa", // Peru — Spanish
  PHL: "fil", // Philippines — Filipino
  PLW: "eng", // Palau — English
  PNG: "eng", // Papua New Guinea — English
  PRY: "spa", // Paraguay — Spanish
  SDN: "ara", // Sudan — Arabic
  SGP: "eng", // Singapore — English
  SOM: "som", // Somalia — Somali
  SXM: "nld", // Sint Maarten — Dutch
  SYC: "eng", // Seychelles — English
  TCD: "ara", // Chad — Arabic
  TJK: "tgk", // Tajikistan — Tajik
  TKM: "tuk", // Turkmenistan — Turkmen
  UZB: "uzb", // Uzbekistan — Uzbek
  VAT: "ita", // Vatican City — Italian
  XKX: "sqi", // Kosovo — Albanian
  ZAF: "eng", // South Africa — English
};
