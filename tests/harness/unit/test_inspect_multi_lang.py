"""Cover the language-specific branches of inspect_repo not exercised
by the default Python/Node fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.inspect_ import inspect_repo


def test_inspect_rust_repo(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "x"\nversion = "0.1.0"\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "lib.rs").write_text("fn x() {}")
    report = inspect_repo(tmp_path)
    assert "rust" in report.languages
    assert "cargo" in report.package_managers
    assert any("test" in c for c in report.test_commands)
    assert any("clippy" in c for c in report.lint_commands)


def test_inspect_go_repo(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module x\n\ngo 1.21\n")
    (tmp_path / "main.go").write_text("package main\n\nfunc main() {}\n")
    report = inspect_repo(tmp_path)
    assert "go" in report.languages
    assert "go" in report.package_managers
    assert any("go test" in c for c in report.test_commands)


def test_inspect_detects_dockerfile(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM alpine\n")
    report = inspect_repo(tmp_path)
    assert report.has_dockerfile


def test_inspect_detects_docker_compose(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text("version: '3'\n")
    report = inspect_repo(tmp_path)
    assert report.has_docker_compose


def test_inspect_env_vars_from_dotenv_example(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "# comment line\n"
        "DATABASE_URL=postgres://x\n"
        "API_KEY=changeme\n"
        "\n"
        "SECRET_KEY=changeme\n"
    )
    report = inspect_repo(tmp_path)
    assert "DATABASE_URL" in report.env_vars
    assert "API_KEY" in report.env_vars
    assert "SECRET_KEY" in report.env_vars


def test_inspect_detects_existing_agent_configs(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# old")
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "rules").write_text("# old")
    report = inspect_repo(tmp_path)
    assert "AGENTS.md" in report.existing_agent_configs
    assert ".cursor/rules" in report.existing_agent_configs


def test_inspect_detects_existing_mcps(tmp_path: Path) -> None:
    import json

    cfg = {"mcpServers": {"filesystem": {}, "fetch": {}}}
    (tmp_path / ".mcp.json").write_text(json.dumps(cfg))
    report = inspect_repo(tmp_path)
    assert "filesystem" in report.detected_mcps
    assert "fetch" in report.detected_mcps


def test_inspect_reads_readme_excerpt(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# X\n\nthe project description goes here.\n")
    report = inspect_repo(tmp_path)
    assert "the project description" in report.readme_excerpt


def test_inspect_reads_contributing_excerpt(tmp_path: Path) -> None:
    (tmp_path / "CONTRIBUTING.md").write_text("how to contribute\n")
    report = inspect_repo(tmp_path)
    assert "how to contribute" in report.contributing_excerpt


def test_inspect_rejects_nondir(tmp_path: Path) -> None:
    p = tmp_path / "file.txt"
    p.write_text("x")
    with pytest.raises(ValueError):
        inspect_repo(p)
