"""Provisioning orchestrator — the engine behind ``harness init``.

End-to-end:

  1. Inspect the repo (deterministic, no LLM).
  2. Build a HarnessProfile (LLM or template).
  3. Pick a blueprint (explicit name, or recommended from the profile).
  4. Plan every file we'd write — adapters, blueprint files, skills, config.
  5. Honor collision policy (refuse if a file is on disk and drifted).
  6. Execute writes atomically (tmp + rename per file).
  7. Record everything in ``.harness/manifest.json`` for future re-runs.

The flow is async because the LLM profiler call is async. Synchronous
callers can use ``provision_sync`` which wraps it in ``asyncio.run``.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import harness
from harness.adapters import ALL_ADAPTERS
from harness.config import CONFIG_FILENAME, HarnessConfig
from harness.inspect_ import InspectionReport, inspect_repo
from harness.manifest import (
    MANIFEST_FILENAME,
    Manifest,
    ManifestEntry,
    build_entry,
    file_matches_manifest,
)
from harness.profile import (
    HarnessProfile,
    profile_from_inspection_llm,
    profile_from_inspection_template,
)

# ── data classes ──────────────────────────────────────────────────────────


@dataclass
class PlannedFile:
    """A file we intend to write."""

    path: Path  # absolute
    content: bytes
    written_by: str  # adapter / blueprint name, used for manifest provenance
    mode: int = 0o644


@dataclass
class RenderPlan:
    """The complete write plan."""

    repo_root: Path
    profile: HarnessProfile
    blueprint_name: str
    blueprint_version: str
    files: list[PlannedFile] = field(default_factory=list)

    @property
    def relative_paths(self) -> list[str]:
        return [str(f.path.relative_to(self.repo_root)) for f in self.files]


@dataclass
class ProvisionResult:
    """The outcome of a provisioning run."""

    plan: RenderPlan
    written: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)  # collisions we refused
    drifted: list[str] = field(default_factory=list)  # paths the user edited
    dry_run: bool = False


# ── public API ────────────────────────────────────────────────────────────


async def provision(
    root: str | Path,
    *,
    blueprint: str | None = None,
    no_llm: bool = False,
    force: bool = False,
    adapters: list[str] | None = None,
    no_skills: bool = False,
    dry_run: bool = False,
    provider: Any | None = None,
) -> ProvisionResult:
    """Run a full init: inspect → profile → blueprint → render → write.

    Pass ``no_llm=True`` to skip the LLM profiler and use only the
    deterministic template — useful for CI, golden-file tests, and
    air-gapped environments.
    """
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"{root_path} is not a directory")

    report = inspect_repo(root_path)
    profile_obj = await _build_profile(report, no_llm=no_llm, provider=provider)
    bp_name, bp_version, bp_files, bp_skills, bp_memory_schemas = _load_blueprint_outputs(
        blueprint, profile_obj, report, root_path, no_skills=no_skills
    )

    plan = RenderPlan(
        repo_root=root_path,
        profile=profile_obj,
        blueprint_name=bp_name,
        blueprint_version=bp_version,
    )

    # 1. profile.yaml — canonical machine-readable state
    plan.files.append(
        PlannedFile(
            path=root_path / ".harness" / "profile.yaml",
            content=profile_obj.to_yaml().encode("utf-8"),
            written_by="harness:profile",
        )
    )

    # 2. IDE adapters
    chosen_adapters = _filter_adapters(adapters)
    for name, render_fn, _outputs in chosen_adapters:
        for path in _adapter_planned_paths(name, render_fn, profile_obj, root_path):
            plan.files.append(path)

    # 3. Blueprint files + skills + memory schemas
    plan.files.extend(bp_files)
    plan.files.extend(bp_skills)
    plan.files.extend(bp_memory_schemas)

    # 4. harness.config.json
    cfg = HarnessConfig(
        harness_version=harness.__version__,
        blueprint=bp_name,
        blueprint_version=bp_version,
        adapters=[name for name, _, _ in chosen_adapters],
    )
    plan.files.append(
        PlannedFile(
            path=root_path / CONFIG_FILENAME,
            content=cfg.to_json().encode("utf-8"),
            written_by="harness:config",
        )
    )

    if dry_run:
        return ProvisionResult(plan=plan, dry_run=True)

    # 5. Execute writes — respect manifest-based collision policy
    written, skipped, drifted = _execute(plan, force=force)

    # 6. Write the new manifest LAST (so it records what we just wrote)
    manifest = _build_manifest(plan, written)
    manifest_path = root_path / MANIFEST_FILENAME
    manifest.save(manifest_path)
    written.append(manifest_path)

    return ProvisionResult(
        plan=plan,
        written=written,
        skipped=skipped,
        drifted=drifted,
    )


def provision_sync(*args: Any, **kwargs: Any) -> ProvisionResult:
    """Synchronous wrapper around :func:`provision`."""
    return asyncio.run(provision(*args, **kwargs))


# ── helpers ───────────────────────────────────────────────────────────────


async def _build_profile(
    report: InspectionReport,
    *,
    no_llm: bool,
    provider: Any | None,
) -> HarnessProfile:
    if no_llm:
        return profile_from_inspection_template(report)
    try:
        if provider is None:
            from aegis.providers import auto_provider

            provider = auto_provider()
        # If the auto-fallback Mock is selected, skip the LLM step entirely —
        # the result would be placeholder text, which is worse than the
        # deterministic template.
        if getattr(provider, "_is_auto_fallback", False):
            return profile_from_inspection_template(report)
        return await profile_from_inspection_llm(report, provider)
    except Exception:
        # Profile-building must never crash provisioning. The template is
        # always good enough to bootstrap.
        return profile_from_inspection_template(report)


def _filter_adapters(names: list[str] | None) -> list[tuple[str, Any, list[str]]]:
    if names is None:
        return list(ALL_ADAPTERS)
    wanted = {n.strip().lower() for n in names}
    out = [a for a in ALL_ADAPTERS if a[0] in wanted]
    if not out:
        raise ValueError(
            f"No adapters matched {sorted(wanted)}. Available: {[a[0] for a in ALL_ADAPTERS]}"
        )
    return out


def _adapter_planned_paths(
    name: str,
    render_fn: Any,
    profile: HarnessProfile,
    root: Path,
) -> list[PlannedFile]:
    """Render an adapter into a temp dir, capture the bytes, return PlannedFiles.

    This is a stage-by-stage rewrite: instead of calling adapters directly
    on the user's repo, we run them in a sandbox tmp dir and stage the
    outputs. This is what makes ``--dry-run`` and the collision policy
    possible.
    """
    planned: list[PlannedFile] = []
    with tempfile.TemporaryDirectory(prefix="harness-adapter-") as tmp:
        tmp_root = Path(tmp)
        # Adapter functions can mkdir freely inside the sandbox
        try:
            written_paths = render_fn(profile, tmp_root)
        except Exception as e:
            # Don't break the whole plan because one adapter has a bug —
            # surface a note and skip it. (Mirrors the safety in
            # ``adapters.render_all``.)
            written_paths = []
            print(f"[harness] WARNING: adapter {name!r} failed to render: {e}")
        for p in written_paths:
            content = p.read_bytes() if p.is_file() else b""
            rel = p.relative_to(tmp_root)
            planned.append(
                PlannedFile(
                    path=root / rel,
                    content=content,
                    written_by=f"adapter:{name}",
                )
            )
    return planned


def _load_blueprint_outputs(
    name: str | None,
    profile: HarnessProfile,
    report: InspectionReport,
    root: Path,
    *,
    no_skills: bool,
) -> tuple[str, str, list[PlannedFile], list[PlannedFile], list[PlannedFile]]:
    """Load and render a blueprint's outputs into PlannedFiles.

    Returns ``(bp_name, bp_version, files, skills, memory_schemas)``.

    v0.2.1: memory_schemas are now copied into ``.harness/memory_schemas/``.
    v0.2 referenced these schema paths from MEMORY.md but never copied
    the actual files (caught by the stock-agent re-eval).
    """
    from harness.blueprints import (  # local import — see module docstring
        load_blueprint,
        recommend_blueprint,
        render_blueprint_files,
        render_blueprint_memory_schemas,
        render_blueprint_skills,
    )

    chosen = name or recommend_blueprint(report, profile)
    bp = load_blueprint(chosen)
    files = render_blueprint_files(bp, profile, report, root)
    skills = [] if no_skills else render_blueprint_skills(bp, root)
    memory_schemas = render_blueprint_memory_schemas(bp, root)
    return bp.name, bp.version, files, skills, memory_schemas


def _execute(plan: RenderPlan, *, force: bool) -> tuple[list[Path], list[Path], list[str]]:
    """Write every planned file. Respect manifest-based collision policy.

    Internal dedupe rule: when two PlannedFiles target the same path, the
    *later* one wins (blueprints are appended after adapters, so blueprints
    always override adapters for shared paths like ``AGENTS.md``).
    """
    repo = plan.repo_root
    written: list[Path] = []
    skipped: list[Path] = []
    drifted: list[str] = []

    # Load existing manifest so we know which files we wrote previously
    existing = Manifest.load(repo / MANIFEST_FILENAME)

    # Dedupe: later entry wins (preserves provenance string of the winner)
    deduped: dict[Path, PlannedFile] = {}
    for pf in plan.files:
        deduped[pf.path.resolve()] = pf

    for pf in deduped.values():
        target = pf.path
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() and not force:
            rel = str(target.relative_to(repo))
            prev = existing.lookup(rel)
            if prev is None:
                # We didn't write this file before — refuse to overwrite a
                # user-authored file unless they pass --force.
                skipped.append(target)
                continue
            if not file_matches_manifest(repo, prev):
                # We wrote it before, but the user edited it. Treat as drift.
                drifted.append(rel)
                skipped.append(target)
                continue

        _atomic_write(target, pf.content, pf.mode)
        written.append(target)

    return written, skipped, drifted


def _atomic_write(path: Path, content: bytes, mode: int) -> None:
    """Write to a sibling tmp file, then rename. Avoids partial writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _build_manifest(plan: RenderPlan, written: list[Path]) -> Manifest:
    written_set = {p.resolve() for p in written}
    # Dedupe by path; later entry wins (matches _execute's rule).
    deduped: dict[Path, PlannedFile] = {}
    for pf in plan.files:
        deduped[pf.path.resolve()] = pf
    entries: list[ManifestEntry] = []
    for path, pf in deduped.items():
        if path in written_set:
            entries.append(
                build_entry(repo_root=plan.repo_root, path=pf.path, written_by=pf.written_by)
            )
    return Manifest(
        schema_version=1,
        harness_version=harness.__version__,
        entries=entries,
    )


__all__ = [
    "PlannedFile",
    "ProvisionResult",
    "RenderPlan",
    "provision",
    "provision_sync",
]
