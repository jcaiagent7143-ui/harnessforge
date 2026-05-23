"""Blueprint loader, recommender, and renderer.

Public surface (re-exported from :mod:`harness.blueprints`):

  * :func:`list_blueprints`            — every blueprint on disk
  * :func:`load_blueprint`             — by name
  * :func:`recommend_blueprint`        — heuristic match from a profile
  * :func:`render_blueprint_files`     — produce PlannedFile list for the user's repo
  * :func:`render_blueprint_skills`    — produce PlannedFile list for SKILLS/
  * :func:`blueprint_dir`              — on-disk path for a blueprint
  * :func:`blueprint_skill_source_dir` — on-disk path for one skill in a blueprint
  * :func:`iter_catalog_skills`        — (blueprint_name, Skill) for every catalog skill
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from harness.blueprints.schema import BlueprintSpec
from harness.skills_io import Skill, load_skill

if TYPE_CHECKING:
    from harness.inspect_ import InspectionReport
    from harness.profile import HarnessProfile
    from harness.provision import PlannedFile


_BLUEPRINT_YAML = "blueprint.yaml"
_FILES_DIR = "files"
_SKILLS_DIR = "skills"


# ── on-disk navigation ────────────────────────────────────────────────────


def _root() -> Path:
    return Path(__file__).parent


def blueprint_dir(name: str) -> Path:
    """Absolute path to a blueprint's directory."""
    d = _root() / name
    if not d.is_dir():
        raise KeyError(f"Blueprint {name!r} not found. Available: {sorted(_iter_names())}")
    return d


def blueprint_skill_source_dir(bp: BlueprintSpec, skill_name: str) -> Path:
    d = blueprint_dir(bp.name) / _SKILLS_DIR / skill_name
    if not d.is_dir():
        raise KeyError(f"Skill {skill_name!r} not found in blueprint {bp.name!r}")
    return d


def _iter_names() -> Iterator[str]:
    root = _root()
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / _BLUEPRINT_YAML).exists():
            yield child.name


# ── public API ────────────────────────────────────────────────────────────


def list_blueprints() -> list[BlueprintSpec]:
    """Return every installed blueprint, sorted by name."""
    out: list[BlueprintSpec] = []
    for name in _iter_names():
        try:
            out.append(load_blueprint(name))
        except Exception:
            # A malformed blueprint shouldn't crash `harness blueprint list`
            continue
    return out


def load_blueprint(name: str) -> BlueprintSpec:
    """Load and validate one blueprint by name."""
    d = blueprint_dir(name)
    yml = (d / _BLUEPRINT_YAML).read_text()
    data = yaml.safe_load(yml) or {}
    return BlueprintSpec.model_validate(data)


def iter_catalog_skills() -> Iterator[tuple[str, Skill]]:
    """Yield ``(blueprint_name, Skill)`` for every catalog skill we ship."""
    for name in _iter_names():
        skills_dir = _root() / name / _SKILLS_DIR
        if not skills_dir.is_dir():
            continue
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                try:
                    yield name, load_skill(child)
                except Exception:
                    continue


# ── recommendation ────────────────────────────────────────────────────────


def recommend_blueprint(report: InspectionReport, profile: HarnessProfile) -> str:
    """Pick the most appropriate blueprint for a profile.

    Heuristic only — explicit ``--blueprint`` always wins. Order matters:
    most-specific signals first, generic fallback last.
    """
    pt = profile.project_type.lower()
    frameworks = {f.lower() for f in profile.frameworks}
    name_lc = profile.name.lower()
    # readme + contributing as a free-text signal pool (lowercased)
    text_pool = (report.readme_excerpt + " " + report.contributing_excerpt).lower()

    # Finance / market-data signal: deps + name + readme keywords
    finance_dep_signals = {
        "yfinance",
        "alpaca-py",
        "alpaca",
        "ib_insync",
        "polygon",
        "polygon-api-client",
        "ccxt",
        "alpha_vantage",
        "alpha-vantage",
        "finnhub",
        "pandas-ta",
        "ta-lib",
    }
    finance_name_signals = {"stock", "portfolio", "trade", "trading", "broker", "crypto", "market"}
    finance_readme_signals = {"portfolio", "ticker", "stock", "broker", "market data", "trading"}
    if (
        finance_dep_signals & frameworks
        or any(s in name_lc for s in finance_name_signals)
        or any(s in text_pool for s in finance_readme_signals)
    ):
        return "finance-agent"

    # RAG signal: docs-heavy or vector-store deps or "rag"/"docs" in name
    rag_signals = {"qdrant", "chroma", "pinecone", "weaviate", "faiss", "langchain"}
    if rag_signals & frameworks or "rag" in name_lc or "docs" in name_lc:
        return "rag-agent"

    # Support signal: ticketing / helpdesk frameworks or "support"/"help" in name
    support_signals = {"django", "rails", "zulip", "discourse"}
    if (
        (support_signals & frameworks and pt == "web-app")
        or "support" in name_lc
        or "help" in name_lc
    ):
        return "support-agent"

    # Workflow signal: explicit orchestration framing — task pipelines, ETL, agent runtime
    workflow_dep_signals = {"airflow", "prefect", "dagster", "celery", "luigi"}
    workflow_text_signals = {"workflow", "pipeline", "etl", "orchestrate", "scheduler"}
    if workflow_dep_signals & frameworks or any(s in text_pool for s in workflow_text_signals):
        return "workflow-agent"

    # Python build-mode — the 80% case per the stock-agent eval.
    # This is now the default for Python projects with no orchestration signal:
    # CLIs, libraries, web-apps, web-APIs — anything where the deliverable is
    # *code* rather than *an orchestration trace*.
    if profile.primary_language == "python" and pt in (
        "cli",
        "library",
        "web-app",
        "web-api",
        "other",
    ):
        return "python-cli-app"

    # Final fallback — generic but useful
    return "workflow-agent"


# ── rendering ─────────────────────────────────────────────────────────────


def render_blueprint_files(
    bp: BlueprintSpec,
    profile: HarnessProfile,
    report: InspectionReport,
    repo_root: Path,
) -> list[PlannedFile]:
    """Render all blueprint.yaml ``generated_files`` into PlannedFile entries."""
    from harness.provision import PlannedFile  # local import — avoid cycle

    files_dir = blueprint_dir(bp.name) / _FILES_DIR
    if not files_dir.is_dir():
        return []
    env = _jinja_env(files_dir)
    ctx = _template_context(bp, profile, report)

    out: list[PlannedFile] = []
    for gf in bp.generated_files:
        try:
            tmpl = env.get_template(gf.template)
        except Exception as e:
            raise RuntimeError(
                f"Blueprint {bp.name!r} references template {gf.template!r} which "
                f"does not exist under {files_dir}: {e}"
            ) from e
        rendered = tmpl.render(**ctx)
        out.append(
            PlannedFile(
                path=repo_root / gf.path,
                content=rendered.encode("utf-8"),
                written_by=f"blueprint:{bp.name}",
                mode=gf.mode if gf.mode is not None else 0o644,
            )
        )
    return out


def render_blueprint_memory_schemas(bp: BlueprintSpec, repo_root: Path) -> list[PlannedFile]:
    """Copy the blueprint's memory_schemas/*.json into ``.harness/memory_schemas/``.

    v0.2.1: the generated MEMORY.md references these paths; v0.2 forgot to
    actually copy the files into the user's repo. Caught by the stock-agent
    re-eval.
    """
    from harness.provision import PlannedFile  # local import — avoid cycle

    src_root = blueprint_dir(bp.name) / "memory_schemas"
    if not src_root.is_dir():
        return []
    out: list[PlannedFile] = []
    for src in sorted(src_root.glob("*.json")):
        target = repo_root / ".harness" / "memory_schemas" / src.name
        out.append(
            PlannedFile(
                path=target,
                content=src.read_bytes(),
                written_by=f"blueprint:{bp.name}:memory_schemas",
            )
        )
    return out


def render_blueprint_skills(bp: BlueprintSpec, repo_root: Path) -> list[PlannedFile]:
    """Render every blueprint-listed skill into PlannedFile entries under SKILLS/."""
    from harness.provision import PlannedFile  # local import — avoid cycle

    out: list[PlannedFile] = []
    src_root = blueprint_dir(bp.name) / _SKILLS_DIR
    if not src_root.is_dir():
        return out

    for skill_name in bp.skills:
        src = src_root / skill_name
        if not src.is_dir():
            continue
        for child in sorted(src.rglob("*")):
            if not child.is_file():
                continue
            rel = child.relative_to(src_root)  # e.g. <skill>/SKILL.md
            target = repo_root / "SKILLS" / rel
            out.append(
                PlannedFile(
                    path=target,
                    content=child.read_bytes(),
                    written_by=f"blueprint:{bp.name}:skills",
                )
            )
    return out


# ── helpers ────────────────────────────────────────────────────────────────


def _jinja_env(template_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
        undefined=StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )


def _template_context(
    bp: BlueprintSpec,
    profile: HarnessProfile,
    report: InspectionReport,
) -> dict[str, object]:
    """Variables available to every blueprint template.

    v0.2.1: ``mcps_list`` is now deduped and pruned. v0.2 concatenated
    ``profile.recommended_mcps + blueprint.recommended_mcps`` which (a)
    duplicated ``filesystem`` and (b) ignored evidence — finance-agent's
    blueprint recommends ``postgres`` even for projects with no DB deps.
    """
    pruned_mcps = _merge_and_prune_mcps(profile, bp, report)
    return {
        "blueprint": bp,
        "profile": profile,
        "report": report,
        "frameworks_list": ", ".join(profile.frameworks) or "none detected",
        # Deduped + pruned MCP list. Templates that use the legacy
        # ``profile.recommended_mcps + blueprint.recommended_mcps`` pattern
        # produce dupes; new templates should use ``pruned_mcps`` directly.
        "mcps_list": ", ".join(pruned_mcps),
        "pruned_mcps": pruned_mcps,
        "skills_list": "\n".join(f"- {s}" for s in bp.skills) or "_(none)_",
    }


def _merge_and_prune_mcps(
    profile: HarnessProfile,
    bp: BlueprintSpec,
    report: InspectionReport,
) -> list[str]:
    """Combine profile + blueprint MCPs, dedup, then prune to project evidence.

    Rules (mirrors the profile-level _default_mcps_for):
      - filesystem and git: always allowed
      - postgres: only if psycopg/sqlalchemy in deps or env DATABASE_URL
      - fetch: only if HTTP-client deps OR web framework OR finance/rag/workflow agent type
      - kubernetes: only if has_kubernetes
      - aws: only if 'aws' appears in README or has_kubernetes
      - time, github, slack, linear, qdrant, chroma: passed through (blueprint's call)
    """
    merged: list[str] = []
    seen: set[str] = set()
    for m in list(profile.recommended_mcps) + list(bp.recommended_mcps):
        if m in seen:
            continue
        seen.add(m)
        merged.append(m)

    dep_signal = (
        " ".join(report.frameworks)
        + " "
        + " ".join(report.notes)
        + " "
        + " ".join(report.env_vars)
        + " "
        + report.readme_excerpt
    ).lower()

    def keep(name: str) -> bool:
        if name in {"filesystem", "git", "time", "github", "slack", "linear", "qdrant", "chroma"}:
            return True
        if name == "postgres":
            return any(
                s in dep_signal for s in ("postgres", "psycopg", "sqlalchemy", "database_url")
            )
        if name == "fetch":
            return bp.agent_type in {"finance", "rag", "workflow", "support"} or any(
                s in dep_signal
                for s in ("httpx", "requests", "aiohttp", "fastapi", "flask", "django")
            )
        if name == "kubernetes":
            return report.has_kubernetes
        if name == "aws":
            return "aws" in dep_signal or report.has_kubernetes
        # Unknown MCP — let the blueprint be the authority
        return True

    return [m for m in merged if keep(m)]


__all__ = [
    "blueprint_dir",
    "blueprint_skill_source_dir",
    "iter_catalog_skills",
    "list_blueprints",
    "load_blueprint",
    "recommend_blueprint",
    "render_blueprint_files",
    "render_blueprint_memory_schemas",
    "render_blueprint_skills",
]
