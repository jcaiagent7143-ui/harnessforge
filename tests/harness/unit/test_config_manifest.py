"""Unit tests for HarnessConfig + Manifest."""

from __future__ import annotations

from pathlib import Path

from harness.config import HarnessConfig
from harness.manifest import (
    Manifest,
    ManifestEntry,
    build_entry,
    detect_drift,
    hash_bytes,
    hash_file,
)


def test_config_roundtrip(tmp_path: Path) -> None:
    cfg = HarnessConfig(
        harness_version="0.1.0",
        blueprint="rag-agent",
        blueprint_version="1.0.0",
        adapters=["claude-code", "cursor"],
    )
    p = tmp_path / "harness.config.json"
    cfg.save(p)
    loaded = HarnessConfig.load(p)
    assert loaded.blueprint == "rag-agent"
    assert loaded.adapters == ["claude-code", "cursor"]
    assert loaded.schema_version == 1


def test_config_extras_forward_compatible(tmp_path: Path) -> None:
    cfg = HarnessConfig(
        harness_version="0.1.0",
        blueprint="rag-agent",
        blueprint_version="1.0.0",
        extras={"future_field": "future_value"},
    )
    p = tmp_path / "harness.config.json"
    cfg.save(p)
    loaded = HarnessConfig.load(p)
    assert loaded.extras == {"future_field": "future_value"}


def test_manifest_empty_load(tmp_path: Path) -> None:
    m = Manifest.load(tmp_path / "absent.json")
    assert m.entries == []


def test_manifest_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello")
    entry = build_entry(repo_root=tmp_path, path=target, written_by="test")
    m = Manifest(harness_version="0.1.0", entries=[entry])
    p = tmp_path / "manifest.json"
    m.save(p)
    loaded = Manifest.load(p)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].path == "hello.txt"
    assert loaded.entries[0].sha256 == entry.sha256


def test_drift_detection(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello")
    entry = build_entry(repo_root=tmp_path, path=target, written_by="test")
    m = Manifest(harness_version="0.1.0", entries=[entry])

    # No drift yet
    assert detect_drift(tmp_path, m) == []

    # Edit the file
    target.write_text("modified")
    drifted = detect_drift(tmp_path, m)
    assert len(drifted) == 1
    assert drifted[0].path == "hello.txt"


def test_drift_detects_deletion(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello")
    entry = build_entry(repo_root=tmp_path, path=target, written_by="test")
    m = Manifest(harness_version="0.1.0", entries=[entry])

    target.unlink()
    drifted = detect_drift(tmp_path, m)
    assert len(drifted) == 1


def test_hash_bytes_matches_hash_file(tmp_path: Path) -> None:
    content = b"hello world"
    target = tmp_path / "x.txt"
    target.write_bytes(content)
    assert hash_bytes(content) == hash_file(target)


def test_manifest_entry_dataclass() -> None:
    e = ManifestEntry(path="x", sha256="abc", bytes=3, written_by="t")
    assert e.path == "x"
