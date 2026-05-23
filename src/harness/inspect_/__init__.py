"""Repo inspectors — deterministic walks that extract project facts.

No LLM calls in this module. Pure file-reading + JSON/TOML parsing.
The output (an ``InspectionReport``) is what the profiler stage feeds
to the LLM as grounded context — so the LLM never has to guess what
language a project is in.
"""

from __future__ import annotations

from harness.inspect_.report import InspectionReport, inspect_repo

__all__ = ["InspectionReport", "inspect_repo"]
