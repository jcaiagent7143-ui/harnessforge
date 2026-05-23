"""v0.2 smart-defaults — inspector-driven test runner picking,
MCP pruning, requires-approval pruning. Each test corresponds to a
specific gap surfaced in the stock-agent A/B real-build evaluation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.blueprints import recommend_blueprint
from harness.inspect_ import inspect_repo
from harness.profile import profile_from_inspection_template


def _seed(tmp: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp


# ── test-runner smart default (Fix 6) ─────────────────────────────────────


def test_python_project_without_pytest_gets_unittest_default(tmp_path: Path) -> None:
    """A Python project with no test runner declared should default to
    `python(3) -m unittest discover` (always works, no install needed).

    v0.2.1: the binary is `python3` on macOS / modern Linux and `python`
    only if that's the only one available — see `_resolve_python_binary`.
    """
    from harness.profile import _resolve_python_binary

    _seed(
        tmp_path,
        {
            "README.md": "# x",
            "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    expected = f"{_resolve_python_binary()} -m unittest discover"
    assert profile.test_command == expected


def test_python_project_with_pytest_keeps_pytest(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "README.md": "# x",
            "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = ["pytest"]\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert profile.test_command == "pytest"


def test_rust_project_defaults_to_cargo_test(tmp_path: Path) -> None:
    _seed(tmp_path, {"Cargo.toml": '[package]\nname = "x"\nversion = "0.1.0"\n'})
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert profile.test_command == "cargo test"


# ── MCP-list pruning (Fix 3) ──────────────────────────────────────────────


def test_mcp_list_does_not_include_postgres_for_portfolio_cli(tmp_path: Path) -> None:
    """The stock-agent eval flagged 'postgres recommended for a CLI is misleading'.
    A Python CLI with yfinance + no DB deps should NOT get postgres in its MCP list."""
    _seed(
        tmp_path,
        {
            "README.md": "# StockBot\nPortfolio tracker.",
            "pyproject.toml": '[project]\nname = "stockbot"\nversion = "0.1"\ndependencies = ["yfinance"]\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert "postgres" not in profile.recommended_mcps


def test_mcp_list_includes_postgres_when_sqlalchemy_present(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "README.md": "# api",
            "pyproject.toml": '[project]\nname = "api"\nversion = "0.1"\ndependencies = ["fastapi", "sqlalchemy"]\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert "postgres" in profile.recommended_mcps


def test_mcp_list_includes_fetch_for_web_api(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "README.md": "# api",
            "pyproject.toml": '[project]\nname = "api"\nversion = "0.1"\ndependencies = ["fastapi"]\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert "fetch" in profile.recommended_mcps


# ── forbidden-paths pruning (Fix 3) ───────────────────────────────────────


def test_forbidden_paths_omits_migrations_when_no_migrations_dir(tmp_path: Path) -> None:
    """The eval flagged 'migrations/ in forbidden list for a project without migrations
    signals generic boilerplate'. We now require evidence."""
    _seed(
        tmp_path,
        {
            "README.md": "# x",
            "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert "migrations/" not in profile.forbidden_paths


def test_forbidden_paths_includes_migrations_when_dir_exists(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "README.md": "# x",
            "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n',
            "migrations/001_init.sql": "-- placeholder",
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert "migrations/" in profile.forbidden_paths


def test_forbidden_paths_omits_aws_credentials_for_plain_python_app(tmp_path: Path) -> None:
    """A Python app with no AWS/K8s signal shouldn't claim '.aws/credentials' as forbidden."""
    _seed(
        tmp_path,
        {
            "README.md": "# tool\nA small utility.",
            "pyproject.toml": '[project]\nname = "tool"\nversion = "0.1"\ndependencies = []\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert ".aws/credentials" not in profile.forbidden_paths


# ── approval-list pruning (Fix 3) ─────────────────────────────────────────


def test_requires_approval_omits_migrations_when_no_migrations_dir(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "README.md": "# x",
            "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    joined = " ".join(profile.requires_human_approval).lower()
    assert "migrations" not in joined


def test_requires_approval_mentions_env_when_env_file_present(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        {
            "README.md": "# x",
            "pyproject.toml": '[project]\nname = "x"\nversion = "0.1"\ndependencies = []\n',
            ".env.example": "API_KEY=changeme\n",
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    joined = " ".join(profile.requires_human_approval).lower()
    assert ".env" in joined


# ── 5-blueprint recommender (Fixes 1 + 2 + 5) ─────────────────────────────


@pytest.mark.parametrize(
    "deps,expected",
    [
        (["yfinance"], "finance-agent"),
        (["alpaca-py"], "finance-agent"),
        (["ib_insync"], "finance-agent"),
        (["polygon-api-client"], "finance-agent"),
        (["ccxt"], "finance-agent"),
        (["langchain"], "rag-agent"),
        (["qdrant-client"], "rag-agent"),
        (["chromadb"], "rag-agent"),
        (["apache-airflow"], "workflow-agent"),
        (["prefect"], "workflow-agent"),
        (["fastapi", "sqlalchemy"], "python-cli-app"),
        ([], "python-cli-app"),  # generic Python defaults to build-mode
    ],
)
def test_recommender_routes_by_dep_signal(
    tmp_path: Path, deps: list[str], expected: str
) -> None:
    deps_str = ", ".join(f'"{d}"' for d in deps)
    _seed(
        tmp_path,
        {
            "README.md": "# x",
            "pyproject.toml": f'[project]\nname = "x"\nversion = "0.1"\ndependencies = [{deps_str}]\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    rec = recommend_blueprint(report, profile)
    assert rec == expected, f"deps={deps}: got {rec!r}, expected {expected!r}"


def test_recommender_routes_stock_by_name_alone(tmp_path: Path) -> None:
    """Even with no finance deps, a project named 'stockbot' should go to finance-agent."""
    _seed(
        tmp_path,
        {
            "README.md": "# StockBot\nDescription.",
            "pyproject.toml": '[project]\nname = "stockbot"\nversion = "0.1"\ndependencies = []\n',
        },
    )
    report = inspect_repo(tmp_path)
    profile = profile_from_inspection_template(report)
    assert recommend_blueprint(report, profile) == "finance-agent"
