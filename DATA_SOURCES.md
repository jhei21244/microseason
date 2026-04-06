# Data Sources

28 signal sources for the Microseason ecological calendar. Each assessed for API access, data quality, and Melbourne relevance.

Status: **Verified** = API tested, working | **Assessed** = reviewed, not yet tested | **Built** = collector implemented

---

## Tier 1 — Daily Automated Ingestion

| # | Source | Signal | API | Status |
|---|--------|--------|-----|--------|
| 1 | Open-Meteo | Weather (temp, rain, humidity, wind, pressure, soil temp/moisture) | REST, no key | **Built** |
| 2 | ARPANSA UV | UV index (Melbourne station, per-minute) | XML, no key | **Built** |
| 3 | EPA Victoria | Air quality (PM2.5, PM10, ozone, NO2) — hourly, multiple Melbourne stations | REST, free key | Assessed |
| 4 | SunCalc / Sunrise-Sunset.org | Day length, golden hour, sun position, twilight | REST / local calc | **Built** |
| 5 | SILO | Historical daily climate (1889-present), gridded 5.5km | REST, email reg | Assessed |

## Tier 2 — Weekly Batch

| # | Source | Signal | API | Status |
|---|--------|--------|-----|--------|
| 6 | iNaturalist | Species observations (birds, plants, insects, fungi) 50km radius | REST, rate-limited | **Built** (18.5k obs) |
| 7 | ALA (Atlas of Living Australia) | Aggregated biodiversity (100M+ records) | REST, JWT for protected | **Verified** |
| 8 | eBird | Bird observations, checklists, migration, effort data | REST, free personal key | Assessed |
| 9 | ClimateWatch Australia (via GBIF) | Phenology-specific: flowering, migration, breeding timing, 140+ species | GBIF REST | **Built** (6k records) |
| 10 | Sentinel-2 NDVI (via GEE/DEA) | Vegetation greenness at 10m resolution, 5-day revisit | GEE Python API | Assessed |
| 11 | Melbourne Water Open Data Hub | River level, flow, rainfall from 200+ telemetry sites, daily dam streamflow | ArcGIS API / CSV | **Verified** |
| 12 | WMIS (Water Measurement Information System) | Surface water, groundwater, water temp — data.water.vic.gov.au | SOS2 web services | Assessed |

## Tier 3 — Seasonal / Periodic

| # | Source | Signal | API | Status |
|---|--------|--------|-----|--------|
| 13 | Melbourne Pollen / pollenforecast.com.au | Species-level pollen counts (grass, individual tree species), 7-day forecast | No API — scrape or partner | Assessed |
| 14 | Deakin AIRwatch | Pollen + fungal spore counts (Burwood), 3-hourly resolution | No API — scrape or partner | Assessed |
| 15 | Vic Dept of Health | Automated pollen counters at multiple locations during grass season | health.vic.gov.au | Assessed |
| 16 | DEA Hotspots | Satellite fire detection (10-min updates) | WMS/WFS | Assessed |
| 17 | Emergency Victoria / CFA | Fire incidents, danger ratings | GeoJSON feeds | Assessed |
| 18 | Landsat Surface Temperature (via GEE) | Land surface temperature 30m, every 16 days | GEE Python API | Assessed |
| 19 | ECOSTRESS (NASA) | Land surface temperature at higher temporal frequency than Landsat | NASA API | Assessed |

## Tier 4 — Reference / Historical

| # | Source | Signal | API | Status |
|---|--------|--------|-----|--------|
| 20 | City of Melbourne Urban Forest | 70,000+ individually audited trees with species, age, health | REST (CKAN) | **Verified** |
| 21 | City of Melbourne tree canopy | Multispectral canopy extent mapping (2013, 2014, 2016, 2018, 2019) | REST (CKAN) | **Verified** |
| 22 | City of Melbourne microclimate sensors | Ambient temp, humidity, PM2.5, wind — 16 sites, 15-min | REST (CKAN) | **Verified** |
| 23 | TERN Australian Phenology Product | Continental greening/browning cycles, MODIS EVI, tuned for Australian rainfall-driven phenology | TERN portal | Assessed |
| 24 | TERN SMIPS | Soil moisture 1km grid, daily | TERN portal | Assessed |
| 25 | PhenoARC | 21,000+ historical Australian phenological records from literature | Research archive | Assessed |
| 26 | Victorian Government water snapshot | Reservoir levels (68% full, -11% YoY), groundwater trends, seasonal outlooks | water.vic.gov.au | Assessed |
| 27 | BoM Water Data Online | National water data portal — watercourse level, discharge, storage, groundwater | SOS2 web services | Assessed |

## Acoustic Layer (Hardware-Dependent)

| # | Source | Signal | API | Status |
|---|--------|--------|-----|--------|
| 28 | BirdWeather / BirdNET | Continuous bird/frog/insect ID (6000+ species) + env sensors (temp, humidity, pressure, tVOC, CO2, spectral light) | Public API + Python library | Assessed — requires PUC hardware |
| — | OpenSoundscape | Open-source Python bioacoustics analysis for processing audio recordings | Python library | Assessed |
| — | Australian Acoustic Observatory (A2O) | Continuous recordings from 360 stations nationally | Open access download | Assessed — check Melbourne coverage |

## DIY / Custom Sensors

| Source | Signal | Setup | Status |
|--------|--------|-------|--------|
| Phenocam | Daily canopy greenness (GCC) from webcam pointed at a deciduous tree | Cheap webcam + cron + image processing | Not started |
| Personal weather station | Hyperlocal temp, humidity, rainfall, soil | Hardware purchase | Not started |

---

## What's Built

| Collector | Records | Coverage |
|-----------|---------|----------|
| Open-Meteo weather | 367 days | Apr 2025 — Apr 2026 |
| Sunrise-Sunset astronomy | 366 days | Apr 2025 — Apr 2026 |
| ARPANSA UV | Real-time | Current readings |
| iNaturalist species | 18,532 obs | Melbourne 50km radius |
| ClimateWatch phenology | 6,000+ records | Melbourne region, multi-year |
| Transition detector | 1 detected | "Cool change" — Mar 31, 2026 |

---

## Identified Gaps

1. **Pollen API** — Data is granular (species-level, 3-hourly) but no public API. Victoria invested heavily post-2016 thunderstorm asthma. Requires scraping or data partnership.
2. **Acoustic monitoring in Melbourne** — A2O has 360 stations nationally but uncertain metro coverage. BirdWeather PUC would solve this.
3. **Insect abundance** — Citizen science captures occurrence, not population trends. No systematic monitoring.
4. **Real-time leaf phenology** — No phenocam or automated leaf tracking in Melbourne urban area. DIY phenocam would fill this.
5. **Atmospheric volatiles** — Petrichor, eucalyptus oil, jasmine — core "felt" signals with no data source.
6. **Light quality** — Spectral colour temperature at ground level not routinely measured. BirdWeather PUC includes a spectral light sensor.
7. **Dawn chorus timing** — No systematic monitoring in Melbourne. BirdWeather PUC would provide this.
8. **Historical phenology baselines** — PhenoARC (21k records) partially addresses this. Australia still lacks the centuries-long records found in Europe/Japan.
