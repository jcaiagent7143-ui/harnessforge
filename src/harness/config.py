"""HarnessConfig — the schema for ``harness.config.json`` written at the
project root.

A tiny, versioned JSON file that records what blueprint a project is bound
to. ``harness sync`` and ``harness verify`` both read it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

CONFIG_FILENAME = "harness.config.json"


class HarnessConfig(BaseModel):
    """Top-level config written into a user's repo after ``harness init``."""

    schema_version: int = 1
    harness_version: str
    blueprint: str
    blueprint_version: str
    manifest: str = Field(
        default=".harness/manifest.json",
        description="Path to the file manifest used for safe re-runs.",
    )
    profile: str = Field(
        default=".harness/profile.yaml",
        description="Path to the canonical machine-readable profile.",
    )
    adapters: list[str] = Field(
        default_factory=list,
        description="IDE adapters rendered for this project (e.g. claude-code, cursor).",
    )
    skills_dir: str = Field(
        default="SKILLS",
        description="Directory containing anthropics/skills-compatible skills.",
    )
    extras: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form forward-compatible bag.",
    )

    @classmethod
    def load(cls, path: str | Path) -> HarnessConfig:
        return cls.model_validate_json(Path(path).read_text())

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json())

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), indent=2, sort_keys=False) + "\n"


__all__ = ["CONFIG_FILENAME", "HarnessConfig"]
