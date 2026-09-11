import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

import requests
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log

from config import EPA_FILES_DIR, MANIFESTS_DIR
from utils.logger import get_logger
from utils.manifest import load_manifest, save_manifest
from utils.checksums import sha256

logger = get_logger("download_epa_files")


@retry(
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def download_file(url: str, dest: Path) -> None:
    logger.debug(f"GET {url}")
    response = requests.get(url, timeout=60, stream=True)
    response.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    time.sleep(0.5)


def safe_filename(url: str) -> str:
    return url.split("/")[-1].split("?")[0]


def download_all(manifest_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    files = manifest.get("files", [])
    logger.info(f"Downloading {len(files)} files from {manifest_path.name}")

    EPA_FILES_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for entry in files:
        url = entry.get("url")
        if not url:
            continue

        filename = safe_filename(url)
        dest = EPA_FILES_DIR / filename

        if dest.exists():
            logger.info(f"Already exists, skipping: {filename}")
            results.append({
                "url": url,
                "filename": filename,
                "status": "skipped",
                "sha256": sha256(dest),
            })
            continue

        logger.info(f"Downloading: {filename}")
        try:
            download_file(url, dest)
            checksum = sha256(dest)
            size = dest.stat().st_size
            logger.info(f"  OK ({size:,} bytes) sha256={checksum[:12]}...")
            results.append({
                "url": url,
                "filename": filename,
                "dest": str(dest),
                "status": "ok",
                "size_bytes": size,
                "sha256": checksum,
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning(f"  Failed: {e}")
            results.append({
                "url": url,
                "filename": filename,
                "status": "error",
                "error": str(e),
            })

    success = sum(1 for r in results if r["status"] in ("ok", "skipped"))
    logger.info(f"Done: {success}/{len(files)} files")

    download_manifest = {
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(manifest_path),
        "output_dir": str(EPA_FILES_DIR),
        "file_count": len(files),
        "success_count": success,
        "files": results,
    }

    out = save_manifest(download_manifest, MANIFESTS_DIR, "epa_files_download")
    logger.info(f"Download manifest saved to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download EPA AirToxScreen files")
    parser.add_argument("--manifest", required=True, help="Path to EPA crawl manifest JSON")
    args = parser.parse_args()

    download_all(Path(args.manifest))
