# AirToxScreen

Open-source archival and reimplementation of EPA's [AirToxScreen](https://www.epa.gov/AirToxScreen) — a national air toxics screening assessment tool providing census block-level cancer risk and noncancer hazard estimates across the US.

AirToxScreen is at risk of going offline. This project preserves the full dataset and rebuilds the tool as an open, ESRI-free platform.

## Repository Structure

```bash
airtoxscreen/
├── archiver/ # capture scripts, phase pipeline, and Zenodo/Dataverse upload
└── docs/ # discovery notes and data inventory
```

## Background

EPA's AirToxScreen models ambient concentrations of 180 air toxics across the US using the National Emissions Inventory and dispersion modeling. The 2020 assessment provides cancer risk and noncancer hazard estimates at the census block level for the first time. The tool covers assessment years 2017, 2018, 2019, and 2020.

The data is currently served via ArcGIS Online and an EPA FTP server. This project captures all of it in open formats before access is lost.

## What's Being Preserved

- ArcGIS feature layers from the 2020 Experience Builder app and the 2017-2019 dashboard-based tool
- Census block-level cancer risk data (5.8M features) and tract-level noncancer hazard indices
- Facility-level emissions, ambient monitoring sites, and tribal boundary context layers
- Block-level risk data from the EPA FTP server
- Static emissions and risk summary files (county, state, facility, airport, railyard)
- Methodology documentation, technical support documents, and tool snapshots

All captured data is archived to Zenodo and Harvard Dataverse with SHA-256 checksums and a full provenance manifest.

## Getting Started

See [`archiver/`](./archiver) for setup and usage instructions.

## Data Source

EPA AirToxScreen 2020 Assessment: <https://www.epa.gov/AirToxScreen>

## License

GPL-3.0. See [LICENSE](./LICENSE) for details.
