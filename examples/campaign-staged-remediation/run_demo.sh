#!/usr/bin/env bash
# run_demo.sh — tmpdir-only demo for the campaign-staged-remediation composition.
# Runs stage-1 then stage-2 in sequence with AUTONOMY=full (skips the human checkpoint).
# Never mutates tracked files — all work happens in a tmpdir.
# git status is clean after this script exits.
#
# Runs under plain bash + coreutils — OMC, plugins, and AI tools are all optional.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RUNNER="${REPO_ROOT}/templates/run-this-loop.sh"

D=$(mktemp -d)
trap 'rm -rf "$D"' EXIT INT TERM

# --- Stage 1: reverse-spec ---
S1="${D}/stage-1"
mkdir -p "${S1}"
cp "${SCRIPT_DIR}/stage-1/verify.sh" \
   "${SCRIPT_DIR}/stage-1/maker.sh" \
   "${RUNNER}" \
   "${S1}/"
chmod +x "${S1}/verify.sh" "${S1}/maker.sh"

printf 'stage-1: running reverse-spec gate loop...\n'
( cd "${S1}" && AUTONOMY=full MAX_ITERS=5 bash run-this-loop.sh )
printf 'stage-1: gate GREEN\n'

# --- Human checkpoint (demo mode — AUTONOMY=full skips this pause) ---
printf 'checkpoint: inter-stage human checkpoint skipped (demo mode)\n'

# --- Stage 2: remediate ---
S2="${D}/stage-2"
mkdir -p "${S2}"
cp "${SCRIPT_DIR}/stage-2/verify.sh" \
   "${SCRIPT_DIR}/stage-2/maker.sh" \
   "${RUNNER}" \
   "${S2}/"
chmod +x "${S2}/verify.sh" "${S2}/maker.sh"

printf 'stage-2: running remediate gate loop...\n'
( cd "${S2}" && AUTONOMY=full MAX_ITERS=5 bash run-this-loop.sh )
printf 'stage-2: gate GREEN\n'

printf 'PASS: campaign-staged-remediation demo complete.\n'
