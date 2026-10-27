"""Idempotency: storing the same content twice must not create a second copy."""

from ingestion import storage


def data_files(folder):
    return [p for p in folder.iterdir() if not p.name.endswith(".meta.json")]


def test_same_content_is_stored_once(tmp_path):
    first_path, first_new = storage.save_raw("demo", "file.json", b"[1, 2]", "url", tmp_path)
    second_path, second_new = storage.save_raw("demo", "file.json", b"[1, 2]", "url", tmp_path)
    assert first_new is True
    assert second_new is False
    assert first_path == second_path
    assert len(data_files(tmp_path / "demo")) == 1


def test_changed_content_is_kept_as_new_version(tmp_path):
    storage.save_raw("demo", "file.json", b"[1, 2]", "url", tmp_path)
    storage.save_raw("demo", "file.json", b"[1, 2, 3]", "url", tmp_path)
    assert len(data_files(tmp_path / "demo")) == 2

    latest = storage.latest_files("demo", tmp_path)
    assert len(latest) == 1
    assert latest[0]["path"].read_bytes() == b"[1, 2, 3]"


def test_metadata_records_lineage(tmp_path):
    storage.save_raw("demo", "file.json", b"[]", "https://example.org/x", tmp_path)
    meta = storage.latest_files("demo", tmp_path)[0]
    assert meta["source_url"] == "https://example.org/x"
    assert len(meta["sha256"]) == 64
    assert meta["ingested_at"]
