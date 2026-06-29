#!/usr/bin/env bash
# verify.sh — external gate (READ-ONLY): GREEN if remediated.flag exists.
# This script is read-only and never sources or execs maker.sh.
# maker != checker is enforced structurally by the runner.
set -euo pipefail

if [ -f remediated.flag ]; then
    printf 'verify: remediated.flag present — GREEN\n'
    exit 0
else
    printf 'verify: remediated.flag missing — RED\n'
    exit 1
fi
