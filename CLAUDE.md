# CLAUDE.md

## Project Overview

This is **Planet Detroit's Michigan Air Permit Violation Dashboard** — a data journalism project that tracks air permit violations issued by Michigan's Department of Environment, Great Lakes and Energy (EGLE). It combines automated PDF scraping/parsing with an interactive map-based dashboard.

The project has two main parts:
1. **Python data pipeline** — scrapes, parses, and geocodes violation notice PDFs from EGLE's database
2. **Static frontend dashboard** — interactive Mapbox map + recent violations feed, served as a static site via GitHub Pages

**Status**: As of 2025, the dashboard stopped receiving daily updates due to EGLE data management changes. It now displays historical data (2018–2024) and directs users to EGLE's MIEnviro Portal for current violations.

## Repository Structure

```
├── EGLE-AQD-violation-parser-mapbuilder.py  # Main automation script (751 lines)
├── sheets-updater.py                         # Google Sheets sync script
├── index.html                                # Dashboard single-page app
├── docs/
│   ├── dashboard.js                          # Frontend JS (Mapbox map, interactivity)
│   ├── violation-map.css                     # All styles (1,558 lines)
│   └── EGLE-AQD-source-directory-geocoded.csv # Facility directory with geocoded locations
├── output/
│   ├── EGLE-AQD-Violation-Notices-2018-Present.csv  # All parsed violations (~9 MB)
│   ├── violation-map-data.csv                # Map data with violations by year
│   ├── violation-map-geo-data.js             # GeoJSON for map (loaded as JS global)
│   ├── recent-violations.js                  # 12 most recent violations (JS global)
│   ├── violation-count-by-source.csv         # Summary by facility
│   └── report-*.csv                          # Automation reports
├── archive/                                  # ~200+ downloaded violation notice PDFs
├── img/                                      # Image assets (SVG, PNG)
├── .github/workflows/
│   └── scrape.yml                            # GitHub Actions daily automation
└── README.md                                 # Project documentation and methodology
```

## Tech Stack

### Backend / Data Pipeline
- **Python 3.9**
- Key libraries: `pandas`, `pdfplumber`, `requests`, `beautifulsoup4`, `regex`, `pygsheets`, `wget`, `pytz`
- No package manager lockfile — dependencies installed directly via `pip install` in CI

### Frontend
- **Vanilla HTML/CSS/JS** — no build system, no framework
- **Mapbox GL JS v2.15.0** — interactive map
- **jQuery 2.1.1** — DOM manipulation
- **Turf.js 5.1.5** — geospatial calculations
- **Datawrapper** — embedded data table visualization
- **Google Fonts** — Inter, Bodoni Moda, Playfair Display, Asap, Gelasio, Source Code Pro

### CI/CD
- **GitHub Actions** — daily cron at 3:30 AM UTC (`scrape.yml`)
- Workflow: run parser → auto-commit data → sync to Google Sheets

## Data Pipeline

```
GitHub Actions Trigger (daily 3:30 AM UTC)
  → EGLE-AQD-violation-parser-mapbuilder.py
    1. Fetches 90-day document list from external scraper repo
    2. Identifies new violation notices not yet parsed
    3. Downloads PDFs to archive/ via wget
    4. Parses PDFs with pdfplumber (tables, regex patterns, full text)
    5. Geocodes facilities using directory CSV
    6. Generates output CSVs and JS data files
  → Auto-commit and push
  → sheets-updater.py (syncs to Google Sheets)
```

If no new violation notices are found, the parser exits early (`sys.exit()`).

### PDF Parsing Strategy
- Extracts first-page text for location detection (regex: `"located at [address], Michigan"`)
- Extracts tables from first 2 pages for structured violation data
- Identifies standard violations via regex (e.g., "Failure to submit [YEAR] air pollution report")
- Falls back to "Please see document" when parsing fails
- Tracks quality via flags: `pdf_parsing_error`, `empty_pdf_error`, `table_error`

## Frontend Architecture

The dashboard is a **single-page static site** (`index.html`) that loads data via `<script>` tags:
- `output/violation-map-geo-data.js` → sets global `var infoData` (GeoJSON FeatureCollection)
- `output/recent-violations.js` → sets global `var violationData` (array of 12 violations)

### Key Frontend Features
- Interactive map with facility markers sized by violation count
- Color-coded by EPA classification (Megasite/Major/Synthetic Minor/True Minor)
- Click facility for details, violations list, and PDF links
- EPA class dropdown filter
- Deep linking via URL params (`?srn=A2809`)
- "Load More" for recent violations feed
- Construction modal tracked via `localStorage`

### Color Scheme (EPA Classifications)
| Class | Color |
|-------|-------|
| Megasite | `#8F0043` |
| Major | `#FF0037` |
| Synthetic Minor | `#FF5400` |
| True Minor | `#FFBD00` |

## Key Data Models

### Violation Notice CSV Fields
`srn`, `date`, `date_str`, `year`, `facility_name`, `facility_name_title`, `epa_class`, `epa_class_full`, `comment_list`, `comment_list_html`, `county`, `city`, `location_clean`, `address_full`, `lat`, `long`, `geometry`, `doc_url`, `vn_map_url`, `full_text`

### GeoJSON Feature Properties
`srn`, `date`, `date_str`, `facility_name`, `comment_list`, `comment_list_html`, `address`, `lat`, `long`, `doc_url`, `county`, `group_name`, `group_id`

## Development Workflow

### Running Locally
1. **Frontend**: Open `index.html` directly in a browser or serve via any static file server. No build step required.
2. **Data pipeline**: Run `python EGLE-AQD-violation-parser-mapbuilder.py` (requires Python 3.9+ and dependencies installed via `pip install requests beautifulsoup4 pandas tqdm regex pdfplumber pytz wget pygsheets`)

### No Testing Framework
There is no automated test suite. Validation is done through:
- Report CSVs (`output/report-parser.csv`, `output/report-map-update.csv`) tracking daily runs
- Error flags on parsed records (`pdf_parsing_error`, `empty_pdf_error`, `table_error`)

### No Linting/Formatting
No linting or formatting tools (eslint, prettier, flake8, black, etc.) are configured.

## Environment & Secrets

- **No `.env` file** — secrets are managed via GitHub Actions secrets
- `PYG_SHEETS_AUTH` — base64-encoded Google Sheets service account JSON (used in `sheets-updater.py`)
- **Mapbox access token** — hardcoded in `docs/dashboard.js`
- **Google Analytics** — GA ID `G-P6JQ77WXSM` in `index.html`

## Conventions & Patterns

- **Data files in `output/`** are auto-generated — do not edit them manually
- **PDFs in `archive/`** are downloaded by the scraper — do not add manually
- **JS data files** use global variables (`var infoData`, `var violationData`) loaded via script tags
- **CSV is the primary data interchange format** — pandas reads/writes throughout the pipeline
- **Git commits from CI** follow the pattern: `"Latest data: <timestamp>"`
- **The `.gitignore`** only covers Jupyter notebook checkpoints and macOS files — all data files and PDFs are tracked in git

## Important Notes for AI Assistants

1. **Large data files are committed to git** — the output/ and archive/ directories contain large CSVs and PDFs that are version-controlled. Be mindful of file sizes when making changes.
2. **No build step** — changes to HTML/CSS/JS are immediately reflected. No transpilation or bundling.
3. **External data dependency** — the parser fetches from `https://raw.githubusercontent.com/srjouppi/michigan-egle-database-auto-scraper/main/output/EGLE-AQD-document-dataset-90days.csv`. This external repo must be accessible for the pipeline to work.
4. **The facility directory** (`docs/EGLE-AQD-source-directory-geocoded.csv`) is the canonical source for facility names, addresses, EPA classifications, and coordinates.
5. **The frontend is served from the repo root** — `index.html` is at the repo root, not in a `docs/` or `public/` folder. GitHub Pages likely serves from the root.
6. **Python script exits early** if no new violations are found — this is expected behavior, not an error.
