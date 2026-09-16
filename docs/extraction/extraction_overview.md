# ArcGIS Feature Layer Extraction Overview

**Date:** 2026-09-15  
**Author:** PJM  
**Purpose:** Documents the extraction of all ArcGIS feature layers from the AirToxScreen 2020 and 2017-2019 tools to GeoParquet and GeoJSON, including methodology, technical decisions, failures, and validation results.

---

## Methodology

All 27 layers identified during discovery were extracted from ESRI's ArcGIS Online hosted feature services using the ArcGIS REST API. Each layer was queried via the `/query` endpoint and written to GeoParquet using geopandas with WGS84 (EPSG:4326) as the output CRS.

Two extraction strategies were used depending on layer size:

**Small layers (< 100,000 features):** Accumulated in memory via offset-based pagination, then written to a single GeoParquet file. Point layers also receive a GeoJSON output. Page size is determined by the service's actual `maxRecordCount` rather than a hardcoded value — critical for services that cap at 1,000 records per page rather than 2,000.

**Large layers (≥ 100,000 features):** Extracted using OBJECTID range-based pagination via the statistics endpoint to get min/max OBJECTID, then querying each range as `OBJECTID >= X AND OBJECTID <= Y`. Each page is written as an individual chunk GeoParquet file, then all chunks are concatenated into a final file and the chunks are deleted. This approach avoids loading all data into memory and is resilient to server-side offset pagination failures.

---

## Technical Decisions

**Why OBJECTID range pagination instead of offset pagination for large layers?**
Offset-based pagination (`resultOffset=N`) is unreliable for large ESRI services — the server can return empty results mid-extraction even when features remain. The 2020 cancer risk layer (5.8M features) failed at offset 2,636,000 during the first extraction attempt using offset pagination. OBJECTID range pagination queries are index-backed and stateless, making them both faster and more reliable.

**Why chunk-then-concatenate for large layers instead of streaming?**
`geopandas.to_parquet()` writes valid GeoParquet metadata (CRS, geometry encoding, bounding box) as part of the file footer. `pyarrow.ParquetWriter` does not — it produces valid Parquet but missing the GeoParquet spec metadata that `geopandas.read_parquet()` requires. The chunk-then-concatenate approach writes each chunk with `gdf.to_parquet()` ensuring valid GeoParquet at every step, then concatenates using pandas.

**Why not use pyesridump?**
pyesridump is unmaintained (last meaningful commit 2022), doesn't handle Experience Builder apps, and doesn't produce GeoParquet output. The custom implementation gives full control over pagination strategy, output format, retry logic, and validation.

---

## Failures and Fixes

**First extraction attempt — Total Cancer Risk (2020)**

- Extracted 2,636,000 of 5,808,484 features
- Cause: offset-based pagination returned empty at resultOffset=2,636,000
- Fix: switched to OBJECTID range pagination

**First extraction attempt — Ambient Monitors (2017)**

- Extracted 1,000 of 12,334 features
- Cause: service `maxRecordCount` is 1,000, not 2,000; loop broke after first page thinking pagination was complete
- Fix: query `maxRecordCount` from service metadata before paginating

---

## Validation

Feature counts for all layers were validated against live counts from the ArcGIS REST API count endpoint. GeoParquet schema validated via pyarrow — all files contain valid `geo` metadata, correct WKB geometry encoding (`geoarrow.wkb`), and EPSG:4326 CRS.

Census block FIPS codes (15-digit Block_ID) confirmed present in 2020 cancer risk layer.

---

## Complete Layer Inventory

### 2020 Layers

| File | Features | Type |
| ------ | ---------- | ------ |
| `airtoxscreen_2020_ambient_monitors_points.parquet` | 630 | Point |
| `airtoxscreen_2020_ambient_monitors.geojson` | 630 | Point |
| `airtoxscreen_2020_facility_level_emissions_points.parquet` | 58,055 | Point |
| `airtoxscreen_2020_facility_level_emissions.geojson` | 58,055 | Point |
| `airtoxscreen_2020_cancer_risk_caveats_blocks.parquet` | 6,623 | Polygon |
| `airtoxscreen_2020_total_cancer_risk_blocks.parquet` | 5,808,484 | Polygon |

### 2017-2019 Layers

| File | Features | Type | Year |
| ------ | ---------- | ------ | ------ |
| `airtoxscreen_2019_alaskan_tribal_areas_polygons.parquet` | 227 | Polygon | 2019 |
| `airtoxscreen_2019_alaska_native_allotments_polygons.parquet` | 16,269 | Polygon | 2019 |
| `airtoxscreen_2019_off_reservation_trust_lands_polygons.parquet` | 160 | Polygon | 2019 |
| `airtoxscreen_2019_american_indian_reservations_polygons.parquet` | 321 | Polygon | 2019 |
| `airtoxscreen_2019_ambient_monitors_points.parquet` | 10,636 | Point | 2019 |
| `airtoxscreen_2019_ambient_monitors.geojson` | 10,636 | Point | 2019 |
| `airtoxscreen_2019_facility_level_emissions_points.parquet` | 48,690 | Point | 2019 |
| `airtoxscreen_2019_facility_level_emissions.geojson` | 48,690 | Point | 2019 |
| `airtoxscreen_2019_cancer_risk_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2019_tract_caveats_tracts.parquet` | 91 | Polygon | 2019 |
| `airtoxscreen_2019_respiratory_hazard_index_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2019_neurological_hazard_index_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2019_liver_hazard_index_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2019_kidney_hazard_index_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2019_immunological_hazard_index_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2019_risk_by_air_toxics_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2019_risk_by_source_type_tracts.parquet` | 73,711 | Polygon | 2019 |
| `airtoxscreen_2018_ambient_monitors_points.parquet` | 11,386 | Point | 2018 |
| `airtoxscreen_2018_ambient_monitors.geojson` | 11,386 | Point | 2018 |
| `airtoxscreen_2018_facility_level_emissions_points.parquet` | 48,555 | Point | 2018 |
| `airtoxscreen_2018_facility_level_emissions.geojson` | 48,555 | Point | 2018 |
| `airtoxscreen_2018_cancer_risk_tracts.parquet` | 73,711 | Polygon | 2018 |
| `airtoxscreen_2018_tract_caveats_tracts.parquet` | 120 | Polygon | 2018 |
| `airtoxscreen_2017_ambient_monitors_points.parquet` | 12,334 | Point | 2017 |
| `airtoxscreen_2017_ambient_monitors.geojson` | 12,334 | Point | 2017 |
| `airtoxscreen_2017_facility_level_emissions_points.parquet` | 47,643 | Point | 2017 |
| `airtoxscreen_2017_facility_level_emissions.geojson` | 47,643 | Point | 2017 |
| `airtoxscreen_2017_cancer_risk_tracts.parquet` | 73,711 | Polygon | 2017 |
| `airtoxscreen_2017_tract_caveats_tracts.parquet` | 133 | Polygon | 2017 |

---

## Notes

**The 2020 cancer risk layer is the most critical artifact.** 5,808,484 census block polygons with 130 columns including total cancer risk, risk by pollutant, risk by source type, and demographic exposure data. This is the data underlying the ArcGIS tool's primary visualization and is not available in this form from any other source.

**The 2017/2018/2019 cancer risk layers all contain exactly 73,711 features** — the census tract count for the US. These are tract-level, not block-level. The move to block-level resolution was introduced in the 2020 assessment.

**Noncancer hazard breakdowns exist only for 2019** — respiratory, neurological, liver, kidney, and immunological hazard indices are not available for 2017 or 2018.

**Tribal boundary layers appear only in 2017-2019 tool** — Alaska Native Villages, Alaska Native Allotments, Off-Reservation Trust Lands, and American Indian Reservations were removed from the 2020 tool. Their absence from the 2020 tool appears to be intentional but is undocumented.
