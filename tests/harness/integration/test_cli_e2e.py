"""End-to-end CLI smoke tests — drive the `harness` binary via subprocess.

These are slower than unit tests but verify the actual installed entry
point, including Typer wiring and provider auto-detection (forced off
via --no-llm).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


def _harness_available() -> bool:
    return shutil.which("harness") is not None


pytestmark = pytest.mark.skipif(
    not _harness_available(),
    reason="`harness` CLI not on PATH — install with `pip install -e .` first",
)


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["harness", *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_cli_version_prints_version() -> None:
    r = _run("version")
    assert r.returncode == 0
    assert "harness-kit" in r.stdout


def test_cli_blueprint_list_includes_three(tmp_path: Path) -> None:
    r = _run("blueprint", "list")
    assert r.returncode == 0
    out = r.stdout
    assert "rag-agent" in out
    assert "support-agent" in out
    assert "workflow-agent" in out


def test_cli_inspect_runs(tmp_repo: Path) -> None:
    r = _run("inspect", str(tmp_repo), "--format", "json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert "languages" in data
    assert "python" in data["languages"]


def test_cli_init_writes_full_tree(tmp_repo: Path) -> None:
    r = _run("init", str(tmp_repo), "--no-llm", "--blueprint", "workflow-agent")
    assert r.returncode == 0, r.stderr
    for rel in ("AGENTS.md", "SOUL.md", "TOOLS.md", "MEMORY.md", "harness.config.json"):
        assert (tmp_repo / rel).exists()


def test_cli_init_then_verify_then_sync_check(tmp_repo: Path) -> None:
    r1 = _run("init", str(tmp_repo), "--no-llm", "--blueprint", "rag-agent")
    assert r1.returncode == 0, r1.stderr

    # verify should exit 0 (structure passes, others skip)
    r2 = _run("verify", str(tmp_repo), "--json")
    assert r2.returncode == 0, r2.stderr
    payload = json.loads(r2.stdout)
    assert payload["blueprint"] == "rag-agent"
    assert payload["summary"]["failed"] == 0

    # sync --check on a clean repo should exit 0
    r3 = _run("sync", str(tmp_repo), "--check")
    assert r3.returncode == 0, r3.stderr


def test_cli_sync_check_detects_drift(tmp_repo: Path) -> None:
    r1 = _run("init", str(tmp_repo), "--no-llm", "--blueprint", "workflow-agent")
    assert r1.returncode == 0

    # Edit a generated file
    (tmp_repo / "AGENTS.md").write_text("# user override\n")

    r2 = _run("sync", str(tmp_repo), "--check")
    assert r2.returncode != 0
    assert "drift" in r2.stdout.lower() or "drift" in r2.stderr.lower()


def test_cli_verify_no_config_exits_3(tmp_path: Path) -> None:
    r = _run("verify", str(tmp_path), "--json")
    assert r.returncode == 3


def test_cli_doctor_runs(tmp_path: Path) -> None:
    r = _run("doctor", str(tmp_path))
    assert r.returncode == 0
    assert "harness-kit" in r.stdout


def test_cli_blueprint_show_prints_spec() -> None:
    r = _run("blueprint", "show", "rag-agent")
    assert r.returncode == 0
    assert "rag-agent" in r.stdout
    assert "RAG Agent" in r.stdout


def test_cli_skills_list_runs(tmp_repo: Path) -> None:
    r = _run("init", str(tmp_repo), "--no-llm", "--blueprint", "rag-agent")
    assert r.returncode == 0
    r2 = _run("skills", "list", str(tmp_repo))
    assert r2.returncode == 0
    # Should include catalog skills + local skills
    assert "chunk-and-embed" in r2.stdout or "answer-with-citations" in r2.stdout
