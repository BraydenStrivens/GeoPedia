# GeoPedia

GeoPedia is an interactive geography learning website built around map-based quizzes. It is designed to help users learn geographic information that is useful for GeoGuessr, including administrative divisions, postal codes, telephone codes, and other regional systems.

The project is currently under active development.

## Features

- Interactive maps powered by MapLibre GL
- Map-based geography quizzes
- Randomized quiz questions
- Correct and incorrect answer tracking
- Visual answer feedback directly on the map
- Support for features containing multiple quiz answers
- Progressive coloring based on completion and accuracy
- Hover feedback for unanswered map features
- Quiz skipping, restarting, and stopping
- Multiple map configurations for different geographic datasets
- Country-based quiz organization

## Current Quizzes

### United States

- States
- State abbreviations
- Area codes
- 1-digit ZIP code prefixes
- 2-digit ZIP code prefixes
- 3-digit ZIP code prefixes
- Counties

More countries and quiz types are planned.

## Quiz System

GeoPedia uses a configuration-driven quiz and map system. Different quizzes can use different geographic datasets while sharing the same underlying map and quiz logic.

A geographic feature can represent either a single quiz answer or multiple answers.

For example, many US telephone area codes are overlays that cover exactly the same geographic region. GeoPedia treats each area code as an individual question while allowing a single map feature to contain multiple answers.

As questions for a feature are answered, its color progressively changes based on both completion and accuracy.

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

### Geographic Data Processing

- Python
- Shapely
- PyShp

Python processing scripts convert source geographic datasets into simplified GeoJSON files suitable for interactive browser maps.

## Geographic Data Processing

Raw geographic datasets are processed before being used by GeoPedia.

Processing includes operations such as:

- Geometry simplification
- Polygon grouping
- Geometry dissolving
- Metadata extraction
- Geographic feature normalization
- ZIP prefix generation
- Quiz question generation

This allows large source datasets to be reduced significantly while retaining enough geographic detail for map-based quizzes.

## Project Structure

```text
src/
├── components/
├── countries/
├── maps/
│   ├── country/
│   └── hooks/
├── quiz/
│   └── quizzes/
└── types/

scripts/
├── Geographic data processing scripts
└── Quiz generation scripts

public/
└── data/
    └── Processed GeoJSON and other application data

data/
└── raw/
    └── Raw geographic source data
```

Raw geographic source files are not intended to be committed to the repository.

## Map Architecture

Maps are defined using reusable `MapConfig` objects that specify information such as:

- GeoJSON source
- Feature properties
- Initial map position
- Map style
- Fill and border appearance
- Hover behavior
- Click behavior
- MapLibre feature IDs

This allows new geographic quizzes to be added without creating a completely new map implementation for each dataset.

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

## Environment Variables

GeoPedia uses MapTiler for its base map.

Create a `.env.local` file in the project root and provide your MapTiler API key:

```env
NEXT_PUBLIC_MAPTILER_KEY=your_key_here
```

Do not commit `.env.local` or API keys to the repository.

## Data Sources

Geographic data used by GeoPedia includes data derived from public geographic datasets such as those provided by the U.S. Census Bureau.

Current US datasets include Census Cartographic Boundary files and ZIP Code Tabulation Areas (ZCTAs).

Processed versions of these datasets are optimized for use with MapLibre.

## Development Status

GeoPedia is in active development.

The initial implementation has focused on building the reusable map and quiz architecture and creating the first collection of United States quizzes.

Future development will expand the quiz system to additional countries and geographic systems.

## License

A project license has not yet been selected.
