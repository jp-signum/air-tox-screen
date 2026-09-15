import time
import logging
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

import requests
import geopandas as gpd
from shapely.geometry import shape
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log

from config import AGOL_DIR, MANIFESTS_DIR
from utils.logger import get_logger
from utils.manifest import load_manifest, save_manifest

logger = get_logger("extract_agol_layers")

PAGE_SIZE = 2000
LARGE_LAYER_THRESHOLD = 100_000


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def query_page(url: str, offset: int) -> dict:
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
        "resultOffset": offset,
        "resultRecordCount": PAGE_SIZE,
    }
    response = requests.get(f"{url}/query", params=params, timeout=60)
    response.raise_for_status()
    time.sleep(0.25)
    return response.json()


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def query_page_by_range(url: str, start_oid: int, end_oid: int) -> dict:
    params = {
        "where": f"OBJECTID >= {start_oid} AND OBJECTID <= {end_oid}",
        "outFields": "*",
        "f": "geojson",
    }
    response = requests.get(f"{url}/query", params=params, timeout=60)
    response.raise_for_status()
    time.sleep(0.25)
    return response.json()


def get_live_count(url: str) -> int:
    params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    response = requests.get(f"{url}/query", params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("count", 0)


def get_max_record_count(url: str) -> int:
    params = {"f": "json"}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("maxRecordCount", PAGE_SIZE)


def features_to_geodataframe(features: list) -> gpd.GeoDataFrame:
    rows = []
    geometries = []
    for feat in features:
        props = feat.get("properties") or {}
        geom = feat.get("geometry")
        rows.append(props)
        geometries.append(shape(geom) if geom else None)
    gdf = gpd.GeoDataFrame(rows, geometry=geometries, crs="EPSG:4326")
    return gdf


def layer_suffix(layer: dict) -> str:
    """Derive geometry suffix from layer metadata."""
    category = layer.get("category", "")
    url = layer.get("url", "")
    geometry_type = layer.get("geometry_type", "")

    if "Point" in geometry_type:
        return "points"
    if category == "tribal_boundary":
        return "polygons"
    # caveats layers used tracts for 2017-2019, blocks for 2020
    if "Caveat" in url or "caveat" in url or "Changes" in url:
        for y in ["2017", "2018", "2019"]:
            if y in url:
                return "tracts"
        return "blocks"
    # main risk layers
    for y in ["2017", "2018", "2019"]:
        if y in url:
            return "tracts"
    return "blocks"


TITLE_OVERRIDES = {
    "Risk Changes (click block for more info)": "cancer_risk_caveats",
    "Tract Changes (click in the tract for more info)": "tract_caveats",
    "2019 Risk by Air Toxics — NATA19AC_CRP_CRSG": "risk_by_air_toxics",
    "2019 Risk by Source Type — NATA19AC_CRP_CRSG": "risk_by_source_type",
    "Alaskan Tribal Areas (DOI & EPA 2021)": "alaskan_tribal_areas",
    "Alaska Native Allotments (DOI & EPA 2021)": "alaska_native_allotments",
    "Off-Reservation Trust Lands (USCB & EPA 2021)": "off_reservation_trust_lands",
    "American Indian Reservations (USCB & EPA 2021)": "american_indian_reservations",
}


def safe_filename(layer: dict, fallback_year: str = "unknown") -> str:
    title = layer.get("title", "unknown")
    url = layer.get("url", "")

    year = fallback_year
    for y in ["2017", "2018", "2019", "2020"]:
        if y in url or y in title:
            year = y
            break

    if title in TITLE_OVERRIDES:
        clean = TITLE_OVERRIDES[title]
    else:
        clean = title.lower()
        for y in ["2017", "2018", "2019", "2020"]:
            clean = clean.replace(f"({y})", "").replace(y, "")
        for ch in [" ", "/", "—", "-", "(", ")", ".", ","]:
            clean = clean.replace(ch, "_")
        while "__" in clean:
            clean = clean.replace("__", "_")
        clean = clean.strip("_")

    name = f"airtoxscreen_{year}_{clean}"
    while "__" in name:
        name = name.replace("__", "_")
    return name.strip("_")


def get_oid_range(url: str) -> tuple[int, int]:
    params = {
        "where": "1=1",
        "outStatistics": '[{"statisticType":"min","onStatisticField":"OBJECTID","outStatisticFieldName":"min_oid"},{"statisticType":"max","onStatisticField":"OBJECTID","outStatisticFieldName":"max_oid"}]',
        "f": "json"
    }
    response = requests.get(f"{url}/query", params=params, timeout=30)
    response.raise_for_status()
    stats = response.json().get("features", [{}])[0].get("attributes", {})
    return stats["min_oid"], stats["max_oid"]


def write_large_layer(url: str, live_count: int, parquet_path: Path) -> int:
    import shutil

    min_oid, max_oid = get_oid_range(url)
    logger.info(f"  OID range: {min_oid} — {max_oid}")

    chunk_dir = parquet_path.parent / f"{parquet_path.stem}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    extracted = 0
    chunk_num = 0

    try:
        for start_oid in range(min_oid, max_oid + 1, PAGE_SIZE):
            end_oid = min(start_oid + PAGE_SIZE - 1, max_oid)

            page = query_page_by_range(url, start_oid, end_oid)
            features = page.get("features", [])

            if features:
                gdf_chunk = features_to_geodataframe(features)
                chunk_path = chunk_dir / f"chunk_{chunk_num:04d}.parquet"
                gdf_chunk.to_parquet(chunk_path, index=False)
                chunk_num += 1

            extracted += len(features)
            logger.info(f"  [{extracted:,}/{live_count:,}] chunk {chunk_num} written")

        logger.info(f"  Concatenating {chunk_num} chunks...")
        chunks = [gpd.read_parquet(chunk_dir / f"chunk_{i:04d}.parquet") for i in range(chunk_num)]
        combined = gpd.GeoDataFrame(pd.concat(chunks, ignore_index=True), crs="EPSG:4326")
        combined.to_parquet(parquet_path, index=False)
        logger.info(f"  Final GeoParquet written: {parquet_path.name}")

    finally:
        shutil.rmtree(chunk_dir, ignore_errors=True)

    return extracted


def write_small_layer(
    url: str,
    live_count: int,
    parquet_path: Path,
    geojson_path: Path | None,
) -> int:
    """Accumulate small layer in memory, write Parquet and optionally GeoJSON."""
    max_count = get_max_record_count(url)
    all_features = []
    offset = 0

    while True:
        page = query_page(url, offset)
        features = page.get("features", [])
        if not features:
            break
        all_features.extend(features)
        logger.info(f"  [{len(all_features):,}/{live_count:,}] fetched")
        offset += len(features)
        if len(features) < max_count:
            break

    gdf = features_to_geodataframe(all_features)
    gdf.to_parquet(parquet_path, index=False)
    logger.info(f"  Parquet written: {parquet_path.name}")

    if geojson_path:
        gdf.to_file(geojson_path, driver="GeoJSON")
        logger.info(f"  GeoJSON written: {geojson_path.name}")

    return len(all_features)


def extract_layer(layer: dict, output_dir: Path, fallback_year: str = "unknown") -> dict:
    url = layer["url"]
    title = layer["title"]
    expected_count = layer.get("feature_count", 0)
    is_point = "Point" in layer.get("geometry_type", "")
    is_large = expected_count > LARGE_LAYER_THRESHOLD

    base_name = safe_filename(layer, fallback_year)
    suffix = layer_suffix(layer)
    parquet_path = output_dir / f"{base_name}_{suffix}.parquet"
    geojson_path = output_dir / f"{base_name}.geojson" if is_point else None

    logger.info(f"Extracting: {title}")
    logger.info(f"  URL: {url}")
    logger.info(f"  Expected: {expected_count:,} | Large: {is_large}")

    live_count = get_live_count(url)
    if live_count != expected_count:
        logger.warning(
            f"  Count mismatch vs manifest: expected {expected_count:,}, live {live_count:,}"
        )

    if is_large:
        extracted = write_large_layer(url, live_count, parquet_path)
    else:
        extracted = write_small_layer(url, live_count, parquet_path, geojson_path)

    count_match = extracted == live_count
    if not count_match:
        logger.warning(f"  Extraction mismatch: extracted {extracted:,}, expected {live_count:,}")
    else:
        logger.info(f"  Validated: {extracted:,} features")

    return {
        "title": title,
        "url": url,
        "parquet_path": str(parquet_path),
        "geojson_path": str(geojson_path) if geojson_path else None,
        "expected_count": expected_count,
        "live_count": live_count,
        "extracted_count": extracted,
        "count_match": count_match,
        "is_large": is_large,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }


def extract_all(manifest_path: Path, layer_url: str | None = None) -> None:
    manifest = load_manifest(manifest_path)
    AGOL_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for year_key in ["2020", "2017_2019"]:
        year_data = manifest.get(year_key, {})
        layers = year_data.get("layers", [])

        if layer_url:
            layers = [lyr for lyr in layers if lyr.get("url") == layer_url]
            if not layers:
                continue

        logger.info(f"=== Extracting {len(layers)} layers for {year_key} ===")

        year_dir = AGOL_DIR / year_key
        year_dir.mkdir(parents=True, exist_ok=True)

        for layer in layers:
            if layer.get("error"):
                logger.warning(f"Skipping errored layer: {layer['title']}")
                results.append({
                    "title": layer["title"],
                    "url": layer.get("url"),
                    "status": "skipped",
                    "reason": layer["error"],
                })
                continue

            try:
                result = extract_layer(layer, year_dir, fallback_year="2019" if year_key == "2017_2019" else "2020")
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed: {layer['title']} — {e}")
                results.append({
                    "title": layer["title"],
                    "url": layer.get("url"),
                    "status": "error",
                    "error": str(e),
                })

    success = sum(1 for r in results if r.get("count_match"))
    logger.info(f"Complete: {success}/{len(results)} layers extracted and validated")

    out = save_manifest(
        {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "source_manifest": str(manifest_path),
            "output_dir": str(AGOL_DIR),
            "layer_count": len(results),
            "success_count": success,
            "layers": results,
        },
        MANIFESTS_DIR,
        "agol_extraction",
    )
    logger.info(f"Extraction manifest saved to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract ArcGIS feature layers to GeoParquet"
    )
    parser.add_argument(
        "--manifest", required=True, help="Path to AGOL discovery manifest JSON"
    )
    parser.add_argument(
        "--layer-url", default=None, help="Extract only the layer matching this URL (for testing)"
    )
    args = parser.parse_args()

    extract_all(Path(args.manifest), layer_url=args.layer_url)
