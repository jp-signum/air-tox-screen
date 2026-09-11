# Crawling Overview

**Date:** 2026-09-10  
**Author:** PJM  
**Purpose:** Documents the discovery process for EPA web pages and the EPA FTP/HTTPS server, covering methodology, findings, anomalies, and notes relevant to static file downloads & bulk data mirroring.

---

## EPA Web Crawl (`crawl_epa.py`)

### Methodology

Recursive HTTP crawl starting at `https://www.epa.gov/AirToxScreen`. Follows all links within the `/AirToxScreen` path on `www.epa.gov`. For each discovered file URL (xlsx, zip, pdf, csv, etc.), sends a HEAD request to capture content type, file size, ETag, and last-modified date. Output saved as a timestamped JSON manifest.

### Results

- **22 pages crawled**
- **82 files found**
  - 63 xlsx — emissions summaries, cancer risk by county/state/pollutant/source group
  - 11 PDFs — methodology, TSD, technical documents
  - 8 zip — county emissions and supplemental data files
- **Baseline manifest:** `epa_crawl_20260910_213117.json`

### Pages Discovered
All pages under `https://www.epa.gov/AirToxScreen/`:

Assessment results pages for 2017, 2018, 2019, and 2020; emissions update documents for 2017, 2018, and 2020; the main assessment overview, assessment methods, data elements explanation, FAQ, glossary, limitations, mapping tool, overview, risk drivers, technical support document, previous assessments, and contact form.

### Zip Files

| File | Size |
| ------ | ------ |
| `airtoxscreen_2020_emissions_county_sourcegroup.zip` | 108.4 MB |
| `2020-airtoxscreen-supplemental-data-files.zip` | 33.4 MB |
| `2019 AirToxScreen Supplemental Data files.zip` | 4.9 MB |
| `2018 AirToxScreen Supplemental Data files.zip` | 47.4 MB |
| `AirToxScreen_2017_Emissions_County_Sourcegroup.zip` | 159.0 MB |
| `AirtoxScreen_2018_Emissions_County_Sourcegroup.zip` | 111.5 MB |
| `AirToxScreen_2019_Emissions_County_Sourcegroup.zip` | 84.9 MB |
| `2017-airtoxscreen-supplemental-data-files.zip` | 45.1 MB |

**Total zip size: ~594 MB**

### Anomalies and Notes

**No 2019 TSD exists.** The generic TSD page (`/airtoxscreen-technical-support-document`) hosts TSDs for 2017, 2018, and 2020 only. There is no 2019 Technical Support Document.

**No standalone 2019 emissions update document.** The 2019 assessment results page links to the 2018 emissions update page for both years. The 2018 page title confirms it covers 2018 only — this appears to be an EPA linking error. The actual 2019 emissions update document exists at `/AirToxScreen/2019-airtoxscreen-emissions-update-document` (returns 200) but was not linked from any crawled page and therefore was not discovered by the crawler.

**Action required:** Add the 2019 emissions update URL explicitly to the Phase 2 download manifest since it won't be discovered via crawl.

---

## FTP/HTTPS Crawl (`crawl_ftp.py`)

### Methodology

The EPA FTP server (`gaftp.epa.gov`) exposes all data via HTTPS with Apache-style directory index pages. No FTP protocol is required — the server is crawled using standard HTTP requests with BeautifulSoup to parse the Apache index HTML tables. The crawler walks the directory tree recursively, constrained to `https://gaftp.epa.gov/rtrmodeling_public/AirToxScreen/` to prevent following parent directory links into the rest of the EPA FTP server.

**Critical note:** An early version of the script without the `START_URL` constraint followed a parent directory link and began crawling the entire EPA FTP server (Comptox, Air emissions modeling, NEI data, etc.) for over two hours before being killed. The constraint `s.startswith(START_URL)` in the walk function is essential.

### Results

- **4,317 files found**
- **56.28 GB total**
- **Baseline manifest:** `ftp_crawl_20260911_001037.json`

### Directory Structure

Only 2020 data is available on this server. The 2017/2018/2019 bulk data is not present.

```bash
/rtrmodeling_public/AirToxScreen/2020/
├── Ambient Concentrations/          # 13 regional xlsx files
├── Exposure Concentrations/         # 13 regional xlsx files
├── Emissions/                       # 1 xlsx + 4 CSVs
├── Cancer/
│   ├── ByPollutant/                 # 13 regional xlsx files, block-level cancer risk by pollutant
│   └── BySource/                    # 13 regional xlsx files, block-level cancer risk by source group
└── Pollutant Summaries/
    └── Region1-10/                  # 426 files per region × 10 regions = 4,260 zip files
```

### File Breakdown

| Type | Count | Notes |
| ------ | ------- | ------- |
| `.zip` | 4,260 | Pollutant summaries — ambient concentration, exposure concentration, risk per pollutant per region |
| `.xlsx` | 53 | Regional ambient/exposure concentrations, block-level cancer risk by pollutant and source, emissions |
| `.csv` | 4 | HAPCAP AERMOD county groups for regions 1-5 and 6-10 |

### Pollutant Summaries Structure

Each of the 10 regions contains 426 zip files covering approximately 180 pollutants × 3 data types:

- `{POLLUTANT}_AMBCONC_{REGION}.zip` — ambient concentrations
- `{POLLUTANT}_EXPCONC_{REGION}.zip` — exposure concentrations  
- `{POLLUTANT}_RISK_{REGION}.zip` — cancer risk

Not all pollutants have all three files (some non-carcinogens have no RISK file).

### Cancer Directory

The `Cancer/ByPollutant/` and `Cancer/BySource/` directories contain block-level cancer risk xlsx files organized by EPA region. These are the underlying tabular data behind the `Cancer_Risk_2020/FeatureServer/0` ArcGIS layer (5,808,484 census block features). Archiving both the xlsx files and the ArcGIS feature layer provides redundant coverage of the most critical dataset.

### Notes

**2017/2018/2019 bulk data not on this server.** Only 2020 data is hosted at `gaftp.epa.gov/rtrmodeling_public/AirToxScreen/`. The 2017/2018/2019 supplemental data is available only via the static zip downloads on the EPA website (captured in the web crawl).

**56 GB is the floor, not the ceiling.** File sizes in the Apache index are shown in abbreviated form (e.g., "2.7M", "38M"). The `parse_size` function converts these to bytes but the abbreviated display loses precision. Actual download size may be slightly larger.

**The `Emissions/` directory contains HAPCAP AERMOD files.** These are the input emissions files used in the AERMOD dispersion modeling that produced the AirToxScreen risk estimates. Archiving these provides the full upstream provenance chain: emissions inputs → dispersion model → risk outputs.

---

## Combined Phase 0 Summary

| Source | Files | Size |
| -------- | ------- | ------ |
| EPA web crawl | 82 | ~1.2 GB (est.) |
| FTP/HTTPS server | 4,317 | 56.28 GB |
| ArcGIS feature layers | 27 layers | TBD (Phase 4) |

**Total estimated Phase 2+3 download: ~57.5 GB before ArcGIS extraction.**

The single largest item is the Pollutant Summaries directory at ~50+ GB across 4,260 zip files. The block-level cancer risk xlsx files in `Cancer/` are the most critical data artifacts and should be downloaded first in Phase 3.
