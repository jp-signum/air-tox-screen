# AGOL Layer Inventory

**Date:** 2026-09-09  
**Author:** PJM  
**Purpose:** Documents the manual discovery process used to identify all ArcGIS feature layers across the AirToxScreen 2020 tool and the 2017-2019 archived tool. This work preceded and informs `discover_agol.py`.

---

## Discovery Method

### 2020 Tool

The 2020 tool is an ArcGIS Experience Builder app (`item ID: a0deb771dbcd40d0a46fbe83adc51747`). The initial naive approach — parsing `dataSources` from the app config JSON — only returned one layer. The full layer inventory required two additional steps:

1. Regex scan of the raw app config JSON for all ArcGIS service URLs and `itemId` references
2. Fetching the embedded Web Map item (`3196c644266947dd852eac929b1f5ca9`) and reading its `operationalLayers`

The app config was retrieved via:

```bash
https://www.arcgis.com/sharing/rest/content/items/a0deb771dbcd40d0a46fbe83adc51747/data?f=json
```

### 2017-2019 Tool

The 2017-2019 tool is an ArcGIS Experience Builder app (`item ID: a2eea9c204004158a85a18371d6883bc`) but unlike the 2020 tool it embeds **8 ArcGIS Dashboards** rather than a webmap directly. No service URLs or itemIds appeared in the app config itself — all data sources are resolved at runtime by the dashboard engine.

Discovery required:

1. Broad URL scan of the app config (found only dashboard URLs and a logo image)
2. Fetching each dashboard's config JSON and scanning for `itemId` keys
3. Resolving each item ID via the AGOL REST API to identify webmaps vs feature services
4. Fetching each webmap's `operationalLayers`

---

## Inaccessible Item IDs

Three item IDs referenced in the 2020 app config returned no metadata. These may be private, restricted, or already removed.

```bash
02c9412ef06b45d8bf8d865d28748a02 | Unknown | Inaccessible as of 2026-09-09 | referenced in 2020 Experience Builder app config
1f16a86caeb94833937eaa93e23c7144 | Unknown | Inaccessible as of 2026-09-09 | referenced in 2020 Experience Builder app config
67c3aa5687444794b12e81da617ece6a | Unknown | Inaccessible as of 2026-09-09 | referenced in 2020 Experience Builder app config
```

---

## Complete Layer Inventory

### 2020 Tool

| Layer | Service URL | Type | Notes |
| ------- | ------------- | ------ | ------- |
| Total Cancer Risk | `Cancer_Risk_2020/FeatureServer/0` | Polygon | 5,808,484 census block features — largest layer |
| Post-publication Corrections | `Cancer_Risk_2020_Caveats/FeatureServer/0` | Unknown | Block-level corrections; found only via webmap inspection |
| Facility Emissions | `point_fac_2020/FeatureServer/0` | Point | 58,055 features |
| Ambient Monitors | `Air_Toxics_Ambient_Monitoring_Sites_ATS2020/FeatureServer/0` | Point | |
| Ambient Monitors (layer 2) | `Air_Toxics_Ambient_Monitoring_Sites_ATS2020/FeatureServer/1` | Unknown | Second layer in same service |

All services hosted under: `https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/`

The `Cancer_Risk_(2020)/MapServer` is a tiled rendering service for display performance. The underlying vector data is captured via the FeatureServer above.

---

### 2019 Layers

| Layer | Service URL | Type | Notes |
| ------- | ------------- | ------ | ------- |
| Cancer Risk | `t2019_AirToxScreen_Cancer_Risks/FeatureServer/6` | Polygon | Layer index 6, not 0 |
| Tract Corrections | `2019_AirToxScreen_Caveat_Tracts/FeatureServer/6` | Polygon | Tract-level, not block-level |
| Facility Emissions | `point_fac_2019/FeatureServer/0` | Point | |
| Ambient Monitors | `Monitor_Data_2019/FeatureServer/1` | Point | |
| Risk by Pollutant | `_AirToxScreen_2019_Risk_by_Air_Toxics_US_EPA_OAR_OAQPS/FeatureServer` | Unknown | 2019 only |
| Risk by Source Type | `AirToxScreen_2019_Risk_Source_Type_US_EPA_OAR_OAQPS/FeatureServer` | Unknown | 2019 only |
| Respiratory HI | `NATA2019_RespHI_with_Pollutants_SourceGroups/FeatureServer/2` | Polygon | 2019 only |
| Neurological HI | `NATA2019_NeuroHI_with_Pollutants_SourceGroups/FeatureServer/3` | Polygon | 2019 only |
| Liver HI | `NATA2019_LiverHI_with_Pollutants_SourceGroups/FeatureServer/1` | Polygon | 2019 only |
| Kidney HI | `NATA2019_KidneyHI_Pollutants_SourceGroups/FeatureServer/0` | Polygon | 2019 only |
| Immunological HI | `NATA2019_Immunological_HI_Pollutants_SourceGroups/FeatureServer/0` | Polygon | 2019 only |

---

### 2018 Layers

| Layer | Service URL | Type | Notes |
| ------- | ------------- | ------ | ------- |
| Cancer Risk | `NATA2018_for_AirToxScreen/FeatureServer/1` | Polygon | |
| Tract Corrections | `Tract_Changes_2018/FeatureServer/0` | Polygon | |
| Ambient Monitors | `Monitoring_Data_2018/FeatureServer/0` | Point | |
| Facility Emissions | `point_2018/FeatureServer/0` | Point | |

---

### 2017 Layers

| Layer | Service URL | Type | Notes |
| ------- | ------------- | ------ | ------- |
| Cancer Risk | `ATS_Risk_View/FeatureServer/0` | Polygon | |
| Tract Corrections | `tract_changes_v2/FeatureServer/0` | Polygon | |
| Ambient Monitors | `AirToxScreen_AMA_AnnualMonitoring_2017_V2/FeatureServer/0` | Point | |
| Facility Emissions | `pt_fac_2017_inc_caveats/FeatureServer/0` | Point | Caveats included in layer name |

---

### Tribal Boundary Layers (present across all 2017-2019 maps)

These are EPA-hosted environmental justice context layers unique to this tool. Not generic ESRI basemap data — archive these.

| Layer | Service URL |
| ------- | ------------- |
| Alaskan Tribal Areas | `BND___Alaska_Native_Villages/FeatureServer/1` |
| Alaska Native Allotments | `BND___Alaska_Native_Allotments/FeatureServer/0` |
| Off-Reservation Trust Lands | `BND___American_Indian_Off_Reservation_Trust_Lands/FeatureServer/3` |
| American Indian Reservations | `BND___American_Indian_Reservations/FeatureServer/2` |

**Note:** These layers do not appear in the 2020 tool.

---

## Key Findings

**Schema differences across years**

- Caveats layer changed from census **tracts** (2017-2019) to census **blocks** (2020) — no crosswalk exists
- Noncancer hazard breakdowns (respiratory, neurological, liver, kidney, immunological) only exist for 2019, not 2017 or 2018
- Risk by pollutant and risk by source type breakdown layers only exist for 2019

**Architecture differences**

- 2020 tool: Experience Builder → Web Map → Feature Services
- 2017-2019 tool: Experience Builder → 8 Dashboards → Web Maps → Feature Services
- This means `discover_agol.py` must handle two completely different traversal strategies

**Layers to skip**

- `states_territories/FeatureServer/0` — generic ESRI reference layer
- `counties_t/FeatureServer/0` — generic ESRI reference layer
- `Cancer_Risk_(2020)/MapServer` — tiled rendering service, vector data captured via FeatureServer
- `Cancer_Risk_2018/MapServer` (tiles.arcgis.com) — same, rendering only

---

## Dashboard Inventory (2017-2019 tool)

| Dashboard ID | Title |
| -------------- | ------- |
| `57fd7e82a6a14d69b7a1a596e53cc818` | 2019 AirToxScreen Respiratory HI Dashboard |
| `9c69b2e7355a47e0bb3719a8764d927b` | 2019 AirToxScreen Liver Dashboard |
| `a42d668c24f641f78eb954068b04b828` | 2019 AirToxScreen Cancer Risk Dashboard |
| `c415a94649d54dd2a458e1523789b6e0` | 2019 AirToxScreen Kidney Dashboard |
| `c90f8b837b96488987328ce2261f5a9b` | 2019 AirToxScreen Immunological HI Dashboard |
| `eb19135c2eb5429c9703bb460fbb644a` | 2019 AirToxScreen Neurological Dashboard |
| `f529c71873214db794a53dbcf165f2e6` | 2018 AirToxScreen Cancer Risk Dashboard |
| `fb6e6b70c7e2480c8ef88cc8e9c061ac` | 2017 AirToxScreen Cancer Risk Dashboard |
