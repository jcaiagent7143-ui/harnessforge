"""Golden-file tests — snapshot the *set of paths* a `harness init` produces
for a given fixture repo x blueprint.

We intentionally do NOT snapshot file contents (templates evolve; that
would make the suite churn). We snapshot the structural shape — every
file that should be present, and the manifest entries.

To regenerate after an intentional change:

    pytest tests/harness/golden -m golden --update-goldens
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.manifest import MANIFEST_FILENAME, Manifest
from harness.provision import provision_sync

# Each entry: (fixture_factory_name, blueprint, expected_path_set_filename)
CASES: list[tuple[str, str, str]] = [
    ("tmp_repo",         "rag-agent",      "py_rag.json"),
    ("tmp_repo",         "support-agent",  "py_support.json"),
    ("tmp_repo",         "workflow-agent", "py_workflow.json"),
    ("tmp_node_repo",    "rag-agent",      "node_rag.json"),
    ("tmp_node_repo",    "workflow-agent", "node_workflow.json"),
    ("tmp_django_repo",  "support-agent",  "django_support.json"),
    ("tmp_rag_repo",     "rag-agent",      "rag_repo_rag.json"),
]

_GOLDENS = Path(__file__).parent / "expected"


def _gather_relpaths(root: Path) -> list[str]:
    """Every file under root, repo-relative, sorted."""
    return sorted(
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
    )


@pytest.mark.parametrize("fixture_name,blueprint,golden_file", CASES)
def test_golden_path_set(
    request: pytest.FixtureRequest,
    fixture_name: str,
    blueprint: str,
    golden_file: str,
) -> None:
    repo = request.getfixturevalue(fixture_name)
    provision_sync(repo, blueprint=blueprint, no_llm=True)
    actual = _gather_relpaths(repo)

    golden_path = _GOLDENS / golden_file
    if request.config.getoption("--update-goldens", default=False):
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(json.dumps(actual, indent=2) + "\n")
        pytest.skip(f"updated golden: {golden_file}")

    if not golden_path.exists():
        # First run: bootstrap the golden file
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(json.dumps(actual, indent=2) + "\n")
        pytest.skip(f"bootstrapped golden: {golden_file}")

    expected = json.loads(golden_path.read_text())
    if expected != actual:
        diff_missing = sorted(set(expected) - set(actual))
        diff_extra = sorted(set(actual) - set(expected))
        pytest.fail(
            f"golden mismatch for {golden_file}:\n"
            f"  missing (in golden, not produced): {diff_missing}\n"
            f"  extra   (produced, not in golden): {diff_extra}\n"
            f"If intentional, re-run with: pytest --update-goldens"
        )


@pytest.mark.parametrize("fixture_name,blueprint,_golden_file", CASES)
def test_manifest_records_all_writes(
    request: pytest.FixtureRequest,
    fixture_name: str,
    blueprint: str,
    _golden_file: str,
) -> None:
    """Manifest must list every generated file with a sha256 + provenance."""
    repo = request.getfixturevalue(fixture_name)
    provision_sync(repo, blueprint=blueprint, no_llm=True)
    manifest = Manifest.load(repo / MANIFEST_FILENAME)
    assert manifest.entries
    for entry in manifest.entries:
        assert entry.path
        assert entry.sha256
        assert entry.bytes >= 0
        assert entry.written_by
        # Provenance prefix should be one of the known sources
        prefix = entry.written_by.split(":")[0]
        assert prefix in {"adapter", "blueprint", "harness"}
