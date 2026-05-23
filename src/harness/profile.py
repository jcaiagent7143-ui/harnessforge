"""HarnessProfile — the canonical artifact harness produces.

A HarnessProfile is a small, structured description of *how an agent should
work in this project*. It contains the data every downstream IDE adapter
needs to render its own native config (CLAUDE.md, .cursor/rules, AGENTS.md,
etc.). The profile is serialized as YAML and committed to the repo.

Generated from an :class:`~harness.inspect_.InspectionReport` via a single
LLM call (the "profiler"). Falls back to a deterministic template if no
LLM is configured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from harness.inspect_ import InspectionReport


@dataclass
class HarnessProfile:
    """The canonical description of a project's agent environment."""

    name: str
    description: str
    project_type: str  # "web-app" | "library" | "cli" | "data-pipeline" | "infra" | "other"
    primary_language: str
    frameworks: list[str] = field(default_factory=list)

    # Commands the agent can run
    test_command: str | None = None
    lint_command: str | None = None
    build_command: str | None = None
    dev_command: str | None = None

    # Safety
    forbidden_paths: list[str] = field(default_factory=list)
    forbidden_commands: list[str] = field(default_factory=list)
    requires_human_approval: list[str] = field(default_factory=list)

    # Environment / credentials
    required_env_vars: list[str] = field(default_factory=list)
    secrets_handling: str = "use .env, never log values, never commit"

    # Behavior
    conventions: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)

    # Tool surface — recommended MCP servers + repo-local tools
    recommended_mcps: list[str] = field(default_factory=list)
    repo_tools: list[str] = field(default_factory=list)

    # Cost / policy
    default_model: str = "claude-sonnet-4-5"
    cost_ceiling_usd_per_task: float = 0.50
    max_steps: int = 12

    # Provenance — populated by the builder, never used as a literal default.
    # The empty string sentinel means "the builder forgot to populate"; the
    # template + LLM builders both pass the live ``harness.__version__``.
    harness_version: str = ""
    generated_from: dict[str, Any] = field(default_factory=dict)

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.__dict__, sort_keys=False, width=100)

    @classmethod
    def from_yaml(cls, text: str) -> HarnessProfile:
        data = yaml.safe_load(text) or {}
        return cls(**data)

    @classmethod
    def load(cls, path: str | Path) -> HarnessProfile:
        return cls.from_yaml(Path(path).read_text())

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_yaml())


# ── builders ──────────────────────────────────────────────────────────────


def profile_from_inspection_template(report: InspectionReport) -> HarnessProfile:
    """Deterministic profile build — no LLM. Used as fallback and as the
    seed the LLM-driven profiler refines."""
    primary = report.languages[0] if report.languages else "unknown"
    project_type = _guess_project_type(report)

    return HarnessProfile(
        name=report.root.name,
        description=_first_sentence(report.readme_excerpt)
        or f"{primary} project at {report.root.name}",
        project_type=project_type,
        primary_language=primary,
        frameworks=list(report.frameworks),
        test_command=_pick_test_command(report),
        lint_command=_pick_lint_command(report),
        build_command=report.build_commands[0] if report.build_commands else None,
        dev_command=report.dev_commands[0] if report.dev_commands else None,
        forbidden_paths=_default_forbidden_paths(report),
        forbidden_commands=_default_forbidden_commands(report),
        requires_human_approval=_default_requires_approval(report),
        required_env_vars=list(report.env_vars),
        conventions=_default_conventions(report),
        success_criteria=_default_success_criteria(report),
        recommended_mcps=list(report.detected_mcps) or _default_mcps_for(report, project_type),
        repo_tools=[],
        harness_version=_live_version(),
        generated_from={
            "inspection": report.to_prompt_dict(),
            "profiler": "deterministic-template",
        },
    )


def _live_version() -> str:
    """Read the live harness package version, deferred to avoid import-time cycles."""
    import harness  # local import — `harness` imports `profile`, so top-level would loop

    return harness.__version__


# ── smart-defaults helpers (Fix 6 + Fix 3) ────────────────────────────────


def _pick_test_command(report: InspectionReport) -> str | None:
    """Pick a test_command even when the inspector didn't find an explicit one.

    Order of preference:
      1. Whatever the inspector explicitly detected (declared in pyproject etc.)
      2. Reasonable default for the primary language so the profile is never
         null-and-useless. The agent can change this; what matters is that
         AGENTS.md can render a concrete command and the `tests` validator
         has something to invoke.
    """
    if report.test_commands:
        return report.test_commands[0]
    if "python" in report.languages:
        # Default to stdlib unittest — works without any installed dep, on every
        # Python project. Pick the binary that actually exists on PATH —
        # macOS-with-only-python3 was the v0.2 first-run footgun the
        # stock-agent re-eval caught.
        py = _resolve_python_binary()
        return f"{py} -m unittest discover"
    if "typescript" in report.languages or "javascript" in report.languages:
        pm = report.package_managers[0] if report.package_managers else "npm"
        return f"{pm} test"
    if "rust" in report.languages:
        return "cargo test"
    if "go" in report.languages:
        return "go test ./..."
    return None


def _resolve_python_binary() -> str:
    """Pick `python` or `python3` based on what's actually on PATH.

    macOS ships only `python3` since stock Python 2 was removed; some
    Linux distros symlink `python` → `python3`; Windows has `python` from
    the official installer. We prefer `python3` when both exist
    (unambiguous about Python 2 vs 3) but fall back to `python` when
    that's all there is.
    """
    import shutil

    if shutil.which("python3"):
        return "python3"
    if shutil.which("python"):
        return "python"
    # Worst case: emit `python3` and let the user fix their environment.
    # We don't crash the profile builder over a missing interpreter.
    return "python3"


def _pick_lint_command(report: InspectionReport) -> str | None:
    """Same logic for lint."""
    if report.lint_commands:
        return report.lint_commands[0]
    if "python" in report.languages:
        # No explicit lint configured — leave null so the agent asks the user.
        # Picking ruff/flake8/pylint blindly is the failure mode from the
        # stock-agent eval.
        return None
    if "rust" in report.languages:
        return "cargo clippy"
    if "go" in report.languages:
        return "go vet ./..."
    return None


def _default_requires_approval(report: InspectionReport) -> list[str]:
    """Approval list — generic items + per-project items.

    Pruned: we don't say "any change to migrations/" if there's no
    migrations/ directory in the repo.
    """
    items = [
        "any git push to main/master",
        "any deploy command",
        "any `rm -rf` of more than one directory",
    ]
    if (report.root / "migrations").is_dir():
        items.append("any change to migrations/")
    if any((report.root / f).exists() for f in (".env", ".env.example")):
        items.append("any change to .env or .env.* files")
    if report.has_kubernetes:
        items.append("any kubectl apply / helm upgrade against production")
    return items


async def profile_from_inspection_llm(
    report: InspectionReport,
    provider: Any,
) -> HarnessProfile:
    """LLM-driven profile build. One call. Strict JSON output. Falls back
    to the deterministic template on any failure."""
    seed = profile_from_inspection_template(report)
    try:
        from aegis.providers.base import Message
    except ImportError:
        return seed

    system = (
        "You are a senior staff engineer joining a new project for the first time. "
        "You are given a deterministic inspection of the repo. Your job: write a "
        "HarnessProfile JSON object that describes how an AI agent should work in "
        "this project — conventions, success criteria, forbidden paths, and the "
        "right MCP server set. Be specific to THIS project; reject generic advice."
    )
    user = (
        "INSPECTION REPORT:\n"
        + json.dumps(report.to_prompt_dict(), indent=2)
        + "\n\nSEED PROFILE (refine — keep its fields but improve descriptions,"
        " conventions, success_criteria, recommended_mcps based on the inspection):\n"
        + json.dumps({k: v for k, v in seed.__dict__.items() if k != "generated_from"}, indent=2)
        + "\n\nReturn ONLY a JSON object matching the HarnessProfile schema. "
        "Do not wrap in markdown. Do not add commentary."
    )

    try:
        response = await provider.complete(
            [Message.system(system), Message.user(user)],
            temperature=0.2,
            max_tokens=2048,
            json_only=True,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        # Preserve provenance regardless of what the model returned
        data["generated_from"] = {
            "inspection": report.to_prompt_dict(),
            "profiler": getattr(provider, "name", "unknown"),
            "tokens_in": response.tokens_in,
            "tokens_out": response.tokens_out,
        }
        # Filter to known fields so future LLM hallucinations don't crash us
        known = set(seed.__dict__.keys())
        return HarnessProfile(**{k: v for k, v in data.items() if k in known})
    except Exception as e:
        seed.generated_from["llm_error"] = str(e)
        return seed


# ── helpers ──────────────────────────────────────────────────────────────


def _guess_project_type(report: InspectionReport) -> str:
    fw = set(f.lower() for f in report.frameworks)
    if fw & {"next.js", "react", "vue", "svelte", "django", "rails", "flask", "fastapi"}:
        return "web-app"
    if fw & {"express", "fastify", "hono", "nestjs"}:
        return "web-api"
    if "cli" in report.root.name.lower() or any("cli" in d for d in report.top_level_dirs):
        return "cli"
    if report.has_kubernetes or report.has_docker_compose:
        return "infra"
    if any(d in {"src", "lib"} for d in report.top_level_dirs):
        return "library"
    return "other"


def _default_forbidden_paths(report: InspectionReport) -> list[str]:
    """Forbidden paths — pruned to what's plausible in *this* project.

    We always include the universal sensitive globs (.env, .env.*, *.pem,
    *.key, secrets/) because even if they're absent today, a careless
    agent could create them. We only include project-specific entries
    (migrations/, .next/, target/) when the inspector found signals
    suggesting they apply — otherwise the list reads as generic
    boilerplate and erodes agent trust (per the stock-agent eval).
    """
    # Universal — always present, even if the file doesn't exist yet.
    paths = [
        ".env",
        ".env.*",
        "*.pem",
        "*.key",
        "secrets/",
    ]
    # ~/.aws and ~/.ssh are user-global; only include if there's any sign
    # the project touches AWS / SSH at all (Dockerfile, CI config, deps).
    text_signal = (report.readme_excerpt + " " + report.contributing_excerpt).lower()
    if "aws" in text_signal or report.has_kubernetes:
        paths.append(".aws/credentials")
    if "ssh" in text_signal or report.has_kubernetes:
        paths.append(".ssh/")
    # Per-language: only include when the directory actually exists or the
    # language is present AND the directory is conventional for it.
    if "python" in report.languages and (report.root / "migrations").is_dir():
        paths.append("migrations/")
    if any(f in report.frameworks for f in ("next.js", "react", "vue", "svelte")):
        paths += [".next/", "node_modules/"]
    if "rust" in report.languages:
        paths.append("target/")
    if report.has_kubernetes:
        paths += ["k8s/production/", "kubernetes/production/"]
    return paths


def _default_forbidden_commands(report: InspectionReport) -> list[str]:
    """Forbidden commands — pruned to what's plausible in *this* project.

    Universal destructive commands (rm -rf, git push --force) are always
    included. Stack-specific commands (kubectl, terraform, DROP DATABASE)
    are only included when there's evidence the stack is in use — per the
    stock-agent re-eval, `kubectl --context=prod*` in a personal portfolio
    CLI was template bloat that diluted the parts that mattered.
    """
    cmds = [
        "rm -rf /",
        "rm -rf ~",
        "rm -rf .",
        "git push --force",
        "git push -f",
        "git reset --hard origin/*",
    ]
    text = (report.readme_excerpt + " " + report.contributing_excerpt).lower()
    dep_text = " ".join(report.frameworks) + " " + " ".join(report.notes)
    dep_text = dep_text.lower()

    if report.has_kubernetes or "kubectl" in text or "k8s" in text:
        cmds.append("kubectl * --context=prod*")
    if "terraform" in text or any(p.name in {"main.tf", "providers.tf"} for p in report.root.iterdir() if p.is_file()):
        cmds.append("terraform apply")
    if any(s in dep_text for s in ("postgres", "psycopg", "sqlalchemy", "mysql", "mariadb")):
        cmds += ["DROP DATABASE", "TRUNCATE"]
    return cmds


def _default_conventions(report: InspectionReport) -> list[str]:
    out = []
    if "python" in report.languages:
        out.append("Python code uses type hints and follows PEP 8.")
        if "ruff" in str(report.lint_commands):
            out.append("Run `ruff check . && ruff format .` before any commit.")
        if any("mypy" in c for c in report.lint_commands):
            out.append("Type-check with `mypy` — strict mode if configured.")
    if any(lang in report.languages for lang in ("typescript", "javascript")):
        out.append("Match existing code style; run `lint` before committing.")
    if report.has_ci:
        out.append(f"CI runs on every push ({report.ci_provider}). Don't merge red.")
    if report.test_commands:
        out.append(f"Always run `{report.test_commands[0]}` after non-trivial changes.")
    out.append("Read the surrounding code before making any edit — match local conventions.")
    out.append("Prefer editing existing files over creating new ones unless asked.")
    return out


def _default_success_criteria(report: InspectionReport) -> list[str]:
    out = []
    if report.test_commands:
        out.append(f"`{report.test_commands[0]}` passes")
    if report.lint_commands:
        out.append(f"`{report.lint_commands[0]}` is clean")
    if report.build_commands:
        out.append(f"`{report.build_commands[0]}` succeeds")
    if not out:
        out.append("Code change is small, focused, and readable")
    out.append("Diff is minimal — touch only files relevant to the task")
    out.append("Commit message explains *why*, not just *what*")
    return out


def _default_mcps_for(report: InspectionReport, project_type: str) -> list[str]:
    """Pick MCPs based on actual project signals, not just project_type.

    Per the stock-agent eval: recommending postgres for a portfolio CLI
    erodes agent trust ("this list is generic boilerplate, don't trust it
    as project-specific"). We now require evidence.
    """
    base = ["filesystem"]
    if (report.root / ".git").exists():
        base.append("git")

    # Postgres only if deps mention it OR docker-compose includes it OR
    # a postgres URL is in env vars.
    dep_text = (
        " ".join(report.frameworks)
        + " ".join(report.notes)
        + " ".join(report.env_vars)
    ).lower()
    if any(s in dep_text for s in ("postgres", "psycopg", "sqlalchemy")) or (
        report.has_docker_compose and "postgres" in dep_text
    ):
        base.append("postgres")

    # Fetch — useful for web-app / web-api or any project mentioning HTTP
    if project_type in ("web-app", "web-api") or "fetch" in dep_text or "httpx" in dep_text or "requests" in dep_text:
        base.append("fetch")

    # GitHub — useful for OSS libraries and CI-using projects
    if (project_type == "library" or report.has_ci) and not base.count("github"):
        base.append("github")

    # K8s / AWS — only if there's actual infra signal
    if report.has_kubernetes:
        base += ["kubernetes"]
    if "aws" in dep_text:
        base.append("aws")

    return base


def _first_sentence(text: str) -> str:
    text = text.strip().split("\n\n", 1)[0]
    # strip markdown headers
    text = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    text = text.strip()
    for end in (". ", ".\n"):
        if end in text:
            return text.split(end, 1)[0].strip() + "."
    return text[:200].strip()
