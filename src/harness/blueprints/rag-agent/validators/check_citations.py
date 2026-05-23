"""check_citations — verify a sample RAG answer cites every factual claim.

If no answer file is present yet (the agent hasn't run), the check is
``skipped`` rather than ``failed`` — citation validation requires real output.

Default answer path: ``$RAG_OUT`` env var, or ``/tmp/<project>-rag-output.json``.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

CITATION_RE = re.compile(r"\[([a-zA-Z0-9_-]{4,64})\]")


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
        return [f"SKIPPED: {answer_path} does not exist (agent hasn't produced an answer yet)"]

    try:
        payload = json.loads(answer_path.read_text())
    except json.JSONDecodeError as e:
        return [f"{answer_path} is not valid JSON: {e}"]

    if not isinstance(payload, dict):
        return [f"{answer_path}: expected JSON object, got {type(payload).__name__}"]

    answer = payload.get("answer", "")
    citations = payload.get("citations", [])
    if not isinstance(answer, str) or not isinstance(citations, list):
        return [f"{answer_path}: malformed shape — needs str 'answer' and list 'citations'"]

    cited_in_text = set(CITATION_RE.findall(answer))
    listed = {c.get("chunk_id") for c in citations if isinstance(c, dict)}
    listed.discard(None)

    failures: list[str] = []
    for cid in sorted(cited_in_text - listed):
        failures.append(f"chunk_id {cid!r} cited in answer text but missing from citations[]")
    for cid in sorted(listed - cited_in_text):
        failures.append(f"chunk_id {cid!r} listed in citations[] but never cited in answer text")

    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    for s in sentences:
        if len(s) < 16:
            continue
        is_factual = bool(re.search(r"\d|[A-Z][a-z]{2,}|\"", s))
        if is_factual and not CITATION_RE.search(s):
            failures.append(f"likely factual sentence missing [chunk_id]: {s[:80]!r}")
            break

    return failures
