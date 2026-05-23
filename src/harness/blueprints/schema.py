"""Blueprint spec — Pydantic model for ``blueprint.yaml``."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):
    """One file the blueprint renders into the user's repo."""

    path: str = Field(..., description="Repo-relative target path.")
    template: str = Field(..., description="Template filename under files/.")
    mode: int | None = Field(None, description="Optional unix mode (e.g. 0o755).")


class Validator(BaseModel):
    """A validator module the blueprint ships."""

    name: str
    module: str = Field(..., description="Python module under validators/ (no .py).")
    description: str = ""


class Suitability(BaseModel):
    """Which kinds of project this blueprint suits."""

    project_types: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class BlueprintSpec(BaseModel):
    """The validated contents of ``blueprint.yaml``."""

    name: str = Field(..., description="kebab-case identifier (rag-agent, etc.)")
    version: str = Field("1.0.0")
    display_name: str
    description: str
    agent_type: str = Field(..., description="rag | support | workflow | sales | browser | ...")
    suitable_for: Suitability = Field(default_factory=Suitability)
    recommended_mcps: list[str] = Field(default_factory=list)
    memory_schemas: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    generated_files: list[GeneratedFile] = Field(default_factory=list)
    validators: list[dict[str, Any]] = Field(default_factory=list)
    eval_set: str | None = Field(None, description="Path to eval questions YAML, under eval/.")
    extras: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


__all__ = ["BlueprintSpec", "GeneratedFile", "Suitability", "Validator"]
