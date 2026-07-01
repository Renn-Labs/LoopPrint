#!/usr/bin/env python3
"""loopprint-update — one-command update for a Looptimal install.

Handles the two install shapes from README.md's "Other harnesses" table:
  * git clone (or a symlinked folder-skill pointing at one) — `git pull`.
  * copy-based installs (e.g. Codex/OMX: `cp -r ~/looptimal ~/.codex/skills/looptimal`) —
    symlinked harnesses update for free via the pull above; a COPY does not, so it needs
    an explicit re-sync against the source clone.

Dry-run by default: prints what would change and does nothing. `--apply` performs it.
Never auto-runs — this is a skill's own script, run explicitly by a human, same discipline
as every other scripts/*.py here. Stdlib-only; no network call beyond `git pull` itself,
which is the same network surface `git clone` already implies (not a new one).

Usage: loopprint-update.py [--apply] [--repo-root DIR]
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# Known copy-based install targets (source: README.md's harness table). Symlinked harnesses
# (Claude Code folder skill, OpenCode, OpenClaw/EClaw, Hermes) update for free via `git pull`
# and are intentionally NOT listed here — re-syncing a symlink target would be a no-op at best
# and a mistake at worst (it would resolve through the symlink back to the source itself).
COPY_TARGETS = (
    Path.home() / ".codex" / "skills" / "looptimal",
    Path.home() / ".codex" / "skills" / "loopprint",  # pre-rebrand path, still honored
)

# Fallback exclude list, used only when repo_root isn't a git checkout (git ls-files is the
# real source of truth below — untracked/gitignored files, e.g. .buildlog/ internal notes,
# .omc/ session state, or build artifacts, must never leak into a copy-based install).
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", "build", "looptimal.egg-info", ".omc"}
EXCLUDE_SUFFIXES = (".pyc",)


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def _tracked_files(repo_root: Path) -> set[Path] | None:
    """Git-tracked files only (relative paths) — the correct definition of "what ships in a
    skill install." Returns None if repo_root isn't a git checkout (caller falls back)."""
    if not (repo_root / ".git").exists():
        return None
    result = _run(["git", "ls-files"], repo_root)
    if result.returncode != 0:
        return None
    return {Path(ln) for ln in result.stdout.splitlines() if ln.strip()}


def _git_preview(repo_root: Path) -> tuple[bool, list[str]]:
    """Returns (is_git_repo, lines describing what `git pull` would bring in)."""
    if not (repo_root / ".git").exists():
        return False, []
    fetch = _run(["git", "fetch", "--quiet"], repo_root)
    if fetch.returncode != 0:
        return True, [f"  (could not fetch: {fetch.stderr.strip()[:200]})"]
    log = _run(["git", "log", "--oneline", "HEAD..@{u}"], repo_root)
    if log.returncode != 0:
        return True, ["  (no upstream configured for the current branch — nothing to preview)"]
    incoming = [ln for ln in log.stdout.splitlines() if ln.strip()]
    if not incoming:
        return True, ["  already up to date"]
    return True, [f"  {ln}" for ln in incoming]


def _git_apply(repo_root: Path) -> str:
    result = _run(["git", "pull"], repo_root)
    return result.stdout.strip() + (("\n" + result.stderr.strip()) if result.returncode != 0 else "")


def _iter_source_files(repo_root: Path) -> set[Path]:
    tracked = _tracked_files(repo_root)
    if tracked is not None:
        return {rel for rel in tracked if (repo_root / rel).is_file()}
    out: set[Path] = set()
    for path in repo_root.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(repo_root)
        if any(part in EXCLUDE_DIRS for part in rel.parts) or path.suffix in EXCLUDE_SUFFIXES:
            continue
        out.add(rel)
    return out


def _diff_copy_target(repo_root: Path, target: Path) -> list[str]:
    """Returns human-readable diff lines: files to add/update/remove to make `target` match
    `repo_root`'s git-tracked content (never untracked/gitignored files — e.g. .buildlog/
    internal notes or .omc/ session state must not leak into a copy-based install). Compares
    by content, not mtime — copy-based installs can be older or newer."""
    if not target.exists():
        return ["  (not installed here — nothing to sync)"]
    changes: list[str] = []
    src_files = _iter_source_files(repo_root)
    for rel in sorted(src_files):
        src_file = repo_root / rel
        dst_file = target / rel
        if not dst_file.exists():
            changes.append(f"  + add    {rel}")
        elif src_file.read_bytes() != dst_file.read_bytes():
            changes.append(f"  ~ update {rel}")
    if target.is_dir():
        dst_files = {p.relative_to(target) for p in target.rglob("*") if p.is_file()}
        for rel in sorted(dst_files - src_files):
            changes.append(f"  - remove {rel}")
    return changes or ["  already in sync"]


def _apply_copy_target(repo_root: Path, target: Path) -> None:
    src_files = _iter_source_files(repo_root)
    if target.exists():
        for p in list(target.rglob("*")):
            if p.is_file() and p.relative_to(target) not in src_files:
                p.unlink()
    for rel in sorted(src_files):
        dst_file = target / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / rel, dst_file)
    # Prune now-empty directories left behind by removed files.
    if target.exists():
        for d in sorted((p for p in target.rglob("*") if p.is_dir()), reverse=True):
            try:
                d.rmdir()
            except OSError:
                pass


def main(argv) -> int:
    apply = "--apply" in argv
    repo_root = Path(__file__).resolve().parent.parent
    if "--repo-root" in argv:
        repo_root = Path(argv[argv.index("--repo-root") + 1]).resolve()

    print(f"# loopprint-update — {'APPLYING' if apply else 'dry-run (pass --apply to perform)'}")
    print(f"# repo root: {repo_root}")

    is_git, preview = _git_preview(repo_root)
    if is_git:
        print("\n## git clone")
        if apply:
            print(_git_apply(repo_root) or "  already up to date")
        else:
            print("\n".join(preview))
    else:
        print("\n## git clone")
        print("  (not a git checkout — skipping; nothing to pull)")

    any_copy_target = False
    for target in COPY_TARGETS:
        if not target.exists():
            continue
        any_copy_target = True
        print(f"\n## copy-based install: {target}")
        if apply:
            _apply_copy_target(repo_root, target)
            print("  re-synced")
        else:
            print("\n".join(_diff_copy_target(repo_root, target)))
    if not any_copy_target:
        print("\n## copy-based installs")
        print(f"  none found at known paths ({', '.join(str(t) for t in COPY_TARGETS)})")
        print("  (symlinked harnesses — Claude Code folder skill, OpenCode, OpenClaw/EClaw,")
        print("   Hermes — already update for free via the git pull above)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
