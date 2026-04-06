# API Assessment — Tested 2026-04-06

Each source tested with real HTTP requests against Melbourne coordinates (-37.8136, 144.9631).

---

## Verdict Summary

| Source | Status | Notes |
|--------|--------|-------|
| Open-Meteo | **Works** | No key, instant, includes soil data |
| ARPANSA UV | **Works** | XML feed, per-minute, Melbourne station present |
| Sunrise-Sunset.org | **Works** | No key, instant |
| iNaturalist | **Works** | 1M+ Melbourne records, rate-limited |
| ALA Biocache | **Works** | 990k April records near Melbourne |
| GBIF ClimateWatch | **Works** | 10k phenology records near Melbourne |
| City of Melbourne | **Works** | Microclimate sensors (16 sites), soil sensors (84 sites), tree canopy data |
| eBird | **Needs key** | Returns 403 without API key (free registration) |
| EPA Victoria | **Needs key** | Returns 404 unauthenticated (free dev portal registration) |
| BirdWeather | **Needs key** | Public station query returns "Access denied" |
| Melbourne Water | **Works** | ArcGIS hub, 20M+ records, API available |
| SILO | **Needs email** | REST API requires email registration |

---

## Detailed Results

### Open-Meteo — WORKS (Tier 1)
- **Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Auth:** None required
- **Response:** JSON, hourly + daily granularity
- **Tested variables:** temperature_2m_max/min, precipitation_sum, windspeed_10m_max, soil_temperature_0cm, soil_moisture_0_to_1cm
- **Soil data:** Yes — 4 depth layers for both temp and moisture
- **Archive API:** `https://archive-api.open-meteo.com/v1/archive` for historical (back to 1940)
- **Quirks:** None. Fast, clean, reliable. Best zero-friction weather source.

### ARPANSA UV — WORKS (Tier 1)
- **Endpoint:** `https://uvdata.arpansa.gov.au/xml/uvvalues.xml`
- **Auth:** None required
- **Response:** XML with all Australian stations
- **Melbourne:** Present as station `mel`, returns current UV index + timestamp
- **Update frequency:** Every minute
- **Quirks:** XML format (not JSON). Simple to parse. Attribution required.

### Sunrise-Sunset.org — WORKS (Tier 1)
- **Endpoint:** `https://api.sunrise-sunset.org/json?lat=-37.8136&lng=144.9631&formatted=0`
- **Auth:** None required
- **Response:** JSON with sunrise, sunset, civil/nautical/astronomical twilight, day_length
- **Quirks:** Returns UTC times. Day length in seconds. No golden hour field but derivable from civil twilight.

### iNaturalist — WORKS (Tier 2)
- **Endpoint:** `https://api.inaturalist.org/v1/observations`
- **Auth:** None for reading
- **Response:** JSON, paginated (200 per page max)
- **Melbourne data:** 1,049,364 total records within 50km radius
- **Quality:** Research-grade filter available. Today's records already present.
- **Rate limit:** ~1 req/sec recommended
- **Quirks:** Rich data — species, photos, GPS, taxonomy. The backbone for species signals.

### ALA Biocache — WORKS (Tier 2)
- **Endpoint:** `https://biocache-ws.ala.org.au/ws/occurrences/search`
- **Auth:** None for basic queries
- **Response:** JSON, paginated
- **Melbourne data:** 990,124 April records within 50km (massive)
- **Quirks:** Aggregates iNaturalist + eBird + VBA + museum collections. Good for cross-referencing.

### GBIF ClimateWatch — WORKS (Tier 2)
- **Endpoint:** `https://api.gbif.org/v1/occurrence/search?datasetKey=3fab912e-e927-4f1c-a97c-eb446cd609e0`
- **Auth:** None for reading
- **Response:** JSON, paginated
- **Melbourne data:** 10,092 records. Includes phenological annotations (flowering, seed pods, mating observations)
- **Quirks:** Lower volume but phenology-specific — exactly what we need for seasonal markers.

### City of Melbourne — WORKS (Tier 4)
- **Microclimate sensors:** 16 locations, includes temp/humidity/PM2.5/wind. Some historical (2019-2021), some current.
- **Soil sensors:** 84 sites across parks (Princes Park, Royal Park, etc.)
- **Tree canopy:** Multiple years (2008, 2013, 2014, 2016, 2018, 2019)
- **API:** CKAN-based REST API at `data.melbourne.vic.gov.au/api/explore/v2.1/`
- **Quirks:** Search function returns irrelevant results for keyword queries — need exact dataset IDs. Sensor data may have gaps.

### Melbourne Water — WORKS (Tier 2)
- **Endpoint:** ArcGIS Open Data Hub
- **Auth:** None
- **Data:** 20M+ records across rainfall, river level, flow, water quality
- **Quirks:** ArcGIS API format. Large dataset. Need to identify specific station IDs for Melbourne waterways.

### eBird — NEEDS KEY (Tier 2)
- **Endpoint:** `https://api.ebird.org/v2/data/obs/AU-VIC/recent`
- **Auth:** API key required (free — apply at ebird.org)
- **Response:** 403 Forbidden without key
- **Action:** Register for free API key

### EPA Victoria — NEEDS KEY (Tier 1)
- **Endpoint:** `https://gateway.api.epa.vic.gov.au/`
- **Auth:** Developer portal registration required (free)
- **Response:** 404 without auth
- **Action:** Register at developer.epa.vic.gov.au

### BirdWeather — NEEDS KEY (Acoustic)
- **Endpoint:** `https://app.birdweather.com/api/v1/`
- **Auth:** Station-specific or account-level access
- **Response:** "Access denied" for public queries
- **Action:** Requires BirdWeather account or PUC hardware ownership

### SILO — NEEDS EMAIL (Tier 1)
- **Endpoint:** `https://www.longpaddock.qld.gov.au/silo/`
- **Auth:** Email address required in API query
- **Response:** Not tested (need email param)
- **Action:** Provide email to unlock. Instant — no approval process.

---

## Immediate Action Items

1. **Register for free API keys:** eBird, EPA Victoria, SILO
2. **No registration needed:** Open-Meteo, ARPANSA, iNaturalist, ALA, GBIF, Sunrise-Sunset, Melbourne Water, City of Melbourne
3. **Hardware decision:** BirdWeather PUC for acoustic layer
4. **Pollen:** Still no API found — needs scraping investigation
