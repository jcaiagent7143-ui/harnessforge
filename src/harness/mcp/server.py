"""harness-kit MCP (stdio) server.

Exposes five tools to any MCP client (Claude Desktop, Claude Code,
Cursor, Cline, Continue, Windsurf, ...). The same JSON contract as the
``harness verify`` CLI — your coding agent can call the harness as a
tool with typed schemas.

Tools:

  * ``harness_inspect``         — deterministic repo InspectionReport
  * ``harness_blueprint_list``  — installed blueprints + metadata
  * ``harness_skills_list``     — local SKILLS/ + blueprint catalog
  * ``harness_verify``          — run blueprint validators (same as `harness verify --json`)
  * ``harness_profile_read``    — current ``.harness/profile.yaml`` as JSON
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from pathlib import Path
from typing import Any

import yaml

from harness.config import CONFIG_FILENAME, HarnessConfig
from harness.inspect_ import inspect_repo
from harness.skills_io import list_skills

DEFAULT_ROOT = Path(os.environ.get("HARNESS_ROOT", "."))


# ── tool schemas ───────────────────────────────────────────────────────────

_INSPECT_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Repo path. Default: $HARNESS_ROOT or CWD."},
    },
}

_BLUEPRINT_LIST_SCHEMA = {"type": "object", "properties": {}}

_SKILLS_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Repo path. Default: $HARNESS_ROOT or CWD."},
    },
}

_VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Repo path. Default: $HARNESS_ROOT or CWD."},
        "check": {"type": "string", "description": "Run only this named check."},
        "fail_fast": {"type": "boolean", "default": False},
    },
}

_PROFILE_READ_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Repo path. Default: $HARNESS_ROOT or CWD."},
    },
}


# ── tool handlers ─────────────────────────────────────────────────────────


def _path(args: dict[str, Any]) -> Path:
    return Path(args.get("path") or DEFAULT_ROOT).resolve()


async def _handle_inspect(args: dict[str, Any]) -> str:
    report = inspect_repo(_path(args))
    return json.dumps(report.to_prompt_dict(), indent=2, default=str)


async def _handle_blueprint_list(_: dict[str, Any]) -> str:
    from harness.blueprints import list_blueprints

    bps = list_blueprints()
    payload = [
        {
            "name": bp.name,
            "version": bp.version,
            "display_name": bp.display_name,
            "description": bp.description,
            "agent_type": bp.agent_type,
            "recommended_mcps": bp.recommended_mcps,
            "skills": bp.skills,
            "validators": [v["name"] for v in bp.validators],
        }
        for bp in bps
    ]
    return json.dumps({"blueprints": payload}, indent=2)


async def _handle_skills_list(args: dict[str, Any]) -> str:
    from harness.blueprints import iter_catalog_skills

    root = _path(args)
    local = list_skills(root / "SKILLS")
    catalog = [
        {
            "blueprint": bp_name,
            "name": s.name,
            "version": s.version,
            "description": s.description,
            "when_to_use": s.when_to_use,
        }
        for bp_name, s in iter_catalog_skills()
    ]
    return json.dumps(
        {
            "local": [
                {"name": s.name, "version": s.version, "description": s.description}
                for s in local
            ],
            "catalog": catalog,
        },
        indent=2,
    )


async def _handle_verify(args: dict[str, Any]) -> str:
    from harness.blueprints import load_blueprint
    from harness.validators import run_checks

    root = _path(args)
    cfg_path = root / CONFIG_FILENAME
    if not cfg_path.exists():
        return json.dumps(
            {"error": f"no {CONFIG_FILENAME} at {root} — run `harness init` first"}
        )
    cfg = HarnessConfig.load(cfg_path)
    bp = load_blueprint(cfg.blueprint)
    report = run_checks(bp, root, only=args.get("check"), fail_fast=bool(args.get("fail_fast")))
    return json.dumps(report, indent=2, default=str)


async def _handle_profile_read(args: dict[str, Any]) -> str:
    profile_path = _path(args) / ".harness" / "profile.yaml"
    if not profile_path.exists():
        return json.dumps({"error": f"no profile at {profile_path}"})
    data = yaml.safe_load(profile_path.read_text())
    return json.dumps(data, indent=2, default=str)


# ── server wiring ─────────────────────────────────────────────────────────


def _build_server() -> Any:
    from mcp.server import Server
    from mcp.types import TextContent, Tool

    server = Server("harness")

    tools = [
        Tool(
            name="harness_inspect",
            description=(
                "Walk a repo and return a deterministic InspectionReport "
                "(languages, frameworks, commands, env vars, CI, existing "
                "agent configs). No LLM. Safe to call on any directory."
            ),
            inputSchema=_INSPECT_SCHEMA,
        ),
        Tool(
            name="harness_blueprint_list",
            description=(
                "List every installed blueprint with metadata "
                "(name, description, agent type, recommended MCPs, skills)."
            ),
            inputSchema=_BLUEPRINT_LIST_SCHEMA,
        ),
        Tool(
            name="harness_skills_list",
            description=(
                "List anthropics/skills-compatible skills under the repo's "
                "SKILLS/ directory and in the blueprint catalog."
            ),
            inputSchema=_SKILLS_LIST_SCHEMA,
        ),
        Tool(
            name="harness_verify",
            description=(
                "Run blueprint validators against a bootstrapped repo. Same "
                "stable JSON contract as `harness verify --json`. Returns a "
                "summary + per-check status. Repo must have a "
                "harness.config.json."
            ),
            inputSchema=_VERIFY_SCHEMA,
        ),
        Tool(
            name="harness_profile_read",
            description="Return the parsed `.harness/profile.yaml` as JSON.",
            inputSchema=_PROFILE_READ_SCHEMA,
        ),
    ]

    handlers = {
        "harness_inspect": _handle_inspect,
        "harness_blueprint_list": _handle_blueprint_list,
        "harness_skills_list": _handle_skills_list,
        "harness_verify": _handle_verify,
        "harness_profile_read": _handle_profile_read,
    }

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return tools

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        handler = handlers.get(name)
        if handler is None:
            return [TextContent(type="text", text=json.dumps({"error": f"unknown tool {name!r}"}))]
        try:
            text = await handler(arguments or {})
        except Exception as e:
            text = json.dumps({"error": f"{type(e).__name__}: {e}"})
        return [TextContent(type="text", text=text)]

    return server


async def _serve_stdio() -> None:
    from mcp.server.stdio import stdio_server

    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def run_stdio() -> None:
    """Blocking entrypoint — what `harness mcp` calls."""
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_serve_stdio())


if __name__ == "__main__":
    run_stdio()
