---
name: Bug report
about: Something in Looptimal is broken — the wizard, a script, or a generated artifact
title: "[bug] "
labels: bug
---

**What happened**
A clear description of the bug.

**Which part**
- [ ] The wizard / skill (`SKILL.md`)
- [ ] Outcome layer script (`looptimal-doctor` / `looptimal-lint` / `looptimal-detect` / `verify-outcome` / `looptimal-persona-promote`)
- [ ] Loop-design layer script (`loopprint-doctor` / `loopprint-lint` / `loopprint-detect` / `loopprint-ls` / `loopprint-skillify` / `loopprint-report` / `loopprint-update`)
- [ ] A generated artifact (`run-this-loop.sh` / `verify.sh` / `maker.sh` / `loop-spec.yaml`)
- [ ] Install / discovery in a harness

**Harness & platform**
- Harness (Claude Code / Codex / OpenCode / Pi / Hermes / OpenClaw / generic):
- OS (Linux / macOS / Windows+WSL / Windows native):
- Python (`python3 --version`):

**Doctor output**
For install problems, "doesn't trigger," or script errors, please paste output from both doctors — it usually pinpoints the issue, and we'll ask for it before triage if it's missing:
- `python3 scripts/looptimal-doctor.py` (outcome layer)
- `python3 scripts/loopprint-doctor.py` (loop-design layer)

**Steps to reproduce**
1.
2.

**Expected vs. actual**
