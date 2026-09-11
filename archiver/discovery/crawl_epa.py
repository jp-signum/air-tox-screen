import time
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log

from config import EPA_AIRTOXSCREEN_URL, PHASE_DIRS, init_dirs
from utils.logger import get_logger
from utils.manifest import save_manifest

logger = get_logger("crawl_epa")

BASE_DOMAIN = "www.epa.gov"
AIRTOXSCREEN_PATH = "/AirToxScreen"

# file extensions we want to capture
CAPTURE_EXTENSIONS = {
    ".pdf", ".xlsx", ".xls", ".csv", ".zip",
    ".shp", ".geojson", ".json", ".xml", ".txt"
}


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def get_page(url: str) -> requests.Response:
    logger.debug(f"GET {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(0.5)
    return response


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def head_file(url: str) -> dict:
    logger.debug(f"HEAD {url}")
    response = requests.head(url, timeout=30, allow_redirects=True)
    time.sleep(0.5)
    return {
        "url": url,
        "content_type": response.headers.get("Content-Type", ""),
        "content_length": response.headers.get("Content-Length"),
        "last_modified": response.headers.get("Last-Modified"),
        "etag": response.headers.get("ETag"),
        "status_code": response.status_code,
    }


def is_airtoxscreen_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc == BASE_DOMAIN
        and parsed.path.startswith(AIRTOXSCREEN_PATH)
    )


def is_file_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in CAPTURE_EXTENSIONS)


def crawl(start_url: str) -> tuple[list[dict], list[str]]:
    visited_pages = set()
    found_files = []
    found_file_urls = set()
    queue = [start_url]

    while queue:
        url = queue.pop(0)
        if url in visited_pages:
            continue

        visited_pages.add(url)
        logger.info(f"Crawling: {url}")

        try:
            response = get_page(url)
            soup = BeautifulSoup(response.text, "lxml")

            for tag in soup.find_all("a", href=True):
                href = tag["href"]
                absolute = urljoin(url, href)
                parsed = urlparse(absolute)

                # strip fragments and query strings for deduplication
                clean = parsed._replace(fragment="", query="").geturl()

                if is_file_url(clean) and clean not in found_file_urls:
                    logger.info(f"  Found file: {clean}")
                    found_file_urls.add(clean)
                    meta = head_file(clean)
                    meta["link_text"] = tag.get_text(strip=True)
                    meta["found_on"] = url
                    found_files.append(meta)

                elif is_airtoxscreen_url(clean) and clean not in visited_pages:
                    queue.append(clean)

        except Exception as e:
            logger.warning(f"  Failed to crawl {url}: {e}")

    logger.info(f"Crawled {len(visited_pages)} pages, found {len(found_files)} files")
    return found_files, list(visited_pages)


if __name__ == "__main__":
    init_dirs()
    PHASE_DIRS[0].mkdir(parents=True, exist_ok=True)

    files, pages = crawl(EPA_AIRTOXSCREEN_URL)

    manifest = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "start_url": EPA_AIRTOXSCREEN_URL,
        "pages_crawled": len(pages),
        "files_found": len(files),
        "pages": pages,
        "files": files,
    }

    out = save_manifest(manifest, PHASE_DIRS[0], "epa_crawl")
    logger.info(f"Manifest saved to {out}")
