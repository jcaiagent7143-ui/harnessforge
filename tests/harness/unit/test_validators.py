"""Unit tests for the validators module."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.blueprints import load_blueprint
from harness.provision import provision_sync
from harness.validators import run_checks


def test_run_checks_returns_contract_shape(tmp_repo: Path) -> None:
    provision_sync(tmp_repo, blueprint="workflow-agent", no_llm=True)
    bp = load_blueprint("workflow-agent")
    report = run_checks(bp, tmp_repo)

    assert report["schema_version"] == 1
    assert report["blueprint"] == "workflow-agent"
    assert "summary" in report
    assert {"total", "passed", "failed"} <= set(report["summary"].keys())
    assert isinstance(report["checks"], list)
    assert report["checks"]
    for c in report["checks"]:
        assert {"name", "status", "duration_ms", "messages"} <= set(c.keys())
        assert c["status"] in {"pass", "fail", "skipped", "error"}


def test_structure_validator_passes_on_fresh_bootstrap(tmp_repo: Path) -> None:
    provision_sync(tmp_repo, blueprint="rag-agent", no_llm=True)
    bp = load_blueprint("rag-agent")
    report = run_checks(bp, tmp_repo, only="structure")
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 0
    assert report["checks"][0]["status"] == "pass"


def test_structure_validator_fails_when_file_deleted(tmp_repo: Path) -> None:
    provision_sync(tmp_repo, blueprint="rag-agent", no_llm=True)
    (tmp_repo / "AGENTS.md").unlink()
    bp = load_blueprint("rag-agent")
    report = run_checks(bp, tmp_repo, only="structure")
    assert report["summary"]["failed"] == 1
    assert any("AGENTS.md" in m for m in report["checks"][0]["messages"])


def test_validator_skipped_marker_not_counted_as_failure(
    tmp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Force the citation validator to find no output file: point RAG_OUT at
    # an unwritable, definitely-nonexistent path. Without this, a stray
    # /tmp/*-rag-output.json from a previous run contaminates the test
    # (caught during the real-agent eval — citations passed instead of skipping).
    monkeypatch.setenv("RAG_OUT", str(tmp_repo / "definitely_no_such_file.json"))
    provision_sync(tmp_repo, blueprint="rag-agent", no_llm=True)
    bp = load_blueprint("rag-agent")
    report = run_checks(bp, tmp_repo, only="citations")
    assert report["checks"][0]["status"] == "skipped"
    assert report["summary"]["failed"] == 0


def test_fail_fast_stops_at_first_failure(tmp_repo: Path) -> None:
    provision_sync(tmp_repo, blueprint="workflow-agent", no_llm=True)
    # Force structure to fail by deleting a required file
    (tmp_repo / "SKILLS").rename(tmp_repo / "SKILLS_moved")
    bp = load_blueprint("workflow-agent")
    report = run_checks(bp, tmp_repo, fail_fast=True)
    # First check (structure) should fail, and we should stop there
    assert report["checks"][0]["name"] == "structure"
    assert report["checks"][0]["status"] == "fail"
    assert len(report["checks"]) == 1
