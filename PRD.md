# PRD — Indonesia Fire Watch Data Scraping

## 1. Product summary

Indonesia Fire Watch collects, stores, and publishes nationwide satellite fire-detection data for website map and reports.

Primary source: NASA FIRMS.

Google Maps Wildfires layer is visual product reference only. Do not scrape Google Maps Wildfires layer or use it as fire-coordinate source.

Website may link each point to Google Maps coordinate view:

```text
https://www.google.com/maps/search/?api=1&query=<latitude>,<longitude>
```

## 2. Problem

Users need one map showing recent fire detections across all 38 Indonesian provinces, plus latest reporting time and evidence details. Google Maps mobile can show wildfire markers, but does not provide stable public API for full historical Indonesia fire-point ingestion.

Raw satellite detections can be duplicated across sensors, lack province classification, and become too numerous for browser map if all history loads at once.

## 3. Goals

1. Collect all available Indonesia fire/hotspot coordinates from NASA FIRMS.
2. Refresh data at least hourly.
3. Keep raw source files, normalized observations, ingestion records, and historical data.
4. Enrich every observation with detection time, source-report time, sensor, confidence, FRP, province classification, severity estimate, and source URL.
5. Group nearby/repeated observations into map-friendly satellite-detected incident areas.
6. Provide API data for website map, filters, reports, and point detail sheet.
7. Support future official status sources: SIPONGI/KLHK, BNPB, BPBD.
8. Preserve source attribution and data limitations in every public output.

## 4. Non-goals

1. Do not scrape Google Maps Wildfires layer.
2. Do not claim satellite hotspot equals confirmed forest fire.
3. Do not claim estimated area equals official fire perimeter or burned area.
4. Do not build wildfire prediction, ML classification, evacuation routing, or emergency dispatch.
5. Do not require Google Maps JavaScript API.
6. Do not scrape official agency sources before their public API/export, terms, license, and schema are verified.

## 5. Users

### Public website visitor

Needs current map, fire-marker details, province and province-group filters, severity filter, last update, and source caveat.

### Report user

Needs downloadable CSV/GeoJSON, daily summary, historical query, counts by province/province-group/severity, and source timestamps.

### Project administrator

Needs ingestion status, rejected-row reason, data freshness status, source health, and ability to rerun refresh safely.

## 6. Data-source policy

### 6.1 NASA FIRMS — required primary source

Use NASA FIRMS API for all fire-point coordinates.

Default sensors:

```text
VIIRS_SNPP_NRT
VIIRS_NOAA20_NRT
```

Default country scope:

```text
Indonesia
```

Default time window:

```text
Last 1 day
```

Required request pattern:

```text
https://firms.modaps.eosdis.nasa.gov/api/area/csv/<FIRMS_MAP_KEY>/<SENSOR>/Indonesia/<DAYS>
```

Requirements:

- `FIRMS_MAP_KEY` remains secret.
- Use finite HTTP timeout: 30 seconds.
- Reject response with HTTP error, empty body, or missing mandatory CSV columns.
- Store unmodified raw CSV privately.
- Never show `FIRMS_MAP_KEY` in logs, errors, output, commits, tests, screenshots, or docs.
- Preserve source URL, sensor, source report timestamp, and original row fields.

### 6.2 Google Search — optional secondary evidence

Reference repository:

```text
https://github.com/scrapfly/scrapfly-scrapers/tree/main/google-scraper
```

Optional use:

- Collect public news/context links for queries such as `kebakaran hutan Indonesia <province>`.
- Collect title, URL, snippet, query, capture time, and `source_type="google_search"`.
- Store output privately under `data/private/context/`.

Requirements:

- Use Scrapfly only when `SCRAPFLY_KEY` exists.
- Skip collector successfully when key absent.
- Do not use search results to create, move, delete, or confirm FIRMS coordinates.
- Do not expose scraped content as authoritative fire status.

### 6.3 Google Maps — visual reference and outbound link only

Supplied image reference has terrain map, pink fire markers, severity labels, relative update time, fire-area legend, and bottom detail sheet.

Allowed:

- Copy interaction concept and general layout without copying Google branding, map tiles, logo, controls, code, or data.
- Open external coordinate link in Google Maps.
- Optionally collect emergency-agency place metadata through Scrapfly later, separate from fire detection records.

Forbidden:

- Scraping Google Maps Wildfires layer for primary data.
- Calling Google Maps marker label or fire-area status official project data.
- Using Google Maps tiles without proper license/API agreement.

### 6.4 Official Indonesian sources — future enrichment

Candidate sources:

```text
SIPONGI / KLHK
BNPB
BPBD
Manggala Agni
BMKG
```

Before ingestion, verify all items:

1. Public API, export, RSS, or published feed exists.
2. Terms and license allow collection and republishing.
3. Update frequency and historical availability known.
4. Source schema captured in fixture.
5. Stable report ID, timestamp, status, location, and source URL available.

When approved, match official report to satellite incident only when both conditions match:

```text
Distance <= 10 km
Time difference <= 24 hours
```

Matched status values:

```text
satellite_detected
officially_reported
officially_resolved
```

No match means preserve each record separately. Do not force match.

## 7. Source-data fields

Expected FIRMS fields:

```text
latitude
longitude
bright_ti4
scan
track
acq_date
acq_time
satellite
confidence
version
bright_ti5
frp
daynight
```

Mandatory input fields:

```text
latitude
longitude
acq_date
acq_time
satellite
confidence
```

Optional input fields:

```text
bright_ti4
bright_ti5
scan
track
frp
daynight
version
```

Reject row when:

- latitude outside `-90..90`;
- longitude outside `-180..180`;
- acquisition date/time invalid;
- satellite blank;
- coordinate outside Indonesia boundary;
- row cannot produce stable ID.

Do not silently coerce malformed required values.

## 8. Normalized observation contract

One satellite detection equals one `fire_observation`.

```json
{
  "id": "firs_<20-sha256-hex>",
  "longitude": 111.7182,
  "latitude": -2.6701,
  "observed_at_utc": "2026-10-19T02:10:00Z",
  "last_source_report_at_utc": "2026-10-19T03:00:00Z",
  "sensor": "VIIRS_SNPP_NRT",
  "satellite": "N",
  "confidence": "nominal",
  "frp_mw": 42.8,
  "bright_ti4_k": 342.5,
  "scan_km": 0.38,
  "track_km": 0.36,
  "daynight": "D",
  "province": "Kalimantan Tengah",
  "province_group": "Pulau Kalimantan",
  "province_capital": "Palangkaraya",
  "classification": "Kalimantan Tengah",
  "severity": "high",
  "severity_reason": "FRP 42.8 MW; confidence nominal",
  "status": "satellite_detected",
  "source": "NASA FIRMS",
  "source_url": "https://firms.modaps.eosdis.nasa.gov/",
  "source_kind": "satellite_estimate"
}
```

Stable ID input, exact order:

```text
NASA FIRMS|<sensor>|<satellite>|<acq_date>|<acq_time>|<latitude to 4 decimals>|<longitude to 4 decimals>
```

ID algorithm:

```text
sha256(input).hexdigest()[:20]
```

Prefix ID with `firs_`.

## 9. Geographic enrichment

### 9.1 Indonesia boundary filter

Use packaged, versioned Indonesia boundary polygon in CRS `EPSG:4326`.

Only point geometries inside or touching Indonesia boundary can enter public output.

### 9.2 Province classification — required 38 provinces

Use packaged Indonesia 2022/2023 province polygons in `EPSG:4326`. The dataset must contain exactly 38 polygon features and use official `PROVINSI` names.

Classify each accepted observation by polygon containment. Public output must include:

```text
province
province_group
province_capital
classification
```

`classification` equals `province`. `province_group` and `province_capital` come only from approved metadata below.

| Province group | Province | Capital |
|---|---|---|
| Pulau Sumatera | Aceh | Banda Aceh |
| Pulau Sumatera | Sumatera Utara | Medan |
| Pulau Sumatera | Sumatera Barat | Padang |
| Pulau Sumatera | Riau | Pekanbaru |
| Pulau Sumatera | Kepulauan Riau | Tanjung Pinang |
| Pulau Sumatera | Jambi | Jambi |
| Pulau Sumatera | Bengkulu | Bengkulu |
| Pulau Sumatera | Sumatera Selatan | Palembang |
| Pulau Sumatera | Kepulauan Bangka Belitung | Pangkal Pinang |
| Pulau Sumatera | Lampung | Bandar Lampung |
| Pulau Jawa | DKI Jakarta | Jakarta |
| Pulau Jawa | Banten | Serang |
| Pulau Jawa | Jawa Barat | Bandung |
| Pulau Jawa | Jawa Tengah | Semarang |
| Pulau Jawa | Daerah Istimewa Yogyakarta | Yogyakarta |
| Pulau Jawa | Jawa Timur | Surabaya |
| Kepulauan Nusa Tenggara & Bali | Bali | Denpasar |
| Kepulauan Nusa Tenggara & Bali | Nusa Tenggara Barat | Mataram |
| Kepulauan Nusa Tenggara & Bali | Nusa Tenggara Timur | Kupang |
| Pulau Kalimantan | Kalimantan Barat | Pontianak |
| Pulau Kalimantan | Kalimantan Tengah | Palangkaraya |
| Pulau Kalimantan | Kalimantan Selatan | Banjarbaru |
| Pulau Kalimantan | Kalimantan Timur | Samarinda |
| Pulau Kalimantan | Kalimantan Utara | Tanjung Selor |
| Pulau Sulawesi | Sulawesi Utara | Manado |
| Pulau Sulawesi | Gorontalo | Gorontalo |
| Pulau Sulawesi | Sulawesi Tengah | Palu |
| Pulau Sulawesi | Sulawesi Barat | Mamuju |
| Pulau Sulawesi | Sulawesi Selatan | Makassar |
| Pulau Sulawesi | Sulawesi Tenggara | Kendari |
| Kepulauan Maluku & Pulau Papua | Maluku | Ambon |
| Kepulauan Maluku & Pulau Papua | Maluku Utara | Sofifi |
| Kepulauan Maluku & Pulau Papua | Papua | Jayapura |
| Kepulauan Maluku & Pulau Papua | Papua Barat | Manokwari |
| Kepulauan Maluku & Pulau Papua | Papua Selatan | Merauke |
| Kepulauan Maluku & Pulau Papua | Papua Tengah | Nabire |
| Kepulauan Maluku & Pulau Papua | Papua Pegunungan | Jayawijaya |
| Kepulauan Maluku & Pulau Papua | Papua Barat Daya | Sorong |

Rules:

- Do not classify point by province-center coordinate or nearest capital.
- Do not assign nearest province when a point does not intersect a province polygon.
- Indonesia-boundary point with no province-polygon match must use `province="unknown"`, `province_group="unknown"`, and `province_capital=null`.
- Record boundary dataset URL, license, retrieval date, CRS, property name `PROVINSI`, and the 38-feature count in README.
- Test representative coordinates in every province group and assert metadata dictionary covers exactly all 38 province names.

## 10. Severity calculation

Severity is project-derived satellite estimate. It is not Google Maps severity, official alert level, confirmed fire, containment status, or burned area.

Default rules:

| Confidence | FRP | Severity |
|---|---:|---|
| `low` | any | `low` |
| `nominal` | `< 25 MW` | `moderate` |
| `nominal` | `25–99.99 MW` | `high` |
| `nominal` | `>= 100 MW` | `severe` |
| `high` | `>= 25 MW` | `severe` |
| any non-low | missing | `moderate` |

Required reason examples:

```text
FRP 42.8 MW; confidence nominal
FRP unavailable; satellite detection requires review
Confidence low; satellite detection requires review
```

Severity levels use these public labels:

```text
Low satellite detection
Moderate satellite fire detection
High satellite fire detection
Severe satellite fire detection
```

## 11. Incident clustering

One `fire_incident` groups nearby/repeated observations for lower-zoom map and report cards.

Default matching thresholds:

```text
Distance: 5 km
Time window: 24 hours
```

Algorithm:

1. Project point coordinates to metric CRS suitable for Indonesia.
2. Link two observations only if distance and time thresholds both pass.
3. Generate connected components from all links.
4. One component becomes one incident.
5. Severity equals highest member severity.
6. Centroid equals component spatial centroid.
7. Use convex hull footprint when component has multiple spatially distinct points.
8. Buffer single-point incident by 1 km for visual-only footprint.
9. Calculate `estimated_area_km2` from metric footprint.

Incident contract:

```json
{
  "id": "inc_20261019_<stable-id>",
  "centroid": {"longitude": 111.72, "latitude": -2.67},
  "started_at_utc": "2026-10-19T00:40:00Z",
  "last_detected_at_utc": "2026-10-19T02:10:00Z",
  "last_source_report_at_utc": "2026-10-19T03:00:00Z",
  "observation_count": 8,
  "max_frp_mw": 219.3,
  "severity": "severe",
  "estimated_area_km2": 8.04,
  "estimated_area_method": "convex_hull_buffered_1km",
  "province": "Kalimantan Tengah",
  "province_group": "Pulau Kalimantan",
  "province_capital": "Palangkaraya",
  "status": "satellite_detected",
  "source": "NASA FIRMS"
}
```

Public caveat, required exact meaning:

```text
Estimated satellite detection area. Not confirmed fire perimeter or burned area.
```

## 12. Storage and retention

Use PostgreSQL + PostGIS for production/query data.

Required tables:

```text
ingestion_runs
fire_observations
fire_incidents
official_reports             # future phase
incident_official_matches    # future phase
```

### 12.1 `ingestion_runs`

Required columns:

```text
id UUID primary key
started_at_utc timestamptz not null
completed_at_utc timestamptz
status running|success|failed
last_source_report_at_utc timestamptz
detail jsonb not null
```

### 12.2 `fire_observations`

Required columns:

```text
id text primary key
run_id UUID foreign key
observed_at_utc timestamptz not null
last_source_report_at_utc timestamptz not null
sensor text not null
satellite text not null
confidence text not null
frp_mw numeric
bright_ti4_k numeric
daynight char(1)
province text not null
province_group text not null
province_capital text
severity text not null
severity_reason text not null
status text not null
source text not null
source_url text not null
geom geometry(Point, 4326) not null
raw jsonb not null
```

### 12.3 `fire_incidents`

Required columns:

```text
id text primary key
run_id UUID foreign key
started_at_utc timestamptz not null
last_detected_at_utc timestamptz not null
last_source_report_at_utc timestamptz not null
observation_count integer not null
max_frp_mw numeric
severity text not null
estimated_area_km2 numeric
estimated_area_method text not null
province text not null
province_group text not null
province_capital text
status text not null
source text not null
centroid geometry(Point, 4326) not null
footprint geometry(Geometry, 4326)
observation_ids jsonb not null
```

Indexes required:

```text
GiST fire_observations.geom
GiST fire_incidents.centroid
B-tree fire_observations.observed_at_utc
B-tree fire_incidents.last_detected_at_utc
B-tree province
B-tree province_group
B-tree severity
B-tree status
```

Retention policy v1:

- Keep normalized observations permanently.
- Keep raw files for 90 days.
- Keep ingestion manifests permanently.
- Purge raw files only after successful normalized database commit.
- Backup database daily before production launch.

## 13. Raw, private, and public files

```text
data/raw/firms-YYYY-MM-DD-<sensor>.csv
data/private/run_manifest_latest.json
data/private/context/google_search_latest.json
data/private/context/google_maps_places_latest.json
data/public/fire_points_latest.geojson
data/public/fire_points_latest.csv
data/public/fire_summary_latest.json
```

Rules:

- `data/raw/` and `data/private/` must not be published.
- Generated data files must not be committed unless explicit reproducible sample fixture.
- CSV must use semicolon delimiter and UTF-8 BOM:

```python
df.to_csv(path, sep=";", encoding="utf-8-sig", index=False)
```

- GeoJSON coordinate order is always `[longitude, latitude]`.
- All timestamps are ISO 8601 UTC, ending `Z`.

## 14. Public API requirements

Base path:

```text
/api/v1
```

### 14.1 Health

```text
GET /health
```

Response:

```json
{"status":"ok"}
```

### 14.2 Metadata

```text
GET /api/v1/metadata
```

Response fields:

```text
generated_at_utc
last_source_report_at_utc
freshness_status
latest_successful_run_id
source
source_url
```

Freshness:

```text
current: last source report <= 8 hours old
stale: last source report > 8 hours old
unknown: no successful source report
```

### 14.3 Incident map query

```text
GET /api/v1/incidents?west=<float>&south=<float>&east=<float>&north=<float>&from=<ISO-UTC>&to=<ISO-UTC>&province=<name>&province_group=<name>&severity=<level>&limit=<int>
```

Requirements:

- bbox and date range mandatory.
- Maximum date range: 31 days.
- Default limit: 500.
- Maximum limit: 1000.
- Reject invalid bbox, invalid time range, or limit above maximum with HTTP 422.
- Return GeoJSON FeatureCollection.
- Add `Cache-Control: public, max-age=300`.
- Never return full Indonesia history in one response.

### 14.4 Incident detail

```text
GET /api/v1/incidents/{incident_id}
```

Returns full incident, member-observation count, source fields, status, caveat, and official match if available.

### 14.5 Observation map query

```text
GET /api/v1/observations?west=<float>&south=<float>&east=<float>&north=<float>&from=<ISO-UTC>&to=<ISO-UTC>&province=<name>&province_group=<name>&severity=<level>&limit=<int>
```

Use only for high zoom. Same validation and limits as incidents.

## 15. Website data requirements

Website map behavior based on supplied Google Maps reference:

1. Start centered on Indonesia extent.
2. Use properly licensed terrain/base map. Do not use Google map tiles/logo.
3. At zoom below 7, render incident centroid markers.
4. At zoom 7 or higher, render observation markers.
5. Render severity marker with pink/red circle, black flame symbol, and readable text label.
6. Render label such as `Severe fire` only as project satellite severity label.
7. Render relative update text from `last_source_report_at_utc`, e.g. `Updated 6 hours ago`.
8. Opening marker shows dark mobile bottom sheet / desktop side panel.
9. Detail panel shows:

```text
Severity label
Detected at
Last source report
Latitude and longitude
Sensor
Satellite
Confidence
FRP
Province
Province group
Province capital
Observation count for incidents
Estimated detection area for incidents
Severity reason
Status
Source: NASA FIRMS
Source link
Open in Google Maps
Satellite-derived estimate caveat
```

10. Legend shows severity colors and `Estimated satellite detection area` caveat.
11. Add filters:

```text
Last 24 hours
Last 7 days
Custom date range
Province
Province group
Severity
```

12. Store filters in URL parameters.
13. Add accessible location control using browser geolocation.
14. On geolocation denial/unavailable, show readable error and keep map usable.
15. On API error, preserve legend/caveat and show retry control.
16. On stale metadata, show `Data may be delayed`, never `Live` or `Current`.

## 16. Ingestion flow

```text
1. Create ingestion run status=running.
2. Fetch both required FIRMS sensors for configured day window.
3. Save exact raw responses privately.
4. Parse CSV rows.
5. Validate required fields and values.
6. Filter Indonesia boundary.
7. Create stable observation IDs.
8. Deduplicate in current batch.
9. Assign one of 38 provinces through polygon containment; derive province group and capital from approved metadata.
10. Calculate satellite severity.
11. Upsert observations transactionally.
12. Build/update incidents.
13. Commit transaction.
14. Complete ingestion run with counts and latest source time.
15. Generate public latest GeoJSON, JSON summary, and CSV.
16. Optionally collect Google Search context only when SCRAPFLY_KEY exists.
17. On failure, rollback observation/incident write; mark run failed; preserve reason without secrets.
```

Idempotency requirement:

- Ingesting same source data twice must not create duplicate observations.
- Existing observation may update only when incoming `last_source_report_at_utc` is newer.

## 17. Scheduling

Required initial schedule:

```text
Hourly
```

Required command:

```bash
uv run firewatch refresh --days 1
```

GitHub Actions requirements:

- `workflow_dispatch` enabled.
- Hourly cron enabled.
- Concurrency group `firewatch-refresh`.
- `cancel-in-progress: false`.
- Secrets only through repository/hosting secret store:

```text
FIRMS_MAP_KEY
DATABASE_URL
SCRAPFLY_KEY        # optional
```

- No secrets printed.
- Failure alert target remains configuration until owner specifies email/Slack/Discord.

## 18. Security and compliance

1. Keep `.env`, credentials, raw private source files, private context, and database dumps out of Git.
2. Validate all API query values before database query.
3. Use parameterized SQL only.
4. Bound bbox, date window, result count, and response size.
5. Do not expose raw API keys through errors, manifests, frontend environment, or client bundle.
6. Keep Google/Scrapfly use optional and compliant with applicable terms.
7. Attribute NASA FIRMS in API, CSV, GeoJSON metadata, website panel, and report.
8. Do not make emergency/evacuation claims.

## 19. Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | System fetches FIRMS Indonesia data for both configured VIIRS sensors. |
| FR-02 | System stores exact raw CSV privately before parsing. |
| FR-03 | System rejects invalid and out-of-Indonesia records. |
| FR-04 | System creates deterministic observation IDs and deduplicates. |
| FR-05 | System classifies accepted records into one of 38 provinces using polygon containment, then adds province group, capital, severity, source, and timestamps. |
| FR-06 | System keeps observation history across refreshes. |
| FR-07 | System creates nearby/time-related incident clusters. |
| FR-08 | System exports current GeoJSON, JSON summary, and semicolon/BOM CSV. |
| FR-09 | API serves bounded viewport/time queries for incidents and observations. |
| FR-10 | API exposes source freshness. |
| FR-11 | Website can display marker, detail sheet, filters, severity legend, and caveat. |
| FR-12 | Website uses Google Maps only as outbound coordinate link. |
| FR-13 | Optional Google Search context skips safely without key. |
| FR-14 | Future official-source records remain separate until valid time/distance match. |
| FR-15 | Scheduled refresh prevents overlapping runs. |

## 20. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| AC-01 | `firewatch refresh --days 1` writes successful ingestion run and public files after valid FIRMS response. |
| AC-02 | Every public observation contains coordinates, detection time, source-report time, sensor, confidence, FRP when supplied, province, province group, province capital, source, and severity. |
| AC-03 | Duplicate source row appears once in database and public latest output. |
| AC-04 | Point outside Indonesia boundary never appears in public output. |
| AC-05 | Province metadata dictionary covers exactly the required 38 province names, each with its specified group and capital. |
| AC-06 | Point intersecting no province polygon exports `province="unknown"`, `province_group="unknown"`, and `province_capital=null`; no nearest-province fallback is used. |
| AC-07 | Same refresh rerun does not increase observation count for identical rows. |
| AC-08 | Two nearby points inside 5 km/24 h form one incident; points outside either threshold do not. |
| AC-09 | Incident detail labels estimated area as estimate, not confirmed perimeter/burned area. |
| AC-10 | `/api/v1/incidents` rejects date range over 31 days and limit over 1000 with HTTP 422. |
| AC-11 | `/api/v1/metadata` returns source timestamp and correct fresh/stale status. |
| AC-12 | CSV starts UTF-8 BOM and uses semicolon delimiter. |
| AC-13 | GeoJSON is valid FeatureCollection with `[longitude, latitude]` coordinates. |
| AC-14 | Website marker opens panel with all required detection/source fields. |
| AC-15 | Website Google Maps link uses exact coordinate URL and no Google data is ingested. |
| AC-16 | No test requires API key, network access, Google, FIRMS, or Scrapfly. |
| AC-17 | Live smoke test validates real FIRMS result and records actual count/timestamp without inventing values. |

## 21. Test strategy

### Unit tests

Use fixtures, fake HTTP transports, fake Scrapfly clients, fixed time, and test PostGIS database.

Required suites:

```text
tests/test_config.py
tests/test_models.py
tests/test_firms.py
tests/test_normalize.py
tests/test_geography.py
tests/test_severity.py
tests/test_incidents.py
tests/test_repository.py
tests/test_export.py
tests/test_api.py
tests/test_cli.py
web/src/test/app.test.tsx
web/src/test/fire-map.test.tsx
```

Run:

```bash
uv run pytest -q
cd web && npm test -- --run
npm run build
```

Expected:

```text
All tests pass.
Frontend build exits 0.
```

### Database integration

```bash
docker compose up -d postgres
uv run pytest tests/test_db_schema.py tests/test_repository.py -q
docker compose down -v
```

Expected:

```text
All database tests pass.
Container volume removed after test.
```

### Live smoke test

Only with local secret configuration:

```bash
export FIRMS_MAP_KEY='replace-with-local-key'
uv run firewatch refresh --days 1
```

Validate:

```bash
uv run python -c "import json; d=json.load(open('data/public/fire_points_latest.geojson', encoding='utf-8')); assert d['type']=='FeatureCollection'; assert all(-180<=f['geometry']['coordinates'][0]<=180 and -90<=f['geometry']['coordinates'][1]<=90 for f in d['features']); print(len(d['features']), 'features valid')"
uv run python -c "from pathlib import Path; b=Path('data/public/fire_points_latest.csv').read_bytes(); assert b.startswith(b'\xef\xbb\xbf') and b';' in b.splitlines()[0]; print('CSV BOM and semicolon verified')"
uv run python -c "import json; d=json.load(open('data/public/fire_summary_latest.json', encoding='utf-8')); assert d['last_source_report_at_utc']; assert d['generated_at_utc']; print(d['last_source_report_at_utc'])"
```

Expected:

```text
All commands exit 0.
Actual output count and timestamp recorded in release note.
```

## 22. Delivery phases

### Phase 1 — Core ingestion

- Project config, secrets, fixtures.
- FIRMS fetch, raw storage, normalize, deduplicate.
- 38-province polygon classification and province metadata enrichment.
- Severity calculation.
- GeoJSON/JSON/CSV exports.

### Phase 2 — Historical reporting

- PostGIS schema and migrations.
- Transactional observation history.
- Incident clustering.
- Ingestion runs and freshness metadata.

### Phase 3 — API

- Health, metadata, incident, observation endpoints.
- Bbox/time/filter limits.
- Caching and pagination.

### Phase 4 — Website integration

- React/Leaflet map.
- Google-style visual interaction without Google assets/data.
- Marker details, filter state, source links, Google Maps outbound link.
- Performance and accessibility checks.

### Phase 5 — Operations

- Hourly scheduler.
- CI test suite.
- Hosting, backup, failure notification.

### Phase 6 — Official-source enrichment

- Research/approve SIPONGI/KLHK, BNPB, BPBD source.
- Build adapter and fixture.
- Store official records.
- Deterministic time/distance incident matching.

## 23. Open decisions

1. Final production database host and backup target.
2. Data retention after first year: permanent versus archive policy.
3. Province-boundary source update and review cadence after new national administrative divisions.
4. Official source priority: SIPONGI/KLHK, BNPB, BPBD, Manggala Agni, BMKG.
5. Is forest/peat mask required before launch? Required if product wording says “forest fires” rather than “satellite fire detections.”
6. Production failure-notification destination.
7. Frontend hosting and API hosting domain.
8. Whether user report downloads require authentication.

## 24. Required public wording

Use one of these phrases near all map/report fire data:

```text
Satellite-derived fire detections
Satellite thermal hotspot detections
```

Required caveat:

```text
Satellite-derived estimate. Not confirmed fire perimeter, burned area, or official emergency status.
```

Do not label all records `confirmed fire`, `forest fire`, `active wildfire`, or `fire area` unless approved official evidence or forest-land classification supports it.
