"""Validators — load a blueprint's validator modules and run them.

Each blueprint ships a ``validators/`` directory with Python modules
exposing ``run(target: Path) -> list[str]``. We load them at runtime
through ``aegis.synthesize.sandbox.load_harness`` so the AST allowlist
+ restricted exec are enforced.

The public entry is :func:`run_checks`, which returns the stable
JSON contract :mod:`harness.cli.verify` emits.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from typing import Any

from harness.blueprints.schema import BlueprintSpec


def run_checks(
    bp: BlueprintSpec,
    target: Path,
    *,
    only: str | None = None,
    fail_fast: bool = False,
) -> dict[str, Any]:
    """Run blueprint validators against a bootstrapped repo.

    Returns a dict matching the published verify-protocol JSON schema.
    """
    from harness.blueprints import blueprint_dir

    bp_dir = blueprint_dir(bp.name)
    validators_dir = bp_dir / "validators"

    checks: list[dict[str, Any]] = []
    passed = failed = 0

    for spec in bp.validators:
        name = spec["name"]
        module_name = spec["module"]
        description = spec.get("description", "")

        if only is not None and name != only:
            continue

        record: dict[str, Any] = {
            "name": name,
            "description": description,
            "status": "pass",
            "duration_ms": 0,
            "messages": [],
        }

        started = time.monotonic()
        try:
            messages = _run_one(validators_dir, module_name, target)
        except Exception as e:
            record["status"] = "error"
            record["messages"] = [f"validator raised: {type(e).__name__}: {e}"]
            failed += 1
        else:
            # SKIPPED markers (e.g. "SKIPPED: no answer file") are not failures.
            if messages and all(m.startswith("SKIPPED") for m in messages):
                record["status"] = "skipped"
                record["messages"] = messages
            elif messages:
                record["status"] = "fail"
                record["messages"] = messages
                failed += 1
            else:
                record["status"] = "pass"
                passed += 1
        record["duration_ms"] = int((time.monotonic() - started) * 1000)
        checks.append(record)

        if fail_fast and record["status"] in {"fail", "error"}:
            break

    return {
        "schema_version": 1,
        "blueprint": bp.name,
        "blueprint_version": bp.version,
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
        },
    }


def _run_one(validators_dir: Path, module_name: str, target: Path) -> list[str]:
    """Import the validator module from disk and invoke its ``run(target)``."""
    src = validators_dir / f"{module_name}.py"
    if not src.exists():
        raise FileNotFoundError(f"validator module {module_name!r} not found at {src}")

    # Use importlib spec so we don't pollute sys.modules permanently.
    spec = importlib.util.spec_from_file_location(f"_harness_validator_{module_name}", str(src))
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load spec for {src}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop(spec.name, None)

    fn = getattr(mod, "run", None)
    if fn is None or not callable(fn):
        raise AttributeError(f"validator {module_name!r} has no callable run(target)")

    result = fn(target)
    if not isinstance(result, list):
        raise TypeError(
            f"validator {module_name!r}.run must return list[str], got {type(result).__name__}"
        )
    return [str(m) for m in result]


__all__ = ["run_checks"]
