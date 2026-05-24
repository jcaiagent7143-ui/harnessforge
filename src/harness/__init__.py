"""harness — make any codebase agent-ready in 60 seconds.

The thesis: in 2026 developers still hand-author the agent environment
per-project per-IDE — system prompt, tool allowlist, test commands,
memory layout, MCP server selection. Harness inspects the repo, profiles
it via one LLM call, and generates a portable ``.harness/`` directory
plus IDE-specific adapter files (``.claude/CLAUDE.md``, ``.cursor/rules``,
``AGENTS.md``, ``.continue/config.json``, …) so any agent in any IDE can
work in the project immediately.

The headline command:

    $ harness init        # walk repo, generate .harness/ + IDE adapters
    $ harness run "task"  # run a task in this project's harness
    $ harness sync        # regenerate IDE adapters from .harness/
"""

from __future__ import annotations

from harness.profile import HarnessProfile

__version__ = "0.2.2"

__all__ = [
    "HarnessProfile",
    "__version__",
]
