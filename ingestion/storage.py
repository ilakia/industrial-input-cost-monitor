"""Store raw files exactly as received, with a metadata file next to each one.

Idempotent: saving identical content twice keeps one copy. Changed content (for example
a revised month) is kept as a new version, so history is never overwritten.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from ingestion import config

log = logging.getLogger(__name__)


def _source_dir(source: str, raw_dir: Path | None) -> Path:
    folder = (raw_dir or config.RAW_DIR) / source
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _read_metadata(source_dir: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(source_dir.glob("*.meta.json"))]


def save_raw(
    source: str,
    logical_name: str,
    content: bytes,
    source_url: str,
    raw_dir: Path | None = None,
) -> tuple[Path, bool]:
    """Save content under raw/<source>/. Returns (path, is_new)."""
    folder = _source_dir(source, raw_dir)
    sha256 = hashlib.sha256(content).hexdigest()

    # Same logical file with the same fingerprint already stored -> nothing to do
    for meta in _read_metadata(folder):
        if meta["logical_name"] == logical_name and meta["sha256"] == sha256:
            log.info("%s/%s unchanged, already stored as %s", source, logical_name, meta["file"])
            return folder / meta["file"], False

    # The short hash in the file name keeps versions of the same logical file apart
    stem, dot, suffix = logical_name.rpartition(".")
    file_name = f"{stem}__{sha256[:12]}.{suffix}" if dot else f"{logical_name}__{sha256[:12]}"
    path = folder / file_name
    path.write_bytes(content)

    meta = {
        "logical_name": logical_name,
        "file": file_name,
        "sha256": sha256,
        "source_url": source_url,
        "ingested_at": datetime.now(UTC).isoformat(),
        "size_bytes": len(content),
    }
    Path(f"{path}.meta.json").write_text(json.dumps(meta, indent=2))
    log.info("stored new file %s/%s", source, file_name)
    return path, True


def latest_files(source: str, raw_dir: Path | None = None) -> list[dict]:
    """Newest stored version of each logical file, with its metadata and full path."""
    folder = _source_dir(source, raw_dir)
    newest: dict[str, dict] = {}
    for meta in _read_metadata(folder):
        current = newest.get(meta["logical_name"])
        # ISO timestamps sort correctly as strings
        if current is None or meta["ingested_at"] >= current["ingested_at"]:
            newest[meta["logical_name"]] = meta
    result = []
    for name in sorted(newest):
        meta = dict(newest[name])
        meta["path"] = folder / meta["file"]
        result.append(meta)
    return result


def has_logical_file(source: str, logical_name: str, raw_dir: Path | None = None) -> bool:
    folder = _source_dir(source, raw_dir)
    return any(meta["logical_name"] == logical_name for meta in _read_metadata(folder))
