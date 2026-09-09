import { MEXICO_STATE_NAMES_BY_ID } from "@/constants/mexicoSubdivisions";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * All Mexican municipality questions keyed by INEGI municipality ID.
 * Duplicate municipality names are disambiguated with state
 * abbreviations and, when necessary, municipality codes.
 */
const MEXICO_MUNICIPALITY_QUESTIONS = [
  {
    answer: "01001",
    display: "Aguascalientes",
  },
  {
    answer: "01002",
    display: "Asientos",
  },
  {
    answer: "01003",
    display: "Calvillo",
  },
  {
    answer: "01004",
    display: "Cosío",
  },
  {
    answer: "01005",
    display: "Jesús María (Ags.)",
  },
  {
    answer: "01006",
    display: "Pabellón de Arteaga",
  },
  {
    answer: "01007",
    display: "Rincón de Romos",
  },
  {
    answer: "01008",
    display: "San José de Gracia",
  },
  {
    answer: "01009",
    display: "Tepezalá",
  },
  {
    answer: "01010",
    display: "El Llano",
  },
  {
    answer: "01011",
    display: "San Francisco de los Romo",
  },
  {
    answer: "02001",
    display: "Ensenada",
  },
  {
    answer: "02002",
    display: "Mexicali",
  },
  {
    answer: "02003",
    display: "Tecate",
  },
  {
    answer: "02004",
    display: "Tijuana",
  },
  {
    answer: "02005",
    display: "Playas de Rosarito",
  },
  {
    answer: "02006",
    display: "San Quintín",
  },
  {
    answer: "02007",
    display: "San Felipe (B.C.)",
  },
  {
    answer: "03001",
    display: "Comondú",
  },
  {
    answer: "03002",
    display: "Mulegé",
  },
  {
    answer: "03003",
    display: "La Paz (B.C.S.)",
  },
  {
    answer: "03008",
    display: "Los Cabos",
  },
  {
    answer: "03009",
    display: "Loreto (B.C.S.)",
  },
  {
    answer: "04001",
    display: "Calkiní",
  },
  {
    answer: "04002",
    display: "Campeche",
  },
  {
    answer: "04003",
    display: "Carmen",
  },
  {
    answer: "04004",
    display: "Champotón",
  },
  {
    answer: "04005",
    display: "Hecelchakán",
  },
  {
    answer: "04006",
    display: "Hopelchén",
  },
  {
    answer: "04007",
    display: "Palizada",
  },
  {
    answer: "04008",
    display: "Tenabo",
  },
  {
    answer: "04009",
    display: "Escárcega",
  },
  {
    answer: "04010",
    display: "Calakmul",
  },
  {
    answer: "04011",
    display: "Candelaria",
  },
  {
    answer: "04012",
    display: "Seybaplaya",
  },
  {
    answer: "04013",
    display: "Dzitbalché",
  },
  {
    answer: "05001",
    display: "Abasolo (Coah.)",
  },
  {
    answer: "05002",
    display: "Acuña",
  },
  {
    answer: "05003",
    display: "Allende (Coah.)",
  },
  {
    answer: "05004",
    display: "Arteaga (Coah.)",
  },
  {
    answer: "05005",
    display: "Candela",
  },
  {
    answer: "05006",
    display: "Castaños",
  },
  {
    answer: "05007",
    display: "Cuatro Ciénegas",
  },
  {
    answer: "05008",
    display: "Escobedo",
  },
  {
    answer: "05009",
    display: "Francisco I. Madero (Coah.)",
  },
  {
    answer: "05010",
    display: "Frontera",
  },
  {
    answer: "05011",
    display: "General Cepeda",
  },
  {
    answer: "05012",
    display: "Guerrero (Coah.)",
  },
  {
    answer: "05013",
    display: "Hidalgo (Coah.)",
  },
  {
    answer: "05014",
    display: "Jiménez (Coah.)",
  },
  {
    answer: "05015",
    display: "Juárez (Coah.)",
  },
  {
    answer: "05016",
    display: "Lamadrid",
  },
  {
    answer: "05017",
    display: "Matamoros (Coah.)",
  },
  {
    answer: "05018",
    display: "Monclova",
  },
  {
    answer: "05019",
    display: "Morelos (Coah.)",
  },
  {
    answer: "05020",
    display: "Múzquiz",
  },
  {
    answer: "05021",
    display: "Nadadores",
  },
  {
    answer: "05022",
    display: "Nava",
  },
  {
    answer: "05023",
    display: "Ocampo (Coah.)",
  },
  {
    answer: "05024",
    display: "Parras",
  },
  {
    answer: "05025",
    display: "Piedras Negras",
  },
  {
    answer: "05026",
    display: "Progreso (Coah.)",
  },
  {
    answer: "05027",
    display: "Ramos Arizpe",
  },
  {
    answer: "05028",
    display: "Sabinas",
  },
  {
    answer: "05029",
    display: "Sacramento",
  },
  {
    answer: "05030",
    display: "Saltillo",
  },
  {
    answer: "05031",
    display: "San Buenaventura",
  },
  {
    answer: "05032",
    display: "San Juan de Sabinas",
  },
  {
    answer: "05033",
    display: "San Pedro",
  },
  {
    answer: "05034",
    display: "Sierra Mojada",
  },
  {
    answer: "05035",
    display: "Torreón",
  },
  {
    answer: "05036",
    display: "Viesca",
  },
  {
    answer: "05037",
    display: "Villa Unión",
  },
  {
    answer: "05038",
    display: "Zaragoza (Coah.)",
  },
  {
    answer: "06001",
    display: "Armería",
  },
  {
    answer: "06002",
    display: "Colima",
  },
  {
    answer: "06003",
    display: "Comala",
  },
  {
    answer: "06004",
    display: "Coquimatlán",
  },
  {
    answer: "06005",
    display: "Cuauhtémoc (Col.)",
  },
  {
    answer: "06006",
    display: "Ixtlahuacán",
  },
  {
    answer: "06007",
    display: "Manzanillo",
  },
  {
    answer: "06008",
    display: "Minatitlán (Col.)",
  },
  {
    answer: "06009",
    display: "Tecomán",
  },
  {
    answer: "06010",
    display: "Villa de Álvarez",
  },
  {
    answer: "07001",
    display: "Acacoyagua",
  },
  {
    answer: "07002",
    display: "Acala",
  },
  {
    answer: "07003",
    display: "Acapetahua",
  },
  {
    answer: "07004",
    display: "Altamirano",
  },
  {
    answer: "07005",
    display: "Amatán",
  },
  {
    answer: "07006",
    display: "Amatenango de la Frontera",
  },
  {
    answer: "07007",
    display: "Amatenango del Valle",
  },
  {
    answer: "07008",
    display: "Ángel Albino Corzo",
  },
  {
    answer: "07009",
    display: "Arriaga",
  },
  {
    answer: "07010",
    display: "Bejucal de Ocampo",
  },
  {
    answer: "07011",
    display: "Bella Vista",
  },
  {
    answer: "07012",
    display: "Berriozábal",
  },
  {
    answer: "07013",
    display: "Bochil",
  },
  {
    answer: "07014",
    display: "El Bosque",
  },
  {
    answer: "07015",
    display: "Cacahoatán",
  },
  {
    answer: "07016",
    display: "Catazajá",
  },
  {
    answer: "07017",
    display: "Cintalapa de Figueroa",
  },
  {
    answer: "07018",
    display: "Coapilla",
  },
  {
    answer: "07019",
    display: "Comitán de Domínguez",
  },
  {
    answer: "07020",
    display: "La Concordia",
  },
  {
    answer: "07021",
    display: "Copainalá",
  },
  {
    answer: "07022",
    display: "Chalchihuitán",
  },
  {
    answer: "07023",
    display: "Chamula",
  },
  {
    answer: "07024",
    display: "Chanal",
  },
  {
    answer: "07025",
    display: "Chapultenango",
  },
  {
    answer: "07026",
    display: "Chenalhó",
  },
  {
    answer: "07027",
    display: "Chiapa de Corzo",
  },
  {
    answer: "07028",
    display: "Chiapilla",
  },
  {
    answer: "07029",
    display: "Chicoasén",
  },
  {
    answer: "07030",
    display: "Chicomuselo",
  },
  {
    answer: "07031",
    display: "Chilón",
  },
  {
    answer: "07032",
    display: "Escuintla",
  },
  {
    answer: "07033",
    display: "Francisco León",
  },
  {
    answer: "07034",
    display: "Frontera Comalapa",
  },
  {
    answer: "07035",
    display: "Frontera Hidalgo",
  },
  {
    answer: "07036",
    display: "La Grandeza",
  },
  {
    answer: "07037",
    display: "Huehuetán",
  },
  {
    answer: "07038",
    display: "Huixtán",
  },
  {
    answer: "07039",
    display: "Huitiupán",
  },
  {
    answer: "07040",
    display: "Huixtla",
  },
  {
    answer: "07041",
    display: "La Independencia",
  },
  {
    answer: "07042",
    display: "Ixhuatán",
  },
  {
    answer: "07043",
    display: "Ixtacomitán",
  },
  {
    answer: "07044",
    display: "Ixtapa",
  },
  {
    answer: "07045",
    display: "Ixtapangajoya",
  },
  {
    answer: "07046",
    display: "Jiquipilas",
  },
  {
    answer: "07047",
    display: "Jitotol",
  },
  {
    answer: "07048",
    display: "Juárez (Chis.)",
  },
  {
    answer: "07049",
    display: "Larráinzar",
  },
  {
    answer: "07050",
    display: "La Libertad",
  },
  {
    answer: "07051",
    display: "Mapastepec",
  },
  {
    answer: "07052",
    display: "Las Margaritas",
  },
  {
    answer: "07053",
    display: "Mazapa de Madero",
  },
  {
    answer: "07054",
    display: "Mazatán (Chis.)",
  },
  {
    answer: "07055",
    display: "Metapa",
  },
  {
    answer: "07056",
    display: "Mitontic",
  },
  {
    answer: "07057",
    display: "Motozintla",
  },
  {
    answer: "07058",
    display: "Nicolás Ruíz",
  },
  {
    answer: "07059",
    display: "Ocosingo",
  },
  {
    answer: "07060",
    display: "Ocotepec (Chis.)",
  },
  {
    answer: "07061",
    display: "Ocozocoautla de Espinosa",
  },
  {
    answer: "07062",
    display: "Ostuacán",
  },
  {
    answer: "07063",
    display: "Osumacinta",
  },
  {
    answer: "07064",
    display: "Oxchuc",
  },
  {
    answer: "07065",
    display: "Palenque",
  },
  {
    answer: "07066",
    display: "Pantelhó",
  },
  {
    answer: "07067",
    display: "Pantepec (Chis.)",
  },
  {
    answer: "07068",
    display: "Pichucalco",
  },
  {
    answer: "07069",
    display: "Pijijiapan",
  },
  {
    answer: "07070",
    display: "El Porvenir",
  },
  {
    answer: "07071",
    display: "Villa Comaltitlán",
  },
  {
    answer: "07072",
    display: "Pueblo Nuevo Solistahuacán",
  },
  {
    answer: "07073",
    display: "Rayón (Chis.)",
  },
  {
    answer: "07074",
    display: "Reforma",
  },
  {
    answer: "07075",
    display: "Las Rosas",
  },
  {
    answer: "07076",
    display: "Sabanilla",
  },
  {
    answer: "07077",
    display: "Salto de Agua",
  },
  {
    answer: "07078",
    display: "San Cristóbal de las Casas",
  },
  {
    answer: "07079",
    display: "San Fernando (Chis.)",
  },
  {
    answer: "07080",
    display: "Siltepec",
  },
  {
    answer: "07081",
    display: "Simojovel",
  },
  {
    answer: "07082",
    display: "Sitalá",
  },
  {
    answer: "07083",
    display: "Socoltenango",
  },
  {
    answer: "07084",
    display: "Solosuchiapa",
  },
  {
    answer: "07085",
    display: "Soyaló",
  },
  {
    answer: "07086",
    display: "Suchiapa",
  },
  {
    answer: "07087",
    display: "Suchiate",
  },
  {
    answer: "07088",
    display: "Sunuapa",
  },
  {
    answer: "07089",
    display: "Tapachula",
  },
  {
    answer: "07090",
    display: "Tapalapa",
  },
  {
    answer: "07091",
    display: "Tapilula",
  },
  {
    answer: "07092",
    display: "Tecpatán",
  },
  {
    answer: "07093",
    display: "Tenejapa",
  },
  {
    answer: "07094",
    display: "Teopisca",
  },
  {
    answer: "07096",
    display: "Tila",
  },
  {
    answer: "07097",
    display: "Tonalá (Chis.)",
  },
  {
    answer: "07098",
    display: "Totolapa",
  },
  {
    answer: "07099",
    display: "La Trinitaria",
  },
  {
    answer: "07100",
    display: "Tumbalá",
  },
  {
    answer: "07101",
    display: "Tuxtla Gutiérrez",
  },
  {
    answer: "07102",
    display: "Tuxtla Chico",
  },
  {
    answer: "07103",
    display: "Tuzantán",
  },
  {
    answer: "07104",
    display: "Tzimol",
  },
  {
    answer: "07105",
    display: "Unión Juárez",
  },
  {
    answer: "07106",
    display: "Venustiano Carranza (Chis.)",
  },
  {
    answer: "07107",
    display: "Villa Corzo",
  },
  {
    answer: "07108",
    display: "Villaflores",
  },
  {
    answer: "07109",
    display: "Yajalón",
  },
  {
    answer: "07110",
    display: "San Lucas (Chis.)",
  },
  {
    answer: "07111",
    display: "Zinacantán",
  },
  {
    answer: "07112",
    display: "San Juan Cancuc",
  },
  {
    answer: "07113",
    display: "Aldama (Chis.)",
  },
  {
    answer: "07114",
    display: "Benemérito de las Américas",
  },
  {
    answer: "07115",
    display: "Maravilla Tenejapa",
  },
  {
    answer: "07116",
    display: "Marqués de Comillas",
  },
  {
    answer: "07117",
    display: "Montecristo de Guerrero",
  },
  {
    answer: "07118",
    display: "San Andrés Duraznal",
  },
  {
    answer: "07119",
    display: "Santiago el Pinar",
  },
  {
    answer: "07120",
    display: "Capitán Luis Ángel Vidal",
  },
  {
    answer: "07121",
    display: "Rincón Chamula San Pedro",
  },
  {
    answer: "07122",
    display: "El Parral",
  },
  {
    answer: "07123",
    display: "Emiliano Zapata (Chis.)",
  },
  {
    answer: "07124",
    display: "Mezcalapa",
  },
  {
    answer: "07125",
    display: "Honduras de la Sierra",
  },
  {
    answer: "08001",
    display: "Ahumada",
  },
  {
    answer: "08002",
    display: "Aldama (Chih.)",
  },
  {
    answer: "08003",
    display: "Allende (Chih.)",
  },
  {
    answer: "08004",
    display: "Aquiles Serdán",
  },
  {
    answer: "08005",
    display: "Ascensión",
  },
  {
    answer: "08006",
    display: "Bachíniva",
  },
  {
    answer: "08007",
    display: "Balleza",
  },
  {
    answer: "08008",
    display: "Batopilas de Manuel Gómez Morín",
  },
  {
    answer: "08009",
    display: "Bocoyna",
  },
  {
    answer: "08010",
    display: "Buenaventura",
  },
  {
    answer: "08011",
    display: "Camargo (Chih.)",
  },
  {
    answer: "08012",
    display: "Carichí",
  },
  {
    answer: "08013",
    display: "Casas Grandes",
  },
  {
    answer: "08014",
    display: "Coronado",
  },
  {
    answer: "08015",
    display: "Coyame del Sotol",
  },
  {
    answer: "08016",
    display: "La Cruz",
  },
  {
    answer: "08017",
    display: "Cuauhtémoc (Chih.)",
  },
  {
    answer: "08018",
    display: "Cusihuiriachi",
  },
  {
    answer: "08019",
    display: "Chihuahua",
  },
  {
    answer: "08020",
    display: "Chínipas",
  },
  {
    answer: "08021",
    display: "Delicias",
  },
  {
    answer: "08022",
    display: "Dr. Belisario Domínguez",
  },
  {
    answer: "08023",
    display: "Galeana (Chih.)",
  },
  {
    answer: "08024",
    display: "Santa Isabel",
  },
  {
    answer: "08025",
    display: "Gómez Farías (Chih.)",
  },
  {
    answer: "08026",
    display: "Gran Morelos",
  },
  {
    answer: "08027",
    display: "Guachochi",
  },
  {
    answer: "08028",
    display: "Guadalupe (Chih.)",
  },
  {
    answer: "08029",
    display: "Guadalupe y Calvo",
  },
  {
    answer: "08030",
    display: "Guazapares",
  },
  {
    answer: "08031",
    display: "Guerrero (Chih.)",
  },
  {
    answer: "08032",
    display: "Hidalgo del Parral",
  },
  {
    answer: "08033",
    display: "Huejotitán",
  },
  {
    answer: "08034",
    display: "Ignacio Zaragoza",
  },
  {
    answer: "08035",
    display: "Janos",
  },
  {
    answer: "08036",
    display: "Jiménez (Chih.)",
  },
  {
    answer: "08037",
    display: "Juárez (Chih.)",
  },
  {
    answer: "08038",
    display: "Julimes",
  },
  {
    answer: "08039",
    display: "López",
  },
  {
    answer: "08040",
    display: "Madera",
  },
  {
    answer: "08041",
    display: "Maguarichi",
  },
  {
    answer: "08042",
    display: "Manuel Benavides",
  },
  {
    answer: "08043",
    display: "Matachí",
  },
  {
    answer: "08044",
    display: "Matamoros (Chih.)",
  },
  {
    answer: "08045",
    display: "Meoqui",
  },
  {
    answer: "08046",
    display: "Morelos (Chih.)",
  },
  {
    answer: "08047",
    display: "Moris",
  },
  {
    answer: "08048",
    display: "Namiquipa",
  },
  {
    answer: "08049",
    display: "Nonoava",
  },
  {
    answer: "08050",
    display: "Nuevo Casas Grandes",
  },
  {
    answer: "08051",
    display: "Ocampo (Chih.)",
  },
  {
    answer: "08052",
    display: "Ojinaga",
  },
  {
    answer: "08053",
    display: "Praxedis G. Guerrero",
  },
  {
    answer: "08054",
    display: "Riva Palacio",
  },
  {
    answer: "08055",
    display: "Rosales",
  },
  {
    answer: "08056",
    display: "Valle del Rosario",
  },
  {
    answer: "08057",
    display: "San Francisco de Borja",
  },
  {
    answer: "08058",
    display: "San Francisco de Conchos",
  },
  {
    answer: "08059",
    display: "San Francisco del Oro",
  },
  {
    answer: "08060",
    display: "Santa Bárbara",
  },
  {
    answer: "08061",
    display: "Satevó",
  },
  {
    answer: "08062",
    display: "Saucillo",
  },
  {
    answer: "08063",
    display: "Temósachic",
  },
  {
    answer: "08064",
    display: "El Tule",
  },
  {
    answer: "08065",
    display: "Urique",
  },
  {
    answer: "08066",
    display: "Uruachi",
  },
  {
    answer: "08067",
    display: "Valle de Zaragoza",
  },
  {
    answer: "09002",
    display: "Azcapotzalco",
  },
  {
    answer: "09003",
    display: "Coyoacán",
  },
  {
    answer: "09004",
    display: "Cuajimalpa de Morelos",
  },
  {
    answer: "09005",
    display: "Gustavo A. Madero",
  },
  {
    answer: "09006",
    display: "Iztacalco",
  },
  {
    answer: "09007",
    display: "Iztapalapa",
  },
  {
    answer: "09008",
    display: "La Magdalena Contreras",
  },
  {
    answer: "09009",
    display: "Milpa Alta",
  },
  {
    answer: "09010",
    display: "Álvaro Obregón (CDMX)",
  },
  {
    answer: "09011",
    display: "Tláhuac",
  },
  {
    answer: "09012",
    display: "Tlalpan",
  },
  {
    answer: "09013",
    display: "Xochimilco",
  },
  {
    answer: "09014",
    display: "Benito Juárez (CDMX)",
  },
  {
    answer: "09015",
    display: "Cuauhtémoc (CDMX)",
  },
  {
    answer: "09016",
    display: "Miguel Hidalgo",
  },
  {
    answer: "09017",
    display: "Venustiano Carranza (CDMX)",
  },
  {
    answer: "10001",
    display: "Canatlán",
  },
  {
    answer: "10002",
    display: "Canelas",
  },
  {
    answer: "10003",
    display: "Coneto de Comonfort",
  },
  {
    answer: "10004",
    display: "Cuencamé",
  },
  {
    answer: "10005",
    display: "Durango",
  },
  {
    answer: "10006",
    display: "General Simón Bolívar",
  },
  {
    answer: "10007",
    display: "Gómez Palacio",
  },
  {
    answer: "10008",
    display: "Guadalupe Victoria (Dgo.)",
  },
  {
    answer: "10009",
    display: "Guanaceví",
  },
  {
    answer: "10010",
    display: "Hidalgo (Dgo.)",
  },
  {
    answer: "10011",
    display: "Indé",
  },
  {
    answer: "10012",
    display: "Lerdo",
  },
  {
    answer: "10013",
    display: "Mapimí",
  },
  {
    answer: "10014",
    display: "Mezquital",
  },
  {
    answer: "10015",
    display: "Nazas",
  },
  {
    answer: "10016",
    display: "Nombre de Dios",
  },
  {
    answer: "10017",
    display: "Ocampo (Dgo.)",
  },
  {
    answer: "10018",
    display: "El Oro (Dgo.)",
  },
  {
    answer: "10019",
    display: "Otáez",
  },
  {
    answer: "10020",
    display: "Pánuco de Coronado",
  },
  {
    answer: "10021",
    display: "Peñón Blanco",
  },
  {
    answer: "10022",
    display: "Poanas",
  },
  {
    answer: "10023",
    display: "Pueblo Nuevo (Dgo.)",
  },
  {
    answer: "10024",
    display: "Rodeo",
  },
  {
    answer: "10025",
    display: "San Bernardo",
  },
  {
    answer: "10026",
    display: "San Dimas",
  },
  {
    answer: "10027",
    display: "San Juan de Guadalupe",
  },
  {
    answer: "10028",
    display: "San Juan del Río (Dgo.)",
  },
  {
    answer: "10029",
    display: "San Luis del Cordero",
  },
  {
    answer: "10030",
    display: "San Pedro del Gallo",
  },
  {
    answer: "10031",
    display: "Santa Clara",
  },
  {
    answer: "10032",
    display: "Santiago Papasquiaro",
  },
  {
    answer: "10033",
    display: "Súchil",
  },
  {
    answer: "10034",
    display: "Tamazula",
  },
  {
    answer: "10035",
    display: "Tepehuanes",
  },
  {
    answer: "10036",
    display: "Tlahualilo",
  },
  {
    answer: "10037",
    display: "Topia",
  },
  {
    answer: "10038",
    display: "Vicente Guerrero (Dgo.)",
  },
  {
    answer: "10039",
    display: "Nuevo Ideal",
  },
  {
    answer: "11001",
    display: "Abasolo (Gto.)",
  },
  {
    answer: "11002",
    display: "Acámbaro",
  },
  {
    answer: "11003",
    display: "San Miguel de Allende",
  },
  {
    answer: "11004",
    display: "Apaseo el Alto",
  },
  {
    answer: "11005",
    display: "Apaseo el Grande",
  },
  {
    answer: "11006",
    display: "Atarjea",
  },
  {
    answer: "11007",
    display: "Celaya",
  },
  {
    answer: "11008",
    display: "Manuel Doblado",
  },
  {
    answer: "11009",
    display: "Comonfort",
  },
  {
    answer: "11010",
    display: "Coroneo",
  },
  {
    answer: "11011",
    display: "Cortazar",
  },
  {
    answer: "11012",
    display: "Cuerámaro",
  },
  {
    answer: "11013",
    display: "Doctor Mora",
  },
  {
    answer: "11014",
    display: "Dolores Hidalgo Cuna de la Independencia Nacional",
  },
  {
    answer: "11015",
    display: "Guanajuato",
  },
  {
    answer: "11016",
    display: "Huanímaro",
  },
  {
    answer: "11017",
    display: "Irapuato",
  },
  {
    answer: "11018",
    display: "Jaral del Progreso",
  },
  {
    answer: "11019",
    display: "Jerécuaro",
  },
  {
    answer: "11020",
    display: "León",
  },
  {
    answer: "11021",
    display: "Moroleón",
  },
  {
    answer: "11022",
    display: "Ocampo (Gto.)",
  },
  {
    answer: "11023",
    display: "Pénjamo",
  },
  {
    answer: "11024",
    display: "Pueblo Nuevo (Gto.)",
  },
  {
    answer: "11025",
    display: "Purísima del Rincón",
  },
  {
    answer: "11026",
    display: "Romita",
  },
  {
    answer: "11027",
    display: "Salamanca",
  },
  {
    answer: "11028",
    display: "Salvatierra",
  },
  {
    answer: "11029",
    display: "San Diego de la Unión",
  },
  {
    answer: "11030",
    display: "San Felipe (Gto.)",
  },
  {
    answer: "11031",
    display: "San Francisco del Rincón",
  },
  {
    answer: "11032",
    display: "San José de Iturbide",
  },
  {
    answer: "11033",
    display: "San Luis de la Paz",
  },
  {
    answer: "11034",
    display: "Santa Catarina (Gto.)",
  },
  {
    answer: "11035",
    display: "Santa Cruz de Juventino Rosas",
  },
  {
    answer: "11036",
    display: "Santiago Maravatío",
  },
  {
    answer: "11037",
    display: "Silao de la Victoria",
  },
  {
    answer: "11038",
    display: "Tarandacuao",
  },
  {
    answer: "11039",
    display: "Tarimoro",
  },
  {
    answer: "11040",
    display: "Tierra Blanca (Gto.)",
  },
  {
    answer: "11041",
    display: "Uriangato",
  },
  {
    answer: "11042",
    display: "Valle de Santiago",
  },
  {
    answer: "11043",
    display: "Victoria (Gto.)",
  },
  {
    answer: "11044",
    display: "Villagrán (Gto.)",
  },
  {
    answer: "11045",
    display: "Xichú",
  },
  {
    answer: "11046",
    display: "Yuriria",
  },
  {
    answer: "12001",
    display: "Acapulco de Juárez",
  },
  {
    answer: "12002",
    display: "Ahuacuotzingo",
  },
  {
    answer: "12003",
    display: "Ajuchitlán del Progreso",
  },
  {
    answer: "12004",
    display: "Alcozauca de Guerrero",
  },
  {
    answer: "12005",
    display: "Alpoyeca",
  },
  {
    answer: "12006",
    display: "Apaxtla de Castrejón",
  },
  {
    answer: "12007",
    display: "Arcelia",
  },
  {
    answer: "12008",
    display: "Atenango del Río",
  },
  {
    answer: "12009",
    display: "Atlamajalcingo del Monte",
  },
  {
    answer: "12010",
    display: "Atlixtac",
  },
  {
    answer: "12011",
    display: "Atoyac de Álvarez",
  },
  {
    answer: "12012",
    display: "Ayutla de los Libres",
  },
  {
    answer: "12013",
    display: "Azoyú",
  },
  {
    answer: "12014",
    display: "Benito Juárez (Gro.)",
  },
  {
    answer: "12015",
    display: "Buenavista de Cuéllar",
  },
  {
    answer: "12016",
    display: "Coahuayutla de José María Izazaga",
  },
  {
    answer: "12017",
    display: "Cocula (Gro.)",
  },
  {
    answer: "12018",
    display: "Copala",
  },
  {
    answer: "12019",
    display: "Copalillo",
  },
  {
    answer: "12020",
    display: "Copanatoyac",
  },
  {
    answer: "12021",
    display: "Coyuca de Benítez",
  },
  {
    answer: "12022",
    display: "Coyuca de Catalán",
  },
  {
    answer: "12023",
    display: "Cuajinicuilapa",
  },
  {
    answer: "12024",
    display: "Cualác",
  },
  {
    answer: "12025",
    display: "Cuautepec",
  },
  {
    answer: "12026",
    display: "Cuetzala del Progreso",
  },
  {
    answer: "12027",
    display: "Cutzamala de Pinzón",
  },
  {
    answer: "12028",
    display: "Chilapa de Álvarez",
  },
  {
    answer: "12029",
    display: "Chilpancingo de los Bravo",
  },
  {
    answer: "12030",
    display: "Florencio Villarreal",
  },
  {
    answer: "12031",
    display: "General Canuto A. Neri",
  },
  {
    answer: "12032",
    display: "General Heliodoro Castillo",
  },
  {
    answer: "12033",
    display: "Huamuxtitlán",
  },
  {
    answer: "12034",
    display: "Huitzuco de los Figueroa",
  },
  {
    answer: "12035",
    display: "Iguala de la Independencia",
  },
  {
    answer: "12036",
    display: "Igualapa",
  },
  {
    answer: "12037",
    display: "Ixcateopan de Cuauhtémoc",
  },
  {
    answer: "12038",
    display: "Zihuatanejo de Azueta",
  },
  {
    answer: "12039",
    display: "Juan R. Escudero",
  },
  {
    answer: "12040",
    display: "Leonardo Bravo",
  },
  {
    answer: "12041",
    display: "Malinaltepec",
  },
  {
    answer: "12042",
    display: "Mártir de Cuilapan",
  },
  {
    answer: "12043",
    display: "Metlatónoc",
  },
  {
    answer: "12044",
    display: "Mochitlán",
  },
  {
    answer: "12045",
    display: "Olinalá",
  },
  {
    answer: "12046",
    display: "Ometepec",
  },
  {
    answer: "12047",
    display: "Pedro Ascencio Alquisiras",
  },
  {
    answer: "12048",
    display: "Petatlán",
  },
  {
    answer: "12049",
    display: "Pilcaya",
  },
  {
    answer: "12050",
    display: "Pungarabato",
  },
  {
    answer: "12051",
    display: "Quechultenango",
  },
  {
    answer: "12052",
    display: "San Luis Acatlán",
  },
  {
    answer: "12053",
    display: "San Marcos (Gro.)",
  },
  {
    answer: "12054",
    display: "San Miguel Totolapan",
  },
  {
    answer: "12055",
    display: "Taxco de Alarcón",
  },
  {
    answer: "12056",
    display: "Tecoanapa",
  },
  {
    answer: "12057",
    display: "Técpan de Galeana",
  },
  {
    answer: "12058",
    display: "Teloloapan",
  },
  {
    answer: "12059",
    display: "Tepecoacuilco de Trujano",
  },
  {
    answer: "12060",
    display: "Tetipac",
  },
  {
    answer: "12061",
    display: "Tixtla de Guerrero",
  },
  {
    answer: "12062",
    display: "Tlacoachistlahuaca",
  },
  {
    answer: "12063",
    display: "Tlacoapa",
  },
  {
    answer: "12064",
    display: "Tlalchapa",
  },
  {
    answer: "12065",
    display: "Tlalixtaquilla de Maldonado",
  },
  {
    answer: "12066",
    display: "Tlapa de Comonfort",
  },
  {
    answer: "12067",
    display: "Tlapehuala",
  },
  {
    answer: "12068",
    display: "La Unión de Isidoro Montes de Oca",
  },
  {
    answer: "12069",
    display: "Xalpatláhuac",
  },
  {
    answer: "12070",
    display: "Xochihuehuetlán",
  },
  {
    answer: "12071",
    display: "Xochistlahuaca",
  },
  {
    answer: "12072",
    display: "Zapotitlán Tablas",
  },
  {
    answer: "12073",
    display: "Zirándaro",
  },
  {
    answer: "12074",
    display: "Zitlala",
  },
  {
    answer: "12075",
    display: "Eduardo Neri",
  },
  {
    answer: "12076",
    display: "Acatepec",
  },
  {
    answer: "12077",
    display: "Marquelia",
  },
  {
    answer: "12078",
    display: "Cochoapa el Grande",
  },
  {
    answer: "12079",
    display: "José Joaquín de Herrera",
  },
  {
    answer: "12080",
    display: "Juchitán",
  },
  {
    answer: "12081",
    display: "Iliatenco",
  },
  {
    answer: "12082",
    display: "Las Vigas",
  },
  {
    answer: "12083",
    display: "Ñuu Savi",
  },
  {
    answer: "12084",
    display: "Santa Cruz del Rincón",
  },
  {
    answer: "12085",
    display: "San Nicolás (Gro.)",
  },
  {
    answer: "13001",
    display: "Acatlán (Hgo.)",
  },
  {
    answer: "13002",
    display: "Acaxochitlán",
  },
  {
    answer: "13003",
    display: "Actopan (Hgo.)",
  },
  {
    answer: "13004",
    display: "Agua Blanca de Iturbide",
  },
  {
    answer: "13005",
    display: "Ajacuba",
  },
  {
    answer: "13006",
    display: "Alfajayucan",
  },
  {
    answer: "13007",
    display: "Almoloya",
  },
  {
    answer: "13008",
    display: "Apan",
  },
  {
    answer: "13009",
    display: "El Arenal (Hgo.)",
  },
  {
    answer: "13010",
    display: "Atitalaquia",
  },
  {
    answer: "13011",
    display: "Atlapexco",
  },
  {
    answer: "13012",
    display: "Atotonilco el Grande",
  },
  {
    answer: "13013",
    display: "Atotonilco de Tula",
  },
  {
    answer: "13014",
    display: "Calnali",
  },
  {
    answer: "13015",
    display: "Cardonal",
  },
  {
    answer: "13016",
    display: "Cuautepec de Hinojosa",
  },
  {
    answer: "13017",
    display: "Chapantongo",
  },
  {
    answer: "13018",
    display: "Chapulhuacán",
  },
  {
    answer: "13019",
    display: "Chilcuautla",
  },
  {
    answer: "13020",
    display: "Eloxochitlán (Hgo.)",
  },
  {
    answer: "13021",
    display: "Emiliano Zapata (Hgo.)",
  },
  {
    answer: "13022",
    display: "Epazoyucan",
  },
  {
    answer: "13023",
    display: "Francisco I. Madero (Hgo.)",
  },
  {
    answer: "13024",
    display: "Huasca de Ocampo",
  },
  {
    answer: "13025",
    display: "Huautla",
  },
  {
    answer: "13026",
    display: "Huazalingo",
  },
  {
    answer: "13027",
    display: "Huehuetla (Hgo.)",
  },
  {
    answer: "13028",
    display: "Huejutla de Reyes",
  },
  {
    answer: "13029",
    display: "Huichapan",
  },
  {
    answer: "13030",
    display: "Ixmiquilpan",
  },
  {
    answer: "13031",
    display: "Jacala de Ledezma",
  },
  {
    answer: "13032",
    display: "Jaltocán",
  },
  {
    answer: "13033",
    display: "Juárez Hidalgo",
  },
  {
    answer: "13034",
    display: "Lolotla",
  },
  {
    answer: "13035",
    display: "Metepec (Hgo.)",
  },
  {
    answer: "13036",
    display: "San Agustín Metzquititlán",
  },
  {
    answer: "13037",
    display: "Metztitlán",
  },
  {
    answer: "13038",
    display: "Mineral del Chico",
  },
  {
    answer: "13039",
    display: "Mineral del Monte",
  },
  {
    answer: "13040",
    display: "La Misión",
  },
  {
    answer: "13041",
    display: "Mixquiahuala de Juárez",
  },
  {
    answer: "13042",
    display: "Molango de Escamilla",
  },
  {
    answer: "13043",
    display: "Nicolás Flores",
  },
  {
    answer: "13044",
    display: "Nopala de Villagrán",
  },
  {
    answer: "13045",
    display: "Omitlán de Juárez",
  },
  {
    answer: "13046",
    display: "San Felipe Orizatlán",
  },
  {
    answer: "13047",
    display: "Pacula",
  },
  {
    answer: "13048",
    display: "Pachuca de Soto",
  },
  {
    answer: "13049",
    display: "Pisaflores",
  },
  {
    answer: "13050",
    display: "Progreso de Obregón",
  },
  {
    answer: "13051",
    display: "Mineral de la Reforma",
  },
  {
    answer: "13052",
    display: "San Agustín Tlaxiaca",
  },
  {
    answer: "13053",
    display: "San Bartolo Tutotepec",
  },
  {
    answer: "13054",
    display: "San Salvador",
  },
  {
    answer: "13055",
    display: "Santiago de Anaya",
  },
  {
    answer: "13056",
    display: "Santiago Tulantepec de Lugo Guerrero",
  },
  {
    answer: "13057",
    display: "Singuilucan",
  },
  {
    answer: "13058",
    display: "Tasquillo",
  },
  {
    answer: "13059",
    display: "Tecozautla",
  },
  {
    answer: "13060",
    display: "Tenango de Doria",
  },
  {
    answer: "13061",
    display: "Tepeapulco",
  },
  {
    answer: "13062",
    display: "Tepehuacán de Guerrero",
  },
  {
    answer: "13063",
    display: "Tepeji del Río de Ocampo",
  },
  {
    answer: "13064",
    display: "Tepetitlán",
  },
  {
    answer: "13065",
    display: "Tetepango",
  },
  {
    answer: "13066",
    display: "Villa de Tezontepec",
  },
  {
    answer: "13067",
    display: "Tezontepec de Aldama",
  },
  {
    answer: "13068",
    display: "Tianguistengo",
  },
  {
    answer: "13069",
    display: "Tizayuca",
  },
  {
    answer: "13070",
    display: "Tlahuelilpan",
  },
  {
    answer: "13071",
    display: "Tlahuiltepa",
  },
  {
    answer: "13072",
    display: "Tlanalapa",
  },
  {
    answer: "13073",
    display: "Tlanchinol",
  },
  {
    answer: "13074",
    display: "Tlaxcoapan",
  },
  {
    answer: "13075",
    display: "Tolcayuca",
  },
  {
    answer: "13076",
    display: "Tula de Allende",
  },
  {
    answer: "13077",
    display: "Tulancingo de Bravo",
  },
  {
    answer: "13078",
    display: "Xochiatipan",
  },
  {
    answer: "13079",
    display: "Xochicoatlán",
  },
  {
    answer: "13080",
    display: "Yahualica",
  },
  {
    answer: "13081",
    display: "Zacualtipán de Ángeles",
  },
  {
    answer: "13082",
    display: "Zapotlán de Juárez",
  },
  {
    answer: "13083",
    display: "Zempoala",
  },
  {
    answer: "13084",
    display: "Zimapán",
  },
  {
    answer: "14001",
    display: "Acatic",
  },
  {
    answer: "14002",
    display: "Acatlán de Juárez",
  },
  {
    answer: "14003",
    display: "Ahualulco de Mercado",
  },
  {
    answer: "14004",
    display: "Amacueca",
  },
  {
    answer: "14005",
    display: "Amatitán",
  },
  {
    answer: "14006",
    display: "Ameca",
  },
  {
    answer: "14007",
    display: "San Juanito de Escobedo",
  },
  {
    answer: "14008",
    display: "Arandas",
  },
  {
    answer: "14009",
    display: "El Arenal (Jal.)",
  },
  {
    answer: "14010",
    display: "Atemajac de Brizuela",
  },
  {
    answer: "14011",
    display: "Atengo",
  },
  {
    answer: "14012",
    display: "Atenguillo",
  },
  {
    answer: "14013",
    display: "Atotonilco el Alto",
  },
  {
    answer: "14014",
    display: "Atoyac (Jal.)",
  },
  {
    answer: "14015",
    display: "Autlán de Navarro",
  },
  {
    answer: "14016",
    display: "Ayotlán",
  },
  {
    answer: "14017",
    display: "Ayutla",
  },
  {
    answer: "14018",
    display: "La Barca",
  },
  {
    answer: "14019",
    display: "Bolaños",
  },
  {
    answer: "14020",
    display: "Cabo Corrientes",
  },
  {
    answer: "14021",
    display: "Casimiro Castillo",
  },
  {
    answer: "14022",
    display: "Cihuatlán",
  },
  {
    answer: "14023",
    display: "Zapotlán el Grande",
  },
  {
    answer: "14024",
    display: "Cocula (Jal.)",
  },
  {
    answer: "14025",
    display: "Colotlán",
  },
  {
    answer: "14026",
    display: "Concepción de Buenos Aires",
  },
  {
    answer: "14027",
    display: "Cuautitlán de García Barragán",
  },
  {
    answer: "14028",
    display: "Cuautla (Jal.)",
  },
  {
    answer: "14029",
    display: "Cuquío",
  },
  {
    answer: "14030",
    display: "Chapala",
  },
  {
    answer: "14031",
    display: "Chimaltitán",
  },
  {
    answer: "14032",
    display: "Chiquilistlán",
  },
  {
    answer: "14033",
    display: "Degollado",
  },
  {
    answer: "14034",
    display: "Ejutla",
  },
  {
    answer: "14035",
    display: "Encarnación de Díaz",
  },
  {
    answer: "14036",
    display: "Etzatlán",
  },
  {
    answer: "14037",
    display: "El Grullo",
  },
  {
    answer: "14038",
    display: "Guachinango",
  },
  {
    answer: "14039",
    display: "Guadalajara",
  },
  {
    answer: "14040",
    display: "Hostotipaquillo",
  },
  {
    answer: "14041",
    display: "Huejúcar",
  },
  {
    answer: "14042",
    display: "Huejuquilla el Alto",
  },
  {
    answer: "14043",
    display: "La Huerta",
  },
  {
    answer: "14044",
    display: "Ixtlahuacán de los Membrillos",
  },
  {
    answer: "14045",
    display: "Ixtlahuacán del Río",
  },
  {
    answer: "14046",
    display: "Jalostotitlán",
  },
  {
    answer: "14047",
    display: "Jamay",
  },
  {
    answer: "14048",
    display: "Jesús María (Jal.)",
  },
  {
    answer: "14049",
    display: "Jilotlán de los Dolores",
  },
  {
    answer: "14050",
    display: "Jocotepec",
  },
  {
    answer: "14051",
    display: "Juanacatlán",
  },
  {
    answer: "14052",
    display: "Juchitlán",
  },
  {
    answer: "14053",
    display: "Lagos de Moreno",
  },
  {
    answer: "14054",
    display: "El Limón",
  },
  {
    answer: "14055",
    display: "Magdalena (Jal.)",
  },
  {
    answer: "14056",
    display: "Santa María del Oro (Jal.)",
  },
  {
    answer: "14057",
    display: "La Manzanilla de la Paz",
  },
  {
    answer: "14058",
    display: "Mascota",
  },
  {
    answer: "14059",
    display: "Mazamitla",
  },
  {
    answer: "14060",
    display: "Mexticacán",
  },
  {
    answer: "14061",
    display: "Mezquitic",
  },
  {
    answer: "14062",
    display: "Mixtlán",
  },
  {
    answer: "14063",
    display: "Ocotlán",
  },
  {
    answer: "14064",
    display: "Ojuelos de Jalisco",
  },
  {
    answer: "14065",
    display: "Pihuamo",
  },
  {
    answer: "14066",
    display: "Poncitlán",
  },
  {
    answer: "14067",
    display: "Puerto Vallarta",
  },
  {
    answer: "14068",
    display: "Villa Purificación",
  },
  {
    answer: "14069",
    display: "Quitupan",
  },
  {
    answer: "14070",
    display: "El Salto",
  },
  {
    answer: "14071",
    display: "San Cristóbal de la Barranca",
  },
  {
    answer: "14072",
    display: "San Diego de Alejandría",
  },
  {
    answer: "14073",
    display: "San Juan de los Lagos",
  },
  {
    answer: "14074",
    display: "San Julián",
  },
  {
    answer: "14075",
    display: "San Marcos (Jal.)",
  },
  {
    answer: "14076",
    display: "San Martín de Bolaños",
  },
  {
    answer: "14077",
    display: "San Martín Hidalgo",
  },
  {
    answer: "14078",
    display: "San Miguel el Alto",
  },
  {
    answer: "14079",
    display: "Gómez Farías (Jal.)",
  },
  {
    answer: "14080",
    display: "San Sebastián del Oeste",
  },
  {
    answer: "14081",
    display: "Santa María de los Ángeles",
  },
  {
    answer: "14082",
    display: "Sayula",
  },
  {
    answer: "14083",
    display: "Tala",
  },
  {
    answer: "14084",
    display: "Talpa de Allende",
  },
  {
    answer: "14085",
    display: "Tamazula de Gordiano",
  },
  {
    answer: "14086",
    display: "Tapalpa",
  },
  {
    answer: "14087",
    display: "Tecalitlán",
  },
  {
    answer: "14088",
    display: "Tecolotlán",
  },
  {
    answer: "14089",
    display: "Techaluta de Montenegro",
  },
  {
    answer: "14090",
    display: "Tenamaxtlán",
  },
  {
    answer: "14091",
    display: "Teocaltiche",
  },
  {
    answer: "14092",
    display: "Teocuitatlán de Corona",
  },
  {
    answer: "14093",
    display: "Tepatitlán de Morelos",
  },
  {
    answer: "14094",
    display: "Tequila (Jal.)",
  },
  {
    answer: "14095",
    display: "Teuchitlán",
  },
  {
    answer: "14096",
    display: "Tizapán el Alto",
  },
  {
    answer: "14097",
    display: "Tlajomulco de Zúñiga",
  },
  {
    answer: "14098",
    display: "San Pedro Tlaquepaque",
  },
  {
    answer: "14099",
    display: "Tolimán (Jal.)",
  },
  {
    answer: "14100",
    display: "Tomatlán (Jal.)",
  },
  {
    answer: "14101",
    display: "Tonalá (Jal.)",
  },
  {
    answer: "14102",
    display: "Tonaya",
  },
  {
    answer: "14103",
    display: "Tonila",
  },
  {
    answer: "14104",
    display: "Totatiche",
  },
  {
    answer: "14105",
    display: "Tototlán",
  },
  {
    answer: "14106",
    display: "Tuxcacuesco",
  },
  {
    answer: "14107",
    display: "Tuxcueca",
  },
  {
    answer: "14108",
    display: "Tuxpan (Jal.)",
  },
  {
    answer: "14109",
    display: "Unión de San Antonio",
  },
  {
    answer: "14110",
    display: "Unión de Tula",
  },
  {
    answer: "14111",
    display: "Valle de Guadalupe",
  },
  {
    answer: "14112",
    display: "Valle de Juárez",
  },
  {
    answer: "14113",
    display: "San Gabriel",
  },
  {
    answer: "14114",
    display: "Villa Corona",
  },
  {
    answer: "14115",
    display: "Villa Guerrero (Jal.)",
  },
  {
    answer: "14116",
    display: "Villa Hidalgo (Jal.)",
  },
  {
    answer: "14117",
    display: "Cañadas de Obregón",
  },
  {
    answer: "14118",
    display: "Yahualica de González Gallo",
  },
  {
    answer: "14119",
    display: "Zacoalco de Torres",
  },
  {
    answer: "14120",
    display: "Zapopan",
  },
  {
    answer: "14121",
    display: "Zapotiltic",
  },
  {
    answer: "14122",
    display: "Zapotitlán de Vadillo",
  },
  {
    answer: "14123",
    display: "Zapotlán del Rey",
  },
  {
    answer: "14124",
    display: "Zapotlanejo",
  },
  {
    answer: "14125",
    display: "San Ignacio Cerro Gordo",
  },
  {
    answer: "15001",
    display: "Acambay de Ruíz Castañeda",
  },
  {
    answer: "15002",
    display: "Acolman",
  },
  {
    answer: "15003",
    display: "Aculco",
  },
  {
    answer: "15004",
    display: "Almoloya de Alquisiras",
  },
  {
    answer: "15005",
    display: "Almoloya de Juárez",
  },
  {
    answer: "15006",
    display: "Almoloya del Río",
  },
  {
    answer: "15007",
    display: "Amanalco",
  },
  {
    answer: "15008",
    display: "Amatepec",
  },
  {
    answer: "15009",
    display: "Amecameca",
  },
  {
    answer: "15010",
    display: "Apaxco",
  },
  {
    answer: "15011",
    display: "Atenco",
  },
  {
    answer: "15012",
    display: "Atizapán",
  },
  {
    answer: "15013",
    display: "Atizapán de Zaragoza",
  },
  {
    answer: "15014",
    display: "Atlacomulco",
  },
  {
    answer: "15015",
    display: "Atlautla",
  },
  {
    answer: "15016",
    display: "Axapusco",
  },
  {
    answer: "15017",
    display: "Ayapango",
  },
  {
    answer: "15018",
    display: "Calimaya",
  },
  {
    answer: "15019",
    display: "Capulhuac",
  },
  {
    answer: "15020",
    display: "Coacalco de Berriozábal",
  },
  {
    answer: "15021",
    display: "Coatepec Harinas",
  },
  {
    answer: "15022",
    display: "Cocotitlán",
  },
  {
    answer: "15023",
    display: "Coyotepec (Méx.)",
  },
  {
    answer: "15024",
    display: "Cuautitlán",
  },
  {
    answer: "15025",
    display: "Chalco",
  },
  {
    answer: "15026",
    display: "Chapa de Mota",
  },
  {
    answer: "15027",
    display: "Chapultepec",
  },
  {
    answer: "15028",
    display: "Chiautla (Méx.)",
  },
  {
    answer: "15029",
    display: "Chicoloapan",
  },
  {
    answer: "15030",
    display: "Chiconcuac",
  },
  {
    answer: "15031",
    display: "Chimalhuacán",
  },
  {
    answer: "15032",
    display: "Donato Guerra",
  },
  {
    answer: "15033",
    display: "Ecatepec de Morelos",
  },
  {
    answer: "15034",
    display: "Ecatzingo",
  },
  {
    answer: "15035",
    display: "Huehuetoca",
  },
  {
    answer: "15036",
    display: "Hueypoxtla",
  },
  {
    answer: "15037",
    display: "Huixquilucan",
  },
  {
    answer: "15038",
    display: "Isidro Fabela",
  },
  {
    answer: "15039",
    display: "Ixtapaluca",
  },
  {
    answer: "15040",
    display: "Ixtapan de la Sal",
  },
  {
    answer: "15041",
    display: "Ixtapan del Oro",
  },
  {
    answer: "15042",
    display: "Ixtlahuaca",
  },
  {
    answer: "15043",
    display: "Xalatlaco",
  },
  {
    answer: "15044",
    display: "Jaltenco",
  },
  {
    answer: "15045",
    display: "Jilotepec (Méx.)",
  },
  {
    answer: "15046",
    display: "Jilotzingo",
  },
  {
    answer: "15047",
    display: "Jiquipilco",
  },
  {
    answer: "15048",
    display: "Jocotitlán",
  },
  {
    answer: "15049",
    display: "Joquicingo",
  },
  {
    answer: "15050",
    display: "Juchitepec",
  },
  {
    answer: "15051",
    display: "Lerma",
  },
  {
    answer: "15052",
    display: "Malinalco",
  },
  {
    answer: "15053",
    display: "Melchor Ocampo (Méx.)",
  },
  {
    answer: "15054",
    display: "Metepec (Méx.)",
  },
  {
    answer: "15055",
    display: "Mexicaltzingo",
  },
  {
    answer: "15056",
    display: "Morelos (Méx.)",
  },
  {
    answer: "15057",
    display: "Naucalpan de Juárez",
  },
  {
    answer: "15058",
    display: "Nezahualcóyotl",
  },
  {
    answer: "15059",
    display: "Nextlalpan",
  },
  {
    answer: "15060",
    display: "Nicolás Romero",
  },
  {
    answer: "15061",
    display: "Nopaltepec",
  },
  {
    answer: "15062",
    display: "Ocoyoacac",
  },
  {
    answer: "15063",
    display: "Ocuilan",
  },
  {
    answer: "15064",
    display: "El Oro (Méx.)",
  },
  {
    answer: "15065",
    display: "Otumba",
  },
  {
    answer: "15066",
    display: "Otzoloapan",
  },
  {
    answer: "15067",
    display: "Otzolotepec",
  },
  {
    answer: "15068",
    display: "Ozumba",
  },
  {
    answer: "15069",
    display: "Papalotla",
  },
  {
    answer: "15070",
    display: "La Paz (Méx.)",
  },
  {
    answer: "15071",
    display: "Polotitlán",
  },
  {
    answer: "15072",
    display: "Rayón (Méx.)",
  },
  {
    answer: "15073",
    display: "San Antonio la Isla",
  },
  {
    answer: "15074",
    display: "San Felipe del Progreso",
  },
  {
    answer: "15075",
    display: "San Martín de las Pirámides",
  },
  {
    answer: "15076",
    display: "San Mateo Atenco",
  },
  {
    answer: "15077",
    display: "San Simón de Guerrero",
  },
  {
    answer: "15078",
    display: "Santo Tomás",
  },
  {
    answer: "15079",
    display: "Soyaniquilpan de Juárez",
  },
  {
    answer: "15080",
    display: "Sultepec",
  },
  {
    answer: "15081",
    display: "Tecámac",
  },
  {
    answer: "15082",
    display: "Tejupilco",
  },
  {
    answer: "15083",
    display: "Temamatla",
  },
  {
    answer: "15084",
    display: "Temascalapa",
  },
  {
    answer: "15085",
    display: "Temascalcingo",
  },
  {
    answer: "15086",
    display: "Temascaltepec",
  },
  {
    answer: "15087",
    display: "Temoaya",
  },
  {
    answer: "15088",
    display: "Tenancingo (Méx.)",
  },
  {
    answer: "15089",
    display: "Tenango del Aire",
  },
  {
    answer: "15090",
    display: "Tenango del Valle",
  },
  {
    answer: "15091",
    display: "Teoloyucan",
  },
  {
    answer: "15092",
    display: "Teotihuacán",
  },
  {
    answer: "15093",
    display: "Tepetlaoxtoc",
  },
  {
    answer: "15094",
    display: "Tepetlixpa",
  },
  {
    answer: "15095",
    display: "Tepotzotlán",
  },
  {
    answer: "15096",
    display: "Tequixquiac",
  },
  {
    answer: "15097",
    display: "Texcaltitlán",
  },
  {
    answer: "15098",
    display: "Texcalyacac",
  },
  {
    answer: "15099",
    display: "Texcoco",
  },
  {
    answer: "15100",
    display: "Tezoyuca",
  },
  {
    answer: "15101",
    display: "Tianguistenco",
  },
  {
    answer: "15102",
    display: "Timilpan",
  },
  {
    answer: "15103",
    display: "Tlalmanalco",
  },
  {
    answer: "15104",
    display: "Tlalnepantla de Baz",
  },
  {
    answer: "15105",
    display: "Tlatlaya",
  },
  {
    answer: "15106",
    display: "Toluca",
  },
  {
    answer: "15107",
    display: "Tonatico",
  },
  {
    answer: "15108",
    display: "Tultepec",
  },
  {
    answer: "15109",
    display: "Tultitlán",
  },
  {
    answer: "15110",
    display: "Valle de Bravo",
  },
  {
    answer: "15111",
    display: "Villa de Allende",
  },
  {
    answer: "15112",
    display: "Villa del Carbón",
  },
  {
    answer: "15113",
    display: "Villa Guerrero (Méx.)",
  },
  {
    answer: "15114",
    display: "Villa Victoria",
  },
  {
    answer: "15115",
    display: "Xonacatlán",
  },
  {
    answer: "15116",
    display: "Zacazonapan",
  },
  {
    answer: "15117",
    display: "Zacualpan (Méx.)",
  },
  {
    answer: "15118",
    display: "Zinacantepec",
  },
  {
    answer: "15119",
    display: "Zumpahuacán",
  },
  {
    answer: "15120",
    display: "Zumpango",
  },
  {
    answer: "15121",
    display: "Cuautitlán Izcalli",
  },
  {
    answer: "15122",
    display: "Valle de Chalco Solidaridad",
  },
  {
    answer: "15123",
    display: "Luvianos",
  },
  {
    answer: "15124",
    display: "San José del Rincón",
  },
  {
    answer: "15125",
    display: "Tonanitla",
  },
  {
    answer: "16001",
    display: "Acuitzio",
  },
  {
    answer: "16002",
    display: "Aguililla",
  },
  {
    answer: "16003",
    display: "Álvaro Obregón (Mich.)",
  },
  {
    answer: "16004",
    display: "Angamacutiro",
  },
  {
    answer: "16005",
    display: "Angangueo",
  },
  {
    answer: "16006",
    display: "Apatzingán",
  },
  {
    answer: "16007",
    display: "Aporo",
  },
  {
    answer: "16008",
    display: "Aquila (Mich.)",
  },
  {
    answer: "16009",
    display: "Ario",
  },
  {
    answer: "16010",
    display: "Arteaga (Mich.)",
  },
  {
    answer: "16011",
    display: "Briseñas",
  },
  {
    answer: "16012",
    display: "Buenavista",
  },
  {
    answer: "16013",
    display: "Carácuaro",
  },
  {
    answer: "16014",
    display: "Coahuayana",
  },
  {
    answer: "16015",
    display: "Coalcomán de Vázquez Pallares",
  },
  {
    answer: "16016",
    display: "Coeneo",
  },
  {
    answer: "16017",
    display: "Contepec",
  },
  {
    answer: "16018",
    display: "Copándaro",
  },
  {
    answer: "16019",
    display: "Cotija",
  },
  {
    answer: "16020",
    display: "Cuitzeo",
  },
  {
    answer: "16021",
    display: "Charapan",
  },
  {
    answer: "16022",
    display: "Charo",
  },
  {
    answer: "16023",
    display: "Chavinda",
  },
  {
    answer: "16024",
    display: "Cherán",
  },
  {
    answer: "16025",
    display: "Chilchota",
  },
  {
    answer: "16026",
    display: "Chinicuila",
  },
  {
    answer: "16027",
    display: "Chucándiro",
  },
  {
    answer: "16028",
    display: "Churintzio",
  },
  {
    answer: "16029",
    display: "Churumuco",
  },
  {
    answer: "16030",
    display: "Ecuandureo",
  },
  {
    answer: "16031",
    display: "Epitacio Huerta",
  },
  {
    answer: "16032",
    display: "Erongarícuaro",
  },
  {
    answer: "16033",
    display: "Gabriel Zamora",
  },
  {
    answer: "16034",
    display: "Hidalgo (Mich.)",
  },
  {
    answer: "16035",
    display: "La Huacana",
  },
  {
    answer: "16036",
    display: "Huandacareo",
  },
  {
    answer: "16037",
    display: "Huaniqueo",
  },
  {
    answer: "16038",
    display: "Huetamo",
  },
  {
    answer: "16039",
    display: "Huiramba",
  },
  {
    answer: "16040",
    display: "Indaparapeo",
  },
  {
    answer: "16041",
    display: "Irimbo",
  },
  {
    answer: "16042",
    display: "Ixtlán",
  },
  {
    answer: "16043",
    display: "Jacona",
  },
  {
    answer: "16044",
    display: "Jiménez (Mich.)",
  },
  {
    answer: "16045",
    display: "Jiquilpan",
  },
  {
    answer: "16046",
    display: "Juárez (Mich.)",
  },
  {
    answer: "16047",
    display: "Jungapeo",
  },
  {
    answer: "16048",
    display: "Lagunillas (Mich.)",
  },
  {
    answer: "16049",
    display: "Madero",
  },
  {
    answer: "16050",
    display: "Maravatío",
  },
  {
    answer: "16051",
    display: "Marcos Castellanos",
  },
  {
    answer: "16052",
    display: "Lázaro Cárdenas (Mich.)",
  },
  {
    answer: "16053",
    display: "Morelia",
  },
  {
    answer: "16054",
    display: "Morelos (Mich.)",
  },
  {
    answer: "16055",
    display: "Múgica",
  },
  {
    answer: "16056",
    display: "Nahuatzen",
  },
  {
    answer: "16057",
    display: "Nocupétaro",
  },
  {
    answer: "16058",
    display: "Nuevo Parangaricutiro",
  },
  {
    answer: "16059",
    display: "Nuevo Urecho",
  },
  {
    answer: "16060",
    display: "Numarán",
  },
  {
    answer: "16061",
    display: "Ocampo (Mich.)",
  },
  {
    answer: "16062",
    display: "Pajacuarán",
  },
  {
    answer: "16063",
    display: "Panindícuaro",
  },
  {
    answer: "16064",
    display: "Parácuaro",
  },
  {
    answer: "16065",
    display: "Paracho",
  },
  {
    answer: "16066",
    display: "Pátzcuaro",
  },
  {
    answer: "16067",
    display: "Penjamillo",
  },
  {
    answer: "16068",
    display: "Peribán",
  },
  {
    answer: "16069",
    display: "La Piedad",
  },
  {
    answer: "16070",
    display: "Purépero",
  },
  {
    answer: "16071",
    display: "Puruándiro",
  },
  {
    answer: "16072",
    display: "Queréndaro",
  },
  {
    answer: "16073",
    display: "Quiroga",
  },
  {
    answer: "16074",
    display: "Cojumatlán de Régules",
  },
  {
    answer: "16075",
    display: "Los Reyes (Mich.)",
  },
  {
    answer: "16076",
    display: "Sahuayo",
  },
  {
    answer: "16077",
    display: "San Lucas (Mich.)",
  },
  {
    answer: "16078",
    display: "Santa Ana Maya",
  },
  {
    answer: "16079",
    display: "Salvador Escalante",
  },
  {
    answer: "16080",
    display: "Senguio",
  },
  {
    answer: "16081",
    display: "Susupuato",
  },
  {
    answer: "16082",
    display: "Tacámbaro",
  },
  {
    answer: "16083",
    display: "Tancítaro",
  },
  {
    answer: "16084",
    display: "Tangamandapio",
  },
  {
    answer: "16085",
    display: "Tangancícuaro",
  },
  {
    answer: "16086",
    display: "Tanhuato",
  },
  {
    answer: "16087",
    display: "Taretan",
  },
  {
    answer: "16088",
    display: "Tarímbaro",
  },
  {
    answer: "16089",
    display: "Tepalcatepec",
  },
  {
    answer: "16090",
    display: "Tingambato",
  },
  {
    answer: "16091",
    display: "Tingüindín",
  },
  {
    answer: "16092",
    display: "Tiquicheo de Nicolás Romero",
  },
  {
    answer: "16093",
    display: "Tlalpujahua",
  },
  {
    answer: "16094",
    display: "Tlazazalca",
  },
  {
    answer: "16095",
    display: "Tocumbo",
  },
  {
    answer: "16096",
    display: "Tumbiscatío",
  },
  {
    answer: "16097",
    display: "Turicato",
  },
  {
    answer: "16098",
    display: "Tuxpan (Mich.)",
  },
  {
    answer: "16099",
    display: "Tuzantla",
  },
  {
    answer: "16100",
    display: "Tzintzuntzan",
  },
  {
    answer: "16101",
    display: "Tzitzio",
  },
  {
    answer: "16102",
    display: "Uruapan",
  },
  {
    answer: "16103",
    display: "Venustiano Carranza (Mich.)",
  },
  {
    answer: "16104",
    display: "Villamar",
  },
  {
    answer: "16105",
    display: "Vista Hermosa",
  },
  {
    answer: "16106",
    display: "Yurécuaro",
  },
  {
    answer: "16107",
    display: "Zacapu",
  },
  {
    answer: "16108",
    display: "Zamora",
  },
  {
    answer: "16109",
    display: "Zináparo",
  },
  {
    answer: "16110",
    display: "Zinapécuaro",
  },
  {
    answer: "16111",
    display: "Ziracuaretiro",
  },
  {
    answer: "16112",
    display: "Zitácuaro",
  },
  {
    answer: "16113",
    display: "José Sixto Verduzco",
  },
  {
    answer: "17001",
    display: "Amacuzac",
  },
  {
    answer: "17002",
    display: "Atlatlahucan",
  },
  {
    answer: "17003",
    display: "Axochiapan",
  },
  {
    answer: "17004",
    display: "Ayala",
  },
  {
    answer: "17005",
    display: "Coatlán del Río",
  },
  {
    answer: "17006",
    display: "Cuautla (Mor.)",
  },
  {
    answer: "17007",
    display: "Cuernavaca",
  },
  {
    answer: "17008",
    display: "Emiliano Zapata (Mor.)",
  },
  {
    answer: "17009",
    display: "Huitzilac",
  },
  {
    answer: "17010",
    display: "Jantetelco",
  },
  {
    answer: "17011",
    display: "Jiutepec",
  },
  {
    answer: "17012",
    display: "Jojutla",
  },
  {
    answer: "17013",
    display: "Jonacatepec de Leandro Valle",
  },
  {
    answer: "17014",
    display: "Mazatepec",
  },
  {
    answer: "17015",
    display: "Miacatlán",
  },
  {
    answer: "17016",
    display: "Ocuituco",
  },
  {
    answer: "17017",
    display: "Puente de Ixtla",
  },
  {
    answer: "17018",
    display: "Temixco",
  },
  {
    answer: "17019",
    display: "Tepalcingo",
  },
  {
    answer: "17020",
    display: "Tepoztlán",
  },
  {
    answer: "17021",
    display: "Tetecala",
  },
  {
    answer: "17022",
    display: "Tetela del Volcán",
  },
  {
    answer: "17023",
    display: "Tlalnepantla",
  },
  {
    answer: "17024",
    display: "Tlaltizapán de Zapata",
  },
  {
    answer: "17025",
    display: "Tlaquiltenango",
  },
  {
    answer: "17026",
    display: "Tlayacapan",
  },
  {
    answer: "17027",
    display: "Totolapan",
  },
  {
    answer: "17028",
    display: "Xochitepec",
  },
  {
    answer: "17029",
    display: "Yautepec",
  },
  {
    answer: "17030",
    display: "Yecapixtla",
  },
  {
    answer: "17031",
    display: "Zacatepec",
  },
  {
    answer: "17032",
    display: "Zacualpan de Amilpas",
  },
  {
    answer: "17033",
    display: "Temoac",
  },
  {
    answer: "17034",
    display: "Coatetelco",
  },
  {
    answer: "17035",
    display: "Xoxocotla (Mor.)",
  },
  {
    answer: "17036",
    display: "Hueyapan (Mor.)",
  },
  {
    answer: "18001",
    display: "Acaponeta",
  },
  {
    answer: "18002",
    display: "Ahuacatlán (Nay.)",
  },
  {
    answer: "18003",
    display: "Amatlán de Cañas",
  },
  {
    answer: "18004",
    display: "Compostela",
  },
  {
    answer: "18005",
    display: "Huajicori",
  },
  {
    answer: "18006",
    display: "Ixtlán del Río",
  },
  {
    answer: "18007",
    display: "Jala",
  },
  {
    answer: "18008",
    display: "Xalisco",
  },
  {
    answer: "18009",
    display: "Del Nayar",
  },
  {
    answer: "18010",
    display: "Rosamorada",
  },
  {
    answer: "18011",
    display: "Ruíz",
  },
  {
    answer: "18012",
    display: "San Blas",
  },
  {
    answer: "18013",
    display: "San Pedro Lagunillas",
  },
  {
    answer: "18014",
    display: "Santa María del Oro (Nay.)",
  },
  {
    answer: "18015",
    display: "Santiago Ixcuintla",
  },
  {
    answer: "18016",
    display: "Tecuala",
  },
  {
    answer: "18017",
    display: "Tepic",
  },
  {
    answer: "18018",
    display: "Tuxpan (Nay.)",
  },
  {
    answer: "18019",
    display: "La Yesca",
  },
  {
    answer: "18020",
    display: "Bahía de Banderas",
  },
  {
    answer: "19001",
    display: "Abasolo (N.L.)",
  },
  {
    answer: "19002",
    display: "Agualeguas",
  },
  {
    answer: "19003",
    display: "Los Aldamas",
  },
  {
    answer: "19004",
    display: "Allende (N.L.)",
  },
  {
    answer: "19005",
    display: "Anáhuac",
  },
  {
    answer: "19006",
    display: "Apodaca",
  },
  {
    answer: "19007",
    display: "Aramberri",
  },
  {
    answer: "19008",
    display: "Bustamante (N.L.)",
  },
  {
    answer: "19009",
    display: "Cadereyta Jiménez",
  },
  {
    answer: "19010",
    display: "El Carmen",
  },
  {
    answer: "19011",
    display: "Cerralvo",
  },
  {
    answer: "19012",
    display: "Ciénega de Flores",
  },
  {
    answer: "19013",
    display: "China",
  },
  {
    answer: "19014",
    display: "Doctor Arroyo",
  },
  {
    answer: "19015",
    display: "Doctor Coss",
  },
  {
    answer: "19016",
    display: "Doctor González",
  },
  {
    answer: "19017",
    display: "Galeana (N.L.)",
  },
  {
    answer: "19018",
    display: "García",
  },
  {
    answer: "19019",
    display: "San Pedro Garza García",
  },
  {
    answer: "19020",
    display: "General Bravo",
  },
  {
    answer: "19021",
    display: "General Escobedo",
  },
  {
    answer: "19022",
    display: "General Terán",
  },
  {
    answer: "19023",
    display: "General Treviño",
  },
  {
    answer: "19024",
    display: "General Zaragoza",
  },
  {
    answer: "19025",
    display: "General Zuazua",
  },
  {
    answer: "19026",
    display: "Guadalupe (N.L.)",
  },
  {
    answer: "19027",
    display: "Los Herreras",
  },
  {
    answer: "19028",
    display: "Higueras",
  },
  {
    answer: "19029",
    display: "Hualahuises",
  },
  {
    answer: "19030",
    display: "Iturbide",
  },
  {
    answer: "19031",
    display: "Juárez (N.L.)",
  },
  {
    answer: "19032",
    display: "Lampazos de Naranjo",
  },
  {
    answer: "19033",
    display: "Linares",
  },
  {
    answer: "19034",
    display: "Marín",
  },
  {
    answer: "19035",
    display: "Melchor Ocampo (N.L.)",
  },
  {
    answer: "19036",
    display: "Mier y Noriega",
  },
  {
    answer: "19037",
    display: "Mina",
  },
  {
    answer: "19038",
    display: "Montemorelos",
  },
  {
    answer: "19039",
    display: "Monterrey",
  },
  {
    answer: "19040",
    display: "Parás",
  },
  {
    answer: "19041",
    display: "Pesquería",
  },
  {
    answer: "19042",
    display: "Los Ramones",
  },
  {
    answer: "19043",
    display: "Rayones",
  },
  {
    answer: "19044",
    display: "Sabinas Hidalgo",
  },
  {
    answer: "19045",
    display: "Salinas Victoria",
  },
  {
    answer: "19046",
    display: "San Nicolás de los Garza",
  },
  {
    answer: "19047",
    display: "Hidalgo (N.L.)",
  },
  {
    answer: "19048",
    display: "Santa Catarina (N.L.)",
  },
  {
    answer: "19049",
    display: "Santiago",
  },
  {
    answer: "19050",
    display: "Vallecillo",
  },
  {
    answer: "19051",
    display: "Villaldama",
  },
  {
    answer: "20001",
    display: "Abejones",
  },
  {
    answer: "20002",
    display: "Acatlán de Pérez Figueroa",
  },
  {
    answer: "20003",
    display: "Asunción Cacalotepec",
  },
  {
    answer: "20004",
    display: "Asunción Cuyotepeji",
  },
  {
    answer: "20005",
    display: "Asunción Ixtaltepec",
  },
  {
    answer: "20006",
    display: "Asunción Nochixtlán",
  },
  {
    answer: "20007",
    display: "Asunción Ocotlán",
  },
  {
    answer: "20008",
    display: "Asunción Tlacolulita",
  },
  {
    answer: "20009",
    display: "Ayotzintepec",
  },
  {
    answer: "20010",
    display: "El Barrio de la Soledad",
  },
  {
    answer: "20011",
    display: "Calihualá",
  },
  {
    answer: "20012",
    display: "Candelaria Loxicha",
  },
  {
    answer: "20013",
    display: "Ciénega de Zimatlán",
  },
  {
    answer: "20014",
    display: "Ciudad Ixtepec",
  },
  {
    answer: "20015",
    display: "Coatecas Altas",
  },
  {
    answer: "20016",
    display: "Coicoyán de las Flores",
  },
  {
    answer: "20017",
    display: "La Compañía",
  },
  {
    answer: "20018",
    display: "Concepción Buenavista",
  },
  {
    answer: "20019",
    display: "Concepción Pápalo",
  },
  {
    answer: "20020",
    display: "Constancia del Rosario",
  },
  {
    answer: "20021",
    display: "Cosolapa",
  },
  {
    answer: "20022",
    display: "Cosoltepec",
  },
  {
    answer: "20023",
    display: "Cuilápam de Guerrero",
  },
  {
    answer: "20024",
    display: "Cuyamecalco Villa de Zaragoza",
  },
  {
    answer: "20025",
    display: "Chahuites",
  },
  {
    answer: "20026",
    display: "Chalcatongo de Hidalgo",
  },
  {
    answer: "20027",
    display: "Chiquihuitlán de Benito Juárez",
  },
  {
    answer: "20028",
    display: "Heroica Ciudad de Ejutla de Crespo",
  },
  {
    answer: "20029",
    display: "Eloxochitlán de Flores Magón",
  },
  {
    answer: "20030",
    display: "El Espinal",
  },
  {
    answer: "20031",
    display: "Tamazulápam del Espíritu Santo",
  },
  {
    answer: "20032",
    display: "Fresnillo de Trujano",
  },
  {
    answer: "20033",
    display: "Guadalupe Etla",
  },
  {
    answer: "20034",
    display: "Guadalupe de Ramírez",
  },
  {
    answer: "20035",
    display: "Guelatao de Juárez",
  },
  {
    answer: "20036",
    display: "Guevea de Humboldt",
  },
  {
    answer: "20037",
    display: "Mesones Hidalgo",
  },
  {
    answer: "20038",
    display: "Villa Hidalgo Yalálag",
  },
  {
    answer: "20039",
    display: "Heroica Ciudad de Huajuapan de León",
  },
  {
    answer: "20040",
    display: "Huautepec",
  },
  {
    answer: "20041",
    display: "Huautla de Jiménez",
  },
  {
    answer: "20042",
    display: "Ixtlán de Juárez",
  },
  {
    answer: "20043",
    display: "Heroica Ciudad de Juchitán de Zaragoza",
  },
  {
    answer: "20044",
    display: "Loma Bonita",
  },
  {
    answer: "20045",
    display: "Magdalena Apasco",
  },
  {
    answer: "20046",
    display: "Magdalena Jaltepec",
  },
  {
    answer: "20047",
    display: "Santa Magdalena Jicotlán",
  },
  {
    answer: "20048",
    display: "Magdalena Mixtepec",
  },
  {
    answer: "20049",
    display: "Magdalena Ocotlán",
  },
  {
    answer: "20050",
    display: "Magdalena Peñasco",
  },
  {
    answer: "20051",
    display: "Magdalena Teitipac",
  },
  {
    answer: "20052",
    display: "Magdalena Tequisistlán",
  },
  {
    answer: "20053",
    display: "Magdalena Tlacotepec",
  },
  {
    answer: "20054",
    display: "Magdalena Zahuatlán",
  },
  {
    answer: "20055",
    display: "Mariscala de Juárez",
  },
  {
    answer: "20056",
    display: "Mártires de Tacubaya",
  },
  {
    answer: "20057",
    display: "Matías Romero Avendaño",
  },
  {
    answer: "20058",
    display: "Mazatlán Villa de Flores",
  },
  {
    answer: "20059",
    display: "Miahuatlán de Porfirio Díaz",
  },
  {
    answer: "20060",
    display: "Mixistlán de la Reforma",
  },
  {
    answer: "20061",
    display: "Monjas",
  },
  {
    answer: "20062",
    display: "Natividad",
  },
  {
    answer: "20063",
    display: "Nazareno Etla",
  },
  {
    answer: "20064",
    display: "Nejapa de Madero",
  },
  {
    answer: "20065",
    display: "Ixpantepec Nieves",
  },
  {
    answer: "20066",
    display: "Santiago Niltepec",
  },
  {
    answer: "20067",
    display: "Oaxaca de Juárez",
  },
  {
    answer: "20068",
    display: "Ocotlán de Morelos",
  },
  {
    answer: "20069",
    display: "La Pe",
  },
  {
    answer: "20070",
    display: "Pinotepa de Don Luis",
  },
  {
    answer: "20071",
    display: "Pluma Hidalgo",
  },
  {
    answer: "20072",
    display: "San José del Progreso",
  },
  {
    answer: "20073",
    display: "Putla Villa de Guerrero",
  },
  {
    answer: "20074",
    display: "Santa Catarina Quioquitani",
  },
  {
    answer: "20075",
    display: "Reforma de Pineda",
  },
  {
    answer: "20076",
    display: "La Reforma",
  },
  {
    answer: "20077",
    display: "Reyes Etla",
  },
  {
    answer: "20078",
    display: "Rojas de Cuauhtémoc",
  },
  {
    answer: "20079",
    display: "Salina Cruz",
  },
  {
    answer: "20080",
    display: "San Agustín Amatengo",
  },
  {
    answer: "20081",
    display: "San Agustín Atenango",
  },
  {
    answer: "20082",
    display: "San Agustín Chayuco",
  },
  {
    answer: "20083",
    display: "San Agustín de las Juntas",
  },
  {
    answer: "20084",
    display: "San Agustín Etla",
  },
  {
    answer: "20085",
    display: "San Agustín Loxicha",
  },
  {
    answer: "20086",
    display: "San Agustín Tlacotepec",
  },
  {
    answer: "20087",
    display: "San Agustín Yatareni",
  },
  {
    answer: "20088",
    display: "San Andrés Cabecera Nueva",
  },
  {
    answer: "20089",
    display: "San Andrés Dinicuiti",
  },
  {
    answer: "20090",
    display: "San Andrés Huaxpaltepec",
  },
  {
    answer: "20091",
    display: "San Andrés Huayápam",
  },
  {
    answer: "20092",
    display: "San Andrés Ixtlahuaca",
  },
  {
    answer: "20093",
    display: "San Andrés Lagunas",
  },
  {
    answer: "20094",
    display: "San Andrés Nuxiño",
  },
  {
    answer: "20095",
    display: "San Andrés Paxtlán",
  },
  {
    answer: "20096",
    display: "San Andrés Sinaxtla",
  },
  {
    answer: "20097",
    display: "San Andrés Solaga",
  },
  {
    answer: "20098",
    display: "San Andrés Teotilálpam",
  },
  {
    answer: "20099",
    display: "San Andrés Tepetlapa",
  },
  {
    answer: "20100",
    display: "San Andrés Yaá",
  },
  {
    answer: "20101",
    display: "San Andrés Zabache",
  },
  {
    answer: "20102",
    display: "San Andrés Zautla",
  },
  {
    answer: "20103",
    display: "San Antonino Castillo Velasco",
  },
  {
    answer: "20104",
    display: "San Antonino el Alto",
  },
  {
    answer: "20105",
    display: "San Antonino Monte Verde",
  },
  {
    answer: "20106",
    display: "San Antonio Acutla",
  },
  {
    answer: "20107",
    display: "San Antonio de la Cal",
  },
  {
    answer: "20108",
    display: "San Antonio Huitepec",
  },
  {
    answer: "20109",
    display: "San Antonio Nanahuatípam",
  },
  {
    answer: "20110",
    display: "San Antonio Sinicahua",
  },
  {
    answer: "20111",
    display: "San Antonio Tepetlapa",
  },
  {
    answer: "20112",
    display: "San Baltazar Chichicápam",
  },
  {
    answer: "20113",
    display: "San Baltazar Loxicha",
  },
  {
    answer: "20114",
    display: "San Baltazar Yatzachi el Bajo",
  },
  {
    answer: "20115",
    display: "San Bartolo Coyotepec",
  },
  {
    answer: "20116",
    display: "San Bartolomé Ayautla",
  },
  {
    answer: "20117",
    display: "San Bartolomé Loxicha",
  },
  {
    answer: "20118",
    display: "San Bartolomé Quialana",
  },
  {
    answer: "20119",
    display: "San Bartolomé Yucuañe",
  },
  {
    answer: "20120",
    display: "San Bartolomé Zoogocho",
  },
  {
    answer: "20121",
    display: "San Bartolo Soyaltepec",
  },
  {
    answer: "20122",
    display: "San Bartolo Yautepec",
  },
  {
    answer: "20123",
    display: "San Bernardo Mixtepec",
  },
  {
    answer: "20124",
    display: "Heroica Villa de San Blas Atempa",
  },
  {
    answer: "20125",
    display: "San Carlos Yautepec",
  },
  {
    answer: "20126",
    display: "San Cristóbal Amatlán",
  },
  {
    answer: "20127",
    display: "San Cristóbal Amoltepec",
  },
  {
    answer: "20128",
    display: "San Cristóbal Lachirioag",
  },
  {
    answer: "20129",
    display: "San Cristóbal Suchixtlahuaca",
  },
  {
    answer: "20130",
    display: "San Dionisio del Mar",
  },
  {
    answer: "20131",
    display: "San Dionisio Ocotepec",
  },
  {
    answer: "20132",
    display: "San Dionisio Ocotlán",
  },
  {
    answer: "20133",
    display: "San Esteban Atatlahuca",
  },
  {
    answer: "20134",
    display: "San Felipe Jalapa de Díaz",
  },
  {
    answer: "20135",
    display: "San Felipe Tejalápam",
  },
  {
    answer: "20136",
    display: "San Felipe Usila",
  },
  {
    answer: "20137",
    display: "San Francisco Cahuacuá",
  },
  {
    answer: "20138",
    display: "San Francisco Cajonos",
  },
  {
    answer: "20139",
    display: "San Francisco Chapulapa",
  },
  {
    answer: "20140",
    display: "San Francisco Chindúa",
  },
  {
    answer: "20141",
    display: "San Francisco del Mar",
  },
  {
    answer: "20142",
    display: "San Francisco Huehuetlán",
  },
  {
    answer: "20143",
    display: "San Francisco Ixhuatán",
  },
  {
    answer: "20144",
    display: "San Francisco Jaltepetongo",
  },
  {
    answer: "20145",
    display: "San Francisco Lachigoló",
  },
  {
    answer: "20146",
    display: "San Francisco Logueche",
  },
  {
    answer: "20147",
    display: "San Francisco Nuxaño",
  },
  {
    answer: "20148",
    display: "San Francisco Ozolotepec",
  },
  {
    answer: "20149",
    display: "San Francisco Sola",
  },
  {
    answer: "20150",
    display: "San Francisco Telixtlahuaca",
  },
  {
    answer: "20151",
    display: "San Francisco Teopan",
  },
  {
    answer: "20152",
    display: "San Francisco Tlapancingo",
  },
  {
    answer: "20153",
    display: "San Gabriel Mixtepec",
  },
  {
    answer: "20154",
    display: "San Ildefonso Amatlán",
  },
  {
    answer: "20155",
    display: "San Ildefonso Sola",
  },
  {
    answer: "20156",
    display: "San Ildefonso Villa Alta",
  },
  {
    answer: "20157",
    display: "San Jacinto Amilpas",
  },
  {
    answer: "20158",
    display: "San Jacinto Tlacotepec",
  },
  {
    answer: "20159",
    display: "San Jerónimo Coatlán",
  },
  {
    answer: "20160",
    display: "San Jerónimo Silacayoapilla",
  },
  {
    answer: "20161",
    display: "San Jerónimo Sosola",
  },
  {
    answer: "20162",
    display: "San Jerónimo Taviche",
  },
  {
    answer: "20163",
    display: "San Jerónimo Tecóatl",
  },
  {
    answer: "20164",
    display: "San Jorge Nuchita",
  },
  {
    answer: "20165",
    display: "San José Ayuquila",
  },
  {
    answer: "20166",
    display: "San José Chiltepec",
  },
  {
    answer: "20167",
    display: "San José del Peñasco",
  },
  {
    answer: "20168",
    display: "San José Estancia Grande",
  },
  {
    answer: "20169",
    display: "San José Independencia",
  },
  {
    answer: "20170",
    display: "San José Lachiguiri",
  },
  {
    answer: "20171",
    display: "San José Tenango",
  },
  {
    answer: "20172",
    display: "San Juan Achiutla",
  },
  {
    answer: "20173",
    display: "San Juan Atepec",
  },
  {
    answer: "20174",
    display: "Ánimas Trujano",
  },
  {
    answer: "20175",
    display: "San Juan Bautista Atatlahuca",
  },
  {
    answer: "20176",
    display: "San Juan Bautista Coixtlahuaca",
  },
  {
    answer: "20177",
    display: "San Juan Bautista Cuicatlán",
  },
  {
    answer: "20178",
    display: "San Juan Bautista Guelache",
  },
  {
    answer: "20179",
    display: "San Juan Bautista Jayacatlán",
  },
  {
    answer: "20180",
    display: "San Juan Bautista Lo de Soto",
  },
  {
    answer: "20181",
    display: "San Juan Bautista Suchitepec",
  },
  {
    answer: "20182",
    display: "San Juan Bautista Tlacoatzintepec",
  },
  {
    answer: "20183",
    display: "San Juan Bautista Tlachichilco",
  },
  {
    answer: "20184",
    display: "San Juan Bautista Tuxtepec",
  },
  {
    answer: "20185",
    display: "San Juan Cacahuatepec",
  },
  {
    answer: "20186",
    display: "San Juan Cieneguilla",
  },
  {
    answer: "20187",
    display: "San Juan Coatzóspam",
  },
  {
    answer: "20188",
    display: "San Juan Colorado",
  },
  {
    answer: "20189",
    display: "San Juan Comaltepec",
  },
  {
    answer: "20190",
    display: "San Juan Cotzocón",
  },
  {
    answer: "20191",
    display: "San Juan Chicomezúchil",
  },
  {
    answer: "20192",
    display: "San Juan Chilateca",
  },
  {
    answer: "20193",
    display: "San Juan del Estado",
  },
  {
    answer: "20194",
    display: "San Juan del Río (Oax.)",
  },
  {
    answer: "20195",
    display: "San Juan Diuxi",
  },
  {
    answer: "20196",
    display: "San Juan Evangelista Analco",
  },
  {
    answer: "20197",
    display: "San Juan Guelavía",
  },
  {
    answer: "20198",
    display: "San Juan Guichicovi",
  },
  {
    answer: "20199",
    display: "San Juan Ihualtepec",
  },
  {
    answer: "20200",
    display: "San Juan Juquila Mixes",
  },
  {
    answer: "20201",
    display: "San Juan Juquila Vijanos",
  },
  {
    answer: "20202",
    display: "San Juan Lachao",
  },
  {
    answer: "20203",
    display: "San Juan Lachigalla",
  },
  {
    answer: "20204",
    display: "San Juan Lajarcia",
  },
  {
    answer: "20205",
    display: "San Juan Lalana",
  },
  {
    answer: "20206",
    display: "San Juan de los Cués",
  },
  {
    answer: "20207",
    display: "San Juan Mazatlán",
  },
  {
    answer: "20208",
    display: "San Juan Mixtepec (Oax. 208)",
  },
  {
    answer: "20209",
    display: "San Juan Mixtepec (Oax. 209)",
  },
  {
    answer: "20210",
    display: "San Juan Ñumí",
  },
  {
    answer: "20211",
    display: "San Juan Ozolotepec",
  },
  {
    answer: "20212",
    display: "San Juan Petlapa",
  },
  {
    answer: "20213",
    display: "San Juan Quiahije",
  },
  {
    answer: "20214",
    display: "San Juan Quiotepec",
  },
  {
    answer: "20215",
    display: "San Juan Sayultepec",
  },
  {
    answer: "20216",
    display: "San Juan Tabaá",
  },
  {
    answer: "20217",
    display: "San Juan Tamazola",
  },
  {
    answer: "20218",
    display: "San Juan Teita",
  },
  {
    answer: "20219",
    display: "San Juan Teitipac",
  },
  {
    answer: "20220",
    display: "San Juan Tepeuxila",
  },
  {
    answer: "20221",
    display: "San Juan Teposcolula",
  },
  {
    answer: "20222",
    display: "San Juan Yaeé",
  },
  {
    answer: "20223",
    display: "San Juan Yatzona",
  },
  {
    answer: "20224",
    display: "San Juan Yucuita",
  },
  {
    answer: "20225",
    display: "San Lorenzo",
  },
  {
    answer: "20226",
    display: "San Lorenzo Albarradas",
  },
  {
    answer: "20227",
    display: "San Lorenzo Cacaotepec",
  },
  {
    answer: "20228",
    display: "San Lorenzo Cuaunecuiltitla",
  },
  {
    answer: "20229",
    display: "San Lorenzo Texmelúcan",
  },
  {
    answer: "20230",
    display: "San Lorenzo Victoria",
  },
  {
    answer: "20231",
    display: "San Lucas Camotlán",
  },
  {
    answer: "20232",
    display: "San Lucas Ojitlán",
  },
  {
    answer: "20233",
    display: "San Lucas Quiaviní",
  },
  {
    answer: "20234",
    display: "San Lucas Zoquiápam",
  },
  {
    answer: "20235",
    display: "San Luis Amatlán",
  },
  {
    answer: "20236",
    display: "San Marcial Ozolotepec",
  },
  {
    answer: "20237",
    display: "San Marcos Arteaga",
  },
  {
    answer: "20238",
    display: "Heroico San Martín de los Cansecos",
  },
  {
    answer: "20239",
    display: "San Martín Huamelúlpam",
  },
  {
    answer: "20240",
    display: "San Martín Itunyoso",
  },
  {
    answer: "20241",
    display: "San Martín Lachilá",
  },
  {
    answer: "20242",
    display: "San Martín Peras",
  },
  {
    answer: "20243",
    display: "San Martín Tilcajete",
  },
  {
    answer: "20244",
    display: "San Martín Toxpalan",
  },
  {
    answer: "20245",
    display: "San Martín Zacatepec",
  },
  {
    answer: "20246",
    display: "San Mateo Cajonos",
  },
  {
    answer: "20247",
    display: "Capulálpam de Méndez",
  },
  {
    answer: "20248",
    display: "San Mateo del Mar",
  },
  {
    answer: "20249",
    display: "San Mateo Yoloxochitlán",
  },
  {
    answer: "20250",
    display: "San Mateo Etlatongo",
  },
  {
    answer: "20251",
    display: "San Mateo Nejápam",
  },
  {
    answer: "20252",
    display: "San Mateo Peñasco",
  },
  {
    answer: "20253",
    display: "San Mateo Piñas",
  },
  {
    answer: "20254",
    display: "San Mateo Río Hondo",
  },
  {
    answer: "20255",
    display: "San Mateo Sindihui",
  },
  {
    answer: "20256",
    display: "San Mateo Tlapiltepec",
  },
  {
    answer: "20257",
    display: "San Melchor Betaza",
  },
  {
    answer: "20258",
    display: "San Miguel Achiutla",
  },
  {
    answer: "20259",
    display: "San Miguel Ahuehuetitlán",
  },
  {
    answer: "20260",
    display: "San Miguel Aloápam",
  },
  {
    answer: "20261",
    display: "San Miguel Amatitlán",
  },
  {
    answer: "20262",
    display: "San Miguel Amatlán",
  },
  {
    answer: "20263",
    display: "San Miguel Coatlán",
  },
  {
    answer: "20264",
    display: "San Miguel Chicahua",
  },
  {
    answer: "20265",
    display: "San Miguel Chimalapa",
  },
  {
    answer: "20266",
    display: "San Miguel del Puerto",
  },
  {
    answer: "20267",
    display: "San Miguel del Río",
  },
  {
    answer: "20268",
    display: "San Miguel Ejutla",
  },
  {
    answer: "20269",
    display: "San Miguel el Grande",
  },
  {
    answer: "20270",
    display: "San Miguel Huautla",
  },
  {
    answer: "20271",
    display: "San Miguel Mixtepec",
  },
  {
    answer: "20272",
    display: "San Miguel Panixtlahuaca",
  },
  {
    answer: "20273",
    display: "San Miguel Peras",
  },
  {
    answer: "20274",
    display: "San Miguel Piedras",
  },
  {
    answer: "20275",
    display: "San Miguel Quetzaltepec",
  },
  {
    answer: "20276",
    display: "San Miguel Santa Flor",
  },
  {
    answer: "20277",
    display: "Villa Sola de Vega",
  },
  {
    answer: "20278",
    display: "San Miguel Soyaltepec",
  },
  {
    answer: "20279",
    display: "San Miguel Suchixtepec",
  },
  {
    answer: "20280",
    display: "Villa Talea de Castro",
  },
  {
    answer: "20281",
    display: "San Miguel Tecomatlán",
  },
  {
    answer: "20282",
    display: "San Miguel Tenango",
  },
  {
    answer: "20283",
    display: "San Miguel Tequixtepec",
  },
  {
    answer: "20284",
    display: "San Miguel Tilquiápam",
  },
  {
    answer: "20285",
    display: "San Miguel Tlacamama",
  },
  {
    answer: "20286",
    display: "San Miguel Tlacotepec",
  },
  {
    answer: "20287",
    display: "San Miguel Tulancingo",
  },
  {
    answer: "20288",
    display: "San Miguel Yotao",
  },
  {
    answer: "20289",
    display: "San Nicolás (Oax.)",
  },
  {
    answer: "20290",
    display: "San Nicolás Hidalgo",
  },
  {
    answer: "20291",
    display: "San Pablo Coatlán",
  },
  {
    answer: "20292",
    display: "San Pablo Cuatro Venados",
  },
  {
    answer: "20293",
    display: "San Pablo Etla",
  },
  {
    answer: "20294",
    display: "San Pablo Huitzo",
  },
  {
    answer: "20295",
    display: "San Pablo Huixtepec",
  },
  {
    answer: "20296",
    display: "San Pablo Macuiltianguis",
  },
  {
    answer: "20297",
    display: "San Pablo Tijaltepec",
  },
  {
    answer: "20298",
    display: "San Pablo Villa de Mitla",
  },
  {
    answer: "20299",
    display: "San Pablo Yaganiza",
  },
  {
    answer: "20300",
    display: "San Pedro Amuzgos",
  },
  {
    answer: "20301",
    display: "San Pedro Apóstol",
  },
  {
    answer: "20302",
    display: "San Pedro Atoyac",
  },
  {
    answer: "20303",
    display: "San Pedro Cajonos",
  },
  {
    answer: "20304",
    display: "San Pedro Coxcaltepec Cántaros",
  },
  {
    answer: "20305",
    display: "San Pedro Comitancillo",
  },
  {
    answer: "20306",
    display: "San Pedro el Alto",
  },
  {
    answer: "20307",
    display: "San Pedro Huamelula",
  },
  {
    answer: "20308",
    display: "San Pedro Huilotepec",
  },
  {
    answer: "20309",
    display: "San Pedro Ixcatlán",
  },
  {
    answer: "20310",
    display: "San Pedro Ixtlahuaca",
  },
  {
    answer: "20311",
    display: "San Pedro Jaltepetongo",
  },
  {
    answer: "20312",
    display: "San Pedro Jicayán",
  },
  {
    answer: "20313",
    display: "San Pedro Jocotipac",
  },
  {
    answer: "20314",
    display: "San Pedro Juchatengo",
  },
  {
    answer: "20315",
    display: "San Pedro Mártir",
  },
  {
    answer: "20316",
    display: "San Pedro Mártir Quiechapa",
  },
  {
    answer: "20317",
    display: "San Pedro Mártir Yucuxaco",
  },
  {
    answer: "20318",
    display: "San Pedro Mixtepec (Oax. 318)",
  },
  {
    answer: "20319",
    display: "San Pedro Mixtepec (Oax. 319)",
  },
  {
    answer: "20320",
    display: "San Pedro Molinos",
  },
  {
    answer: "20321",
    display: "San Pedro Nopala",
  },
  {
    answer: "20322",
    display: "San Pedro Ocopetatillo",
  },
  {
    answer: "20323",
    display: "San Pedro Ocotepec",
  },
  {
    answer: "20324",
    display: "San Pedro Pochutla",
  },
  {
    answer: "20325",
    display: "San Pedro Quiatoni",
  },
  {
    answer: "20326",
    display: "San Pedro Sochiápam",
  },
  {
    answer: "20327",
    display: "San Pedro Tapanatepec",
  },
  {
    answer: "20328",
    display: "San Pedro Taviche",
  },
  {
    answer: "20329",
    display: "San Pedro Teozacoalco",
  },
  {
    answer: "20330",
    display: "San Pedro Teutila",
  },
  {
    answer: "20331",
    display: "San Pedro Tidaá",
  },
  {
    answer: "20332",
    display: "San Pedro Topiltepec",
  },
  {
    answer: "20333",
    display: "San Pedro Totolápam",
  },
  {
    answer: "20334",
    display: "Villa de Tututepec",
  },
  {
    answer: "20335",
    display: "San Pedro Yaneri",
  },
  {
    answer: "20336",
    display: "San Pedro Yólox",
  },
  {
    answer: "20337",
    display: "San Pedro y San Pablo Ayutla",
  },
  {
    answer: "20338",
    display: "Villa de Etla",
  },
  {
    answer: "20339",
    display: "San Pedro y San Pablo Teposcolula",
  },
  {
    answer: "20340",
    display: "San Pedro y San Pablo Tequixtepec",
  },
  {
    answer: "20341",
    display: "San Pedro Yucunama",
  },
  {
    answer: "20342",
    display: "San Raymundo Jalpan",
  },
  {
    answer: "20343",
    display: "San Sebastián Abasolo",
  },
  {
    answer: "20344",
    display: "San Sebastián Coatlán",
  },
  {
    answer: "20345",
    display: "San Sebastián Ixcapa",
  },
  {
    answer: "20346",
    display: "San Sebastián Nicananduta",
  },
  {
    answer: "20347",
    display: "San Sebastián Río Hondo",
  },
  {
    answer: "20348",
    display: "San Sebastián Tecomaxtlahuaca",
  },
  {
    answer: "20349",
    display: "San Sebastián Teitipac",
  },
  {
    answer: "20350",
    display: "San Sebastián Tutla",
  },
  {
    answer: "20351",
    display: "San Simón Almolongas",
  },
  {
    answer: "20352",
    display: "San Simón Zahuatlán",
  },
  {
    answer: "20353",
    display: "Santa Ana (Oax.)",
  },
  {
    answer: "20354",
    display: "Santa Ana Ateixtlahuaca",
  },
  {
    answer: "20355",
    display: "Santa Ana Cuauhtémoc",
  },
  {
    answer: "20356",
    display: "Santa Ana del Valle",
  },
  {
    answer: "20357",
    display: "Santa Ana Tavela",
  },
  {
    answer: "20358",
    display: "Santa Ana Tlapacoyan",
  },
  {
    answer: "20359",
    display: "Santa Ana Yareni",
  },
  {
    answer: "20360",
    display: "Santa Ana Zegache",
  },
  {
    answer: "20361",
    display: "Santa Catalina Quierí",
  },
  {
    answer: "20362",
    display: "Santa Catarina Cuixtla",
  },
  {
    answer: "20363",
    display: "Santa Catarina Ixtepeji",
  },
  {
    answer: "20364",
    display: "Santa Catarina Juquila",
  },
  {
    answer: "20365",
    display: "Santa Catarina Lachatao",
  },
  {
    answer: "20366",
    display: "Santa Catarina Loxicha",
  },
  {
    answer: "20367",
    display: "Santa Catarina Mechoacán",
  },
  {
    answer: "20368",
    display: "Santa Catarina Minas",
  },
  {
    answer: "20369",
    display: "Santa Catarina Quiané",
  },
  {
    answer: "20370",
    display: "Santa Catarina Tayata",
  },
  {
    answer: "20371",
    display: "Santa Catarina Ticuá",
  },
  {
    answer: "20372",
    display: "Santa Catarina Yosonotú",
  },
  {
    answer: "20373",
    display: "Santa Catarina Zapoquila",
  },
  {
    answer: "20374",
    display: "Santa Cruz Acatepec",
  },
  {
    answer: "20375",
    display: "Santa Cruz Amilpas",
  },
  {
    answer: "20376",
    display: "Santa Cruz de Bravo",
  },
  {
    answer: "20377",
    display: "Santa Cruz Itundujia",
  },
  {
    answer: "20378",
    display: "Santa Cruz Mixtepec",
  },
  {
    answer: "20379",
    display: "Santa Cruz Nundaco",
  },
  {
    answer: "20380",
    display: "Santa Cruz Papalutla",
  },
  {
    answer: "20381",
    display: "Santa Cruz Tacache de Mina",
  },
  {
    answer: "20382",
    display: "Santa Cruz Tacahua",
  },
  {
    answer: "20383",
    display: "Santa Cruz Tayata",
  },
  {
    answer: "20384",
    display: "Santa Cruz Xitla",
  },
  {
    answer: "20385",
    display: "Santa Cruz Xoxocotlán",
  },
  {
    answer: "20386",
    display: "Santa Cruz Zenzontepec",
  },
  {
    answer: "20387",
    display: "Santa Gertrudis",
  },
  {
    answer: "20388",
    display: "Santa Inés del Monte",
  },
  {
    answer: "20389",
    display: "Santa Inés Yatzeche",
  },
  {
    answer: "20390",
    display: "Santa Lucía del Camino",
  },
  {
    answer: "20391",
    display: "Santa Lucía Miahuatlán",
  },
  {
    answer: "20392",
    display: "Santa Lucía Monteverde",
  },
  {
    answer: "20393",
    display: "Santa Lucía Ocotlán",
  },
  {
    answer: "20394",
    display: "Santa María Alotepec",
  },
  {
    answer: "20395",
    display: "Santa María Apazco",
  },
  {
    answer: "20396",
    display: "Santa María la Asunción",
  },
  {
    answer: "20397",
    display: "Heroica Ciudad de Tlaxiaco",
  },
  {
    answer: "20398",
    display: "Ayoquezco de Aldama",
  },
  {
    answer: "20399",
    display: "Santa María Atzompa",
  },
  {
    answer: "20400",
    display: "Santa María Camotlán",
  },
  {
    answer: "20401",
    display: "Santa María Colotepec",
  },
  {
    answer: "20402",
    display: "Santa María Cortijo",
  },
  {
    answer: "20403",
    display: "Santa María Coyotepec",
  },
  {
    answer: "20404",
    display: "Santa María Chachoápam",
  },
  {
    answer: "20405",
    display: "Villa de Chilapa de Díaz",
  },
  {
    answer: "20406",
    display: "Santa María Chilchotla",
  },
  {
    answer: "20407",
    display: "Santa María Chimalapa",
  },
  {
    answer: "20408",
    display: "Santa María del Rosario",
  },
  {
    answer: "20409",
    display: "Santa María del Tule",
  },
  {
    answer: "20410",
    display: "Santa María Ecatepec",
  },
  {
    answer: "20411",
    display: "Santa María Guelacé",
  },
  {
    answer: "20412",
    display: "Santa María Guienagati",
  },
  {
    answer: "20413",
    display: "Santa María Huatulco",
  },
  {
    answer: "20414",
    display: "Santa María Huazolotitlán",
  },
  {
    answer: "20415",
    display: "Santa María Ipalapa",
  },
  {
    answer: "20416",
    display: "Santa María Ixcatlán",
  },
  {
    answer: "20417",
    display: "Santa María Jacatepec",
  },
  {
    answer: "20418",
    display: "Santa María Jalapa del Marqués",
  },
  {
    answer: "20419",
    display: "Santa María Jaltianguis",
  },
  {
    answer: "20420",
    display: "Santa María Lachixío",
  },
  {
    answer: "20421",
    display: "Santa María Mixtequilla",
  },
  {
    answer: "20422",
    display: "Santa María Nativitas",
  },
  {
    answer: "20423",
    display: "Santa María Nduayaco",
  },
  {
    answer: "20424",
    display: "Santa María Ozolotepec",
  },
  {
    answer: "20425",
    display: "Santa María Pápalo",
  },
  {
    answer: "20426",
    display: "Santa María Peñoles",
  },
  {
    answer: "20427",
    display: "Santa María Petapa",
  },
  {
    answer: "20428",
    display: "Santa María Quiegolani",
  },
  {
    answer: "20429",
    display: "Santa María Sola",
  },
  {
    answer: "20430",
    display: "Santa María Tataltepec",
  },
  {
    answer: "20431",
    display: "Santa María Tecomavaca",
  },
  {
    answer: "20432",
    display: "Santa María Temaxcalapa",
  },
  {
    answer: "20433",
    display: "Santa María Temaxcaltepec",
  },
  {
    answer: "20434",
    display: "Santa María Teopoxco",
  },
  {
    answer: "20435",
    display: "Santa María Tepantlali",
  },
  {
    answer: "20436",
    display: "Santa María Texcatitlán",
  },
  {
    answer: "20437",
    display: "Santa María Tlahuitoltepec",
  },
  {
    answer: "20438",
    display: "Santa María Tlalixtac",
  },
  {
    answer: "20439",
    display: "Santa María Tonameca",
  },
  {
    answer: "20440",
    display: "Santa María Totolapilla",
  },
  {
    answer: "20441",
    display: "Santa María Xadani",
  },
  {
    answer: "20442",
    display: "Santa María Yalina",
  },
  {
    answer: "20443",
    display: "Santa María Yavesía",
  },
  {
    answer: "20444",
    display: "Santa María Yolotepec",
  },
  {
    answer: "20445",
    display: "Santa María Yosoyúa",
  },
  {
    answer: "20446",
    display: "Santa María Yucuhiti",
  },
  {
    answer: "20447",
    display: "Santa María Zacatepec",
  },
  {
    answer: "20448",
    display: "Santa María Zaniza",
  },
  {
    answer: "20449",
    display: "Santa María Zoquitlán",
  },
  {
    answer: "20450",
    display: "Santiago Amoltepec",
  },
  {
    answer: "20451",
    display: "Santiago Apoala",
  },
  {
    answer: "20452",
    display: "Santiago Apóstol",
  },
  {
    answer: "20453",
    display: "Santiago Astata",
  },
  {
    answer: "20454",
    display: "Santiago Atitlán",
  },
  {
    answer: "20455",
    display: "Santiago Ayuquililla",
  },
  {
    answer: "20456",
    display: "Santiago Cacaloxtepec",
  },
  {
    answer: "20457",
    display: "Santiago Camotlán",
  },
  {
    answer: "20458",
    display: "Santiago Comaltepec",
  },
  {
    answer: "20459",
    display: "Villa de Santiago Chazumba",
  },
  {
    answer: "20460",
    display: "Santiago Choápam",
  },
  {
    answer: "20461",
    display: "Santiago del Río",
  },
  {
    answer: "20462",
    display: "Santiago Huajolotitlán",
  },
  {
    answer: "20463",
    display: "Santiago Huauclilla",
  },
  {
    answer: "20464",
    display: "Santiago Ihuitlán Plumas",
  },
  {
    answer: "20465",
    display: "Santiago Ixcuintepec",
  },
  {
    answer: "20466",
    display: "Santiago Ixtayutla",
  },
  {
    answer: "20467",
    display: "Santiago Jamiltepec",
  },
  {
    answer: "20468",
    display: "Santiago Jocotepec",
  },
  {
    answer: "20469",
    display: "Santiago Juxtlahuaca",
  },
  {
    answer: "20470",
    display: "Santiago Lachiguiri",
  },
  {
    answer: "20471",
    display: "Santiago Lalopa",
  },
  {
    answer: "20472",
    display: "Santiago Laollaga",
  },
  {
    answer: "20473",
    display: "Santiago Laxopa",
  },
  {
    answer: "20474",
    display: "Santiago Llano Grande",
  },
  {
    answer: "20475",
    display: "Santiago Matatlán",
  },
  {
    answer: "20476",
    display: "Santiago Miltepec",
  },
  {
    answer: "20477",
    display: "Santiago Minas",
  },
  {
    answer: "20478",
    display: "Santiago Nacaltepec",
  },
  {
    answer: "20479",
    display: "Santiago Nejapilla",
  },
  {
    answer: "20480",
    display: "Santiago Nundiche",
  },
  {
    answer: "20481",
    display: "Santiago Nuyoó",
  },
  {
    answer: "20482",
    display: "Santiago Pinotepa Nacional",
  },
  {
    answer: "20483",
    display: "Santiago Suchilquitongo",
  },
  {
    answer: "20484",
    display: "Santiago Tamazola",
  },
  {
    answer: "20485",
    display: "Santiago Tapextla",
  },
  {
    answer: "20486",
    display: "Villa Tejúpam de la Unión",
  },
  {
    answer: "20487",
    display: "Santiago Tenango",
  },
  {
    answer: "20488",
    display: "Santiago Tepetlapa",
  },
  {
    answer: "20489",
    display: "Santiago Tetepec",
  },
  {
    answer: "20490",
    display: "Santiago Texcalcingo",
  },
  {
    answer: "20491",
    display: "Santiago Textitlán",
  },
  {
    answer: "20492",
    display: "Santiago Tilantongo",
  },
  {
    answer: "20493",
    display: "Santiago Tillo",
  },
  {
    answer: "20494",
    display: "Santiago Tlazoyaltepec",
  },
  {
    answer: "20495",
    display: "Santiago Xanica",
  },
  {
    answer: "20496",
    display: "Santiago Xiacuí",
  },
  {
    answer: "20497",
    display: "Santiago Yaitepec",
  },
  {
    answer: "20498",
    display: "Santiago Yaveo",
  },
  {
    answer: "20499",
    display: "Santiago Yolomécatl",
  },
  {
    answer: "20500",
    display: "Santiago Yosondúa",
  },
  {
    answer: "20501",
    display: "Santiago Yucuyachi",
  },
  {
    answer: "20502",
    display: "Santiago Zacatepec",
  },
  {
    answer: "20503",
    display: "Santiago Zoochila",
  },
  {
    answer: "20504",
    display: "Nuevo Zoquiápam",
  },
  {
    answer: "20505",
    display: "Santo Domingo Ingenio",
  },
  {
    answer: "20506",
    display: "Santo Domingo Albarradas",
  },
  {
    answer: "20507",
    display: "Santo Domingo Armenta",
  },
  {
    answer: "20508",
    display: "Santo Domingo Chihuitán",
  },
  {
    answer: "20509",
    display: "Santo Domingo de Morelos",
  },
  {
    answer: "20510",
    display: "Santo Domingo Ixcatlán",
  },
  {
    answer: "20511",
    display: "Santo Domingo Nuxaá",
  },
  {
    answer: "20512",
    display: "Santo Domingo Ozolotepec",
  },
  {
    answer: "20513",
    display: "Santo Domingo Petapa",
  },
  {
    answer: "20514",
    display: "Santo Domingo Roayaga",
  },
  {
    answer: "20515",
    display: "Santo Domingo Tehuantepec",
  },
  {
    answer: "20516",
    display: "Santo Domingo Teojomulco",
  },
  {
    answer: "20517",
    display: "Santo Domingo Tepuxtepec",
  },
  {
    answer: "20518",
    display: "Santo Domingo Tlatayápam",
  },
  {
    answer: "20519",
    display: "Santo Domingo Tomaltepec",
  },
  {
    answer: "20520",
    display: "Santo Domingo Tonalá",
  },
  {
    answer: "20521",
    display: "Santo Domingo Tonaltepec",
  },
  {
    answer: "20522",
    display: "Santo Domingo Xagacía",
  },
  {
    answer: "20523",
    display: "Santo Domingo Yanhuitlán",
  },
  {
    answer: "20524",
    display: "Santo Domingo Yodohino",
  },
  {
    answer: "20525",
    display: "Santo Domingo Zanatepec",
  },
  {
    answer: "20526",
    display: "Santos Reyes Nopala",
  },
  {
    answer: "20527",
    display: "Santos Reyes Pápalo",
  },
  {
    answer: "20528",
    display: "Santos Reyes Tepejillo",
  },
  {
    answer: "20529",
    display: "Santos Reyes Yucuná",
  },
  {
    answer: "20530",
    display: "Santo Tomás Jalieza",
  },
  {
    answer: "20531",
    display: "Santo Tomás Mazaltepec",
  },
  {
    answer: "20532",
    display: "Santo Tomás Ocotepec",
  },
  {
    answer: "20533",
    display: "Santo Tomás Tamazulapan",
  },
  {
    answer: "20534",
    display: "San Vicente Coatlán",
  },
  {
    answer: "20535",
    display: "San Vicente Lachixío",
  },
  {
    answer: "20536",
    display: "San Vicente Nuñú",
  },
  {
    answer: "20537",
    display: "Silacayoápam",
  },
  {
    answer: "20538",
    display: "Sitio de Xitlapehua",
  },
  {
    answer: "20539",
    display: "Soledad Etla",
  },
  {
    answer: "20540",
    display: "Villa de Tamazulápam del Progreso",
  },
  {
    answer: "20541",
    display: "Tanetze de Zaragoza",
  },
  {
    answer: "20542",
    display: "Taniche",
  },
  {
    answer: "20543",
    display: "Tataltepec de Valdés",
  },
  {
    answer: "20544",
    display: "Teococuilco de Marcos Pérez",
  },
  {
    answer: "20545",
    display: "Teotitlán de Flores Magón",
  },
  {
    answer: "20546",
    display: "Teotitlán del Valle",
  },
  {
    answer: "20547",
    display: "Teotongo",
  },
  {
    answer: "20548",
    display: "Tepelmeme Villa de Morelos",
  },
  {
    answer: "20549",
    display:
      "Heroica Villa Tezoatlán de Segura y Luna, Cuna de la Independencia de Oaxaca",
  },
  {
    answer: "20550",
    display: "San Jerónimo Tlacochahuaya",
  },
  {
    answer: "20551",
    display: "Tlacolula de Matamoros",
  },
  {
    answer: "20552",
    display: "Tlacotepec Plumas",
  },
  {
    answer: "20553",
    display: "Tlalixtac de Cabrera",
  },
  {
    answer: "20554",
    display: "Totontepec Villa de Morelos",
  },
  {
    answer: "20555",
    display: "Trinidad Zaachila",
  },
  {
    answer: "20556",
    display: "La Trinidad Vista Hermosa",
  },
  {
    answer: "20557",
    display: "Unión Hidalgo",
  },
  {
    answer: "20558",
    display: "Valerio Trujano",
  },
  {
    answer: "20559",
    display: "San Juan Bautista Valle Nacional",
  },
  {
    answer: "20560",
    display: "Villa Díaz Ordaz",
  },
  {
    answer: "20561",
    display: "Yaxe",
  },
  {
    answer: "20562",
    display: "Magdalena Yodocono de Porfirio Díaz",
  },
  {
    answer: "20563",
    display: "Yogana",
  },
  {
    answer: "20564",
    display: "Yutanduchi de Guerrero",
  },
  {
    answer: "20565",
    display: "Villa de Zaachila",
  },
  {
    answer: "20566",
    display: "San Mateo Yucutindoo",
  },
  {
    answer: "20567",
    display: "Zapotitlán Lagunas",
  },
  {
    answer: "20568",
    display: "Zapotitlán Palmas",
  },
  {
    answer: "20569",
    display: "Santa Inés de Zaragoza",
  },
  {
    answer: "20570",
    display: "Zimatlán de Álvarez",
  },
  {
    answer: "21001",
    display: "Acajete (Pue.)",
  },
  {
    answer: "21002",
    display: "Acateno",
  },
  {
    answer: "21003",
    display: "Acatlán (Pue.)",
  },
  {
    answer: "21004",
    display: "Acatzingo",
  },
  {
    answer: "21005",
    display: "Acteopan",
  },
  {
    answer: "21006",
    display: "Ahuacatlán (Pue.)",
  },
  {
    answer: "21007",
    display: "Ahuatlán",
  },
  {
    answer: "21008",
    display: "Ahuazotepec",
  },
  {
    answer: "21009",
    display: "Ahuehuetitla",
  },
  {
    answer: "21010",
    display: "Ajalpan",
  },
  {
    answer: "21011",
    display: "Albino Zertuche",
  },
  {
    answer: "21012",
    display: "Aljojuca",
  },
  {
    answer: "21013",
    display: "Altepexi",
  },
  {
    answer: "21014",
    display: "Amixtlán",
  },
  {
    answer: "21015",
    display: "Amozoc",
  },
  {
    answer: "21016",
    display: "Aquixtla",
  },
  {
    answer: "21017",
    display: "Atempan",
  },
  {
    answer: "21018",
    display: "Atexcal",
  },
  {
    answer: "21019",
    display: "Atlixco",
  },
  {
    answer: "21020",
    display: "Atoyatempan",
  },
  {
    answer: "21021",
    display: "Atzala",
  },
  {
    answer: "21022",
    display: "Atzitzihuacán",
  },
  {
    answer: "21023",
    display: "Atzitzintla",
  },
  {
    answer: "21024",
    display: "Axutla",
  },
  {
    answer: "21025",
    display: "Ayotoxco de Guerrero",
  },
  {
    answer: "21026",
    display: "Calpan",
  },
  {
    answer: "21027",
    display: "Caltepec",
  },
  {
    answer: "21028",
    display: "Camocuautla",
  },
  {
    answer: "21029",
    display: "Caxhuacan",
  },
  {
    answer: "21030",
    display: "Coatepec (Pue.)",
  },
  {
    answer: "21031",
    display: "Coatzingo",
  },
  {
    answer: "21032",
    display: "Cohetzala",
  },
  {
    answer: "21033",
    display: "Cohuecan",
  },
  {
    answer: "21034",
    display: "Coronango",
  },
  {
    answer: "21035",
    display: "Coxcatlán (Pue.)",
  },
  {
    answer: "21036",
    display: "Coyomeapan",
  },
  {
    answer: "21037",
    display: "Coyotepec (Pue.)",
  },
  {
    answer: "21038",
    display: "Cuapiaxtla de Madero",
  },
  {
    answer: "21039",
    display: "Cuautempan",
  },
  {
    answer: "21040",
    display: "Cuautinchán",
  },
  {
    answer: "21041",
    display: "Cuautlancingo",
  },
  {
    answer: "21042",
    display: "Cuayuca de Andrade",
  },
  {
    answer: "21043",
    display: "Cuetzalan del Progreso",
  },
  {
    answer: "21044",
    display: "Cuyoaco",
  },
  {
    answer: "21045",
    display: "Chalchicomula de Sesma",
  },
  {
    answer: "21046",
    display: "Chapulco",
  },
  {
    answer: "21047",
    display: "Chiautla (Pue.)",
  },
  {
    answer: "21048",
    display: "Chiautzingo",
  },
  {
    answer: "21049",
    display: "Chiconcuautla",
  },
  {
    answer: "21050",
    display: "Chichiquila",
  },
  {
    answer: "21051",
    display: "Chietla",
  },
  {
    answer: "21052",
    display: "Chigmecatitlán",
  },
  {
    answer: "21053",
    display: "Chignahuapan",
  },
  {
    answer: "21054",
    display: "Chignautla",
  },
  {
    answer: "21055",
    display: "Chila",
  },
  {
    answer: "21056",
    display: "Chila de la Sal",
  },
  {
    answer: "21057",
    display: "Honey",
  },
  {
    answer: "21058",
    display: "Chilchotla",
  },
  {
    answer: "21059",
    display: "Chinantla",
  },
  {
    answer: "21060",
    display: "Domingo Arenas",
  },
  {
    answer: "21061",
    display: "Eloxochitlán (Pue.)",
  },
  {
    answer: "21062",
    display: "Epatlán",
  },
  {
    answer: "21063",
    display: "Esperanza",
  },
  {
    answer: "21064",
    display: "Francisco Z. Mena",
  },
  {
    answer: "21065",
    display: "General Felipe Ángeles",
  },
  {
    answer: "21066",
    display: "Guadalupe (Pue.)",
  },
  {
    answer: "21067",
    display: "Guadalupe Victoria (Pue.)",
  },
  {
    answer: "21068",
    display: "Hermenegildo Galeana",
  },
  {
    answer: "21069",
    display: "Huaquechula",
  },
  {
    answer: "21070",
    display: "Huatlatlauca",
  },
  {
    answer: "21071",
    display: "Huauchinango",
  },
  {
    answer: "21072",
    display: "Huehuetla (Pue.)",
  },
  {
    answer: "21073",
    display: "Huehuetlán el Chico",
  },
  {
    answer: "21074",
    display: "Huejotzingo",
  },
  {
    answer: "21075",
    display: "Hueyapan (Pue.)",
  },
  {
    answer: "21076",
    display: "Hueytamalco",
  },
  {
    answer: "21077",
    display: "Hueytlalpan",
  },
  {
    answer: "21078",
    display: "Huitzilan de Serdán",
  },
  {
    answer: "21079",
    display: "Huitziltepec",
  },
  {
    answer: "21080",
    display: "Atlequizayan",
  },
  {
    answer: "21081",
    display: "Ixcamilpa de Guerrero",
  },
  {
    answer: "21082",
    display: "Ixcaquixtla",
  },
  {
    answer: "21083",
    display: "Ixtacamaxtitlán",
  },
  {
    answer: "21084",
    display: "Ixtepec",
  },
  {
    answer: "21085",
    display: "Izúcar de Matamoros",
  },
  {
    answer: "21086",
    display: "Jalpan",
  },
  {
    answer: "21087",
    display: "Jolalpan",
  },
  {
    answer: "21088",
    display: "Jonotla",
  },
  {
    answer: "21089",
    display: "Jopala",
  },
  {
    answer: "21090",
    display: "Juan C. Bonilla",
  },
  {
    answer: "21091",
    display: "Juan Galindo",
  },
  {
    answer: "21092",
    display: "Juan N. Méndez",
  },
  {
    answer: "21093",
    display: "Lafragua",
  },
  {
    answer: "21094",
    display: "Libres",
  },
  {
    answer: "21095",
    display: "La Magdalena Tlatlauquitepec",
  },
  {
    answer: "21096",
    display: "Mazapiltepec de Juárez",
  },
  {
    answer: "21097",
    display: "Mixtla",
  },
  {
    answer: "21098",
    display: "Molcaxac",
  },
  {
    answer: "21099",
    display: "Cañada Morelos",
  },
  {
    answer: "21100",
    display: "Naupan",
  },
  {
    answer: "21101",
    display: "Nauzontla",
  },
  {
    answer: "21102",
    display: "Nealtican",
  },
  {
    answer: "21103",
    display: "Nicolás Bravo",
  },
  {
    answer: "21104",
    display: "Nopalucan",
  },
  {
    answer: "21105",
    display: "Ocotepec (Pue.)",
  },
  {
    answer: "21106",
    display: "Ocoyucan",
  },
  {
    answer: "21107",
    display: "Olintla",
  },
  {
    answer: "21108",
    display: "Oriental",
  },
  {
    answer: "21109",
    display: "Pahuatlán",
  },
  {
    answer: "21110",
    display: "Palmar de Bravo",
  },
  {
    answer: "21111",
    display: "Pantepec (Pue.)",
  },
  {
    answer: "21112",
    display: "Petlalcingo",
  },
  {
    answer: "21113",
    display: "Piaxtla",
  },
  {
    answer: "21114",
    display: "Puebla",
  },
  {
    answer: "21115",
    display: "Quecholac",
  },
  {
    answer: "21116",
    display: "Quimixtlán",
  },
  {
    answer: "21117",
    display: "Rafael Lara Grajales",
  },
  {
    answer: "21118",
    display: "Los Reyes de Juárez",
  },
  {
    answer: "21119",
    display: "San Andrés Cholula",
  },
  {
    answer: "21120",
    display: "San Antonio Cañada",
  },
  {
    answer: "21121",
    display: "San Diego la Mesa Tochimiltzingo",
  },
  {
    answer: "21122",
    display: "San Felipe Teotlalcingo",
  },
  {
    answer: "21123",
    display: "San Felipe Tepatlán",
  },
  {
    answer: "21124",
    display: "San Gabriel Chilac",
  },
  {
    answer: "21125",
    display: "San Gregorio Atzompa",
  },
  {
    answer: "21126",
    display: "San Jerónimo Tecuanipan",
  },
  {
    answer: "21127",
    display: "San Jerónimo Xayacatlán",
  },
  {
    answer: "21128",
    display: "San José Chiapa",
  },
  {
    answer: "21129",
    display: "San José Miahuatlán",
  },
  {
    answer: "21130",
    display: "San Juan Atenco",
  },
  {
    answer: "21131",
    display: "San Juan Atzompa",
  },
  {
    answer: "21132",
    display: "San Martín Texmelucan",
  },
  {
    answer: "21133",
    display: "San Martín Totoltepec",
  },
  {
    answer: "21134",
    display: "San Matías Tlalancaleca",
  },
  {
    answer: "21135",
    display: "San Miguel Ixitlán",
  },
  {
    answer: "21136",
    display: "San Miguel Xoxtla",
  },
  {
    answer: "21137",
    display: "San Nicolás Buenos Aires",
  },
  {
    answer: "21138",
    display: "San Nicolás de los Ranchos",
  },
  {
    answer: "21139",
    display: "San Pablo Anicano",
  },
  {
    answer: "21140",
    display: "San Pedro Cholula",
  },
  {
    answer: "21141",
    display: "San Pedro Yeloixtlahuaca",
  },
  {
    answer: "21142",
    display: "San Salvador el Seco",
  },
  {
    answer: "21143",
    display: "San Salvador el Verde",
  },
  {
    answer: "21144",
    display: "San Salvador Huixcolotla",
  },
  {
    answer: "21145",
    display: "San Sebastián Tlacotepec",
  },
  {
    answer: "21146",
    display: "Santa Catarina Tlaltempan",
  },
  {
    answer: "21147",
    display: "Santa Inés Ahuatempan",
  },
  {
    answer: "21148",
    display: "Santa Isabel Cholula",
  },
  {
    answer: "21149",
    display: "Santiago Miahuatlán",
  },
  {
    answer: "21150",
    display: "Huehuetlán el Grande",
  },
  {
    answer: "21151",
    display: "Santo Tomás Hueyotlipan",
  },
  {
    answer: "21152",
    display: "Soltepec",
  },
  {
    answer: "21153",
    display: "Tecali de Herrera",
  },
  {
    answer: "21154",
    display: "Tecamachalco",
  },
  {
    answer: "21155",
    display: "Tecomatlán",
  },
  {
    answer: "21156",
    display: "Tehuacán",
  },
  {
    answer: "21157",
    display: "Tehuitzingo",
  },
  {
    answer: "21158",
    display: "Tenampulco",
  },
  {
    answer: "21159",
    display: "Teopantlán",
  },
  {
    answer: "21160",
    display: "Teotlalco",
  },
  {
    answer: "21161",
    display: "Tepanco de López",
  },
  {
    answer: "21162",
    display: "Tepango de Rodríguez",
  },
  {
    answer: "21163",
    display: "Tepatlaxco de Hidalgo",
  },
  {
    answer: "21164",
    display: "Tepeaca",
  },
  {
    answer: "21165",
    display: "Tepemaxalco",
  },
  {
    answer: "21166",
    display: "Tepeojuma",
  },
  {
    answer: "21167",
    display: "Tepetzintla (Pue.)",
  },
  {
    answer: "21168",
    display: "Tepexco",
  },
  {
    answer: "21169",
    display: "Tepexi de Rodríguez",
  },
  {
    answer: "21170",
    display: "Tepeyahualco",
  },
  {
    answer: "21171",
    display: "Tepeyahualco de Cuauhtémoc",
  },
  {
    answer: "21172",
    display: "Tetela de Ocampo",
  },
  {
    answer: "21173",
    display: "Teteles de Ávila Castillo",
  },
  {
    answer: "21174",
    display: "Teziutlán",
  },
  {
    answer: "21175",
    display: "Tianguismanalco",
  },
  {
    answer: "21176",
    display: "Tilapa",
  },
  {
    answer: "21177",
    display: "Tlacotepec de Benito Juárez",
  },
  {
    answer: "21178",
    display: "Tlacuilotepec",
  },
  {
    answer: "21179",
    display: "Tlachichuca",
  },
  {
    answer: "21180",
    display: "Tlahuapan",
  },
  {
    answer: "21181",
    display: "Tlaltenango",
  },
  {
    answer: "21182",
    display: "Tlanepantla",
  },
  {
    answer: "21183",
    display: "Tlaola",
  },
  {
    answer: "21184",
    display: "Tlapacoya",
  },
  {
    answer: "21185",
    display: "Tlapanalá",
  },
  {
    answer: "21186",
    display: "Tlatlauquitepec",
  },
  {
    answer: "21187",
    display: "Tlaxco (Pue.)",
  },
  {
    answer: "21188",
    display: "Tochimilco",
  },
  {
    answer: "21189",
    display: "Tochtepec",
  },
  {
    answer: "21190",
    display: "Totoltepec de Guerrero",
  },
  {
    answer: "21191",
    display: "Tulcingo",
  },
  {
    answer: "21192",
    display: "Tuzamapan de Galeana",
  },
  {
    answer: "21193",
    display: "Tzicatlacoyan",
  },
  {
    answer: "21194",
    display: "Venustiano Carranza (Pue.)",
  },
  {
    answer: "21195",
    display: "Vicente Guerrero (Pue.)",
  },
  {
    answer: "21196",
    display: "Xayacatlán de Bravo",
  },
  {
    answer: "21197",
    display: "Xicotepec",
  },
  {
    answer: "21198",
    display: "Xicotlán",
  },
  {
    answer: "21199",
    display: "Xiutetelco",
  },
  {
    answer: "21200",
    display: "Xochiapulco",
  },
  {
    answer: "21201",
    display: "Xochiltepec",
  },
  {
    answer: "21202",
    display: "Xochitlán de Vicente Suárez",
  },
  {
    answer: "21203",
    display: "Xochitlán Todos Santos",
  },
  {
    answer: "21204",
    display: "Yaonáhuac",
  },
  {
    answer: "21205",
    display: "Yehualtepec",
  },
  {
    answer: "21206",
    display: "Zacapala",
  },
  {
    answer: "21207",
    display: "Zacapoaxtla",
  },
  {
    answer: "21208",
    display: "Zacatlán",
  },
  {
    answer: "21209",
    display: "Zapotitlán",
  },
  {
    answer: "21210",
    display: "Zapotitlán de Méndez",
  },
  {
    answer: "21211",
    display: "Zaragoza (Pue.)",
  },
  {
    answer: "21212",
    display: "Zautla",
  },
  {
    answer: "21213",
    display: "Zihuateutla",
  },
  {
    answer: "21214",
    display: "Zinacatepec",
  },
  {
    answer: "21215",
    display: "Zongozotla",
  },
  {
    answer: "21216",
    display: "Zoquiapan",
  },
  {
    answer: "21217",
    display: "Zoquitlán",
  },
  {
    answer: "22001",
    display: "Amealco de Bonfil",
  },
  {
    answer: "22002",
    display: "Pinal de Amoles",
  },
  {
    answer: "22003",
    display: "Arroyo Seco",
  },
  {
    answer: "22004",
    display: "Cadereyta de Montes",
  },
  {
    answer: "22005",
    display: "Colón",
  },
  {
    answer: "22006",
    display: "Corregidora",
  },
  {
    answer: "22007",
    display: "Ezequiel Montes",
  },
  {
    answer: "22008",
    display: "Huimilpan",
  },
  {
    answer: "22009",
    display: "Jalpan de Serra",
  },
  {
    answer: "22010",
    display: "Landa de Matamoros",
  },
  {
    answer: "22011",
    display: "El Marqués",
  },
  {
    answer: "22012",
    display: "Pedro Escobedo",
  },
  {
    answer: "22013",
    display: "Peñamiller",
  },
  {
    answer: "22014",
    display: "Querétaro",
  },
  {
    answer: "22015",
    display: "San Joaquín",
  },
  {
    answer: "22016",
    display: "San Juan del Río (Qro.)",
  },
  {
    answer: "22017",
    display: "Tequisquiapan",
  },
  {
    answer: "22018",
    display: "Tolimán (Qro.)",
  },
  {
    answer: "23001",
    display: "Cozumel",
  },
  {
    answer: "23002",
    display: "Felipe Carrillo Puerto",
  },
  {
    answer: "23003",
    display: "Isla Mujeres",
  },
  {
    answer: "23004",
    display: "Othón P. Blanco",
  },
  {
    answer: "23005",
    display: "Benito Juárez (Q. Roo)",
  },
  {
    answer: "23006",
    display: "José María Morelos",
  },
  {
    answer: "23007",
    display: "Lázaro Cárdenas (Q. Roo)",
  },
  {
    answer: "23008",
    display: "Playa del Carmen",
  },
  {
    answer: "23009",
    display: "Tulum",
  },
  {
    answer: "23010",
    display: "Bacalar",
  },
  {
    answer: "23011",
    display: "Puerto Morelos",
  },
  {
    answer: "24001",
    display: "Ahualulco del Sonido 13",
  },
  {
    answer: "24002",
    display: "Alaquines",
  },
  {
    answer: "24003",
    display: "Aquismón",
  },
  {
    answer: "24004",
    display: "Armadillo de los Infante",
  },
  {
    answer: "24005",
    display: "Cárdenas (S.L.P.)",
  },
  {
    answer: "24006",
    display: "Catorce",
  },
  {
    answer: "24007",
    display: "Cedral",
  },
  {
    answer: "24008",
    display: "Cerritos",
  },
  {
    answer: "24009",
    display: "Cerro de San Pedro",
  },
  {
    answer: "24010",
    display: "Ciudad del Maíz",
  },
  {
    answer: "24011",
    display: "Ciudad Fernández",
  },
  {
    answer: "24012",
    display: "Tancanhuitz",
  },
  {
    answer: "24013",
    display: "Ciudad Valles",
  },
  {
    answer: "24014",
    display: "Coxcatlán (S.L.P.)",
  },
  {
    answer: "24015",
    display: "Charcas",
  },
  {
    answer: "24016",
    display: "Ebano",
  },
  {
    answer: "24017",
    display: "Guadalcázar",
  },
  {
    answer: "24018",
    display: "Huehuetlán",
  },
  {
    answer: "24019",
    display: "Lagunillas (S.L.P.)",
  },
  {
    answer: "24020",
    display: "Matehuala",
  },
  {
    answer: "24021",
    display: "Mexquitic de Carmona",
  },
  {
    answer: "24022",
    display: "Moctezuma (S.L.P.)",
  },
  {
    answer: "24023",
    display: "Rayón (S.L.P.)",
  },
  {
    answer: "24024",
    display: "Rioverde",
  },
  {
    answer: "24025",
    display: "Salinas",
  },
  {
    answer: "24026",
    display: "San Antonio",
  },
  {
    answer: "24027",
    display: "San Ciro de Acosta",
  },
  {
    answer: "24028",
    display: "San Luis Potosí",
  },
  {
    answer: "24029",
    display: "San Martín Chalchicuautla",
  },
  {
    answer: "24030",
    display: "San Nicolás Tolentino",
  },
  {
    answer: "24031",
    display: "Santa Catarina (S.L.P.)",
  },
  {
    answer: "24032",
    display: "Santa María del Río",
  },
  {
    answer: "24033",
    display: "Santo Domingo",
  },
  {
    answer: "24034",
    display: "San Vicente Tancuayalab",
  },
  {
    answer: "24035",
    display: "Soledad de Graciano Sánchez",
  },
  {
    answer: "24036",
    display: "Tamasopo",
  },
  {
    answer: "24037",
    display: "Tamazunchale",
  },
  {
    answer: "24038",
    display: "Tampacán",
  },
  {
    answer: "24039",
    display: "Tampamolón Corona",
  },
  {
    answer: "24040",
    display: "Tamuín",
  },
  {
    answer: "24041",
    display: "Tanlajás",
  },
  {
    answer: "24042",
    display: "Tanquián de Escobedo",
  },
  {
    answer: "24043",
    display: "Tierra Nueva",
  },
  {
    answer: "24044",
    display: "Vanegas",
  },
  {
    answer: "24045",
    display: "Venado",
  },
  {
    answer: "24046",
    display: "Villa de Arriaga",
  },
  {
    answer: "24047",
    display: "Villa de Guadalupe",
  },
  {
    answer: "24048",
    display: "Villa de la Paz",
  },
  {
    answer: "24049",
    display: "Villa de Ramos",
  },
  {
    answer: "24050",
    display: "Villa de Reyes",
  },
  {
    answer: "24051",
    display: "Villa Hidalgo (S.L.P.)",
  },
  {
    answer: "24052",
    display: "Villa Juárez",
  },
  {
    answer: "24053",
    display: "Axtla de Terrazas",
  },
  {
    answer: "24054",
    display: "Xilitla",
  },
  {
    answer: "24055",
    display: "Zaragoza (S.L.P.)",
  },
  {
    answer: "24056",
    display: "Villa de Arista",
  },
  {
    answer: "24057",
    display: "Matlapa",
  },
  {
    answer: "24058",
    display: "El Naranjo",
  },
  {
    answer: "24059",
    display: "Villa de Pozos",
  },
  {
    answer: "25001",
    display: "Ahome",
  },
  {
    answer: "25002",
    display: "Angostura",
  },
  {
    answer: "25003",
    display: "Badiraguato",
  },
  {
    answer: "25004",
    display: "Concordia",
  },
  {
    answer: "25005",
    display: "Cosalá",
  },
  {
    answer: "25006",
    display: "Culiacán",
  },
  {
    answer: "25007",
    display: "Choix",
  },
  {
    answer: "25008",
    display: "Elota",
  },
  {
    answer: "25009",
    display: "Escuinapa",
  },
  {
    answer: "25010",
    display: "El Fuerte",
  },
  {
    answer: "25011",
    display: "Guasave",
  },
  {
    answer: "25012",
    display: "Mazatlán",
  },
  {
    answer: "25013",
    display: "Mocorito",
  },
  {
    answer: "25014",
    display: "Rosario (Sin.)",
  },
  {
    answer: "25015",
    display: "Salvador Alvarado",
  },
  {
    answer: "25016",
    display: "San Ignacio",
  },
  {
    answer: "25017",
    display: "Sinaloa",
  },
  {
    answer: "25018",
    display: "Navolato",
  },
  {
    answer: "25019",
    display: "Eldorado",
  },
  {
    answer: "25020",
    display: "Juan José Ríos",
  },
  {
    answer: "26001",
    display: "Aconchi",
  },
  {
    answer: "26002",
    display: "Agua Prieta",
  },
  {
    answer: "26003",
    display: "Álamos",
  },
  {
    answer: "26004",
    display: "Altar",
  },
  {
    answer: "26005",
    display: "Arivechi",
  },
  {
    answer: "26006",
    display: "Arizpe",
  },
  {
    answer: "26007",
    display: "Atil",
  },
  {
    answer: "26008",
    display: "Bacadéhuachi",
  },
  {
    answer: "26009",
    display: "Bacanora",
  },
  {
    answer: "26010",
    display: "Bacerac",
  },
  {
    answer: "26011",
    display: "Bacoachi",
  },
  {
    answer: "26012",
    display: "Bácum",
  },
  {
    answer: "26013",
    display: "Banámichi",
  },
  {
    answer: "26014",
    display: "Baviácora",
  },
  {
    answer: "26015",
    display: "Bavispe",
  },
  {
    answer: "26016",
    display: "Benjamín Hill",
  },
  {
    answer: "26017",
    display: "Caborca",
  },
  {
    answer: "26018",
    display: "Cajeme",
  },
  {
    answer: "26019",
    display: "Cananea",
  },
  {
    answer: "26020",
    display: "Carbó",
  },
  {
    answer: "26021",
    display: "La Colorada",
  },
  {
    answer: "26022",
    display: "Cucurpe",
  },
  {
    answer: "26023",
    display: "Cumpas",
  },
  {
    answer: "26024",
    display: "Divisaderos",
  },
  {
    answer: "26025",
    display: "Empalme",
  },
  {
    answer: "26026",
    display: "Etchojoa",
  },
  {
    answer: "26027",
    display: "Fronteras",
  },
  {
    answer: "26028",
    display: "Granados",
  },
  {
    answer: "26029",
    display: "Guaymas",
  },
  {
    answer: "26030",
    display: "Hermosillo",
  },
  {
    answer: "26031",
    display: "Huachinera",
  },
  {
    answer: "26032",
    display: "Huásabas",
  },
  {
    answer: "26033",
    display: "Huatabampo",
  },
  {
    answer: "26034",
    display: "Huépac",
  },
  {
    answer: "26035",
    display: "Imuris",
  },
  {
    answer: "26036",
    display: "Magdalena (Son.)",
  },
  {
    answer: "26037",
    display: "Mazatán (Son.)",
  },
  {
    answer: "26038",
    display: "Moctezuma (Son.)",
  },
  {
    answer: "26039",
    display: "Naco",
  },
  {
    answer: "26040",
    display: "Nácori Chico",
  },
  {
    answer: "26041",
    display: "Nacozari de García",
  },
  {
    answer: "26042",
    display: "Navojoa",
  },
  {
    answer: "26043",
    display: "Nogales (Son.)",
  },
  {
    answer: "26044",
    display: "Ónavas",
  },
  {
    answer: "26045",
    display: "Opodepe",
  },
  {
    answer: "26046",
    display: "Oquitoa",
  },
  {
    answer: "26047",
    display: "Pitiquito",
  },
  {
    answer: "26048",
    display: "Puerto Peñasco",
  },
  {
    answer: "26049",
    display: "Quiriego",
  },
  {
    answer: "26050",
    display: "Rayón (Son.)",
  },
  {
    answer: "26051",
    display: "Rosario (Son.)",
  },
  {
    answer: "26052",
    display: "Sahuaripa",
  },
  {
    answer: "26053",
    display: "San Felipe de Jesús",
  },
  {
    answer: "26054",
    display: "San Javier",
  },
  {
    answer: "26055",
    display: "San Luis Río Colorado",
  },
  {
    answer: "26056",
    display: "San Miguel de Horcasitas",
  },
  {
    answer: "26057",
    display: "San Pedro de la Cueva",
  },
  {
    answer: "26058",
    display: "Santa Ana (Son.)",
  },
  {
    answer: "26059",
    display: "Santa Cruz",
  },
  {
    answer: "26060",
    display: "Sáric",
  },
  {
    answer: "26061",
    display: "Soyopa",
  },
  {
    answer: "26062",
    display: "Suaqui Grande",
  },
  {
    answer: "26063",
    display: "Tepache",
  },
  {
    answer: "26064",
    display: "Trincheras",
  },
  {
    answer: "26065",
    display: "Tubutama",
  },
  {
    answer: "26066",
    display: "Ures",
  },
  {
    answer: "26067",
    display: "Villa Hidalgo (Son.)",
  },
  {
    answer: "26068",
    display: "Villa Pesqueira",
  },
  {
    answer: "26069",
    display: "Yécora",
  },
  {
    answer: "26070",
    display: "General Plutarco Elías Calles",
  },
  {
    answer: "26071",
    display: "Benito Juárez (Son.)",
  },
  {
    answer: "26072",
    display: "San Ignacio Río Muerto",
  },
  {
    answer: "27001",
    display: "Balancán",
  },
  {
    answer: "27002",
    display: "Cárdenas (Tab.)",
  },
  {
    answer: "27003",
    display: "Centla",
  },
  {
    answer: "27004",
    display: "Centro",
  },
  {
    answer: "27005",
    display: "Comalcalco",
  },
  {
    answer: "27006",
    display: "Cunduacán",
  },
  {
    answer: "27007",
    display: "Emiliano Zapata (Tab.)",
  },
  {
    answer: "27008",
    display: "Huimanguillo",
  },
  {
    answer: "27009",
    display: "Jalapa",
  },
  {
    answer: "27010",
    display: "Jalpa de Méndez",
  },
  {
    answer: "27011",
    display: "Jonuta",
  },
  {
    answer: "27012",
    display: "Macuspana",
  },
  {
    answer: "27013",
    display: "Nacajuca",
  },
  {
    answer: "27014",
    display: "Paraíso",
  },
  {
    answer: "27015",
    display: "Tacotalpa",
  },
  {
    answer: "27016",
    display: "Teapa",
  },
  {
    answer: "27017",
    display: "Tenosique",
  },
  {
    answer: "28001",
    display: "Abasolo (Tamps.)",
  },
  {
    answer: "28002",
    display: "Aldama (Tamps.)",
  },
  {
    answer: "28003",
    display: "Altamira",
  },
  {
    answer: "28004",
    display: "Antiguo Morelos",
  },
  {
    answer: "28005",
    display: "Burgos",
  },
  {
    answer: "28006",
    display: "Bustamante (Tamps.)",
  },
  {
    answer: "28007",
    display: "Camargo (Tamps.)",
  },
  {
    answer: "28008",
    display: "Casas",
  },
  {
    answer: "28009",
    display: "Ciudad Madero",
  },
  {
    answer: "28010",
    display: "Cruillas",
  },
  {
    answer: "28011",
    display: "Gómez Farías (Tamps.)",
  },
  {
    answer: "28012",
    display: "González",
  },
  {
    answer: "28013",
    display: "Güémez",
  },
  {
    answer: "28014",
    display: "Guerrero (Tamps.)",
  },
  {
    answer: "28015",
    display: "Gustavo Díaz Ordaz",
  },
  {
    answer: "28016",
    display: "Hidalgo (Tamps.)",
  },
  {
    answer: "28017",
    display: "Jaumave",
  },
  {
    answer: "28018",
    display: "Jiménez (Tamps.)",
  },
  {
    answer: "28019",
    display: "Llera",
  },
  {
    answer: "28020",
    display: "Mainero",
  },
  {
    answer: "28021",
    display: "El Mante",
  },
  {
    answer: "28022",
    display: "Matamoros (Tamps.)",
  },
  {
    answer: "28023",
    display: "Méndez",
  },
  {
    answer: "28024",
    display: "Mier",
  },
  {
    answer: "28025",
    display: "Miguel Alemán",
  },
  {
    answer: "28026",
    display: "Miquihuana",
  },
  {
    answer: "28027",
    display: "Nuevo Laredo",
  },
  {
    answer: "28028",
    display: "Nuevo Morelos",
  },
  {
    answer: "28029",
    display: "Ocampo (Tamps.)",
  },
  {
    answer: "28030",
    display: "Padilla",
  },
  {
    answer: "28031",
    display: "Palmillas",
  },
  {
    answer: "28032",
    display: "Reynosa",
  },
  {
    answer: "28033",
    display: "Río Bravo",
  },
  {
    answer: "28034",
    display: "San Carlos",
  },
  {
    answer: "28035",
    display: "San Fernando (Tamps.)",
  },
  {
    answer: "28036",
    display: "San Nicolás (Tamps.)",
  },
  {
    answer: "28037",
    display: "Soto la Marina",
  },
  {
    answer: "28038",
    display: "Tampico",
  },
  {
    answer: "28039",
    display: "Tula",
  },
  {
    answer: "28040",
    display: "Valle Hermoso",
  },
  {
    answer: "28041",
    display: "Victoria (Tamps.)",
  },
  {
    answer: "28042",
    display: "Villagrán (Tamps.)",
  },
  {
    answer: "28043",
    display: "Xicoténcatl",
  },
  {
    answer: "29001",
    display: "Amaxac de Guerrero",
  },
  {
    answer: "29002",
    display: "Apetatitlán de Antonio Carvajal",
  },
  {
    answer: "29003",
    display: "Atlangatepec",
  },
  {
    answer: "29004",
    display: "Atltzayanca",
  },
  {
    answer: "29005",
    display: "Apizaco",
  },
  {
    answer: "29006",
    display: "Calpulalpan",
  },
  {
    answer: "29007",
    display: "El Carmen Tequexquitla",
  },
  {
    answer: "29008",
    display: "Cuapiaxtla",
  },
  {
    answer: "29009",
    display: "Cuaxomulco",
  },
  {
    answer: "29010",
    display: "Chiautempan",
  },
  {
    answer: "29011",
    display: "Muñoz de Domingo Arenas",
  },
  {
    answer: "29012",
    display: "Españita",
  },
  {
    answer: "29013",
    display: "Huamantla",
  },
  {
    answer: "29014",
    display: "Hueyotlipan",
  },
  {
    answer: "29015",
    display: "Ixtacuixtla de Mariano Matamoros",
  },
  {
    answer: "29016",
    display: "Ixtenco",
  },
  {
    answer: "29017",
    display: "Mazatecochco de José María Morelos",
  },
  {
    answer: "29018",
    display: "Contla de Juan Cuamatzi",
  },
  {
    answer: "29019",
    display: "Tepetitla de Lardizábal",
  },
  {
    answer: "29020",
    display: "Sanctórum de Lázaro Cárdenas",
  },
  {
    answer: "29021",
    display: "Nanacamilpa de Mariano Arista",
  },
  {
    answer: "29022",
    display: "Acuamanala de Miguel Hidalgo",
  },
  {
    answer: "29023",
    display: "Natívitas",
  },
  {
    answer: "29024",
    display: "Panotla",
  },
  {
    answer: "29025",
    display: "San Pablo del Monte",
  },
  {
    answer: "29026",
    display: "Santa Cruz Tlaxcala",
  },
  {
    answer: "29027",
    display: "Tenancingo (Tlax.)",
  },
  {
    answer: "29028",
    display: "Teolocholco",
  },
  {
    answer: "29029",
    display: "Tepeyanco",
  },
  {
    answer: "29030",
    display: "Terrenate",
  },
  {
    answer: "29031",
    display: "Tetla de la Solidaridad",
  },
  {
    answer: "29032",
    display: "Tetlatlahuca",
  },
  {
    answer: "29033",
    display: "Tlaxcala",
  },
  {
    answer: "29034",
    display: "Tlaxco (Tlax.)",
  },
  {
    answer: "29035",
    display: "Tocatlán",
  },
  {
    answer: "29036",
    display: "Totolac",
  },
  {
    answer: "29037",
    display: "Ziltlaltépec de Trinidad Sánchez Santos",
  },
  {
    answer: "29038",
    display: "Tzompantepec",
  },
  {
    answer: "29039",
    display: "Xaloztoc",
  },
  {
    answer: "29040",
    display: "Xaltocan",
  },
  {
    answer: "29041",
    display: "Papalotla de Xicohténcatl",
  },
  {
    answer: "29042",
    display: "Xicohtzinco",
  },
  {
    answer: "29043",
    display: "Yauhquemehcan",
  },
  {
    answer: "29044",
    display: "Zacatelco",
  },
  {
    answer: "29045",
    display: "Benito Juárez (Tlax.)",
  },
  {
    answer: "29046",
    display: "Emiliano Zapata (Tlax.)",
  },
  {
    answer: "29047",
    display: "Lázaro Cárdenas (Tlax.)",
  },
  {
    answer: "29048",
    display: "La Magdalena Tlaltelulco",
  },
  {
    answer: "29049",
    display: "San Damián Texóloc",
  },
  {
    answer: "29050",
    display: "San Francisco Tetlanohcan",
  },
  {
    answer: "29051",
    display: "San Jerónimo Zacualpan",
  },
  {
    answer: "29052",
    display: "San José Teacalco",
  },
  {
    answer: "29053",
    display: "San Juan Huactzinco",
  },
  {
    answer: "29054",
    display: "San Lorenzo Axocomanitla",
  },
  {
    answer: "29055",
    display: "San Lucas Tecopilco",
  },
  {
    answer: "29056",
    display: "Santa Ana Nopalucan",
  },
  {
    answer: "29057",
    display: "Santa Apolonia Teacalco",
  },
  {
    answer: "29058",
    display: "Santa Catarina Ayometla",
  },
  {
    answer: "29059",
    display: "Santa Cruz Quilehtla",
  },
  {
    answer: "29060",
    display: "Santa Isabel Xiloxoxtla",
  },
  {
    answer: "30001",
    display: "Acajete (Ver.)",
  },
  {
    answer: "30002",
    display: "Acatlán (Ver.)",
  },
  {
    answer: "30003",
    display: "Acayucan",
  },
  {
    answer: "30004",
    display: "Actopan (Ver.)",
  },
  {
    answer: "30005",
    display: "Acula",
  },
  {
    answer: "30006",
    display: "Acultzingo",
  },
  {
    answer: "30007",
    display: "Camarón de Tejeda",
  },
  {
    answer: "30008",
    display: "Alpatláhuac",
  },
  {
    answer: "30009",
    display: "Alto Lucero de Gutiérrez Barrios",
  },
  {
    answer: "30010",
    display: "Altotonga",
  },
  {
    answer: "30011",
    display: "Alvarado",
  },
  {
    answer: "30012",
    display: "Amatitlán",
  },
  {
    answer: "30013",
    display: "Naranjos Amatlán",
  },
  {
    answer: "30014",
    display: "Amatlán de los Reyes",
  },
  {
    answer: "30015",
    display: "Angel R. Cabada",
  },
  {
    answer: "30016",
    display: "La Antigua",
  },
  {
    answer: "30017",
    display: "Apazapan",
  },
  {
    answer: "30018",
    display: "Aquila (Ver.)",
  },
  {
    answer: "30019",
    display: "Astacinga",
  },
  {
    answer: "30020",
    display: "Atlahuilco",
  },
  {
    answer: "30021",
    display: "Atoyac (Ver.)",
  },
  {
    answer: "30022",
    display: "Atzacan",
  },
  {
    answer: "30023",
    display: "Atzalan",
  },
  {
    answer: "30024",
    display: "Tlaltetela",
  },
  {
    answer: "30025",
    display: "Ayahualulco",
  },
  {
    answer: "30026",
    display: "Banderilla",
  },
  {
    answer: "30027",
    display: "Benito Juárez (Ver.)",
  },
  {
    answer: "30028",
    display: "Boca del Río",
  },
  {
    answer: "30029",
    display: "Calcahualco",
  },
  {
    answer: "30030",
    display: "Camerino Z. Mendoza",
  },
  {
    answer: "30031",
    display: "Carrillo Puerto",
  },
  {
    answer: "30032",
    display: "Catemaco",
  },
  {
    answer: "30033",
    display: "Cazones de Herrera",
  },
  {
    answer: "30034",
    display: "Cerro Azul",
  },
  {
    answer: "30035",
    display: "Citlaltépetl",
  },
  {
    answer: "30036",
    display: "Coacoatzintla",
  },
  {
    answer: "30037",
    display: "Coahuitlán",
  },
  {
    answer: "30038",
    display: "Coatepec (Ver.)",
  },
  {
    answer: "30039",
    display: "Coatzacoalcos",
  },
  {
    answer: "30040",
    display: "Coatzintla",
  },
  {
    answer: "30041",
    display: "Coetzala",
  },
  {
    answer: "30042",
    display: "Colipa",
  },
  {
    answer: "30043",
    display: "Comapa",
  },
  {
    answer: "30044",
    display: "Córdoba",
  },
  {
    answer: "30045",
    display: "Cosamaloapan de Carpio",
  },
  {
    answer: "30046",
    display: "Cosautlán de Carvajal",
  },
  {
    answer: "30047",
    display: "Coscomatepec",
  },
  {
    answer: "30048",
    display: "Cosoleacaque",
  },
  {
    answer: "30049",
    display: "Cotaxtla",
  },
  {
    answer: "30050",
    display: "Coxquihui",
  },
  {
    answer: "30051",
    display: "Coyutla",
  },
  {
    answer: "30052",
    display: "Cuichapa",
  },
  {
    answer: "30053",
    display: "Cuitláhuac",
  },
  {
    answer: "30054",
    display: "Chacaltianguis",
  },
  {
    answer: "30055",
    display: "Chalma",
  },
  {
    answer: "30056",
    display: "Chiconamel",
  },
  {
    answer: "30057",
    display: "Chiconquiaco",
  },
  {
    answer: "30058",
    display: "Chicontepec",
  },
  {
    answer: "30059",
    display: "Chinameca",
  },
  {
    answer: "30060",
    display: "Chinampa de Gorostiza",
  },
  {
    answer: "30061",
    display: "Las Choapas",
  },
  {
    answer: "30062",
    display: "Chocamán",
  },
  {
    answer: "30063",
    display: "Chontla",
  },
  {
    answer: "30064",
    display: "Chumatlán",
  },
  {
    answer: "30065",
    display: "Emiliano Zapata (Ver.)",
  },
  {
    answer: "30066",
    display: "Espinal",
  },
  {
    answer: "30067",
    display: "Filomeno Mata",
  },
  {
    answer: "30068",
    display: "Fortín",
  },
  {
    answer: "30069",
    display: "Gutiérrez Zamora",
  },
  {
    answer: "30070",
    display: "Hidalgotitlán",
  },
  {
    answer: "30071",
    display: "Huatusco",
  },
  {
    answer: "30072",
    display: "Huayacocotla",
  },
  {
    answer: "30073",
    display: "Hueyapan de Ocampo",
  },
  {
    answer: "30074",
    display: "Huiloapan de Cuauhtémoc",
  },
  {
    answer: "30075",
    display: "Ignacio de la Llave",
  },
  {
    answer: "30076",
    display: "Ilamatlán",
  },
  {
    answer: "30077",
    display: "Isla",
  },
  {
    answer: "30078",
    display: "Ixcatepec",
  },
  {
    answer: "30079",
    display: "Ixhuacán de los Reyes",
  },
  {
    answer: "30080",
    display: "Ixhuatlán del Café",
  },
  {
    answer: "30081",
    display: "Ixhuatlancillo",
  },
  {
    answer: "30082",
    display: "Ixhuatlán del Sureste",
  },
  {
    answer: "30083",
    display: "Ixhuatlán de Madero",
  },
  {
    answer: "30084",
    display: "Ixmatlahuacan",
  },
  {
    answer: "30085",
    display: "Ixtaczoquitlán",
  },
  {
    answer: "30086",
    display: "Jalacingo",
  },
  {
    answer: "30087",
    display: "Xalapa",
  },
  {
    answer: "30088",
    display: "Jalcomulco",
  },
  {
    answer: "30089",
    display: "Jáltipan",
  },
  {
    answer: "30090",
    display: "Jamapa",
  },
  {
    answer: "30091",
    display: "Jesús Carranza",
  },
  {
    answer: "30092",
    display: "Xico",
  },
  {
    answer: "30093",
    display: "Jilotepec (Ver.)",
  },
  {
    answer: "30094",
    display: "Juan Rodríguez Clara",
  },
  {
    answer: "30095",
    display: "Juchique de Ferrer",
  },
  {
    answer: "30096",
    display: "Landero y Coss",
  },
  {
    answer: "30097",
    display: "Lerdo de Tejada",
  },
  {
    answer: "30098",
    display: "Magdalena (Ver.)",
  },
  {
    answer: "30099",
    display: "Maltrata",
  },
  {
    answer: "30100",
    display: "Manlio Fabio Altamirano",
  },
  {
    answer: "30101",
    display: "Mariano Escobedo",
  },
  {
    answer: "30102",
    display: "Martínez de la Torre",
  },
  {
    answer: "30103",
    display: "Mecatlán",
  },
  {
    answer: "30104",
    display: "Mecayapan",
  },
  {
    answer: "30105",
    display: "Medellín de Bravo",
  },
  {
    answer: "30106",
    display: "Miahuatlán",
  },
  {
    answer: "30107",
    display: "Las Minas",
  },
  {
    answer: "30108",
    display: "Minatitlán (Ver.)",
  },
  {
    answer: "30109",
    display: "Misantla",
  },
  {
    answer: "30110",
    display: "Mixtla de Altamirano",
  },
  {
    answer: "30111",
    display: "Moloacán",
  },
  {
    answer: "30112",
    display: "Naolinco",
  },
  {
    answer: "30113",
    display: "Naranjal",
  },
  {
    answer: "30114",
    display: "Nautla",
  },
  {
    answer: "30115",
    display: "Nogales (Ver.)",
  },
  {
    answer: "30116",
    display: "Oluta",
  },
  {
    answer: "30117",
    display: "Omealca",
  },
  {
    answer: "30118",
    display: "Orizaba",
  },
  {
    answer: "30119",
    display: "Otatitlán",
  },
  {
    answer: "30120",
    display: "Oteapan",
  },
  {
    answer: "30121",
    display: "Ozuluama de Mascareñas",
  },
  {
    answer: "30122",
    display: "Pajapan",
  },
  {
    answer: "30123",
    display: "Pánuco (Ver.)",
  },
  {
    answer: "30124",
    display: "Papantla",
  },
  {
    answer: "30125",
    display: "Paso del Macho",
  },
  {
    answer: "30126",
    display: "Paso de Ovejas",
  },
  {
    answer: "30127",
    display: "La Perla",
  },
  {
    answer: "30128",
    display: "Perote",
  },
  {
    answer: "30129",
    display: "Platón Sánchez",
  },
  {
    answer: "30130",
    display: "Playa Vicente",
  },
  {
    answer: "30131",
    display: "Poza Rica de Hidalgo",
  },
  {
    answer: "30132",
    display: "Las Vigas de Ramírez",
  },
  {
    answer: "30133",
    display: "Pueblo Viejo",
  },
  {
    answer: "30134",
    display: "Puente Nacional",
  },
  {
    answer: "30135",
    display: "Rafael Delgado",
  },
  {
    answer: "30136",
    display: "Rafael Lucio",
  },
  {
    answer: "30137",
    display: "Los Reyes (Ver.)",
  },
  {
    answer: "30138",
    display: "Río Blanco",
  },
  {
    answer: "30139",
    display: "Saltabarranca",
  },
  {
    answer: "30140",
    display: "San Andrés Tenejapan",
  },
  {
    answer: "30141",
    display: "San Andrés Tuxtla",
  },
  {
    answer: "30142",
    display: "San Juan Evangelista",
  },
  {
    answer: "30143",
    display: "Santiago Tuxtla",
  },
  {
    answer: "30144",
    display: "Sayula de Alemán",
  },
  {
    answer: "30145",
    display: "Soconusco",
  },
  {
    answer: "30146",
    display: "Sochiapa",
  },
  {
    answer: "30147",
    display: "Soledad Atzompa",
  },
  {
    answer: "30148",
    display: "Soledad de Doblado",
  },
  {
    answer: "30149",
    display: "Soteapan",
  },
  {
    answer: "30150",
    display: "Tamalín",
  },
  {
    answer: "30151",
    display: "Tamiahua",
  },
  {
    answer: "30152",
    display: "Tampico Alto",
  },
  {
    answer: "30153",
    display: "Tancoco",
  },
  {
    answer: "30154",
    display: "Tantima",
  },
  {
    answer: "30155",
    display: "Tantoyuca",
  },
  {
    answer: "30156",
    display: "Tatatila",
  },
  {
    answer: "30157",
    display: "Castillo de Teayo",
  },
  {
    answer: "30158",
    display: "Tecolutla",
  },
  {
    answer: "30159",
    display: "Tehuipango",
  },
  {
    answer: "30160",
    display: "Álamo Temapache",
  },
  {
    answer: "30161",
    display: "Tempoal",
  },
  {
    answer: "30162",
    display: "Tenampa",
  },
  {
    answer: "30163",
    display: "Tenochtitlán",
  },
  {
    answer: "30164",
    display: "Teocelo",
  },
  {
    answer: "30165",
    display: "Tepatlaxco",
  },
  {
    answer: "30166",
    display: "Tepetlán",
  },
  {
    answer: "30167",
    display: "Tepetzintla (Ver.)",
  },
  {
    answer: "30168",
    display: "Tequila (Ver.)",
  },
  {
    answer: "30169",
    display: "José Azueta",
  },
  {
    answer: "30170",
    display: "Texcatepec",
  },
  {
    answer: "30171",
    display: "Texhuacán",
  },
  {
    answer: "30172",
    display: "Texistepec",
  },
  {
    answer: "30173",
    display: "Tezonapa",
  },
  {
    answer: "30174",
    display: "Tierra Blanca (Ver.)",
  },
  {
    answer: "30175",
    display: "Tihuatlán",
  },
  {
    answer: "30176",
    display: "Tlacojalpan",
  },
  {
    answer: "30177",
    display: "Tlacolulan",
  },
  {
    answer: "30178",
    display: "Tlacotalpan",
  },
  {
    answer: "30179",
    display: "Tlacotepec de Mejía",
  },
  {
    answer: "30180",
    display: "Tlachichilco",
  },
  {
    answer: "30181",
    display: "Tlalixcoyan",
  },
  {
    answer: "30182",
    display: "Tlalnelhuayocan",
  },
  {
    answer: "30183",
    display: "Tlapacoyan",
  },
  {
    answer: "30184",
    display: "Tlaquilpa",
  },
  {
    answer: "30185",
    display: "Tlilapan",
  },
  {
    answer: "30186",
    display: "Tomatlán (Ver.)",
  },
  {
    answer: "30187",
    display: "Tonayán",
  },
  {
    answer: "30188",
    display: "Totutla",
  },
  {
    answer: "30189",
    display: "Tuxpan (Ver.)",
  },
  {
    answer: "30190",
    display: "Tuxtilla",
  },
  {
    answer: "30191",
    display: "Ursulo Galván",
  },
  {
    answer: "30192",
    display: "Vega de Alatorre",
  },
  {
    answer: "30193",
    display: "Veracruz",
  },
  {
    answer: "30194",
    display: "Villa Aldama",
  },
  {
    answer: "30195",
    display: "Xoxocotla (Ver.)",
  },
  {
    answer: "30196",
    display: "Yanga",
  },
  {
    answer: "30197",
    display: "Yecuatla",
  },
  {
    answer: "30198",
    display: "Zacualpan (Ver.)",
  },
  {
    answer: "30199",
    display: "Zaragoza (Ver.)",
  },
  {
    answer: "30200",
    display: "Zentla",
  },
  {
    answer: "30201",
    display: "Zongolica",
  },
  {
    answer: "30202",
    display: "Zontecomatlán de López y Fuentes",
  },
  {
    answer: "30203",
    display: "Zozocolco de Hidalgo",
  },
  {
    answer: "30204",
    display: "Agua Dulce",
  },
  {
    answer: "30205",
    display: "El Higo",
  },
  {
    answer: "30206",
    display: "Nanchital de Lázaro Cárdenas del Río",
  },
  {
    answer: "30207",
    display: "Tres Valles",
  },
  {
    answer: "30208",
    display: "Carlos A. Carrillo",
  },
  {
    answer: "30209",
    display: "Tatahuicapan de Juárez",
  },
  {
    answer: "30210",
    display: "Uxpanapa",
  },
  {
    answer: "30211",
    display: "San Rafael",
  },
  {
    answer: "30212",
    display: "Santiago Sochiapan",
  },
  {
    answer: "31001",
    display: "Abalá",
  },
  {
    answer: "31002",
    display: "Acanceh",
  },
  {
    answer: "31003",
    display: "Akil",
  },
  {
    answer: "31004",
    display: "Baca",
  },
  {
    answer: "31005",
    display: "Bokobá",
  },
  {
    answer: "31006",
    display: "Buctzotz",
  },
  {
    answer: "31007",
    display: "Cacalchén",
  },
  {
    answer: "31008",
    display: "Calotmul",
  },
  {
    answer: "31009",
    display: "Cansahcab",
  },
  {
    answer: "31010",
    display: "Cantamayec",
  },
  {
    answer: "31011",
    display: "Celestún",
  },
  {
    answer: "31012",
    display: "Cenotillo",
  },
  {
    answer: "31013",
    display: "Conkal",
  },
  {
    answer: "31014",
    display: "Cuncunul",
  },
  {
    answer: "31015",
    display: "Cuzamá",
  },
  {
    answer: "31016",
    display: "Chacsinkín",
  },
  {
    answer: "31017",
    display: "Chankom",
  },
  {
    answer: "31018",
    display: "Chapab",
  },
  {
    answer: "31019",
    display: "Chemax",
  },
  {
    answer: "31020",
    display: "Chicxulub Pueblo",
  },
  {
    answer: "31021",
    display: "Chichimilá",
  },
  {
    answer: "31022",
    display: "Chikindzonot",
  },
  {
    answer: "31023",
    display: "Chocholá",
  },
  {
    answer: "31024",
    display: "Chumayel",
  },
  {
    answer: "31025",
    display: "Dzan",
  },
  {
    answer: "31026",
    display: "Dzemul",
  },
  {
    answer: "31027",
    display: "Dzidzantún",
  },
  {
    answer: "31028",
    display: "Dzilam de Bravo",
  },
  {
    answer: "31029",
    display: "Dzilam González",
  },
  {
    answer: "31030",
    display: "Dzitás",
  },
  {
    answer: "31031",
    display: "Dzoncauich",
  },
  {
    answer: "31032",
    display: "Espita",
  },
  {
    answer: "31033",
    display: "Halachó",
  },
  {
    answer: "31034",
    display: "Hocabá",
  },
  {
    answer: "31035",
    display: "Hoctún",
  },
  {
    answer: "31036",
    display: "Homún",
  },
  {
    answer: "31037",
    display: "Huhí",
  },
  {
    answer: "31038",
    display: "Hunucmá",
  },
  {
    answer: "31039",
    display: "Ixil",
  },
  {
    answer: "31040",
    display: "Izamal",
  },
  {
    answer: "31041",
    display: "Kanasín",
  },
  {
    answer: "31042",
    display: "Kantunil",
  },
  {
    answer: "31043",
    display: "Kaua",
  },
  {
    answer: "31044",
    display: "Kinchil",
  },
  {
    answer: "31045",
    display: "Kopomá",
  },
  {
    answer: "31046",
    display: "Mama",
  },
  {
    answer: "31047",
    display: "Maní",
  },
  {
    answer: "31048",
    display: "Maxcanú",
  },
  {
    answer: "31049",
    display: "Mayapán",
  },
  {
    answer: "31050",
    display: "Mérida",
  },
  {
    answer: "31051",
    display: "Mocochá",
  },
  {
    answer: "31052",
    display: "Motul",
  },
  {
    answer: "31053",
    display: "Muna",
  },
  {
    answer: "31054",
    display: "Muxupip",
  },
  {
    answer: "31055",
    display: "Opichén",
  },
  {
    answer: "31056",
    display: "Oxkutzcab",
  },
  {
    answer: "31057",
    display: "Panabá",
  },
  {
    answer: "31058",
    display: "Peto",
  },
  {
    answer: "31059",
    display: "Progreso (Yuc.)",
  },
  {
    answer: "31060",
    display: "Quintana Roo",
  },
  {
    answer: "31061",
    display: "Río Lagartos",
  },
  {
    answer: "31062",
    display: "Sacalum",
  },
  {
    answer: "31063",
    display: "Samahil",
  },
  {
    answer: "31064",
    display: "Sanahcat",
  },
  {
    answer: "31065",
    display: "San Felipe (Yuc.)",
  },
  {
    answer: "31066",
    display: "Santa Elena",
  },
  {
    answer: "31067",
    display: "Seyé",
  },
  {
    answer: "31068",
    display: "Sinanché",
  },
  {
    answer: "31069",
    display: "Sotuta",
  },
  {
    answer: "31070",
    display: "Sucilá",
  },
  {
    answer: "31071",
    display: "Sudzal",
  },
  {
    answer: "31072",
    display: "Suma",
  },
  {
    answer: "31073",
    display: "Tahdziú",
  },
  {
    answer: "31074",
    display: "Tahmek",
  },
  {
    answer: "31075",
    display: "Teabo",
  },
  {
    answer: "31076",
    display: "Tecoh",
  },
  {
    answer: "31077",
    display: "Tekal de Venegas",
  },
  {
    answer: "31078",
    display: "Tekantó",
  },
  {
    answer: "31079",
    display: "Tekax",
  },
  {
    answer: "31080",
    display: "Tekit",
  },
  {
    answer: "31081",
    display: "Tekom",
  },
  {
    answer: "31082",
    display: "Telchac Pueblo",
  },
  {
    answer: "31083",
    display: "Telchac Puerto",
  },
  {
    answer: "31084",
    display: "Temax",
  },
  {
    answer: "31085",
    display: "Temozón",
  },
  {
    answer: "31086",
    display: "Tepakán",
  },
  {
    answer: "31087",
    display: "Tetiz",
  },
  {
    answer: "31088",
    display: "Teya",
  },
  {
    answer: "31089",
    display: "Ticul",
  },
  {
    answer: "31090",
    display: "Timucuy",
  },
  {
    answer: "31091",
    display: "Tinum",
  },
  {
    answer: "31092",
    display: "Tixcacalcupul",
  },
  {
    answer: "31093",
    display: "Tixkokob",
  },
  {
    answer: "31094",
    display: "Tixméhuac",
  },
  {
    answer: "31095",
    display: "Tixpéhual",
  },
  {
    answer: "31096",
    display: "Tizimín",
  },
  {
    answer: "31097",
    display: "Tunkás",
  },
  {
    answer: "31098",
    display: "Tzucacab",
  },
  {
    answer: "31099",
    display: "Uayma",
  },
  {
    answer: "31100",
    display: "Ucú",
  },
  {
    answer: "31101",
    display: "Umán",
  },
  {
    answer: "31102",
    display: "Valladolid",
  },
  {
    answer: "31103",
    display: "Xocchel",
  },
  {
    answer: "31104",
    display: "Yaxcabá",
  },
  {
    answer: "31105",
    display: "Yaxkukul",
  },
  {
    answer: "31106",
    display: "Yobaín",
  },
  {
    answer: "32001",
    display: "Apozol",
  },
  {
    answer: "32002",
    display: "Apulco",
  },
  {
    answer: "32003",
    display: "Atolinga",
  },
  {
    answer: "32004",
    display: "Benito Juárez (Zac.)",
  },
  {
    answer: "32005",
    display: "Calera",
  },
  {
    answer: "32006",
    display: "Cañitas de Felipe Pescador",
  },
  {
    answer: "32007",
    display: "Concepción del Oro",
  },
  {
    answer: "32008",
    display: "Cuauhtémoc (Zac.)",
  },
  {
    answer: "32009",
    display: "Chalchihuites",
  },
  {
    answer: "32010",
    display: "Fresnillo",
  },
  {
    answer: "32011",
    display: "Trinidad García de la Cadena",
  },
  {
    answer: "32012",
    display: "Genaro Codina",
  },
  {
    answer: "32013",
    display: "General Enrique Estrada",
  },
  {
    answer: "32014",
    display: "General Francisco R. Murguía",
  },
  {
    answer: "32015",
    display: "El Plateado de Joaquín Amaro",
  },
  {
    answer: "32016",
    display: "General Pánfilo Natera",
  },
  {
    answer: "32017",
    display: "Guadalupe (Zac.)",
  },
  {
    answer: "32018",
    display: "Huanusco",
  },
  {
    answer: "32019",
    display: "Jalpa",
  },
  {
    answer: "32020",
    display: "Jerez",
  },
  {
    answer: "32021",
    display: "Jiménez del Teul",
  },
  {
    answer: "32022",
    display: "Juan Aldama",
  },
  {
    answer: "32023",
    display: "Juchipila",
  },
  {
    answer: "32024",
    display: "Loreto (Zac.)",
  },
  {
    answer: "32025",
    display: "Luis Moya",
  },
  {
    answer: "32026",
    display: "Mazapil",
  },
  {
    answer: "32027",
    display: "Melchor Ocampo (Zac.)",
  },
  {
    answer: "32028",
    display: "Mezquital del Oro",
  },
  {
    answer: "32029",
    display: "Miguel Auza",
  },
  {
    answer: "32030",
    display: "Momax",
  },
  {
    answer: "32031",
    display: "Monte Escobedo",
  },
  {
    answer: "32032",
    display: "Morelos (Zac.)",
  },
  {
    answer: "32033",
    display: "Moyahua de Estrada",
  },
  {
    answer: "32034",
    display: "Nochistlán de Mejía",
  },
  {
    answer: "32035",
    display: "Noria de Ángeles",
  },
  {
    answer: "32036",
    display: "Ojocaliente",
  },
  {
    answer: "32037",
    display: "Pánuco (Zac.)",
  },
  {
    answer: "32038",
    display: "Pinos",
  },
  {
    answer: "32039",
    display: "Río Grande",
  },
  {
    answer: "32040",
    display: "Sain Alto",
  },
  {
    answer: "32041",
    display: "El Salvador",
  },
  {
    answer: "32042",
    display: "Sombrerete",
  },
  {
    answer: "32043",
    display: "Susticacán",
  },
  {
    answer: "32044",
    display: "Tabasco",
  },
  {
    answer: "32045",
    display: "Tepechitlán",
  },
  {
    answer: "32046",
    display: "Tepetongo",
  },
  {
    answer: "32047",
    display: "Teúl de González Ortega",
  },
  {
    answer: "32048",
    display: "Tlaltenango de Sánchez Román",
  },
  {
    answer: "32049",
    display: "Valparaíso",
  },
  {
    answer: "32050",
    display: "Vetagrande",
  },
  {
    answer: "32051",
    display: "Villa de Cos",
  },
  {
    answer: "32052",
    display: "Villa García",
  },
  {
    answer: "32053",
    display: "Villa González Ortega",
  },
  {
    answer: "32054",
    display: "Villa Hidalgo (Zac.)",
  },
  {
    answer: "32055",
    display: "Villanueva",
  },
  {
    answer: "32056",
    display: "Zacatecas",
  },
  {
    answer: "32057",
    display: "Trancoso",
  },
  {
    answer: "32058",
    display: "Santa María de la Paz",
  },
];

/**
 * Quiz configuration for all Mexican municipalities, grouped by state.
 */
export const mexicoMunicipalitiesQuiz: FeatureQuiz = {
  id: "mexico-municipalities",
  name: "Mexico Municipalities",
  description: `Learn all ${MEXICO_MUNICIPALITY_QUESTIONS.length} municipalities of Mexico, with filters that let you practice municipalities from any desired state or combination of states.`,

  kind: "feature",
  mapId: "mexico-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "state_id",
        label: "State",
        valueType: "string",
        valueLabels: MEXICO_STATE_NAMES_BY_ID,
      },
    ],
  },

  questions: MEXICO_MUNICIPALITY_QUESTIONS,
};
