"""check_no_trades_without_gate — static scan for broker calls without an
explicit per-action approval gate.

This is the safety contract of the finance-agent blueprint. A trade call
that's *only* gated by a config flag (``if ENABLE_TRADING:``) fails. A
trade call gated by a runtime approval check (``if approved_in_session:``,
``if user_confirmed(...)``, ``if input("type yes...")``) passes.

We're conservative: a false positive means the agent has to add an
approval check it should have anyway. A false negative would mean
shipping autonomous trades.
"""

from __future__ import annotations

import re
from pathlib import Path

# Broker-shaped function names. Tunable.
TRADE_CALLS = re.compile(
    r"\b("
    r"order|"
    r"buy|"
    r"sell|"
    r"place_order|"
    r"submit_order|"
    r"cancel_order|"
    r"place_trade|"
    r"execute_trade|"
    r"market_order|"
    r"limit_order|"
    r"stop_order"
    r")\s*\("
)

# Gate-shaped patterns that should appear *before* the trade call in the
# same function. We accept any of these as "explicit approval gate".
GATE_PATTERNS = re.compile(
    r"approved_in_session|"
    r"user_confirmed|"
    r"confirm_trade|"
    r"input\s*\(.*yes|"
    r"prompt_user|"
    r"approval_granted|"
    r"@requires_approval"
)

# Files we should not scan.
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".harness", "SKILLS"}


def run(target: Path) -> list[str]:
    failures: list[str] = []
    py_files = [
        p for p in target.rglob("*.py")
        if not any(seg in SKIP_DIRS for seg in p.parts)
    ]

    if not py_files:
        return ["SKIPPED: no .py files to scan yet"]

    for path in py_files:
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue

        # Quick filter: does the file mention any trade call at all?
        if not TRADE_CALLS.search(text):
            continue

        # Walk function bodies (cheap regex-based, not AST — keeps validator dep-free).
        # Split on `def ` to get function chunks; check each for gate-then-call.
        chunks = re.split(r"^def\s+", text, flags=re.MULTILINE)
        for chunk in chunks[1:]:  # first chunk is module-level pre-defs
            # End the chunk at the next top-level def or class (rough)
            end = re.search(r"^(def\s|class\s)", chunk, flags=re.MULTILINE)
            if end:
                chunk = chunk[: end.start()]

            for m in TRADE_CALLS.finditer(chunk):
                preceding = chunk[: m.start()]
                if not GATE_PATTERNS.search(preceding):
                    # Find the line number of the offending call
                    line_no_in_chunk = preceding.count("\n") + 1
                    failures.append(
                        f"{path}: function calls `{m.group(1)}(...)` (line ~{line_no_in_chunk} of its function) "
                        f"without a preceding approval gate (looked for: approved_in_session, "
                        f"user_confirmed, confirm_trade, input('...yes...'), prompt_user, "
                        f"approval_granted, @requires_approval). "
                        f"This violates the finance-agent read-only-by-default contract."
                    )
                    # One report per file is enough — don't overwhelm
                    break

    return failures
