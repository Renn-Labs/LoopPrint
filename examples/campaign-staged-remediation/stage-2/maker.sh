#!/usr/bin/env bash
# maker.sh — harness-agnostic dispatch: remediate findings against spec.md.
#
# Replace the body below with your actual dispatch:
#   claude -p "remediate all findings against spec.md; touch remediated.flag on success"
#   codex exec "apply spec-driven fixes, write remediated.flag when done"
#   python3 scripts/remediate.py && touch remediated.flag
#
# The runner calls maker.sh as a SEPARATE PROCESS (maker != checker is enforced
# structurally). This script MUST NOT modify verify.sh or any gate artifact.
set -euo pipefail

# Demo: write remediated.flag to satisfy the gate.
# In real use, replace this with your tool dispatch above.
touch remediated.flag
