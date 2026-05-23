"""Unit tests for the IDE adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.adapters import ALL_ADAPTERS, render_all
from harness.inspect_ import inspect_repo
from harness.profile import profile_from_inspection_template


@pytest.mark.parametrize("name,_render,_outs", ALL_ADAPTERS)
def test_adapter_renders_without_error(
    tmp_repo: Path, name: str, _render: object, _outs: list[str]
) -> None:
    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    written = _render(profile, tmp_repo)  # type: ignore[operator]
    assert written, f"adapter {name!r} wrote nothing"
    for p in written:
        assert p.exists() and p.stat().st_size > 0


def test_render_all_writes_all_five(tmp_repo: Path) -> None:
    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    written = render_all(profile, tmp_repo)
    assert set(written) == {"claude-code", "cursor", "continue", "codex-cli", "windsurf"}
    for name, paths in written.items():
        assert paths, f"adapter {name!r} returned []"


def test_windsurf_adapter_creates_windsurf_dir(tmp_repo: Path) -> None:
    from harness.adapters import windsurf

    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    paths = windsurf.render(profile, tmp_repo)
    assert (tmp_repo / ".windsurf" / "rules").exists()
    assert paths == [tmp_repo / ".windsurf" / "rules"]
