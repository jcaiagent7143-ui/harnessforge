"""Curated MCP server catalog.

Read the YAML once at import time; expose helpers to query by name or
agent type.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_CATALOG_PATH = Path(__file__).parent / "mcps.yaml"


@dataclass(frozen=True)
class McpEntry:
    name: str
    command: str
    description: str
    requires_auth: bool
    agent_types: tuple[str, ...]
    install_hint: str = ""


@lru_cache(maxsize=1)
def load_catalog() -> list[McpEntry]:
    data: dict[str, Any] = yaml.safe_load(_CATALOG_PATH.read_text())
    out: list[McpEntry] = []
    for raw in data.get("servers", []):
        out.append(
            McpEntry(
                name=raw["name"],
                command=raw["command"],
                description=raw.get("description", ""),
                requires_auth=bool(raw.get("requires_auth", False)),
                agent_types=tuple(raw.get("agent_types", [])),
                install_hint=raw.get("install_hint", ""),
            )
        )
    return out


def get(name: str) -> McpEntry | None:
    for e in load_catalog():
        if e.name == name:
            return e
    return None


def for_agent_type(agent_type: str) -> list[McpEntry]:
    return [e for e in load_catalog() if agent_type in e.agent_types]


__all__ = ["McpEntry", "for_agent_type", "get", "load_catalog"]
