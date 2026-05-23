"""v0.2.1 — surgical fixes for issues the v0.2 stock-agent re-eval caught.

Each test pins one of the 5 fixes against regression.
"""

from __future__ import annotations

from pathlib import Path

from harness.blueprints import load_blueprint
from harness.blueprints.loader import _merge_and_prune_mcps
from harness.inspect_ import inspect_repo
from harness.profile import _resolve_python_binary, profile_from_inspection_template
from harness.provision import provision_sync


def _seed(tmp: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp


# ── Fix A: python vs python3 detection ────────────────────────────────────


def test_resolve_python_binary_returns_a_real_binary() -> None:
    """Whatever it returns, it must be `python` or `python3`."""
    py = _resolve_python_binary()
    assert py in {"python", "python3"}


def test_test_command_uses_resolved_python_binary(tmp_path: Path) -> None:
    """The default Python test command should embed the resolved binary,
    not blindly say `python` (which doesn't exist on stock macOS)."""
    _seed(tmp_path, {"README.md": "# x", "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n'})
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert profile.test_command is not None
    assert profile.test_command.startswith(_resolve_python_binary())


# ── Fix B: memory_schemas copied into user .harness/memory_schemas/ ───────


def test_memory_schemas_copied_into_user_repo_for_finance_agent(tmp_path: Path) -> None:
    """finance-agent ships positions.json + signals.json schemas.
    They must land in the user's .harness/memory_schemas/, not just
    be referenced from MEMORY.md (the v0.2 bug)."""
    _seed(tmp_path, {"README.md": "# x", "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n'})
    provision_sync(tmp_path, blueprint="finance-agent", no_llm=True)
    schema_dir = tmp_path / ".harness" / "memory_schemas"
    assert schema_dir.is_dir()
    names = {p.name for p in schema_dir.glob("*.json")}
    assert names == {"conversation.json", "positions.json", "signals.json"}


def test_memory_schemas_copied_for_rag_agent(tmp_path: Path) -> None:
    _seed(tmp_path, {"README.md": "# x", "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n'})
    provision_sync(tmp_path, blueprint="rag-agent", no_llm=True)
    schema_dir = tmp_path / ".harness" / "memory_schemas"
    assert schema_dir.is_dir()
    names = {p.name for p in schema_dir.glob("*.json")}
    assert "conversation.json" in names
    assert "rag_chunks.json" in names


# ── Fix C + D: blueprint-level MCP pruning + dedup ────────────────────────


def test_pruned_mcps_for_portfolio_cli_excludes_postgres(tmp_path: Path) -> None:
    """The v0.2 re-eval flagged: 'postgres MCP recommended for a v0.1
    single-file portfolio agent is template bloat'. The finance-agent
    blueprint declares postgres; pruning must drop it when there's no
    DB evidence."""
    _seed(
        tmp_path,
        {
            "README.md": "# stockbot\nPortfolio tracker.",
            "pyproject.toml": '[project]\nname = "stockbot"\nversion = "0.1"\ndependencies = ["yfinance"]\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    bp = load_blueprint("finance-agent")
    pruned = _merge_and_prune_mcps(profile, bp, report)
    assert "postgres" not in pruned


def test_pruned_mcps_keeps_postgres_when_sqlalchemy_present(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "README.md": "# bot",
            "pyproject.toml": '[project]\nname = "bot"\nversion = "0.1"\ndependencies = ["fastapi", "sqlalchemy"]\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    bp = load_blueprint("workflow-agent")
    pruned = _merge_and_prune_mcps(profile, bp, report)
    assert "postgres" in pruned


def test_pruned_mcps_dedupes_filesystem(tmp_path: Path) -> None:
    """v0.2 had ``filesystem`` appearing twice in AGENTS.md because
    profile.recommended_mcps + blueprint.recommended_mcps wasn't deduped."""
    _seed(tmp_path, {"README.md": "# x", "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n'})
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    bp = load_blueprint("finance-agent")
    pruned = _merge_and_prune_mcps(profile, bp, report)
    assert pruned.count("filesystem") <= 1


def test_rendered_agents_md_has_no_duplicate_mcps(tmp_path: Path) -> None:
    """End-to-end: after provision, AGENTS.md doesn't list any MCP twice."""
    _seed(tmp_path, {"README.md": "# stockbot", "pyproject.toml": '[project]\nname = "stockbot"\nversion = "0.1"\ndependencies = ["yfinance"]\n'})
    provision_sync(tmp_path, blueprint="finance-agent", no_llm=True)
    text = (tmp_path / "AGENTS.md").read_text()
    # Find the MCP block
    if "## Recommended MCP servers" in text:
        mcp_block = text.split("## Recommended MCP servers", 1)[1].split("##", 1)[0]
        entries = [line.strip() for line in mcp_block.splitlines() if line.strip().startswith("- `")]
        assert len(entries) == len(set(entries)), f"AGENTS.md has duplicate MCP entries: {entries}"


# ── Fix E: forbidden_commands pruned by evidence ──────────────────────────


def test_forbidden_commands_omits_kubectl_for_personal_cli(tmp_path: Path) -> None:
    """The v0.2 re-eval flagged: 'kubectl --context=prod*' in a personal
    portfolio CLI is template bloat that dilutes the parts that matter."""
    _seed(tmp_path, {"README.md": "# stockbot\nPortfolio tracker.", "pyproject.toml": '[project]\nname = "stockbot"\nversion = "0.1"\ndependencies = ["yfinance"]\n'})
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    joined = " ".join(profile.forbidden_commands)
    assert "kubectl" not in joined
    assert "terraform" not in joined
    assert "DROP DATABASE" not in joined


def test_forbidden_commands_includes_kubectl_when_kubernetes_present(tmp_path: Path) -> None:
    _seed(tmp_path, {"README.md": "# infra\nk8s cluster manager.", "k8s/deployment.yaml": "kind: Deployment\napiVersion: apps/v1\n"})
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    joined = " ".join(profile.forbidden_commands)
    assert "kubectl" in joined


def test_forbidden_commands_includes_drop_database_when_db_deps(tmp_path: Path) -> None:
    _seed(tmp_path, {"README.md": "# api", "pyproject.toml": '[project]\nname = "api"\nversion = "0.1"\ndependencies = ["sqlalchemy"]\n'})
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    joined = " ".join(profile.forbidden_commands)
    assert "DROP DATABASE" in joined


def test_forbidden_commands_always_includes_destructive_universals(tmp_path: Path) -> None:
    """Universal destructive commands (rm -rf, git push --force) always present."""
    _seed(tmp_path, {"README.md": "# x", "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n'})
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    joined = " ".join(profile.forbidden_commands)
    assert "rm -rf /" in joined
    assert "git push --force" in joined
