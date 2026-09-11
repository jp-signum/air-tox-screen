# Download Overview

**Date:** 2026-09-11  
**Author:** PJM  
**Purpose:** Documents the download scripts, methodology, decisions, and status for capturing EPA AirToxScreen web pages, static data files, and the EPA FTP/HTTPS bulk data mirror.

---

## Web Page Archival (`archive_epa_pages.py`)

### Methodology

Reads the EPA crawl manifest and captures each discovered page as a WARC record using `warcio`. All 22 pages are written to a single gzip-compressed WARC file — the community standard format used by EDGI, the Internet Archive, and the broader data rescue community. WARC includes full HTTP response headers, timestamps, and is immutable and replayable.

Pages are captured as static HTML. The EPA AirToxScreen documentation pages are mostly static so a `requests` fetch is sufficient — no headless browser needed.

### Output

- **WARC file:** `/epa_airtoxscreen_20260911_010939.warc.gz`
- **Capture manifest:** `epa_pages_capture_20260911_011003.json`
- **Pages captured:** 22/22
- **All responses:** 200 OK

### Verification

WARC integrity verified with `warcio.archiveiterator` — 1 warcinfo record + 22 response records confirmed.

### Notes

The ArcGIS Experience Builder tool pages are captured as HTML only — the interactive map content is not present in the static HTML. The actual data is captured via feature layer extraction. No Playwright or screenshot capture is needed.

---

## EPA Static File Downloads (`download_epa_files.py`)

### Methodology

Reads the EPA crawl manifest and downloads every linked file (xlsx, pdf, zip) using `requests` with streaming. Each file is checksummed with SHA-256 after download. A download manifest records URL, destination path, file size, checksum, and download timestamp for every file.

### Output

- **Files directory:** `air-tox-screen/epa-files/`
- **Download manifest:** `epa_files_download_20260911_013328.json`
- **Files downloaded:** 82/82
- **Total size:** 2.47 GB
- **Errors:** 0

### File Breakdown

- 63 xlsx — emissions summaries, cancer risk by county/state/pollutant/source group across all four years
- 11 PDFs — TSD (2017, 2018, 2020), methodology, emissions update documents
- 8 zip — county emissions and supplemental data files (~594MB)

### Notes

The 2019 emissions update document (`/AirToxScreen/2019-airtoxscreen-emissions-update-document`) was not in the crawl manifest since it isn't linked from any crawled page. It needs to be added manually to a future rerun or captured separately. See crawling overview for full context.

---

## FTP/HTTPS Bulk Data Mirror (`download_ftp_files.py`)

### Methodology

Reads the FTP crawl manifest and mirrors all 4,317 files from `https://gaftp.epa.gov/rtrmodeling_public/AirToxScreen/2020/` preserving the full directory structure. Uses `wget` via subprocess for downloads — the correct tool for large file transfers with built-in retry, resume, and connection handling that `requests` cannot reliably provide for files 100MB+.

Key `wget` flags:

- `--continue` — resumes partial downloads on restart
- `--tries=10` — retries up to 10 times per file
- `--read-timeout=300` — 5 minute read timeout per attempt
- `--random-wait` — polite random delay between requests

The `.tmp` extension is used during download and renamed on completion — no partial files are ever left on disk, making reruns always safe.

File sizes in the FTP manifest are abbreviated (e.g. "2.7M") so a 5% tolerance is used for size validation rather than exact byte matching.

### Output

- **Mirror directory:** `air-tox-screen/ftp-mirror/`
- **Download manifest:** `ftp_download_*.json` (generated on completion)
- **Files to mirror:** 4,317
- **Total size:** 56.28 GB
- **Status:** In progress as of 2026-09-11

### Download Speed

The EPA FTP server throttles connections to approximately 280-333 KB/s. At this rate the full mirror will take approximately 50-60 hours. The script is resilient to interruption — rerunning skips completed files and retries failures.

### Directory Structure Preserved

```bash
ftp-mirror/rtrmodeling_public/AirToxScreen/2020/
├── Ambient Concentrations/      # 13 regional xlsx
├── Exposure Concentrations/     # 13 regional xlsx
├── Emissions/                   # 1 xlsx + 4 CSVs
├── Cancer/
│   ├── ByPollutant/             # 13 regional xlsx, block-level cancer risk by pollutant
│   └── BySource/                # 13 regional xlsx, block-level cancer risk by source group
└── Pollutant Summaries/
    └── Region1-10/              # 4,260 zip files, ~180 pollutants × 3 data types × 10 regions
```

### Key Notes

**The Cancer/ directory is the most critical data.** `Cancer/ByPollutant/` and `Cancer/BySource/` contain block-level cancer risk xlsx files — the underlying tabular data behind the `Cancer_Risk_2020/FeatureServer/0` ArcGIS layer (5.8M census block features). These should be verified first on completion.

**Only 2020 data is on this server.** 2017/2018/2019 bulk data is not available via FTP/HTTPS — those years are only available through the static zip downloads captured in the EPA files download.

**Rerun is safe.** The `.tmp` pattern and `dest.exists()` check mean the script can be stopped and restarted at any time without corrupting or re-downloading completed files.

---

## Technical Decisions

**Why WARC for pages, not MHTML or raw HTML?**
WARC is the ISO standard (ISO 28500:2017) for web archiving, used by EDGI, the Internet Archive, and the data rescue community. It includes full HTTP response metadata, is timestamped, immutable, and replayable. EDGI's own archiving tools (`eis-WARC-archiver`) use WARC via `grab-site`. Raw HTML loses headers and metadata; MHTML is browser-specific and not archival-grade.

**Why `wget` for FTP mirror, not `requests`?**
`requests` is not designed for large file transfers. It lacks native retry-on-partial-content, resume support, and connection timeout handling appropriate for files 100MB+. `wget` is purpose-built for this, handles all edge cases correctly, and is the standard tool in archiving workflows. The tradeoff is a system dependency (`brew install wget`) which is acceptable for an archiving project.

**Why `requests` for EPA static files but `wget` for FTP?**
The EPA static files are mostly small (xlsx, pdf) with a few mid-size zips (up to ~160MB). `requests` handles these reliably with appropriate timeouts. The FTP files include many 200-400MB xlsx files where `requests` demonstrated real failure — this informed the decision to use `wget` for the FTP mirror specifically.
