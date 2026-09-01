/**
 * Global quiz for identifying countries and territories by their flags.
 *
 * This file is generated from GeoPedia's world-country GeoJSON and country
 * flag assets by:
 *
 *   scripts/generate/generate-global-country-flags-quiz.ts
 */

import type { Quiz } from "@/types/quiz";

/**
 * Global map quiz that displays a country flag and asks the player to select
 * its corresponding geographic feature on the world map.
 *
 * Quiz answers intentionally preserve the raw `iso_a3` values stored by
 * world-countries.geojson because that same property is used by the map's
 * feature interactions.
 */
export const countryFlagsQuiz: Quiz = {
  id: "country-flags",
  name: "Country Flags",

  mapId: "world-countries",
  kind: "feature",

  answerProperty: "iso_a3",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "continent",
        label: "Continent",
        valueType: "string",
      },
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "subregion",
        label: "Subregion",
        valueType: "string",
      },
    ],
  },

  questions: [
    {
      answer: "AFG",
      display: "Afghanistan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/afg.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ALA",
      display: "Åland Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ala.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ALB",
      display: "Albania",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/alb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "DZA",
      display: "Algeria",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/dza.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ASM",
      display: "American Samoa",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/asm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "AND",
      display: "Andorra",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/and.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "AGO",
      display: "Angola",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ago.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "AIA",
      display: "Anguilla",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/aia.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ATA",
      display: "Antarctica",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ata.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ATG",
      display: "Antigua and Barbuda",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/atg.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ARG",
      display: "Argentina",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/arg.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ARM",
      display: "Armenia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/arm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ABW",
      display: "Aruba",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/abw.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "AUS",
      display: "Australia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/aus.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "AUT",
      display: "Austria",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/aut.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "AZE",
      display: "Azerbaijan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/aze.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BHS",
      display: "Bahamas",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bhs.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BHR",
      display: "Bahrain",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bhr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BGD",
      display: "Bangladesh",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bgd.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BRB",
      display: "Barbados",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/brb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BLR",
      display: "Belarus",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/blr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BEL",
      display: "Belgium",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bel.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BLZ",
      display: "Belize",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/blz.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BEN",
      display: "Benin",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ben.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BMU",
      display: "Bermuda",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bmu.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BTN",
      display: "Bhutan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/btn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BOL",
      display: "Bolivia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bol.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BIH",
      display: "Bosnia and Herzegovina",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bih.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BWA",
      display: "Botswana",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bwa.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BVT",
      display: "Bouvet Island",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bvt.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BRA",
      display: "Brazil",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bra.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "IOT",
      display: "British Indian Ocean Territory",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/iot.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "VGB",
      display: "British Virgin Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/vgb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BRN",
      display: "Brunei",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/brn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BGR",
      display: "Bulgaria",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bgr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BFA",
      display: "Burkina Faso",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bfa.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BDI",
      display: "Burundi",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bdi.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CPV",
      display: "Cabo Verde",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cpv.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KHM",
      display: "Cambodia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/khm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CMR",
      display: "Cameroon",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cmr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CAN",
      display: "Canada",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/can.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BES",
      display: "Caribbean Netherlands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/bes.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CYM",
      display: "Cayman Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cym.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CAF",
      display: "Central African Republic",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/caf.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TCD",
      display: "Chad",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tcd.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CHL",
      display: "Chile",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/chl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CHN",
      display: "China",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/chn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CXR",
      display: "Christmas Island",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cxr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CCK",
      display: "Cocos (Keeling) Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cck.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "COL",
      display: "Colombia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/col.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "COM",
      display: "Comoros",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/com.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "COG",
      display: "Congo",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cog.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "COK",
      display: "Cook Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cok.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CRI",
      display: "Costa Rica",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cri.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "HRV",
      display: "Croatia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/hrv.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CUB",
      display: "Cuba",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cub.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CUW",
      display: "Curaçao",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cuw.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CYP",
      display: "Cyprus",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cyp.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CZE",
      display: "Czechia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cze.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "DNK",
      display: "Denmark",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/dnk.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "DJI",
      display: "Djibouti",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/dji.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "DMA",
      display: "Dominica",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/dma.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "DOM",
      display: "Dominican Republic",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/dom.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "COD",
      display: "DRC",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/cod.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ECU",
      display: "Ecuador",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ecu.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "EGY",
      display: "Egypt",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/egy.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SLV",
      display: "El Salvador",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/slv.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GNQ",
      display: "Equatorial Guinea",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gnq.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ERI",
      display: "Eritrea",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/eri.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "EST",
      display: "Estonia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/est.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SWZ",
      display: "Eswatini",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/swz.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ETH",
      display: "Ethiopia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/eth.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "FLK",
      display: "Falkland Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/flk.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "FRO",
      display: "Faroe Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/fro.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "FJI",
      display: "Fiji",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/fji.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "FIN",
      display: "Finland",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/fin.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "FRA",
      display: "France",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/fra.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GUF",
      display: "French Guiana",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/guf.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PYF",
      display: "French Polynesia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pyf.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ATF",
      display: "French Southern and Antarctic Lands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/atf.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GAB",
      display: "Gabon",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gab.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GMB",
      display: "Gambia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gmb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GEO",
      display: "Georgia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/geo.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "DEU",
      display: "Germany",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/deu.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GHA",
      display: "Ghana",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gha.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GIB",
      display: "Gibraltar",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gib.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GRC",
      display: "Greece",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/grc.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GRL",
      display: "Greenland",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/grl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GRD",
      display: "Grenada",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/grd.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GLP",
      display: "Guadeloupe",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/glp.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GUM",
      display: "Guam",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gum.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GTM",
      display: "Guatemala",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gtm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GGY",
      display: "Guernsey",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ggy.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GIN",
      display: "Guinea",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gin.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GNB",
      display: "Guinea-Bissau",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gnb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GUY",
      display: "Guyana",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/guy.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "HTI",
      display: "Haiti",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/hti.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "HMD",
      display: "Heard Island and McDonald Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/hmd.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "HND",
      display: "Honduras",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/hnd.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "HKG",
      display: "Hong Kong",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/hkg.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "HUN",
      display: "Hungary",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/hun.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ISL",
      display: "Iceland",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/isl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "IND",
      display: "India",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ind.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "IDN",
      display: "Indonesia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/idn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "IRN",
      display: "Iran",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/irn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "IRQ",
      display: "Iraq",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/irq.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "IRL",
      display: "Ireland",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/irl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "IMN",
      display: "Isle of Man",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/imn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ISR",
      display: "Israel",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/isr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ITA",
      display: "Italy",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ita.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CIV",
      display: "Ivory Coast",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/civ.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "JAM",
      display: "Jamaica",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/jam.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "JPN",
      display: "Japan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/jpn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "JEY",
      display: "Jersey",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/jey.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "JOR",
      display: "Jordan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/jor.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KAZ",
      display: "Kazakhstan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/kaz.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KEN",
      display: "Kenya",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ken.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KIR",
      display: "Kiribati",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/kir.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "XKX",
      display: "Kosovo",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/xkx.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KWT",
      display: "Kuwait",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/kwt.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KGZ",
      display: "Kyrgyzstan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/kgz.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LAO",
      display: "Laos",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lao.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LVA",
      display: "Latvia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lva.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LBN",
      display: "Lebanon",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lbn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LSO",
      display: "Lesotho",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lso.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LBR",
      display: "Liberia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lbr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LBY",
      display: "Libya",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lby.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LIE",
      display: "Liechtenstein",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lie.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LTU",
      display: "Lithuania",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ltu.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LUX",
      display: "Luxembourg",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lux.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MAC",
      display: "Macau",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mac.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MDG",
      display: "Madagascar",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mdg.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MWI",
      display: "Malawi",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mwi.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MYS",
      display: "Malaysia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mys.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MDV",
      display: "Maldives",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mdv.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MLI",
      display: "Mali",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mli.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MLT",
      display: "Malta",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mlt.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MHL",
      display: "Marshall Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mhl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MTQ",
      display: "Martinique",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mtq.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MRT",
      display: "Mauritania",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mrt.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MUS",
      display: "Mauritius",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mus.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MYT",
      display: "Mayotte",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/myt.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MEX",
      display: "Mexico",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mex.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "FSM",
      display: "Micronesia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/fsm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MDA",
      display: "Moldova",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mda.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MCO",
      display: "Monaco",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mco.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MNG",
      display: "Mongolia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mng.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MNE",
      display: "Montenegro",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mne.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MSR",
      display: "Montserrat",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/msr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MAR",
      display: "Morocco",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mar.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MOZ",
      display: "Mozambique",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/moz.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MMR",
      display: "Myanmar",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mmr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NAM",
      display: "Namibia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nam.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NRU",
      display: "Nauru",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nru.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NPL",
      display: "Nepal",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/npl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NLD",
      display: "Netherlands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nld.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NCL",
      display: "New Caledonia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ncl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NZL",
      display: "New Zealand",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nzl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NIC",
      display: "Nicaragua",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nic.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NER",
      display: "Niger",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ner.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NGA",
      display: "Nigeria",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nga.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NIU",
      display: "Niue",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/niu.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NFK",
      display: "Norfolk Island",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nfk.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PRK",
      display: "North Korea",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/prk.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MKD",
      display: "North Macedonia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mkd.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MNP",
      display: "Northern Mariana Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/mnp.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "NOR",
      display: "Norway",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/nor.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "OMN",
      display: "Oman",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/omn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PAK",
      display: "Pakistan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pak.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PLW",
      display: "Palau",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/plw.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PSE",
      display: "Palestine",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pse.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PAN",
      display: "Panama",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pan.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PNG",
      display: "Papua New Guinea",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/png.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PRY",
      display: "Paraguay",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pry.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PER",
      display: "Peru",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/per.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PHL",
      display: "Philippines",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/phl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PCN",
      display: "Pitcairn Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pcn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "POL",
      display: "Poland",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pol.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PRT",
      display: "Portugal",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/prt.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "PRI",
      display: "Puerto Rico",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/pri.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "QAT",
      display: "Qatar",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/qat.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "REU",
      display: "Réunion",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/reu.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ROU",
      display: "Romania",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/rou.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "RUS",
      display: "Russia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/rus.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "RWA",
      display: "Rwanda",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/rwa.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "BLM",
      display: "Saint Barthélemy",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/blm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SHN",
      display: "Saint Helena, Ascension and Tristan da Cunha",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/shn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KNA",
      display: "Saint Kitts and Nevis",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/kna.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LCA",
      display: "Saint Lucia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lca.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "MAF",
      display: "Saint Martin",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/maf.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SPM",
      display: "Saint Pierre and Miquelon",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/spm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "VCT",
      display: "Saint Vincent and the Grenadines",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/vct.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "WSM",
      display: "Samoa",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/wsm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SMR",
      display: "San Marino",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/smr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "STP",
      display: "São Tomé and Príncipe",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/stp.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SAU",
      display: "Saudi Arabia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sau.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SEN",
      display: "Senegal",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sen.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SRB",
      display: "Serbia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/srb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SYC",
      display: "Seychelles",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/syc.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SLE",
      display: "Sierra Leone",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sle.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SGP",
      display: "Singapore",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sgp.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SXM",
      display: "Sint Maarten",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sxm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SVK",
      display: "Slovakia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/svk.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SVN",
      display: "Slovenia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/svn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SLB",
      display: "Solomon Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/slb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SOM",
      display: "Somalia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/som.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ZAF",
      display: "South Africa",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/zaf.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SGS",
      display: "South Georgia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sgs.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "KOR",
      display: "South Korea",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/kor.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SSD",
      display: "South Sudan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ssd.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ESP",
      display: "Spain",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/esp.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "LKA",
      display: "Sri Lanka",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/lka.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SDN",
      display: "Sudan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sdn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SUR",
      display: "Suriname",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sur.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SJM",
      display: "Svalbard and Jan Mayen",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/sjm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SWE",
      display: "Sweden",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/swe.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "CHE",
      display: "Switzerland",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/che.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "SYR",
      display: "Syria",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/syr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TWN",
      display: "Taiwan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/twn.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TJK",
      display: "Tajikistan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tjk.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TZA",
      display: "Tanzania",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tza.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "THA",
      display: "Thailand",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tha.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TLS",
      display: "Timor-Leste",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tls.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TGO",
      display: "Togo",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tgo.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TKL",
      display: "Tokelau",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tkl.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TON",
      display: "Tonga",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ton.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TTO",
      display: "Trinidad and Tobago",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tto.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TUN",
      display: "Tunisia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tun.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TUR",
      display: "Turkey",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tur.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TKM",
      display: "Turkmenistan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tkm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TCA",
      display: "Turks and Caicos Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tca.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "TUV",
      display: "Tuvalu",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/tuv.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "UGA",
      display: "Uganda",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/uga.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "UKR",
      display: "Ukraine",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ukr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ARE",
      display: "United Arab Emirates",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/are.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "GBR",
      display: "United Kingdom",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/gbr.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "USA",
      display: "United States",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/usa.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "UMI",
      display: "United States Minor Outlying Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/umi.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "VIR",
      display: "United States Virgin Islands",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/vir.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "URY",
      display: "Uruguay",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ury.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "UZB",
      display: "Uzbekistan",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/uzb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "VUT",
      display: "Vanuatu",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/vut.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "VAT",
      display: "Vatican City",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/vat.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "VEN",
      display: "Venezuela",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/ven.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "VNM",
      display: "Vietnam",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/vnm.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "WLF",
      display: "Wallis and Futuna",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/wlf.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ESH",
      display: "Western Sahara",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/esh.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "YEM",
      display: "Yemen",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/yem.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ZMB",
      display: "Zambia",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/zmb.svg",
        alt: "Country flag",
      },
    },
    {
      answer: "ZWE",
      display: "Zimbabwe",
      prompt: {
        type: "image",
        imageUrl: "/data/country-flags/zwe.svg",
        alt: "Country flag",
      },
    },
  ],
};
