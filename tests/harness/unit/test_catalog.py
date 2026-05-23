"""Unit tests for the MCP catalog."""

from __future__ import annotations

import pytest

from harness.catalog import for_agent_type, get, load_catalog


def test_load_catalog_returns_entries() -> None:
    entries = load_catalog()
    assert len(entries) >= 20  # we ship ~25
    names = {e.name for e in entries}
    assert "filesystem" in names
    assert "fetch" in names
    assert "postgres" in names


def test_get_known_entry() -> None:
    fs = get("filesystem")
    assert fs is not None
    assert fs.requires_auth is False
    assert "rag" in fs.agent_types


def test_get_unknown_entry_returns_none() -> None:
    assert get("nonexistent-server-xyz") is None


def test_for_agent_type_rag() -> None:
    rag_servers = for_agent_type("rag")
    assert rag_servers
    assert any(e.name == "qdrant" for e in rag_servers)
    assert any(e.name == "chroma" for e in rag_servers)


def test_for_agent_type_support_includes_ticketing() -> None:
    support = for_agent_type("support")
    assert any(e.name == "github" for e in support)


def test_for_agent_type_workflow_includes_shell() -> None:
    wf = for_agent_type("workflow")
    assert any(e.name == "shell" for e in wf)


def test_load_catalog_is_cached() -> None:
    # lru_cache(maxsize=1) — same object instance on repeat call
    a = load_catalog()
    b = load_catalog()
    assert a is b


@pytest.mark.parametrize("agent_type", ["rag", "support", "workflow"])
def test_every_blueprint_agent_type_has_recommendations(agent_type: str) -> None:
    """Every shipped blueprint agent_type must have ≥3 recommended servers."""
    entries = for_agent_type(agent_type)
    assert len(entries) >= 3
