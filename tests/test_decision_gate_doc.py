"""Structural guards for the decision-gate ROUTE (#6).

The decision gate is the moat: it must keep REJECTing non-loops even as it gains the ROUTE branch.
These tests are deliberately about *structure*, not prose — they fail loudly if a future edit drops the
Fail/REJECT verdict or the routing table, so the gate can't silently turn into a rubber stamp.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DG = (ROOT / "references" / "decision-gate.md").read_text(encoding="utf-8")
DG_L = DG.lower()
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
SKILL_L = SKILL.lower()


def test_tier0_gate_preserved():
    # The 4 conditions + an all-must-hold framing remain the entry test.
    assert "ALL must hold" in DG
    for cond in ("recurs", "objective gate", "budget", "agent can run"):
        assert cond in DG_L, f"Tier-0 condition missing: {cond}"


def test_reject_verdict_is_the_moat():
    # Fail must still reject and recommend an honest alternative — the most valuable thing the gate does.
    assert "fail" in DG_L
    assert "reject" in DG_L
    assert "human-reviewed task" in DG_L or "human-gated" in DG_L
    assert "one high-quality pass" in DG_L or "single high-quality pass" in DG_L


def test_route_branch_present_for_all_archetypes():
    assert "route" in DG_L
    for archetype in ("ratchet", "critic-panel", "checkpoint", "budget", "quorum"):
        assert archetype in DG_L, f"route table does not cover: {archetype}"


def test_route_expands_pass_set_without_lowering_the_bar():
    # The strategic claim must be explicit so it can't drift: archetypes expand what passes, the bar is unchanged.
    assert "without lowering the bar" in DG_L
    assert "bar is unchanged" in DG_L or "never waves a task through" in DG_L


def test_skill_routes_on_pass_and_pins_shape():
    # Step 1 routes on Pass; Step 4 pins the verifier shape/kind, not just a work pattern.
    assert "route" in SKILL_L
    assert "verifier.shape" in SKILL or "verifier.kind" in SKILL
    assert "orthogonal" in SKILL_L  # the axis discipline is stated in the wizard
