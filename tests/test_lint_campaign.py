"""Tests for lint_campaign_spec — S4 of the campaign-atom plan.

Pure-python tests only (no bash subprocess calls), so no _bash_ok() / skipif guard needed.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LINT = ROOT / "scripts" / "loopprint-lint.py"
EXAMPLE = ROOT / "examples" / "campaign-staged-remediation"


def _load_lint():
    spec = importlib.util.spec_from_file_location("loopprint_lint", LINT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lint_mod = _load_lint()
lint_campaign_spec = lint_mod.lint_campaign_spec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_leaf(tmp_path: Path, name: str) -> None:
    """Write a minimal lint-GREEN gate leaf loop into tmp_path/name/."""
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "loop-spec.yaml").write_text(yaml.dump({
        "slug": f"test-campaign-leaf-{name}",
        "goal": f"Leaf loop goal for {name}.",
        "pattern": "spec-driven",
        "state": {"path": f"{name}/state.md"},
        "verifier": {"command": "bash verify.sh", "shape": "gate"},
        "stop": {"max_iterations": 5},
        "autonomy": "full",
    }))
    (d / "verify.sh").write_text("#!/usr/bin/env bash\nexit 0\n")


def _write_valid(tmp_path: Path) -> dict:
    """Write supporting files and return a valid campaign spec dict."""
    _write_leaf(tmp_path, "stage-1")
    _write_leaf(tmp_path, "stage-2")
    (tmp_path / "plan.md").write_text("# Plan\nTwo-stage campaign.\n")
    return {
        "schema_version": 1,
        "kind": "campaign",
        "goal": "Drive all findings to zero in two supervised stages.",
        "plan": "plan.md",
        "autonomy": "checkpoint",
        "stages": [
            {
                "slug": "stage-1-reverse",
                "goal": "Reverse-spec.",
                "loop_dir": "stage-1",
                "stage_success": "gate",
            },
            {
                "slug": "stage-2-remedi",
                "goal": "Remediate.",
                "loop_dir": "stage-2",
                "stage_success": "gate",
            },
        ],
        "stop": {"on_stage_failure": "halt-and-flag"},
    }


def _lint(tmp_path: Path, spec: dict) -> tuple:
    spec_path = str(tmp_path / "campaign-spec.yaml")
    return lint_campaign_spec(spec_path, spec)


# ---------------------------------------------------------------------------
# GREEN: shipped example must lint clean
# ---------------------------------------------------------------------------

def test_example_campaign_lints_green():
    """The shipped example campaign-spec.yaml must lint GREEN (zero blocking)."""
    spec_path = str(EXAMPLE / "campaign-spec.yaml")
    with open(spec_path) as fh:
        spec = yaml.safe_load(fh)
    blocking, _ = lint_campaign_spec(spec_path, spec)
    assert blocking == [], f"Expected GREEN, got blocking: {blocking}"


def test_valid_spec_no_advisory(tmp_path):
    """A fully valid campaign spec produces no advisory either."""
    spec = _write_valid(tmp_path)
    blocking, advisory = _lint(tmp_path, spec)
    assert blocking == [], f"Unexpected blocking: {blocking}"
    assert advisory == [], f"Unexpected advisory: {advisory}"


# ---------------------------------------------------------------------------
# RED: empty / missing stages
# ---------------------------------------------------------------------------

def test_empty_stages_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["stages"] = []
    blocking, _ = _lint(tmp_path, spec)
    assert any("stages" in b for b in blocking), f"Expected stages finding, got: {blocking}"


def test_missing_stages_key_red(tmp_path):
    spec = _write_valid(tmp_path)
    del spec["stages"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("stages" in b for b in blocking), f"Expected stages finding, got: {blocking}"


def test_stages_not_list_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["stages"] = "stage-1"  # string, not list
    blocking, _ = _lint(tmp_path, spec)
    assert any("stages" in b for b in blocking), f"Expected stages finding, got: {blocking}"


# ---------------------------------------------------------------------------
# RED: duplicate slug
# ---------------------------------------------------------------------------

def test_duplicate_slug_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["stages"][1]["slug"] = spec["stages"][0]["slug"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("slug" in b and "unique" in b for b in blocking), (
        f"Expected duplicate-slug finding, got: {blocking}"
    )


# ---------------------------------------------------------------------------
# RED: bad stage_success value
# ---------------------------------------------------------------------------

def test_bad_stage_success_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["stages"][0]["stage_success"] = "always-yes"
    blocking, _ = _lint(tmp_path, spec)
    assert any("stage_success" in b for b in blocking), (
        f"Expected stage_success finding, got: {blocking}"
    )


def test_missing_stage_success_red(tmp_path):
    spec = _write_valid(tmp_path)
    del spec["stages"][0]["stage_success"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("stage_success" in b for b in blocking), (
        f"Expected stage_success missing finding, got: {blocking}"
    )


# ---------------------------------------------------------------------------
# RED: loop_dir problems
# ---------------------------------------------------------------------------

def test_nonexistent_loop_dir_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["stages"][0]["loop_dir"] = "nonexistent-dir"
    blocking, _ = _lint(tmp_path, spec)
    assert any("loop_dir" in b or "nonexistent" in b for b in blocking), (
        f"Expected loop_dir finding, got: {blocking}"
    )


def test_missing_loop_spec_yaml_red(tmp_path):
    """loop_dir exists but is missing loop-spec.yaml."""
    spec = _write_valid(tmp_path)
    (tmp_path / "stage-1" / "loop-spec.yaml").unlink()
    blocking, _ = _lint(tmp_path, spec)
    assert any("loop-spec.yaml" in b for b in blocking), (
        f"Expected loop-spec.yaml finding, got: {blocking}"
    )


def test_missing_verify_sh_red(tmp_path):
    """loop_dir exists but is missing verify.sh."""
    spec = _write_valid(tmp_path)
    (tmp_path / "stage-1" / "verify.sh").unlink()
    blocking, _ = _lint(tmp_path, spec)
    assert any("verify.sh" in b for b in blocking), (
        f"Expected verify.sh finding, got: {blocking}"
    )


def test_missing_loop_dir_key_red(tmp_path):
    spec = _write_valid(tmp_path)
    del spec["stages"][0]["loop_dir"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("loop_dir" in b for b in blocking), (
        f"Expected loop_dir missing finding, got: {blocking}"
    )


# ---------------------------------------------------------------------------
# RED: missing plan file
# ---------------------------------------------------------------------------

def test_missing_plan_file_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["plan"] = "no-such-plan.md"
    blocking, _ = _lint(tmp_path, spec)
    assert any("plan" in b for b in blocking), f"Expected plan finding, got: {blocking}"


def test_missing_plan_key_red(tmp_path):
    spec = _write_valid(tmp_path)
    del spec["plan"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("plan" in b for b in blocking), f"Expected plan-key finding, got: {blocking}"


# ---------------------------------------------------------------------------
# RED: autonomy != checkpoint
# ---------------------------------------------------------------------------

def test_autonomy_not_checkpoint_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["autonomy"] = "full"
    blocking, _ = _lint(tmp_path, spec)
    assert any("autonomy" in b for b in blocking), (
        f"Expected autonomy finding, got: {blocking}"
    )


def test_missing_autonomy_red(tmp_path):
    spec = _write_valid(tmp_path)
    del spec["autonomy"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("autonomy" in b for b in blocking), (
        f"Expected autonomy-missing finding, got: {blocking}"
    )


# ---------------------------------------------------------------------------
# RED: goal empty
# ---------------------------------------------------------------------------

def test_goal_empty_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["goal"] = ""
    blocking, _ = _lint(tmp_path, spec)
    assert any("goal" in b for b in blocking), f"Expected goal finding, got: {blocking}"


def test_goal_missing_red(tmp_path):
    spec = _write_valid(tmp_path)
    del spec["goal"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("goal" in b for b in blocking), f"Expected goal-missing finding, got: {blocking}"


# ---------------------------------------------------------------------------
# RED: kind != campaign (but stages present — detected as campaign, kind wrong)
# ---------------------------------------------------------------------------

def test_kind_not_campaign_red(tmp_path):
    spec = _write_valid(tmp_path)
    spec["kind"] = "loop"
    blocking, _ = _lint(tmp_path, spec)
    assert any("kind" in b for b in blocking), f"Expected kind finding, got: {blocking}"


def test_kind_missing_red(tmp_path):
    spec = _write_valid(tmp_path)
    del spec["kind"]
    blocking, _ = _lint(tmp_path, spec)
    assert any("kind" in b for b in blocking), f"Expected kind-missing finding, got: {blocking}"


# ---------------------------------------------------------------------------
# RED: malformed input never crashes — clean RED instead
# ---------------------------------------------------------------------------

def test_none_spec_no_crash(tmp_path):
    """lint_campaign_spec must not crash on a None spec."""
    blocking, _ = lint_campaign_spec(str(tmp_path / "campaign-spec.yaml"), {})
    assert isinstance(blocking, list)
    assert len(blocking) > 0  # empty dict has many violations


def test_stage_not_dict_no_crash(tmp_path):
    """Non-dict stage entry must not crash — produce a blocking finding."""
    spec = _write_valid(tmp_path)
    spec["stages"].append("not-a-dict")
    blocking, _ = _lint(tmp_path, spec)
    assert isinstance(blocking, list)


# ---------------------------------------------------------------------------
# Advisory (non-failing)
# ---------------------------------------------------------------------------

def test_ratchet_shape_gate_success_advisory(tmp_path):
    """Leaf verifier.shape:ratchet but stage_success:gate -> advisory, not blocking."""
    spec = _write_valid(tmp_path)
    # Overwrite stage-1 loop-spec with ratchet shape + required budget
    leaf = yaml.safe_load((tmp_path / "stage-1" / "loop-spec.yaml").read_text())
    leaf["verifier"]["shape"] = "ratchet"
    leaf["stop"]["budget"] = {"wall_clock_minutes": 30}
    (tmp_path / "stage-1" / "loop-spec.yaml").write_text(yaml.dump(leaf))
    # stage_success stays "gate"
    blocking, advisory = _lint(tmp_path, spec)
    assert blocking == [], f"Expected no blocking, got: {blocking}"
    assert any("ratchet" in a for a in advisory), (
        f"Expected ratchet/shape advisory, got: {advisory}"
    )


def test_gate_shape_ratchet_success_advisory(tmp_path):
    """Leaf verifier.shape:gate but stage_success:ratchet -> advisory, not blocking."""
    spec = _write_valid(tmp_path)
    spec["stages"][0]["stage_success"] = "ratchet"
    # stage-1 leaf already has shape:gate
    blocking, advisory = _lint(tmp_path, spec)
    assert blocking == [], f"Expected no blocking, got: {blocking}"
    assert any("gate" in a for a in advisory), (
        f"Expected gate/shape advisory, got: {advisory}"
    )


def test_schema_version_future_advisory(tmp_path):
    """schema_version newer than linter -> advisory, not blocking."""
    spec = _write_valid(tmp_path)
    spec["schema_version"] = 9999
    blocking, advisory = _lint(tmp_path, spec)
    assert blocking == [], f"Expected no blocking, got: {blocking}"
    assert any("schema_version" in a or "9999" in a for a in advisory), (
        f"Expected schema_version advisory, got: {advisory}"
    )
