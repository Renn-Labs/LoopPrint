"""Tests for scripts/looptimal-persona-promote.py — the Agent Foundry Dynamism -> Consistency
promotion mechanism (references/agent-foundry.md #9). Covers both direct-import unit coverage of
validate_persona()/draft_from() and CLI-level subprocess coverage of the promote path, including
project vs. user scope routing."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "looptimal-persona-promote.py"
PERSONAS_DIR = REPO / "personas"


def _load():
    spec = importlib.util.spec_from_file_location("looptimal_persona_promote", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pp = _load()

GOOD_PERSONA = """# Demo Expert

**Identity:** I demonstrate that this validator works end to end.

## Core Capabilities
- Prove the write path works
- Prove the validate path works

## Failure Mode I Own
**Forgetting to verify** — shipping a script without running it for real.

## Anti-Patterns to Avoid
- Trusting code that was never executed
- Skipping the adversarial cases

## Checklist I Apply
1. Did I actually run this?
2. Did I check the failure cases too?
"""

TIER_B_PERSONA = """You are a **data-migration** domain expert operating inside Looptimal execution.

## Mission context

Migrate the pricing table schema for objective obj-9f2. Task node T-12 covers the cutover.

## Success criteria (outcome-based)

Criterion c3 passes: zero rows dropped, verified via row-count parity check.

You succeed only when the **sealed acceptance suite** passes via external verification — not \
when you self-report GREEN or close tasks.

## Operating rules

1. Maker != checker.

## Anti-patterns (do not)

- Running a destructive migration without a dry-run count-parity check first
- Assuming a foreign-key constraint holds without verifying it against live schema

## Pre-action checklist

1. Have I dry-run the migration against a snapshot and confirmed row-count parity?
2. Do I have a rollback script tested against the same snapshot?

## Output format

- Hypothesis / Actions / Artifacts / Receipts / Residual risk
"""


# ---- validate_persona(): the real library is the regression guard ------------------
@pytest.mark.parametrize("persona_path", sorted(PERSONAS_DIR.glob("*.md")), ids=lambda p: p.name)
def test_all_real_personas_validate_green(persona_path):
    text = persona_path.read_text(encoding="utf-8")
    findings = pp.validate_persona(text)
    assert findings == [], f"{persona_path.name}: {findings}"


def test_validate_persona_accepts_good_fixture():
    assert pp.validate_persona(GOOD_PERSONA) == []


def test_validate_persona_missing_section_is_red():
    bad = GOOD_PERSONA.replace("## Failure Mode I Own\n**Forgetting to verify** — shipping a "
                                "script without running it for real.\n\n", "")
    findings = pp.validate_persona(bad)
    assert any("section headers must be exactly" in f for f in findings)


def test_validate_persona_wrong_order_is_red():
    # swap Anti-Patterns and Checklist order
    reordered = (
        "# Demo Expert\n\n**Identity:** I demonstrate order checks.\n\n"
        "## Core Capabilities\n- Thing\n\n"
        "## Failure Mode I Own\n**Sloppiness** — misses things.\n\n"
        "## Checklist I Apply\n1. Did I check?\n\n"
        "## Anti-Patterns to Avoid\n- Bad thing\n"
    )
    findings = pp.validate_persona(reordered)
    assert any("in that order" in f for f in findings)


def test_validate_persona_core_capabilities_not_bullets_is_red():
    bad = GOOD_PERSONA.replace(
        "## Core Capabilities\n- Prove the write path works\n- Prove the validate path works",
        "## Core Capabilities\nI do a lot of stuff, generally.",
    )
    findings = pp.validate_persona(bad)
    assert any("Core Capabilities" in f and "bullet list" in f for f in findings)


def test_validate_persona_anti_patterns_not_bullets_is_red():
    bad = GOOD_PERSONA.replace(
        "## Anti-Patterns to Avoid\n- Trusting code that was never executed\n"
        "- Skipping the adversarial cases",
        "## Anti-Patterns to Avoid\nJust generally being careless.",
    )
    findings = pp.validate_persona(bad)
    assert any("Anti-Patterns to Avoid" in f and "bullet list" in f for f in findings)


def test_validate_persona_failure_mode_not_single_bold_line_is_red():
    bad = GOOD_PERSONA.replace(
        "**Forgetting to verify** — shipping a script without running it for real.",
        "Forgetting to verify things, generally speaking, without any bold name at all.",
    )
    findings = pp.validate_persona(bad)
    assert any("Failure Mode I Own" in f for f in findings)


def test_validate_persona_checklist_not_numbered_is_red():
    bad = GOOD_PERSONA.replace(
        "## Checklist I Apply\n1. Did I actually run this?\n2. Did I check the failure cases too?",
        "## Checklist I Apply\n- Did I actually run this?\n- Did I check the failure cases too?",
    )
    findings = pp.validate_persona(bad)
    assert any("Checklist I Apply" in f and "numbered list" in f for f in findings)


def test_validate_persona_missing_identity_line_is_red():
    bad = GOOD_PERSONA.replace(
        "**Identity:** I demonstrate that this validator works end to end.\n\n", ""
    )
    findings = pp.validate_persona(bad)
    assert any("Identity" in f for f in findings)


def test_validate_persona_placeholder_token_is_red():
    bad = GOOD_PERSONA.replace("Demo Expert", "{domain} Expert")
    findings = pp.validate_persona(bad)
    assert any("placeholder" in f and "{domain}" in f for f in findings)


def test_validate_persona_fill_in_marker_is_red():
    bad = GOOD_PERSONA.replace(
        "I demonstrate that this validator works end to end.",
        "[FILL IN: one-sentence identity]",
    )
    findings = pp.validate_persona(bad)
    assert any("FILL IN" in f for f in findings)


def test_validate_persona_mission_specific_id_is_red():
    bad = GOOD_PERSONA.replace(
        "Did I actually run this?", "Did I satisfy criterion C7 for task-node T-12?"
    )
    findings = pp.validate_persona(bad)
    assert any("mission-specific" in f for f in findings)


# ---- draft_from(): mechanical extraction only --------------------------------------
def test_draft_from_extracts_anti_patterns_and_checklist(tmp_path):
    src = tmp_path / "tier-b.md"
    src.write_text(TIER_B_PERSONA, encoding="utf-8")
    draft = pp.draft_from(src, "data-migration")
    assert "Running a destructive migration without a dry-run count-parity check first" in draft
    assert "Have I dry-run the migration against a snapshot and confirmed row-count parity?" in draft
    assert "[FILL IN" in draft  # Identity/Capabilities/Failure Mode all need judgment
    assert "# Data Migration" in draft


def test_draft_from_output_fails_validation_until_completed(tmp_path):
    src = tmp_path / "tier-b.md"
    src.write_text(TIER_B_PERSONA, encoding="utf-8")
    draft = pp.draft_from(src, "data-migration")
    findings = pp.validate_persona(draft)
    assert findings, "an unedited draft-from skeleton must not silently validate GREEN"


def test_draft_from_never_writes_to_disk(tmp_path):
    src = tmp_path / "tier-b.md"
    src.write_text(TIER_B_PERSONA, encoding="utf-8")
    before = sorted(tmp_path.iterdir())
    pp.draft_from(src, "data-migration")
    after = sorted(tmp_path.iterdir())
    assert before == after


# ---- promote(): scope routing, dry-run default, force/collision --------------------
def test_target_path_project_scope():
    target = pp._target_path("project", "demo-expert")
    assert target == REPO / "personas" / "demo-expert.md"


def test_target_path_user_scope():
    target = pp._target_path("user", "demo-expert")
    assert target == Path.home() / ".looptimal" / "personas" / "demo-expert.md"


def test_promote_rejects_non_kebab_case_slug(tmp_path, capsys):
    candidate = tmp_path / "good.md"
    candidate.write_text(GOOD_PERSONA, encoding="utf-8")
    rc = pp.promote("Not_Kebab", candidate, "project", write=False, force=False)
    assert rc == 1
    assert "kebab-case" in capsys.readouterr().out


def test_promote_dry_run_by_default_does_not_write(tmp_path, capsys):
    candidate = tmp_path / "good.md"
    candidate.write_text(GOOD_PERSONA, encoding="utf-8")
    target = tmp_path / "target.md"
    rc = pp.promote("demo-expert", candidate, "project", write=False, force=False)
    assert rc == 0
    assert not target.exists()
    assert "dry run" in capsys.readouterr().out


def test_promote_invalid_candidate_is_red_exit_1(tmp_path, capsys):
    candidate = tmp_path / "bad.md"
    candidate.write_text("# Not even close\n\nNo sections at all.\n", encoding="utf-8")
    rc = pp.promote("bad-one", candidate, "project", write=False, force=False)
    assert rc == 1
    assert "RED" in capsys.readouterr().out


# ---- CLI-level: full subprocess round trip, project and user scope -----------------
def _run(*args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, encoding="utf-8", env=env)


def test_cli_draft_from(tmp_path):
    src = tmp_path / "tier-b.md"
    src.write_text(TIER_B_PERSONA, encoding="utf-8")
    result = _run("draft-from", str(src), "--capability", "data-migration")
    assert result.returncode == 0
    assert "# Data Migration" in result.stdout


def test_cli_promote_write_scope_project(tmp_path):
    # Copy the script + an isolated personas/ dir so this test never touches the real repo.
    fake_repo = tmp_path / "repo"
    (fake_repo / "scripts").mkdir(parents=True)
    (fake_repo / "personas").mkdir()
    script_copy = fake_repo / "scripts" / "looptimal-persona-promote.py"
    script_copy.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    candidate = tmp_path / "good.md"
    candidate.write_text(GOOD_PERSONA, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script_copy), "promote", "demo-expert", str(candidate), "--write"],
        cwd=str(fake_repo / "scripts"), capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    written = fake_repo / "personas" / "demo-expert.md"
    assert written.is_file()
    assert written.read_text(encoding="utf-8") == GOOD_PERSONA


def test_cli_promote_write_scope_user_isolated_home(tmp_path):
    # pathlib.Path.home() checks USERPROFILE before HOME on Windows (ntpath.expanduser's own
    # precedence) — overriding only HOME silently no-ops there. Override both; USERPROFILE is
    # simply unused/ignored on POSIX. Same lesson as tests/test_ls.py's _run_with_home().
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    candidate = tmp_path / "good.md"
    candidate.write_text(GOOD_PERSONA, encoding="utf-8")
    env = {**os.environ, "HOME": str(fake_home), "USERPROFILE": str(fake_home)}

    result = _run("promote", "demo-expert", str(candidate), "--scope", "user", "--write", env=env)
    assert result.returncode == 0, result.stderr
    written = fake_home / ".looptimal" / "personas" / "demo-expert.md"
    assert written.is_file()
    assert written.read_text(encoding="utf-8") == GOOD_PERSONA


def test_cli_promote_refuses_existing_target_without_force(tmp_path):
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    candidate = tmp_path / "good.md"
    candidate.write_text(GOOD_PERSONA, encoding="utf-8")
    env = {**os.environ, "HOME": str(fake_home), "USERPROFILE": str(fake_home)}

    first = _run("promote", "demo-expert", str(candidate), "--scope", "user", "--write", env=env)
    assert first.returncode == 0

    second = _run("promote", "demo-expert", str(candidate), "--scope", "user", "--write", env=env)
    assert second.returncode == 1
    assert "already exists" in second.stdout

    forced = _run("promote", "demo-expert", str(candidate), "--scope", "user", "--write",
                  "--force", env=env)
    assert forced.returncode == 0
    assert "WROTE" in forced.stdout
