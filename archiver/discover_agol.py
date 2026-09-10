import requests
import time
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log
import logging

from config import AGOL_REST_BASE, AGOL_ITEM_2020, AGOL_ITEM_2017, PHASE_DIRS, init_dirs
from utils.logger import get_logger
from utils.manifest import save_manifest

logger = get_logger("discover_agol")


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def get(url: str) -> dict:
    logger.debug(f"GET {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(0.5)  # polite delay between every request
    return response.json()


def fetch_app_config(item_id: str) -> dict:
    url = f"{AGOL_REST_BASE}/content/items/{item_id}/data?f=json"
    logger.info(f"Fetching app config for item {item_id}")
    return get(url)


def extract_service_urls(config: dict) -> list[str]:
    urls = set()
    data_sources = config.get("dataSources", {})
    for val in data_sources.values():
        url = val.get("url")
        if url:
            urls.add(url.rstrip("/"))
    return list(urls)


def inspect_service(service_url: str) -> dict:
    logger.info(f"Inspecting service: {service_url}")
    info = get(f"{service_url}?f=json")
    service_type = "FeatureServer" if "FeatureServer" in service_url else "MapServer"

    layers = []
    for layer in info.get("layers", []) + info.get("tables", []):
        layer_id = layer["id"]
        layer_url = f"{service_url}/{layer_id}"

        logger.info(f"  Inspecting layer {layer_id}: {layer.get('name')}")

        # layer metadata + field schema
        layer_info = get(f"{layer_url}?f=json")

        # feature count
        count_resp = get(
            f"{layer_url}/query?where=1=1&returnCountOnly=true&f=json"
        )
        feature_count = count_resp.get("count", 0)
        logger.info(f"    Feature count: {feature_count}")

        layers.append({
            "id": layer_id,
            "name": layer_info.get("name"),
            "type": layer_info.get("type"),
            "geometry_type": layer_info.get("geometryType"),
            "feature_count": feature_count,
            "spatial_reference": layer_info.get("extent", {}).get("spatialReference"),
            "fields": [
                {
                    "name": f.get("name"),
                    "type": f.get("type"),
                    "alias": f.get("alias"),
                    "domain": f.get("domain")
                }
                for f in layer_info.get("fields", [])
            ],
            "url": layer_url
        })

    return {
        "url": service_url,
        "service_type": service_type,
        "name": info.get("serviceDescription") or info.get("name"),
        "layers": layers
    }


def discover(item_id: str, label: str) -> dict:
    config = fetch_app_config(item_id)
    service_urls = extract_service_urls(config)
    logger.info(f"Found {len(service_urls)} services for {label}")

    services = []
    for url in service_urls:
        service = inspect_service(url)
        services.append(service)

    return {
        "item_id": item_id,
        "label": label,
        "service_count": len(services),
        "services": services
    }


if __name__ == "__main__":
    init_dirs()

    results = {
        "2020": discover(AGOL_ITEM_2020, "2020"),
        "2017_2019": discover(AGOL_ITEM_2017, "2017_2019")
    }

    total_features = sum(
        layer["feature_count"]
        for year in results.values()
        for service in year["services"]
        for layer in service["layers"]
    )
    logger.info(f"Total features across all layers: {total_features:,}")

    out = save_manifest(results, PHASE_DIRS[0], "agol_discovery")
    logger.info(f"Manifest saved to {out}")
