# AirToxScreen Archiver

Tooling to archive and rebuild EPA's [AirToxScreen](https://www.epa.gov/AirToxScreen) — preserving data, feature layers, and documentation for open-source reimplementation.

## What This Does

EPA's AirToxScreen is a national air toxics screening assessment tool providing census block-level cancer risk and noncancer hazard estimates across the US. This repo captures the full dataset before it goes offline, including:

- ArcGIS feature layers from the interactive mapping tool
- Block-level risk data from the EPA FTP server
- Static emissions and risk summary files
- Methodology documentation and technical support documents
- Visual snapshots of the interactive tool

All captured data is archived to Zenodo and Harvard Dataverse with SHA-256 checksums and a full provenance manifest.

## Phases

| Phase | Description |
| ------- | ------------- |
| 0 | Discovery — build a complete capture manifest |
| 1 | Documentation — EPA web pages, TSD, methodology |
| 2 | Static files — emissions and risk summary downloads |
| 3 | FTP mirror — block-level data from gaftp.epa.gov |
| 4 | ArcGIS extraction — feature layers to GeoParquet |
| 5 | Visual capture — Playwright screenshots of the tool |
| 6 | Packaging and Zenodo upload |
| 7 | Data Processing — ETL, schema standardization, vintage crosswalks |
| 8 | Backend/API - open API to serve processed data |
| 9 | Open-source tool — ESRI-free interactive map frontend |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add Zenodo and Dataverse tokens
```

## Output

All data writes to a configurable base path set in `.env`. The repo contains only scripts, logs, and manifests — never data files.

## Data Source

EPA AirToxScreen 2020 Assessment: <https://www.epa.gov/AirToxScreen>
