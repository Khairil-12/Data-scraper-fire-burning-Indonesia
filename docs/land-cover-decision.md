# Land-cover candidate evaluation and decision

Date: 2026-10-20
Status: REJECTED (no classifier deployed)

## Evaluated sources

### 1. BNPB PL_KLHK_2020 ArcGIS MapServer
- Authority: BNPB ArcGIS service republishing KLHK 2020 land-cover
- Layer URL: `https://gis.bnpb.go.id/server/rest/services/thematic/PL_KLHK_2020/MapServer/0`
- Query URL: `https://gis.bnpb.go.id/server/rest/services/thematic/PL_KLHK_2020/MapServer/0/query`
- Total features: 370,425
- Category field: `kelas` (22 classes, 7 forest classes)
- CRS: EPSG:4326 (service extent EPSG:3857)
- Terms / License: Empty `copyrightText`. No license URL exposed in service metadata.
- Peatland coverage: None (only wetland/marsh classes: `Rawa`, `Belukar Rawa`).
- Decision: REJECTED. Lacks verified open license and lacks peatland classification.

### 2. KLHK SIGAP / Penutupan Lahan 2022
- Authority: KLHK Ditjen PKTL (Direktorat Inventarisasi dan Pemantauan Sumber Daya Hutan)
- Candidate Service: `https://geoportal.menlhk.go.id/server/rest/services/SIGAP_Interaktif/Penutupan_Lahan_2022/MapServer`
- Decision: REJECTED. DNS resolution failed from execution environment.

### 3. BIG Satu Peta Kehutanan
- Authority: Badan Informasi Geospasial (BIG)
- Candidate Service: `https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/KEHUTANAN/MapServer/6`
- Category field: Transition code `id_pl_perubahan` without verified codebook or year.
- Terms / License: Empty layer copyright.
- Decision: REJECTED.

## Conclusion and policy
No candidate meets the verification gate: verified machine API, exact category mapping, reproducible version, and explicit license/terms URL.
Per roadmap policy, `land_cover_class` remains `None` on all exported hotspots until an approved source with verifiable terms and schema is integrated. No heuristic or fake land-cover classification is permitted.
