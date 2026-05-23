"""Unit tests for `harness inspect` — deterministic repo walking."""

from __future__ import annotations

from pathlib import Path

from harness.inspect_ import inspect_repo


def test_inspect_python_repo(tmp_repo: Path) -> None:
    report = inspect_repo(tmp_repo)
    assert "python" in report.languages
    assert "pip" in report.package_managers
    assert "fastapi" in report.frameworks
    assert any("pytest" in c for c in report.test_commands)
    assert any("ruff" in c for c in report.lint_commands)


def test_inspect_node_repo(tmp_node_repo: Path) -> None:
    report = inspect_repo(tmp_node_repo)
    assert "typescript" in report.languages
    assert "pnpm" in report.package_managers
    assert "next.js" in report.frameworks
    assert any("test" in c for c in report.test_commands)
    assert any("build" in c for c in report.build_commands)


def test_inspect_returns_to_prompt_dict(tmp_repo: Path) -> None:
    report = inspect_repo(tmp_repo)
    data = report.to_prompt_dict()
    assert "languages" in data
    assert "frameworks" in data
    assert "scale" in data
    assert isinstance(data["scale"]["file_count"], int)
    assert data["scale"]["file_count"] >= 2  # README + pyproject + src/sample.py


def test_inspect_detects_no_ci_in_empty_repo(tmp_path: Path) -> None:
    report = inspect_repo(tmp_path)
    assert not report.has_ci
    assert report.ci_provider is None
