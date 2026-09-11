import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO

import requests
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log

from utils.logger import get_logger
from utils.manifest import load_manifest, save_manifest
from config import EPA_PAGES_DIR


logger = get_logger("archive_epa_pages")

OUTPUT_DIR = EPA_PAGES_DIR


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def fetch(url: str) -> requests.Response:
    logger.debug(f"GET {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(0.5)
    return response


def write_warc_record(writer: WARCWriter, url: str, response: requests.Response) -> None:
    headers_list = list(response.headers.items())
    status_line = f"{response.status_code} {response.reason}"
    http_headers = StatusAndHeaders(status_line, headers_list, protocol="HTTP/1.1")

    payload = BytesIO(response.content)
    record = writer.create_warc_record(
        url,
        "response",
        payload=payload,
        http_headers=http_headers,
        warc_content_type=response.headers.get("Content-Type", "text/html"),
    )
    writer.write_record(record)


def archive_pages(manifest_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    pages = manifest.get("pages", [])
    logger.info(f"Archiving {len(pages)} pages from {manifest_path.name}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    warc_path = OUTPUT_DIR / f"epa_airtoxscreen_{timestamp}.warc.gz"

    results = []
    with open(warc_path, "wb") as f:
        writer = WARCWriter(f, gzip=True)

        info = {
            "software": "airtoxscreen-archiver",
            "source-manifest": manifest_path.name,
            "captured-at": datetime.now(timezone.utc).isoformat(),
        }
        writer.write_record(writer.create_warcinfo_record(str(warc_path), info))

        for url in pages:
            logger.info(f"Capturing: {url}")
            try:
                response = fetch(url)
                write_warc_record(writer, url, response)
                results.append({
                    "url": url,
                    "status": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": len(response.content),
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f"  OK ({len(response.content)} bytes)")
            except Exception as e:
                logger.warning(f"  Failed: {e}")
                results.append({
                    "url": url,
                    "status": "error",
                    "error": str(e),
                })

    logger.info(f"WARC written to {warc_path}")

    capture_manifest = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(manifest_path),
        "warc_file": str(warc_path),
        "page_count": len(pages),
        "success_count": sum(1 for r in results if r.get("status") == 200),
        "pages": results,
    }

    out = save_manifest(capture_manifest, OUTPUT_DIR, "epa_pages_capture")
    logger.info(f"Capture manifest saved to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Archive EPA AirToxScreen pages to WARC")
    parser.add_argument("--manifest", required=True, help="Path to EPA crawl manifest JSON")
    args = parser.parse_args()

    archive_pages(Path(args.manifest))
