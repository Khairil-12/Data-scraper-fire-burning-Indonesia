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

## 25. Data accuracy implementation roadmap

# Data accuracy roadmap — ordered implementation

## Goal

Improve Indonesia Fire Watch data correctness in strict dependency order: accurate 38-province geography, forest/peat classification, source-quality preservation, cross-sensor linkage, finalized history, persistence-based incidents, approved official context, and refresh-quality reporting.

## Current context / assumptions

- Repository: `D:\Kuliah\Hackathon\MIA\DataScraper`.
- Existing pipeline fetches NASA FIRMS `VIIRS_SNPP_NRT` and `VIIRS_NOAA20_NRT`, normalizes rows, uses a 38-province GeoJSON file, and exports latest GeoJSON/CSV/summary.
- Current public contract already exports `province`, `province_group`, `province_capital`, `classification`, `confidence`, `frp_mw`, `bright_ti4_k`, `sensor`, `satellite`, and timestamps.
- A 5-day live refresh produced 57,138 records and 861 `unknown` province records. All 38 provinces had at least one detection. Unknown points are not automatically assigned to nearest province.
- Current `Hotspot.island` field is legacy and is incorrectly populated with province name. Remove it when changing data model; public exports must never overload `island` with province value.
- Current source client validates HTTP/empty response but does not enforce FIRMS schema drift policy, raw-response checksum lineage, durable historical deduplication, or land/coastal uncertainty classes.
- NASA FIRMS remains primary coordinate authority. Its points are satellite thermal detections, not confirmed forest-fire boundaries, burned area, or official incident reports.
- KLHK/BIG ArcGIS land-cover services are candidates for forest/peat classification. Verify endpoint fields, terms, query limits, and reproducible snapshot/version before making them a production source.
- SIPONGI/KLHK, BNPB, BPBD, and Manggala Agni are not approved automatic incident feeds until documented API/export access, license/terms, schema, cadence, stable identifier, and source URL are verified.
- Generated raw, private, and public runtime data remains ignored by Git. Never commit `FIRMS_MAP_KEY`.

## Architecture / proposed approach

Keep raw FIRMS observations immutable and preserve all source attributes. Add explicit derived fields in pure transformations: province classification, land-cover class, cross-sensor linkage, processing level, and persistence/incident summary. Every derived value must carry a method/version/source field so later changes never overwrite or disguise raw detection facts.

Implement one vertical slice at a time: write one failing test, run it red, add minimum production code, run green, execute full suite, inspect output artifact, and commit only that completed slice. Do not build PostGIS/API/UI work in this roadmap unless a task explicitly requires a data-storage migration.

## Ordered step-by-step tasks

### 0. Freeze baseline and add data-quality fixture contract

Files:

- `tests/fixtures/firms_quality_sample.csv`
- `tests/fixtures/firms_cross_sensor_sample.csv`
- `tests/fixtures/firms_persistence_sample.csv`
- `tests/test_quality_contract.py`
- `README.md`

1. Create fixtures only. Include documented FIRMS columns:

```text
latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
```

`firms_quality_sample.csv` must include nominal/high/low confidence, day/night, missing FRP, two valid provinces, one point inside Indonesia ADM0 but outside ADM1 polygon, and one invalid coordinate.

`firms_cross_sensor_sample.csv` must include one SNPP/NOAA-20 pair within 375 m and 30 minutes plus one pair outside distance/time threshold.

`firms_persistence_sample.csv` must include same-location detections across three timestamps plus one spatially separate detection.

2. Write failing `tests/test_quality_contract.py` with exact required export keys:

```python
REQUIRED_PUBLIC_KEYS = {
    "id", "latitude", "longitude", "observed_at_utc",
    "sensor", "satellite", "confidence", "frp_mw", "bright_ti4_k",
    "scan_km", "track_km", "daynight", "version",
    "province", "province_group", "province_capital",
    "land_cover_class", "land_cover_source", "land_cover_version",
    "dedupe_group_id", "processing_level", "severity", "source",
}
```

3. Run red:

```bash
uv run pytest tests/test_quality_contract.py -q
```

Expected: fail because export keys/fixtures do not yet satisfy full contract.

4. Do not implement the listed fields yet. Commit fixture and contract only:

```bash
git add tests/fixtures tests/test_quality_contract.py README.md && git commit -m "test: define fire data quality contract"
```

Done when: baseline fixtures exist, test fails only for fields intentionally added by subsequent tasks, and commit contains no production changes.

### 1. Add FIRMS schema-drift validation and raw-response lineage

Files:

- `src/firewatch/firms.py`
- `src/firewatch/cli.py`
- `tests/test_firms.py`
- `tests/test_cli.py`
- `README.md`

1. Write failing tests first:

```python
def test_fetch_rejects_missing_required_firms_header(tmp_path):
    body = b"latitude,longitude,acq_date\n-2.0,113.0,2026-10-20\n"
    client = firms_client_returning(body, tmp_path)
    with pytest.raises(RuntimeError, match="missing required FIRMS columns: acq_time, satellite, confidence"):
        client.fetch("VIIRS_SNPP_NRT", 1)


def test_fetch_records_raw_response_lineage_without_exposing_key(tmp_path):
    manifest = refresh_with_fixture(tmp_path)
    raw = manifest["raw_sources"][0]
    assert raw["raw_sha256"] == hashlib.sha256(FIRMS_CSV).hexdigest()
    assert raw["source_url"].startswith("https://firms.modaps.eosdis.nasa.gov/")
    assert raw["fetched_at_utc"].endswith("Z")
    assert "secret-map-key" not in json.dumps(manifest)
```

2. Run red:

```bash
uv run pytest tests/test_firms.py tests/test_cli.py -q
```

Expected: tests fail because client currently accepts header-only/missing-schema payloads and manifest lacks lineage.

3. Implement required schema policy in `src/firewatch/firms.py`:

```python
REQUIRED_FIRMS_COLUMNS = {
    "latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence"
}
```

- Parse CSV header before raw response is accepted.
- Raise `RuntimeError` with sorted missing column names; never include map key or full URL containing it.
- Preserve unknown source columns in raw CSV and record sorted `unexpected_columns` in private manifest; do not fail solely for added columns.
- Add raw-source manifest fields:

```text
sensor
processing_level
raw_file_path
raw_sha256
source_url_redacted
fetched_at_utc
row_count_including_header
required_columns
unexpected_columns
```

- `source_url_redacted` must replace map key with `<redacted>`.

4. Run green:

```bash
uv run pytest tests/test_firms.py tests/test_cli.py -q
uv run pytest -q
```

Expected: all pass.

5. Verify fixture manifest bytes:

```bash
uv run python -c "import json; d=json.load(open('data/private/run_manifest_latest.json', encoding='utf-8')); r=d['raw_sources'][0]; assert len(r['raw_sha256']) == 64 and '<redacted>' in r['source_url_redacted']; print('raw lineage verified')"
```

Expected: `raw lineage verified`.

6. Commit:

```bash
git add src/firewatch/firms.py src/firewatch/cli.py tests/test_firms.py tests/test_cli.py README.md && git commit -m "feat: validate FIRMS schema and source lineage"
```

Done when: schema changes are visible and safely fail rather than silently corrupt output; every accepted raw response is reproducible by checksum and timestamp.

### 2. Replace legacy geography field and make province classification authoritative

Files:

- `src/firewatch/models.py`
- `src/firewatch/normalize.py`
- `src/firewatch/geography.py`
- `src/firewatch/export.py`
- `tests/test_geography.py`
- `tests/test_core.py`
- `tests/test_export.py`
- `README.md`

1. Add failing tests before production edit:

```python
def test_hotspot_has_no_legacy_island_field():
    hotspot = make_hotspot()
    assert not hasattr(hotspot, "island")


def test_unmatched_adm1_exports_explicit_unknown_geography(tmp_path):
    hotspot = make_hotspot(province=None)
    write_public_exports([hotspot], FIXED_NOW, tmp_path)
    properties = read_first_feature(tmp_path)["properties"]
    assert properties["province"] == "unknown"
    assert properties["province_group"] == "unknown"
    assert properties["province_capital"] is None
```

2. Run red:

```bash
uv run pytest tests/test_geography.py tests/test_core.py tests/test_export.py -q
```

Expected: failure because `Hotspot.island` still exists and/or output does not meet explicit unknown contract.

3. Implement minimum changes:

- Delete `island: str = "unknown"` from `src/firewatch/models.py`.
- Delete `island=...` argument from `src/firewatch/normalize.py`.
- Keep `province_for_coordinate()` polygon containment only.
- Preserve `province=None` internally when ADM1 polygon does not contain point.
- Export `province="unknown"`, `province_group="unknown"`, `province_capital=null`, and `classification="unknown"` for unmatched ADM1 point.
- Ensure `PROVINCE_METADATA` keys exactly equal sorted `PROVINSI` values from `data/reference/indonesia-38-provinces.geojson`.

4. Run green:

```bash
uv run pytest tests/test_geography.py tests/test_core.py tests/test_export.py -q
uv run pytest -q
```

Expected: all tests pass.

5. Inspect exported schema using only fixture input:

```bash
uv run python -c "from pathlib import Path; import json; d=json.loads(Path('data/public/fire_points_latest.geojson').read_text()); assert 'island' not in d['features'][0]['properties']; print('legacy island field absent')"
```

Expected: `legacy island field absent`.

6. Commit:

```bash
git add src/firewatch/models.py src/firewatch/normalize.py src/firewatch/geography.py src/firewatch/export.py tests/test_geography.py tests/test_core.py tests/test_export.py README.md && git commit -m "fix: make 38-province classification authoritative"
```

Done when: all 38 ADM1 province names map exactly to approved group/capital metadata; legacy `island` field is absent from model and export.

### 3. Diagnose and improve province-boundary coverage without nearest-province guesses

Files:

- `scripts/inspect_unknown_provinces.py`
- `src/firewatch/geography.py`
- `tests/test_geography.py`
- `README.md`
- `data/reference/province-boundary-provenance.json`
- `data/reference/coastline-provenance.json`

1. Write failing tests:

```python
def test_unknown_province_diagnostic_returns_distance_and_nearest_name():
    result = diagnose_unknown_province(latitude=-2.82823, longitude=122.17849)
    assert result["nearest_province"] == "Sulawesi Tengah"
    assert result["distance_to_boundary_km"] > 0
    assert result["assigned_province"] == "unknown"


def test_all_province_polygons_are_covered_by_indonesia_boundary():
    uncovered = province_boundary_coverage_errors()
    assert uncovered == []
```

2. Run red:

```bash
uv run pytest tests/test_geography.py::test_unknown_province_diagnostic_returns_distance_and_nearest_name -q
```

Expected: import/attribute failure.

3. Implement `diagnose_unknown_province(latitude, longitude)` in `src/firewatch/geography.py`.

Required return shape:

```python
{
    "assigned_province": "unknown",
    "nearest_province": "Sulawesi Tengah",
    "distance_to_boundary_km": 0.0,
    "boundary_source": "...",
    "boundary_version": "...",
}
```

Use metric projection or geodesic calculation for kilometers. Never return nearest province as classification.

Implement `province_boundary_coverage_errors()` in `src/firewatch/geography.py`:

- Load all 38 province geometries and Indonesia ADM0 geometry.
- Return each province name only when its geometry is not covered by the ADM0 geometry after both datasets are read in the same CRS.
- Allow geometric floating-point tolerance only by applying a documented 1 m buffer in metric CRS; never use a degree buffer.
- If any province fails, block public refresh with `boundary_consistency_failed`; do not publish a mixed-source output.

4. Implement `scripts/inspect_unknown_provinces.py` with command:

```bash
uv run python scripts/inspect_unknown_provinces.py data/public/fire_points_latest.geojson data/private/unknown_province_diagnostic.csv
```

CSV columns must be:

```text
id;latitude;longitude;nearest_province;distance_to_boundary_km;observed_at_utc;sensor
```

Use semicolon delimiter and UTF-8 BOM.

5. Add `data/reference/province-boundary-provenance.json` with explicit fields:

```json
{
  "source_url": "<actual downloaded source URL>",
  "retrieved_at_utc": "<actual UTC timestamp>",
  "license_url": "<actual license URL or null>",
  "crs": "EPSG:4326",
  "property_name": "PROVINSI",
  "feature_count": 38
}
```

Do not guess URLs/licenses. Read them from source metadata before writing.

6. Run green:

```bash
uv run pytest tests/test_geography.py -q
uv run python scripts/inspect_unknown_provinces.py data/public/fire_points_latest.geojson data/private/unknown_province_diagnostic.csv
uv run python -c "from pathlib import Path; b=Path('data/private/unknown_province_diagnostic.csv').read_bytes(); assert b.startswith(b'\xef\xbb\xbf') and b';' in b.splitlines()[0]; print('unknown diagnostic CSV verified')"
```

Expected: tests pass; script exits 0; CSV verification prints exact success line.

7. Boundary upgrade decision gate:

- Compare unknown count before/after replacing source geometry.
- Replace province boundary file only if it is a 38-province polygon dataset with documented source, license, CRS, and version/retrieval date.
- Re-run all province representative-point tests and live diagnostic.
- Keep unmatched points `unknown` even after update.

8. Commit:

```bash
git add scripts/inspect_unknown_provinces.py src/firewatch/geography.py tests/test_geography.py data/reference/province-boundary-provenance.json README.md && git commit -m "feat: diagnose unmatched province detections"
```

Done when: every unknown record is explainable with measured nearest-boundary distance; no code path assigns nearest province.

### 4. Classify unmatched province points as coastal, offshore, or unresolved

Files:

- `src/firewatch/geography.py`
- `src/firewatch/models.py`
- `src/firewatch/normalize.py`
- `src/firewatch/export.py`
- `tests/test_geography.py`
- `tests/test_export.py`
- `data/reference/coastline-provenance.json`
- `README.md`

1. Source decision gate. Before code, select a documented coastline/land polygon source with explicit license, CRS, version, retrieval time, and URL. Store exact values in `data/reference/coastline-provenance.json`. Do not use visual web-map tiles.

2. Write failing tests:

```python
def test_unmatched_province_point_near_land_is_coastal_unknown():
    result = classify_unmatched_geography(point_near_indonesia_land())
    assert result == "coastal_unknown"


def test_unmatched_province_point_far_from_land_is_offshore_unknown():
    result = classify_unmatched_geography(point_far_from_indonesia_land())
    assert result == "offshore_unknown"


def test_unmatched_point_is_never_assigned_to_nearest_province():
    geography = classify_geography(point_near_indonesia_land())
    assert geography["province"] == "unknown"
```

3. Run red:

```bash
uv run pytest tests/test_geography.py tests/test_export.py -q
```

Expected: import/field failure.

4. Implement `classify_unmatched_geography()` using local polygon distance in metric CRS. Store only one of:

```text
province_match
coastal_unknown
offshore_unknown
unresolved_unknown
```

Policy values must be configuration constants and documented:

```text
COASTAL_UNKNOWN_MAX_DISTANCE_KM = 5
OFFSHORE_UNKNOWN_MIN_DISTANCE_KM = 5
```

Do not choose a province from this calculation. Preserve `province="unknown"`, `province_group="unknown"`, and `province_capital=null` for every non-`province_match` state.

5. Add export fields:

```text
geography_match_status
distance_to_nearest_land_km
```

Add summary counts by `geography_match_status`.

6. Run green:

```bash
uv run pytest tests/test_geography.py tests/test_export.py -q
uv run pytest -q
```

Expected: all pass.

7. Live artifact validation:

```bash
uv run firewatch refresh --days 1
uv run python -c "import json; d=json.load(open('data/public/fire_points_latest.geojson', encoding='utf-8')); allowed={'province_match','coastal_unknown','offshore_unknown','unresolved_unknown'}; assert {f['properties']['geography_match_status'] for f in d['features']} <= allowed; assert all(f['properties']['province']=='unknown' for f in d['features'] if f['properties']['geography_match_status'] != 'province_match'); print('unmatched geography policy verified')"
```

Expected: `unmatched geography policy verified`.

8. Commit:

```bash
git add src/firewatch/geography.py src/firewatch/models.py src/firewatch/normalize.py src/firewatch/export.py tests/test_geography.py tests/test_export.py data/reference/coastline-provenance.json README.md && git commit -m "feat: classify coastal and offshore unknown detections"
```

Done when: unknown geographic points are measurable and reportable without false province assignment.

### 5. Research and pin authoritative land-cover source before writing classifier

Files:

- `docs/land-cover-source-decision.md`
- `tests/test_land_cover_source.py`

1. Research only documented services. Candidate starting points:

```text
https://www.menlhk.go.id/public-service/sigap/
https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/KEHUTANAN/MapServer/6
https://gis.bnpb.go.id/server/rest/services/thematic/PL_KLHK_2020/MapServer/layers
```

2. Record in `docs/land-cover-source-decision.md`:

```text
Provider and owning authority
Exact REST/query URL and layer ID
Dataset title/version/year
CRS
Allowed query format
License/terms URL
Attribute containing land-cover category
Forest category values
Peatland category values, or explicit “not provided”
Max record count and pagination method
Attribution text
Decision: approved or rejected
Reason
```

3. Write failing source-contract test. It reads a checked-in small fixture, not live network:

```python
def test_approved_land_cover_source_has_required_contract():
    decision = load_source_decision()
    assert decision["decision"] == "approved"
    assert decision["query_url"].startswith("https://")
    assert decision["category_field"]
    assert decision["version"]
    assert decision["license_url"]
```

4. Run red:

```bash
uv run pytest tests/test_land_cover_source.py -q
```

Expected: failure because decision document/parser does not exist or has no approved source.

5. Do not approve source if API/terms/fields cannot be verified. In that case write `decision: rejected`, update test to assert rejected decision has evidence/reason, commit research, and stop land-cover implementation. Do not scrape map tiles or dashboard HTML.

6. If approved, add fixture response containing one forest feature, one peat feature if dataset supports it, one non-forest feature, and schema metadata.

7. Run green:

```bash
uv run pytest tests/test_land_cover_source.py -q
```

Expected: all source-contract tests pass offline.

8. Commit:

```bash
git add docs/land-cover-source-decision.md tests/test_land_cover_source.py tests/fixtures/land_cover_* && git commit -m "docs: approve land cover source contract"
```

Done when: land-cover provider is documented, reproducible, legally usable, and fixture-backed. If not, task ends rejected with evidence; do not proceed to task 4.

### 6. Add land-cover/forest classification with raw-data preservation

Prerequisite: task 3 source decision is approved.

Files:

- `src/firewatch/land_cover.py`
- `src/firewatch/models.py`
- `src/firewatch/normalize.py`
- `src/firewatch/export.py`
- `tests/test_land_cover.py`
- `tests/test_export.py`
- `README.md`

1. Write failing tests for pure mapping first:

```python
def test_source_categories_map_to_public_land_cover_classes():
    assert classify_land_cover("<fixture forest category>") == "forest"
    assert classify_land_cover("<fixture peat category>") == "peatland"
    assert classify_land_cover("<fixture plantation category>") == "plantation"
    assert classify_land_cover("<fixture settlement category>") == "settlement"
    assert classify_land_cover("unmapped source category") == "unknown"
```

2. Write failing batch-enrichment test using fake approved-source client:

```python
def test_enrich_preserves_hotspot_and_adds_land_cover_provenance():
    enriched = enrich_land_cover([make_hotspot()], fake_client)
    assert enriched[0].id == make_hotspot().id
    assert enriched[0].land_cover_class == "forest"
    assert enriched[0].land_cover_source == APPROVED_SOURCE_NAME
    assert enriched[0].land_cover_version == APPROVED_SOURCE_VERSION
```

3. Run red:

```bash
uv run pytest tests/test_land_cover.py tests/test_export.py -q
```

Expected: import/field failure.

4. Implement minimum code:

- Add optional `land_cover_class`, `land_cover_source`, `land_cover_version`, `land_cover_year`, `land_cover_classified_at_utc`, and `land_cover_raw_category` fields to `Hotspot`.
- `land_cover_year` is source dataset observation year, never current refresh year unless source says so. `land_cover_classified_at_utc` is local classification time.
- Fetch land-cover features using documented pagination and bbox query, never one request per point.
- Cache exact approved-source responses in `data/raw/land-cover/` with retrieval timestamp/version.
- Perform polygon containment locally after download.
- Never delete an observation because class is non-forest.
- Export all classes. Add report-facing boolean:

```python
is_forest_or_peat = land_cover_class in {"forest", "peatland"}
```

5. Run green:

```bash
uv run pytest tests/test_land_cover.py tests/test_export.py -q
uv run pytest -q
```

Expected: all tests pass without live network.

6. Execute opt-in live source smoke test only after source approval:

```bash
uv run firewatch refresh --days 1 --with-land-cover
```

Expected: manifest reports land-cover source/version, fetched-feature count, and category counts. If source fails, refresh must still preserve FIRMS observations but mark `land_cover_class="unknown"` and manifest status `land_cover_degraded`.

7. Verify artifacts:

```bash
uv run python -c "import json; d=json.load(open('data/public/fire_points_latest.geojson', encoding='utf-8')); assert all('land_cover_class' in f['properties'] for f in d['features']); print('land cover fields verified')"
```

Expected: `land cover fields verified`.

8. Commit:

```bash
git add src/firewatch/land_cover.py src/firewatch/models.py src/firewatch/normalize.py src/firewatch/export.py tests/test_land_cover.py tests/test_export.py README.md && git commit -m "feat: classify hotspot land cover"
```

Done when: public data can distinguish forest/peatland detections from plantation/agriculture/settlement/unknown without losing original FIRMS observations.

### 7. Preserve every FIRMS source-quality field and make severity provenance explicit

Files:

- `src/firewatch/models.py`
- `src/firewatch/normalize.py`
- `src/firewatch/export.py`
- `src/firewatch/severity.py`
- `tests/test_models.py`
- `tests/test_normalize.py`
- `tests/test_export.py`
- `tests/test_severity.py`

1. Write failing test for all source-quality fields:

```python
def test_normalization_preserves_firms_quality_fields():
    hotspot = normalize_one(FIRMS_FULL_ROW)
    assert hotspot.bright_ti4_k == 342.5
    assert hotspot.bright_ti5_k == 300.1
    assert hotspot.scan_km == 0.4
    assert hotspot.track_km == 0.4
    assert hotspot.daynight == "D"
    assert hotspot.version == "2.0NRT"
    assert hotspot.confidence == "n"
```

2. Write failing test that low confidence never becomes official confirmation:

```python
def test_severity_result_includes_method_version_and_is_not_confirmation():
    severity, reason, method = classify_severity("l", 500)
    assert severity == "low"
    assert method == "frp_confidence_v1"
    assert "confirmed" not in reason.lower()
```

3. Run red:

```bash
uv run pytest tests/test_models.py tests/test_normalize.py tests/test_export.py tests/test_severity.py -q
```

Expected: failing missing `bright_ti5_k`, `version`, and method provenance.

4. Implement:

- Add `bright_ti5_k` and `version` to `Hotspot`.
- Preserve raw input `instrument` too when present.
- Export `scan_km`, `track_km`, `bright_ti5_k`, `version`, `instrument`, and `severity_method`.
- Use normalized FIRMS confidence exactly as provider emits: `l`, `n`, `h`; create human-readable label separately if required.
- Keep current severity thresholds documented as project rule, not NASA classification.

5. Run green:

```bash
uv run pytest tests/test_models.py tests/test_normalize.py tests/test_export.py tests/test_severity.py -q
uv run pytest -q
```

Expected: all tests pass.

6. Commit:

```bash
git add src/firewatch/models.py src/firewatch/normalize.py src/firewatch/export.py src/firewatch/severity.py tests/test_models.py tests/test_normalize.py tests/test_export.py tests/test_severity.py && git commit -m "feat: preserve FIRMS quality provenance"
```

Done when: all listed input fields reach public export unmodified where present, and severity has explicit project-method version.

### 8. Add cross-sensor linkage without deleting observations

Files:

- `src/firewatch/cross_sensor.py`
- `src/firewatch/models.py`
- `src/firewatch/export.py`
- `tests/test_cross_sensor.py`
- `tests/test_export.py`

1. Write failing tests with `firms_cross_sensor_sample.csv`:

```python
def test_pair_within_500m_and_30_minutes_gets_same_dedupe_group():
    grouped = link_cross_sensor_observations(sample_pair())
    assert len({item.dedupe_group_id for item in grouped}) == 1
    assert len({item.id for item in grouped}) == 2


def test_pair_outside_threshold_does_not_link():
    grouped = link_cross_sensor_observations(sample_unlinked_pair())
    assert len({item.dedupe_group_id for item in grouped}) == 2
```

2. Run red:

```bash
uv run pytest tests/test_cross_sensor.py -q
```

Expected: import/field failure.

3. Implement `link_cross_sensor_observations(observations, distance_m=500, window_minutes=30)`.

Rules:

- Do not delete raw FIRMS observations.
- Never link observations from same sensor in this task.
- Group only if sensors differ, spatial distance <=500 m, and absolute time delta <=30 minutes.
- `dedupe_group_id` must be deterministic from sorted member IDs after components form.
- An unlinked observation has `dedupe_group_id == id`.
- Record method string `cross_sensor_500m_30m_v1` on export/summary.

4. Run green:

```bash
uv run pytest tests/test_cross_sensor.py tests/test_export.py -q
uv run pytest -q
```

Expected: all pass.

5. Add summary counts:

```text
raw_observation_count
unique_cross_sensor_group_count
cross_sensor_linked_observation_count
```

6. Commit:

```bash
git add src/firewatch/cross_sensor.py src/firewatch/models.py src/firewatch/export.py tests/test_cross_sensor.py tests/test_export.py && git commit -m "feat: link overlapping satellite detections"
```

Done when: map/report can count physical candidate detections without destroying sensor-level provenance.

### 9. Add NASA standard-processing backfill and NRT/SP provenance

Files:

- `src/firewatch/firms.py`
- `src/firewatch/models.py`
- `src/firewatch/normalize.py`
- `src/firewatch/cli.py`
- `tests/test_firms.py`
- `tests/test_cli.py`
- `README.md`

1. Write failing tests:

```python
def test_source_config_marks_nrt_and_standard_processing():
    assert processing_level("VIIRS_SNPP_NRT") == "NRT"
    assert processing_level("VIIRS_SNPP_SP") == "SP"


def test_backfill_accepts_only_standard_processing_sensors():
    with pytest.raises(ValueError, match="standard-processing"):
        parse_backfill_sensors(["VIIRS_SNPP_NRT"])
```

2. Run red:

```bash
uv run pytest tests/test_firms.py tests/test_cli.py -q
```

Expected: missing function/CLI behavior failure.

3. Implement explicit CLI commands:

```bash
uv run firewatch refresh --days 1
uv run firewatch backfill-standard --from 2026-10-01 --to 2026-10-07
```

Rules:

- `refresh` uses NRT sensors only.
- `backfill-standard` uses only `VIIRS_SNPP_SP` and `VIIRS_NOAA20_SP`.
- Query each provider-supported date window; never send day range outside FIRMS documented limit.
- Store `processing_level` as `NRT` or `SP`.
- Preserve NRT and SP rows separately. Do not overwrite NRT coordinates.
- Add `supersession_key`, built from timestamp/normalized coordinate/satellite-family, only as a link candidate. Do not claim a verified one-to-one replacement without documented provider relation.

4. Run green:

```bash
uv run pytest tests/test_firms.py tests/test_cli.py -q
uv run pytest -q
```

Expected: all pass.

5. Live smoke test, after checking availability:

```bash
uv run firewatch backfill-standard --from <available-date> --to <available-date>
```

Expected: manifest prints actual source availability, accepted count, and processing-level counts. If FIRMS has no data for date/sensor, command exits non-zero with readable message and no partial public overwrite.

6. Commit:

```bash
git add src/firewatch/firms.py src/firewatch/models.py src/firewatch/normalize.py src/firewatch/cli.py tests/test_firms.py tests/test_cli.py README.md && git commit -m "feat: add FIRMS standard data backfill"
```

Done when: recent map uses NRT as current source; research/report pipeline can fetch SP data separately with explicit provenance.

### 10. Add durable deduplication across refresh runs

Files:

- `src/firewatch/history.py`
- `src/firewatch/cli.py`
- `src/firewatch/export.py`
- `tests/test_history.py`
- `tests/test_cli.py`
- `README.md`

1. Write failing tests with two separately fetched batches containing same source observation:

```python
def test_same_observation_from_two_refreshes_is_stored_once(tmp_path):
    store = ObservationHistory(tmp_path / "data/private/observation_history.jsonl")
    first = store.upsert([make_hotspot()])
    second = store.upsert([make_hotspot()])
    assert first == {"inserted": 1, "already_seen": 0}
    assert second == {"inserted": 0, "already_seen": 1}
    assert len(list(store.read_all())) == 1


def test_newer_source_report_updates_seen_metadata_but_not_raw_identity(tmp_path):
    store = ObservationHistory(tmp_path / "data/private/observation_history.jsonl")
    original = make_hotspot()
    later = make_hotspot(last_source_report_at_utc=FIXED_LATER)
    store.upsert([original])
    store.upsert([later])
    record = next(store.read_all())
    assert record["id"] == original.id
    assert record["last_seen_at_utc"] == FIXED_LATER
```

2. Run red:

```bash
uv run pytest tests/test_history.py tests/test_cli.py -q
```

Expected: import failure.

3. Implement append-safe `ObservationHistory` in `src/firewatch/history.py`.

Required historical fields:

```text
id
first_seen_at_utc
last_seen_at_utc
first_run_id
last_run_id
observation_payload_sha256
source_identity
```

Rules:

- Stable `Hotspot.id` remains canonical identity.
- Same ID from a later refresh never creates a second historical observation.
- Update only run/seen metadata when source payload is byte-identical after canonical JSON ordering.
- If same ID carries a different canonical payload, keep first raw identity and append a private `history_conflict` record with both checksums. Do not silently overwrite.
- Public latest export stays source-run snapshot; historical storage stays private until a database migration exists.

4. Change `firewatch refresh` order:

```text
fetch -> validate -> normalize -> batch dedupe -> durable-history upsert -> public export -> manifest
```

Manifest fields:

```text
historical_inserted_count
historical_already_seen_count
history_conflict_count
```

5. Run green:

```bash
uv run pytest tests/test_history.py tests/test_cli.py -q
uv run pytest -q
```

Expected: all pass.

6. Live duplicate validation. Run same saved raw fixture twice, not two changing live requests:

```bash
uv run firewatch refresh --days 1
uv run firewatch refresh --days 1
uv run python -c "import json; d=json.load(open('data/private/run_manifest_latest.json', encoding='utf-8')); assert d['historical_already_seen_count'] >= 0; print(d['historical_inserted_count'], d['historical_already_seen_count'])"
```

Expected: command exits 0. Treat actual live result as non-deterministic because provider data can change between runs; fixture test is proof of duplicate behavior.

7. Commit:

```bash
git add src/firewatch/history.py src/firewatch/cli.py src/firewatch/export.py tests/test_history.py tests/test_cli.py README.md && git commit -m "feat: retain unique observations across refreshes"
```

Done when: repeated refreshes cannot inflate historical observation count, and conflicting same-ID source data is auditable.

### 11. Add persistence episodes from repeated detections

Files:

- `src/firewatch/persistence.py`
- `src/firewatch/export.py`
- `tests/test_persistence.py`
- `tests/test_export.py`

1. Write failing tests using `firms_persistence_sample.csv`:

```python
def test_repeated_nearby_detections_form_one_persistence_episode():
    episodes = build_persistence_episodes(sample_observations())
    episode = episodes[0]
    assert episode.detection_count == 3
    assert episode.first_detected_at_utc.isoformat() == "2026-10-19T00:00:00+00:00"
    assert episode.last_detected_at_utc.isoformat() == "2026-10-19T12:00:00+00:00"
    assert episode.active_duration_hours == 12


def test_spatially_separate_detection_starts_new_episode():
    assert len(build_persistence_episodes(sample_observations())) == 2
```

2. Run red:

```bash
uv run pytest tests/test_persistence.py -q
```

Expected: import failure.

3. Implement transparent baseline rule:

```text
same episode iff distance <= 1 km and gap between consecutive detections <= 24 hours
```

Use connected components sorted by time. Version method as `persistence_1km_24h_v1`. Do not call episode a confirmed wildfire incident.

4. Required episode fields:

```text
persistence_episode_id
first_detected_at_utc
last_detected_at_utc
detection_count
active_duration_hours
max_frp_mw
province
land_cover_class
member_observation_ids
method
```

5. Export `data/public/fire_persistence_latest.geojson` and add summary count. Keep original point export unchanged.

6. Run green:

```bash
uv run pytest tests/test_persistence.py tests/test_export.py -q
uv run pytest -q
```

Expected: all pass.

7. Commit:

```bash
git add src/firewatch/persistence.py src/firewatch/export.py tests/test_persistence.py tests/test_export.py && git commit -m "feat: summarize repeated fire detections"
```

Done when: report can distinguish one-off detection from repeated satellite signal over time.

### 12. Add refresh quality report and enforce transparent degradation states

Files:

- `src/firewatch/quality_report.py`
- `src/firewatch/cli.py`
- `src/firewatch/export.py`
- `tests/test_quality_report.py`
- `tests/test_cli.py`
- `README.md`

1. Write failing test:

```python
def test_quality_report_counts_every_required_category():
    report = build_quality_report(observations, rejected={"invalid": 2})
    assert report["fetched_count"] == 5
    assert report["accepted_count"] == 3
    assert report["rejected_invalid_count"] == 2
    assert report["unknown_province_count"] == 1
    assert report["low_confidence_count"] == 1
    assert report["counts_by_province"] == {"unknown": 1, "Kalimantan Tengah": 2}
```

2. Run red:

```bash
uv run pytest tests/test_quality_report.py -q
```

Expected: import failure.

3. Implement `build_quality_report()` and write:

```text
data/public/fire_data_quality_latest.json
data/private/run_manifest_latest.json
```

Required quality fields:

```text
run_id
generated_at_utc
fetched_count
accepted_count
rejected_invalid_count
rejected_outside_indonesia_count
duplicate_count
unknown_province_count
low_confidence_count
counts_by_sensor
counts_by_processing_level
counts_by_province
counts_by_land_cover
raw_observation_count
unique_cross_sensor_group_count
unknown_province_percent
low_confidence_percent
forest_peat_percent
water_coastal_unknown_percent
cross_sensor_link_rate
nrt_vs_sp_difference_count
newest_detection_at_utc
last_source_report_at_utc
freshness_status
land_cover_status
boundary_source
boundary_version
```

Freshness rules:

```text
current: newest detection no older than 8 hours
stale: newest detection older than 8 hours
unknown: no accepted observations
```

Degradation rules:

```text
schema_changed: required FIRMS header missing
boundary_consistency_failed: any of 38 ADM1 polygons fail ADM0 coverage check
unknown_province_high: unknown_province_percent > 2
source_volume_drop: accepted count < 50% of trailing 7-run median after at least 7 successful runs
land_cover_degraded: approved land-cover source failed; observations retained with unknown class
```

Store `refresh_status` as `success`, `partial`, or `failed`; store zero or more `degradation_reasons`. Do not overwrite prior successful public output after `failed`. `partial` may publish FIRMS points only when source schema, national boundary, and deduplication pass; it must never label land-cover or official context as current.

4. Run green:

```bash
uv run pytest tests/test_quality_report.py tests/test_cli.py -q
uv run pytest -q
```

Expected: all pass.

5. Live verification:

```bash
uv run firewatch refresh --days 1
uv run python -c "import json; d=json.load(open('data/public/fire_data_quality_latest.json', encoding='utf-8')); required={'fetched_count','accepted_count','unknown_province_count','counts_by_province','freshness_status'}; assert required <= d.keys(); print(d['accepted_count'], d['freshness_status'])"
```

Expected: actual accepted count and one of `current`, `stale`, `unknown`.

6. Commit:

```bash
git add src/firewatch/quality_report.py src/firewatch/cli.py src/firewatch/export.py tests/test_quality_report.py tests/test_cli.py README.md && git commit -m "feat: publish fire data quality report"
```

Done when: every refresh reports data completeness, source age, geographic uncertainty, and derived-data degradation explicitly.

### 13. Evaluate official incident sources; integrate only approved machine-readable feed

Files:

- `docs/official-source-decision.md`
- `tests/test_official_source_contract.py`
- `src/firewatch/official_reports.py` only if source approved
- `tests/test_official_reports.py` only if source approved

1. Research candidates one by one, in this exact order:

```text
1. SIPONGI / KLHK
2. BNPB
3. BPBD
4. Manggala Agni
5. BMKG weather context only
```

2. For every candidate, document exact evidence:

```text
Owner authority
Official URL
Machine-readable API/export/RSS URL
Terms/license URL
Authentication requirement
Stable report ID
Timestamp field
Latitude/longitude or official geometry field
Status field
Update cadence
Test fixture origin
Decision: approved/rejected
Reason
```

3. Write source-decision failing test for approved source:

```python
def test_approved_official_source_has_machine_contract():
    source = load_approved_official_source()
    assert source["stable_id_field"]
    assert source["timestamp_field"]
    assert source["geometry_field"]
    assert source["terms_url"]
```

4. Run red:

```bash
uv run pytest tests/test_official_source_contract.py -q
```

Expected: failure until evidence satisfies contract.

5. If no candidate passes, commit only `docs/official-source-decision.md` with rejection evidence. Do not scrape dashboards, map tiles, or search snippets as incident data.

6. If one source passes, then and only then implement `src/firewatch/official_reports.py`:

- Preserve raw official report separately.
- Do not change FIRMS points.
- Match candidate official report to persistence episode only when both pass:

```text
distance <= 10 km
time delta <= 24 hours
```

- Export match status:

```text
satellite_detected
officially_reported
officially_resolved
unmatched_official_report
```

- Include match method/version/distance/time delta/source URL.

7. Run green:

```bash
uv run pytest tests/test_official_source_contract.py tests/test_official_reports.py -q
uv run pytest -q
```

Expected: all pass with fixtures and no live network.

8. Commit one of:

```bash
git add docs/official-source-decision.md tests/test_official_source_contract.py && git commit -m "docs: evaluate official fire report sources"
```

or, only after approval:

```bash
git add docs/official-source-decision.md src/firewatch/official_reports.py tests/test_official_source_contract.py tests/test_official_reports.py && git commit -m "feat: add official incident report matching"
```

Done when: official status has provenance and explicit match rules, or is honestly deferred with evidence.

## Tests / validation

Run after every green task:

```bash
uv run pytest -q
```

Run exact impacted test first in red and green cycles; never write all tests then all production code.

After data-changing live refresh, inspect artifacts:

```bash
uv run python -m json.tool data/public/fire_points_latest.geojson > /dev/null
uv run python -c "from pathlib import Path; b=Path('data/public/fire_points_latest.csv').read_bytes(); assert b.startswith(b'\xef\xbb\xbf') and b';' in b.splitlines()[0]; print('CSV BOM and semicolon verified')"
uv run python -c "import json; d=json.load(open('data/public/fire_data_quality_latest.json', encoding='utf-8')); assert d['accepted_count'] >= 0; print(d['freshness_status'])"
```

Expected: all commands exit 0.

Live source validation only after local key setup:

```bash
export FIRMS_MAP_KEY='set-in-local-shell-only'
uv run firewatch refresh --days 1
```

Do not print/export key. Record actual observation count and timestamps in quality report, never documentation samples.

## Risks, tradeoffs, and open questions

- `unknown` province points may be coastal/offshore detections or geometry omissions. Nearest-province assignment improves count completeness but creates false geographic claims; keep unknown until documented product policy says otherwise.
- Province geometry source must be reviewed for boundary/license/version correctness. A more detailed boundary can reduce unknown points but must still preserve 38 current provinces and official names.
- Land-cover class indicates mapped surface type, not proof that a detection is forest fire. Peatland requires separate authoritative layer if land-cover source does not carry peat attribute.
- NASA FIRMS FRP is pixel-integrated radiative power; it is not fire size, perimeter, burned hectares, or confirmed severity.
- Cross-sensor linkage and persistence are transparent project-derived relationships, not NASA-confirmed event IDs.
- FIRMS NRT and SP availability ranges differ. Never silently substitute one for another.
- Land-cover services may have request limits, changing layers, or restrictive terms. Cache versioned source extracts privately and fail degraded rather than invent classifications.
- Official-source work remains blocked until a source exposes documented machine-readable geometry, timestamp, status, and reuse terms.
- PostGIS/API migration is intentionally deferred. Keep file exports stable until historical volume requires query service.
