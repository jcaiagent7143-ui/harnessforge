"""InspectionReport — the structured output of a repo walk.

Fields are intentionally minimal but cover everything an LLM needs to
write a useful HarnessProfile. Add fields here when you find the profiler
guessing instead of grounding.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InspectionReport:
    """Everything we learned about a repo without calling an LLM."""

    root: Path
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    lint_commands: list[str] = field(default_factory=list)
    build_commands: list[str] = field(default_factory=list)
    dev_commands: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    has_ci: bool = False
    ci_provider: str | None = None
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    has_kubernetes: bool = False
    git_remote: str | None = None
    git_default_branch: str | None = None
    readme_excerpt: str = ""
    contributing_excerpt: str = ""
    top_level_dirs: list[str] = field(default_factory=list)
    file_count: int = 0
    line_count_approx: int = 0
    existing_agent_configs: list[str] = field(default_factory=list)
    detected_mcps: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_prompt_dict(self) -> dict[str, Any]:
        """Serializable shape suitable for stuffing into an LLM prompt."""
        return {
            "languages": self.languages,
            "frameworks": self.frameworks,
            "package_managers": self.package_managers,
            "test_commands": self.test_commands,
            "lint_commands": self.lint_commands,
            "build_commands": self.build_commands,
            "dev_commands": self.dev_commands,
            "env_vars_expected": self.env_vars,
            "ci": {"enabled": self.has_ci, "provider": self.ci_provider},
            "containerization": {
                "dockerfile": self.has_dockerfile,
                "docker_compose": self.has_docker_compose,
                "kubernetes": self.has_kubernetes,
            },
            "git": {"remote": self.git_remote, "default_branch": self.git_default_branch},
            "readme_excerpt": self.readme_excerpt[:1500],
            "contributing_excerpt": self.contributing_excerpt[:800],
            "top_level_dirs": self.top_level_dirs,
            "scale": {"file_count": self.file_count, "line_count_approx": self.line_count_approx},
            "existing_agent_configs": self.existing_agent_configs,
            "detected_mcps": self.detected_mcps,
            "notes": self.notes,
        }


# ── public entrypoint ──────────────────────────────────────────────────────


def inspect_repo(root: str | Path) -> InspectionReport:
    """Walk a repo, return a grounded InspectionReport.

    Pure function — no LLM, no network (except a quick `git remote get-url`
    if a .git directory is present). Safe to run on any repo.
    """
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"{root_path} is not a directory")

    report = InspectionReport(root=root_path)

    _detect_languages_and_frameworks(report)
    _detect_python(report)
    _detect_node(report)
    _detect_rust(report)
    _detect_go(report)
    _detect_ci(report)
    _detect_containerization(report)
    _detect_env_vars(report)
    _detect_git(report)
    _detect_existing_agent_configs(report)
    _detect_existing_mcps(report)
    _read_readme(report)
    _read_contributing(report)
    _summarize_structure(report)

    return report


# ── individual probes ──────────────────────────────────────────────────────


def _has(report: InspectionReport, *paths: str) -> bool:
    return any((report.root / p).exists() for p in paths)


def _detect_languages_and_frameworks(report: InspectionReport) -> None:
    if _has(report, "pyproject.toml", "setup.py", "requirements.txt", "Pipfile"):
        report.languages.append("python")
    if _has(report, "package.json"):
        report.languages.append("typescript" if _has(report, "tsconfig.json") else "javascript")
    if _has(report, "Cargo.toml"):
        report.languages.append("rust")
    if _has(report, "go.mod"):
        report.languages.append("go")
    if _has(report, "pom.xml", "build.gradle", "build.gradle.kts"):
        report.languages.append("java")
    if _has(report, "Gemfile"):
        report.languages.append("ruby")
    if _has(report, "composer.json"):
        report.languages.append("php")
    if _has(report, "mix.exs"):
        report.languages.append("elixir")


def _detect_python(report: InspectionReport) -> None:
    pyproject = report.root / "pyproject.toml"
    if pyproject.exists():
        report.package_managers.append("pip")
        try:
            data = tomllib.loads(pyproject.read_text())
        except Exception:
            data = {}
        deps_text = json.dumps(data)
        # Web frameworks
        if '"fastapi"' in deps_text:
            report.frameworks.append("fastapi")
        if '"django"' in deps_text:
            report.frameworks.append("django")
        if '"flask"' in deps_text:
            report.frameworks.append("flask")
        # Test runners
        if '"pytest"' in deps_text:
            report.test_commands.append("pytest")
        # Linters
        if '"ruff"' in deps_text:
            report.lint_commands.append("ruff check .")
        if '"mypy"' in deps_text:
            report.lint_commands.append("mypy src")
        # RAG / vector-store / LLM-orchestration deps — these are signals
        # the blueprint recommender needs to route the project correctly.
        # Treating them as "frameworks" so they surface uniformly in profile.
        for needle, tag in (
            ('"langchain"', "langchain"),
            ('"llama-index"', "llama-index"),
            ('"qdrant-client"', "qdrant"),
            ('"chromadb"', "chroma"),
            ('"chroma"', "chroma"),
            ('"pinecone-client"', "pinecone"),
            ('"weaviate-client"', "weaviate"),
            ('"faiss-cpu"', "faiss"),
            ('"faiss-gpu"', "faiss"),
        ):
            if needle in deps_text and tag not in report.frameworks:
                report.frameworks.append(tag)
        # Finance / market-data deps
        for needle, tag in (
            ('"yfinance"', "yfinance"),
            ('"alpaca-py"', "alpaca-py"),
            ('"alpaca"', "alpaca-py"),
            ('"ib_insync"', "ib_insync"),
            ('"polygon-api-client"', "polygon"),
            ('"polygon"', "polygon"),
            ('"ccxt"', "ccxt"),
            ('"alpha_vantage"', "alpha_vantage"),
            ('"alpha-vantage"', "alpha_vantage"),
            ('"finnhub-python"', "finnhub"),
            ('"pandas-ta"', "pandas-ta"),
        ):
            if needle in deps_text and tag not in report.frameworks:
                report.frameworks.append(tag)
        # Workflow / orchestration deps
        for needle, tag in (
            ('"apache-airflow"', "airflow"),
            ('"airflow"', "airflow"),
            ('"prefect"', "prefect"),
            ('"dagster"', "dagster"),
            ('"celery"', "celery"),
            ('"luigi"', "luigi"),
        ):
            if needle in deps_text and tag not in report.frameworks:
                report.frameworks.append(tag)
        # HTTP client deps — drives `fetch` MCP recommendation
        for needle, tag in (
            ('"httpx"', "httpx"),
            ('"requests"', "requests"),
            ('"aiohttp"', "aiohttp"),
        ):
            if needle in deps_text and tag not in report.notes:
                report.notes.append(f"http client: {tag}")
        # DB deps — drives `postgres` MCP recommendation
        for needle, tag in (
            ('"psycopg"', "psycopg"),
            ('"psycopg2"', "psycopg2"),
            ('"sqlalchemy"', "sqlalchemy"),
            ('"asyncpg"', "asyncpg"),
        ):
            if needle in deps_text and tag not in report.notes:
                report.notes.append(f"db: {tag}")
        # Scripts
        scripts = data.get("project", {}).get("scripts", {}) or {}
        for name in scripts:
            report.dev_commands.append(name)
        # Hatchling / poetry / uv hints
        backend = data.get("build-system", {}).get("build-backend", "")
        if "hatchling" in backend:
            report.notes.append("build backend: hatchling")
        if "poetry" in backend:
            report.package_managers.append("poetry")
        if (report.root / "uv.lock").exists():
            report.package_managers.append("uv")
    elif (report.root / "requirements.txt").exists():
        report.package_managers.append("pip")
        if "pytest" in (report.root / "requirements.txt").read_text():
            report.test_commands.append("pytest")


def _detect_node(report: InspectionReport) -> None:
    pkg = report.root / "package.json"
    if not pkg.exists():
        return
    try:
        data = json.loads(pkg.read_text())
    except Exception:
        return
    scripts = data.get("scripts", {}) or {}
    deps = {**(data.get("dependencies", {}) or {}), **(data.get("devDependencies", {}) or {})}

    # Package manager
    if (report.root / "pnpm-lock.yaml").exists():
        report.package_managers.append("pnpm")
    elif (report.root / "yarn.lock").exists():
        report.package_managers.append("yarn")
    elif (report.root / "bun.lockb").exists():
        report.package_managers.append("bun")
    else:
        report.package_managers.append("npm")

    pm = report.package_managers[-1]
    for s in ("test", "lint", "build", "dev", "start"):
        if s in scripts:
            cmd = f"{pm} run {s}"
            if s == "test":
                report.test_commands.append(cmd)
            elif s == "lint":
                report.lint_commands.append(cmd)
            elif s == "build":
                report.build_commands.append(cmd)
            else:
                report.dev_commands.append(cmd)

    # Framework sniffing
    if "next" in deps:
        report.frameworks.append("next.js")
    if "react" in deps and "next" not in deps:
        report.frameworks.append("react")
    if "vue" in deps:
        report.frameworks.append("vue")
    if "svelte" in deps or "@sveltejs/kit" in deps:
        report.frameworks.append("svelte")
    if "express" in deps:
        report.frameworks.append("express")
    if "fastify" in deps:
        report.frameworks.append("fastify")
    if "hono" in deps:
        report.frameworks.append("hono")
    if "@nestjs/core" in deps:
        report.frameworks.append("nestjs")
    if "vite" in deps:
        report.notes.append("bundler: vite")
    if "prisma" in deps or "@prisma/client" in deps:
        report.notes.append("orm: prisma")
    if "drizzle-orm" in deps:
        report.notes.append("orm: drizzle")


def _detect_rust(report: InspectionReport) -> None:
    cargo = report.root / "Cargo.toml"
    if not cargo.exists():
        return
    report.package_managers.append("cargo")
    report.test_commands.append("cargo test")
    report.lint_commands.append("cargo clippy")
    report.build_commands.append("cargo build")
    report.dev_commands.append("cargo run")


def _detect_go(report: InspectionReport) -> None:
    if not (report.root / "go.mod").exists():
        return
    report.package_managers.append("go")
    report.test_commands.append("go test ./...")
    report.lint_commands.append("go vet ./...")
    report.build_commands.append("go build ./...")


def _detect_ci(report: InspectionReport) -> None:
    if (report.root / ".github" / "workflows").is_dir():
        report.has_ci = True
        report.ci_provider = "github-actions"
    elif (report.root / ".gitlab-ci.yml").exists():
        report.has_ci = True
        report.ci_provider = "gitlab-ci"
    elif (report.root / ".circleci" / "config.yml").exists():
        report.has_ci = True
        report.ci_provider = "circleci"
    elif (report.root / "azure-pipelines.yml").exists():
        report.has_ci = True
        report.ci_provider = "azure-pipelines"


def _detect_containerization(report: InspectionReport) -> None:
    report.has_dockerfile = _has(report, "Dockerfile", "dockerfile")
    report.has_docker_compose = _has(
        report,
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    )
    report.has_kubernetes = _has(report, "k8s", "kubernetes") or any(
        p.suffix in (".yaml", ".yml") and "kind:" in p.read_text(errors="ignore")[:200]
        for p in report.root.rglob("*.y*ml")
        if p.is_file() and p.stat().st_size < 10_000
    )


def _detect_env_vars(report: InspectionReport) -> None:
    """Read .env.example / .env.sample / env.template — the documented env schema."""
    for fname in (".env.example", ".env.sample", ".env.template", "env.example", ".envrc.example"):
        p = report.root / fname
        if p.exists():
            for line in p.read_text(errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(r"^([A-Z][A-Z0-9_]*)\s*=", line)
                if m:
                    report.env_vars.append(m.group(1))
            if report.env_vars:
                break


def _detect_git(report: InspectionReport) -> None:
    if not (report.root / ".git").exists():
        return
    try:
        remote = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=report.root,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if remote.returncode == 0:
            report.git_remote = remote.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    try:
        branch = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=report.root,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if branch.returncode == 0:
            report.git_default_branch = branch.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


def _detect_existing_agent_configs(report: InspectionReport) -> None:
    """Other agent tools may have left their own config — we honor them."""
    candidates = [
        ".claude/CLAUDE.md",
        ".claude/skills",
        "CLAUDE.md",
        ".cursor/rules",
        ".cursorrules",
        "AGENTS.md",
        ".continue/config.json",
        ".windsurf/rules",
        ".aider.conf.yml",
        ".github/copilot-instructions.md",
    ]
    for c in candidates:
        if (report.root / c).exists():
            report.existing_agent_configs.append(c)


def _detect_existing_mcps(report: InspectionReport) -> None:
    """Look for repo-local MCP configs the user already set up."""
    candidates = [".mcp.json", "mcp.json", ".cursor/mcp.json"]
    for c in candidates:
        p = report.root / c
        if p.exists():
            try:
                data = json.loads(p.read_text())
                servers = data.get("mcpServers", {})
                report.detected_mcps.extend(servers.keys())
            except (json.JSONDecodeError, OSError):
                continue


def _read_readme(report: InspectionReport) -> None:
    for fname in ("README.md", "Readme.md", "readme.md", "README.rst", "README"):
        p = report.root / fname
        if p.exists():
            report.readme_excerpt = p.read_text(errors="ignore")[:3000]
            return


def _read_contributing(report: InspectionReport) -> None:
    for fname in ("CONTRIBUTING.md", "CONTRIBUTING.rst", "docs/CONTRIBUTING.md"):
        p = report.root / fname
        if p.exists():
            report.contributing_excerpt = p.read_text(errors="ignore")[:2000]
            return


def _summarize_structure(report: InspectionReport) -> None:
    """Top-level dirs and a rough scale measurement."""
    ignore = {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "target",
        ".next",
    }
    for child in sorted(report.root.iterdir()):
        if child.is_dir() and child.name not in ignore and not child.name.startswith("."):
            report.top_level_dirs.append(child.name)

    # Rough scale — count files (capped) and approximate lines
    count = 0
    lines = 0
    for p in report.root.rglob("*"):
        if any(seg in ignore for seg in p.parts):
            continue
        if p.is_file() and p.stat().st_size < 1_000_000:
            count += 1
            if count > 5000:
                report.notes.append("file_count truncated at 5000")
                break
            try:
                with p.open("rb") as fh:
                    lines += sum(1 for _ in fh)
            except OSError:
                pass
    report.file_count = count
    report.line_count_approx = lines


# Local ``os`` import only used here — keeps the module's top clean.
_ = os
