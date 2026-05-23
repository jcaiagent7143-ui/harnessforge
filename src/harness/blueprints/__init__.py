"""Blueprint system — reusable agent patterns harness can render into a repo.

A *blueprint* is a directory under ``harness/blueprints/`` containing:

  * ``blueprint.yaml`` — the spec (validated by :class:`BlueprintSpec`)
  * ``files/`` — Jinja2 templates rendered into the user's repo root
  * ``skills/`` — anthropics/skills-compatible skill bundles
  * ``validators/`` — Python modules with ``run(target: Path) -> list[str]``
  * ``memory_schemas/`` — JSON Schemas the blueprint expects
  * ``eval/`` — optional eval question set

To add a blueprint: create a directory, write the yaml, drop templates +
validators + skills into the right subdirs. The loader picks it up on
the next CLI invocation.
"""

from __future__ import annotations

from collections.abc import Iterator
from importlib import resources
from pathlib import Path

from harness.blueprints.loader import (
    blueprint_dir,
    blueprint_skill_source_dir,
    iter_catalog_skills,
    list_blueprints,
    load_blueprint,
    recommend_blueprint,
    render_blueprint_files,
    render_blueprint_memory_schemas,
    render_blueprint_skills,
)
from harness.blueprints.schema import BlueprintSpec

__all__ = [
    "BlueprintSpec",
    "blueprint_dir",
    "blueprint_skill_source_dir",
    "iter_catalog_skills",
    "list_blueprints",
    "load_blueprint",
    "recommend_blueprint",
    "render_blueprint_files",
    "render_blueprint_memory_schemas",
    "render_blueprint_skills",
]


# Re-export the resources module path so external tooling can introspect
# the installed blueprints without depending on importlib internals.
def blueprints_root() -> Path:
    """Return the on-disk directory containing all bundled blueprints."""
    # importlib.resources.files returns a Traversable; for our package layout
    # it's always a real Path. Cast through str → Path to satisfy mypy.
    try:
        return Path(str(resources.files("harness.blueprints")))
    except (TypeError, ModuleNotFoundError):
        return Path(__file__).parent


def _all_blueprint_names() -> Iterator[str]:
    """Iterate every blueprint name found on disk (one dir per blueprint)."""
    root = blueprints_root()
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "blueprint.yaml").exists():
            yield child.name
