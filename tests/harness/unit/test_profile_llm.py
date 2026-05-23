"""Cover the LLM profiler path in harness.profile."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from harness.inspect_ import inspect_repo
from harness.profile import profile_from_inspection_llm


class _StubProvider:
    """Minimal Provider-shaped stub; not a Mock — we want predictable JSON."""

    name = "stub"

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    async def complete(self, messages: list[Any], **kwargs: Any) -> Any:
        class _R:
            text = json.dumps(self._payload)
            tokens_in = 1
            tokens_out = 1

        return _R()


def test_llm_profiler_uses_returned_json(tmp_repo: Path) -> None:
    report = inspect_repo(tmp_repo)
    payload = {
        "name": "stub-name",
        "description": "stub description",
        "project_type": "library",
        "primary_language": "python",
        "frameworks": ["pytest"],
        "test_command": "pytest -q",
        "lint_command": None,
        "build_command": None,
        "dev_command": None,
        "forbidden_paths": [".env"],
        "forbidden_commands": ["rm -rf /"],
        "requires_human_approval": [],
        "required_env_vars": [],
        "secrets_handling": "use .env",
        "conventions": ["be careful"],
        "success_criteria": ["tests pass"],
        "recommended_mcps": ["filesystem"],
        "repo_tools": [],
        "default_model": "claude-sonnet-4-5",
        "cost_ceiling_usd_per_task": 0.5,
        "max_steps": 12,
        "harness_version": "0.1.0",
    }
    provider = _StubProvider(payload)
    profile = asyncio.run(profile_from_inspection_llm(report, provider))
    assert profile.name == "stub-name"
    assert profile.description == "stub description"
    assert profile.frameworks == ["pytest"]
    # Provenance is rewritten by the builder regardless
    assert profile.generated_from["profiler"] == "stub"


def test_llm_profiler_falls_back_on_garbage(tmp_repo: Path) -> None:
    class _GarbageProvider:
        name = "garbage"

        async def complete(self, *a: Any, **kw: Any) -> Any:
            class _R:
                text = "not json at all"
                tokens_in = 0
                tokens_out = 0

            return _R()

    report = inspect_repo(tmp_repo)
    profile = asyncio.run(profile_from_inspection_llm(report, _GarbageProvider()))
    # Falls back to template — has a name + language
    assert profile.name
    assert profile.primary_language == "python"
    assert "llm_error" in profile.generated_from


def test_llm_profiler_strips_markdown_fence(tmp_repo: Path) -> None:
    payload = {"name": "fenced", "description": "x", "project_type": "library",
               "primary_language": "python", "frameworks": [],
               "test_command": None, "lint_command": None, "build_command": None,
               "dev_command": None, "forbidden_paths": [], "forbidden_commands": [],
               "requires_human_approval": [], "required_env_vars": [],
               "secrets_handling": "x", "conventions": [], "success_criteria": [],
               "recommended_mcps": [], "repo_tools": [],
               "default_model": "x", "cost_ceiling_usd_per_task": 0.5, "max_steps": 12,
               "harness_version": "0.1.0"}

    class _Fenced:
        name = "fenced-provider"

        async def complete(self, *a: Any, **kw: Any) -> Any:
            class _R:
                text = "```json\n" + json.dumps(payload) + "\n```"
                tokens_in = 0
                tokens_out = 0

            return _R()

    report = inspect_repo(tmp_repo)
    profile = asyncio.run(profile_from_inspection_llm(report, _Fenced()))
    assert profile.name == "fenced"
