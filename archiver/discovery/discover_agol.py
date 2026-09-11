import time
import logging
from datetime import datetime, timezone

import requests
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log

from config import AGOL_REST_BASE, AGOL_ITEM_2020, AGOL_ITEM_2017, PHASE_DIRS, init_dirs
from utils.logger import get_logger
from utils.manifest import save_manifest

logger = get_logger("discover_agol")

# --- Layers to skip (basemap reference data, tiled rendering services) ---
SKIP_URLS = {
    "states_territories",
    "counties_t",
}
SKIP_LAYER_TYPES = {"ArcGISTiledMapServiceLayer", "VectorTileLayer"}

# --- Inaccessible item IDs found in 2020 app config ---
INACCESSIBLE_ITEMS = [
    "02c9412ef06b45d8bf8d865d28748a02",
    "1f16a86caeb94833937eaa93e23c7144",
    "67c3aa5687444794b12e81da617ece6a",
]

# --- 2020 cancer risk is served as a tiled MapServer in the webmap ---
# --- but the vector data lives in a separate FeatureServer ---
# --- not referenced in the webmap operationalLayers ---
EXPLICIT_2020_LAYERS = [
    {
        "title": "Total Cancer Risk (2020)",
        "url": "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/Cancer_Risk_2020/FeatureServer/0",
        "layer_type": "ArcGISFeatureLayer",
        "category": "cancer_risk",
    }
]

# --- Tribal boundary layers present across 2017-2019 maps ---
TRIBAL_BOUNDARY_LAYERS = [
    {
        "title": "Alaskan Tribal Areas",
        "url": "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/BND___Alaska_Native_Villages/FeatureServer/1",
        "layer_type": "ArcGISFeatureLayer",
        "category": "tribal_boundary",
    },
    {
        "title": "Alaska Native Allotments",
        "url": "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/BND___Alaska_Native_Allotments/FeatureServer/0",
        "layer_type": "ArcGISFeatureLayer",
        "category": "tribal_boundary",
    },
    {
        "title": "Off-Reservation Trust Lands",
        "url": "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/BND___American_Indian_Off_Reservation_Trust_Lands/FeatureServer/3",
        "layer_type": "ArcGISFeatureLayer",
        "category": "tribal_boundary",
    },
    {
        "title": "American Indian Reservations",
        "url": "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/BND___American_Indian_Reservations/FeatureServer/2",
        "layer_type": "ArcGISFeatureLayer",
        "category": "tribal_boundary",
    },
]

# --- Risk breakdown services found in dashboard configs ---
# --- these are FeatureServer roots with multiple sublayers ---
DASHBOARD_FEATURE_SERVICES = {
    "c542501d0d664289a9945fb8e167813d": {
        "title": "2019 Risk by Air Toxics",
        "url": "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/_AirToxScreen_2019_Risk_by_Air_Toxics_US_EPA_OAR_OAQPS/FeatureServer",
        "category": "risk_breakdown",
    },
    "f38d5b4cc72242199472ec41d802b39f": {
        "title": "2019 Risk by Source Type",
        "url": "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/AirToxScreen_2019_Risk_Source_Type_US_EPA_OAR_OAQPS/FeatureServer",
        "category": "risk_breakdown",
    },
}


# --- HTTP ---

@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def get(url: str) -> dict:
    logger.debug(f"GET {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(0.5)
    return response.json()


# --- Layer filtering ---

def should_skip(url: str, layer_type: str) -> bool:
    if layer_type in SKIP_LAYER_TYPES:
        return True
    if url and any(skip in url for skip in SKIP_URLS):
        return True
    return False


# --- Layer inspection ---

def inspect_layer(
    url: str, title: str, layer_type: str, category: str = "data"
) -> dict:
    logger.info(f"  Inspecting: {title} ({url})")
    try:
        info = get(f"{url}?f=json")
        count_resp = get(f"{url}/query?where=1=1&returnCountOnly=true&f=json")
        feature_count = count_resp.get("count", 0)
        logger.info(f"    Feature count: {feature_count:,}")
        return {
            "title": title,
            "url": url,
            "layer_type": layer_type,
            "category": category,
            "geometry_type": info.get("geometryType"),
            "feature_count": feature_count,
            "spatial_reference": info.get("extent", {}).get("spatialReference"),
            "fields": [
                {
                    "name": f.get("name"),
                    "type": f.get("type"),
                    "alias": f.get("alias"),
                    "domain": f.get("domain"),
                }
                for f in info.get("fields", [])
            ],
        }
    except Exception as e:
        logger.warning(f"    Failed to inspect {url}: {e}")
        return {
            "title": title,
            "url": url,
            "layer_type": layer_type,
            "category": category,
            "error": str(e),
        }


def enumerate_sublayers(service_url: str, title: str, category: str) -> list:
    """Enumerate and inspect all sublayers within a FeatureServer root."""
    logger.info(f"Enumerating sublayers: {title} ({service_url})")
    try:
        info = get(f"{service_url}?f=json")
        sublayers = []
        for sublayer in info.get("layers", []):
            layer_id = sublayer["id"]
            layer_name = sublayer.get("name", f"layer_{layer_id}")
            url = f"{service_url}/{layer_id}"
            sublayers.append(
                inspect_layer(url, f"{title} — {layer_name}", "ArcGISFeatureLayer", category)
            )
        return sublayers
    except Exception as e:
        logger.warning(f"    Failed to enumerate sublayers for {service_url}: {e}")
        return []


# --- Webmap layer extraction ---

def layers_from_webmap(item_id: str, webmap_title: str) -> list:
    logger.info(f"Fetching webmap: {webmap_title} ({item_id})")
    data = get(f"{AGOL_REST_BASE}/content/items/{item_id}/data?f=json")
    layers = []
    for layer in data.get("operationalLayers", []):
        url = layer.get("url")
        title = layer.get("title", "")
        layer_type = layer.get("layerType", "")
        if not url or should_skip(url, layer_type):
            logger.debug(f"  Skipping: {title}")
            continue
        layers.append(inspect_layer(url, title, layer_type))
    return layers


# --- 2020 traversal: Experience Builder → webmap ---

def discover_2020() -> dict:
    logger.info("=== Discovering 2020 tool ===")
    webmap_id = "3196c644266947dd852eac929b1f5ca9"
    layers = layers_from_webmap(webmap_id, "2020 AirToxScreen Cancer Risk Map")

    for meta in EXPLICIT_2020_LAYERS:
        layers.append(
            inspect_layer(meta["url"], meta["title"], meta["layer_type"], meta["category"])
        )

    return {
        "tool": "2020",
        "app_item_id": AGOL_ITEM_2020,
        "architecture": "experience_builder_webmap",
        "webmap_item_id": webmap_id,
        "inaccessible_items": [
            {
                "item_id": i,
                "status": "inaccessible",
                "checked": datetime.now(timezone.utc).isoformat(),
            }
            for i in INACCESSIBLE_ITEMS
        ],
        "layers": layers,
    }


# --- 2017-2019 traversal: Experience Builder → dashboards → webmaps ---

DASHBOARD_IDS = {
    "57fd7e82a6a14d69b7a1a596e53cc818": "2019 Respiratory HI Dashboard",
    "9c69b2e7355a47e0bb3719a8764d927b": "2019 Liver HI Dashboard",
    "a42d668c24f641f78eb954068b04b828": "2019 Cancer Risk Dashboard",
    "c415a94649d54dd2a458e1523789b6e0": "2019 Kidney HI Dashboard",
    "c90f8b837b96488987328ce2261f5a9b": "2019 Immunological HI Dashboard",
    "eb19135c2eb5429c9703bb460fbb644a": "2019 Neurological HI Dashboard",
    "f529c71873214db794a53dbcf165f2e6": "2018 Cancer Risk Dashboard",
    "fb6e6b70c7e2480c8ef88cc8e9c061ac": "2017 Cancer Risk Dashboard",
}

WEBMAP_IDS = {
    "5c5866f7ef714d2e8ab98a4a7a2ae199": "2019 Cancer Risk Map",
    "0f3c217f06b94404addf3586de1d38b6": "2019 Respiratory HI Map",
    "19467c982c354e348b9b76f64f8d8edf": "2019 Neurological HI Map",
    "4887c67db0d448149cd61693e44a4e3f": "2018 Cancer Risk Map",
    "72da5ce0b7d643cb80e6611232727205": "2019 Liver HI Map",
    "d8dc72eff2594cb5b0dba41c827e7f0f": "2019 Kidney HI Map",
    "eff8b979df444b6984cdba8ecb5a4542": "2017 Cancer Risk Map",
    "f1cc994228fc4c2bb273a44eb2eddb4a": "2019 Immunological HI Map",
}


def discover_2017_2019() -> dict:
    logger.info("=== Discovering 2017-2019 tool ===")

    all_layers = []
    seen_urls = set()

    for item_id, title in WEBMAP_IDS.items():
        for layer in layers_from_webmap(item_id, title):
            url = layer.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                all_layers.append(layer)
            else:
                logger.debug(f"  Deduped: {layer.get('title')}")

    for meta in DASHBOARD_FEATURE_SERVICES.values():
        for sublayer in enumerate_sublayers(meta["url"], meta["title"], meta["category"]):
            url = sublayer.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                all_layers.append(sublayer)

    for layer in TRIBAL_BOUNDARY_LAYERS:
        url = layer["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            all_layers.append(
                inspect_layer(url, layer["title"], layer["layer_type"], layer["category"])
            )

    return {
        "tool": "2017_2019",
        "app_item_id": AGOL_ITEM_2017,
        "architecture": "experience_builder_dashboards_webmaps",
        "dashboards": DASHBOARD_IDS,
        "webmaps": WEBMAP_IDS,
        "layers": all_layers,
    }


# --- Main ---

if __name__ == "__main__":
    init_dirs()
    PHASE_DIRS[0].mkdir(parents=True, exist_ok=True)

    results = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "2020": discover_2020(),
        "2017_2019": discover_2017_2019(),
    }

    total = sum(
        len(v["layers"])
        for v in results.values()
        if isinstance(v, dict) and "layers" in v
    )
    logger.info(f"Total layers discovered: {total}")

    out = save_manifest(results, PHASE_DIRS[0], "agol_discovery")
    logger.info(f"Manifest saved to {out}")
