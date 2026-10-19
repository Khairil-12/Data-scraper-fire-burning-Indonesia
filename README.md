# Indonesia Fire Watch

Indonesia-wide satellite fire-detection pipeline and map client.

Primary coordinate source: NASA FIRMS VIIRS NRT. The project labels records as satellite-derived thermal hotspot detections, not confirmed forest fires, official emergency status, burned area, or fire perimeter.

## Features

- Fetches Indonesia detections from `VIIRS_SNPP_NRT` and `VIIRS_NOAA20_NRT`.
- Preserves raw FIRMS CSV privately.
- Validates coordinates, acquisition time, mandatory fields, and duplicate IDs.
- Classifies detections through current 38-province polygons.
- Adds province group and capital metadata.
- Exports GeoJSON, JSON summary, and Excel-friendly CSV.
- Includes React + Leaflet map client with severity markers, detail panel, source link, and Google Maps coordinate link.

## Province groups

| Group | Provinces |
|---|---:|
| Pulau Sumatera | 10 |
| Pulau Jawa | 6 |
| Kepulauan Nusa Tenggara & Bali | 3 |
| Pulau Kalimantan | 5 |
| Pulau Sulawesi | 6 |
| Kepulauan Maluku & Pulau Papua | 8 |

All 38 provinces have group and capital metadata.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ for web client
- NASA FIRMS `MAP_KEY`

Request a free FIRMS key from https://firms.modaps.eosdis.nasa.gov/api/

## Setup

```bash
git clone https://github.com/Khairil-12/Data-scraper-for-fire-burning-Indonesia.git
cd Data-scraper-for-fire-burning-Indonesia
uv sync --extra dev
cd web && npm install && cd ..
```

Set key in current shell. Never commit it or paste it into source files.

```bash
export FIRMS_MAP_KEY='your-firms-map-key'
```

Windows PowerShell:

```powershell
$env:FIRMS_MAP_KEY='your-firms-map-key'
```

## Fetch current data

```bash
uv run firewatch refresh --days 1
```

FIRMS allows `--days` from 1 through 5.

```bash
uv run firewatch refresh --days 5
```

Default sensors:

```text
VIIRS_SNPP_NRT
VIIRS_NOAA20_NRT
```

## Output

Generated files stay untracked:

```text
data/raw/firms-YYYY-MM-DD-<sensor>.csv
data/private/run_manifest_latest.json
data/public/fire_points_latest.geojson
data/public/fire_points_latest.csv
data/public/fire_summary_latest.json
```

`fire_points_latest.csv` uses UTF-8 BOM and semicolon delimiter for Excel.

Every GeoJSON feature contains:

```text
id
latitude
longitude
observed_at_utc
last_source_report_at_utc
sensor
satellite
confidence
frp_mw
province
province_group
province_capital
severity
severity_reason
source
source_url
```

GeoJSON coordinate order is always `[longitude, latitude]`.

## Data limits

- FIRMS detection can be delayed, obscured by clouds, duplicated across sensors, or caused by non-wildfire heat sources.
- Province uses polygon containment. Detections inside Indonesia but outside available province polygons remain `unknown`; project does not guess nearest province.
- Severity is project-derived from FIRMS FRP and confidence. It is not a Google Maps or government severity level.
- Google Maps is only an external coordinate link. This project does not scrape Google Maps Wildfires layer.

## Test

Python:

```bash
uv run pytest -q
```

Web client:

```bash
cd web
npm test -- --run
npm run build
```

## Web client

Set API base URL when backend API exists:

```bash
cd web
VITE_FIREWATCH_API_URL='http://127.0.0.1:8000' npm run build
```

Current web client expects:

```text
GET /api/v1/metadata
GET /api/v1/incidents
```

## Project structure

```text
src/firewatch/       Python ingestion, validation, classification, export
scripts/             Reference-data acquisition scripts
data/reference/      Versioned Indonesia boundary datasets
tests/               Python test suite
web/                 React + Leaflet map client
PRD.md               Full product requirements
```

## Attribution

Fire coordinates and source fields: NASA FIRMS.

Indonesia province boundary references are stored in `data/reference/`. See `PRD.md` for source policy and technical requirements.
