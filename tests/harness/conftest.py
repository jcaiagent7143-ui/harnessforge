"""Shared fixtures + pytest options for harness-kit tests."""

from __future__ import annotations

from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-goldens",
        action="store_true",
        default=False,
        help="Rewrite golden-file snapshots under tests/harness/golden/expected/.",
    )


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A minimal Python repo on disk — enough for inspect_repo to classify."""
    (tmp_path / "README.md").write_text(
        "# Sample\n\nA minimal project used by harness-kit tests.\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n'
        'dependencies = ["fastapi", "pytest", "ruff"]\n'
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sample.py").write_text("def hello() -> str:\n    return 'hi'\n")
    return tmp_path


@pytest.fixture
def tmp_node_repo(tmp_path: Path) -> Path:
    """A minimal Node/Next.js repo."""
    (tmp_path / "README.md").write_text("# node-sample\n\nA tiny Next.js app.\n")
    (tmp_path / "package.json").write_text(
        '{"name":"node-sample","scripts":{"test":"jest","lint":"eslint .",'
        '"build":"next build","dev":"next dev"},'
        '"dependencies":{"next":"15.0","react":"19.0"}}'
    )
    (tmp_path / "tsconfig.json").write_text("{}")
    (tmp_path / "pnpm-lock.yaml").write_text("")
    return tmp_path


@pytest.fixture
def tmp_django_repo(tmp_path: Path) -> Path:
    """A Django-shaped repo."""
    (tmp_path / "README.md").write_text(
        "# helpdesk\n\nDjango app for customer support tickets.\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "helpdesk"\nversion = "0.1.0"\n'
        'dependencies = ["django", "pytest", "ruff"]\n'
    )
    (tmp_path / "manage.py").write_text("# django entry\n")
    return tmp_path


@pytest.fixture
def tmp_rag_repo(tmp_path: Path) -> Path:
    """A docs/RAG-shaped repo."""
    (tmp_path / "README.md").write_text(
        "# rag-docs\n\nDocument retrieval over our knowledge base.\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "rag-docs"\nversion = "0.1.0"\n'
        'dependencies = ["langchain", "qdrant-client", "pytest"]\n'
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "intro.md").write_text("# Intro\n\nWhat this knowledge base is.\n")
    return tmp_path
