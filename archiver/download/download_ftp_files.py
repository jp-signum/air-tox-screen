import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from config import FTP_DIR, MANIFESTS_DIR
from utils.logger import get_logger
from utils.manifest import load_manifest, save_manifest
from utils.checksums import sha256

logger = get_logger("download_ftp_files")


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(dest) + ".tmp")

    try:
        subprocess.run(
            [
                "wget",
                "--continue",
                "--tries=10",
                "--wait=2",
                "--random-wait",
                "--timeout=60",
                "--read-timeout=300",
                "--retry-connrefused",
                # "--no-verbose",
                "--output-document", str(tmp),
                url,
            ],
            check=True,
            # capture_output=True,
        )
        tmp.rename(dest)
    except subprocess.CalledProcessError as e:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"wget failed for {url}: {e.stderr.decode().strip()}")


def validate_size(actual: int, expected: int | None) -> bool:
    if expected is None:
        return True
    # manifest sizes are abbreviated (e.g. "2.7M") so allow 5% tolerance
    return abs(actual - expected) / max(expected, 1) < 0.05


def dest_path(file_entry: dict) -> Path:
    path = file_entry.get("path", "")
    relative = path.lstrip("/")
    return FTP_DIR / relative


def download_all(manifest_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    files = manifest.get("files", [])
    logger.info(f"Mirroring {len(files)} files from {manifest_path.name}")

    FTP_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for i, entry in enumerate(files, 1):
        url = entry.get("url")
        if not url:
            continue

        dest = dest_path(entry)

        if dest.exists():
            checksum = sha256(dest)
            size = dest.stat().st_size
            logger.info(f"[{i}/{len(files)}] Skipping (exists): {dest.name}")
            results.append({
                "url": url,
                "dest": str(dest),
                "status": "skipped",
                "size_bytes": size,
                "sha256": checksum,
            })
            continue

        logger.info(f"[{i}/{len(files)}] Downloading: {dest.name}")
        try:
            download_file(url, dest)
            checksum = sha256(dest)
            size = dest.stat().st_size
            expected = entry.get("size_bytes")
            size_ok = validate_size(size, expected)
            if not size_ok:
                logger.warning(f"  Size mismatch: expected ~{expected}, got {size}")
            logger.info(f"  OK ({size / 1024**2:.1f} MB) sha256={checksum[:12]}...")
            results.append({
                "url": url,
                "dest": str(dest),
                "status": "ok",
                "size_bytes": size,
                "expected_size_bytes": expected,
                "size_match": size_ok,
                "sha256": checksum,
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning(f"  Failed: {e}")
            if dest.exists():
                dest.unlink()
            results.append({
                "url": url,
                "dest": str(dest),
                "status": "error",
                "error": str(e),
            })

    success = sum(1 for r in results if r["status"] in ("ok", "skipped"))
    errors = [r for r in results if r["status"] == "error"]
    size_mismatches = [r for r in results if r.get("size_match") is False]

    logger.info(f"Done: {success}/{len(files)} files")
    if errors:
        logger.warning(f"{len(errors)} errors — rerun to retry")
    if size_mismatches:
        logger.warning(f"{len(size_mismatches)} size mismatches — inspect before uploading")

    download_manifest = {
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(manifest_path),
        "output_dir": str(FTP_DIR),
        "file_count": len(files),
        "success_count": success,
        "error_count": len(errors),
        "size_mismatch_count": len(size_mismatches),
        "files": results,
    }

    out = save_manifest(download_manifest, MANIFESTS_DIR, "ftp_download")
    logger.info(f"Download manifest saved to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mirror EPA AirToxScreen FTP data")
    parser.add_argument("--manifest", required=True, help="Path to FTP crawl manifest JSON")
    args = parser.parse_args()

    download_all(Path(args.manifest))
