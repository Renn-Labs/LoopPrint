#!/usr/bin/env python3
"""record-demo.py — capture a real, honest demo of Looptimal's core differentiator (an outer
verifier catching a self-reported GREEN as fraudulent) into an asciinema v2 .cast file.

Every command's OUTPUT is real: each step is actually run via subprocess and its real stdout is
captured verbatim — nothing here is fabricated or hand-written. The "typing" you see when this
plays back is a synthesized animation of the command text (a standard, accepted asciinema
recording technique — plenty of real demo .cast files are produced by scripting a canned command
sequence rather than literally hand-typing every keystroke); the output that follows each command
is always the program's genuine output from this run.

Usage: python3 scripts/record-demo.py [--out assets/demo.cast]
Then, if you have `agg` (https://github.com/asciinema/agg) installed:
    agg assets/demo.cast assets/demo.gif
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (typed command, real subprocess argv to run, cwd relative to REPO) — kept short and true to
# the issue's own ask (README.md issue #7): the highest-leverage ~20s a skeptical visitor can be
# shown is the tamper-to-RED catch, not a feature tour.
STEPS = [
    ("# Looptimal's outer verifier: an honest run round-trips GREEN...",
     None, "."),
    ("python3 scripts/verify-outcome.py --selftest",
     [sys.executable, "scripts/verify-outcome.py", "--selftest"], "."),
    ("# ...and a worked example: 3 independent judges score an artifact, k-of-N quorum gates it.",
     None, "."),
    ("bash run_demo.sh",
     ["bash", "run_demo.sh"], "examples/critic-panel"),
]

TYPING_CHAR_DELAY_S = 0.035  # synthesized typing speed for the command text only


def _run_step(argv: list[str], cwd: Path) -> str:
    result = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=120)
    return result.stdout + result.stderr


def record(out_path: Path, width: int = 100, height: int = 24) -> None:
    events: list[list] = []
    t = 0.0

    def emit(text: str, dt: float) -> None:
        nonlocal t
        t += dt
        events.append([round(t, 6), "o", text])

    for label, argv, cwd_rel in STEPS:
        if label.startswith("#"):
            emit(f"\x1b[2m{label}\x1b[0m\r\n", 0.6)
            continue
        emit("$ ", 0.3)
        for ch in label:
            emit(ch, TYPING_CHAR_DELAY_S)
        emit("\r\n", 0.15)
        real_output = _run_step(argv, REPO / cwd_rel) if argv else ""
        # Real output, replayed as a small number of realistic chunks rather than one instant
        # dump — still 100% the program's genuine text, just paced for watchability.
        lines = real_output.splitlines(keepends=True) or ["\n"]
        for line in lines:
            emit(line.replace("\n", "\r\n") if not line.endswith("\r\n") else line, 0.05)
        emit("\r\n", 0.5)

    header = {
        "version": 2, "width": width, "height": height,
        "timestamp": 0,
        "title": "Looptimal — outer-verifier proof",
        "env": {"TERM": "xterm-256color", "SHELL": "/bin/bash"},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(header) + "\n")
        for ev in events:
            fh.write(json.dumps(ev) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[2] if __doc__ else "")
    ap.add_argument("--out", default=str(REPO / "assets" / "demo.cast"))
    args = ap.parse_args(argv)
    out_path = Path(args.out)
    record(out_path)
    print(f"record-demo: wrote {out_path}")
    print(f"record-demo: preview locally with `asciinema play {out_path}` "
         f"(pip install asciinema), or render a GIF with `agg {out_path} demo.gif` "
         f"(https://github.com/asciinema/agg)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
