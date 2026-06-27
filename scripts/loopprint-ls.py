#!/usr/bin/env python3
"""loopprint-ls — repo-local loop health view ("rot radar").

Enumerates the loops in this repo and reports each one's health from its OWN run history, so you can
answer one question at a glance: *is any of my automation silently broken?*

  HEALTHY  — ran recently, last verdict GREEN (or a short red run still in progress)
  RUNNING  — wrote within --running-grace and last verdict RED (a live iteration; not judged)
  ROTTEN   — failing repeatedly: red_streak >= K (default 3) and ran within N days
  STALE    — no run in > N days (default 14): the automation went quiet
  UNKNOWN  — no run history yet (reason: never_run | parse_error | no_data)

Discovery is BINDING-AWARE: it asks loopprint-detect.py where this harness keeps loop state (state_dir),
then falls back to loops/ and .omc/loops/. It NEVER hardcodes a per-harness matrix; the binding owns the path.

Health source ladder (first that has data wins): metrics.jsonl -> state.jsonl -> the verifier marker. Streaks
are counted in FILE APPEND ORDER, never by sorting timestamps (clocks skew; the runner appends in order).

This tool only READS state. It never executes a loop, a maker, or a verifier. Stdlib only — no PyYAML, no
network. Exit code is 0 unless --exit-nonzero-if-rotten is set and at least one loop is ROTTEN (a CI/cron hook).

Usage:
  loopprint-ls.py [--dir DIR ...] [--stale-days N] [--rot-streak K] [--running-grace SECONDS]
                  [--json] [--rotten] [--exit-nonzero-if-rotten]
"""
from __future__ import annotations
import sys, os, json, argparse, subprocess
from pathlib import Path
from datetime import datetime, timezone

DEFAULT_ROOTS = ["loops", ".omc/loops"]


def _detect_binding(script_dir: Path, cwd: Path) -> dict:
    """Ask loopprint-detect.py for the binding (state_dir, marker_path). Empty dict if unavailable."""
    detect = script_dir / "loopprint-detect.py"
    if not detect.is_file():
        return {}
    try:
        out = subprocess.run([sys.executable, str(detect), "--cwd", str(cwd)],
                             capture_output=True, text=True, timeout=10)
    except Exception:
        return {}
    binding = {}
    for line in out.stdout.splitlines():
        if line.startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        binding[k.strip()] = v.strip()
    return binding


def _root_from_state_dir(state_dir: str):
    """'loops/<slug>' -> 'loops'; '.omc/loops/<slug>' -> '.omc/loops'. Strips trailing slug placeholder."""
    parts = [p for p in state_dir.strip().split("/") if p != ""]
    while parts and ("<slug>" in parts[-1] or "{slug}" in parts[-1]):
        parts.pop()
    return "/".join(parts) if parts else None


def _scan_roots(script_dir: Path, cwd: Path, extra_dirs: list[str]) -> tuple[list[str], str]:
    roots: list[str] = []
    binding = _detect_binding(script_dir, cwd)
    r = _root_from_state_dir(binding.get("state_dir", ""))
    if r:
        roots.append(r)
    env_root = os.environ.get("LOOPPRINT_ROOT")
    if env_root:
        roots.append(env_root)
    roots.extend(extra_dirs or [])
    roots.extend(DEFAULT_ROOTS)
    # de-dupe, preserve order
    seen, ordered = set(), []
    for r in roots:
        if r and r not in seen:
            seen.add(r)
            ordered.append(r)
    return ordered, binding.get("marker_path", "")


def _find_loops(roots: list[str], cwd: Path) -> dict:
    """slug -> loop dir. A loop dir holds loop-spec.yaml OR metrics.jsonl OR state.jsonl. First root wins."""
    found: dict[str, Path] = {}
    for root in roots:
        base = cwd / root
        if not base.is_dir():
            continue
        for sub in sorted(base.iterdir()):
            if not sub.is_dir():
                continue
            if (sub / "loop-spec.yaml").is_file() or (sub / "metrics.jsonl").is_file() or (sub / "state.jsonl").is_file():
                found.setdefault(sub.name, sub)
    return found


def _read_jsonl_results(path: Path):
    """Return (results, malformed_count). results = [(verifier_result, ts)] in FILE ORDER; only GREEN/RED kept."""
    results, bad = [], 0
    try:
        lines = path.read_text().splitlines()
    except Exception:
        return results, bad
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception:
            bad += 1
            continue
        vr = obj.get("verifier_result")
        if vr in ("GREEN", "RED"):
            results.append((vr, obj.get("ts")))
    return results, bad


def _resolve_marker(marker_tmpl: str, slug: str, cwd: Path):
    """Best-effort resolve a verifier-marker path from the binding's marker_path template."""
    if not marker_tmpl:
        return None
    cand = marker_tmpl.replace("<mode>", slug).replace("<slug>", slug)
    p = cwd / cand
    if p.is_file():
        return p
    # marker_path often points at .omc/state/<mode>-verifier.json; try matching this slug there.
    parent = (cwd / marker_tmpl).parent
    if parent.is_dir():
        for m in sorted(parent.glob("*verifier.json")):
            if slug in m.name:
                return m
    return None


def _from_results(results, source: str) -> dict:
    last_result, last_ts = results[-1]
    streak = 0
    for vr, _ in reversed(results):       # append order: count trailing REDs
        if vr == "RED":
            streak += 1
        else:
            break
    return {
        "last_result": last_result,
        "last_ts": last_ts,
        "red_streak": streak,
        "green_ever": any(vr == "GREEN" for vr, _ in results),
        "iters": len(results),
        "source": source,
    }


def _health(loop_dir: Path, marker_tmpl: str, slug: str, cwd: Path):
    """Return (health_dict | None, reason | None) via the source ladder."""
    for fn in ("metrics.jsonl", "state.jsonl"):
        p = loop_dir / fn
        if p.is_file():
            results, bad = _read_jsonl_results(p)
            if results:
                return _from_results(results, fn), None
            if bad:
                return None, "parse_error"
    marker = _resolve_marker(marker_tmpl, slug, cwd)
    if marker:
        try:
            m = json.loads(marker.read_text())
        except Exception:
            return None, "parse_error"
        res = m.get("result")
        if res in ("GREEN", "RED"):
            return _from_results([(res, m.get("ts"))], "marker"), None
    if (loop_dir / "loop-spec.yaml").is_file():
        return None, "never_run"
    return None, "no_data"


def _parse_ts(s):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _classify(h, reason, now, N, K, grace):
    if h is None:
        return "UNKNOWN", reason
    last_ts = _parse_ts(h["last_ts"])
    age_sec = (now - last_ts).total_seconds() if last_ts else None
    age_days = age_sec / 86400 if age_sec is not None else None
    # RUNNING: wrote very recently and last verdict is RED -> a live iteration, don't judge it.
    if age_sec is not None and age_sec < grace and h["last_result"] == "RED":
        return "RUNNING", None
    if age_days is not None and age_days > N:
        return "STALE", None
    if h["red_streak"] >= K or (h["source"] == "marker" and h["last_result"] == "RED"):
        return "ROTTEN", None
    return "HEALTHY", None


def _age_str(last_ts, now):
    dt = _parse_ts(last_ts)
    if dt is None:
        return "-"
    sec = (now - dt).total_seconds()
    if sec < 90:
        return f"{int(sec)}s ago"
    if sec < 5400:
        return f"{int(sec // 60)}m ago"
    if sec < 172800:
        return f"{int(sec // 3600)}h ago"
    return f"{int(sec // 86400)}d ago"


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="loopprint-ls.py", description="Repo-local loop health view (rot radar).")
    ap.add_argument("--dir", action="append", default=[], help="extra root to scan (repeatable)")
    ap.add_argument("--stale-days", type=int, default=14, help="STALE if no run in > N days (default 14)")
    ap.add_argument("--rot-streak", type=int, default=3, help="ROTTEN at >= K trailing RED runs (default 3)")
    ap.add_argument("--running-grace", type=int, default=120, help="recent-write window (s) treated as RUNNING")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--rotten", action="store_true", help="show only ROTTEN + STALE loops")
    ap.add_argument("--exit-nonzero-if-rotten", action="store_true", help="exit 1 if any loop is ROTTEN (CI hook)")
    args = ap.parse_args(argv[1:])

    cwd = Path.cwd()
    script_dir = Path(__file__).resolve().parent
    now = datetime.now(timezone.utc)

    roots, marker_tmpl = _scan_roots(script_dir, cwd, args.dir)
    loops = _find_loops(roots, cwd)

    rows = []
    for slug in sorted(loops):
        h, reason = _health(loops[slug], marker_tmpl, slug, cwd)
        status, why = _classify(h, reason, now, args.stale_days, args.rot_streak, args.running_grace)
        rows.append({
            "slug": slug,
            "status": status,
            "reason": why,
            "last_run": (h or {}).get("last_ts"),
            "iters": (h or {}).get("iters", 0),
            "red_streak": (h or {}).get("red_streak", 0),
            "last_result": (h or {}).get("last_result"),
            "source": (h or {}).get("source"),
            "dir": str(loops[slug]),
        })

    if args.rotten:
        rows = [r for r in rows if r["status"] in ("ROTTEN", "STALE")]

    any_rotten = any(r["status"] == "ROTTEN" for r in rows)

    if args.json:
        print(json.dumps({"scanned_roots": roots, "loops": rows}, indent=2))
    else:
        if not rows:
            print(f"No loops found (scanned: {', '.join(roots)}).")
        else:
            print(f"{'SLUG':<24} {'STATUS':<8} {'LAST RUN':<11} {'ITERS':>5} {'RED-STREAK':>10}  SOURCE")
            for r in rows:
                tag = r["status"] + (f"({r['reason']})" if r["reason"] else "")
                print(f"{r['slug']:<24} {tag:<8} {_age_str(r['last_run'], now):<11} "
                      f"{r['iters']:>5} {r['red_streak']:>10}  {r['source'] or '-'}")
            rotten = [r['slug'] for r in rows if r['status'] == 'ROTTEN']
            stale = [r['slug'] for r in rows if r['status'] == 'STALE']
            if rotten:
                print(f"\n⚠  ROTTEN (failing repeatedly): {', '.join(rotten)}", file=sys.stderr)
            if stale:
                print(f"⏸  STALE (no recent run): {', '.join(stale)}", file=sys.stderr)

    return 1 if (args.exit_nonzero_if_rotten and any_rotten) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
