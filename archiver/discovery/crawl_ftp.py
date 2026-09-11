import time
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log


from config import EPA_FTP_URL, EPA_FTP_PATH, MANIFESTS_DIR
from utils.logger import get_logger
from utils.manifest import save_manifest

logger = get_logger("crawl_ftp")

BASE_URL = f"https://{EPA_FTP_URL}"
START_URL = f"{BASE_URL}{EPA_FTP_PATH}"

FILE_EXTENSIONS = {".xlsx", ".csv", ".zip", ".pdf", ".txt"}


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def get_page(url: str) -> requests.Response:
    logger.debug(f"GET {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(0.25)
    return response


def is_file(href: str) -> bool:
    return any(unquote(href).lower().endswith(ext) for ext in FILE_EXTENSIONS)


def is_directory(href: str) -> bool:
    return href.endswith("/") and not href.startswith("?") and href != "../"


def parse_size(size_text: str) -> int | None:
    size_text = size_text.strip()
    if not size_text or size_text == "-":
        return None
    multipliers = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}
    for suffix, mult in multipliers.items():
        if size_text.endswith(suffix):
            try:
                return int(float(size_text[:-1]) * mult)
            except ValueError:
                return None
    try:
        return int(size_text)
    except ValueError:
        return None


def parse_index(url: str) -> tuple[list[dict], list[str]]:
    response = get_page(url)
    soup = BeautifulSoup(response.text, "lxml")

    files = []
    subdirs = []

    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        link_tag = cols[1].find("a", href=True)
        if not link_tag:
            continue

        href = link_tag["href"]
        size_text = cols[3].get_text(strip=True) if len(cols) > 3 else ""
        modified = cols[2].get_text(strip=True) if len(cols) > 2 else ""

        if is_file(href):
            file_url = urljoin(url, href)
            files.append({
                "url": file_url,
                "name": unquote(href),
                "path": unquote(file_url.replace(BASE_URL, "")),
                "size_bytes": parse_size(size_text),
                "last_modified": modified,
            })
        elif is_directory(href):
            subdirs.append(urljoin(url, href))

    return files, subdirs


def walk(url: str) -> list[dict]:
    all_files = []
    queue = [url]
    visited = set()

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        logger.info(f"Walking: {current}")
        try:
            files, subdirs = parse_index(current)
            all_files.extend(files)
            logger.info(f"  Found {len(files)} files, {len(subdirs)} subdirs")
            queue.extend(s for s in subdirs if s not in visited and s.startswith(START_URL))
        except Exception as e:
            logger.warning(f"  Failed to walk {current}: {e}")

    return all_files


if __name__ == "__main__":
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    files = walk(START_URL)

    total_bytes = sum(f["size_bytes"] for f in files if f["size_bytes"])
    total_gb = total_bytes / 1024 ** 3
    logger.info(f"Found {len(files)} files, total size: {total_gb:.2f} GB")

    manifest = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "start_path": EPA_FTP_PATH,
        "file_count": len(files),
        "total_size_bytes": total_bytes,
        "total_size_gb": round(total_gb, 2),
        "files": files,
    }

    out = save_manifest(manifest, MANIFESTS_DIR, "ftp_crawl")
    logger.info(f"Manifest saved to {out}")
