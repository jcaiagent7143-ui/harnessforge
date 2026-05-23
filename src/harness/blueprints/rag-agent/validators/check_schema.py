"""check_schema — validate the sample RAG answer against the declared Pydantic schema."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Minimal schema check without pulling Pydantic at validator-load time (the
# sandbox import allowlist may not include it). We hand-roll a tight check
# that matches what files/verify_output.py.j2 enforces in the generated repo.

REQUIRED_KEYS = {"schema_version", "answer", "citations"}
SCHEMA_VERSION = 1


def run(target: Path) -> list[str]:
    out = os.environ.get("RAG_OUT")
    if out:
        answer_path = Path(out)
    else:
        candidates = list(Path("/tmp").glob("*-rag-output.json"))
        if not candidates:
            return ["SKIPPED: no answer file found at $RAG_OUT or /tmp/*-rag-output.json"]
        answer_path = candidates[0]

    if not answer_path.exists():
        return [f"SKIPPED: {answer_path} does not exist"]

    try:
        payload = json.loads(answer_path.read_text())
    except json.JSONDecodeError as e:
        return [f"{answer_path} is not valid JSON: {e}"]

    if not isinstance(payload, dict):
        return [f"expected JSON object, got {type(payload).__name__}"]

    failures: list[str] = []
    missing = REQUIRED_KEYS - set(payload)
    if missing:
        failures.append(f"missing keys: {sorted(missing)}")

    if payload.get("schema_version") != SCHEMA_VERSION:
        failures.append(
            f"schema_version is {payload.get('schema_version')!r}, expected {SCHEMA_VERSION}"
        )

    if "answer" in payload and not isinstance(payload["answer"], str):
        failures.append("'answer' must be a string")
    if "citations" in payload:
        if not isinstance(payload["citations"], list):
            failures.append("'citations' must be a list")
        else:
            for i, c in enumerate(payload["citations"]):
                if not isinstance(c, dict):
                    failures.append(f"citations[{i}] must be an object")
                    continue
                if "chunk_id" not in c:
                    failures.append(f"citations[{i}] missing 'chunk_id'")
                if "source" not in c:
                    failures.append(f"citations[{i}] missing 'source'")

    return failures
