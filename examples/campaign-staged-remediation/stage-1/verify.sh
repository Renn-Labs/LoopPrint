#!/usr/bin/env bash
# verify.sh — external gate (READ-ONLY): GREEN if spec.md exists.
# This script is read-only and never sources or execs maker.sh.
# maker != checker is enforced structurally by the runner.
set -euo pipefail

if [ -f spec.md ]; then
    printf 'verify: spec.md present — GREEN\n'
    exit 0
else
    printf 'verify: spec.md missing — RED\n'
    exit 1
fi
