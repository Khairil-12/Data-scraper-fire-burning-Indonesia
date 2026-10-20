# Official fire incident source evaluation and decision

Date: 2026-10-20
Status: ALL CANDIDATES REJECTED (no automated official incident matching deployed)

## Evaluated candidate sources

### 1. SIPONGI / KLHK (Sistem Informasi Karhutla)
- Owner authority: Kementerian Lingkungan Hidup dan Kehutanan (KLHK)
- Official URL: `https://sipongi.menlhk.go.id/`
- Machine-readable API / RSS: None documented or publicly authenticated.
- Terms/license URL: None found.
- Decision: REJECTED. Lacks machine-readable public API with stable identifiers and verified terms of service. Do not scrape web dashboard or map tiles.

### 2. BNPB (Badan Nasional Penanggulangan Bencana)
- Owner authority: BNPB
- Official URL: `https://bnpb.go.id/`
- Data portal: `https://data.bnpb.go.id/`
- Machine-readable feed: Periodic XLSX disaster summaries, not real-time API.
- Decision: REJECTED. Cadence is retrospective/irregular, lacking per-incident geographic coordinates and real-time machine API.

### 3. BPBD (Badan Penanggulangan Bencana Daerah)
- Owner authority: Regional disaster management agencies (e.g. BPBD DKI Jakarta)
- Machine-readable feed: Fragmented by province/regency; no unified national feed.
- Decision: REJECTED. No nationwide API covering Indonesia's 38 provinces.

### 4. Manggala Agni
- Owner authority: Brigada Pengendalian Kebakaran Hutan dan Lahan KLHK
- Decision: REJECTED. Operations report through KLHK/SIPONGI; no independent automated data feed.

### 5. BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)
- Owner authority: BMKG
- Official URL: `https://data.bmkg.go.id/`
- Machine-readable API: `https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4}`
- Content: Weather forecasts and early weather warnings, NOT ground fire incident reports.
- Decision: REJECTED for fire incidents. Can be used for auxiliary weather context only.

## Summary policy
No official candidate currently qualifies as an approved real-time incident feed under the data accuracy contract.
All map and export points remain classified as `satellite_detected` from NASA FIRMS. Do not present satellite hotspot detections as confirmed official disaster incidents.
