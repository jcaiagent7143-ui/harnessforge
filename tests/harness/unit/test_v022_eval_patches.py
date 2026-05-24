"""Regression tests for v0.2.2 — fixes surfaced by the 2026-05-24 support-agent A/B eval.

The eval (real Claude Code subagent on /tmp/eval-harness) found three issues:
  1. Agent spent ~3 minutes locating a Python with pytest — the generated
     AGENTS.md didn't mention pytest as a setup dependency.
  2. The support-agent's classify-intent SKILL.md listed only the canonical
     intent vocabulary; the agent had to discover the validator's vocab by
     reading scripts/verify_output.py and reconcile it with the task spec's
     vocab manually. SKILL.md now ships an explicit mapping table.
  3. SKILL.md's "below 0.5 → escalate" guidance read as a constant rather
     than a tuning knob — agents felt compelled to override without
     guidance on when. SKILL.md now ships a tuning-trade-off table.

These tests guard each fix so the next eval can't regress them silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest

BLUEPRINTS_ROOT = Path(__file__).parent.parent.parent.parent / "src" / "harness" / "blueprints"
ALL_BLUEPRINTS = ["rag-agent", "finance-agent", "support-agent", "workflow-agent", "python-cli-app"]


# ---------------------------------------------------------------------------
# Fix #1 — pytest-install hint in every blueprint's AGENTS.md.j2
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("blueprint", ALL_BLUEPRINTS)
def test_agents_md_has_setup_section_mentioning_pytest(blueprint: str) -> None:
    """Every blueprint's AGENTS.md.j2 must have a ## Setup section that mentions pytest.

    Regression for v0.2.2 fix #1: the support-agent A/B eval found that the
    agent spent 3 of 15 minutes locating a Python interpreter with pytest.
    A one-line setup hint in AGENTS.md eliminates this entirely.
    """
    agents_md = BLUEPRINTS_ROOT / blueprint / "files" / "AGENTS.md.j2"
    content = agents_md.read_text()

    assert "## Setup" in content, (
        f"{blueprint}: AGENTS.md.j2 must have a '## Setup' section. "
        "This was added in v0.2.2 to fix the pytest-install friction surfaced "
        "by the 2026-05-24 support-agent eval."
    )
    assert "pip install pytest" in content, (
        f"{blueprint}: AGENTS.md.j2 Setup section must mention `pip install pytest`. "
        "Without it, the agent has no signal that pytest is required."
    )


# ---------------------------------------------------------------------------
# Fix #2 — intent-vocabulary mapping table in classify-intent SKILL
# ---------------------------------------------------------------------------


def test_classify_intent_skill_has_vocabulary_mapping_table() -> None:
    """classify-intent SKILL.md must document the canonical→synonym mapping.

    Regression for v0.2.2 fix #2: the eval found the agent had to manually
    bridge the task spec's vocab (`technical`, `feature_request`) and the
    validator's vocab (`bug`, `feature`). SKILL.md now ships the mapping.
    """
    skill = BLUEPRINTS_ROOT / "support-agent" / "skills" / "classify-intent" / "SKILL.md"
    content = skill.read_text()

    # Section header is the signal of intent (no pun intended).
    assert "## Canonical intent vocabulary" in content, (
        "classify-intent SKILL.md must have a '## Canonical intent vocabulary' "
        "section. Added in v0.2.2 — without it, agents map task-spec names "
        "directly and break `harnessforge verify`."
    )

    # All five canonical names must appear together in the mapping table.
    for canonical in ["question", "bug", "feature", "billing", "other"]:
        assert f"`{canonical}`" in content, (
            f"classify-intent SKILL.md must enumerate canonical intent `{canonical}` "
            "in its vocabulary section."
        )

    # At least the most-common synonyms that the eval's task brief used.
    for synonym in ["technical", "feature_request", "account"]:
        assert synonym in content, (
            f"classify-intent SKILL.md must list `{synonym}` as a known "
            "synonym to map to a canonical name."
        )


def test_classify_intent_skill_matches_validator_intents() -> None:
    """The SKILL doc's claimed canonical set must match what the validator enforces.

    If these diverge, the SKILL would lie to the agent and the agent's
    correctly-classified output would still fail verify. Hard guard.
    """
    skill = BLUEPRINTS_ROOT / "support-agent" / "skills" / "classify-intent" / "SKILL.md"
    validator = BLUEPRINTS_ROOT / "support-agent" / "files" / "verify_output.py.j2"
    skill_content = skill.read_text()
    validator_content = validator.read_text()

    # Validator hard-codes the canonical set
    assert (
        'VALID_INTENTS = {"question", "bug", "feature", "billing", "other"}' in validator_content
    ), (
        "verify_output.py.j2 must define VALID_INTENTS exactly as documented "
        "in classify-intent SKILL.md. If you change one, change both."
    )
    # And the SKILL's table covers exactly that set
    for canonical in ["question", "bug", "feature", "billing", "other"]:
        assert canonical in skill_content


# ---------------------------------------------------------------------------
# Fix #3 — confidence threshold is documented as a tuning knob, not a constant
# ---------------------------------------------------------------------------


def test_classify_intent_skill_documents_threshold_as_tunable() -> None:
    """classify-intent SKILL.md must frame the 0.5 threshold as a tuning knob.

    Regression for v0.2.2 fix #3: the eval agent felt compelled to deviate
    to 0.45 without explicit guidance on when to lower or raise. SKILL.md
    now ships a trade-off table.
    """
    skill = BLUEPRINTS_ROOT / "support-agent" / "skills" / "classify-intent" / "SKILL.md"
    content = skill.read_text()

    assert "## Confidence threshold" in content, (
        "classify-intent SKILL.md must have a '## Confidence threshold' section."
    )
    # The trade-off must show both directions
    assert "Lower the threshold" in content
    assert "Raise the threshold" in content
    # And state it's a knob, not a constant
    assert "tuning knob" in content.lower(), (
        "SKILL.md must explicitly say the threshold is a tuning knob, not a constant."
    )
