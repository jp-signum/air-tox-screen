import json
from datetime import datetime, timezone
from pathlib import Path


def save_manifest(data: dict, path: Path, name: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    out = path / f"{name}_{timestamp}.json"
    with open(out, 'w') as f:
        json.dump(data, f, indent=2)
    return out


def load_manifest(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)
