# Data Sources

Signal sources for the Microseason ecological calendar. Each source has been assessed for API access, data quality, and Melbourne relevance.

Status key: **Verified** = API tested, working | **Assessed** = reviewed, not yet tested | **Gap** = no good source exists

---

## Tier 1 — Daily Automated Ingestion

| Source | Signal | API | Status |
|--------|--------|-----|--------|
| Open-Meteo | Weather (temp, rain, humidity, wind, pressure, soil temp/moisture) | REST, no key | Assessed |
| ARPANSA | UV index (Melbourne station) | XML, per-minute | Assessed |
| EPA Victoria | Air quality (PM2.5, PM10, ozone, NO2) | REST, free key | Assessed |
| SunCalc | Day length, golden hour, sun position | Local calc (JS lib) | Assessed |
| SILO | Historical daily climate (1889-present) | REST, email reg | Assessed |

## Tier 2 — Weekly Batch

| Source | Signal | API | Status |
|--------|--------|-----|--------|
| iNaturalist | Species observations (birds, plants, insects, fungi) 50km radius | REST, rate-limited | Assessed |
| ALA (Atlas of Living Australia) | Aggregated biodiversity (100M+ records) | REST, JWT for protected | Assessed |
| eBird | Bird observations, checklists, migration | REST, personal key | Assessed |
| ClimateWatch (via GBIF) | Phenology-specific obs (flowering, migration, breeding) | GBIF REST | Assessed |
| Sentinel-2 NDVI (via GEE/DEA) | Vegetation greenness at 10m resolution | GEE Python API | Assessed |
| Melbourne Water | River level, flow, rainfall (200+ stations) | ArcGIS API / CSV | Assessed |
| WMIS | Surface water, groundwater, water temp | SOS2 web services | Assessed |

## Tier 3 — Seasonal / Periodic

| Source | Signal | API | Status |
|--------|--------|-----|--------|
| Melbourne Pollen (Uni Melbourne) | Grass pollen count, species-level breakdown | No API — scrape? | Gap |
| Deakin AIRwatch | Pollen + fungal spore counts (Burwood, 3-hourly) | No API — scrape? | Gap |
| DEA Hotspots | Satellite fire detection (10-min updates) | WMS/WFS | Assessed |
| Emergency Victoria | Fire incidents, danger ratings | GeoJSON feeds | Assessed |
| BoM Tidal Predictions | Port Phillip Bay tides | FTP / download | Assessed |
| IMOS / AODN | Sea surface temperature (Bass Strait) | OPeNDAP/THREDDS | Assessed |
| Landsat Thermal (via GEE) | Land surface temperature 30m | GEE Python API | Assessed |

## Tier 4 — Reference Layers

| Source | Signal | API | Status |
|--------|--------|-----|--------|
| City of Melbourne Open Data | Urban microclimate sensors (15-min), 70k tree inventory | REST (CKAN) | Assessed |
| City of Melbourne Urban Forest | Tree species, age, health, canopy | Visual map + data | Assessed |
| TERN SMIPS | Soil moisture 1km grid, daily | TERN portal | Assessed |
| TERN Australian Phenology Product | Continental greening/browning cycles (MODIS-derived) | TERN portal | Assessed |
| Melbourne UHI Dataset | Urban heat island mapping (30m) | Data.vic.gov.au | Assessed |

## Acoustic Layer (Hardware-Dependent)

| Source | Signal | API | Status |
|--------|--------|-----|--------|
| BirdWeather PUC | Continuous bird/frog/insect ID + env sensors | Public API | Assessed — requires hardware purchase |
| BirdNET | Open-source bird species ID from audio | Python library | Assessed |
| OpenSoundscape | Offline audio species classification | Python library | Assessed |
| Australian Acoustic Observatory (A2O) | Continuous recordings from 360 stations | Open access download | Assessed — check Melbourne coverage |

## Additional Species Sources

| Source | Signal | API | Status |
|--------|--------|-----|--------|
| FrogID (Australian Museum) | Frog species from call recordings | Via ALA | Assessed |
| Fungimap (via iNaturalist) | Fungi fruiting observations | iNaturalist project filter | Assessed |
| Butterflies Australia | Butterfly occurrence + juvenile stages | Via ALA | Assessed |
| Victorian Biodiversity Atlas | 6M+ Victorian flora/fauna records | API exists | Assessed |
| BirdLife Birdata | 30M+ bird records, standardised surveys | No public API, data request | Assessed |
| QuestaGame | Gamified species observations | Via ALA | Assessed |

## DIY / Custom Sensors

| Source | Signal | Setup | Status |
|--------|--------|-------|--------|
| Phenocam | Daily canopy greenness (GCC) from webcam | Cheap webcam + cron + image processing | Not started |
| Personal weather station | Hyperlocal temp, humidity, rainfall, soil | Hardware purchase | Not started |

---

## Identified Gaps

1. **Pollen API** — Melbourne Pollen and Deakin AIRwatch have no public API. Requires scraping or partnership.
2. **Acoustic monitoring in Melbourne** — A2O has 360 stations nationally but uncertain metro coverage. BirdWeather PUC would solve this.
3. **Insect abundance** — Citizen science captures occurrence, not population trends. No systematic monitoring.
4. **Real-time leaf phenology** — No phenocam or automated leaf tracking in Melbourne urban area.
5. **Atmospheric volatiles** — Petrichor, eucalyptus oil, jasmine — core "felt" signals with no data source.
6. **Light quality** — Spectral colour temperature at ground level not routinely measured.
7. **Dawn chorus timing** — No systematic monitoring network in Melbourne.
8. **Historical phenology baselines** — Australia lacks the centuries-long records found in Europe/Japan.
