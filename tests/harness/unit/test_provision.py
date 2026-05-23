"""Unit tests for the provision orchestrator."""

from __future__ import annotations

from pathlib import Path

import pytest

import harness
from harness.config import CONFIG_FILENAME, HarnessConfig
from harness.manifest import MANIFEST_FILENAME, Manifest, detect_drift
from harness.provision import provision_sync


@pytest.mark.parametrize(
    "blueprint",
    ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"],
)
def test_provision_writes_full_tree(tmp_repo: Path, blueprint: str) -> None:
    provision_sync(tmp_repo, blueprint=blueprint, no_llm=True)

    # All standard files exist
    for rel in ("AGENTS.md", "SOUL.md", "TOOLS.md", "MEMORY.md", CONFIG_FILENAME, MANIFEST_FILENAME):
        assert (tmp_repo / rel).exists(), f"{rel} not written for {blueprint}"

    # harness.config.json reflects the chosen blueprint
    cfg = HarnessConfig.load(tmp_repo / CONFIG_FILENAME)
    assert cfg.blueprint == blueprint
    assert cfg.harness_version == harness.__version__

    # SKILLS/ rendered
    assert (tmp_repo / "SKILLS").is_dir()
    skills = list((tmp_repo / "SKILLS").iterdir())
    assert skills, f"no SKILLS rendered for {blueprint}"

    # IDE adapters
    for rel in (".claude/CLAUDE.md", ".cursor/rules", ".continue/config.json", ".windsurf/rules"):
        assert (tmp_repo / rel).exists()


def test_provision_dry_run_writes_nothing(tmp_repo: Path) -> None:
    result = provision_sync(tmp_repo, no_llm=True, dry_run=True)
    assert result.dry_run
    assert result.written == []
    # Plan still computed
    assert result.plan.files
    # Nothing on disk
    assert not (tmp_repo / "AGENTS.md").exists()


def test_provision_blueprint_wins_over_adapter_for_AGENTS_md(tmp_repo: Path) -> None:
    """The blueprint-rendered AGENTS.md (richer) should beat the codex
    adapter's AGENTS.md (generic). Provision dedupes paths, last wins."""
    provision_sync(tmp_repo, blueprint="rag-agent", no_llm=True)
    text = (tmp_repo / "AGENTS.md").read_text()
    # rag-agent blueprint's content has the loop description
    assert "RAG agent" in text or "retrieved" in text
    # generic codex template has different shape — make sure it didn't win
    assert "## Project" not in text or "RAG" in text


def test_provision_sync_with_check_detects_drift(tmp_repo: Path) -> None:
    provision_sync(tmp_repo, no_llm=True)
    # Drift the AGENTS.md
    (tmp_repo / "AGENTS.md").write_text("user edited this")
    manifest = Manifest.load(tmp_repo / MANIFEST_FILENAME)
    drifted = detect_drift(tmp_repo, manifest)
    assert any(e.path == "AGENTS.md" for e in drifted)


def test_provision_refuses_to_overwrite_user_files(tmp_repo: Path) -> None:
    """A user-authored AGENTS.md (not in manifest) is left alone on first init."""
    (tmp_repo / "AGENTS.md").write_text("# Hand-written by the user\n")
    result = provision_sync(tmp_repo, blueprint="rag-agent", no_llm=True)
    # The file we put there should be preserved
    assert (tmp_repo / "AGENTS.md").read_text() == "# Hand-written by the user\n"
    # And it should be reported as skipped
    skipped_rels = [p.relative_to(tmp_repo) for p in result.skipped]
    assert Path("AGENTS.md") in skipped_rels


def test_provision_force_overwrites_user_files(tmp_repo: Path) -> None:
    (tmp_repo / "AGENTS.md").write_text("# Hand-written by the user\n")
    provision_sync(tmp_repo, blueprint="rag-agent", no_llm=True, force=True)
    assert "Hand-written" not in (tmp_repo / "AGENTS.md").read_text()
    assert "RAG" in (tmp_repo / "AGENTS.md").read_text() or "retrieved" in (tmp_repo / "AGENTS.md").read_text()


def test_provision_filters_adapters(tmp_repo: Path) -> None:
    provision_sync(
        tmp_repo, blueprint="workflow-agent", no_llm=True, adapters=["claude-code"]
    )
    cfg = HarnessConfig.load(tmp_repo / CONFIG_FILENAME)
    assert cfg.adapters == ["claude-code"]
    assert (tmp_repo / ".claude" / "CLAUDE.md").exists()
    assert not (tmp_repo / ".cursor" / "rules").exists()


def test_provision_no_skills_skips_SKILLS(tmp_repo: Path) -> None:
    provision_sync(tmp_repo, blueprint="rag-agent", no_llm=True, no_skills=True)
    assert not (tmp_repo / "SKILLS").exists()


def test_provision_idempotent_second_run(tmp_repo: Path) -> None:
    """A second `init --no-llm` on a fresh-bootstrapped repo finds no drift."""
    provision_sync(tmp_repo, no_llm=True)
    result = provision_sync(tmp_repo, no_llm=True)
    assert result.drifted == []
