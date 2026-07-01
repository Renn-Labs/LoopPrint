"""Tests for loopprint-update.py (dry-run by default; --apply performs the sync)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UPDATE = REPO / "scripts" / "loopprint-update.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("loopprint_update", UPDATE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


update = _load_module()


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True,
                    env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                         "PATH": "/usr/bin:/bin"})


def _make_source_repo(root: Path) -> Path:
    src = root / "src-repo"
    src.mkdir()
    (src / "SKILL.md").write_text("# skill\n")
    (src / "scripts").mkdir()
    (src / "scripts" / "tool.py").write_text("print('v1')\n")
    _git(["init", "-q"], src)
    _git(["add", "-A"], src)
    _git(["commit", "-q", "-m", "seed"], src)
    return src


# ---- _tracked_files / _iter_source_files ------------------------------------
def test_tracked_files_excludes_untracked_and_gitignored(tmp_path):
    src = _make_source_repo(tmp_path)
    # Untracked internal state that must never leak into a copy-based install.
    (src / ".omc").mkdir()
    (src / ".omc" / "session.json").write_text("{}")
    tracked = update._iter_source_files(src)
    assert Path("SKILL.md") in tracked
    assert Path("scripts/tool.py") in tracked
    assert Path(".omc/session.json") not in tracked


def test_iter_source_files_falls_back_when_not_a_git_repo(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "a.txt").write_text("x")
    (plain / "__pycache__").mkdir()
    (plain / "__pycache__" / "junk.pyc").write_text("x")
    files = update._iter_source_files(plain)
    assert Path("a.txt") in files
    assert not any("__pycache__" in str(p) for p in files)


# ---- _diff_copy_target -------------------------------------------------------
def test_diff_reports_add_update_remove(tmp_path):
    src = _make_source_repo(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    (target / "SKILL.md").write_text("# stale copy\n")  # differs -> update
    (target / "stale.md").write_text("old file")  # not in src -> remove
    # scripts/tool.py missing entirely -> add

    diff = update._diff_copy_target(src, target)
    joined = "\n".join(diff)
    assert "update SKILL.md" in joined
    assert "add    scripts/tool.py" in joined
    assert "remove stale.md" in joined


def test_diff_reports_already_in_sync(tmp_path):
    src = _make_source_repo(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    (target / "SKILL.md").write_text("# skill\n")
    (target / "scripts").mkdir()
    (target / "scripts" / "tool.py").write_text("print('v1')\n")
    assert update._diff_copy_target(src, target) == ["  already in sync"]


def test_diff_not_installed(tmp_path):
    src = _make_source_repo(tmp_path)
    missing = tmp_path / "does-not-exist"
    assert update._diff_copy_target(src, missing) == ["  (not installed here — nothing to sync)"]


# ---- _apply_copy_target -------------------------------------------------------
def test_apply_syncs_add_update_and_removes_stale(tmp_path):
    src = _make_source_repo(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    (target / "SKILL.md").write_text("# stale copy\n")
    (target / "stale.md").write_text("old file")

    update._apply_copy_target(src, target)

    assert (target / "SKILL.md").read_text() == "# skill\n"
    assert (target / "scripts" / "tool.py").read_text() == "print('v1')\n"
    assert not (target / "stale.md").exists()


def test_apply_never_copies_gitignored_state(tmp_path):
    src = _make_source_repo(tmp_path)
    (src / ".omc").mkdir()
    (src / ".omc" / "session.json").write_text("{}")
    target = tmp_path / "target"
    target.mkdir()

    update._apply_copy_target(src, target)

    assert not (target / ".omc").exists()


# ---- end-to-end CLI (subprocess, dry-run-by-default semantics) -------------
def test_cli_dry_run_by_default_makes_no_changes(tmp_path):
    src = _make_source_repo(tmp_path)
    result = subprocess.run(
        [sys.executable, str(UPDATE), "--repo-root", str(src)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "dry-run" in result.stdout
    assert "APPLYING" not in result.stdout
    # dry-run must not have touched the source repo's git state.
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(src),
                            capture_output=True, text=True)
    assert status.stdout.strip() == ""


def test_cli_runs_clean_regardless_of_this_machines_install_state(tmp_path):
    # COPY_TARGETS is a module-level constant pointing at real, fixed paths (e.g.
    # ~/.codex/skills/looptimal) — a subprocess re-reads the script fresh, so it can't be
    # monkeypatched from this test process (see _apply_copy_target/_diff_copy_target unit
    # tests above for the actual sync-logic coverage, which IS safely parameterizable).
    # This only asserts the CLI exits 0 and never touches a target that doesn't exist.
    src = _make_source_repo(tmp_path)
    for target in update.COPY_TARGETS:
        before = target.exists()
        result = subprocess.run(
            [sys.executable, str(UPDATE), "--repo-root", str(src)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert target.exists() == before, "dry-run must never create or remove a copy target"
