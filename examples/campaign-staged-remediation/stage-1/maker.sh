#!/usr/bin/env bash
# maker.sh — harness-agnostic dispatch: write the reverse-engineered spec.
#
# Replace the body below with your actual dispatch:
#   claude -p "reverse-spec the target module, write spec.md"
#   codex exec "derive spec from module and output spec.md"
#   python3 scripts/reverse-spec.py > spec.md
#
# The runner calls maker.sh as a SEPARATE PROCESS (maker != checker is enforced
# structurally). This script MUST NOT modify verify.sh or any gate artifact.
set -euo pipefail

# Demo: write a minimal spec.md to satisfy the gate.
# In real use, replace this with your tool dispatch above.
cat > spec.md <<'SPEC'
# Reverse-Engineered Spec: target-module

## Behaviour contract

- Input: a list of items
- Output: filtered and sorted list, duplicates removed
- Side-effects: none (pure function)
- Error handling: raises ValueError on non-list input

## Invariants

1. Output length <= input length
2. Output is sorted ascending
3. No duplicates in output
SPEC
