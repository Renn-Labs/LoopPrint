#!/usr/bin/env bash
# verify.sh — the EXTERNAL verifier for this loop. The single source of "done".
#
# Contract:
#   exit 0  => GREEN  (goal met for this iteration)
#   exit !0 => RED    (not yet; the loop iterates)
#
# Rules:
#   * This must be something the MAKER cannot satisfy by self-assessment. A test, a build, a lint, a
#     reproduction, a benchmark threshold, or a SEPARATE reviewer — never "the same agent says it looks good".
#   * Keep it fast and deterministic; it runs every iteration.
#   * Print enough on failure that the next iteration knows what to fix.
set -euo pipefail

# --- pick the gate(s) for your pattern; delete the rest ----------------------

# MORTY (bug): the reproduction must pass, and nothing else may regress.
# pytest tests/test_repro_issue_123.py -q && pytest -q

# Spec-Driven: the derived spec suite must pass.
# npm test --silent

# Performance: hit the target AND keep correctness. Both gates, every time.
# ms=$(./bench.sh --json | jq .p95_ms)
# awk "BEGIN{exit !($ms <= 150)}"   # target: p95 <= 150ms
# npm test --silent                 # correctness must still pass

# Reviewer gate (separate from the maker): exit on the reviewer's verdict.
# verdict=$(your-reviewer --check "loops/<slug>/state.md")
# [ "$verdict" = "PASS" ]

echo "verify.sh: no gate wired in yet — refusing to report GREEN." >&2
exit 1
