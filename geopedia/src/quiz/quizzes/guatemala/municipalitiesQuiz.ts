import { GUATEMALA_DEPARTMENT_NAMES_BY_ID } from "@/constants/guatemalaSubdivisions";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * All Guatemalan municipality questions keyed by municipality ID.
 * Duplicate municipality names are disambiguated with their parent
 * department names.
 */
const GUATEMALA_MUNICIPALITY_QUESTIONS = [
  {
    answer: "0100",
    display: "Lago De Amatitlan",
  },
  {
    answer: "0101",
    display: "Guatemala",
  },
  {
    answer: "0102",
    display: "Santa Catarina Pinula",
  },
  {
    answer: "0103",
    display: "San José Pinula",
  },
  {
    answer: "0104",
    display: "San José del Golfo",
  },
  {
    answer: "0105",
    display: "Palencia",
  },
  {
    answer: "0106",
    display: "Chinautla",
  },
  {
    answer: "0107",
    display: "San Pedro Ayampuc",
  },
  {
    answer: "0108",
    display: "Mixco",
  },
  {
    answer: "0109",
    display: "San Pedro Sacatepéquez (Guatemala)",
  },
  {
    answer: "0110",
    display: "San Juan Sacatepéquez",
  },
  {
    answer: "0111",
    display: "San Raimundo",
  },
  {
    answer: "0112",
    display: "Chuarrancho",
  },
  {
    answer: "0113",
    display: "Fraijanes",
  },
  {
    answer: "0114",
    display: "Amatitlán",
  },
  {
    answer: "0115",
    display: "Villa Nueva",
  },
  {
    answer: "0116",
    display: "Villa Canales",
  },
  {
    answer: "0117",
    display: "Petapa",
  },
  {
    answer: "0201",
    display: "Guastatoya",
  },
  {
    answer: "0202",
    display: "Morazán",
  },
  {
    answer: "0203",
    display: "San Agustín Acasaguastlán",
  },
  {
    answer: "0204",
    display: "San Cristóbal Acasaguastlán",
  },
  {
    answer: "0205",
    display: "El Jícaro",
  },
  {
    answer: "0206",
    display: "Sanarate",
  },
  {
    answer: "0207",
    display: "Sansare",
  },
  {
    answer: "0208",
    display: "San Antonio La Paz",
  },
  {
    answer: "0301",
    display: "Antigua Guatemala",
  },
  {
    answer: "0302",
    display: "Jocotenango",
  },
  {
    answer: "0303",
    display: "Pastores",
  },
  {
    answer: "0304",
    display: "Sumpango",
  },
  {
    answer: "0305",
    display: "Santo Domingo Xenacoj",
  },
  {
    answer: "0306",
    display: "Santiago Sacatepéquez",
  },
  {
    answer: "0307",
    display: "San Bartolomé Milpas Altas",
  },
  {
    answer: "0308",
    display: "San Lucas Sacatepéquez",
  },
  {
    answer: "0309",
    display: "Santa Lucía Milpas Altas",
  },
  {
    answer: "0310",
    display: "Magdalena Milpas Altas",
  },
  {
    answer: "0311",
    display: "Santa María de Jesús",
  },
  {
    answer: "0312",
    display: "Ciudad Vieja",
  },
  {
    answer: "0313",
    display: "San Miguel Dueñas",
  },
  {
    answer: "0314",
    display: "Alotenango",
  },
  {
    answer: "0315",
    display: "San Antonio Aguas Calientes",
  },
  {
    answer: "0316",
    display: "Santa Catarina Barahona",
  },
  {
    answer: "0401",
    display: "Chimaltenango",
  },
  {
    answer: "0402",
    display: "San José Poaquil",
  },
  {
    answer: "0403",
    display: "San Martín Jilotepeque",
  },
  {
    answer: "0404",
    display: "Comalapa",
  },
  {
    answer: "0405",
    display: "Santa Apolonia",
  },
  {
    answer: "0406",
    display: "Tecpán Guatemala",
  },
  {
    answer: "0407",
    display: "Patzún",
  },
  {
    answer: "0408",
    display: "Pochuta",
  },
  {
    answer: "0409",
    display: "Patzicía",
  },
  {
    answer: "0410",
    display: "Santa Cruz Balanyá",
  },
  {
    answer: "0411",
    display: "Acatenango",
  },
  {
    answer: "0412",
    display: "Yepocapa",
  },
  {
    answer: "0413",
    display: "San Andrés Itzapa",
  },
  {
    answer: "0414",
    display: "Parramos",
  },
  {
    answer: "0415",
    display: "Zaragoza",
  },
  {
    answer: "0416",
    display: "El Tejar",
  },
  {
    answer: "0501",
    display: "Escuintla",
  },
  {
    answer: "0502",
    display: "Santa Lucía Cotzumalguapa",
  },
  {
    answer: "0503",
    display: "La Democracia (Escuintla)",
  },
  {
    answer: "0504",
    display: "Siquinalá",
  },
  {
    answer: "0505",
    display: "Masagua",
  },
  {
    answer: "0506",
    display: "Tiquisate",
  },
  {
    answer: "0507",
    display: "La Gomera",
  },
  {
    answer: "0508",
    display: "Guanagazapa",
  },
  {
    answer: "0509",
    display: "San José (Escuintla)",
  },
  {
    answer: "0510",
    display: "Iztapa",
  },
  {
    answer: "0511",
    display: "Palín",
  },
  {
    answer: "0512",
    display: "San Vicente Pacaya",
  },
  {
    answer: "0513",
    display: "Nueva Concepción",
  },
  {
    answer: "0514",
    display: "Sipacate",
  },
  {
    answer: "0601",
    display: "Cuilapa",
  },
  {
    answer: "0602",
    display: "Barberena",
  },
  {
    answer: "0603",
    display: "Santa Rosa de Lima",
  },
  {
    answer: "0604",
    display: "Casillas",
  },
  {
    answer: "0605",
    display: "San Rafael Las Flores",
  },
  {
    answer: "0606",
    display: "Oratorio",
  },
  {
    answer: "0607",
    display: "San Juan Tecuaco",
  },
  {
    answer: "0608",
    display: "Chiquimulilla",
  },
  {
    answer: "0609",
    display: "Taxisco",
  },
  {
    answer: "0610",
    display: "Santa María Ixhuatán",
  },
  {
    answer: "0611",
    display: "Guazacapán",
  },
  {
    answer: "0612",
    display: "Santa Cruz Naranjo",
  },
  {
    answer: "0613",
    display: "Pueblo Nuevo Viñas",
  },
  {
    answer: "0614",
    display: "Nueva Santa Rosa",
  },
  {
    answer: "0700",
    display: "Lago De Atitlan",
  },
  {
    answer: "0701",
    display: "Sololá",
  },
  {
    answer: "0702",
    display: "San José Chacayá",
  },
  {
    answer: "0703",
    display: "Santa María Visitación",
  },
  {
    answer: "0704",
    display: "Santa Lucía Utatlán",
  },
  {
    answer: "0705",
    display: "Nahualá",
  },
  {
    answer: "0706",
    display: "Santa Catarina Ixtahuacán",
  },
  {
    answer: "0707",
    display: "Santa Clara La Laguna",
  },
  {
    answer: "0708",
    display: "Concepción",
  },
  {
    answer: "0709",
    display: "San Andrés Semetabaj",
  },
  {
    answer: "0710",
    display: "Panajachel",
  },
  {
    answer: "0711",
    display: "Santa Catarina Palopó",
  },
  {
    answer: "0712",
    display: "San Antonio Palopó",
  },
  {
    answer: "0713",
    display: "San Lucas Tolimán",
  },
  {
    answer: "0714",
    display: "Santa Cruz La Laguna",
  },
  {
    answer: "0715",
    display: "San Pablo La Laguna",
  },
  {
    answer: "0716",
    display: "San Marcos La Laguna",
  },
  {
    answer: "0717",
    display: "San Juan La Laguna",
  },
  {
    answer: "0718",
    display: "San Pedro La Laguna",
  },
  {
    answer: "0719",
    display: "Santiago Atitlán",
  },
  {
    answer: "0801",
    display: "Totonicapán",
  },
  {
    answer: "0802",
    display: "San Cristóbal Totonicapán",
  },
  {
    answer: "0803",
    display: "San Francisco El Alto",
  },
  {
    answer: "0804",
    display: "San Andrés Xecul",
  },
  {
    answer: "0805",
    display: "Momostenango",
  },
  {
    answer: "0806",
    display: "Santa María Chiquimula",
  },
  {
    answer: "0807",
    display: "Santa Lucía La Reforma",
  },
  {
    answer: "0808",
    display: "San Bartolo",
  },
  {
    answer: "0901",
    display: "Quetzaltenango",
  },
  {
    answer: "0902",
    display: "Salcajá",
  },
  {
    answer: "0903",
    display: "Olintepeque",
  },
  {
    answer: "0904",
    display: "San Carlos Sija",
  },
  {
    answer: "0905",
    display: "Sibilia",
  },
  {
    answer: "0906",
    display: "Cabricán",
  },
  {
    answer: "0907",
    display: "Cajolá",
  },
  {
    answer: "0908",
    display: "San Miguel Sigüila",
  },
  {
    answer: "0909",
    display: "Ostuncalco",
  },
  {
    answer: "0910",
    display: "San Mateo",
  },
  {
    answer: "0911",
    display: "Concepción Chiquirichapa",
  },
  {
    answer: "0912",
    display: "San Martín Sacatepéquez",
  },
  {
    answer: "0913",
    display: "Almolonga",
  },
  {
    answer: "0914",
    display: "Cantel",
  },
  {
    answer: "0915",
    display: "Huitán",
  },
  {
    answer: "0916",
    display: "Zunil",
  },
  {
    answer: "0917",
    display: "Colomba",
  },
  {
    answer: "0918",
    display: "San Francisco La Unión",
  },
  {
    answer: "0919",
    display: "El Palmar",
  },
  {
    answer: "0920",
    display: "Coatepeque",
  },
  {
    answer: "0921",
    display: "Génova",
  },
  {
    answer: "0922",
    display: "Flores Costa Cuca",
  },
  {
    answer: "0923",
    display: "La Esperanza",
  },
  {
    answer: "0924",
    display: "Palestina de Los Altos",
  },
  {
    answer: "1001",
    display: "Mazatenango",
  },
  {
    answer: "1002",
    display: "Cuyotenango",
  },
  {
    answer: "1003",
    display: "San Francisco Zapotitlán",
  },
  {
    answer: "1004",
    display: "San Bernardino",
  },
  {
    answer: "1005",
    display: "San José El Ídolo",
  },
  {
    answer: "1006",
    display: "Santo Domingo Suchitepéquez",
  },
  {
    answer: "1007",
    display: "San Lorenzo (Suchitepéquez)",
  },
  {
    answer: "1008",
    display: "Samayac",
  },
  {
    answer: "1009",
    display: "San Pablo Jocopilas",
  },
  {
    answer: "1010",
    display: "San Antonio Suchitepéquez",
  },
  {
    answer: "1011",
    display: "San Miguel Panán",
  },
  {
    answer: "1012",
    display: "San Gabriel",
  },
  {
    answer: "1013",
    display: "Chicacao",
  },
  {
    answer: "1014",
    display: "Patulul",
  },
  {
    answer: "1015",
    display: "Santa Bárbara (Suchitepéquez)",
  },
  {
    answer: "1016",
    display: "San Juan Bautista",
  },
  {
    answer: "1017",
    display: "Santo Tomás La Unión",
  },
  {
    answer: "1018",
    display: "Zunilito",
  },
  {
    answer: "1019",
    display: "Pueblo Nuevo",
  },
  {
    answer: "1020",
    display: "Río Bravo",
  },
  {
    answer: "1021",
    display: "San José La Máquina",
  },
  {
    answer: "1101",
    display: "Retalhuleu",
  },
  {
    answer: "1102",
    display: "San Sebastián",
  },
  {
    answer: "1103",
    display: "Santa Cruz Muluá",
  },
  {
    answer: "1104",
    display: "San Martín Zapotitlán",
  },
  {
    answer: "1105",
    display: "San Felipe",
  },
  {
    answer: "1106",
    display: "San Andrés Villa Seca",
  },
  {
    answer: "1107",
    display: "Champerico",
  },
  {
    answer: "1108",
    display: "Nuevo San Carlos",
  },
  {
    answer: "1109",
    display: "El Asintal",
  },
  {
    answer: "1201",
    display: "San Marcos",
  },
  {
    answer: "1202",
    display: "San Pedro Sacatepéquez (San Marcos)",
  },
  {
    answer: "1203",
    display: "San Antonio Sacatepéquez",
  },
  {
    answer: "1204",
    display: "Comitancillo",
  },
  {
    answer: "1205",
    display: "San Miguel Ixtahuacán",
  },
  {
    answer: "1206",
    display: "Concepción Tutuapa",
  },
  {
    answer: "1207",
    display: "Tacaná",
  },
  {
    answer: "1208",
    display: "Sibinal",
  },
  {
    answer: "1209",
    display: "Tajumulco",
  },
  {
    answer: "1210",
    display: "Tejutla",
  },
  {
    answer: "1211",
    display: "San Rafael Pie de la Cuesta",
  },
  {
    answer: "1212",
    display: "Nuevo Progreso",
  },
  {
    answer: "1213",
    display: "El Tumbador",
  },
  {
    answer: "1214",
    display: "El Rodeo",
  },
  {
    answer: "1215",
    display: "Malacatán",
  },
  {
    answer: "1216",
    display: "Catarina",
  },
  {
    answer: "1217",
    display: "Ayutla",
  },
  {
    answer: "1218",
    display: "Ocós",
  },
  {
    answer: "1219",
    display: "San Pablo",
  },
  {
    answer: "1220",
    display: "El Quetzal",
  },
  {
    answer: "1221",
    display: "La Reforma",
  },
  {
    answer: "1222",
    display: "Pajapita",
  },
  {
    answer: "1223",
    display: "Ixchiguán",
  },
  {
    answer: "1224",
    display: "San José Ojetenam",
  },
  {
    answer: "1225",
    display: "San Cristóbal Cucho",
  },
  {
    answer: "1226",
    display: "Sipacapa",
  },
  {
    answer: "1227",
    display: "Esquipulas Palo Gordo",
  },
  {
    answer: "1228",
    display: "Río Blanco",
  },
  {
    answer: "1229",
    display: "San Lorenzo (San Marcos)",
  },
  {
    answer: "1230",
    display: "La Blanca",
  },
  {
    answer: "1301",
    display: "Huehuetenango",
  },
  {
    answer: "1302",
    display: "Chiantla",
  },
  {
    answer: "1303",
    display: "Malacatancito",
  },
  {
    answer: "1304",
    display: "Cuilco",
  },
  {
    answer: "1305",
    display: "Nentón",
  },
  {
    answer: "1306",
    display: "San Pedro Necta",
  },
  {
    answer: "1307",
    display: "Jacaltenango",
  },
  {
    answer: "1308",
    display: "Soloma",
  },
  {
    answer: "1309",
    display: "Ixtahuacán",
  },
  {
    answer: "1310",
    display: "Santa Bárbara (Huehuetenango)",
  },
  {
    answer: "1311",
    display: "La Libertad (Huehuetenango)",
  },
  {
    answer: "1312",
    display: "La Democracia (Huehuetenango)",
  },
  {
    answer: "1313",
    display: "San Miguel Acatán",
  },
  {
    answer: "1314",
    display: "San Rafael La Independencia",
  },
  {
    answer: "1315",
    display: "Todos Santos Cuchumatán",
  },
  {
    answer: "1316",
    display: "San Juan Atitán",
  },
  {
    answer: "1317",
    display: "Santa Eulalia",
  },
  {
    answer: "1318",
    display: "San Mateo Ixtatán",
  },
  {
    answer: "1319",
    display: "Colotenango",
  },
  {
    answer: "1320",
    display: "San Sebastián Huehuetenango",
  },
  {
    answer: "1321",
    display: "Tectitán",
  },
  {
    answer: "1322",
    display: "Concepción Huista",
  },
  {
    answer: "1323",
    display: "San Juan Ixcoy",
  },
  {
    answer: "1324",
    display: "San Antonio Huista",
  },
  {
    answer: "1325",
    display: "San Sebastián Coatán",
  },
  {
    answer: "1326",
    display: "Barillas",
  },
  {
    answer: "1327",
    display: "Aguacatán",
  },
  {
    answer: "1328",
    display: "San Rafael Petzal",
  },
  {
    answer: "1329",
    display: "San Gaspar Ixchil",
  },
  {
    answer: "1330",
    display: "Santiago Chimaltenango",
  },
  {
    answer: "1331",
    display: "Santa Ana Huista",
  },
  {
    answer: "1332",
    display: "Unión Cantinil",
  },
  {
    answer: "1333",
    display: "Petatán",
  },
  {
    answer: "1401",
    display: "Santa Cruz del Quiché",
  },
  {
    answer: "1402",
    display: "Chiché",
  },
  {
    answer: "1403",
    display: "Chinique",
  },
  {
    answer: "1404",
    display: "Zacualpa",
  },
  {
    answer: "1405",
    display: "Chajul",
  },
  {
    answer: "1406",
    display: "Chichicastenango",
  },
  {
    answer: "1407",
    display: "Patzité",
  },
  {
    answer: "1408",
    display: "San Antonio Ilotenango",
  },
  {
    answer: "1409",
    display: "San Pedro Jocopilas",
  },
  {
    answer: "1410",
    display: "Cunén",
  },
  {
    answer: "1411",
    display: "San Juan Cotzal",
  },
  {
    answer: "1412",
    display: "Joyabaj",
  },
  {
    answer: "1413",
    display: "Nebaj",
  },
  {
    answer: "1414",
    display: "San Andrés Sajcabajá",
  },
  {
    answer: "1415",
    display: "Uspantán",
  },
  {
    answer: "1416",
    display: "Sacapulas",
  },
  {
    answer: "1417",
    display: "San Bartolomé Jocotenango",
  },
  {
    answer: "1418",
    display: "Canillá",
  },
  {
    answer: "1419",
    display: "Chicamán",
  },
  {
    answer: "1420",
    display: "Ixcán",
  },
  {
    answer: "1421",
    display: "Pachalum",
  },
  {
    answer: "1501",
    display: "Salamá",
  },
  {
    answer: "1502",
    display: "San Miguel Chicaj",
  },
  {
    answer: "1503",
    display: "Rabinal",
  },
  {
    answer: "1504",
    display: "Cubulco",
  },
  {
    answer: "1505",
    display: "Granados",
  },
  {
    answer: "1506",
    display: "El Chol",
  },
  {
    answer: "1507",
    display: "San Jerónimo",
  },
  {
    answer: "1508",
    display: "Purulhá",
  },
  {
    answer: "1601",
    display: "Cobán",
  },
  {
    answer: "1602",
    display: "Santa Cruz Verapaz",
  },
  {
    answer: "1603",
    display: "San Cristóbal Verapaz",
  },
  {
    answer: "1604",
    display: "Tactic",
  },
  {
    answer: "1605",
    display: "Tamahú",
  },
  {
    answer: "1606",
    display: "Tucurú",
  },
  {
    answer: "1607",
    display: "Panzós",
  },
  {
    answer: "1608",
    display: "Senahú",
  },
  {
    answer: "1609",
    display: "San Pedro Carchá",
  },
  {
    answer: "1610",
    display: "San Juan Chamelco",
  },
  {
    answer: "1611",
    display: "Lanquín",
  },
  {
    answer: "1612",
    display: "Cahabón",
  },
  {
    answer: "1613",
    display: "Chisec",
  },
  {
    answer: "1614",
    display: "Chahal",
  },
  {
    answer: "1615",
    display: "Fray Bartolomé de Las Casas",
  },
  {
    answer: "1616",
    display: "Santa Catalina La Tinta",
  },
  {
    answer: "1617",
    display: "Raxruhá",
  },
  {
    answer: "1701",
    display: "Flores",
  },
  {
    answer: "1702",
    display: "San José (Petén)",
  },
  {
    answer: "1703",
    display: "San Benito",
  },
  {
    answer: "1704",
    display: "San Andrés",
  },
  {
    answer: "1705",
    display: "La Libertad (Petén)",
  },
  {
    answer: "1706",
    display: "San Francisco",
  },
  {
    answer: "1707",
    display: "Santa Ana",
  },
  {
    answer: "1708",
    display: "Dolores",
  },
  {
    answer: "1709",
    display: "San Luis",
  },
  {
    answer: "1710",
    display: "Sayaxché",
  },
  {
    answer: "1711",
    display: "Melchor de Mencos",
  },
  {
    answer: "1712",
    display: "Poptún",
  },
  {
    answer: "1713",
    display: "Las Cruces",
  },
  {
    answer: "1714",
    display: "El Chal",
  },
  {
    answer: "1801",
    display: "Puerto Barrios",
  },
  {
    answer: "1802",
    display: "Lívingston",
  },
  {
    answer: "1803",
    display: "El Estor",
  },
  {
    answer: "1804",
    display: "Morales",
  },
  {
    answer: "1805",
    display: "Los Amates",
  },
  {
    answer: "1901",
    display: "Zacapa",
  },
  {
    answer: "1902",
    display: "Estanzuela",
  },
  {
    answer: "1903",
    display: "Río Hondo",
  },
  {
    answer: "1904",
    display: "Gualán",
  },
  {
    answer: "1905",
    display: "Teculután",
  },
  {
    answer: "1906",
    display: "Usumatlán",
  },
  {
    answer: "1907",
    display: "Cabañas",
  },
  {
    answer: "1908",
    display: "San Diego",
  },
  {
    answer: "1909",
    display: "La Unión",
  },
  {
    answer: "1910",
    display: "Huité",
  },
  {
    answer: "1911",
    display: "San Jorge",
  },
  {
    answer: "2001",
    display: "Chiquimula",
  },
  {
    answer: "2002",
    display: "San José La Arada",
  },
  {
    answer: "2003",
    display: "San Juan Ermita",
  },
  {
    answer: "2004",
    display: "Jocotán",
  },
  {
    answer: "2005",
    display: "Camotán",
  },
  {
    answer: "2006",
    display: "Olopa",
  },
  {
    answer: "2007",
    display: "Esquipulas",
  },
  {
    answer: "2008",
    display: "Concepción Las Minas",
  },
  {
    answer: "2009",
    display: "Quezaltepeque",
  },
  {
    answer: "2010",
    display: "San Jacinto",
  },
  {
    answer: "2011",
    display: "Ipala",
  },
  {
    answer: "2101",
    display: "Jalapa",
  },
  {
    answer: "2102",
    display: "San Pedro Pinula",
  },
  {
    answer: "2103",
    display: "San Luis Jilotepeque",
  },
  {
    answer: "2104",
    display: "San Manuel Chaparrón",
  },
  {
    answer: "2105",
    display: "San Carlos Alzatate",
  },
  {
    answer: "2106",
    display: "Monjas",
  },
  {
    answer: "2107",
    display: "Mataquescuintla",
  },
  {
    answer: "2201",
    display: "Jutiapa",
  },
  {
    answer: "2202",
    display: "El Progreso",
  },
  {
    answer: "2203",
    display: "Santa Catarina Mita",
  },
  {
    answer: "2204",
    display: "Agua Blanca",
  },
  {
    answer: "2205",
    display: "Asunción Mita",
  },
  {
    answer: "2206",
    display: "Yupiltepeque",
  },
  {
    answer: "2207",
    display: "Atescatempa",
  },
  {
    answer: "2208",
    display: "Jerez",
  },
  {
    answer: "2209",
    display: "El Adelanto",
  },
  {
    answer: "2210",
    display: "Zapotitlán",
  },
  {
    answer: "2211",
    display: "Comapa",
  },
  {
    answer: "2212",
    display: "Jalpatagua",
  },
  {
    answer: "2213",
    display: "Conguaco",
  },
  {
    answer: "2214",
    display: "Moyuta",
  },
  {
    answer: "2215",
    display: "Pasaco",
  },
  {
    answer: "2216",
    display: "San José Acatempa",
  },
  {
    answer: "2217",
    display: "Quesada",
  },
];

/**
 * Quiz configuration for all Guatemalan municipalities,
 * grouped by department.
 */
export const guatemalaMunicipalitiesQuiz: FeatureQuiz = {
  id: "guatemala-municipalities",
  name: "Municipalities",
  description: `Learn all ${GUATEMALA_MUNICIPALITY_QUESTIONS.length} municipalities of Guatemala, with filters that let you practice municipalities from any desired department or combination of departments.`,

  kind: "feature",
  mapId: "guatemala-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: GUATEMALA_DEPARTMENT_NAMES_BY_ID,
      },
    ],
  },

  questions: GUATEMALA_MUNICIPALITY_QUESTIONS,
};
