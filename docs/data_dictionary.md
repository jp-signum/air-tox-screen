# AirToxScreen Data Dictionary

**Date:** 2026-09-15  
**Author:** PJM  
**Source:** Extracted GeoParquet field schemas cross-referenced with AirToxScreen Technical Support Documents (2017, 2018, 2020)

This dictionary covers all fields present in the extracted GeoParquet and GeoJSON files. Fields are grouped by category. For pollutant-specific cancer risk and inhalation unit risk values, refer to the Technical Support Document for the relevant assessment year.

---

## Geographic and Administrative Fields

| Field | Layers | Type | Description |
| ------- | -------- | ------ | ------------- |
| `Block_ID` | 2020 cancer risk, caveats | string | 15-digit Census block FIPS code (state + county + tract + block). Format: SSCCCTTTTTTBBBB |
| `FIPS` | 2017/2019 cancer risk, caveats, hazard index | string | Census tract FIPS code (11 digits: state + county + tract) |
| `FIPS_2017` / `FIPS_2018` | 2018 cancer risk | string | Dual FIPS codes present in 2018 layer due to tract boundary changes between years |
| `STCOFIPS` | 2017/2018/2019 cancer risk, hazard index | string | State + county FIPS (5 digits) |
| `County_FIPS_Code` | 2020 cancer risk | string | 5-digit state + county FIPS |
| `County_Name` / `County_Nam` / `County` | cancer risk layers | string | County name. Truncated to `County_Nam` in 2017/2019 layers due to field length limits |
| `County_Long` | 2018 cancer risk | string | Full county name (untruncated) |
| `State` | cancer risk, facility emissions | string | State abbreviation (2020) or full name (2017-2019) |
| `EPA_Region` | cancer risk, hazard index | integer | EPA administrative region (1-10) |
| `CBSA_NAME` | ambient monitors | string | Core-Based Statistical Area name |
| `CENSUS_TRACT_ID_2010` | ambient monitors (2017-2019) | string | 2010 census tract FIPS for monitor location |
| `CENSUS_TRACT_ID_2020` | ambient monitors (2020) | string | 2020 census tract FIPS for monitor location |

---

## Demographic and Area Fields

| Field | Layers | Type | Description |
| ------- | -------- | ------ | ------------- |
| `Population` | 2020 cancer risk | integer | Census block population (2020 Census) |
| `POP2010` | 2017/2018/2019 cancer risk, hazard index | integer | Census tract population (2010 Census) |
| `ALAND` | 2020 cancer risk | float | Land area in square meters (from Census TIGER) |
| `AWATER` | 2020 cancer risk | float | Water area in square meters (from Census TIGER) |
| `Area` | 2017/2018/2019 cancer risk, hazard index | float | Census tract area. Units vary by year — see TSD |
| `Shape__Area` | multiple layers | float | ESRI-calculated polygon area in the layer's spatial reference units |
| `Shape__Length` | multiple layers | float | ESRI-calculated polygon perimeter length |

---

## Cancer Risk Fields

All cancer risk values are in **excess cancer risk per million people** (lifetime excess cancer risk assuming 70-year continuous exposure).

### Total Risk

| Field | Layers | Description |
| ------- | -------- | ------------- |
| `Total_Cancer_Risk__per_million_` | 2020 cancer risk | Total cancer risk from all pollutants and source types combined. Primary metric of the 2020 assessment. Census block level. |
| `CR_Total_Risk` | 2017/2018/2019 cancer risk | Total cancer risk (census tract level). Equivalent to `Total_Cancer_Risk__per_million_` in 2020. |
| `Total_Cancer_Risk` | 2017/2019 cancer risk | Duplicate of `CR_Total_Risk` present in some layers — verify which is authoritative per TSD |

### Per-Pollutant Cancer Risk

Fields prefixed with `CR_` in 2017/2018/2019 layers and without prefix in 2020 cancer risk layer represent cancer risk attributable to a single pollutant. Example: `CR_Benzene` and `BENZENE` both represent cancer risk from benzene exposure in cancer risk per million.

The 2020 layer uses the pollutant name directly (e.g. `BENZENE`, `FORMALDEHYDE`) while 2017-2019 layers use `CR_` prefix (e.g. `CR_Benzene`, `CR_Formaldehyde`). The values are comparable but the naming convention changed.

Numerically prefixed pollutant fields (e.g. `F1_3_BUTADIENE`, `CR_1_3_Butadiene`) represent chemicals whose names begin with numbers — the `F` prefix and number prefix were added to comply with field name constraints that prohibit starting with a digit.

---

## Source Type Breakdown Fields

AirToxScreen attributes cancer risk to five major source type categories. All values are in cancer risk per million.

| Prefix | Full Name | Description |
| -------- | ----------- | ------------- |
| `PT_` | Point Sources | Stationary industrial point sources — facilities that report to the National Emissions Inventory |
| `OR_` | On-Road Mobile | Vehicle emissions on roads. Subdivided by vehicle class and network type (see below) |
| `NR_` | Non-Road Mobile | Off-road equipment, aircraft, locomotives, marine vessels |
| `NP_` | Non-Point | Area sources — smaller stationary sources, residential combustion, agriculture, etc. |
| `FIRE_` / `Fire_Risk` | Fires | Wildfire and prescribed burn emissions |
| `BIOGENICS_` / `Biogenics_Risk` | Biogenics | Natural biogenic emissions |
| `SECONDARY_` / `Secondary_Risk` | Secondary Formation | Pollutants formed in the atmosphere from precursor emissions |
| `BACKGROUND_` / `Background_Risk` | Background | Ambient background concentrations not attributable to modeled sources |

### On-Road Subcategories (OR_)

| Field Pattern | Description |
| --------------- | ------------- |
| `OR_LightDuty_OffNetwork_Gas` | Light-duty gasoline vehicles on non-network roads |
| `OR_LightDuty_OffNetwork_Diesel` | Light-duty diesel vehicles on non-network roads |
| `OR_HeavyDuty_OffNetwork_Gas` | Heavy-duty gasoline vehicles on non-network roads |
| `OR_HeavyDuty_OffNetwork_Diesel` | Heavy-duty diesel vehicles on non-network roads |
| `OR_LightDuty_OnNetwork_Gas` | Light-duty gasoline vehicles on road network |
| `OR_LightDuty_OnNetwork_Diesel` | Light-duty diesel vehicles on road network |
| `OR_HeavyDuty_OnNetwork_Gas` | Heavy-duty gasoline vehicles on road network |
| `OR_HeavyDuty_OnNetwork_Diesel` | Heavy-duty diesel vehicles on road network |
| `OR_Refueling` | Evaporative emissions from vehicle refueling |
| `OR_HeavyDuty_Hoteling` | Heavy-duty truck idling (hoteling) emissions |
| `OR_Total_Cancer_Risk` | Sum of all on-road subcategories (2020 only) |

**Schema note:** 2018 layer contains truncated aggregate fields `OR_`, `NR`, `NP` alongside the subcategory fields. These appear to be total on-road, non-road, and non-point aggregates with field names truncated by ESRI. Treat with caution — verify against TSD.

### Non-Road Subcategories (NR_)

| Field Pattern | Description |
| --------------- | ------------- |
| `NR_Recreational` / `NR_Recreational_inc_PleasureCra` | Recreational boats and pleasure craft |
| `NR_Construction` | Construction equipment |
| `NR_CommercialLawnGarden` / `NR_Commercial_Lawn_Garden` | Commercial lawn and garden equipment |
| `NR_ResidentialLawnGarden` / `NR_Residential_Lawn_Garden` | Residential lawn and garden equipment |
| `NR_Agriculture` | Agricultural equipment |
| `NR_CommercialEquipment` / `NR_Commercial_Equipment` | Commercial and industrial equipment |
| `NR_AllOther` / `NR_All_Other` | All other non-road sources |
| `NR_CMV_C1C2_ports` / `NR_CMV_Port_C1_and_C2` | Commercial marine vessels, Class 1-2, at ports |
| `NR_CMV_C3_ports` / `NR_CMV_Port_C3` | Commercial marine vessels, Class 3, at ports |
| `NR_CMV_C1C2C3_underway` / `NR_CMV_Underway` | Commercial marine vessels underway |
| `NR_Locomotives` | Locomotive emissions |
| `NR_Point_Airports` | Airport emissions (point source) |
| `NR__Point_Railyards` | Railyard emissions (point source) |
| `NR_Total_Cancer_Risk` | Sum of all non-road subcategories (2020 only) |

### Non-Point Subcategories (NP_)

| Field Pattern | Description |
| --------------- | ------------- |
| `NP_industrial` / `NP_Industrial` | Industrial area sources |
| `NP_CommercialCooking` | Commercial cooking emissions |
| `NP_OilGas` / `NP_Oil_and_Gas` | Oil and gas production area sources |
| `NP_SolventsCoatings` / `NP_Solvents_Coatings` | Solvent and coating use |
| `NP_StorageTransfer_BulkTerminal` / `NP_StorTrans_BulkTerm_GasStg1` | Bulk storage and transfer terminals |
| `NP_MiscellaneousNonindustrial` / `NP_Miscellaneous_Nonindustrial` | Miscellaneous non-industrial sources |
| `NP_FuelCombustion_not_RWC` / `NP_Fuel_Combustion` | Fuel combustion excluding residential wood |
| `NP_ResidentialWoodCombustionRWC` / `NP_RWC` | Residential wood combustion |
| `NP_WasteDisposal` / `NP_Waste_Disposal` | Waste disposal and treatment |
| `NP_AgricultureLivestockWaste` / `NP_AgricultureLivestock` | Agricultural livestock waste emissions |
| `NP_AgricultureLivestockSilage` | Agricultural silage emissions (2020 only) |
| `NP_Total_Cancer_Risk` | Sum of all non-point subcategories (2020 only) |

---

## Noncancer Hazard Index Fields (2019 only)

Noncancer hazard is expressed as a **Hazard Quotient (HQ)** — ratio of estimated exposure to a reference concentration. Values above 1.0 indicate potential concern. Total Hazard Index is the sum of HQs across all pollutants for that endpoint.

| Field | Layer | Description |
| ------- | ------- | ------------- |
| `Total_Respiratory_Hazard_Quotie` | 2019 respiratory HI | Total respiratory hazard index (truncated field name) |
| `Total_Neurological_Hazard_Quoti` | 2019 neurological HI | Total neurological hazard index (truncated) |
| `Total_Liver_Hazard_Quotient` | 2019 liver HI | Total liver hazard index |
| `Total_Kidney_Hazard_Quotient` | 2019 kidney HI | Total kidney hazard index |
| `Total_Immunological_Hazard_Quot` | 2019 immunological HI | Total immunological hazard index (truncated) |
| `Point` | hazard index layers | Hazard contribution from point sources |
| `Onroad` | hazard index layers | Hazard contribution from on-road mobile sources |
| `Nonroad` | hazard index layers | Hazard contribution from non-road mobile sources |
| `Nonpoint` | hazard index layers | Hazard contribution from non-point area sources |
| `Fire` | hazard index layers | Hazard contribution from fires |
| `Biogenics` | hazard index layers | Hazard contribution from biogenic sources |
| `Secondary` | hazard index layers | Hazard contribution from secondary formation |
| `Background` | hazard index layers | Hazard contribution from background concentrations |

Per-pollutant hazard quotient fields in the hazard index layers use the pollutant name directly (e.g. `BENZENE`, `TRICHLOROETHYLENE`) — these are HQ values for that specific pollutant, not cancer risk values.

---

## Ambient Monitoring Fields

| Field | Description | Units |
| ------- | ------------- | ------- |
| `AMA_SITE_CODE` / `ATA_SITE_CODE` | Air Monitoring Archive site code | — |
| `AQS_PARAMETER_CODE` | EPA Air Quality System parameter code | — |
| `AQS_PARAMETER_NAME` | Pollutant name per AQS | — |
| `NEI_POLLUTANT_NAME` | Pollutant name per National Emissions Inventory | — |
| `DURATION_DESC` | Sampling duration description (e.g. "24 HOUR") | — |
| `MEAN_UG_M3` | Annual mean concentration | µg/m³ |
| `VAR_UG_M3` | Variance of measurements | µg/m³ |
| `MAX_UG_M3` | Maximum observed concentration | µg/m³ |
| `P10_UG_M3` through `P90_UG_M3` | 10th through 90th percentile concentrations | µg/m³ |
| `N` | Number of valid measurements | count |
| `PER_BELOWMDL` | Percent of measurements below method detection limit | % |
| `MEAN_MDL_UG_M3` | Mean substituting MDL/2 for below-detection values | µg/m³ |
| `MEAN_ROS_UG_M3` | Mean using regression on order statistics for censored data | µg/m³ |
| `P10_ROS_UG_M3` through `P90_ROS_UG_M3` | Percentiles using ROS method | µg/m³ |

---

## Facility Emissions Fields

| Field | 2020 name | 2017-2019 name | Description | Units |
| ------- | ----------- | ---------------- | ------------- | ------- |
| Facility ID | `EIS_Facility_ID` | `facility_id` | EPA Emissions Inventory System facility identifier | — |
| Facility name | `Facility_Name` | `facility_name` | Facility name as reported to NEI | — |
| County | `County_or_Tribe` | `county` | County or tribal territory name | — |
| EPA Region | — | `region_cd` | EPA administrative region code | — |
| Per-pollutant emissions | `BENZENE`, `FORMALDEHYDE`, etc. | `Benzene`, `Formaldehyde`, etc. | Annual facility-level emissions for each HAP. **2020 uses ALL CAPS; 2017-2019 use Title Case.** | tons/year |
| Caveat notes | `Caveat_Notes` | `caveat_notes` | Emissions caveat description if applicable | — |

Numerically-prefixed pollutant emissions fields follow the same `F` prefix convention as the cancer risk layers.

---

## Caveat Fields

| Field | Description |
| ------- | ------------- |
| `Caveat_Type` / `caveat_type` / `Risk_Change` | Type of caveat or post-publication correction. Values: `Y` (change applied), `N` (no change), or specific caveat category codes per TSD |
| `Caveat_Notes` / `caveat_notes` / `Popup_Note` | Text description of the caveat — what changed, why, and what facilities were affected |

The 2020 caveats layer uses `Caveat_Type` and `Caveat_Notes`. The 2017-2019 caveats layers use `Risk_Change` and `Popup_Note`. These are functionally equivalent.

---

## Tribal Boundary Fields

| Field | Layer | Description |
| ------- | ------- | ------------- |
| `NAME` | tribal areas, reservations | Name of the tribal area or reservation |
| `TRIBE_NAME` | tribal areas, reservations | Name of the associated tribe |
| `NAMELSAD` | reservations, trust lands | Legal/statistical area description |
| `EPA_ID` | tribal areas, reservations | EPA tribal identifier |
| `GEOID` | reservations, trust lands | Census geographic identifier |
| `AIANNHNS` | reservations, trust lands | American Indian/Alaska Native/Native Hawaiian area name-space |
| `BIA_CODE` | tribal areas, allotments | Bureau of Indian Affairs code |
| `CLASSFP` | reservations, trust lands | Census FIPS class code |
| `PARCEL_NO` | allotments | Land parcel number |
| `CASE_TYPE` | allotments | Case type code for allotment |
| `VALID_LAND` | allotments | Land validity status |
| `ACRES_HYPE` | allotments | Parcel area in acres (hyperbolically calculated) |

---

## System Fields

| Field | Description |
| ------- | ------------- |
| `OBJECTID` | ESRI internal object ID — unique per layer, not stable across extractions |
| `GlobalID` | ESRI global unique identifier — UUID format |
| `Shape__Area` / `Shape__Length` | ESRI-calculated geometry metrics in spatial reference units |

---

## Schema Differences Across Assessment Years

| Element | 2017 | 2018 | 2019 | 2020 |
| --------- | ------ | ------ | ------ | ------ |
| Geographic unit | Census tract | Census tract | Census tract | Census block |
| Total risk field name | `CR_Total_Risk` | `CR_Total_Risk` | `CR_Total_Risk` | `Total_Cancer_Risk__per_million_` |
| Per-pollutant prefix | `CR_` | `CR_` | `CR_` | None (raw pollutant name) |
| Facility emissions case | Title_Case | Title_Case | Title_Case | ALL_CAPS |
| Facility ID field | `facility_id` | `facility_id` | `facility_id` | `EIS_Facility_ID` |
| Noncancer hazard layers | No | No | Yes (5 endpoints) | No |
| Risk by pollutant layer | No | No | Yes | No |
| Risk by source type layer | No | No | Yes | No |
| Tribal boundary layers | Yes | Yes | Yes | No |
| Caveats geometry | Tract | Tract | Tract | Block |
| Caveat field names | `Risk_Change`, `Popup_Note` | `Risk_Change`, `Popup_Note` | `Risk_Change`, `Popup_Note` | `Caveat_Type`, `Caveat_Notes` |
| Population vintage | 2010 Census | 2010 Census | 2010 Census | 2020 Census |
| FIPS vintage | 2010 tracts | 2017 + 2018 tracts (dual) | 2010 tracts | 2020 blocks |

**The dual FIPS fields in the 2018 layer** (`FIPS_2017`, `FIPS_2018`, `STCOFIPS_2017`, `STCOFIPS_2018`) reflect that the 2018 assessment was conducted using 2017 NEI geography but reported against 2018 Census tract boundaries. No crosswalk is provided — analysts should verify which FIPS vintage matches their use case.

---

## Truncated Field Names

ESRI feature services enforce a maximum field name length of 31 characters. Several descriptive field names are truncated:

| Truncated | Likely full name |
| ----------- | ----------------- |
| `Total_Respiratory_Hazard_Quotie` | Total Respiratory Hazard Quotient |
| `Total_Neurological_Hazard_Quoti` | Total Neurological Hazard Quotient |
| `Total_Immunological_Hazard_Quot` | Total Immunological Hazard Quotient |
| `County_Nam` | County Name |
| `NR_Recreational_inc_PleasureCra` | NR Recreational including Pleasure Craft |
| `NR__Point_Railyards` | NR Point Railyards (double underscore is a typo in source data) |
| `OR_HeavyDuty_OffNetwork_Diesel_` | OR Heavy Duty Off-Network Diesel Cancer Risk |
| `OR_LightDuty_OffNetwork_Diesel_` | OR Light Duty Off-Network Diesel Cancer Risk |
| `NR_CommercialEquipment_Cancer_R` | NR Commercial Equipment Cancer Risk |
| `ARSENIC_COMPOUNDS_INORGANIC_INC` | Arsenic Compounds Inorganic Including Arsine |
| `ARSENIC_COMPOUNDS_INORGANIC_INC` | Arsenic Compounds Inorganic Including Arsine |
| `F4_4__METHYLENEDIPHENYL_DIISOCY` | 4,4'-Methylenediphenyl Diisocyanate (MDI) |

---

## Units Reference

| Data type | Units |
| ----------- | ------- |
| Cancer risk | Excess cancer cases per million people (lifetime, 70-year continuous exposure) |
| Noncancer hazard | Hazard Quotient (dimensionless ratio; >1.0 indicates potential concern) |
| Ambient concentrations | µg/m³ (micrograms per cubic meter) |
| Facility emissions | Tons per year |
| Area | Square meters (ALAND, AWATER) or ESRI spatial reference units (Shape__Area) |
| Coordinates | Decimal degrees, WGS84 (EPSG:4326) |
