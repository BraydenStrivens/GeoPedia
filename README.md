# GeoPedia

GeoPedia is an interactive geography learning website built around map-based quizzes. It is designed to help users learn geographic information that is useful for GeoGuessr, including countries, towns, administrative divisions, telephone codes, postal codes, flags, and other regional systems.

A major focus of GeoPedia is making large geographic datasets easier to learn. Quizzes can be divided into smaller groups using geographic properties or manual feature selection, allowing users to practice manageable subsets before attempting a full quiz.

The project is currently under active development.

## Features

- Interactive maps powered by MapLibre GL JS
- Feature-based and town-based geography quizzes
- Randomized quiz questions
- Correct and incorrect answer tracking
- Visual answer feedback directly on the map
- Progressive feature coloring based on completion and accuracy
- Support for geographic features containing multiple quiz answers
- Normal and Hard quiz modes
- Configurable map shading, borders, labels, and answer feedback
- Show Answers mode with map-based answer labels
- Quiz skipping, restarting, and stopping
- Property-based quiz groups
- Manual feature selection for creating custom quiz subsets
- Saved custom quiz groups
- Country-based quiz organization
- Global country quizzes
- Town quizzes with distance-based scoring
- Country flags, silhouettes, and geographic data generated from reusable source data
- Responsive map labels and contextual place names

## Current Quizzes

### Global

- Country Names
- Country Flags
- Country Capitals
- Calling Codes

### United States

- States
- State Abbreviations
- State Flags
- Area Codes
- 1-Digit ZIP Code Prefixes
- 2-Digit ZIP Code Prefixes
- 3-Digit ZIP Code Prefixes
- Counties
- Towns

Town quizzes are also generated for supported countries using GeoPedia's global town dataset.

More countries, geographic datasets, and quiz types are planned.

## Quiz System

GeoPedia uses a configuration-driven quiz system that allows many quizzes to share the same underlying map and gameplay infrastructure.

Feature quizzes define information such as:

- Map dataset
- Answer property
- Answer type
- Available questions
- Property-based grouping options
- Quiz-specific base-map visibility

A geographic feature can represent either a single quiz answer or multiple answers.

For example, many U.S. telephone area codes are overlays covering the same geographic region. GeoPedia can treat each area code as an individual question while allowing a single geographic feature to represent multiple valid answers.

As questions for a feature are answered, its map color changes based on both completion and accuracy.

### Quiz Groups

Large quizzes can be divided into smaller subsets instead of requiring the entire dataset to be learned at once.

GeoPedia supports:

- Full quizzes
- Property-based groups
- Manual feature selection
- Saved custom groups

Property groups can use geographic metadata such as regions, while manual selection allows individual map features to be included or excluded.

### Quiz Modes

Feature quizzes support multiple ways of practicing geography.

**Normal mode** provides the standard map presentation and visual assistance.

**Hard mode** reduces geographic assistance to make identification more challenging.

Additional display settings allow supported quizzes to control map shading, borders, labels, and incorrect-selection feedback.

## Town Quizzes

GeoPedia includes a separate quiz system for learning towns.

Town quizzes use geographic coordinates rather than polygon selection. The user is shown a town and attempts to identify its location on the map.

Answers are scored using geographic distance between the guessed and actual locations. Country-specific scoring tolerances are generated from the spatial distribution of towns so that scoring can account for differences in country size and settlement distribution.

Town datasets and quiz configurations are generated from GeoPedia's processed global town data.

## Map Architecture

GeoPedia uses reusable map configurations to separate geographic datasets from runtime map behavior.

Each map is created through a configuration factory that applies shared defaults while allowing individual maps to override only the properties that differ.

Map configurations define information such as:

- GeoJSON source
- Feature properties
- Initial camera position
- Base map style
- Fill appearance
- Border appearance
- Hover behavior
- MapLibre feature IDs
- Answer-label density settings

Shared defaults provide consistent feature colors, borders, and hover behavior without requiring those values to be repeated in every map configuration.

Quiz-specific base-map visibility is kept in the quiz configuration because labels or administrative boundaries that are harmless for one quiz may reveal the answers to another quiz using the same map.

This architecture allows multiple quizzes to reuse the same geographic map while changing quiz behavior independently.

## Tech Stack

### Application

- Next.js
- React
- TypeScript
- Tailwind CSS

### Mapping

- MapLibre GL JS
- MapTiler
- GeoJSON
- PMTiles

### Geographic Data Processing

- TypeScript
- Python
- Shapely
- PyShp

GeoPedia uses processing and generation scripts to transform external geographic datasets into optimized runtime data and generated quiz configurations.

## Geographic Data Processing

Raw geographic datasets are processed before being used by the application.

Processing includes operations such as:

- Geometry simplification
- Polygon grouping
- Geometry dissolving
- Metadata extraction
- Geographic feature normalization
- ZIP prefix generation
- Country-data generation
- Country GeoJSON generation
- Town-data processing
- Quiz question generation
- Flag and silhouette asset preparation

The data pipeline separates raw source data, intermediate processing data, and final browser-ready assets.

```text
Raw external data
        ↓
Intermediate processing data
        ↓
Runtime data in public/data
```

Intermediate data is retained only when another processing stage requires it.

## Running Locally

Clone the repository:

```bash
git clone https://github.com/BraydenStrivens/GeoPedia.git
cd GeoPedia
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Then open:

```text
http://localhost:3000
```

### Validation

Run ESLint:

```bash
npm run lint
```

Run the TypeScript compiler without emitting build files:

```bash
npx tsc --noEmit
```

## Environment Variables

GeoPedia uses MapTiler for its base map.

Create a `.env.local` file in the project root and provide your MapTiler API key:

```env
NEXT_PUBLIC_MAPTILER_KEY=your_key_here
```

## Data Sources

GeoPedia uses geographic information derived from multiple public datasets.

Current U.S. geographic data includes sources such as U.S. Census Bureau Cartographic Boundary files and ZIP Code Tabulation Areas (ZCTAs).

Global country and town data is processed into standardized GeoJSON, PMTiles, generated country metadata, quiz configurations, and supporting assets before being consumed by the application.

Processed runtime datasets are optimized for interactive browser maps while retaining the geographic detail needed for map-based learning.

## Development Status

GeoPedia is in active development.

Development has progressed beyond the initial U.S.-only quiz prototype into a reusable global geography platform. The project now includes global country infrastructure, town quizzes, configurable quiz groups, multiple quiz modes, generated geographic data, and shared map and quiz systems.

Current development continues to focus on expanding country coverage, adding new geographic quiz types, improving the learning and grouping systems, and refining the reusable map infrastructure.

## License

A project license has not yet been selected.
